from typing import Dict, Any

# Configuración de conectores SFTP
SFTP_CONNECTORS: Dict[str, Dict[str, Any]] = {
    "orchard_sandbox": {
        "host": "localhost",  # Cambiar a sandbox.apstudios.local cuando esté configurado
        "port": 2222,  # Puerto SFTP del sandbox
        "username": "apstudios",
        "password": "password123",  # En producción usar variables de entorno
        "remote_path": "/incoming"
    }
    # Agregar más conectores aquí, e.g., "the_orchard": {...}
}