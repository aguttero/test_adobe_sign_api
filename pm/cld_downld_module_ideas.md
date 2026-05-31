# Download Module Scrap Pad

## Doc Lifecycle status(es)
* PENDING
* DOWNLOADED
* PARSED
* TOKENIZED
* PURGED_PDF
* PURGED_TXT

## DESIGN IDEAS

### Prompt:
now i need to build a module that has to parse data from the actual downloaded files from specific agreement types (purchase orders authorizations and contracts) . The endpoint for downloading is  {{base_url}}/api/rest/v6/agreements/{agreementId}/combinedDocument/url?attachAuditReport=true. The Adobe Rest API reference is located here: https://secure.na1.adobesign.com/public/docs/restapi/v6#/agreements. What do you recommend as platform and process to download, store and parse these agreements?

### Prompt Answer:
No worries — I know the `combinedDocument/url` endpoint well enough from the API design. Let me ask one key question before recommending a stack:While you answer those, here is my initial recommendation on the **download and storage** side, which is independent of the parsing goal.

---

## Download layer — how the endpoint works

The `combinedDocument/url` endpoint does **not** return the PDF directly. It returns a **temporary pre-signed URL** (valid for a short window, typically 5 minutes) that you then `GET` to stream the actual PDF bytes. Your code must do two calls per agreement:

```python
# Step 1 — get the temp URL
r = requests.get(
    f"{BASE_URL}/agreements/{agreement_id}/combinedDocument/url",
    headers=get_headers(sender_email),
    params={"attachAuditReport": "true"}
)
download_url = r.json()["url"]

# Step 2 — download the PDF from the temp URL (no auth header needed)
pdf_bytes = requests.get(download_url, timeout=60).content
```

The audit report is appended as an extra page at the end of the PDF — useful for contracts since it records who signed, when, and from which IP.

---

## Storage recommendation — local filesystem + SQLite reference

Since you are already on SQLite and running locally, the simplest architecture is:

```
/storage
  /purchase_orders/
      {agreement_id}.pdf
  /contracts/
      {agreement_id}.pdf
  /authorizations/
      {agreement_id}.pdf
```

Add a `documents` table to SQLite that acts as the index:

```sql
CREATE TABLE IF NOT EXISTS documents (
    agreement_id     TEXT PRIMARY KEY,
    agreement_type   TEXT NOT NULL,  -- purchase_order | contract | authorization
    file_path        TEXT NOT NULL,
    file_size_bytes  INTEGER,
    downloaded_at    TEXT,
    parsed_at        TEXT,
    parse_status     TEXT,           -- pending | success | failed
    FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
);
```

This keeps the filesystem as the blob store (PDFs can be large) and SQLite as the queryable index and parse-status tracker — the same pattern as your existing sync.

---

## Agreement type classification

You will need to classify each agreement as a purchase order, contract, or authorization before routing it to the right parser. The cleanest signal is the agreement `name` field you already have in your `agreements` table. A simple keyword matcher works well as a first pass:

```python
def classify_agreement(name: str) -> str | None:
    name_lower = name.lower()
    if any(k in name_lower for k in ["purchase order", "p.o.", " po "]):
        return "purchase_order"
    if any(k in name_lower for k in ["contract", "agreement", "msa", "nda", "sow"]):
        return "contract"
    if any(k in name_lower for k in ["authorization", "auth", "approval"]):
        return "authorization"
    return None  # unclassified — skip or flag for manual review
```

If your account has consistent naming conventions this will cover most cases. The `workflow_id` column is a stronger signal if workflows are used — a specific workflow ID will always map to one agreement type.

---

Answer the two questions above and I will give you the full parsing stack recommendation (libraries, field extraction approach, and whether you need OCR).

___

Perfect — no OCR needed, and structured field extraction is a well-solved problem for digital PDFs. Here is the full recommendation.

---

## Platform recommendation: Python + `pdfplumber` + Claude API
## AG: TEST FAILED ON PDFPLUMBER
For digitally created PDFs with selectable text, the right stack is:

- **`pdfplumber`** for text and table extraction (better than `PyPDF2` or `pdfminer` for structured content — it preserves layout geometry and can extract tables natively)
- **Claude API (`claude-sonnet-4-20250514`)** as the field extraction engine — you pass the extracted text and ask it to return structured JSON. This is dramatically more robust than regex for real-world contract language where the same field appears in dozens of different phrasings across document types
- **SQLite** for storing extracted fields, keyed to `agreement_id`

The reason to use Claude for extraction rather than pure regex: purchase orders, contracts, and authorizations each have their own vocabulary and layout. A regex that catches "Total Amount: $12,400.00" will miss "Aggregate value not to exceed USD 12,400" or a table cell with no label. Claude reads the document the way a human would.

---

## Schema additions

One parsed fields table per document type keeps queries clean:

```sql
CREATE TABLE IF NOT EXISTS parsed_purchase_orders (
    agreement_id     TEXT PRIMARY KEY,
    po_number        TEXT,
    vendor_name      TEXT,
    buyer_name       TEXT,
    issue_date       TEXT,
    delivery_date    TEXT,
    total_amount     REAL,
    currency         TEXT,
    line_items_json  TEXT,   -- JSON array of {description, qty, unit_price}
    parsed_at        TEXT,
    FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
);

CREATE TABLE IF NOT EXISTS parsed_contracts (
    agreement_id        TEXT PRIMARY KEY,
    contract_title      TEXT,
    party_a             TEXT,
    party_b             TEXT,
    effective_date      TEXT,
    expiration_date     TEXT,
    renewal_terms       TEXT,
    total_value         REAL,
    currency            TEXT,
    governing_law       TEXT,
    parsed_at           TEXT,
    FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
);

CREATE TABLE IF NOT EXISTS parsed_authorizations (
    agreement_id        TEXT PRIMARY KEY,
    authorizing_party   TEXT,
    authorized_party    TEXT,
    authorization_scope TEXT,
    effective_date      TEXT,
    expiration_date     TEXT,
    amount_limit        REAL,
    currency            TEXT,
    parsed_at           TEXT,
    FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
);
```

---

## Full parsing module

```python
import os, json, re, sqlite3, logging
from datetime import datetime, timezone
from pathlib import Path
import requests
import pdfplumber

BASE_URL    = "https://api.na1.adobesign.com/api/rest/v6"
DB_PATH     = os.environ.get("DB_PATH", "agreements.db")
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "storage"))
ADMIN_TOKEN = os.environ["ADOBE_SIGN_TOKEN"]

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ── 1. Download ───────────────────────────────────────────────────────────────

def get_headers(sender_email: str) -> dict:
    return {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "x-api-user": f"user:email:{sender_email}",
    }


def download_agreement_pdf(agreement_id: str, sender_email: str, agreement_type: str) -> Path:
    """Download combined PDF (with audit report) and save to storage. Returns local path."""
    dest_dir = STORAGE_DIR / agreement_type
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{agreement_id}.pdf"

    if dest_path.exists():
        log.info("Already downloaded: %s", dest_path)
        return dest_path

    # Step 1 — get temp URL
    r = requests.get(
        f"{BASE_URL}/agreements/{agreement_id}/combinedDocument/url",
        headers=get_headers(sender_email),
        params={"attachAuditReport": "true"},
        timeout=30,
    )
    r.raise_for_status()
    temp_url = r.json()["url"]

    # Step 2 — stream PDF bytes (no auth header on this call)
    pdf_resp = requests.get(temp_url, timeout=60, stream=True)
    pdf_resp.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in pdf_resp.iter_content(chunk_size=8192):
            f.write(chunk)

    log.info("Downloaded %s → %s (%d bytes)", agreement_id, dest_path, dest_path.stat().st_size)
    return dest_path


# ── 2. Text extraction ────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a digital PDF, preserving layout and tables."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Extract tables first (pdfplumber detects table structure)
            tables = page.extract_tables()
            table_text = ""
            for table in tables:
                for row in table:
                    clean_row = [cell or "" for cell in row]
                    table_text += " | ".join(clean_row) + "\n"

            # Extract remaining text (non-table regions)
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages.append(f"--- Page {i+1} ---\n{text}\n{table_text}")

    return "\n".join(pages)


# ── 3. Claude-powered field extraction ───────────────────────────────────────

PROMPTS = {
    "purchase_order": """
You are a data extraction assistant. Extract the following fields from this purchase order document.
Return ONLY a valid JSON object with these exact keys — no preamble, no markdown.
If a field is not found, use null.

Fields:
- po_number: string
- vendor_name: string
- buyer_name: string
- issue_date: string (ISO 8601 if possible, else as written)
- delivery_date: string (ISO 8601 if possible, else as written)
- total_amount: number (numeric value only, no currency symbols)
- currency: string (3-letter ISO code, e.g. USD, EUR, CLP)
- line_items: array of objects with keys: description (string), quantity (number), unit_price (number)

Document text:
""",
    "contract": """
You are a data extraction assistant. Extract the following fields from this contract document.
Return ONLY a valid JSON object with these exact keys — no preamble, no markdown.
If a field is not found, use null.

Fields:
- contract_title: string
- party_a: string (first named party)
- party_b: string (second named party)
- effective_date: string (ISO 8601 if possible)
- expiration_date: string (ISO 8601 if possible)
- renewal_terms: string (brief description of auto-renewal or renewal notice clauses)
- total_value: number (numeric value only, no currency symbols)
- currency: string (3-letter ISO code)
- governing_law: string (jurisdiction)

Document text:
""",
    "authorization": """
You are a data extraction assistant. Extract the following fields from this authorization document.
Return ONLY a valid JSON object with these exact keys — no preamble, no markdown.
If a field is not found, use null.

Fields:
- authorizing_party: string
- authorized_party: string
- authorization_scope: string (brief description of what is authorized)
- effective_date: string (ISO 8601 if possible)
- expiration_date: string (ISO 8601 if possible)
- amount_limit: number (numeric value only, if a monetary limit is stated)
- currency: string (3-letter ISO code)

Document text:
""",
}


def extract_fields_with_claude(text: str, agreement_type: str) -> dict:
    """Send extracted PDF text to Claude and get structured fields back."""
    prompt = PROMPTS[agreement_type] + text[:12000]  # stay within token budget

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    raw = response.json()["content"][0]["text"].strip()

    # Strip accidental markdown fences
    raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


# ── 4. Persist parsed fields ──────────────────────────────────────────────────

def persist_parsed_fields(conn: sqlite3.Connection, agreement_id: str,
                           agreement_type: str, fields: dict):
    now = datetime.now(timezone.utc).isoformat()

    if agreement_type == "purchase_order":
        conn.execute("""
            INSERT OR REPLACE INTO parsed_purchase_orders
            (agreement_id, po_number, vendor_name, buyer_name, issue_date,
             delivery_date, total_amount, currency, line_items_json, parsed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            agreement_id,
            fields.get("po_number"),
            fields.get("vendor_name"),
            fields.get("buyer_name"),
            fields.get("issue_date"),
            fields.get("delivery_date"),
            fields.get("total_amount"),
            fields.get("currency"),
            json.dumps(fields.get("line_items") or []),
            now,
        ))

    elif agreement_type == "contract":
        conn.execute("""
            INSERT OR REPLACE INTO parsed_contracts
            (agreement_id, contract_title, party_a, party_b, effective_date,
             expiration_date, renewal_terms, total_value, currency, governing_law, parsed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            agreement_id,
            fields.get("contract_title"),
            fields.get("party_a"),
            fields.get("party_b"),
            fields.get("effective_date"),
            fields.get("expiration_date"),
            fields.get("renewal_terms"),
            fields.get("total_value"),
            fields.get("currency"),
            fields.get("governing_law"),
            now,
        ))

    elif agreement_type == "authorization":
        conn.execute("""
            INSERT OR REPLACE INTO parsed_authorizations
            (agreement_id, authorizing_party, authorized_party, authorization_scope,
             effective_date, expiration_date, amount_limit, currency, parsed_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            agreement_id,
            fields.get("authorizing_party"),
            fields.get("authorized_party"),
            fields.get("authorization_scope"),
            fields.get("effective_date"),
            fields.get("expiration_date"),
            fields.get("amount_limit"),
            fields.get("currency"),
            now,
        ))

    conn.commit()


# ── 5. Main pipeline ──────────────────────────────────────────────────────────

def run_parsing_pipeline(agreement_types: list[str] | None = None):
    """
    Download and parse all agreements of the given types.
    Defaults to all three types if none specified.
    Skips already-parsed agreements (parse_status = 'success').
    """
    if agreement_types is None:
        agreement_types = ["purchase_order", "contract", "authorization"]

    conn = sqlite3.connect(DB_PATH)
    _init_parse_tables(conn)

    placeholders = ",".join("?" * len(agreement_types))
    rows = conn.execute(f"""
        SELECT a.agreement_id, a.sender_email, d.agreement_type
        FROM agreements a
        JOIN documents d ON a.agreement_id = d.agreement_id
        WHERE d.agreement_type IN ({placeholders})
          AND (d.parse_status IS NULL OR d.parse_status = 'failed')
        ORDER BY a.created_date DESC
    """, agreement_types).fetchall()

    log.info("Found %d agreements to parse", len(rows))

    for agreement_id, sender_email, agreement_type in rows:
        log.info("Processing %s (%s)", agreement_id, agreement_type)
        try:
            # Download
            pdf_path = download_agreement_pdf(agreement_id, sender_email, agreement_type)
            _update_doc_status(conn, agreement_id, pdf_path, "pending")

            # Extract text
            text = extract_text_from_pdf(pdf_path)
            if not text.strip():
                raise ValueError("No text extracted — may be a scanned PDF")

            # Parse fields
            fields = extract_fields_with_claude(text, agreement_type)

            # Persist
            persist_parsed_fields(conn, agreement_id, agreement_type, fields)
            _update_doc_status(conn, agreement_id, pdf_path, "success")
            log.info("  → parsed OK: %s", list(fields.keys()))

        except Exception as e:
            log.error("  → failed: %s", e)
            _update_doc_status(conn, agreement_id, None, "failed", str(e))

    conn.close()


def _update_doc_status(conn, agreement_id, pdf_path, status, error=None):
    now = datetime.now(timezone.utc).isoformat()
    if pdf_path:
        conn.execute("""
            INSERT INTO documents (agreement_id, file_path, file_size_bytes,
                                   downloaded_at, parse_status)
            VALUES (?,?,?,?,?)
            ON CONFLICT(agreement_id) DO UPDATE SET
                file_path=excluded.file_path,
                file_size_bytes=excluded.file_size_bytes,
                downloaded_at=excluded.downloaded_at,
                parse_status=excluded.parse_status
        """, (agreement_id, str(pdf_path),
              pdf_path.stat().st_size if pdf_path.exists() else None, now, status))
    else:
        conn.execute("""
            UPDATE documents SET parse_status=?, parsed_at=? WHERE agreement_id=?
        """, (status, now, agreement_id))
    if status == "success":
        conn.execute("UPDATE documents SET parsed_at=? WHERE agreement_id=?", (now, agreement_id))
    conn.commit()


def _init_parse_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS parsed_purchase_orders (
            agreement_id TEXT PRIMARY KEY, po_number TEXT, vendor_name TEXT,
            buyer_name TEXT, issue_date TEXT, delivery_date TEXT,
            total_amount REAL, currency TEXT, line_items_json TEXT, parsed_at TEXT,
            FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
        );
        CREATE TABLE IF NOT EXISTS parsed_contracts (
            agreement_id TEXT PRIMARY KEY, contract_title TEXT, party_a TEXT,
            party_b TEXT, effective_date TEXT, expiration_date TEXT,
            renewal_terms TEXT, total_value REAL, currency TEXT,
            governing_law TEXT, parsed_at TEXT,
            FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
        );
        CREATE TABLE IF NOT EXISTS parsed_authorizations (
            agreement_id TEXT PRIMARY KEY, authorizing_party TEXT,
            authorized_party TEXT, authorization_scope TEXT,
            effective_date TEXT, expiration_date TEXT,
            amount_limit REAL, currency TEXT, parsed_at TEXT,
            FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
        );
    """)


if __name__ == "__main__":
    import sys
    types = sys.argv[1:] or None  # e.g. python parser.py purchase_order contract
    run_parsing_pipeline(types)
```

---

## Key design decisions explained

**Why `pdfplumber` over alternatives.** `PyPDF2` extracts text but loses table structure entirely — amounts in a PO line-items table come out as a jumbled string. `pdfplumber` detects table geometry and gives you rows and cells. For contracts with clause numbering and indented text it also preserves spatial relationships better than `pdfminer` directly.

**Why Claude for field extraction rather than regex.** The same field appears in too many surface forms across real documents. PO numbers alone can appear as "PO #", "Purchase Order Number:", "P.O.:", "Order Ref", or unlabeled in a header cell. Regex maintenance becomes a full-time job. The Claude prompt approach handles all of these and generalizes to documents you haven't seen yet. The `text[:12000]` slice keeps you well within the token budget for the extraction task — most contracts fit in that window, and the critical fields (parties, dates, amounts) appear in the first few pages.

**Why `text` not PDF bytes as Claude input.** You could send the PDF as a base64 document to Claude's document API, but that consumes significantly more tokens and is slower. Since your PDFs are digitally created with selectable text, `pdfplumber` extraction is lossless — you get the same information at a fraction of the cost.

**Idempotency.** The pipeline skips any agreement where `parse_status = 'success'` and retries `failed` ones. Re-running after a partial failure or API timeout is safe.

---

## Installation

```bash
pip install pdfplumber requests
```

No other dependencies needed — `pdfplumber` bundles `pdfminer.six` internally.

# Contract Agreement use case

This changes the extraction approach significantly. An unstructured contract — no labeled fields, no consistent layout — means `pdfplumber` alone is not enough. You need to treat the full document as a reading comprehension problem, not a data extraction problem. Claude is the right engine for this, but the prompting strategy needs to be more sophisticated than what we have now.

Let me ask one clarifying question first:While you answer — here is the core architectural shift this use case requires.

---

## The fundamental problem with unstructured contracts

A structured document has landmarks — a field label followed by a value. An unstructured contract buries the same information in prose clauses, legalese, and cross-references. For example:

- **Activation date** might appear as *"This Agreement shall become effective upon execution by both parties"* with the actual date only in the signature block three pages later
- **Exit clause** might be scattered across three separate clauses: one defining the right, one defining the notice period, one defining the penalties
- **Auto-renewal** might read *"unless either party provides written notice of non-renewal no fewer than sixty (60) days prior to the expiration of the then-current term"* — the trigger date is derived, not stated

No regex, no layout parser, and no simple prompt will reliably extract these. The right approach is a **multi-pass extraction pipeline** using Claude with contract-specific prompting strategies.

---

## Recommended architecture: multi-pass Claude extraction

```
PDF bytes
    ↓
pdfplumber → full text (preserve page breaks)
    ↓
Pass 1 — Segmentation:   Claude splits the contract into named sections
    ↓
Pass 2 — Field extraction: Claude extracts structured fields per section
    ↓
Pass 3 — Derived fields:   Claude computes trigger dates from stated terms
    ↓
Pass 4 — Confidence scoring: Claude flags low-confidence extractions for review
    ↓
SQLite parsed_contracts table
```

The segmentation pass is the key addition. Rather than throwing the full contract text at Claude and asking for everything at once, you first ask Claude to locate *where* each concept lives in the document. Then you extract from those targeted segments. This improves accuracy significantly for long documents and makes the confidence scoring meaningful.

---

## Expanded schema

```sql
CREATE TABLE IF NOT EXISTS parsed_contracts (
    agreement_id            TEXT PRIMARY KEY,

    -- Parties
    party_a_name            TEXT,
    party_a_tax_id          TEXT,
    party_a_role            TEXT,   -- e.g. "Proveedor", "Cliente", "Licenciante"
    party_b_name            TEXT,
    party_b_tax_id          TEXT,
    party_b_role            TEXT,

    -- Core terms
    contract_objective      TEXT,   -- brief summary of purpose
    activation_date         TEXT,   -- ISO 8601 or as written
    contract_term_months    INTEGER,
    contract_term_text      TEXT,   -- raw text describing the term
    expiration_date         TEXT,

    -- Renewal
    auto_renewal            INTEGER, -- 0/1 boolean
    renewal_period_months   INTEGER,
    renewal_period_text     TEXT,
    auto_renewal_trigger_date TEXT,  -- date by which notice must be given
    renewal_notice_days     INTEGER, -- days prior to expiry notice must be sent

    -- Exit clause
    exit_clause_exists      INTEGER, -- 0/1
    exit_clause_summary     TEXT,
    exit_notice_days        INTEGER,
    exit_activation_date    TEXT,    -- earliest date exit can be invoked
    exit_penalty_text       TEXT,

    -- Governing terms
    governing_law           TEXT,
    total_value             REAL,
    currency                TEXT,

    -- Extraction metadata
    confidence_parties      TEXT,    -- high / medium / low
    confidence_dates        TEXT,
    confidence_exit         TEXT,
    confidence_renewal      TEXT,
    low_confidence_notes    TEXT,    -- free text flags for human review
    raw_extraction_json     TEXT,    -- full Claude response for audit
    parsed_at               TEXT,

    FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
);
```

---

## Multi-pass extraction module

```python
import os, json, re, sqlite3, logging
from datetime import datetime, timezone
from pathlib import Path
import requests
import pdfplumber

log = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 2000


def call_claude(prompt: str, max_tokens: int = MAX_TOKENS) -> str:
    response = requests.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    response.raise_for_status()
    raw = response.json()["content"][0]["text"].strip()
    return re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()


def extract_text_with_pages(pdf_path: Path) -> str:
    """Extract text preserving page markers — important for long contracts."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            table_text = ""
            for table in tables:
                for row in table:
                    table_text += " | ".join(cell or "" for cell in row) + "\n"
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages.append(f"[PAGE {i+1}]\n{text}\n{table_text}")
    return "\n".join(pages)


# ── Pass 1: Segmentation ──────────────────────────────────────────────────────

SEGMENTATION_PROMPT = """
You are a legal document analyst. Read the contract below and identify the exact 
location of the following sections. For each section, return the verbatim text 
excerpt (up to 400 words) most relevant to that topic.

Return ONLY a valid JSON object with these keys. If a section is not found, 
use null for its value.

Keys:
- parties_section: text identifying both contracting parties and their tax IDs / RUT / NIT
- objective_section: text describing the purpose or object of the contract
- term_section: text describing the contract duration, start date, and end date
- renewal_section: text describing auto-renewal, renewal periods, and notice deadlines
- exit_clause_section: text describing termination rights, exit conditions, notice periods, and penalties
- governing_law_section: text describing jurisdiction or applicable law
- value_section: text describing the contract value, fees, or payment amounts

Contract:
"""


def segment_contract(text: str) -> dict:
    """Pass 1 — locate and extract relevant sections from the full contract text."""
    # For very long contracts, send in chunks if needed
    # Claude's context handles ~100k tokens but we trim to keep costs low
    prompt = SEGMENTATION_PROMPT + text[:30000]
    raw = call_claude(prompt, max_tokens=3000)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Segmentation JSON parse failed, using full text fallback")
        return {"_full_text": text[:30000]}


# ── Pass 2: Field extraction ──────────────────────────────────────────────────

EXTRACTION_PROMPT = """
You are a contract data extraction specialist. Using ONLY the contract sections 
provided below, extract the specified fields.

Return ONLY a valid JSON object. Use null for any field not determinable from 
the text. Do not invent or infer values not present in the text.

Fields to extract:

PARTIES:
- party_a_name: full legal name of first party
- party_a_tax_id: tax ID / RUT / NIT / RFC of first party
- party_a_role: role label as stated in the contract (e.g. Proveedor, Licensor)
- party_b_name: full legal name of second party
- party_b_tax_id: tax ID / RUT / NIT / RFC of second party
- party_b_role: role label as stated in the contract

CONTRACT TERMS:
- contract_objective: one sentence summarizing the purpose of the contract
- activation_date: the date the contract becomes effective (ISO 8601 if possible)
- contract_term_months: duration in months as an integer (null if stated differently)
- contract_term_text: the raw text describing the duration
- expiration_date: the date the contract expires (ISO 8601 if possible)

RENEWAL:
- auto_renewal: true or false
- renewal_period_months: renewal period in months as integer
- renewal_period_text: raw text describing the renewal period
- renewal_notice_days: number of days prior to expiry that notice must be given
- auto_renewal_trigger_date: the calendar date by which notice must be sent to 
  prevent auto-renewal (ISO 8601 — derive from expiration_date minus 
  renewal_notice_days if both are available, otherwise null)

EXIT CLAUSE:
- exit_clause_exists: true or false
- exit_clause_summary: plain-language summary of exit rights (2-3 sentences)
- exit_notice_days: days of notice required to invoke exit clause
- exit_activation_date: earliest calendar date the exit clause can be invoked 
  (ISO 8601 if determinable)
- exit_penalty_text: description of any penalties or fees for early exit

OTHER:
- governing_law: jurisdiction or applicable law
- total_value: numeric contract value (no currency symbols)
- currency: 3-letter ISO currency code

Contract sections:
"""


def extract_fields(segments: dict) -> dict:
    """Pass 2 — extract structured fields from the located segments."""
    # Concatenate only the non-null segments for the extraction prompt
    sections_text = ""
    for key, value in segments.items():
        if value and key != "_full_text":
            label = key.replace("_section", "").replace("_", " ").upper()
            sections_text += f"\n\n=== {label} ===\n{value}"

    # Fallback: if segmentation failed, use full text
    if not sections_text and "_full_text" in segments:
        sections_text = segments["_full_text"]

    prompt = EXTRACTION_PROMPT + sections_text
    raw = call_claude(prompt, max_tokens=2000)
    return json.loads(raw)


# ── Pass 3: Confidence scoring ────────────────────────────────────────────────

CONFIDENCE_PROMPT = """
You are a quality control reviewer for contract data extraction.

Review the extracted fields below against the source contract sections.
For each confidence group, assign: "high", "medium", or "low".

- high: the value is explicitly stated in the text with no ambiguity
- medium: the value is reasonably inferred but not explicitly labeled
- low: the value is uncertain, derived from incomplete information, or missing

Also provide a brief note (1-2 sentences) for any low-confidence field 
explaining what is unclear and what a human reviewer should check.

Return ONLY a valid JSON object with these keys:
- confidence_parties: high/medium/low
- confidence_dates: high/medium/low
- confidence_exit: high/medium/low
- confidence_renewal: high/medium/low
- low_confidence_notes: string (null if all high)

Extracted fields:
{fields}

Source sections:
{sections}
"""


def score_confidence(fields: dict, segments: dict) -> dict:
    """Pass 3 — score extraction confidence and flag uncertain fields."""
    sections_summary = {k: v[:500] if v else None for k, v in segments.items()
                        if k != "_full_text"}
    prompt = CONFIDENCE_PROMPT.format(
        fields=json.dumps(fields, indent=2),
        sections=json.dumps(sections_summary, indent=2)
    )
    raw = call_claude(prompt, max_tokens=500)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "confidence_parties": "low",
            "confidence_dates": "low",
            "confidence_exit": "low",
            "confidence_renewal": "low",
            "low_confidence_notes": "Confidence scoring failed — manual review required"
        }


# ── Pass 4: Persist ───────────────────────────────────────────────────────────

def persist_contract(conn: sqlite3.Connection, agreement_id: str,
                     fields: dict, confidence: dict, raw_json: str):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO parsed_contracts (
            agreement_id,
            party_a_name, party_a_tax_id, party_a_role,
            party_b_name, party_b_tax_id, party_b_role,
            contract_objective, activation_date,
            contract_term_months, contract_term_text, expiration_date,
            auto_renewal, renewal_period_months, renewal_period_text,
            renewal_notice_days, auto_renewal_trigger_date,
            exit_clause_exists, exit_clause_summary, exit_notice_days,
            exit_activation_date, exit_penalty_text,
            governing_law, total_value, currency,
            confidence_parties, confidence_dates,
            confidence_exit, confidence_renewal,
            low_confidence_notes, raw_extraction_json, parsed_at
        ) VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
    """, (
        agreement_id,
        fields.get("party_a_name"),      fields.get("party_a_tax_id"),
        fields.get("party_a_role"),
        fields.get("party_b_name"),      fields.get("party_b_tax_id"),
        fields.get("party_b_role"),
        fields.get("contract_objective"), fields.get("activation_date"),
        fields.get("contract_term_months"), fields.get("contract_term_text"),
        fields.get("expiration_date"),
        1 if fields.get("auto_renewal") else 0,
        fields.get("renewal_period_months"), fields.get("renewal_period_text"),
        fields.get("renewal_notice_days"),   fields.get("auto_renewal_trigger_date"),
        1 if fields.get("exit_clause_exists") else 0,
        fields.get("exit_clause_summary"),   fields.get("exit_notice_days"),
        fields.get("exit_activation_date"),  fields.get("exit_penalty_text"),
        fields.get("governing_law"),
        fields.get("total_value"),           fields.get("currency"),
        confidence.get("confidence_parties"),
        confidence.get("confidence_dates"),
        confidence.get("confidence_exit"),
        confidence.get("confidence_renewal"),
        confidence.get("low_confidence_notes"),
        raw_json, now,
    ))
    conn.commit()


# ── Orchestrator ──────────────────────────────────────────────────────────────

def parse_contract(pdf_path: Path, agreement_id: str,
                   conn: sqlite3.Connection) -> bool:
    """Full multi-pass extraction for a single contract PDF."""
    try:
        log.info("[%s] Extracting text...", agreement_id)
        text = extract_text_with_pages(pdf_path)
        if not text.strip():
            raise ValueError("Empty text extraction")

        log.info("[%s] Pass 1 — segmenting...", agreement_id)
        segments = segment_contract(text)

        log.info("[%s] Pass 2 — extracting fields...", agreement_id)
        fields = extract_fields(segments)

        log.info("[%s] Pass 3 — scoring confidence...", agreement_id)
        confidence = score_confidence(fields, segments)

        raw_json = json.dumps({"fields": fields, "confidence": confidence,
                               "segments": {k: bool(v) for k, v in segments.items()}})

        persist_contract(conn, agreement_id, fields, confidence, raw_json)

        low = confidence.get("low_confidence_notes")
        if low:
            log.warning("[%s] Low confidence flags: %s", agreement_id, low)

        return True

    except Exception as e:
        log.error("[%s] Parsing failed: %s", agreement_id, e)
        return False
```

---

## How the three passes work together

**Pass 1 — segmentation** reads the full document and returns only the relevant excerpts for each concept. This is the most important pass. A 40-page contract becomes 7 focused text blocks. All subsequent passes work on those blocks, not the full document.

**Pass 2 — field extraction** works on the targeted segments. Because it is already looking at the right clause, it does not need to reason about document structure — it only needs to read and convert. This is where the derived fields like `auto_renewal_trigger_date` are computed: Claude subtracts the notice period from the expiration date rather than you doing that in Python.

**Pass 3 — confidence scoring** sends both the extracted fields and the source segments back to Claude and asks it to audit its own work. Low-confidence flags go into `low_confidence_notes` as a human review queue. Any contract with a `low` confidence on dates or exit clauses should be reviewed before being used operationally.

---

## Human review query

After a sync run, pull everything that needs review:

```sql
SELECT
    a.agreement_id,
    a.name,
    a.sender_email,
    c.party_a_name,
    c.party_b_name,
    c.confidence_parties,
    c.confidence_dates,
    c.confidence_exit,
    c.confidence_renewal,
    c.low_confidence_notes
FROM parsed_contracts c
JOIN agreements a ON a.agreement_id = c.agreement_id
WHERE 'low' IN (c.confidence_parties, c.confidence_dates,
                c.confidence_exit, c.confidence_renewal)
ORDER BY c.parsed_at DESC;
```
---
## Question
Q: What language are the contracts written in?
A: Spanish only
---
Good — Spanish-only simplifies things. The prompts need to be rewritten in Spanish, and the model needs to handle Spanish legal terminology correctly. This matters more than it might seem: Chilean/Latin American contracts use specific terms like **RUT**, **objeto del contrato**, **plazo de vigencia**, **cláusula de salida**, **renovación automática**, and **multa por término anticipado** that a generic English prompt will miss or misclassify.

Here are the targeted changes to the module above.

---

## What changes and why

**The segmentation prompt must be in Spanish.** The model locates sections by matching the language and structure of the source document. An English prompt asking for "exit clause" will underperform against a clause titled "Cláusula de Término Anticipado" or "Rescisión del Contrato." Prompting in Spanish dramatically improves section location accuracy.

**Tax ID terminology.** Chile uses **RUT** (Rol Único Tributario). Other Latin American countries use NIT (Colombia), RFC (Mexico), RUC (Perú/Ecuador). Since you confirmed Spanish-only and given you are based in Santiago, RUT is the primary target — but the prompt should also catch the others in case you have cross-border contracts.

**Date formats.** Spanish contracts write dates as *"15 de marzo de 2024"* or *"15/03/2024"* — Claude should normalize these to ISO 8601 in the output, which the current extraction prompt already requests but needs to handle Spanish month names explicitly.

**Legal term mapping.** The key terms to target by name in the prompts:

| Concept | Typical Spanish terms |
|---|---|
| Contract objective | objeto del contrato, materia del contrato |
| Activation date | fecha de entrada en vigencia, fecha de inicio |
| Contract term | plazo de vigencia, duración del contrato |
| Auto-renewal | renovación automática, prórroga automática |
| Renewal notice | aviso de no renovación, notificación de término |
| Exit clause | cláusula de salida, término anticipado, rescisión |
| Exit notice | plazo de aviso previo, preaviso |
| Exit penalty | multa, indemnización por término anticipado |
| Governing law | ley aplicable, jurisdicción, tribunales competentes |

---

## Revised prompts — Spanish

Replace the three prompt constants in the module with these:

```python
SEGMENTATION_PROMPT = """
Eres un analista de documentos legales en español. Lee el contrato a continuación 
e identifica la ubicación exacta de las siguientes secciones. Para cada sección, 
devuelve el texto verbatim más relevante (hasta 400 palabras).

Devuelve ÚNICAMENTE un objeto JSON válido con estas claves. Si una sección no 
existe en el documento, usa null como valor.

Claves:
- seccion_partes: texto que identifica a ambas partes contratantes, incluyendo 
  razón social, RUT u otro identificador tributario
- seccion_objeto: texto que describe el objeto o propósito del contrato
- seccion_plazo: texto que describe la duración, fecha de inicio y fecha de término
- seccion_renovacion: texto sobre renovación automática, prórroga, períodos de 
  renovación y plazos de aviso para no renovar
- seccion_termino_anticipado: texto sobre cláusula de salida, término anticipado, 
  rescisión, causales, plazos de preaviso y multas o indemnizaciones
- seccion_ley_aplicable: texto sobre jurisdicción, ley aplicable y tribunales competentes
- seccion_valor: texto sobre el valor del contrato, honorarios, precios o montos de pago

Contrato:
"""


EXTRACTION_PROMPT = """
Eres un especialista en extracción de datos de contratos en español. Usando 
ÚNICAMENTE las secciones del contrato proporcionadas a continuación, extrae 
los campos especificados.

Devuelve ÚNICAMENTE un objeto JSON válido. Usa null para cualquier campo que 
no pueda determinarse a partir del texto. No inventes ni inferyas valores que 
no estén presentes en el texto.

Campos a extraer:

PARTES:
- party_a_name: nombre o razón social completa de la primera parte
- party_a_tax_id: RUT, NIT, RFC, RUC u otro identificador tributario de la primera parte
- party_a_role: rol de la primera parte según el contrato (ej: Proveedor, Mandante, 
  Licenciante, Cliente, Arrendador)
- party_b_name: nombre o razón social completa de la segunda parte
- party_b_tax_id: RUT, NIT, RFC, RUC u otro identificador tributario de la segunda parte
- party_b_role: rol de la segunda parte según el contrato

TÉRMINOS DEL CONTRATO:
- contract_objective: resumen en una oración del objeto o propósito del contrato
- activation_date: fecha en que el contrato entra en vigencia (ISO 8601 si es posible, 
  de lo contrario tal como está escrito). Buscar frases como "entrará en vigencia", 
  "fecha de inicio", "a partir del"
- contract_term_months: duración en meses como número entero (null si se expresa 
  de otra forma)
- contract_term_text: texto original que describe la duración del contrato
- expiration_date: fecha de término del contrato (ISO 8601 si es posible)

RENOVACIÓN:
- auto_renewal: true si existe renovación o prórroga automática, false si no existe
- renewal_period_months: período de renovación en meses como número entero
- renewal_period_text: texto original que describe el período de renovación
- renewal_notice_days: días de anticipación con que se debe dar aviso para 
  no renovar (buscar "días de anticipación", "días hábiles antes del vencimiento", 
  "preaviso de no renovación")
- auto_renewal_trigger_date: fecha calendario límite para dar aviso y evitar 
  la renovación automática (ISO 8601 — calcular restando renewal_notice_days 
  a expiration_date si ambos están disponibles, de lo contrario null)

CLÁUSULA DE SALIDA / TÉRMINO ANTICIPADO:
- exit_clause_exists: true si existe cláusula de término anticipado o salida, 
  false si no existe
- exit_clause_summary: resumen en lenguaje simple de los derechos de término 
  anticipado (2-3 oraciones)
- exit_notice_days: días de preaviso requeridos para ejercer el término anticipado
- exit_activation_date: fecha calendario más temprana en que puede ejercerse 
  el término anticipado (ISO 8601 si puede determinarse)
- exit_penalty_text: descripción de multas, indemnizaciones o penalidades por 
  término anticipado

OTROS:
- governing_law: jurisdicción o ley aplicable (ej: "Ley chilena, Tribunales de Santiago")
- total_value: valor numérico del contrato sin símbolos de moneda
- currency: código ISO de 3 letras (CLP, USD, EUR, UF — nota: UF es unidad de 
  fomento chilena, tratar como currency code "UF")

Secciones del contrato:
"""


CONFIDENCE_PROMPT = """
Eres un revisor de control de calidad para extracción de datos de contratos en español.

Revisa los campos extraídos a continuación comparándolos con las secciones 
fuente del contrato. Para cada grupo de confianza, asigna: "high", "medium" o "low".

- high: el valor está explícitamente indicado en el texto sin ambigüedad
- medium: el valor se infiere razonablemente pero no está etiquetado explícitamente
- low: el valor es incierto, derivado de información incompleta, o no encontrado

Para cualquier campo con confianza baja, incluye una nota breve (1-2 oraciones) 
explicando qué es incierto y qué debe verificar un revisor humano. Escribe las 
notas en español.

Devuelve ÚNICAMENTE un objeto JSON válido con estas claves:
- confidence_parties: high/medium/low
- confidence_dates: high/medium/low
- confidence_exit: high/medium/low
- confidence_renewal: high/medium/low
- low_confidence_notes: string en español (null si todo es high)

Campos extraídos:
{fields}

Secciones fuente:
{sections}
"""
```

---

## One additional consideration: UF (Unidad de Fomento)

Chilean contracts frequently express values in **UF** rather than CLP or USD — especially for longer-term service contracts and leases. UF is an inflation-indexed unit; its CLP value changes daily. Your schema stores `currency = "UF"` and `total_value` as the UF amount, which is correct for the contract record. If you ever need to report values in CLP you will need to fetch the UF value for a specific date from the CMF API (`https://api.cmfchile.cl/api-sbifv3/recursos_api/uf`), but that is a reporting concern, not a parsing concern. The extraction module handles it correctly as-is.

---

## Nothing else changes

The Python orchestration logic — `parse_contract()`, `segment_contract()`, `extract_fields()`, `score_confidence()`, `persist_contract()` — stays exactly as written. Only the three prompt strings are replaced. The segmentation keys also change (from `parties_section` to `seccion_partes` etc.) so update the `extract_fields` function's section label formatting:

```python
# In extract_fields(), replace the label formatting line with:
label = key.replace("seccion_", "").replace("_", " ").upper()
```

And update the segment key references in `score_confidence` accordingly — since it passes the full `segments` dict as JSON, no other change is needed there.

__
## AG QUESTION PERSIST STRATEGY:
Does it make sense to create a separate table to store downloaded document paths? Should I add these fields to the existing agreemt table? what are the pros and cons?

___
Good design question. Here is a direct analysis.

---

## Option A — Separate `documents` table

```sql
CREATE TABLE documents (
    agreement_id     TEXT PRIMARY KEY,
    agreement_type   TEXT,
    file_path        TEXT,
    file_size_bytes  INTEGER,
    downloaded_at    TEXT,
    parse_status     TEXT,
    parsed_at        TEXT,
    FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
);
```

**Pros**
- The `agreements` table stays focused on API metadata. The `documents` table owns the file lifecycle. Each table has one clear responsibility.
- You can have agreements with no downloaded document (not all agreements need parsing — only purchase orders, contracts, and authorizations). A separate table means no nullable columns on the main table for records that will never have a file.
- Parse status and file path are operationally different from agreement metadata — they change frequently during processing while agreement fields are stable after sync. Separating them avoids touching the main table during parse runs.
- Easier to drop and rebuild the documents table if you change your storage strategy without affecting the agreements table.
- If you later add multiple documents per agreement (e.g. individual participant documents in addition to the combined PDF), the table extends naturally with a composite key.

**Cons**
- Every query that needs both agreement metadata and file path requires a JOIN.
- One more table to manage.

---

## Option B — Add columns to `agreements`

```sql
ALTER TABLE agreements ADD COLUMN file_path        TEXT;
ALTER TABLE agreements ADD COLUMN file_size_bytes  INTEGER;
ALTER TABLE agreements ADD COLUMN downloaded_at    TEXT;
ALTER TABLE agreements ADD COLUMN parse_status     TEXT;
ALTER TABLE agreements ADD COLUMN parsed_at        TEXT;
```

**Pros**
- Simpler — everything about an agreement in one place.
- No JOIN needed for the common case of "give me this agreement and its file path."

**Cons**
- Most rows will have null file columns permanently — you are only downloading 3 of however many agreement types exist in the account.
- The `agreements` table is populated by the sync pipeline and the file columns are populated by the download pipeline. Two different processes writing to the same table creates contention and makes it harder to reason about what each pipeline owns.
- `parse_status` is a processing concern, not an agreement property. Mixing processing state into a data table is a design smell that tends to accumulate over time — you end up adding `retry_count`, `error_message`, `last_attempt_at` and the table becomes a job queue hybrid.

---

## Recommendation

**Keep them separate.** The deciding factor for your specific case is that only a subset of agreements will ever have documents — the three agreement types you are parsing. Adding file columns to the main table means the majority of rows carry permanent nulls for those columns, which is a signal that the data does not belong there.

The JOIN cost is negligible for SQLite at your scale, and the operational clarity of having the sync pipeline own `agreements` and the download pipeline own `documents` is worth it. The schema you already have in the module is correct as designed.

The one refinement worth making to the existing `documents` table is adding an `error_message` column so failed downloads have their reason recorded without needing the `error_log` table for that:

```sql
CREATE TABLE IF NOT EXISTS documents (
    agreement_id      TEXT PRIMARY KEY,
    agreement_type    TEXT NOT NULL,
    file_path         TEXT,
    file_size_bytes   INTEGER,
    downloaded_at     TEXT,
    parse_status      TEXT CHECK(parse_status IN ('pending','success','failed')),
    parsed_at         TEXT,
    error_message     TEXT,
    FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
);
```
## AG QUESTION
and  where should i store the parsed fields of the documents?
___
Same logic applies — separate tables, one per agreement type. You already have this in the module (`parsed_contracts`, `parsed_purchase_orders`, `parsed_authorizations`), and it is the right call. Here is the reasoning laid out explicitly.

---

## Why separate parsed tables, not columns on `agreements` or `documents`

**The fields are completely different per type.** A purchase order has `po_number`, `line_items`, `delivery_date`. A contract has `exit_clause_summary`, `auto_renewal_trigger_date`, `governing_law`. There is no meaningful overlap. Putting them all in one table means either dozens of nullable columns or a generic key-value store — both are worse than three clean tables.

**The parsing pipeline owns these tables exclusively.** Nothing else writes to them. That clean ownership boundary is the same argument as separating `documents` from `agreements`.

**Querying stays simple.** When you want all contracts expiring in the next 90 days you query `parsed_contracts` directly — no joins to `agreements` needed for the parsed fields themselves. You only join when you need the sender or agreement metadata alongside the parsed content.

**Schema evolution is isolated.** When you discover a new field to extract from contracts — say `payment_terms` or `penalty_cap` — you add a column to `parsed_contracts` without touching anything else.

---

## The full table relationship

This is how all the tables relate to each other:

```
agreements  (sync pipeline owns this)
    │
    ├── documents  (download pipeline owns this)
    │
    ├── parsed_contracts       (parse pipeline owns this)
    ├── parsed_purchase_orders (parse pipeline owns this)
    └── parsed_authorizations  (parse pipeline owns this)
```

Every table hangs off `agreements.agreement_id` as the primary key and foreign key. That single ID is the thread connecting all layers — API metadata, file on disk, and extracted fields.

---

## The one alternative worth considering

If you anticipate adding many more agreement types over time, a **single `parsed_fields` EAV table** (Entity-Attribute-Value) avoids creating a new table per type:

```sql
CREATE TABLE parsed_fields (
    agreement_id    TEXT NOT NULL,
    field_name      TEXT NOT NULL,
    field_value     TEXT,
    confidence      TEXT,
    PRIMARY KEY (agreement_id, field_name),
    FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
);
```

**Do not use this.** EAV is tempting for flexibility but makes every meaningful query painful — getting a full contract record requires pivoting dozens of rows into columns. Type safety disappears. Aggregations like `SUM(total_value)` become string-cast gymnastics. It is the right structure only for truly dynamic, unpredictable schemas. Your schema is well-defined per type, so typed tables are strictly better.

---

## Verdict

What you already have in the module is correct. Three typed parsed tables, each with a foreign key to `agreements`, each owned exclusively by the parse pipeline. No changes needed.
__
## AG QUESTION
in the documents table what is the purpose for downloaded_at and parsed_at status?
__

They track two different lifecycle events that happen at different times and can fail independently.

---

## `downloaded_at`

Records when the PDF was successfully fetched from Adobe Sign and saved to disk. It answers: **do we have the file?**

Useful for:
- Skipping the download API call on reruns — if `downloaded_at` is not null and the file exists on disk, there is no need to hit Adobe Sign again
- Detecting downloads that are stale and need refreshing (e.g. if you re-download after a certain period to get an updated audit report page)
- Diagnosing failures — if `downloaded_at` is null but the agreement has existed for days, something went wrong in the download step

---

## `parsed_at`

Records when Claude successfully extracted fields and wrote them to the relevant parsed table. It answers: **have we processed the file?**

Useful for:
- The parse pipeline's skip logic — `WHERE parsed_at IS NULL OR parse_status = 'failed'` is how you avoid re-parsing already processed documents on every run
- Detecting documents that were downloaded but never parsed — a non-null `downloaded_at` with a null `parsed_at` means the file is sitting on disk unprocessed
- Incremental re-parsing — if you update your prompts to extract a new field, you can force a re-parse by resetting `parsed_at` to null without re-downloading

---

## Why both matter

A document moves through two distinct failure points:

```
Adobe Sign API  →  [download_at]  →  disk  →  [parsed_at]  →  parsed_* table
```

If the Adobe Sign API is down, `downloaded_at` stays null. The file never reaches disk. The parse step never runs.

If the download succeeds but Claude returns malformed JSON or the extraction crashes, `downloaded_at` is set but `parsed_at` stays null and `parse_status` is `failed`. You have the file — you just need to retry the parse step, not the download.

Without both timestamps you cannot distinguish between these two failure modes, and your retry logic has to be coarser — either re-run everything or nothing.

---

## In practice

The combination of `downloaded_at`, `parsed_at`, and `parse_status` gives you four meaningful states for any document:

| `downloaded_at` | `parse_status` | `parsed_at` | Meaning |
|---|---|---|---|
| null | null | null | Not yet downloaded |
| set | pending | null | Downloaded, parse in progress |
| set | success | set | Fully processed |
| set | failed | null | Downloaded, parse failed — retry parse only |

That state matrix is what makes the pipeline safely resumable after any failure without re-downloading files you already have.
__

## AG QUESTION
so what values do I store in downloaded_at and parsed_at?

Both store a **UTC timestamp string** — the ISO 8601 datetime of when that event completed successfully.

```python
from datetime import datetime, timezone

datetime.now(timezone.utc).isoformat()
# → "2024-03-15T14:32:07.451823+00:00"
```

---

## Exactly when you set each one

**`downloaded_at`** — set once, immediately after the PDF bytes are written to disk and the file is confirmed to exist:

```python
with open(dest_path, "wb") as f:
    for chunk in pdf_resp.iter_content(chunk_size=8192):
        f.write(chunk)

# Only set it after the write succeeds
conn.execute("""
    UPDATE documents SET
        downloaded_at = ?,
        file_size_bytes = ?
    WHERE agreement_id = ?
""", (datetime.now(timezone.utc).isoformat(), dest_path.stat().st_size, agreement_id))
```

Never set it speculatively before the write, or on error. A non-null value must mean the file is on disk.

**`parsed_at`** — set once, immediately after `persist_contract()` (or the equivalent for the other types) commits successfully to the database:

```python
persist_contract(conn, agreement_id, fields, confidence, raw_json)

# Only set it after the DB write succeeds
conn.execute("""
    UPDATE documents SET
        parse_status = 'success',
        parsed_at = ?
    WHERE agreement_id = ?
""", (datetime.now(timezone.utc).isoformat(), agreement_id))
```

---

## What you never store there

- Do not store the timestamp when you *started* the operation — only when it *completed successfully*. A started-but-never-finished timestamp is indistinguishable from a success.
- Do not store a timestamp on failure — that is what `parse_status = 'failed'` and `error_message` are for. A null `parsed_at` with a failed status is unambiguous: it failed, and when it failed is in the `error_log`.
__
## AG QUESTION
the same module that is calling the download request is saving the document to file (in chunks) what is the best practice here?

The best practice is to **stream-write to a temp file first, then atomically move it to the final path** once the download is complete and verified. Never write directly to the final destination path during the download.

---

## Why this matters

If you write directly to `{agreement_id}.pdf` and the process crashes mid-download — network timeout, disk full, KeyboardInterrupt — you are left with a partial file at the final path. On the next run, `dest_path.exists()` returns `True`, the download is skipped, and you silently process a corrupted PDF. `downloaded_at` gets set, parsing fails or produces garbage, and the root cause is invisible.

---

## The pattern

```python
import tempfile
import shutil
from pathlib import Path

def download_agreement_pdf(agreement_id: str, sender_email: str, 
                           agreement_type: str) -> Path:
    dest_dir = STORAGE_DIR / agreement_type
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{agreement_id}.pdf"

    if dest_path.exists():
        log.info("Already downloaded: %s", dest_path)
        return dest_path

    # Step 1 — get temp URL from Adobe Sign
    r = requests.get(
        f"{BASE_URL}/agreements/{agreement_id}/combinedDocument/url",
        headers=get_headers(sender_email),
        params={"attachAuditReport": "true"},
        timeout=30,
    )
    r.raise_for_status()
    temp_url = r.json()["url"]

    # Step 2 — stream to a temp file in the SAME directory as the destination
    # Using the same directory is critical — ensures the rename is atomic
    # (a cross-device move would be a copy+delete, not atomic)
    with tempfile.NamedTemporaryFile(
        dir=dest_dir,
        prefix=f".tmp_{agreement_id}_",
        suffix=".pdf",
        delete=False
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)
        try:
            pdf_resp = requests.get(temp_url, timeout=60, stream=True)
            pdf_resp.raise_for_status()

            for chunk in pdf_resp.iter_content(chunk_size=8192):
                tmp_file.write(chunk)

        except Exception:
            # Clean up the incomplete temp file before re-raising
            tmp_path.unlink(missing_ok=True)
            raise

    # Step 3 — verify the download produced a non-empty file
    if tmp_path.stat().st_size == 0:
        tmp_path.unlink()
        raise ValueError(f"Downloaded file is empty for agreement {agreement_id}")

    # Step 4 — atomic rename to final destination
    # On the same filesystem this is a single OS operation — it either
    # completes fully or not at all, no partial state possible
    shutil.move(str(tmp_path), dest_path)

    log.info("Downloaded %s → %s (%d bytes)", 
             agreement_id, dest_path, dest_path.stat().st_size)
    return dest_path
```

---

## Why each step matters

**Temp file in the same directory as the destination.** `shutil.move` on the same filesystem becomes an `os.rename` — a single atomic OS syscall. If the temp file were in `/tmp` and the destination on a different mount point, `shutil.move` falls back to copy-then-delete, which is not atomic. Keeping both on the same filesystem guarantees the rename is instantaneous and uninterruptible.

**`delete=False` on the NamedTemporaryFile.** The default `delete=True` would delete the file when the `with` block exits — before you can rename it. You need `delete=False` and manual cleanup on failure.

**Explicit cleanup in the `except` block.** If the download fails mid-stream, the incomplete temp file is deleted immediately. Your storage directory never accumulates `.tmp_*` debris from failed runs.

**Size check before rename.** A 200 OK with an empty body is a valid HTTP response but not a valid PDF. The size check catches this before the bad file reaches its final path.

**`downloaded_at` is set by the caller after `download_agreement_pdf` returns successfully.** The download function's only job is to get the file to disk safely. The timestamp is the caller's concern — this keeps the function focused and makes the timestamp meaningful: it reflects when the caller confirmed the file is ready for use, not just when the last byte was written.

---

## What your storage directory looks like during a run

```
storage/contracts/
    abc123.pdf          ← completed, safe
    def456.pdf          ← completed, safe
    .tmp_ghi789_a1b2.pdf ← in progress right now
```

And after any crash or interruption:

```
storage/contracts/
    abc123.pdf          ← completed, safe
    def456.pdf          ← completed, safe
    # .tmp_ file was cleaned up by the except block
    # ghi789.pdf does not exist — next run will re-download cleanly
```
___
# AG QUESTION PURGE STATUS

Yes, a status field is exactly the right approach — for the same reason `parse_status` works well: a document moves through a defined lifecycle and you need to know which state it is in at any point.

---

## Recommended approach: a single `file_status` field

Rather than a boolean `is_purged` flag, use a status enum that captures the full lifecycle:

```sql
file_status TEXT CHECK(file_status IN (
    'pending',      -- agreement identified, download not yet attempted
    'downloaded',   -- file is on disk, ready for parsing
    'parsed',       -- parsing complete, file still on disk
    'purged'        -- file deleted from disk, parsed data retained in DB
)) DEFAULT 'pending'
```

This replaces the looser `parse_status` field and consolidates file lifecycle tracking into one column. The states map cleanly to what you already have:

| Before | After |
|---|---|
| `downloaded_at IS NULL` | `file_status = 'pending'` |
| `downloaded_at SET, parse_status = 'pending/failed'` | `file_status = 'downloaded'` |
| `parse_status = 'success'` | `file_status = 'parsed'` |
| *(new)* | `file_status = 'purged'` |

---

## Updated `documents` table

```sql
CREATE TABLE IF NOT EXISTS documents (
    agreement_id        TEXT PRIMARY KEY,
    agreement_type      TEXT NOT NULL,
    file_path           TEXT,
    file_size_bytes     INTEGER,
    downloaded_at       TEXT,
    parsed_at           TEXT,
    purged_at           TEXT,
    file_status         TEXT CHECK(file_status IN (
                            'pending','downloaded','parsed','purged'
                        )) DEFAULT 'pending',
    error_message       TEXT,
    FOREIGN KEY (agreement_id) REFERENCES agreements(agreement_id)
);
```

`purged_at` is the timestamp when the file was deleted — same pattern as `downloaded_at` and `parsed_at`. You keep all three timestamps so the full history of the document is auditable.

## SQLA CREATE TABLE CODE: (GEMINI)
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

```python
# 1. Base Class definition
class Base(DeclarativeBase):
    pass

# 2. Mapped ORM Model
class Document(Base):
    __tablename__ = "documents"

    agreement_id: Mapped[str] = mapped_column(
        ForeignKey("agreements.agreement_id"), 
        primary_key=True
    )
    agreement_type: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    downloaded_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parsed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    purged_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    file_status: Mapped[str] = mapped_column(
        str,
        # AG: Validate CheckConstraint in SQLA documentation
        CheckConstraint("file_status IN ('pending', 'downloaded', 'parsed', 'purged')"),
        server_default="pending",
        nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```


---

## Purge module

```python
from pathlib import Path
from datetime import datetime, timezone
import sqlite3
import logging

log = logging.getLogger(__name__)


def purge_documents(
    conn: sqlite3.Connection,
    agreement_type: str | None = None,
    older_than_days: int | None = None,
    dry_run: bool = True,
) -> dict:
    """
    Delete PDF files from disk for parsed agreements.
    
    Only purges documents where file_status = 'parsed' — never touches
    files that have not been successfully parsed.
    
    Args:
        agreement_type: restrict purge to one type, or None for all types
        older_than_days: only purge files parsed more than N days ago
        dry_run: if True, report what would be purged without deleting
    
    Returns:
        dict with counts of purged, skipped, and failed files
    """
    query = """
        SELECT agreement_id, file_path, file_size_bytes, agreement_type, parsed_at
        FROM documents
        WHERE file_status = 'parsed'
          AND file_path IS NOT NULL
    """
    params = []

    if agreement_type:
        query += " AND agreement_type = ?"
        params.append(agreement_type)

    if older_than_days:
        cutoff = (
            datetime.now(timezone.utc).timestamp() - older_than_days * 86400
        )
        cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat()
        query += " AND parsed_at < ?"
        params.append(cutoff_iso)

    rows = conn.execute(query, params).fetchall()
    log.info("Found %d files eligible for purge (dry_run=%s)", len(rows), dry_run)

    results = {"purged": 0, "skipped": 0, "failed": 0, "bytes_freed": 0}

    for agreement_id, file_path, file_size_bytes, agr_type, parsed_at in rows:
        path = Path(file_path)

        if not path.exists():
            # File already gone — update status to reflect reality
            log.warning("File not found on disk, marking as purged: %s", file_path)
            if not dry_run:
                _mark_purged(conn, agreement_id, file_size_bytes or 0)
            results["skipped"] += 1
            continue

        if dry_run:
            log.info("[DRY RUN] Would purge: %s (%d bytes, parsed %s)",
                     file_path, file_size_bytes or 0, parsed_at)
            results["purged"] += 1
            results["bytes_freed"] += file_size_bytes or 0
            continue

        try:
            path.unlink()
            _mark_purged(conn, agreement_id, file_size_bytes or 0)
            log.info("Purged: %s (%d bytes)", file_path, file_size_bytes or 0)
            results["purged"] += 1
            results["bytes_freed"] += file_size_bytes or 0
        except OSError as e:
            log.error("Failed to delete %s: %s", file_path, e)
            results["failed"] += 1

    log.info(
        "Purge complete — purged: %d, skipped: %d, failed: %d, freed: %.1f MB",
        results["purged"], results["skipped"], results["failed"],
        results["bytes_freed"] / 1_048_576,
    )
    return results


def _mark_purged(conn: sqlite3.Connection, agreement_id: str, file_size_bytes: int):
    conn.execute("""
        UPDATE documents SET
            file_status = 'purged',
            purged_at   = ?,
            file_path   = NULL
        WHERE agreement_id = ?
    """, (datetime.now(timezone.utc).isoformat(), agreement_id))
    conn.commit()
```

---

## Key decisions in the purge design

**Only purge `file_status = 'parsed'`.** The purge module will never touch a file that has not been successfully parsed. A `downloaded` file that failed parsing still has value — it is the only copy of that document. Losing it means re-downloading from Adobe Sign, which may not always be possible if the agreement was archived or the temp URL expired.

**`file_path` is set to NULL after purge.** Once the file is gone, the path is meaningless and potentially misleading. Storing a path that points to a non-existent file is worse than storing NULL — a NULL is unambiguous.

**`dry_run=True` by default.** The first time you run a purge, you want to see exactly what would be deleted before committing. Make dry run the default so a misfire does not cost you files.

**`purged_at` timestamp is kept permanently.** You retain the full audit trail — when it was downloaded, when it was parsed, when it was purged — even after the file is gone. This is useful for compliance and for debugging if a parsed field value is ever questioned.

---

## Useful queries after purge

```sql
-- Storage still in use
SELECT agreement_type,
       COUNT(*) as files,
       ROUND(SUM(file_size_bytes) / 1048576.0, 1) as mb_on_disk
FROM documents
WHERE file_status IN ('downloaded', 'parsed')
GROUP BY agreement_type;

-- Files purged this month
SELECT COUNT(*) as purged,
       ROUND(SUM(file_size_bytes) / 1048576.0, 1) as mb_freed
FROM documents
WHERE file_status = 'purged'
  AND purged_at >= date('now', 'start of month');

-- Agreements where parsed data exists but file is gone (expected after purge)
SELECT a.agreement_id, a.name, c.party_a_name, c.expiration_date
FROM parsed_contracts c
JOIN agreements a ON a.agreement_id = c.agreement_id
JOIN documents d ON d.agreement_id = c.agreement_id
WHERE d.file_status = 'purged';
```
____
## STORAGE RELATIVE LOCATION INDEX in DB

Store a **relative path from a known base directory**, not the full absolute path and not just the filename alone.

---

## Why not the full absolute path

Full paths are environment-specific. The same database moved from your laptop to a server, or from one OS to another, breaks every path reference:

```
# Stored in DB on your laptop:
/Users/carlos/projects/sign-sync/storage/contracts/abc123.pdf

# Meaningless on the server where the project lives at:
/opt/sign-sync/storage/contracts/abc123.pdf
```

Every time the storage root moves you would need to run an UPDATE across the entire documents table. Worse, if you forget, the paths silently point nowhere and `path.exists()` returns False for everything.

---

## Why not just the filename

A bare filename loses the agreement type subfolder structure:

```
abc123.pdf   ← which folder? contracts? purchase_orders?
```

You could reconstruct the path by joining with `agreement_type`, but that is implicit logic scattered across your codebase — anywhere you need the path you have to remember to do that join and reconstruction. It is fragile.

---

## The right approach: relative path from a fixed base

Store the path relative to your storage root:

```
contracts/abc123.pdf
purchase_orders/def456.pdf
authorizations/ghi789.pdf
```

Then resolve to an absolute path at runtime by joining with the base directory from your environment config:

```python
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "storage"))

# When storing:
relative_path = Path(agreement_type) / f"{agreement_id}.pdf"
conn.execute("UPDATE documents SET file_path = ? ...", (str(relative_path), ...))

# When reading:
relative_path = Path(row["file_path"])
absolute_path = STORAGE_DIR / relative_path
```

This way the database is portable. You can move the storage root by changing one environment variable — nothing in the database needs to change. The relative path is also human-readable and self-describing: `contracts/abc123.pdf` tells you both the type and the identifier without any joins.

---

## Updated download function

```python
def download_agreement_pdf(agreement_id: str, sender_email: str,
                           agreement_type: str) -> tuple[Path, str]:
    """
    Returns (absolute_path, relative_path_str).
    Caller stores relative_path_str in the DB.
    """
    relative_path = Path(agreement_type) / f"{agreement_id}.pdf"
    absolute_path = STORAGE_DIR / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)

    if absolute_path.exists():
        log.info("Already downloaded: %s", relative_path)
        return absolute_path, str(relative_path)

    # ... download logic unchanged ...

    return absolute_path, str(relative_path)
```

And in the caller:

```python
absolute_path, relative_path = download_agreement_pdf(
    agreement_id, sender_email, agreement_type
)
conn.execute("""
    UPDATE documents SET
        file_path       = ?,
        file_size_bytes = ?,
        downloaded_at   = ?,
        file_status     = 'downloaded'
    WHERE agreement_id = ?
""", (relative_path, absolute_path.stat().st_size,
      datetime.now(timezone.utc).isoformat(), agreement_id))
```

---

## Summary

| Option | Verdict | Reason |
|---|---|---|
| Full absolute path | No | Breaks when storage root moves |
| Filename only | No | Loses folder structure, requires implicit reconstruction |
| Relative path from base | Yes | Portable, self-describing, resolved at runtime from config |

## File size data:

Para calcular el tamaño de un archivo PDF en Python, la forma más directa y eficiente es obtener los bytes directamente desde el sistema operativo. No necesitas leer ni abrir el contenido del archivo, por lo que el proceso es instantáneo. [1] 
Aquí tienes las tres mejores opciones para lograrlo:
## 1. Usando la librería estándar os (La más común)
Es el método tradicional. Funciona con cualquier tipo de archivo, incluido un PDF.

import os
ruta = "documento.pdf"tamaño_bytes = os.path.getsize(ruta)

print(f"El tamaño es: {tamaño_bytes} bytes")

## 2. Usando pathlib (Recomendado para Python moderno)
Es la forma más limpia y orientada a objetos disponible desde Python 3.4.

from pathlib import Path
ruta = Path("documento.pdf")tamaño_bytes = ruta.stat().st_size

print(f"El tamaño es: {tamaño_bytes} bytes")

## 3. Conversión a unidades legibles (KB, MB)
Como los bytes son difíciles de leer para los humanos, puedes usar este fragmento para convertir el resultado:

import os
tamaño_bytes = os.path.getsize("documento.pdf")
# Conversióntamaño_kb = tamaño_bytes / 1024tamaño_mb = tamaño_kb / 1024

print(f"{tamaño_bytes} bytes | {tamaño_kb:.2f} KB | {tamaño_mb:.2f} MB")



### Sin OS or Pathlib modules:

La única manera nativa de hacerlo sin importar os ni pathlib es abriendo el archivo directamente con la función integrada open() y midiendo su contenido.
Aquí tienes las dos formas de lograrlo, dependiendo de si quieres leer todo el archivo o solo moverte a través de él:
## 1. El método eficiente (Moviendo el cursor)
Este método es el mejor porque no carga el PDF en la memoria RAM. Abre el archivo en modo binario, mueve el cursor al final con seek() y te dice en qué posición quedó con tell().

with open("documento.pdf", "rb") as archivo:
    # Mueve el cursor al final del archivo (0 bytes desde el final)
    archivo.seek(0, 2)
    # Te da la posición actual del cursor, que equivale al tamaño total
    tamaño_bytes = archivo.tell()

print(f"El tamaño es: {tamaño_bytes} bytes")

## 2. El método directo (Leyendo el contenido)
Este método abre el archivo en modo binario ("rb") y lee todos sus bytes de golpe. No se recomienda para PDFs muy grandes (de muchos megabytes), ya que consumirá mucha memoria RAM.

with open("documento.pdf", "rb") as archivo:
    contenido = archivo.read()
    tamaño_bytes = len(contenido)

print(f"El tamaño es: {tamaño_bytes} bytes")

## 💡 ¿Por qué funciona "rb"?
Es fundamental usar el modo "rb" (Read Binary). Si abres el PDF en modo de texto normal ("r"), Python intentará decodificar los caracteres y el conteo de bytes será incorrecto o arrojará un error de decodificación (UnicodeDecodeError).
