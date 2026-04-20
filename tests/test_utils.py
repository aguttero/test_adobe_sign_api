"""
Pure stateless helper functions for the Adobe Sign dashboard.
No IO, no exceptions, no imports from other app modules.
"""
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Transform date with isoformat to naive SQLlite date
def convert_to_sqlite_date (date_iso:str):
    
    logger.debug(f"input value: {date_iso}")
    # 1. Convertimos el string a un objeto datetime (maneja el offset -08:00 automáticamente)
    dt_obj = datetime.fromisoformat(date_iso)

    # 2. Extraemos solo la fecha (objeto date)
    date_sqllite = dt_obj.date()
    return date_sqllite


## TEST CODE
# fecha_str = "2026-03-02T08:23:52-08:00"

# fecha_final = convert_to_sqlite_date(fecha_str)

# print(fecha_final)  # Resultado: 2026-03-02
# print(type(fecha_final))  # <class 'datetime.date'>
