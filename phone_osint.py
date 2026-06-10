#!/usr/bin/env python3
"""
phone_osint.py — Orchestrates multiple OSINT tools against one or more phone numbers.

Usage:
    python phone_osint.py +15022693133
    python phone_osint.py +15022693133 +14155551234
    python phone_osint.py --file numbers.txt
    python phone_osint.py --install-deps
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_PYTHON_DIR = Path(sys.executable).parent
# On Windows the layout is pythoncore-X.Y-64/{python.exe,Scripts/}
# On Linux/Mac it is bin/ so Scripts fallback covers both
SCRIPTS_DIR = _PYTHON_DIR / 'Scripts' if (_PYTHON_DIR / 'Scripts').exists() else _PYTHON_DIR
OUTPUT_DIR = Path("phone_osint_reports")

PHONEINTEL_EXE = SCRIPTS_DIR / "phoneintel.exe"
if not PHONEINTEL_EXE.exists():
    PHONEINTEL_EXE = SCRIPTS_DIR / "phoneintel"  # non-Windows fallback


PIP_DEPS = [
    "phoneintel",
    "ignorant",
    "requests",
    "beautifulsoup4",
]

# Phunter is not on PyPI — installed via git clone into this directory
PHUNTER_DIR = Path(__file__).parent / "Phunter"
PHUNTER_REPO = "https://github.com/N0rz3/Phunter.git"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(msg: str) -> str:
    bar = "=" * 60
    return f"\n{bar}\n  {msg}\n{bar}\n"


def run_cli(cmd: list[str], timeout: int = 60, cwd: str | None = None) -> str:
    """Run a subprocess, return combined stdout+stderr as a string."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr.strip():
            output += "\n[stderr]\n" + result.stderr.strip()
        return output or "(no output)"
    except FileNotFoundError:
        return f"[ERROR] Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return f"[ERROR] Timed out after {timeout}s"
    except Exception as e:
        return f"[ERROR] {e}"


def fetch_scamsearch(number: str) -> str:
    """Scrape ScamSearch.io for a number report."""
    clean = re.sub(r"[^\d]", "", number)
    url = f"https://scamsearch.io/search_report?searchoption=3&search={clean}"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.find_all("div", class_=re.compile(r"report|result|card", re.I))
        if results:
            return "\n".join(r.get_text(separator=" ", strip=True) for r in results[:5])
        return f"No results found (URL: {url})"
    except Exception as e:
        return f"[ERROR] {e} (URL: {url})"


def fetch_haveibeenzuckered(number: str) -> str:
    """Check Have I Been Zuckered for a Facebook breach hit."""
    clean = re.sub(r"[^\d]", "", number)
    url = f"https://haveibeenzuckered.com/?number={clean}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        # look for result text in the page
        for tag in soup.find_all(["div", "p", "h1", "h2", "h3", "span"]):
            t = tag.get_text(strip=True)
            if clean in t or "found" in t.lower() or "breach" in t.lower() or "zucked" in t.lower():
                if len(t) > 5:
                    return t[:500]
        return "No breach data returned (check manually: https://haveibeenzuckered.com)"
    except Exception as e:
        return f"[ERROR] {e}"


def fetch_numlookup(number: str) -> str:
    """Pull basic info from NumLookup (US numbers)."""
    clean = re.sub(r"[^\d]", "", number)  # digits only for URL path
    url = f"https://www.numlookup.com/{clean}"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # grab the meta description which typically has the summary
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return meta["content"].strip()
        # fallback: grab any result paragraphs
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs[:4])
        return text or f"No summary found (URL: {url})"
    except Exception as e:
        return f"[ERROR] {e} (URL: {url})"


# ---------------------------------------------------------------------------
# Install deps
# ---------------------------------------------------------------------------

def install_deps():
    print("Installing pip dependencies...")
    for dep in PIP_DEPS:
        print(f"  pip install {dep}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", dep],
            capture_output=True,
            text=True,
        )
        status = "OK" if result.returncode == 0 else "FAILED"
        print(f"  [{status}] {dep}")
        if result.returncode != 0:
            print(result.stderr.strip())

    # Phunter: git clone + pip install its requirements
    print("\nInstalling Phunter (git clone)...")
    if PHUNTER_DIR.exists():
        print(f"  [SKIP] Phunter already cloned at {PHUNTER_DIR}")
    else:
        result = subprocess.run(
            ["git", "clone", PHUNTER_REPO, str(PHUNTER_DIR)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  [OK] Cloned to {PHUNTER_DIR}")
        else:
            print(f"  [FAILED] git clone failed:\n{result.stderr.strip()}")
            return

    req_file = PHUNTER_DIR / "requirements.txt"
    if req_file.exists():
        print("  pip install Phunter requirements...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            capture_output=True,
            text=True,
        )
        status = "OK" if result.returncode == 0 else "FAILED"
        print(f"  [{status}] Phunter requirements")
        if result.returncode != 0:
            print(result.stderr.strip())

    print("\nDone. Re-run without --install-deps to use the tool.")


# ---------------------------------------------------------------------------
# Per-number report
# ---------------------------------------------------------------------------

def run_all(number: str) -> str:
    lines = []
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(banner(f"OSINT REPORT: {number}  [{ts}]"))

    # --- PhoneIntel ---
    lines.append(banner("PhoneIntel"))
    lines.append(run_cli([str(PHONEINTEL_EXE), "--info", number]))

    # --- Ignorant ---
    lines.append(banner("Ignorant (Amazon / Instagram check)"))
    ignorant_exe = SCRIPTS_DIR / "ignorant.exe"
    if not ignorant_exe.exists():
        ignorant_exe = SCRIPTS_DIR / "ignorant"
    lines.append(run_cli([str(ignorant_exe), number]))

    # --- Phunter ---
    lines.append(banner("Phunter"))
    phunter_script = PHUNTER_DIR / "phunter.py"
    if phunter_script.exists():
        lines.append(run_cli([sys.executable, str(phunter_script), "-t", number], cwd=str(PHUNTER_DIR)))
    else:
        lines.append(f"[SKIP] Phunter not found at {phunter_script} — run --install-deps")

    # --- Web lookups ---
    lines.append(banner("ScamSearch.io"))
    lines.append(fetch_scamsearch(number))

    lines.append(banner("Have I Been Zuckered (Facebook breach)"))
    lines.append(fetch_haveibeenzuckered(number))

    lines.append(banner("NumLookup"))
    lines.append(fetch_numlookup(number))

    lines.append("\n" + "=" * 60 + "\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run OSINT tools against one or more phone numbers."
    )
    parser.add_argument(
        "numbers",
        nargs="*",
        help="Phone number(s) in E.164 format, e.g. +15022693133",
    )
    parser.add_argument(
        "--file", "-f",
        type=Path,
        help="Text file with one phone number per line",
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install required Python packages then exit",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Directory for report files (default: {OUTPUT_DIR})",
    )
    args = parser.parse_args()

    if args.install_deps:
        install_deps()
        return

    numbers: list[str] = list(args.numbers)

    if args.file:
        if not args.file.exists():
            print(f"[ERROR] File not found: {args.file}")
            sys.exit(1)
        for line in args.file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                numbers.append(line)

    if not numbers:
        parser.print_help()
        sys.exit(1)

    # deduplicate, preserve order
    seen = set()
    unique = []
    for n in numbers:
        if n not in seen:
            seen.add(n)
            unique.append(n)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for number in unique:
        print(f"[*] Running OSINT on {number} ...")
        report = run_all(number)

        # print to terminal
        print(report)

        # write to file
        safe = re.sub(r"[^\d+]", "_", number)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        outfile = args.output_dir / f"{safe}_{ts}.txt"
        outfile.write_text(report, encoding="utf-8")
        print(f"[+] Report saved: {outfile}\n")


if __name__ == "__main__":
    main()
