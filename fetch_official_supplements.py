#!/usr/bin/env python3
"""Fetch recent official/supplement lottery results for supported games."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import fetch_bc_keno_history


UTC = timezone.utc


RO_TZ = ZoneInfo("Europe/Bucharest")
IT_TZ = ZoneInfo("Europe/Rome")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

YESPLAY_API_URL = (
    "https://yesplay.bet/scp/api/1.0/lucky-numbers/draws/russia_rapido/results"
    "?pageSize=12"
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


def read_url(
    url: str,
    *,
    timeout: float = 30,
    headers: dict[str, str] | None = None,
) -> str:
    request_headers = dict(DEFAULT_HEADERS)
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers, method="GET")
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def validate_numbers(
    numbers: list[int],
    *,
    expected_count: int,
    total_numbers: int,
) -> list[int]:
    fetch_bc_keno_history.parse_balls(
        ",".join(str(number) for number in numbers),
        expected_count=expected_count,
        total_numbers=total_numbers,
    )
    return numbers


def row_from_datetime(
    *,
    source: str,
    draw_time: datetime,
    numbers: list[int],
    expected_count: int,
    total_numbers: int,
    draw_event_id: str = "",
    bonus_ball: str = "",
) -> dict[str, Any]:
    if draw_time.tzinfo is None:
        raise ValueError("draw_time must be timezone-aware")
    utc_dt = draw_time.astimezone(UTC)
    validated = validate_numbers(
        numbers,
        expected_count=expected_count,
        total_numbers=total_numbers,
    )
    draw_time_ms = int(utc_dt.timestamp() * 1000)
    return {
        "source": source,
        "drawEventId": draw_event_id or f"{source}-{draw_time_ms}",
        "drawTimeMs": draw_time_ms,
        "drawTimeUtc": utc_dt.isoformat(timespec="seconds"),
        "numbers": validated,
        "bonusBall": bonus_ball,
    }


def parse_lotodate_rows(
    page_html: str,
    *,
    expected_count: int,
    total_numbers: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_pattern = re.compile(
        r"<tr\b(?P<attrs>[^>]*)>(?P<body>.*?)</tr>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in row_pattern.finditer(page_html):
        attrs = match.group("attrs")
        body = match.group("body")
        if "upcoming-draw" in attrs:
            continue
        time_match = re.search(
            r'<time[^>]+datetime="(?P<dt>[^"]+)"',
            body,
            flags=re.IGNORECASE,
        )
        if not time_match:
            continue
        numbers = [
            int(value)
            for value in re.findall(
                r'<span[^>]*class="[^"]*\bball\b[^"]*"[^>]*>\s*(\d{1,2})\s*</span>',
                body,
                flags=re.IGNORECASE,
            )
        ]
        if len(numbers) != expected_count:
            continue
        dt_text = time_match.group("dt").replace("Z", "+00:00")
        draw_time = datetime.fromisoformat(dt_text)
        rows.append(
            row_from_datetime(
                source="lotodate",
                draw_time=draw_time,
                numbers=numbers,
                expected_count=expected_count,
                total_numbers=total_numbers,
            )
        )
    return sorted(rows, key=lambda item: item["drawTimeMs"], reverse=True)


def parse_polonia_rows(
    page_html: str,
    *,
    expected_count: int,
    total_numbers: int,
) -> list[dict[str, Any]]:
    # Legacy parser: Poland now uses the LotoDate source in LOTTERY_GAMES.
    # Keep this parser only to document and support the old fallback path.
    date_pattern = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\b")
    matches = list(date_pattern.finditer(page_html))
    rows_by_time: dict[int, dict[str, Any]] = {}
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(page_html)
        segment = page_html[match.end() : next_start]
        numbers = [
            int(value)
            for value in re.findall(
                r"<span[^>]*>\s*(\d{1,2})\s*</span>",
                segment,
                flags=re.IGNORECASE,
            )
        ]
        if len(numbers) < expected_count:
            continue
        day, month, year, hour, minute, second = [
            int(value) for value in re.findall(r"\d+", match.group(0))
        ]
        draw_time = datetime(year, month, day, hour, minute, second, tzinfo=RO_TZ)
        row = row_from_datetime(
            source="polonia-loto",
            draw_time=draw_time,
            numbers=numbers[:expected_count],
            expected_count=expected_count,
            total_numbers=total_numbers,
        )
        rows_by_time[row["drawTimeMs"]] = row
    return sorted(rows_by_time.values(), key=lambda item: item["drawTimeMs"], reverse=True)


def fetch_yesplay_rapido_rows(
    *,
    expected_count: int,
    total_numbers: int,
    timeout: float,
) -> list[dict[str, Any]]:
    raw = read_url(
        YESPLAY_API_URL,
        timeout=timeout,
        headers={
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://yesplay.bet/lucky-numbers/russia_rapido/results",
        },
    )
    payload = json.loads(raw)
    rows = []
    for item in payload.get("results") or []:
        balls = item.get("balls") or []
        normal = [int(ball["value"]) for ball in balls if ball.get("type") == "NORMAL"]
        bonus = next(
            (str(ball.get("value")) for ball in balls if ball.get("type") == "BONUS"),
            "",
        )
        if len(normal) != expected_count:
            continue
        draw_time_ms = int(item["drawDate"])
        draw_time = datetime.fromtimestamp(draw_time_ms / 1000, tz=UTC)
        rows.append(
            row_from_datetime(
                source="yesplay",
                draw_time=draw_time,
                numbers=normal,
                expected_count=expected_count,
                total_numbers=total_numbers,
                draw_event_id=f"yesplay-{item.get('drawNumber', draw_time_ms)}",
                bonus_ball=bonus,
            )
        )
    return sorted(rows, key=lambda item: item["drawTimeMs"], reverse=True)


def parse_winforlife_rows(
    page_html: str,
    *,
    expected_count: int,
    total_numbers: int,
) -> list[dict[str, Any]]:
    decoded = html.unescape(page_html)
    pattern = re.compile(
        r"N[º°]\s*(?P<draw>\d+)\s+del\s+"
        r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-zÀ-ÿ]+)\s+(?P<year>\d{4})\s+"
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2})(?P<body>.*?)(?=N[º°]\s*\d+\s+del|$)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    rows = []
    for match in pattern.finditer(decoded):
        month = ITALIAN_MONTHS.get(match.group("month").lower())
        if not month:
            continue
        body = match.group("body")
        numbers = [
            int(value)
            for value in re.findall(
                r"<[^>]*(?:ball|numero|number)[^>]*>\s*(\d{1,2})\s*<",
                body,
                flags=re.IGNORECASE,
            )
        ]
        if len(numbers) < expected_count:
            numbers = [int(value) for value in re.findall(r"\b(\d{1,2})\b", body)]
        if len(numbers) < expected_count:
            continue
        draw_time = datetime(
            int(match.group("year")),
            month,
            int(match.group("day")),
            int(match.group("hour")),
            int(match.group("minute")),
            tzinfo=IT_TZ,
        )
        rows.append(
            row_from_datetime(
                source="winforlife",
                draw_time=draw_time,
                numbers=numbers[:expected_count],
                expected_count=expected_count,
                total_numbers=total_numbers,
                draw_event_id=f"winforlife-{match.group('draw')}",
            )
        )
    return sorted(rows, key=lambda item: item["drawTimeMs"], reverse=True)


def fetch_recent_official(
    config: dict[str, Any],
    *,
    timeout: float = 30,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = str(config.get("officialSupplement") or "")
    url = str(config.get("supplementUrl") or "")
    expected_count = int(config["drawnNumbers"])
    total_numbers = int(config["totalNumbers"])

    try:
        if source == "lotodate":
            page_html = read_url(url, timeout=timeout)
            rows = parse_lotodate_rows(
                page_html,
                expected_count=expected_count,
                total_numbers=total_numbers,
            )
        elif source == "polonia-loto":
            # Legacy fallback. Active Poland config uses LotoDate.
            page_html = read_url(
                url,
                timeout=timeout,
                headers={"Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8"},
            )
            rows = parse_polonia_rows(
                page_html,
                expected_count=expected_count,
                total_numbers=total_numbers,
            )
        elif source == "yesplay":
            rows = fetch_yesplay_rapido_rows(
                expected_count=expected_count,
                total_numbers=total_numbers,
                timeout=timeout,
            )
        elif source == "winforlife":
            page_html = read_url(
                url,
                timeout=timeout,
                headers={"Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8"},
            )
            rows = parse_winforlife_rows(
                page_html,
                expected_count=expected_count,
                total_numbers=total_numbers,
            )
        else:
            return [], {
                "source": source,
                "url": url,
                "newRows": 0,
                "status": "not_implemented",
                "message": "该彩种官网补历史抓取暂未启用，本次使用 BC.Game 历史",
            }
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        return [], {
            "source": source,
            "url": url,
            "newRows": 0,
            "status": "error",
            "error": str(exc),
        }

    return rows, {
        "source": source,
        "url": url or (YESPLAY_API_URL if source == "yesplay" else ""),
        "checkedRows": len(rows),
        "newRows": 0,
        "status": "ok",
        "newestOfficialUtc": rows[0]["drawTimeUtc"] if rows else "",
    }
