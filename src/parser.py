import logging
import ast
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

# --- PDF TO WORDS.TXT CONVERSION
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

# --- TXT FILE TO WORDS LIST
def fetch_txt_file(agreement_id:str)->list:
    # --- FETCH WORD LIST from txt file
    txt_file_name = f"{STORAGE_FOLDER}{JAD_TXT_FOLDER}{agreement_id}.txt"
    with open (txt_file_name,'r', encoding='utf-8') as file:
        file_content = file.read().strip()

    word_list = ast.literal_eval(file_content)
    logger.debug(f"Fetched file= {txt_file_name}, word_qty= {len(word_list)}")
    return word_list

# --- PARSE WORD LIST FUNCTIONS FOR JAD
def find_anchor(tokens: list, *anchor_words) -> int:
    """Find the index of the first token in a known sequence of anchor words.
    Returns: int: -1 if the anchor word, or anchor word sequence does not exist in the given token list"""
    total_tokens = len(tokens)
    total_anchors = len(anchor_words)
    search_limit = total_tokens - total_anchors + 1
    logger.debug(
        f"total_tokens len= {total_tokens}, total_anchors len= {total_anchors}, type(anchor_words)= {type(anchor_words)}"
    )

    for i in range(search_limit):
        anchor_match = True

        # Word by word comparison:
        for j in range(total_anchors):
            token_word = tokens[i + j].lower()
            anchor_word = anchor_words[j].lower()

            # if a single word does not match -> break loop
            if token_word != anchor_word:
                anchor_match = False
                break

        # If internal anchor loop finished and everything matched -> index found
        if anchor_match:
            logger.debug(
                f"Match found for anchor= {anchor_words} - Returning index= {i} "
            )
            return i
    # If we parsed al text and no complete coincidence:
    return -1  #  '-1' flag means: anchor words not found

def extract_until_anchor_claude(tokens, start, *stop_anchors):
    """Collect tokens from `start` until we hit any known stop anchor."""
    stop_sequences = [
        s.lower() if isinstance(s, str) else [x.lower() for x in s]
        for s in stop_anchors
    ]
    result = []
    i = start
    while i < len(tokens):
        # Check if current position matches any stop sequence
        for stop in stop_sequences:
            words = [stop] if isinstance(stop, str) else stop
            if tokens[i : i + len(words)] and all(
                tokens[i + j].lower() == words[j] for j in range(len(words))
            ):
                return result, i
        result.append(tokens[i])
        i += 1
    return result, i

def parse_jad_words(tokens: list) -> dict:
    """Extracts data from a JAD token list
    Returns: dictionary"""
    result = {}

    # --- Date ---
    # Anchor: "Fecha:" → next token is the date
    idx = find_anchor(tokens, "Fecha:")
    if idx != -1:
        result["fecha"] = tokens[idx + 1]

    # --- Requesting area (Gerencia Solicitante) ---
    # Anchor: "Gerencia", "Solicitante" → collect until "Rut" anchor
    idx = find_anchor(tokens, "Gerencia", "Solicitante")
    if idx != -1:
        area_tokens, _ = extract_until_anchor_claude(
            tokens, idx + 2, ["Rut", "Proveedor"]
        )
        result["gerencia_solicitante"] = " ".join(area_tokens)
        logger.debug(f"area_tokens= {area_tokens!r}")

    # --- RUT Proveedor ---
    # Anchor/header: "Rut", "Proveedor", "Razón", "Social", "Proveedor", "SI/NO"
    # Anchor/header v2: "Social", "Proveedor", "SI/NO"
    # The RUT is the token immediately after this header block
    idx = find_anchor(tokens, "Social", "Proveedor", "SI/NO")
    if idx != -1:
        # Skip the full header: "Rut Proveedor Razón Social Proveedor SI/NO" (6 tokens)
        # Skip the full header v2: "Social Proveedor SI/NO" (3 tokens)
        header_end = idx + 3  # adjust if your header varies
        result["rut_proveedor"] = tokens[header_end]
        logger.debug(f"rut_proveedor= {tokens[header_end]!r}")

    # --- Razón Social Proveedor(Company Name) ---
    # Company name starts right after the RUT value, ends at next anchor
    if "rut_proveedor" in result:
        rut_idx = tokens.index(result["rut_proveedor"])
        name_tokens, _ = extract_until_anchor_claude(
            tokens, rut_idx + 1, ["Proveedor", "Relacionado"]
        )
        result["nombre_proveedor"] = " ".join(name_tokens)
        logger.debug(f"name_tokens= {name_tokens!r}")

    # --- Monto en UF (UF Amount) ---
    # Anchor/header: 'Criticidad', 'del', 'Servicio'
    # The UF amount is the token immediately after this header block
    idx = find_anchor(tokens, "Criticidad", "del", "Servicio")
    if idx != -1:
        # Skip the full header: 'Criticidad', 'del', 'Servicio' (3 tokens)
        header_end = idx + 3  # adjust if your header varies
        uf_amount_float = float(
            tokens[header_end].strip().replace(".", "").replace(",", ".")
        )
        result["monto_uf"] = uf_amount_float
        logger.debug(f"monto_uf= {result['monto_uf']!r}")

    # --- Cuenta Contable (Accounting Account) ---
    # Anchor/header: 'Cuenta', 'Contable', 'Centro', 'de', 'Costo', 'Orden', 'Controlling'
    # Anchor/header v2: 'Costo', 'Orden', 'Controlling'
    # The account_id is the token immediately after this header block. 1 token in lenght
    idx = find_anchor(tokens, "Costo", "Orden", "Controlling")
    if idx != -1:
        # Skip the full header v2: 'Costo', 'Orden', 'Controlling' (3 tokens)
        cta_contable_idx = idx + 3  # adjust if your header varies
        result["cuenta_contable"] = tokens[cta_contable_idx]
        logger.debug(f"cuenta_contable= {result['cuenta_contable']!r}")

    # --- Centro de Costo (Cost Center) ---
    # Cost Center starts right after the 'Accounting Account' value, 1 token in lenght
    if "cuenta_contable" in result:
        centro_costo_idx = cta_contable_idx + 1
        result["centro_costo"] = tokens[centro_costo_idx]
        logger.debug(f"centro_costo= {result['centro_costo']!r}")

    # --- Orden Controlling (Controlling Order) ---
    # Orden Controlling starts right after the 'Cost Center' value, 1 token in lenght
    if "centro_costo" in result:
        orden_ctrl_idx = centro_costo_idx + 1
        result["orden_controlling"] = tokens[orden_ctrl_idx]
        logger.debug(f"orden_controlling= {result['orden_controlling']!r}")

    return result