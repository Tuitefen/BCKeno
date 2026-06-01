#!/usr/bin/env python3
"""
Fetch BC.Game lottery draw history for Slovakia E-Klub Keno 20/80.

The public page calls:
  POST https://bcgame.nz/api/platform-lottery/lottery-detail/history

The endpoint returns paged draw history. This script writes a CSV where the
last 20 columns are n1..n20, so it can be passed directly to
keno_triple_omission.py.

Examples:
  python fetch_bc_keno_history.py
  python fetch_bc_keno_history.py --limit 5000 --out bc_keno_history.csv
  python fetch_bc_keno_history.py --all --out bc_keno_history_all.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://bcgame.nz/api/platform-lottery/lottery-detail/history"
LOTTERY_URL = "https://bcgame.nz/zh-CN/lottery/detail/{lottery_id}?tab=1"
DEFAULT_LOTTERY_ID = "74214"
ROOT = Path(__file__).resolve().parent
DATA_ROOT = Path(os.environ.get("BCKENO_DATA_DIR", ROOT / "data")).resolve()
DEFAULT_OUTPUT = DATA_ROOT / "bc_keno_history.csv"
MAX_NUMBER_COLUMNS = 20
NUMBER_COLUMNS = [f"n{i}" for i in range(1, MAX_NUMBER_COLUMNS + 1)]
CANCELLED_STATUS_CODES = {"60"}


def draw_time_iso(draw_time_ms: str | int | None) -> str:
    if draw_time_ms in (None, ""):
        return ""
    try:
        timestamp = int(draw_time_ms) / 1000
    except (TypeError, ValueError):
        return ""
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def parse_balls(
    normal_ball: str,
    *,
    expected_count: int = 20,
    total_numbers: int = 80,
) -> list[int]:
    balls = [int(part.strip()) for part in normal_ball.split(",") if part.strip()]
    if len(balls) != expected_count:
        raise ValueError(f"expected {expected_count} balls, got {len(balls)}: {normal_ball!r}")
    bad = [ball for ball in balls if ball < 1 or ball > total_numbers]
    if bad:
        raise ValueError(f"balls out of 1..{total_numbers} range: {bad}")
    if len(set(balls)) != len(balls):
        raise ValueError(f"duplicate balls: {normal_ball!r}")
    return balls


def is_cancelled_item(item: dict[str, Any]) -> bool:
    status = str(item.get("status", "")).strip()
    normal_ball = str(item.get("normalBall", "")).strip()
    return status in CANCELLED_STATUS_CODES and normal_ball == ""


def api_headers(lottery_id: str) -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": "https://bcgame.nz",
        "Referer": LOTTERY_URL.format(lottery_id=lottery_id),
    }


def post_history_page(
    *,
    lottery_id: str,
    page: int,
    page_size: int,
    timeout: float,
    retries: int,
    retry_sleep: float,
) -> dict[str, Any]:
    payload = {
        "lotteryId": lottery_id,
        "pageSize": page_size,
        "page": page,
        "sortBy": "DRAW_DATE",
        "sort": "DESC",
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = Request(API_URL, data=body, headers=api_headers(lottery_id), method="POST")

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                text = response.read().decode(charset)
            decoded = json.loads(text)
            if decoded.get("code") != 0:
                raise RuntimeError(
                    f"API returned code={decoded.get('code')!r}, msg={decoded.get('msg')!r}"
                )
            return decoded["data"]
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(retry_sleep * (attempt + 1))

    raise RuntimeError(f"failed to fetch page {page}: {last_error}") from last_error


def normalize_row(
    item: dict[str, Any],
    *,
    expected_count: int = 20,
    total_numbers: int = 80,
) -> dict[str, Any]:
    if is_cancelled_item(item):
        balls: list[int] = []
    else:
        balls = parse_balls(
            str(item.get("normalBall", "")),
            expected_count=expected_count,
            total_numbers=total_numbers,
        )
    row = {
        "id": item.get("id", ""),
        "lottery_id": item.get("lotteryId", ""),
        "lottery_country": item.get("lotteryCountry", ""),
        "draw_event_id": item.get("drawEventId", ""),
        "draw_time_ms": item.get("drawTime", ""),
        "draw_time_utc": draw_time_iso(item.get("drawTime")),
        "status": item.get("status", ""),
        "bonus_ball": item.get("bonusBall", ""),
    }
    for index, column in enumerate(NUMBER_COLUMNS):
        row[column] = balls[index] if index < len(balls) else ""
    return row


def csv_fieldnames() -> list[str]:
    return [
        "id",
        "lottery_id",
        "lottery_country",
        "draw_event_id",
        "draw_time_ms",
        "draw_time_utc",
        "status",
        "bonus_ball",
        *NUMBER_COLUMNS,
    ]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fieldnames())
        writer.writeheader()
        writer.writerows(rows)


def replace_path_with_retry(temp_path: Path, target_path: Path) -> None:
    last_error: PermissionError | None = None
    for attempt in range(12):
        try:
            temp_path.replace(target_path)
            return
        except PermissionError as exc:
            last_error = exc
            if attempt == 11:
                break
            time.sleep(0.25)
    raise PermissionError(
        f"无法替换历史文件：{target_path}。Windows 拒绝访问，通常是 CSV 正被 Excel/WPS/"
        f"编辑器/杀毒扫描占用。请关闭打开该 CSV 的程序后重试。原始错误：{last_error}"
    ) from last_error


def skipped_example(page: int, item: dict[str, Any], exc: ValueError) -> dict[str, Any]:
    return {
        "page": page,
        "drawEventId": item.get("drawEventId", ""),
        "status": item.get("status", ""),
        "reason": str(exc),
    }


def fetch_history(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = 1
    total = None
    total_page = None
    target_limit = None if args.all else args.limit
    latest_meta: dict[str, Any] = {}
    skipped_rows = 0
    skipped_examples: list[dict[str, Any]] = []
    duplicate_rows = 0
    seen_keys: set[str] = set()
    expected_count = int(getattr(args, "expected_count", 20))
    total_numbers = int(getattr(args, "total_numbers", 80))

    while True:
        data = post_history_page(
            lottery_id=args.lottery_id,
            page=page,
            page_size=args.page_size,
            timeout=args.timeout,
            retries=args.retries,
            retry_sleep=args.retry_sleep,
        )
        total = int(data.get("total") or 0)
        total_page = int(data.get("totalPage") or 0)
        items = data.get("list") or []
        if not items:
            break

        page_rows: list[dict[str, Any]] = []
        page_skipped = 0
        page_duplicates = 0
        for item in items:
            try:
                row = normalize_row(
                    item,
                    expected_count=expected_count,
                    total_numbers=total_numbers,
                )
            except ValueError as exc:
                page_skipped += 1
                skipped_rows += 1
                if len(skipped_examples) < 5:
                    skipped_examples.append(skipped_example(page, item, exc))
                continue

            key = str(row.get("draw_event_id") or row.get("id"))
            if key and key in seen_keys:
                page_duplicates += 1
                duplicate_rows += 1
                continue
            if key:
                seen_keys.add(key)
            page_rows.append(row)

        rows.extend(page_rows)
        latest_meta = {
            "page": data.get("page"),
            "page_size": data.get("pageSize"),
            "total": total,
            "total_page": total_page,
            "skipped_rows": skipped_rows,
            "skipped_examples": skipped_examples,
            "duplicate_rows": duplicate_rows,
        }

        print(
            f"Fetched page {page}/{total_page or '?'}: "
            f"{len(page_rows)} rows"
            f"{f', skipped {page_skipped}' if page_skipped else ''}, "
            f"{f'duplicates {page_duplicates}, ' if page_duplicates else ''}"
            f"accumulated {len(rows)}/{target_limit or total or '?'}",
            flush=True,
        )

        if target_limit is not None and len(rows) >= target_limit:
            rows = rows[:target_limit]
            break
        if total_page and page >= total_page:
            break

        page += 1
        if args.sleep > 0:
            time.sleep(args.sleep)

    return rows, latest_meta


def fetch_history_to_csv(args: argparse.Namespace, path: Path) -> tuple[int, dict[str, Any]]:
    """Fetch history and write each valid row to a temporary CSV as pages arrive."""
    temp_path = path.with_suffix(path.suffix + ".tmp")
    page = 1
    total = None
    total_page = None
    target_limit = None if args.all else args.limit
    written_rows = 0
    skipped_rows = 0
    skipped_examples: list[dict[str, Any]] = []
    newest_row: dict[str, Any] | None = None
    oldest_row: dict[str, Any] | None = None
    latest_meta: dict[str, Any] = {}
    duplicate_rows = 0
    seen_keys: set[str] = set()
    expected_count = int(getattr(args, "expected_count", 20))
    total_numbers = int(getattr(args, "total_numbers", 80))

    with temp_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fieldnames())
        writer.writeheader()

        while True:
            data = post_history_page(
                lottery_id=args.lottery_id,
                page=page,
                page_size=args.page_size,
                timeout=args.timeout,
                retries=args.retries,
                retry_sleep=args.retry_sleep,
            )
            total = int(data.get("total") or 0)
            total_page = int(data.get("totalPage") or 0)
            items = data.get("list") or []
            if not items:
                break

            page_rows = 0
            page_skipped = 0
            page_duplicates = 0
            reached_limit = False
            for item in items:
                try:
                    row = normalize_row(
                        item,
                        expected_count=expected_count,
                        total_numbers=total_numbers,
                    )
                except ValueError as exc:
                    page_skipped += 1
                    skipped_rows += 1
                    if len(skipped_examples) < 5:
                        skipped_examples.append(skipped_example(page, item, exc))
                    continue

                key = str(row.get("draw_event_id") or row.get("id"))
                if key and key in seen_keys:
                    page_duplicates += 1
                    duplicate_rows += 1
                    continue
                if key:
                    seen_keys.add(key)

                if newest_row is None:
                    newest_row = row
                oldest_row = row
                writer.writerow(row)
                written_rows += 1
                page_rows += 1

                if target_limit is not None and written_rows >= target_limit:
                    reached_limit = True
                    break

            latest_meta = {
                "page": data.get("page"),
                "page_size": data.get("pageSize"),
                "total": total,
                "total_page": total_page,
                "skipped_rows": skipped_rows,
                "skipped_examples": skipped_examples,
                "duplicate_rows": duplicate_rows,
                "newest_row": newest_row,
                "oldest_row": oldest_row,
            }

            print(
                f"Fetched page {page}/{total_page or '?'}: "
                f"{page_rows} rows"
                f"{f', skipped {page_skipped}' if page_skipped else ''}, "
                f"{f'duplicates {page_duplicates}, ' if page_duplicates else ''}"
                f"written {written_rows}/{target_limit or total or '?'}",
                flush=True,
            )

            if reached_limit:
                break
            if total_page and page >= total_page:
                break

            page += 1
            if args.sleep > 0:
                time.sleep(args.sleep)

    replace_path_with_retry(temp_path, path)
    latest_meta["written_rows"] = written_rows
    return written_rows, latest_meta


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch BC.Game Slovakia E-Klub Keno 20/80 draw history to CSV."
    )
    parser.add_argument("--lottery-id", default=DEFAULT_LOTTERY_ID)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-count", type=int, default=20)
    parser.add_argument("--total-numbers", type=int, default=80)
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum rows to fetch unless --all is supplied. Default: 1000.",
    )
    parser.add_argument("--all", action="store_true", help="Fetch all available rows.")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=0.15, help="Sleep between pages.")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-sleep", type=float, default=1.0)
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run keno_triple_omission.py after writing the CSV.",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=DATA_ROOT / "bc_triples_report.csv",
        help="Output CSV for --analyze. Default: data/bc_triples_report.csv.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="Top omitted triples to print when --analyze is used. Default: 30.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.limit < 1 and not args.all:
        parser.error("--limit must be positive unless --all is supplied")
    if args.page_size < 1 or args.page_size > 500:
        parser.error("--page-size must be between 1 and 500")
    if args.expected_count < 1 or args.expected_count > MAX_NUMBER_COLUMNS:
        parser.error(f"--expected-count must be between 1 and {MAX_NUMBER_COLUMNS}")
    if args.total_numbers < args.expected_count:
        parser.error("--total-numbers must be >= --expected-count")

    row_count, meta = fetch_history_to_csv(args, args.out)

    print(flush=True)
    print(f"Wrote {row_count} rows to {args.out}", flush=True)
    if meta:
        print(
            f"API reported total={meta.get('total')} rows, "
            f"total_page={meta.get('total_page')}, page_size={meta.get('page_size')}",
            flush=True,
        )
        if meta.get("skipped_rows"):
            print(
                f"Skipped {meta.get('skipped_rows')} invalid or unfinished rows",
                flush=True,
            )
            for example in meta.get("skipped_examples") or []:
                print(f"  skip example: {example}", flush=True)
        if meta.get("duplicate_rows"):
            print(
                f"Skipped {meta.get('duplicate_rows')} duplicate rows caused by moving API pages",
                flush=True,
            )
    newest = meta.get("newest_row") if meta else None
    oldest = meta.get("oldest_row") if meta else None
    if newest and oldest:
        print(
            "Newest draw: "
            f"{newest['draw_event_id']} at {newest['draw_time_utc']} "
            f"numbers={','.join(str(newest[column]) for column in NUMBER_COLUMNS[:args.expected_count])}",
            flush=True,
        )
        print(
            "Oldest fetched draw: "
            f"{oldest['draw_event_id']} at {oldest['draw_time_utc']}",
            flush=True,
        )

    if args.analyze:
        analyzer = Path(__file__).with_name("keno_triple_omission.py")
        command = [
            sys.executable,
            str(analyzer),
            "--history",
            str(args.out),
            "--newest-first",
            "--top",
            str(args.top),
            "--out",
            str(args.report_out),
        ]
        print(flush=True)
        print("Running omission analysis...", flush=True)
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
