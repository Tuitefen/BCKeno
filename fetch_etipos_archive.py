#!/usr/bin/env python3
"""
Fetch recent official eTIPOS e-KLUB KENO archive draws.

The official archive page has no draw event id. It exposes a classic ASP.NET
form filtered by Slovakia local date and one-hour time span. This module is
used to fill the short delay where BC.Game has not published the newest draws
yet.
"""

from __future__ import annotations

import argparse
import html
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import fetch_bc_keno_history


ARCHIVE_URL = "https://eklubkeno.etipos.sk/Archive.aspx"
SK_TZ = ZoneInfo("Europe/Bratislava")
NUMBER_COLUMNS = [f"n{i}" for i in range(1, 21)]


def archive_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "sk-SK,sk;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://eklubkeno.etipos.sk",
        "Referer": ARCHIVE_URL,
    }


def read_html(request: Request, timeout: float) -> str:
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def get_archive_page(timeout: float = 30) -> str:
    request = Request(ARCHIVE_URL, headers=archive_headers(), method="GET")
    return read_html(request, timeout)


def hidden_fields(page_html: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    pattern = re.compile(
        r'<input[^>]+type="hidden"[^>]+>',
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(page_html):
        tag = match.group(0)
        name_match = re.search(r'name="([^"]+)"', tag)
        if not name_match:
            continue
        value_match = re.search(r'value="([^"]*)"', tag)
        fields[html.unescape(name_match.group(1))] = html.unescape(
            value_match.group(1) if value_match else ""
        )
    return fields


def post_archive_page(target_time: datetime, timeout: float = 30) -> str:
    if target_time.tzinfo is None:
        raise ValueError("target_time must be timezone-aware")
    local_time = target_time.astimezone(SK_TZ)
    initial = get_archive_page(timeout=timeout)
    fields = hidden_fields(initial)
    fields.update(
        {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "_ctl0:ContentPlaceHolder:ddlDay": str(local_time.day),
            "_ctl0:ContentPlaceHolder:ddlMonth": str(local_time.month),
            "_ctl0:ContentPlaceHolder:ddlYear": str(local_time.year),
            "_ctl0:ContentPlaceHolder:ddlTimeSpan": str(local_time.hour),
            "_ctl0:ContentPlaceHolder:btnSubmit": "Zobraziť",
        }
    )
    body = urlencode(fields).encode("utf-8")
    request = Request(ARCHIVE_URL, data=body, headers=archive_headers(), method="POST")
    return read_html(request, timeout)


def parse_archive_rows(page_html: str, target_date: datetime) -> list[dict[str, Any]]:
    local_date = target_date.astimezone(SK_TZ).date()
    pattern = re.compile(
        r'<div class="closest">.*?lblDrawTimeValue">(?P<time>\d{1,2}:\d{2})</span>'
        r'.*?<div class="numbers">(?P<numbers>.*?)</div>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    rows: list[dict[str, Any]] = []
    for match in pattern.finditer(page_html):
        time_text = match.group("time")
        hour, minute = [int(part) for part in time_text.split(":")]
        local_dt = datetime(
            local_date.year,
            local_date.month,
            local_date.day,
            hour,
            minute,
            tzinfo=SK_TZ,
        )
        numbers = [int(value) for value in re.findall(r"<span>(\d+)</span>", match.group("numbers"))]
        if len(numbers) != 20:
            continue
        fetch_bc_keno_history.parse_balls(",".join(str(number) for number in numbers))
        utc_dt = local_dt.astimezone(UTC)
        rows.append(
            {
                "drawTimeUtc": utc_dt.isoformat(),
                "drawTimeMs": int(utc_dt.timestamp() * 1000),
                "localTime": local_dt.isoformat(),
                "numbers": numbers,
                "source": "etipos",
            }
        )
    rows.sort(key=lambda item: item["drawTimeMs"], reverse=True)
    return rows


def fetch_recent_archive(hours: int = 2, timeout: float = 30) -> list[dict[str, Any]]:
    now = datetime.now(tz=SK_TZ)
    rows: dict[int, dict[str, Any]] = {}
    for offset in range(max(1, hours)):
        target = now - timedelta(hours=offset)
        page_html = post_archive_page(target, timeout=timeout)
        for row in parse_archive_rows(page_html, target):
            rows[row["drawTimeMs"]] = row
    return sorted(rows.values(), key=lambda item: item["drawTimeMs"], reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch recent official eTIPOS Keno draws.")
    parser.add_argument("--hours", type=int, default=2)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    rows = fetch_recent_archive(hours=args.hours)
    for row in rows[: args.limit]:
        print(
            f"{row['drawTimeUtc']} {','.join(str(number) for number in row['numbers'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
