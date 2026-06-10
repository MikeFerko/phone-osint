# Example Workflow: Phone Number OSINT

This walkthrough covers a typical investigation from setup to finished report.

---

## 1. Prerequisites

- Python 3.11 or newer
- Git installed and on your PATH
- A terminal (PowerShell, CMD, bash, etc.)

---

## 2. Install dependencies (first time only)

```bash
python phone_osint.py --install-deps
```

This will:
- Install `phoneintel`, `ignorant`, `requests`, and `beautifulsoup4` via pip
- Clone [Phunter](https://github.com/N0rz3/Phunter) into a `Phunter/` subfolder next to the script

You only need to run this once.

---

## 3. Run against a single number

```bash
python phone_osint.py +15022693133
```

Results print to the terminal and a report file is saved automatically:

```
phone_osint_reports/
  +15022693133_20240821_143022.txt
```

---

## 4. Run against multiple numbers

Pass them as arguments:

```bash
python phone_osint.py +15022693133 +14155551234 +447911123456
```

---

## 5. Batch mode from a file

Create a plain text file with one number per line. Lines starting with `#` are skipped.

**numbers.txt**
```
# Suspected scam callers
+15022693133
+14155551234
```

Then run:

```bash
python phone_osint.py --file numbers.txt
```

---

## 6. Save reports to a custom folder

```bash
python phone_osint.py --file numbers.txt --output-dir ./investigation_2024
```

---

## 7. Reading the report

Each report is divided into sections:

| Section | Source | What it tells you |
|---|---|---|
| PhoneIntel | CLI tool | Carrier, region, spam score, Instagram registration |
| Ignorant | CLI tool | Whether the number is linked to Amazon or Instagram |
| Phunter | CLI tool | Broader account/site linkage |
| ScamSearch.io | Web scrape | Community-reported scam activity |
| Have I Been Zuckered | Web scrape | Facebook data breach linkage |
| NumLookup | Web scrape | US reverse lookup summary |

---

## 8. Reporting a scam number

If your investigation confirms a scam caller, report them:

- **FTC (US):** https://reportfraud.ftc.gov
- **FCC (US):** https://consumercomplaints.fcc.gov
- **ScamSearch:** https://scamsearch.io
- **Tellows:** https://www.tellows.com

---

## Notes

- Numbers must be in E.164 format: `+` followed by country code and digits, no spaces or dashes.
- Web lookups depend on third-party service availability and may return limited data.
- Treat breach data as a starting point. It can be years old.
