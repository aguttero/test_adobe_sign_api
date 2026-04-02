import logging

# Configuración global del logger
logging.basicConfig(
    level=logging.INFO, # Nivel mínimo de eventos a registrar
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app_adobe_sync.log"), # Guarda en este archivo
        logging.StreamHandler() # También muestra en la consola (opcional)
    ]
)

logger = logging.getLogger("AdobeSyncApp")

import logging
import json
import uuid
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """Formatea el registro de log como un objeto JSON estructurado."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "correlation_id": getattr(record, "correlation_id", "N/A"),
            "user_id": getattr(record, "user_id", "anonymous")
        }
        
        # Incluir detalles de la excepción si existen
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

# 1. Configuración del Logger
logger = logging.getLogger("AppEmpresarial")
handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 2. Función de ejemplo para llamadas a la API
def registrar_llamada_api(metodo, endpoint, status, duracion_ms, usuario_id):
    # El Correlation ID permite rastrear esta petición en toda la infraestructura
    corr_id = str(uuid.uuid4()) 
    
    # Pasamos datos contextuales usando el argumento 'extra'
    contexto = {
        "correlation_id": corr_id,
        "user_id": usuario_id
    }
    
    mensaje = f"API {metodo} {endpoint} finalizada"
    
    # Agregamos datos técnicos al registro
    logger.info(
        f"{mensaje} | Status: {status} | Latencia: {duracion_ms}ms",
        extra=contexto
    )

# Ejecución de prueba
registrar_llamada_api("GET", "/api/v1/usuarios", 200, 145, "id_empleado_88")
