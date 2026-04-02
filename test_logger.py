import logging

# LOGGER CONFIG
logger = logging.getLogger(__name__)

texto = "texto mod"
logger.debug(f"{texto}")
logger.error("Error Mod")