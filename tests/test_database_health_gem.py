# test_database.py
import os
from pathlib import Path

# Ruta a un archivo oculto que indica si la DB está en uso
HEALTH_FILE = Path(".db_session_active")

def check_db_last_closed_status() -> bool:
    """
    Verifica si el archivo de sesión quedó existiendo desde la última vez.
    Si el archivo existe, significa que el programa anterior no cerró bien.
    """
    if HEALTH_FILE.exists():
        # Si el archivo existe, la última sesión falló o no cerró
        return False
    
    # Si no existe, todo está OK. Creamos uno para la sesión actual.
    HEALTH_FILE.touch()
    return True

def close_db():
    """
    Esta función debe llamarse al final del programa para limpiar el estado.
    """
    if HEALTH_FILE.exists():
        HEALTH_FILE.unlink()
