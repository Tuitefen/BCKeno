#!/usr/bin/env python3
"""
Analyze Keno odds and consecutive 3-number omissions.

Input history format:
  - one draw per row
  - either exactly 20 number columns, or metadata columns followed by 20 numbers
  - numbers must be unique integers within the configured total-number range

Examples:
  python keno_triple_omission.py
  python keno_triple_omission.py --history history.csv --top 30
  python keno_triple_omission.py --history data/bc_spain_l_express_20_70_history.csv --newest-first --top 30
  python keno_triple_omission.py --history history.csv --number-columns n1,n2,n3,...,n20
  python keno_triple_omission.py --history history.csv --out data/bc_spain_triples_report.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TOTAL_NUMBERS = 70
DRAWN_NUMBERS = 20
DRAW_INTERVAL_MINUTES = 4

# Default 20/70 main-number odds. Interpreted as total decimal payout.
PAY_TABLE = {
    1: 3.2,
    2: 11.0,
    3: 40.0,
    4: 150.0,
    5: 500.0,
    6: 2000.0,
    7: 6500.0,
    8: 18000.0,
}

TRIPLES = tuple((start, start + 1, start + 2) for start in range(1, TOTAL_NUMBERS - 1))


@dataclass
class TripleStats:
    triple: tuple[int, int, int]
    hits: int = 0
    current_miss: int = 0
    max_miss: int = 0
    last_hit_draw: int | None = None


def hit_probability(picks: int) -> float:
    """Probability that all selected picks are included in the configured draw."""
    if picks < 1 or picks > DRAWN_NUMBERS:
        raise ValueError(f"picks must be between 1 and {DRAWN_NUMBERS}")
    return math.comb(TOTAL_NUMBERS - picks, DRAWN_NUMBERS - picks) / math.comb(
        TOTAL_NUMBERS, DRAWN_NUMBERS
    )


def no_three_run_count(total_numbers: int, drawn_numbers: int) -> int:
    """Count draws with no three consecutive selected numbers."""
    # dp[(picked_count, current_run_len)] = count.
    # current_run_len is 0, 1, or 2 selected numbers at the end of the prefix.
    dp: dict[tuple[int, int], int] = {(0, 0): 1}
    for _ in range(total_numbers):
        next_dp: dict[tuple[int, int], int] = {}
        for (picked, run_len), count in dp.items():
            # Current number not selected.
            key = (picked, 0)
            next_dp[key] = next_dp.get(key, 0) + count

            # Current number selected, but do not create a 3-run.
            if picked < drawn_numbers and run_len < 2:
                key = (picked + 1, run_len + 1)
                next_dp[key] = next_dp.get(key, 0) + count
        dp = next_dp
    return sum(count for (picked, _run_len), count in dp.items() if picked == drawn_numbers)


def fmt_pct(value: float, digits: int = 4) -> str:
    return f"{value * 100:.{digits}f}%"


def fmt_float(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def print_probability_table() -> None:
    print(f"Keno {DRAWN_NUMBERS}/{TOTAL_NUMBERS} probability table")
    print("=" * 72)
    print(
        "Pick | P(all hit) | Fair total odds | Screen odds | EV total payout | EV if odds are profit"
    )
    print("-" * 72)
    for picks, odds in PAY_TABLE.items():
        p_hit = hit_probability(picks)
        fair_total_odds = 1 / p_hit
        ev_total = p_hit * odds - 1
        ev_profit_only = p_hit * (odds + 1) - 1
        print(
            f"{picks:>4} | "
            f"{fmt_pct(p_hit):>10} | "
            f"{fair_total_odds:>15.2f}x | "
            f"{odds:>10.4g}x | "
            f"{fmt_pct(ev_total):>15} | "
            f"{fmt_pct(ev_profit_only):>17}"
        )

    p3 = hit_probability(3)
    expected_draws = 1 / p3
    print()
    print("Key 3-pick numbers")
    print(f"- Specific 3-number ticket hit probability: {fmt_pct(p3)}")
    print(f"- Average waiting time for one fixed 3-number ticket: {expected_draws:.2f} draws")
    print(
        f"- At one draw every {DRAW_INTERVAL_MINUTES:g} minutes: "
        f"{expected_draws * DRAW_INTERVAL_MINUTES:.1f} minutes"
    )
    print(f"- Break-even total payout for 3 picks: {expected_draws:.2f}x")
    print(f"- 60x total payout EV: {fmt_pct(p3 * 60 - 1)}")

    total_draws = math.comb(TOTAL_NUMBERS, DRAWN_NUMBERS)
    no_run = no_three_run_count(TOTAL_NUMBERS, DRAWN_NUMBERS)
    any_run_probability = 1 - no_run / total_draws
    expected_windows = len(TRIPLES) * p3
    print()
    print("Consecutive triples")
    print(
        f"- Consecutive 3-number windows: {len(TRIPLES)} groups, "
        f"1-2-3 through {TOTAL_NUMBERS - 2}-{TOTAL_NUMBERS - 1}-{TOTAL_NUMBERS}"
    )
    print(f"- A fixed consecutive triple has the same hit probability: {fmt_pct(p3)}")
    print(f"- Expected hit consecutive windows per draw: {expected_windows:.3f}")
    print(f"- Probability a draw contains at least one 3-run anywhere: {fmt_pct(any_run_probability)}")


def parse_int_cell(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    if re.fullmatch(r"[+-]?\d+", text) is None:
        return None
    return int(text)


def parse_number_list(value: str) -> list[int]:
    return [int(item) for item in re.findall(r"\d+", value)]


def validate_draw(numbers: Iterable[int], row_number: int) -> tuple[int, ...]:
    draw = tuple(numbers)
    if len(draw) != DRAWN_NUMBERS:
        raise ValueError(
            f"row {row_number}: expected {DRAWN_NUMBERS} drawn numbers, got {len(draw)}"
        )
    bad = [number for number in draw if number < 1 or number > TOTAL_NUMBERS]
    if bad:
        raise ValueError(f"row {row_number}: numbers out of 1..{TOTAL_NUMBERS} range: {bad}")
    if len(set(draw)) != len(draw):
        raise ValueError(f"row {row_number}: duplicate numbers in draw: {draw}")
    return draw


def read_history(
    path: Path,
    *,
    delimiter: str,
    encoding: str,
    number_columns: list[str] | None,
) -> list[tuple[int, ...]]:
    with path.open("r", newline="", encoding=encoding) as fh:
        if number_columns:
            reader = csv.DictReader(fh, delimiter=delimiter)
            if reader.fieldnames is None:
                raise ValueError("CSV has no header row; remove --number-columns or add headers")
            missing_columns = [name for name in number_columns if name not in reader.fieldnames]
            if missing_columns:
                raise ValueError(f"missing number columns: {', '.join(missing_columns)}")

            draws: list[tuple[int, ...]] = []
            for row_number, row in enumerate(reader, start=2):
                if len(number_columns) == 1:
                    draw = parse_number_list(row[number_columns[0]] or "")
                else:
                    draw = []
                    for column in number_columns:
                        value = parse_int_cell(row[column] or "")
                        if value is None:
                            raise ValueError(
                                f"row {row_number}: column {column!r} is not an integer"
                            )
                        draw.append(value)
                draws.append(validate_draw(draw, row_number))
            return draws

        reader = csv.reader(fh, delimiter=delimiter)
        draws = []
        for row_number, row in enumerate(reader, start=1):
            if not row or all(not cell.strip() for cell in row):
                continue
            if row[0].lstrip().startswith("#"):
                continue

            strict_numbers = [
                parsed
                for parsed in (parse_int_cell(cell) for cell in row)
                if parsed is not None and 1 <= parsed <= TOTAL_NUMBERS
            ]

            if len(strict_numbers) < DRAWN_NUMBERS and len(row) == 1:
                strict_numbers = [
                    number
                    for number in parse_number_list(row[0])
                    if 1 <= number <= TOTAL_NUMBERS
                ]

            if len(strict_numbers) < DRAWN_NUMBERS:
                # Probably a header row.
                if not draws:
                    continue
                raise ValueError(
                    f"row {row_number}: could not find {DRAWN_NUMBERS} number cells"
                )

            # If metadata columns are present, keep the last 20 valid number cells.
            draw = strict_numbers[-DRAWN_NUMBERS:]
            draws.append(validate_draw(draw, row_number))
        return draws


def analyze_triples(draws: list[tuple[int, ...]]) -> list[TripleStats]:
    stats = {triple: TripleStats(triple=triple) for triple in TRIPLES}

    for draw_index, draw in enumerate(draws, start=1):
        draw_set = set(draw)
        for triple, item in stats.items():
            if all(number in draw_set for number in triple):
                item.hits += 1
                item.last_hit_draw = draw_index
                item.max_miss = max(item.max_miss, item.current_miss)
                item.current_miss = 0
            else:
                item.current_miss += 1
                item.max_miss = max(item.max_miss, item.current_miss)

    return list(stats.values())


def tail_probability(misses: int, p_hit: float) -> float:
    """Probability that a fixed triple misses at least this many consecutive draws."""
    return (1 - p_hit) ** misses


def print_triple_report(stats: list[TripleStats], draw_count: int, top: int) -> None:
    p3 = hit_probability(3)
    expected_wait = 1 / p3
    ranked = sorted(stats, key=lambda item: (-item.current_miss, -item.max_miss, item.triple))

    print()
    print(f"Triple omission report: {draw_count} draws")
    print("=" * 72)
    print(f"Fixed-triple hit probability: {fmt_pct(p3)}")
    print(f"Theoretical average wait: {expected_wait:.2f} draws ({expected_wait * 2:.1f} minutes)")
    print()
    print(
        "Rank | Triple   | Current miss | Max miss | Hits | Last hit draw | Miss tail"
    )
    print("-" * 72)
    for index, item in enumerate(ranked[:top], start=1):
        triple_text = "-".join(str(number) for number in item.triple)
        last_hit = "-" if item.last_hit_draw is None else str(item.last_hit_draw)
        miss_tail = tail_probability(item.current_miss, p3)
        print(
            f"{index:>4} | "
            f"{triple_text:<8} | "
            f"{item.current_miss:>12} | "
            f"{item.max_miss:>8} | "
            f"{item.hits:>4} | "
            f"{last_hit:>13} | "
            f"{fmt_pct(miss_tail):>9}"
        )

    total_hits = sum(item.hits for item in stats)
    avg_hits_per_draw = total_hits / draw_count if draw_count else 0
    print()
    print(f"Observed consecutive-window hits per draw: {avg_hits_per_draw:.3f}")
    print(
        "Note: current omission is historical information only; it does not increase "
        "the next-draw hit probability for that triple."
    )


def write_report_csv(path: Path, stats: list[TripleStats], draw_count: int) -> None:
    p3 = hit_probability(3)
    ranked = sorted(stats, key=lambda item: (-item.current_miss, -item.max_miss, item.triple))
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "triple",
                "current_miss",
                "max_miss",
                "hits",
                "last_hit_draw",
                "miss_tail_probability",
                "draw_count",
            ]
        )
        for item in ranked:
            writer.writerow(
                [
                    "-".join(str(number) for number in item.triple),
                    item.current_miss,
                    item.max_miss,
                    item.hits,
                    "" if item.last_hit_draw is None else item.last_hit_draw,
                    f"{tail_probability(item.current_miss, p3):.12f}",
                    draw_count,
                ]
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Analyze Keno {DRAWN_NUMBERS}/{TOTAL_NUMBERS} probabilities and consecutive triple omissions."
    )
    parser.add_argument(
        "--history",
        type=Path,
        help="CSV file with one draw per row. Omit to print theory only.",
    )
    parser.add_argument(
        "--number-columns",
        help=(
            "Comma-separated draw-number columns. Use one column name if that column "
            "contains all 20 numbers."
        ),
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="CSV delimiter. Default: comma. Use '\\t' for tab-separated files.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Input file encoding. Default: utf-8-sig.",
    )
    parser.add_argument("--top", type=int, default=20, help="Top omitted triples to print.")
    parser.add_argument("--out", type=Path, help="Write the full triple report to CSV.")
    parser.add_argument(
        "--newest-first",
        action="store_true",
        help=(
            "Use when the input CSV is sorted newest-to-oldest. The analyzer will "
            "reverse it so current omission is calculated at the latest draw."
        ),
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    delimiter = "\t" if args.delimiter == r"\t" else args.delimiter
    number_columns = (
        [column.strip() for column in args.number_columns.split(",") if column.strip()]
        if args.number_columns
        else None
    )

    print_probability_table()

    if args.history is None:
        print()
        print("No --history file supplied, so only theoretical probabilities were printed.")
        return 0

    draws = read_history(
        args.history,
        delimiter=delimiter,
        encoding=args.encoding,
        number_columns=number_columns,
    )
    if not draws:
        raise ValueError("history file did not contain any valid draws")
    if args.newest_first:
        draws.reverse()

    stats = analyze_triples(draws)
    print_triple_report(stats, len(draws), args.top)

    if args.out:
        write_report_csv(args.out, stats, len(draws))
        print()
        print(f"Full report written to: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
