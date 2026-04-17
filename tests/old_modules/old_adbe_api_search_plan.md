# Adobe Sign API Implementation Plan

## Search API Request Format

The Adobe Sign Search API uses the following request body format:

```json
{
  "scope": [
    "AGREEMENT_ASSETS"
  ],
  "agreementAssetsCriteria": {
    "type": [
      "AGREEMENT"
    ],
    "createdDate": {
      "range": {
        "min": "2026-03-01T00:00:00Z",
        "max": "2026-03-31T23:59:59Z"
      }
    },
    "startIndex": 0,
    "status": ["SIGNED"],
    "sortByField":"CREATED_DATE",
    "sortOrder":"ASC"
  }
}
```

## Key Implementation Points

| Field | Value | Description |
|-------|-------|-------------|
| `scope` | `["AGREEMENT_ASSETS"]` | Scope to search agreement assets |
| `agreementAssetsCriteria.type` | `["AGREEMENT"]` | Filter by agreement type |
| `agreementAssetsCriteria.createdDate.range` | `{"min": ..., "max": ...}` | Date range using min/max |
| `agreementAssetsCriteria.startIndex` | `0` | Pagination offset |
| `agreementAssetsCriteria.status` | `["SIGNED"]` | Filter by status |
| `agreementAssetsCriteria.sortByField` | `"CREATED_DATE"` | Sort field |
| `agreementAssetsCriteria.sortOrder` | `"ASC"` | Sort order |

## API Implementation Notes

- Endpoint: `POST /search`
- Use `agreementAssetsCriteria` (NOT `agreementAssetFilter`)
- Date format: ISO 8601 with timezone (e.g., `2026-03-01T00:00:00Z`)
- Pagination via `startIndex` - increment by page size for subsequent requests
- Response includes `agreementAssetsResults` with `agreementAssetsResultList` array

## Next Steps

1. Update `api.py` search method with correct request body format
2. Handle pagination using `startIndex`
3. Parse response `agreementAssetsResults` structure
4. Add proper error handling for 429 rate limit responses
