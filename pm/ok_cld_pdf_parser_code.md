Your anchor-based approach is exactly right. Here's a clean, robust Python parsing strategy:

**Core idea:** Use `list.index()` to find anchor words, then grab tokens at fixed offsets from those anchors — rather than relying on absolute positions.

```python
def find_anchor(tokens, *anchor_words):
    """Find the index of the first token in a known sequence of anchor words."""
    for i in range(len(tokens) - len(anchor_words) + 1):
        if all(tokens[i + j].lower() == anchor_words[j].lower() for j in range(len(anchor_words))):
            return i
    return -1


def extract_until_anchor(tokens, start, *stop_anchors):
    """Collect tokens from `start` until we hit any known stop anchor."""
    stop_sequences = [s.lower() if isinstance(s, str) else [x.lower() for x in s] for s in stop_anchors]
    result = []
    i = start
    while i < len(tokens):
        # Check if current position matches any stop sequence
        for stop in stop_sequences:
            words = [stop] if isinstance(stop, str) else stop
            if tokens[i:i+len(words)] and all(tokens[i+j].lower() == words[j] for j in range(len(words))):
                return result, i
        result.append(tokens[i])
        i += 1
    return result, i


def parse_po(tokens):
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
        area_tokens, _ = extract_until_anchor(tokens, idx + 2, ["Rut", "Proveedor"])
        result["gerencia_solicitante"] = " ".join(area_tokens)

    # --- RUT Proveedor ---
    # Anchor: "Rut", "Proveedor", "Razón", "Social", "Proveedor", "SI/NO"
    # The RUT is the token immediately after this header block
    idx = find_anchor(tokens, "Rut", "Proveedor")
    if idx != -1:
        # Skip the full header: "Rut Proveedor Razón Social Proveedor SI/NO" (6 tokens)
        header_end = idx + 6  # adjust if your header varies
        result["rut"] = tokens[header_end]

    # --- Razón Social (Company Name) ---
    # Company name starts right after the RUT value, ends at next anchor
    if "rut" in result:
        rut_idx = tokens.index(result["rut"])
        name_tokens, _ = extract_until_anchor(
            tokens, rut_idx + 1,
            ["Proveedor", "Relacionado"]
        )
        result["razon_social"] = " ".join(name_tokens)

    # --- Proveedor Relacionado ---
    idx = find_anchor(tokens, "Proveedor", "Relacionado")
    if idx != -1:
        result["proveedor_relacionado"] = tokens[idx + 2]  # e.g. "NO" or "SI"

    # --- Proveedor PEP ---
    idx = find_anchor(tokens, "Proveedor", "PEP")
    if idx != -1:
        result["proveedor_pep"] = tokens[idx + 2]

    return result
```

**Usage:**
```python
tokens = ['JUSTIFICACIÓN', 'DE', 'ASIGNACIÓN', 'DIRECTA', 'A', 'PROVEEDOR',
          'Fecha:', '11/11/2025', 'Gerencia', 'Solicitante', 'Protección',
          'de', 'Datos', 'Rut', 'Proveedor', 'Razón', 'Social', 'Proveedor',
          'SI/NO', '77.777.777-7', 'COMPANY', 'NAME', 'SPA', 'Proveedor',
          'Relacionado', 'NO', 'Proveedor', 'PEP', ...]

data = parse_po(tokens)
# → {'fecha': '11/11/2025', 'gerencia_solicitante': 'Protección de Datos',
#    'rut': '77.777.777-7', 'razon_social': 'COMPANY NAME SPA',
#    'proveedor_relacionado': 'NO', ...}
```

---

**Key design decisions explained:**

| Problem | Solution |
|---|---|
| Multi-word company names | `extract_until_anchor()` collects tokens until a known stop anchor, so length doesn't matter |
| Multi-word anchors | `find_anchor(*anchor_words)` matches sequences, e.g. `"Rut", "Proveedor"` together |
| The table header before data | Count the exact header tokens (`idx + 6`) to skip the label row before the value |
| Varying field lengths | Never hardcode absolute index — always compute relative to the nearest anchor |

**Two things to calibrate as you see more PDFs:**
1. The header offset (`idx + 6`) for the RUT — count the exact tokens in `"Rut Proveedor Razón Social Proveedor SI/NO"` in your actual data (accents, extra spaces, merged tokens can shift this).
2. The stop anchors for each field — map out all the fixed label sequences that reliably appear between fields and use those as boundaries.

Want me to extend this with RUT validation (Chilean format `XX.XXX.XXX-X`), batch processing across multiple PO files, or output to CSV/Excel?