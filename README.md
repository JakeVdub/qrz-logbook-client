# Ham Radio Log Utils

Python utilities for amateur radio log workflows, including a QRZ Logbook API client.

## Features

- QRZ API support for `FETCH`, `INSERT`, `DELETE`, and `STATUS`
- Class-based client (`QRZClient`) for reusable integrations
- Convenience module-level functions (`setup`, `fetch_records`, etc.)
- Response parsing into Python dictionaries with normalized numeric fields

## Installation

### Local development

```bash
pip install -e .
```

### From GitHub (after publishing)

```bash
pip install git+https://github.com/jakevdub/ham-radio-log-utils.git
```

## Quick Start (Recommended)

```python
from ham_radio_log_utils import QRZClient

client = QRZClient(
    api_key="YOUR-QRZ-API-KEY",
    user_agent="MyCoolUploadScript.py/1.0.0 (VA7STV)",
)

# STATUS
status_response = client.status()
print(status_response)

# INSERT
adif = "<band:3>20m<mode:3>SSB<call:5>K1ABC<qso_date:8>20260322<station_callsign:5>W1XYZ<time_on:4>1830<eor>"
insert_response = client.insert_record(adif)
print(insert_response)

# FETCH (paged)
fetch_response = client.fetch_records(limit=250, offset=0)
print(fetch_response.get("COUNT"), fetch_response.get("LOGIDS"))

# DELETE
delete_response = client.delete_record([123456789])
print(delete_response)
```

## Convenience Function Style

```python
from ham_radio_log_utils import setup, fetch_records

setup(
    api_key="YOUR-QRZ-API-KEY",
    user_agent="MyCoolUploadScript.py/1.0.0 (VA7STV)",
)

response = fetch_records(limit=100, offset=0)
print(response)
```

## Notes

- QRZ requires a specific and identifiable `User-Agent` value.
- Do not use generic values like `python-requests` or `node-fetch`.
- Some QRZ actions require a paid subscription.

