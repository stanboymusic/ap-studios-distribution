#!/usr/bin/env python3
"""
DSP Sandbox - Simulador de Ingest Server para AP Studios
Recibe entregas via SFTP, valida ERN y assets, simula procesamiento DSP.
"""

import os
import sys
import time
import shutil
import zipfile
import json
import threading
import socket
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from uuid import UUID

import paramiko
from paramiko import ServerInterface, SFTPServerInterface, SFTPServer
from paramiko.common import AUTH_SUCCESSFUL, AUTH_FAILED, OPEN_SUCCEEDED, OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

# Import delivery logger
sys.path.append('./backend')
try:
    from app.services.delivery_logger import log_event
except ImportError:
    # Fallback if backend not available
    def log_event(release_id, dsp, event_type, message):
        print(f"[SANDBOX EVENT] {dsp} | {release_id} | {event_type} | {message}")


class DummyServer(ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return OPEN_SUCCEEDED
        return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username == 'apstudios' and password == 'password123':
            return AUTH_SUCCESSFUL
        return AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return False

    def check_channel_subsystem_request(self, channel, name):
        self.event.set()
        if name == 'sftp':
            return True
        return False


class SandboxSFTPServer:
    def __init__(self, root_dir: str = "./sandbox-dsp", port: int = 2222):
        self.root_dir = Path(root_dir)
        self.port = port
        self.server_socket = None
        self.running = False

        # Crear directorios
        self.incoming_dir = self.root_dir / "incoming"
        self.processing_dir = self.root_dir / "processing"
        self.accepted_dir = self.root_dir / "accepted"
        self.rejected_dir = self.root_dir / "rejected"
        self.logs_dir = self.root_dir / "logs"

        for d in [self.incoming_dir, self.processing_dir, self.accepted_dir, self.rejected_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Inicia el servidor SFTP."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("localhost", self.port))
        sock.listen(100)

        print(f"DSP Sandbox SFTP server started on port {self.port}")
        print(f"Root directory: {self.root_dir}")

        # Generar llave una sola vez para evitar lentitud
        server_key = paramiko.RSAKey.generate(2048)

        # Iniciar thread de procesamiento
        processor_thread = threading.Thread(target=self.process_deliveries, daemon=True)
        processor_thread.start()

        self.running = True
        try:
            while self.running:
                client_sock, addr = sock.accept()
                print(f"Connection from {addr}")
                
                # Manejar cada conexión en un thread para no bloquear el loop principal
                t = threading.Thread(target=self.handle_connection, args=(client_sock, server_key))
                t.daemon = True
                t.start()

        except KeyboardInterrupt:
            print("Stopping SFTP server...")
        finally:
            sock.close()

    def handle_connection(self, client_sock, server_key):
        """Maneja el handshake inicial y el servidor SFTP."""
        transport = None
        try:
            transport = paramiko.Transport(client_sock)
            transport.add_server_key(server_key)

            server = DummyServer()
            try:
                transport.start_server(server=server)
            except paramiko.SSHException:
                print("SSH negotiation failed.")
                return

            channel = transport.accept(20)
            if channel is None:
                print("No channel requested.")
                return

            print("Waiting for subsystem request...")
            server.event.wait(10)
            if channel.active:
                print("Starting SFTP subsystem...")
                # SFTPServer in paramiko handles the subsystem on the channel
                # We need to keep the transport alive while the channel is active
                sftp_server = SFTPServer(channel, str(self.root_dir), server)
                
                while channel.active:
                    time.sleep(0.5)
                
                print("SFTP session closed by client.")
            else:
                print("Channel not active.")
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            if transport:
                print("Closing transport.")
                transport.close()

    def handle_client(self, transport):
        # Esta función ya no es necesaria con el nuevo flujo pero la dejamos vacía por compatibilidad si se llama
        pass

    def process_deliveries(self):
        """Procesa entregas en incoming."""
        while self.running:
            try:
                for zip_file in self.incoming_dir.glob("*.zip"):
                    self.process_delivery(zip_file)
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"Error in processing thread: {e}")

    def process_delivery(self, zip_path: Path):
        """Procesa una entrega ZIP."""
        release_id_str = zip_path.stem.replace("delivery_", "")
        try:
            release_id = UUID(release_id_str)
        except ValueError:
            print(f"Invalid release ID: {release_id_str}")
            return

        processing_dir = self.processing_dir / release_id_str
        processing_dir.mkdir(exist_ok=True)

        print(f"Processing delivery: {release_id}")

        # Log processing start
        log_event(
            release_id=release_id,
            dsp="DSP SANDBOX",
            event_type="PROCESSING",
            message="DSP started processing delivery"
        )

        try:
            # Mover a processing
            shutil.move(str(zip_path), str(processing_dir / zip_path.name))

            # Unzip
            with zipfile.ZipFile(processing_dir / zip_path.name, 'r') as zip_ref:
                zip_ref.extractall(processing_dir)

            # Validar
            status, issues = self.validate_delivery(processing_dir)

            # Mover según resultado
            if status == "ACCEPTED":
                target_dir = self.accepted_dir / release_id_str
            else:
                target_dir = self.rejected_dir / release_id_str

            target_dir.mkdir(exist_ok=True)
            for item in processing_dir.iterdir():
                shutil.move(str(item), str(target_dir / item.name))

            # Crear status.json
            status_data = {
                "release_id": release_id_str,
                "status": status,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "issues": issues
            }

            with open(target_dir / "status.json", 'w') as f:
                json.dump(status_data, f, indent=2)

            # Log final status
            log_event(
                release_id=release_id,
                dsp="DSP SANDBOX",
                event_type=status,  # ACCEPTED or REJECTED
                message=f"DSP {status.lower()}: {issues}" if issues else f"DSP {status.lower()}"
            )

            print(f"Delivery {release_id} {status.lower()}")

        except Exception as e:
            print(f"Error processing {release_id}: {e}")
            # Mover a rejected
            rejected_dir = self.rejected_dir / release_id_str
            rejected_dir.mkdir(exist_ok=True)
            shutil.move(str(zip_path), str(rejected_dir / zip_path.name))

            status_data = {
                "release_id": release_id_str,
                "status": "REJECTED",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "issues": [f"Processing error: {str(e)}"]
            }
            with open(rejected_dir / "status.json", 'w') as f:
                json.dump(status_data, f, indent=2)

            # Log error
            log_event(
                release_id=release_id,
                dsp="DSP SANDBOX",
                event_type="ERROR",
                message=f"DSP processing error: {str(e)}"
            )

    def validate_delivery(self, delivery_dir: Path) -> tuple[str, list]:
        """Valida la entrega. Retorna (status, issues)."""
        issues = []

        # Buscar ERN XML
        ern_files = list(delivery_dir.glob("*.xml"))
        if not ern_files:
            return "REJECTED", ["Missing ERN XML file"]

        ern_file = ern_files[0]

        try:
            # Parsear XML
            tree = ET.parse(ern_file)
            root = tree.getroot()

            # Verificar namespace ERN
            if not root.tag.startswith("{http://ddex.net/xml/ern/"):
                issues.append("Invalid ERN namespace")

            # Verificar MessageHeader
            header = root.find(".//{http://ddex.net/xml/ern/}MessageHeader")
            if header is None:
                issues.append("Missing MessageHeader")

            # Verificar ReleaseList
            release_list = root.find(".//{http://ddex.net/xml/ern/}ReleaseList")
            if release_list is None:
                issues.append("Missing ReleaseList")

            # Verificar ResourceList
            resource_list = root.find(".//{http://ddex.net/xml/ern/}ResourceList")
            if resource_list is None:
                issues.append("Missing ResourceList")

            # Verificar DealList
            deal_list = root.find(".//{http://ddex.net/xml/ern/}DealList")
            if deal_list is None:
                issues.append("Missing DealList")

            # Validar assets
            self.validate_assets(delivery_dir, root, issues)

        except ET.ParseError as e:
            issues.append(f"Invalid XML: {str(e)}")

        status = "ACCEPTED" if not issues else "REJECTED"
        return status, issues

    def validate_assets(self, delivery_dir: Path, ern_root, issues: list):
        """Valida que los assets referenciados en ERN existan."""
        # Buscar referencias de audio
        audio_files = []
        for sound_recording in ern_root.iterfind(".//{http://ddex.net/xml/ern/}SoundRecording"):
            file_elem = sound_recording.find(".//{http://ddex.net/xml/ern/}File")
            if file_elem is not None:
                filename = file_elem.text
                if filename:
                    audio_files.append(filename)

        # Buscar artwork
        artwork_files = []
        for image in ern_root.iterfind(".//{http://ddex.net/xml/ern/}Image"):
            file_elem = image.find(".//{http://ddex.net/xml/ern/}File")
            if file_elem is not None:
                filename = file_elem.text
                if filename:
                    artwork_files.append(filename)

        # Verificar existencia
        for audio_file in audio_files:
            if not (delivery_dir / audio_file).exists():
                issues.append(f"Missing audio file: {audio_file}")

        for artwork_file in artwork_files:
            if not (delivery_dir / artwork_file).exists():
                issues.append(f"Missing artwork file: {artwork_file}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        # Limpiar sandbox
        import shutil
        if os.path.exists("./sandbox-dsp"):
            shutil.rmtree("./sandbox-dsp")
        print("Sandbox cleaned")
        return

    server = SandboxSFTPServer()
    server.start()


if __name__ == "__main__":
    main()