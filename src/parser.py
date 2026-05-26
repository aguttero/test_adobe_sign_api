import logging
from dotenv import dotenv_values

# Init module logger
logger = logging.getLogger(__name__)



# STORAGE CONFIG
FOLDER_IN = "storage/jad/"
FOLDER_OUT = "storage/test_out/" 

# Storage Locations
storage_config = dotenv_values.get('.env')

STORAGE_FOLDER = storage_config.get("STORAGE_FOLDER") # "storage/"
JAD_PDF_FOLDER = storage_config.get("JAD_PDF_FOLDER") # "jad_pdf/"
JAD_TXT_FOLDER = storage_config.get("JAD_TXT_FOLDER") # "jad_txt/"
CONTRACT_PDF_FOLDER = storage_config.get("CONTRACT_PDF_FOLDER") # "con_pdf/"
CONTRACT_TXT_FOLDER = storage_config.get("CONTRACT_TXT_FOLDER") # "con_txt/"