import logging
from dotenv import dotenv_values
import pymupdf

# Init module logger
logger = logging.getLogger(__name__)



# STORAGE CONFIG
FOLDER_IN = "storage/jad/"
FOLDER_OUT = "storage/test_out/" 

# Storage Locations
storage_config = dotenv_values('.env')

STORAGE_FOLDER = storage_config.get("STORAGE_FOLDER") # "storage/"
JAD_PDF_FOLDER = storage_config.get("JAD_PDF_FOLDER") # "jad_pdf/"
JAD_TXT_FOLDER = storage_config.get("JAD_TXT_FOLDER") # "jad_txt/"
CONTRACT_PDF_FOLDER = storage_config.get("CONTRACT_PDF_FOLDER") # "con_pdf/"
CONTRACT_TXT_FOLDER = storage_config.get("CONTRACT_TXT_FOLDER") # "con_txt/"

def convert_pdf_to_words(file_name: str) -> list:
    """Converts file_name PDF content into a list of words
    Returns: list of words"""
    all_words_list = []
    with pymupdf.open(f"{STORAGE_FOLDER}{JAD_PDF_FOLDER}{file_name}") as doc:  # open a document
        logger.debug(f"found file name: {file_name!r}")
        for page in doc:  # iterate the document pages
            full_words = page.get_text("words")  # convert page into word tuples
            # PARSE WORDS:
            for word_tuple in full_words:
                all_words_list.append(word_tuple[4]) #4 is the actual word. Tuple includes other metadata values
    logger.debug(f"Converted file {file_name} to words. Word qty= {len(all_words_list)}")
    return all_words_list

def save_words_file(word_list: list, pdf_filename: str):
    """Saves input list to TXT file in FOLDER_OUT directory. Renames the file from .pdf to .txt"""
    file_name_wo_ext = pdf_filename.rsplit(".")[0]

    txt_file_name = f"{STORAGE_FOLDER}{JAD_TXT_FOLDER}{file_name_wo_ext}.txt"
    with open(txt_file_name, "w") as file:
        file.write(f"{word_list}")
    logger.debug(f"Stored tokens in file= {txt_file_name}")