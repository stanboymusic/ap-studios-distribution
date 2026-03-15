import paramiko
from typing import Optional
import socket


class SFTPConnector:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.transport: Optional[paramiko.Transport] = None
        self.sftp: Optional[paramiko.SFTPClient] = None

    def connect(self, timeout_seconds: float = 3.0):
        """Establece la conexión SFTP."""
        try:
            sock = socket.create_connection((self.host, self.port), timeout=timeout_seconds)
            sock.settimeout(timeout_seconds)
            self.transport = paramiko.Transport(sock)
            # Paramiko can hang on handshake/auth if the server is misconfigured.
            # Enforce timeouts so delivery fallback can proceed quickly.
            self.transport.banner_timeout = timeout_seconds
            self.transport.auth_timeout = timeout_seconds
            self.transport.start_client(timeout=timeout_seconds)
            self.transport.auth_password(self.username, self.password, timeout=timeout_seconds)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        except Exception as e:
            raise ConnectionError(f"Error conectando a SFTP: {str(e)}")

    def upload(self, local_path: str, remote_path: str):
        """Sube un archivo local al servidor remoto."""
        if not self.sftp:
            raise ConnectionError("SFTP no conectado. Llama a connect() primero.")
        try:
            self.sftp.put(local_path, remote_path)
        except Exception as e:
            raise IOError(f"Error subiendo archivo: {str(e)}")

    def disconnect(self):
        """Cierra la conexión SFTP."""
        if self.sftp:
            self.sftp.close()
        if self.transport:
            self.transport.close()


def upload_file(
    host: str,
    username: str,
    password: str,
    local_file: str,
    remote_path: str,
    port: int = 22,
    timeout_seconds: float = 3.0,
) -> None:
    connector = SFTPConnector(host=host, port=port, username=username, password=password)
    connector.connect(timeout_seconds=timeout_seconds)
    try:
        connector.upload(local_file, remote_path)
    finally:
        connector.disconnect()
