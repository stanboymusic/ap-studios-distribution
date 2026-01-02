import paramiko
from typing import Optional


class SFTPConnector:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.transport: Optional[paramiko.Transport] = None
        self.sftp: Optional[paramiko.SFTPClient] = None

    def connect(self):
        """Establece la conexión SFTP."""
        try:
            self.transport = paramiko.Transport((self.host, self.port))
            self.transport.connect(username=self.username, password=self.password)
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