# phone_osint.py

A Python script that orchestrates multiple open-source OSINT tools against one or more phone numbers and writes the results to timestamped report files.

## What it runs

| Tool | Type | What it checks |
|---|---|---|
| PhoneIntel | CLI | Carrier, region, Instagram registration, Tellows, SpamCalls |
| Ignorant | CLI | Amazon + Instagram account linkage |
| Phunter | CLI (git clone) | Broader phone OSINT |
| ScamSearch.io | Web | Global scam database |
| Have I Been Zuckered | Web | Facebook data breach |
| NumLookup | Web | US reverse lookup summary |

## Requirements

- Python 3.11+
- Git (required for Phunter install)
- Windows, Linux, or macOS

## Installation

Clone or download `phone_osint.py`, then run:

```bash
python phone_osint.py --install-deps
```

This installs `phoneintel`, `ignorant`, `requests`, and `beautifulsoup4` via pip, and clones Phunter from GitHub into a `Phunter/` subdirectory alongside the script. Git must be available on your PATH.

## Usage

### Single number

```bash
python phone_osint.py +15022693133
```

### Multiple numbers

```bash
python phone_osint.py +15022693133 +14155551234
```

### Batch from file

Create a text file with one number per line (E.164 format). Lines starting with `#` are treated as comments and skipped.

```
# numbers.txt
+15022693133
+14155551234
+447911123456
```

Then run:

```bash
python phone_osint.py --file numbers.txt
```

### Custom output directory

```bash
python phone_osint.py --file numbers.txt --output-dir ./reports
```

## Output

Each number gets its own timestamped `.txt` file under `phone_osint_reports/` (or your custom `--output-dir`):

```
phone_osint_reports/
  +15022693133_20240821_143022.txt
  +14155551234_20240821_143045.txt
```

Results are also printed to the terminal as they run. The `Phunter/` directory will be created alongside `phone_osint.py` when `--install-deps` is run.

## Notes

- Numbers should be in E.164 format: `+` followed by country code and number, no spaces or dashes (e.g. `+15022693133`).
- Web lookups (ScamSearch, NumLookup, Have I Been Zuckered) depend on those services being available and may return limited results if the number hasn't been reported.
- Tools like Ignorant and Phunter make outbound requests to third-party sites — results vary based on service uptime.
- Datasets from breach sources can be years old. Treat them as a starting point, not ground truth.

## Intended use

For legitimate research, personal security awareness, and reporting suspected scam/spam numbers to the appropriate authorities:

- FTC: https://reportfraud.ftc.gov
- FCC: https://consumercomplaints.fcc.gov
- ScamSearch: https://scamsearch.io
- Tellows: https://www.tellows.com

## License

MIT — use responsibly and within applicable laws.
