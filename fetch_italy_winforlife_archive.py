#!/usr/bin/env python3
"""
Fetch deep Italy Win for Life Classico history from a public Blogger archive.

The official WinForLife/Sisal archive blocks local script requests with 403 in
this environment. This script uses the public estrazioniwinforlife.cloud feed as
a practical deep-history supplement, then merges by draw time so existing BC.Game
rows remain authoritative when both sources have the same draw.
"""

from __future__ import annotations

import argparse
import os
import html
import json
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from keno_dashboard_server import (
    LOTTERY_GAMES,
    game_history_path,
    load_history_rows,
    merge_history_rows,
    write_dashboard_rows,
)


GAME_KEY = "italy_win_for_life_10_20"
FEED_URL = "https://www.estrazioniwinforlife.cloud/feeds/posts/default/-/Win-for-Life-Classico"
SOURCE_URL = "https://www.estrazioniwinforlife.cloud/search/label/Win-for-Life-Classico"
MAX_PAGE_SIZE = 150
IT_TZ = ZoneInfo("Europe/Rome")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
)

ITALIAN_MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}


def read_url_with_powershell(url: str, timeout: float) -> str:
    script = (
        "$ProgressPreference='SilentlyContinue';"
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
        "$headers=@{"
        "'User-Agent'='" + USER_AGENT.replace("'", "''") + "';"
        "'Accept'='application/json,text/html,*/*';"
        "'Accept-Language'='it-IT,it;q=0.9,en-US;q=0.8';"
        "'Referer'='" + SOURCE_URL + "'"
        "};"
        "$response=Invoke-WebRequest -UseBasicParsing "
        f"-TimeoutSec {max(1, int(timeout))} "
        f"-Uri '{url.replace("'", "''")}' "
        "-Headers $headers;"
        "$response.Content"
    )
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=max(5, timeout + 10),
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def read_url_with_urllib(url: str, timeout: float) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/html,*/*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8",
            "Referer": SOURCE_URL,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def read_url_with_requests(url: str, timeout: float) -> str:
    import requests

    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/html,*/*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8",
            "Referer": SOURCE_URL,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def read_url(url: str, timeout: float, fetcher: str) -> str:
    if fetcher == "requests":
        return read_url_with_requests(url, timeout)
    if fetcher == "powershell" or (fetcher == "auto" and sys.platform.startswith("win")):
        try:
            return read_url_with_requests(url, timeout)
        except Exception:
            pass
        return read_url_with_powershell(url, timeout)
    return read_url_with_urllib(url, timeout)


def text_from_html(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def parse_draw_time(text: str) -> datetime | None:
    normalized = text_from_html(text).lower()
    month_match = re.search(
        r"(?P<day>\d{1,2})\s+(?P<month>[a-zà-ÿ]+)\s+(?P<year>\d{4})\s+ore\s+"
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2})",
        normalized,
        flags=re.IGNORECASE,
    )
    if month_match:
        month = ITALIAN_MONTHS.get(month_match.group("month").lower())
        if not month:
            return None
        return datetime(
            int(month_match.group("year")),
            month,
            int(month_match.group("day")),
            int(month_match.group("hour")),
            int(month_match.group("minute")),
            tzinfo=IT_TZ,
        )

    numeric_match = re.search(
        r"(?P<day>\d{1,2})-(?P<month>\d{1,2})-(?P<year>\d{4})\s+ore\s+"
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2})",
        normalized,
        flags=re.IGNORECASE,
    )
    if numeric_match:
        return datetime(
            int(numeric_match.group("year")),
            int(numeric_match.group("month")),
            int(numeric_match.group("day")),
            int(numeric_match.group("hour")),
            int(numeric_match.group("minute")),
            tzinfo=IT_TZ,
        )
    return None


def extract_first(pattern: str, text: str, flags: int = re.IGNORECASE | re.DOTALL) -> str:
    match = re.search(pattern, text, flags=flags)
    return match.group(1).strip() if match else ""


def extract_div_by_class(text: str, class_name: str) -> str:
    for match in re.finditer(
        r"<div\b(?P<attrs>[^>]*)>(?P<body>.*?)</div>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        class_match = re.search(
            r"class=[\"'](?P<classes>[^\"']+)[\"']",
            match.group("attrs"),
            flags=re.IGNORECASE,
        )
        if not class_match:
            continue
        classes = set(class_match.group("classes").split())
        if class_name in classes:
            return match.group("body").strip()
    return ""


def parse_entry(entry: dict[str, Any], config: dict[str, Any]) -> dict[str, Any] | None:
    content = str((entry.get("content") or {}).get("$t") or "")
    title = str((entry.get("title") or {}).get("$t") or "")
    content_text = html.unescape(content)
    date_text = extract_first(
        r'id=["\']data-estrazione["\'][^>]*>(.*?)</span>',
        content_text,
    )
    draw_time = parse_draw_time(date_text or title)
    if draw_time is None:
        return None

    combination = extract_div_by_class(content_text, "combinazione")
    numbers = [int(value) for value in re.findall(r"\b\d{1,2}\b", text_from_html(combination))]
    if len(numbers) != int(config["drawnNumbers"]):
        return None
    if sorted(set(numbers)) != sorted(numbers):
        return None
    if any(number < 1 or number > int(config["totalNumbers"]) for number in numbers):
        return None

    bonus_ball = extract_div_by_class(content_text, "numerone")
    bonus_numbers = re.findall(r"\b\d{1,2}\b", text_from_html(bonus_ball))
    bonus = bonus_numbers[0] if bonus_numbers else ""
    draw_number = extract_div_by_class(content_text, "numero-concorso")
    draw_id_part = re.sub(r"\D+", "", text_from_html(draw_number))

    utc_dt = draw_time.astimezone(UTC)
    draw_time_ms = int(utc_dt.timestamp() * 1000)
    draw_id = draw_id_part or str(draw_time_ms)
    return {
        "id": "",
        "lotteryId": str(config["lotteryId"]),
        "lotteryCountry": str(config.get("country") or "Italy"),
        "drawEventId": f"wflcloud-{draw_time.year}-{draw_id}",
        "drawTimeMs": draw_time_ms,
        "drawTimeUtc": utc_dt.isoformat(timespec="seconds"),
        "status": "official-wflcloud",
        "bonusBall": bonus,
        "numbers": sorted(numbers),
        "sourceUrl": SOURCE_URL,
    }


def feed_url(start_index: int, page_size: int) -> str:
    query = urlencode(
        {
            "alt": "json",
            "max-results": page_size,
            "start-index": start_index,
        }
    )
    return f"{FEED_URL}?{query}"


def fetch_archive_rows(
    *,
    limit: int,
    page_size: int,
    timeout: float,
    sleep: float,
    fetcher: str,
    start_index: int = 1,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = LOTTERY_GAMES[GAME_KEY]
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    rows_by_time: dict[int, dict[str, Any]] = {}
    pages = 0
    skipped = 0
    next_index = max(1, start_index)

    while len(rows_by_time) < limit:
        url = feed_url(next_index, page_size)
        raw = read_url(url, timeout, fetcher)
        payload = json.loads(raw)
        entries = payload.get("feed", {}).get("entry") or []
        if not entries:
            break
        pages += 1
        for entry in entries:
            row = parse_entry(entry, config)
            if row is None:
                skipped += 1
                continue
            rows_by_time[int(row["drawTimeMs"])] = row
            if len(rows_by_time) >= limit:
                break
        print(
            f"page {pages}: start-index={next_index}, entries={len(entries)}, "
            f"parsed={len(rows_by_time)}, skipped={skipped}",
            flush=True,
        )
        if len(entries) < page_size:
            break
        next_index += len(entries)
        if sleep > 0:
            time.sleep(sleep)

    rows = sorted(rows_by_time.values(), key=lambda item: item["drawTimeMs"], reverse=True)
    return rows, {
        "source": "estrazioniwinforlife.cloud",
        "sourceUrl": SOURCE_URL,
        "pages": pages,
        "checkedRows": len(rows) + skipped,
        "parsedRows": len(rows),
        "skippedRows": skipped,
        "newestUtc": rows[0]["drawTimeUtc"] if rows else "",
        "oldestUtc": rows[-1]["drawTimeUtc"] if rows else "",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Italy Win for Life Classico deep archive rows and merge them into the local CSV."
    )
    parser.add_argument("--limit", type=int, default=5000, help="Rows to fetch from the archive feed.")
    parser.add_argument("--page-size", type=int, default=150, help="Blogger feed page size, max 150.")
    parser.add_argument("--start-index", type=int, default=1, help="Blogger feed start index.")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--sleep", type=float, default=0.15)
    parser.add_argument(
        "--fetcher",
        choices=("auto", "requests", "powershell", "urllib"),
        default="auto",
        help="HTTP fetcher. Auto prefers requests, then falls back to PowerShell on Windows.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Target CSV. Defaults to the configured Italy history CSV.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch and report without writing.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if os.environ.get("WFL_DEBUG_STACK"):
        import faulthandler

        faulthandler.dump_traceback_later(15, repeat=False)
    if args.limit < 1:
        raise SystemExit("--limit must be positive")
    config = LOTTERY_GAMES[GAME_KEY]
    out_path = args.out or game_history_path(config)

    archive_rows, meta = fetch_archive_rows(
        limit=args.limit,
        page_size=args.page_size,
        timeout=args.timeout,
        sleep=args.sleep,
        fetcher=args.fetcher,
        start_index=args.start_index,
    )
    existing_rows = load_history_rows(out_path, config)
    merged_rows = merge_history_rows(existing_rows, archive_rows)
    added = len(merged_rows) - len(existing_rows)

    print(json.dumps({**meta, "existingRows": len(existing_rows), "addedRows": added}, ensure_ascii=False))
    if args.dry_run:
        return 0

    write_dashboard_rows(out_path, merged_rows, config)
    print(f"writtenRows={len(merged_rows)} out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
