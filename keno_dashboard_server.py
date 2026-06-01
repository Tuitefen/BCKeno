#!/usr/bin/env python3
"""
Local web dashboard API for BC.Game multi-market Keno analysis and tracking.

No third-party dependencies are required. The server serves static frontend files
from ./web and exposes JSON endpoints for data refresh and analysis.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import mimetypes
import re
import sqlite3
import threading
import time
import traceback
import uuid
from bisect import bisect_left
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from itertools import combinations
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from zoneinfo import ZoneInfo

import fetch_bc_keno_history
import fetch_etipos_archive
import fetch_official_supplements
import keno_triple_omission


class RequestBodyTooLarge(ValueError):
    pass


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
DEFAULT_HISTORY = ROOT / "bc_keno_history.csv"
DEFAULT_BETS = ROOT / "simulated_bets.jsonl"
DEFAULT_PREDICTION_TRACKING = ROOT / "prediction_tracking.json"
DEFAULT_PREDICTION_TRACKING_DB = ROOT / "prediction_tracking.sqlite3"
DEFAULT_PREDICTION_AUTO_CONFIG = ROOT / "prediction_auto_config.json"
DEFAULT_LOTTERY_ID = "74214"
DEFAULT_GAME_KEY = "sk_keno_20_80"
HOST = "127.0.0.1"
PORT = 8787
DEFAULT_PAGE_SIZE = 100
DEFAULT_SYNC_SLEEP = 0.25

MAX_NUMBER_COLUMNS = 20
NUMBER_COLUMNS = [f"n{i}" for i in range(1, MAX_NUMBER_COLUMNS + 1)]
SUPPLEMENT_ID_PREFIXES = ("etipos-", "lotodate-", "polonia-loto-", "yesplay-", "winforlife-", "wflcloud-")
DATA_LOCK = threading.Lock()
BETS_LOCK = threading.Lock()
ANALYSIS_CACHE_LOCK = threading.Lock()
PREDICTION_CACHE_LOCK = threading.Lock()
BACKTEST_CACHE_LOCK = threading.Lock()
BACKTEST_STATUS_LOCK = threading.Lock()
BACKTEST_SCAN_CACHE_LOCK = threading.Lock()
BACKTEST_SCAN_STATUS_LOCK = threading.Lock()
HISTORY_CACHE_LOCK = threading.Lock()
PREDICTION_TRACKING_LOCK = threading.Lock()
PREDICTION_TRACKING_AUTO_SYNC_LOCK = threading.Lock()
PREDICTION_DB_INIT_LOCK = threading.Lock()
PREDICTION_AUTO_LOCK = threading.Lock()
PREDICTION_AUTO_STOP = threading.Event()
PREDICTION_AUTO_THREAD: threading.Thread | None = None
PREDICTION_DB_INITIALIZED = False
HISTORY_CACHE_MAX_ITEMS = 5
ANALYSIS_CACHE_MAX_ITEMS = 5
PREDICTION_CACHE_MAX_ITEMS = 5
HISTORY_CACHE: dict[tuple[str, int, int], list[dict[str, Any]]] = {}
ANALYSIS_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}
PREDICTION_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}
BACKTEST_CACHE: dict[str, dict[str, Any]] = {}
BACKTEST_SCAN_CACHE: dict[str, dict[str, Any]] = {}
BACKTEST_STATUS: dict[str, Any] = {
    "ok": True,
    "status": "idle",
    "jobId": "",
    "progress": 0,
    "message": "暂无回测任务",
    "generatedAt": "",
}
BACKTEST_SCAN_STATUS: dict[str, Any] = {
    "ok": True,
    "status": "idle",
    "jobId": "",
    "progress": 0,
    "message": "尚未扫描",
    "generatedAt": "",
}
PREDICTION_AUTO_STATUS: dict[str, Any] = {
    "ok": True,
    "status": "stopped",
    "enabled": False,
    "running": False,
    "lastRunAt": "",
    "nextRunAt": "",
    "message": "自动追踪未启动",
    "results": [],
    "errors": [],
}
PREDICTION_AUTO_HISTORY_MARKERS: dict[str, tuple[int, int, str, str]] = {}
PREDICTION_TRACKING_AUTO_SYNC_LAST_ATTEMPT: dict[str, float] = {}
PREDICTION_VOID_REASON_MISSING_TARGET = "目标期开奖缺失，且后续期次已到达，追踪作废"
PREDICTION_VOID_REASON_PAST_TARGET = "预测创建晚于目标期开奖，追踪作废"
PREDICTION_VOID_REASON_SUPERSEDED = "同期开奖已有更新预测批次，较早批次作废"
LEGACY_VOID_REASONS = {
    "Target draw was skipped after later draws arrived; tracking voided": PREDICTION_VOID_REASON_MISSING_TARGET,
}

LOTTERY_GAMES: dict[str, dict[str, Any]] = {
    "sk_keno_20_80": {
        "key": "sk_keno_20_80",
        "lotteryId": "74214",
        "name": "斯洛伐克 E-Klub Keno",
        "shortName": "斯洛伐克 20/80",
        "country": "Slovakia",
        "drawnNumbers": 20,
        "totalNumbers": 80,
        "drawIntervalMinutes": 2,
        "historyPath": DEFAULT_HISTORY,
        "supportsAnalysis": False,
        "supportsPredictions": False,
        "supportsPredictionTracking": False,
        "supportsSimBets": False,
        "supportsBacktest": False,
        "supportsMartingale": False,
        "officialSupplement": "lotodate",
        "supplementUrl": "https://lotodate.ro/en/Extrageri/1-slovakia-eklub-keno-20-80",
    },
    "spain_l_express_20_70": {
        "key": "spain_l_express_20_70",
        "lotteryId": "115889",
        "name": "西班牙快车 L Express",
        "shortName": "西班牙快车 20/70",
        "country": "Spain",
        "drawnNumbers": 20,
        "totalNumbers": 70,
        "drawIntervalMinutes": 4,
        "historyPath": ROOT / "bc_spain_l_express_20_70_history.csv",
        "supportsAnalysis": True,
        "supportsPredictions": True,
        "officialSupplement": "lotodate",
        "supplementUrl": "https://lotodate.ro/en/Extrageri/5-spain-l-express-20-70",
        "operatingHours": {"timezone": "Europe/Madrid", "start": "07:06", "end": "23:58"},
    },
    "poland_keno_20_70": {
        "key": "poland_keno_20_70",
        "lotteryId": "79830",
        "name": "波兰基诺",
        "shortName": "波兰基诺 20/70",
        "country": "Poland",
        "drawnNumbers": 20,
        "totalNumbers": 70,
        "drawIntervalMinutes": 4,
        "historyPath": ROOT / "bc_poland_keno_20_70_history.csv",
        "supportsAnalysis": True,
        "supportsPredictions": True,
        "officialSupplement": "lotodate",
        "supplementUrl": "https://lotodate.ro/en/Extrageri/4-poland-keno-20-70",
        "operatingHours": {"timezone": "Europe/Warsaw", "start": "06:34", "end": "23:54"},
    },
    "russia_rapido_8_20": {
        "key": "russia_rapido_8_20",
        "lotteryId": "56526",
        "name": "快速俄罗斯 Rapido",
        "shortName": "快速俄罗斯 8/20",
        "country": "Russia",
        "drawnNumbers": 8,
        "totalNumbers": 20,
        "drawIntervalMinutes": 15,
        "historyPath": ROOT / "bc_russia_rapido_8_20_history.csv",
        "supportsAnalysis": True,
        "supportsPredictions": True,
        "officialSupplement": "yesplay",
        "supplementUrl": "https://yesplay.bet/lucky-numbers/russia_rapido/results",
        "hasBonusBall": True,
        "bonusBallTotalNumbers": 4,
        "bonusBallPredictionCount": 2,
        "bonusBallPredictionLabel": "1主1辅",
    },
    "italy_win_for_life_10_20": {
        "key": "italy_win_for_life_10_20",
        "lotteryId": "69692",
        "name": "意大利 Win for Life 经典版",
        "shortName": "意大利终身赢 10/20",
        "country": "Italy",
        "drawnNumbers": 10,
        "totalNumbers": 20,
        "drawIntervalMinutes": 60,
        "historyPath": ROOT / "bc_italy_win_for_life_10_20_history.csv",
        "supportsAnalysis": True,
        "supportsPredictions": True,
        "officialSupplement": "lotodate",
        "supplementUrl": "https://lotodate.ro/en/Extrageri/11-italy-win-for-life-classico-10-20",
        "hasBonusBall": True,
        "bonusBallTotalNumbers": 20,
        "bonusBallPredictionCount": 3,
        "bonusBallPredictionLabel": "1主2辅",
        "operatingHours": {"timezone": "Europe/Rome", "start": "07:00", "end": "23:00"},
    },
}
SUM_RANGES = [
    ("210-600", 210, 600),
    ("601-634", 601, 634),
    ("635-700", 635, 700),
    ("701-730", 701, 730),
    ("731-760", 731, 760),
    ("761-790", 761, 790),
    ("791-809", 791, 809),
    ("810-829", 810, 829),
    ("830-859", 830, 859),
    ("860-889", 860, 889),
    ("890-919", 890, 919),
    ("920-985", 920, 985),
    ("986-1019", 986, 1019),
    ("1020-1410", 1020, 1410),
]
SUM_RANGES_20_70 = [
    ("210-529", 210, 529),
    ("530-559", 530, 559),
    ("560-589", 560, 589),
    ("590-629", 590, 629),
    ("630-659", 630, 659),
    ("660-689", 660, 689),
    ("690-709", 690, 709),
    ("710-730", 710, 730),
    ("731-760", 731, 760),
    ("761-790", 761, 790),
    ("791-830", 791, 830),
    ("831-860", 831, 860),
    ("861-890", 861, 890),
    ("891-1210", 891, 1210),
]
SUM_RANGES_8_20 = [
    ("36-53", 36, 53),
    ("54-58", 54, 58),
    ("59-64", 59, 64),
    ("65-69", 65, 69),
    ("70-73", 70, 73),
    ("74-78", 74, 78),
    ("79-83", 79, 83),
    ("84-89", 84, 89),
    ("90-94", 90, 94),
    ("95-98", 95, 98),
    ("99-103", 99, 103),
    ("104-109", 104, 109),
    ("110-114", 110, 114),
    ("115-132", 115, 132),
]
SUM_RANGES_10_20 = [
    ("55-77", 55, 77),
    ("78-83", 78, 83),
    ("84-89", 84, 89),
    ("90-95", 90, 95),
    ("96-101", 96, 101),
    ("102-107", 102, 107),
    ("108-113", 108, 113),
    ("114-119", 114, 119),
    ("120-125", 120, 125),
    ("126-131", 126, 131),
    ("132-137", 132, 137),
    ("138-143", 138, 143),
    ("144-149", 144, 149),
    ("150-155", 150, 155),
]
LOTTERY_GAMES["spain_l_express_20_70"]["sumRanges"] = SUM_RANGES_20_70
LOTTERY_GAMES["poland_keno_20_70"]["sumRanges"] = SUM_RANGES_20_70
LOTTERY_GAMES["russia_rapido_8_20"]["sumRanges"] = SUM_RANGES_8_20
LOTTERY_GAMES["italy_win_for_life_10_20"]["sumRanges"] = SUM_RANGES_10_20
RUN_CONDITIONS = [
    ("all", "全部开奖"),
    ("hasPair", "含两连"),
    ("hasDoublePair", "含双两连"),
    ("hasTriplePairSet", "含三双两连"),
    ("hasTriple", "含三连"),
    ("hasQuadPairSet", "含四双两连"),
    ("hasFivePairSet", "含五双两连"),
    ("hasPairTriple", "含两连+三连"),
    ("hasDoubleTriple", "含双三连"),
    ("hasTripleDoublePair", "含三连配双两连"),
    ("hasQuad", "含四连"),
    ("hasQuadPair", "含四连+两连"),
    ("hasFive", "含五连"),
    ("hasSix", "含六连"),
]
RUN_CONDITION_LABELS = dict(RUN_CONDITIONS)
RUSSIA_ITALY_RUN_CONDITION_KEYS = [
    "hasPair",
    "hasDoublePair",
    "hasTriplePairSet",
    "hasTriple",
    "hasPairTriple",
    "hasTripleDoublePair",
    "hasQuad",
    "hasQuadPair",
    "hasFive",
    "hasSix",
]
LOTTERY_GAMES["russia_rapido_8_20"]["runConditionKeys"] = RUSSIA_ITALY_RUN_CONDITION_KEYS
LOTTERY_GAMES["russia_rapido_8_20"]["predictionConditionKeys"] = LOTTERY_GAMES[
    "russia_rapido_8_20"
]["runConditionKeys"]
LOTTERY_GAMES["italy_win_for_life_10_20"]["runConditionKeys"] = RUSSIA_ITALY_RUN_CONDITION_KEYS
LOTTERY_GAMES["italy_win_for_life_10_20"]["predictionConditionKeys"] = LOTTERY_GAMES[
    "italy_win_for_life_10_20"
]["runConditionKeys"]
PREDICTION_HORIZONS = 5
PREDICTION_TRACKING_LEAD_SECONDS = 45
PREDICTION_TRACKING_AUTO_SYNC_COOLDOWN_SECONDS = 45
PREDICTION_RECENT_WINDOW = 240
PREDICTION_NUMBER_WEIGHTS = [
    {"miss": 0.50, "momentum": 0.32, "history": 0.18},
    {"miss": 0.45, "momentum": 0.28, "history": 0.27},
    {"miss": 0.40, "momentum": 0.24, "history": 0.36},
    {"miss": 0.35, "momentum": 0.21, "history": 0.44},
    {"miss": 0.30, "momentum": 0.18, "history": 0.52},
]
PREDICTION_PATTERN_LABELS = {
    "pair": "两连号",
    "triple": "三连号",
    "quad": "四连号",
    "hasPair": "两连",
    "hasDoublePair": "双两连",
    "hasTriplePairSet": "三双两连",
    "hasTriple": "三连",
    "hasQuadPairSet": "四双两连",
    "hasFivePairSet": "五双两连",
    "hasPairTriple": "两连+三连",
    "hasDoubleTriple": "双三连",
    "hasTripleDoublePair": "三连+双两连",
    "hasQuad": "四连",
    "hasQuadPair": "四连+两连",
    "hasFive": "五连",
    "hasSix": "六连",
}
BET_TYPES = {
    "numbers": {
        "label": "号码组选全中",
        "requiresNumbers": True,
        "minNumbers": 1,
        "maxNumbers": 20,
        "defaultOdds": 60,
    },
    "pair": {
        "label": "指定两连号",
        "requiresNumbers": True,
        "exactNumbers": 2,
        "defaultOdds": 60,
    },
    "triple": {
        "label": "指定三连号",
        "requiresNumbers": True,
        "exactNumbers": 3,
        "defaultOdds": 60,
    },
    "quad": {
        "label": "指定四连号",
        "requiresNumbers": True,
        "exactNumbers": 4,
        "defaultOdds": 60,
    },
    "hasPair": {"label": "任意两连", "requiresNumbers": False, "defaultOdds": 60},
    "hasDoublePair": {"label": "双两连", "requiresNumbers": False, "defaultOdds": 60},
    "hasTriplePairSet": {"label": "三双两连", "requiresNumbers": False, "defaultOdds": 60},
    "hasTriple": {"label": "任意三连", "requiresNumbers": False, "defaultOdds": 60},
    "hasQuadPairSet": {"label": "四双两连", "requiresNumbers": False, "defaultOdds": 60},
    "hasFivePairSet": {"label": "五双两连", "requiresNumbers": False, "defaultOdds": 60},
    "hasPairTriple": {"label": "两连+三连", "requiresNumbers": False, "defaultOdds": 60},
    "hasDoubleTriple": {"label": "双三连", "requiresNumbers": False, "defaultOdds": 60},
    "hasTripleDoublePair": {
        "label": "三连+双两连",
        "requiresNumbers": False,
        "defaultOdds": 60,
    },
    "hasQuad": {"label": "任意四连", "requiresNumbers": False, "defaultOdds": 60},
    "hasQuadPair": {"label": "四连+两连", "requiresNumbers": False, "defaultOdds": 60},
    "hasFive": {"label": "任意五连", "requiresNumbers": False, "defaultOdds": 60},
    "hasSix": {"label": "任意六连", "requiresNumbers": False, "defaultOdds": 60},
}
BACKTEST_CACHE_TTL_SECONDS = 300
BACKTEST_SCAN_CACHE_TTL_SECONDS = 300
BACKTEST_MAX_TRAIN_WINDOW = 30000
BACKTEST_MAX_TEST_WINDOW = 5000
BACKTEST_CURVE_STEP = 10
BACKTEST_SCAN_DEFAULT_TOP_NS = (1, 2, 3, 5)
BACKTEST_SCAN_DEFAULT_MISS_THRESHOLDS = (0, 5, 10, 20, 30)
BACKTEST_SCAN_EXACT_RUN_LENGTHS = (2, 3, 4)
BACKTEST_SCAN_MAX_RESULTS = 80
BACKTEST_SHAPE_GROUP_LIMIT = 20000
BACKTEST_SHAPE_FIXED_SCAN_LIMIT = 10000
DEFAULT_MAIN_ODDS_BY_GAME = {
    "sk_keno_20_80": {1: 3.6, 2: 15, 3: 60, 4: 250, 5: 1000, 6: 3800, 7: 12500, 8: 35000},
    "spain_l_express_20_70": {1: 3.2, 2: 11, 3: 40, 4: 150, 5: 500, 6: 2000, 7: 6500, 8: 18000},
    "poland_keno_20_70": {1: 3.2, 2: 11, 3: 40, 4: 150, 5: 500, 6: 2000, 7: 6500, 8: 18000},
    "italy_win_for_life_10_20": {1: 1.8, 2: 3.8, 3: 9, 4: 20, 5: 50, 6: 150, 7: 500, 8: 1650},
    "russia_rapido_8_20": {1: 2.2, 2: 6, 3: 18, 4: 60, 5: 220, 6: 1000, 7: 5000},
}
DEFAULT_BONUS_ODDS_BY_GAME = {
    "russia_rapido_8_20": {1: 9, 2: 25, 3: 70, 4: 200, 5: 700, 6: 2000, 7: 8000},
    "italy_win_for_life_10_20": {1: 35, 2: 75, 3: 150, 4: 300, 5: 600, 6: 1500, 7: 3000, 8: 10000},
}
PREDICTION_TICKET_STRATEGIES = {
    "italy_win_for_life_10_20": [
        {"mode": "main", "pickCount": 3, "label": "意大利 3球候选票"},
        {"mode": "bonus", "pickCount": 1, "label": "意大利 1+1特殊球候选票"},
    ],
    "russia_rapido_8_20": {"mode": "bonus", "pickCount": 2, "label": "俄罗斯 2+1特殊球候选票"},
    "spain_l_express_20_70": [
        {"mode": "main", "pickCount": 1, "label": "西班牙 1球候选票"},
        {"mode": "main", "pickCount": 2, "label": "西班牙 2球候选票"},
    ],
    "poland_keno_20_70": [
        {"mode": "main", "pickCount": 1, "label": "波兰 1球候选票"},
        {"mode": "main", "pickCount": 2, "label": "波兰 2球候选票"},
    ],
}
PREDICTION_TRACKING_METHOD_VERSION = "strategy-ticket-v1"
PREDICTION_TICKET_BACKTEST_WINDOW = 1000
PREDICTION_TICKET_CHASE_PERIODS = 10
PREDICTION_TICKET_TOP_COUNT = 3
ADJACENT_DERIVED_STATS_GAME_KEYS = {"spain_l_express_20_70", "poland_keno_20_70"}
ADJACENT_DERIVED_EXAMPLE_LIMIT = 4
ADJACENT_DERIVED_HIT_DETAIL_LIMIT = 4
BACKTEST_SIMPLE_SHAPE_RUN_LENGTHS = {
    "hasPair": 2,
    "hasTriple": 3,
    "hasQuad": 4,
    "hasFive": 5,
    "hasSix": 6,
}
BACKTEST_CONDITION_KEYS = tuple(key for key, _label in RUN_CONDITIONS if key != "all")
BACKTEST_STRATEGIES = {
    "exact_numbers",
    "pair_top_n",
    "triple_top_n",
    "quad_top_n",
    "shape_top_n",
    "condition_top_n",
    "condition_fixed",
    "condition",
}


def game_key_from_value(value: Any) -> str:
    text = str(value or "").strip()
    if text in LOTTERY_GAMES:
        return text
    if text:
        for key, config in LOTTERY_GAMES.items():
            if text == str(config["lotteryId"]):
                return key
    return DEFAULT_GAME_KEY


def game_from_query(query: dict[str, list[str]]) -> dict[str, Any]:
    value = query.get("game", query.get("lotteryId", [DEFAULT_GAME_KEY]))[0]
    return LOTTERY_GAMES[game_key_from_value(value)]


def game_from_options(options: dict[str, Any]) -> dict[str, Any]:
    return LOTTERY_GAMES[game_key_from_value(options.get("game") or options.get("lotteryId"))]


def game_public_config(config: dict[str, Any]) -> dict[str, Any]:
    analysis_supported = supports_analysis(config)
    predictions_supported = supports_predictions(config)
    prediction_tracking_supported = supports_prediction_tracking(config)
    sim_bets_supported = supports_sim_bets(config)
    backtest_supported = supports_backtest(config)
    martingale_supported = supports_martingale(config)
    return {
        "key": config["key"],
        "lotteryId": config["lotteryId"],
        "name": config["name"],
        "shortName": config["shortName"],
        "country": config["country"],
        "drawnNumbers": config["drawnNumbers"],
        "totalNumbers": config["totalNumbers"],
        "drawIntervalMinutes": config["drawIntervalMinutes"],
        "supportsHistory": bool(config.get("supportsHistory", True)),
        "supportsAnalysis": analysis_supported,
        "supportsPredictions": predictions_supported,
        "supportsPredictionTracking": prediction_tracking_supported,
        "supportsSimBets": sim_bets_supported,
        "supportsBacktest": backtest_supported,
        "supportsMartingale": martingale_supported,
        "officialSupplement": config.get("officialSupplement", ""),
        "supplementUrl": config.get("supplementUrl", ""),
        "hasBonusBall": bool(config.get("hasBonusBall")),
        "bonusBallTotalNumbers": config.get("bonusBallTotalNumbers") or config["totalNumbers"],
        "operatingHours": config.get("operatingHours"),
        "runConditions": [
            {"key": key, "label": label}
            for key, label in game_run_conditions(config, include_all=False)
        ],
    }


def game_run_conditions(
    config: dict[str, Any],
    *,
    include_all: bool = True,
) -> list[tuple[str, str]]:
    keys = config.get("runConditionKeys")
    if not keys:
        conditions = list(RUN_CONDITIONS)
    else:
        conditions = []
        if include_all:
            conditions.append(("all", RUN_CONDITION_LABELS["all"]))
        for key in keys:
            label = RUN_CONDITION_LABELS.get(str(key))
            if label:
                conditions.append((str(key), label))
    if not include_all:
        conditions = [(key, label) for key, label in conditions if key != "all"]
    return conditions


def game_condition_keys(config: dict[str, Any]) -> tuple[str, ...]:
    return tuple(key for key, _label in game_run_conditions(config, include_all=False))


def games_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "defaultGame": DEFAULT_GAME_KEY,
        "items": [game_public_config(config) for config in LOTTERY_GAMES.values()],
    }


def bc_head_meta(config: dict[str, Any]) -> dict[str, Any]:
    data = fetch_bc_keno_history.post_history_page(
        lottery_id=str(config["lotteryId"]),
        page=1,
        page_size=DEFAULT_PAGE_SIZE,
        timeout=30,
        retries=2,
        retry_sleep=1.0,
    )
    items = data.get("list") or []
    skipped_rows = 0
    for item in items:
        try:
            fetch_bc_keno_history.normalize_row(
                item,
                expected_count=int(config["drawnNumbers"]),
                total_numbers=int(config["totalNumbers"]),
            )
        except ValueError:
            skipped_rows += 1
    newest = items[0] if items else {}
    oldest = items[-1] if items else {}
    return {
        "total": int(data.get("total") or 0),
        "totalPage": int(data.get("totalPage") or 0),
        "pageSize": int(data.get("pageSize") or DEFAULT_PAGE_SIZE),
        "page1Items": len(items),
        "skippedRows": skipped_rows,
        "newestDrawEventId": newest.get("drawEventId", ""),
        "newestDrawTimeMs": parse_int(newest.get("drawTime"), 0),
        "newestDrawTimeUtc": fetch_bc_keno_history.draw_time_iso(newest.get("drawTime")) if newest else "",
        "oldestPage1DrawEventId": oldest.get("drawEventId", ""),
        "oldestPage1DrawTimeUtc": fetch_bc_keno_history.draw_time_iso(oldest.get("drawTime")) if oldest else "",
    }


def integrity_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    game_value = query.get("game", [""])[0]
    configs = (
        [game_from_query(query)]
        if game_value
        else list(LOTTERY_GAMES.values())
    )
    remote = str(query.get("remote", ["1"])[0]).strip().lower() not in {"0", "false", "no"}
    items: list[dict[str, Any]] = []
    for config in configs:
        history_path = game_history_path(config)
        with DATA_LOCK:
            rows = load_history_rows(history_path, config)
        remote_meta: dict[str, Any] | None = None
        remote_error = ""
        if remote:
            try:
                remote_meta = bc_head_meta(config)
            except Exception as exc:
                remote_error = str(exc)
        item = history_data_integrity(rows, config, remote_meta)
        item["game"] = game_public_config(config)
        item["historyFile"] = file_info(history_path)
        if remote_error:
            item["remoteError"] = remote_error
        items.append(item)
    issue_items = [
        item
        for item in items
        if item.get("status") in {"missing", "behind_latest"}
        or item.get("invalidRows")
        or item.get("duplicateTimes")
    ]
    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "remoteChecked": remote,
        "allAligned": not issue_items,
        "items": items,
    }


def game_history_path(config: dict[str, Any]) -> Path:
    return Path(config["historyPath"])


def game_number_columns(config: dict[str, Any]) -> list[str]:
    return NUMBER_COLUMNS[: int(config["drawnNumbers"])]


def run_groups(config: dict[str, Any], length: int) -> tuple[tuple[int, ...], ...]:
    total_numbers = int(config["totalNumbers"])
    return tuple(
        tuple(range(start, start + length))
        for start in range(1, total_numbers - length + 2)
    )


def pair_groups(config: dict[str, Any]) -> tuple[tuple[int, ...], ...]:
    return run_groups(config, 2)


def triple_groups(config: dict[str, Any]) -> tuple[tuple[int, ...], ...]:
    return run_groups(config, 3)


def quad_groups(config: dict[str, Any]) -> tuple[tuple[int, ...], ...]:
    return run_groups(config, 4)


def hit_probability_for(config: dict[str, Any], picks: int) -> float:
    total_numbers = int(config["totalNumbers"])
    drawn_numbers = int(config["drawnNumbers"])
    if picks < 1 or picks > drawn_numbers:
        raise ValueError("picks must be between 1 and drawnNumbers")
    return math.comb(total_numbers - picks, drawn_numbers - picks) / math.comb(
        total_numbers,
        drawn_numbers,
    )


def supports_analysis(config: dict[str, Any]) -> bool:
    return bool(config.get("supportsAnalysis"))


def ensure_analysis_supported(config: dict[str, Any]) -> None:
    if not supports_analysis(config):
        raise ValueError(f"{config['shortName']} 当前仅接入抓取和历史展示，分析规则后续再做")


def supports_predictions(config: dict[str, Any]) -> bool:
    return supports_analysis(config) and bool(config.get("supportsPredictions", True))


def ensure_predictions_supported(config: dict[str, Any]) -> None:
    if not supports_predictions(config):
        raise ValueError(f"{config['shortName']} 当前只保留开奖同步，不再生成预测")


def supports_prediction_tracking(config: dict[str, Any]) -> bool:
    return supports_predictions(config) and bool(config.get("supportsPredictionTracking", True))


def ensure_prediction_tracking_supported(config: dict[str, Any]) -> None:
    if not supports_prediction_tracking(config):
        raise ValueError(f"{config['shortName']} 当前只保留开奖同步，不再生成预测追踪")


def supports_sim_bets(config: dict[str, Any]) -> bool:
    return supports_analysis(config) and bool(config.get("supportsSimBets", True))


def ensure_sim_bets_supported(config: dict[str, Any]) -> None:
    if not supports_sim_bets(config):
        raise ValueError(f"{config['shortName']} 当前只保留开奖同步，不开放模拟投注")


def supports_backtest(config: dict[str, Any]) -> bool:
    return supports_analysis(config) and bool(config.get("supportsBacktest", True))


def ensure_backtest_supported(config: dict[str, Any]) -> None:
    if not supports_backtest(config):
        raise ValueError(f"{config['shortName']} 当前只保留开奖同步，不开放回测")


def supports_martingale(config: dict[str, Any]) -> bool:
    return supports_analysis(config) and bool(config.get("supportsMartingale", True))


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")


def parse_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_datetime_ms(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return 0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.timestamp() * 1000)


def is_cancelled_status(status: Any) -> bool:
    return str(status or "").strip() in fetch_bc_keno_history.CANCELLED_STATUS_CODES


def is_valid_draw_row(
    row: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> bool:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    if row.get("isCancelled") or is_cancelled_status(row.get("status")):
        return False
    drawn_numbers = int(config["drawnNumbers"])
    total_numbers = int(config["totalNumbers"])
    try:
        numbers = [int(number) for number in row.get("numbers") or []]
    except (TypeError, ValueError):
        return False
    return (
        len(numbers) == drawn_numbers
        and len(set(numbers)) == drawn_numbers
        and all(1 <= number <= total_numbers for number in numbers)
    )


def valid_draw_rows(
    rows: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    return [row for row in rows if is_valid_draw_row(row, config)]


def file_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    stat = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "size": stat.st_size,
        "modifiedUtc": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(
            timespec="seconds"
        ),
    }


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
        f"编辑器/杀毒扫描或另一个页面请求占用。请关闭打开该 CSV 的程序后重试。原始错误：{last_error}"
    ) from last_error


def lru_cache_get(cache: dict[Any, Any], key: Any) -> Any:
    if key not in cache:
        return None
    value = cache.pop(key)
    cache[key] = value
    return value


def lru_cache_set(cache: dict[Any, Any], key: Any, value: Any, max_items: int) -> None:
    if key in cache:
        cache.pop(key)
    elif len(cache) >= max_items:
        cache.pop(next(iter(cache)))
    cache[key] = value


def clear_data_caches() -> None:
    with HISTORY_CACHE_LOCK:
        HISTORY_CACHE.clear()
    with ANALYSIS_CACHE_LOCK:
        ANALYSIS_CACHE.clear()
    with PREDICTION_CACHE_LOCK:
        PREDICTION_CACHE.clear()
    with BACKTEST_CACHE_LOCK:
        BACKTEST_CACHE.clear()
    with BACKTEST_STATUS_LOCK:
        if BACKTEST_STATUS.get("status") != "running":
            BACKTEST_STATUS.clear()
            BACKTEST_STATUS.update(
                {
                    "ok": True,
                    "status": "idle",
                    "jobId": "",
                    "progress": 0,
                    "message": "历史数据已更新，请重新运行回测",
                    "generatedAt": utc_now_iso(),
                }
            )
    with BACKTEST_SCAN_CACHE_LOCK:
        BACKTEST_SCAN_CACHE.clear()
    with BACKTEST_SCAN_STATUS_LOCK:
        if BACKTEST_SCAN_STATUS.get("status") != "running":
            BACKTEST_SCAN_STATUS.clear()
            BACKTEST_SCAN_STATUS.update(
                {
                    "ok": True,
                    "status": "idle",
                    "jobId": "",
                    "progress": 0,
                    "message": "历史数据已更新，请重新扫描",
                    "generatedAt": utc_now_iso(),
                }
            )


def history_fieldnames() -> list[str]:
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


def load_history_rows(
    path: Path = DEFAULT_HISTORY,
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    number_columns = game_number_columns(config)
    total_numbers = int(config["totalNumbers"])
    drawn_numbers = int(config["drawnNumbers"])
    if not path.exists():
        return []

    stat = path.stat()
    cache_key = (str(path), stat.st_mtime_ns, stat.st_size)
    with HISTORY_CACHE_LOCK:
        cached_rows = lru_cache_get(HISTORY_CACHE, cache_key)
    if cached_rows is not None:
        return list(cached_rows)

    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for index, row in enumerate(reader, start=1):
            status = row.get("status", "")
            try:
                raw_numbers = [row.get(column, "") for column in number_columns]
                balls = [int(value) for value in raw_numbers if str(value).strip()]
            except (KeyError, TypeError, ValueError):
                continue
            is_cancelled = is_cancelled_status(status) and not balls
            if not is_cancelled and (
                len(balls) != drawn_numbers or len(set(balls)) != drawn_numbers
            ):
                continue
            if not is_cancelled and any(number < 1 or number > total_numbers for number in balls):
                continue
            rows.append(
                {
                    "sourceIndex": index,
                    "id": row.get("id", ""),
                    "lotteryId": row.get("lottery_id", ""),
                    "lotteryCountry": row.get("lottery_country", ""),
                    "drawEventId": row.get("draw_event_id", ""),
                    "drawTimeMs": parse_int(row.get("draw_time_ms"), 0),
                    "drawTimeUtc": row.get("draw_time_utc", ""),
                    "status": status,
                    "bonusBall": row.get("bonus_ball", ""),
                    "numbers": balls,
                    "isCancelled": is_cancelled,
                }
            )
    rows.sort(key=lambda item: item["drawTimeMs"], reverse=True)
    with HISTORY_CACHE_LOCK:
        lru_cache_set(HISTORY_CACHE, cache_key, rows, HISTORY_CACHE_MAX_ITEMS)
    return list(rows)


def dashboard_row_to_csv_row(
    row: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    number_columns = game_number_columns(config)
    csv_row = {
        "id": row.get("id", ""),
        "lottery_id": row.get("lotteryId", ""),
        "lottery_country": row.get("lotteryCountry", ""),
        "draw_event_id": row.get("drawEventId", ""),
        "draw_time_ms": row.get("drawTimeMs", ""),
        "draw_time_utc": row.get("drawTimeUtc", ""),
        "status": row.get("status", ""),
        "bonus_ball": row.get("bonusBall", ""),
    }
    numbers = row.get("numbers") or []
    for index, column in enumerate(NUMBER_COLUMNS):
        csv_row[column] = (
            numbers[index] if index < len(number_columns) and index < len(numbers) else ""
        )
    return csv_row


def row_source_rank(row: dict[str, Any]) -> int:
    identifier = str(row.get("id") or row.get("drawEventId") or "")
    status = str(row.get("status") or "")
    if row.get("isCancelled") or is_cancelled_status(status):
        return 0
    if status.startswith("official-") or identifier.startswith(SUPPLEMENT_ID_PREFIXES):
        return 1
    return 2


def write_dashboard_rows(
    path: Path,
    rows: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> None:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    ordered = sorted(rows, key=lambda item: item["drawTimeMs"], reverse=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=history_fieldnames())
        writer.writeheader()
        writer.writerows(dashboard_row_to_csv_row(row, config) for row in ordered)
    replace_path_with_retry(temp_path, path)
    clear_data_caches()


def merge_history_rows(
    existing_rows: list[dict[str, Any]],
    fetched_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged_by_time: dict[int, dict[str, Any]] = {}
    for row in [*existing_rows, *fetched_rows]:
        key = parse_int(row.get("drawTimeMs"), 0)
        if not key:
            continue
        current = merged_by_time.get(key)
        if current is None or row_source_rank(row) >= row_source_rank(current):
            merged_by_time[key] = row
    return sorted(merged_by_time.values(), key=lambda item: item["drawTimeMs"], reverse=True)


def draw_time_utc_from_ms(draw_time_ms: int) -> str:
    if draw_time_ms <= 0:
        return ""
    return datetime.fromtimestamp(draw_time_ms / 1000, tz=UTC).isoformat(
        timespec="seconds"
    )


def hhmm_to_minutes(value: str, default: int) -> int:
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", str(value or "").strip())
    if not match:
        return default
    hour = max(0, min(23, int(match.group(1))))
    minute = max(0, min(59, int(match.group(2))))
    return hour * 60 + minute


def is_inside_operating_hours(draw_time_ms: int, config: dict[str, Any]) -> bool:
    schedule = config.get("operatingHours")
    if not schedule:
        return True
    try:
        timezone = ZoneInfo(str(schedule.get("timezone") or "UTC"))
    except Exception:
        timezone = UTC
    local_dt = datetime.fromtimestamp(draw_time_ms / 1000, tz=UTC).astimezone(timezone)
    minute_of_day = local_dt.hour * 60 + local_dt.minute
    start = hhmm_to_minutes(str(schedule.get("start") or ""), 0)
    end = hhmm_to_minutes(str(schedule.get("end") or ""), 23 * 60 + 59)
    if start <= end:
        return start <= minute_of_day <= end
    return minute_of_day >= start or minute_of_day <= end


def future_prediction_draw_times(
    newest_ms: int,
    config: dict[str, Any],
    *,
    count: int = PREDICTION_HORIZONS,
    now_ms: int | None = None,
) -> list[dict[str, Any]]:
    interval_ms = int(float(config["drawIntervalMinutes"]) * 60000)
    if newest_ms <= 0 or interval_ms <= 0 or count <= 0:
        return []
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    minimum_target_ms = now_ms + PREDICTION_TRACKING_LEAD_SECONDS * 1000
    first_offset = max(1, math.floor((minimum_target_ms - newest_ms) / interval_ms) + 1)
    draw_times: list[dict[str, Any]] = []
    offset = first_offset
    max_offset = first_offset + max(count * 12, count + 1440)
    while len(draw_times) < count and offset <= max_offset:
        draw_time_ms = newest_ms + offset * interval_ms
        if (
            draw_time_ms >= minimum_target_ms
            and is_inside_operating_hours(draw_time_ms, config)
        ):
            draw_times.append(
                {
                    "drawOffset": offset,
                    "drawTimeMs": draw_time_ms,
                    "drawTimeUtc": draw_time_utc_from_ms(draw_time_ms),
                }
            )
        offset += 1
    return draw_times


def prediction_schedule_cache_bucket(config: dict[str, Any]) -> int:
    interval_ms = int(float(config["drawIntervalMinutes"]) * 60000)
    if interval_ms <= 0:
        return 0
    return int((int(time.time() * 1000) + PREDICTION_TRACKING_LEAD_SECONDS * 1000) // interval_ms)


def gap_audit(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    interval_ms = int(float(config["drawIntervalMinutes"]) * 60000)
    if interval_ms <= 0:
        return {"checked": False, "missingIntervals": 0, "hasGaps": False}
    times = sorted(
        {
            parse_int(row.get("drawTimeMs"), 0)
            for row in rows
            if parse_int(row.get("drawTimeMs"), 0) > 0
        }
    )
    if len(times) < 2:
        return {
            "checked": True,
            "intervalMinutes": config["drawIntervalMinutes"],
            "rowsChecked": len(times),
            "missingIntervals": 0,
            "hasGaps": False,
            "samples": [],
        }

    missing_intervals = 0
    largest_gap_intervals = 0
    samples: list[dict[str, Any]] = []
    tolerance_ms = max(1000, interval_ms // 20)
    for older, newer in zip(times, times[1:]):
        diff = newer - older
        if diff <= interval_ms + tolerance_ms:
            continue
        gap_intervals = 0
        expected = older + interval_ms
        while expected < newer - tolerance_ms:
            if is_inside_operating_hours(expected, config):
                gap_intervals += 1
            expected += interval_ms
        if gap_intervals <= 0:
            continue
        missing_intervals += gap_intervals
        largest_gap_intervals = max(largest_gap_intervals, gap_intervals)
        if len(samples) < 5:
            samples.append(
                {
                    "afterUtc": draw_time_utc_from_ms(older),
                    "beforeUtc": draw_time_utc_from_ms(newer),
                    "missingIntervals": gap_intervals,
                    "gapMinutes": round(diff / 60000, 3),
                }
            )

    return {
        "checked": True,
        "kind": "fixed_interval_scan",
        "authoritativeMissingCheck": False,
        "intervalMinutes": config["drawIntervalMinutes"],
        "rowsChecked": len(times),
        "missingIntervals": missing_intervals,
        "largestGapIntervals": largest_gap_intervals,
        "hasGaps": missing_intervals > 0,
        "note": "固定开奖间隔扫描只提示时间间隔异常，可能包含停开、官方跳期或上游源未提供的期次，不等同本地历史少抓。",
        "samples": samples,
    }


def is_supplement_history_row(row: dict[str, Any]) -> bool:
    identifier = str(row.get("id") or row.get("drawEventId") or "")
    status = str(row.get("status") or "")
    return status.startswith("official-") or identifier.startswith(SUPPLEMENT_ID_PREFIXES)


def meta_int(meta: dict[str, Any] | None, *keys: str) -> int | None:
    if not meta:
        return None
    for key in keys:
        if key not in meta:
            continue
        value = meta.get(key)
        if value not in (None, ""):
            return parse_int(value, 0)
    return None


def newest_draw_time_from_meta(meta: dict[str, Any] | None) -> int:
    if not meta:
        return 0
    direct = meta_int(meta, "newestDrawTimeMs", "newest_draw_time_ms")
    if direct:
        return direct
    newest_row = meta.get("newest_row")
    if isinstance(newest_row, dict):
        return parse_int(newest_row.get("draw_time_ms"), 0)
    return 0


def history_data_integrity(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    remote_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    draw_times: list[int] = []
    duplicate_times = 0
    seen_times: set[int] = set()
    valid_rows = 0
    cancelled_rows = 0
    supplement_rows = 0

    for row in rows:
        draw_time_ms = parse_int(row.get("drawTimeMs"), 0)
        if draw_time_ms > 0:
            if draw_time_ms in seen_times:
                duplicate_times += 1
            seen_times.add(draw_time_ms)
            draw_times.append(draw_time_ms)
        if row.get("isCancelled") or is_cancelled_status(row.get("status")):
            cancelled_rows += 1
        elif is_valid_draw_row(row, config):
            valid_rows += 1
        if is_supplement_history_row(row):
            supplement_rows += 1

    local_rows = len(rows)
    bc_rows = local_rows - supplement_rows
    invalid_rows = max(0, local_rows - valid_rows - cancelled_rows)
    newest_local_ms = max(draw_times, default=0)
    oldest_local_ms = min(draw_times, default=0)
    bc_total = meta_int(remote_meta, "total", "bcTotal")
    bc_total_page = meta_int(remote_meta, "totalPage", "total_page")
    bc_page_size = meta_int(remote_meta, "pageSize", "page_size")
    skipped_rows = meta_int(remote_meta, "skippedRows", "skipped_rows") or 0
    duplicate_bc_rows = meta_int(remote_meta, "duplicateRows", "duplicate_rows") or 0
    bc_newest_ms = newest_draw_time_from_meta(remote_meta)

    checked_remote = bc_total is not None
    missing_vs_bc = max(0, (bc_total or 0) - local_rows) if checked_remote else None
    delta_vs_bc = local_rows - bc_total if checked_remote else None
    bc_rows_delta = bc_rows - bc_total if checked_remote else None
    latest_covers_bc = None
    if checked_remote and bc_newest_ms:
        latest_covers_bc = newest_local_ms >= bc_newest_ms

    if not checked_remote:
        status = "local_checked"
        message = "已检查本地文件结构，未连接 BC total 做远端对账。"
    elif missing_vs_bc and missing_vs_bc > 0:
        status = "missing"
        message = f"本地历史少于 BC 当前 total {missing_vs_bc} 期，需要补齐后再分析。"
    elif latest_covers_bc is False:
        status = "behind_latest"
        message = "本地最新开奖时间落后于 BC 最新开奖，需要同步。"
    else:
        status = "aligned"
        if supplement_rows:
            message = "本地历史已覆盖 BC 当前 total；部分最新记录来自官网/补充源，后续 BC 发布后会自动替换。"
        else:
            message = "本地历史已和 BC 当前 total 对齐。"

    return {
        "checked": True,
        "checkedRemote": checked_remote,
        "status": status,
        "message": message,
        "localRows": local_rows,
        "validRows": valid_rows,
        "cancelledRows": cancelled_rows,
        "invalidRows": invalid_rows,
        "duplicateTimes": duplicate_times,
        "supplementRows": supplement_rows,
        "bcRows": bc_rows,
        "bcTotal": bc_total,
        "bcTotalPage": bc_total_page,
        "bcPageSize": bc_page_size,
        "localVsBcDelta": delta_vs_bc,
        "bcRowsVsTotalDelta": bc_rows_delta,
        "missingVsBc": missing_vs_bc,
        "skippedBcRows": skipped_rows,
        "duplicateBcRows": duplicate_bc_rows,
        "latestLocalCoversBc": latest_covers_bc,
        "newestLocalUtc": draw_time_utc_from_ms(newest_local_ms),
        "oldestLocalUtc": draw_time_utc_from_ms(oldest_local_ms),
        "bcNewestUtc": draw_time_utc_from_ms(bc_newest_ms),
    }


def next_generated_event_id(existing_rows: list[dict[str, Any]], draw_time_ms: int) -> str:
    older = [
        row
        for row in existing_rows
        if row.get("drawTimeMs", 0) < draw_time_ms
        and not str(row.get("drawEventId", "")).startswith("etipos-")
    ]
    if older:
        anchor = max(older, key=lambda item: item["drawTimeMs"])
    else:
        official = [
            row
            for row in existing_rows
            if not str(row.get("drawEventId", "")).startswith("etipos-")
        ]
        anchor = max(official, key=lambda item: item["drawTimeMs"]) if official else None
    if anchor:
        step = round((draw_time_ms - anchor["drawTimeMs"]) / 120000)
        try:
            return str(int(anchor["drawEventId"]) + max(1, step))
        except (TypeError, ValueError):
            pass
    return f"etipos-{draw_time_ms}"


def etipos_row_to_dashboard_row(
    row: dict[str, Any],
    existing_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    draw_time_ms = parse_int(row.get("drawTimeMs"), 0)
    generated_event_id = next_generated_event_id(existing_rows, draw_time_ms)
    return {
        "sourceIndex": 0,
        "id": f"etipos-{draw_time_ms}",
        "lotteryId": DEFAULT_LOTTERY_ID,
        "lotteryCountry": "Slovakia",
        "drawEventId": generated_event_id,
        "drawTimeMs": draw_time_ms,
        "drawTimeUtc": row.get("drawTimeUtc", ""),
        "status": "official-etipos",
        "bonusBall": "",
        "numbers": row["numbers"],
        "isCancelled": False,
    }


def official_row_to_dashboard_row(
    row: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    draw_time_ms = parse_int(row.get("drawTimeMs"), 0)
    source = str(row.get("source") or config.get("officialSupplement") or "official")
    return {
        "sourceIndex": 0,
        "id": f"{source}-{draw_time_ms}",
        "lotteryId": config["lotteryId"],
        "lotteryCountry": config["country"],
        "drawEventId": row.get("drawEventId") or f"{source}-{draw_time_ms}",
        "drawTimeMs": draw_time_ms,
        "drawTimeUtc": row.get("drawTimeUtc", ""),
        "status": f"official-{source}",
        "bonusBall": row.get("bonusBall", ""),
        "numbers": row["numbers"],
        "isCancelled": False,
    }


def select_supplement_rows(
    recent_rows: list[dict[str, Any]],
    existing_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    existing_by_time = {
        parse_int(row.get("drawTimeMs"), 0): row
        for row in existing_rows
        if parse_int(row.get("drawTimeMs"), 0) > 0
    }
    newest_local = max(existing_by_time.keys()) if existing_by_time else 0
    selected: list[dict[str, Any]] = []
    for row in recent_rows:
        draw_time_ms = parse_int(row.get("drawTimeMs"), 0)
        if not draw_time_ms:
            continue
        current = existing_by_time.get(draw_time_ms)
        if current is not None:
            if row_source_rank(row) > row_source_rank(current):
                selected.append(row)
            continue
        if draw_time_ms > newest_local:
            selected.append(row)
    return selected


def fetch_official_supplement(
    config: dict[str, Any],
    existing_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = config.get("officialSupplement")
    if source == "etipos":
        recent = [
            etipos_row_to_dashboard_row(row, existing_rows)
            for row in fetch_etipos_archive.fetch_recent_archive(hours=2)
        ]
        dashboard_rows = select_supplement_rows(recent, existing_rows)
        return dashboard_rows, {
            "source": "etipos",
            "checkedRows": len(recent),
            "newRows": len(dashboard_rows),
            "status": "ok",
            "newestOfficialUtc": recent[0]["drawTimeUtc"] if recent else "",
        }

    recent, meta = fetch_official_supplements.fetch_recent_official(config)
    dashboard_recent = [official_row_to_dashboard_row(row, config) for row in recent]
    dashboard_rows = select_supplement_rows(dashboard_recent, existing_rows)
    meta = dict(meta)
    meta["checkedRows"] = len(recent)
    meta["newRows"] = len(dashboard_rows)
    meta["newestOfficialUtc"] = (
        recent[0]["drawTimeUtc"] if recent else meta.get("newestOfficialUtc", "")
    )
    return dashboard_rows, meta


def fetch_etipos_supplement(existing_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deprecated compatibility wrapper.

    Slovakia's active supplement source is configured through
    fetch_official_supplement(), currently using LotoDate. Keep this only for
    older callers that still import the old eTIPOS helper name.
    """
    return fetch_official_supplement(LOTTERY_GAMES[DEFAULT_GAME_KEY], existing_rows)


def fetch_rows_page(
    *,
    lottery_id: str,
    page: int,
    page_size: int,
    sleep: float,
    timeout: float,
    retries: int,
    retry_sleep: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = fetch_bc_keno_history.post_history_page(
        lottery_id=lottery_id,
        page=page,
        page_size=page_size,
        timeout=timeout,
        retries=retries,
        retry_sleep=retry_sleep,
    )
    rows: list[dict[str, Any]] = []
    skipped_rows = 0
    skipped_examples: list[dict[str, Any]] = []
    for index, item in enumerate(data.get("list") or [], start=1):
        try:
            rows.append(api_item_to_dashboard_row(item, index=index))
        except ValueError as exc:
            skipped_rows += 1
            if len(skipped_examples) < 5:
                skipped_examples.append(
                    {
                        "drawEventId": item.get("drawEventId", ""),
                        "status": item.get("status", ""),
                        "reason": str(exc),
                    }
                )
    if sleep > 0:
        # Sleep is handled by callers between pages. Keep this argument here so
        # refresh options stay centralized.
        pass
    return rows, {
        "page": data.get("page"),
        "pageSize": data.get("pageSize"),
        "total": int(data.get("total") or 0),
        "totalPage": int(data.get("totalPage") or 0),
        "skippedRows": skipped_rows,
        "skippedExamples": skipped_examples,
    }


def api_item_to_dashboard_row(item: dict[str, Any], index: int) -> dict[str, Any]:
    lottery_id = str(item.get("lotteryId") or DEFAULT_LOTTERY_ID)
    config = LOTTERY_GAMES[game_key_from_value(lottery_id)]
    is_cancelled = fetch_bc_keno_history.is_cancelled_item(item)
    if is_cancelled:
        balls: list[int] = []
    else:
        balls = fetch_bc_keno_history.parse_balls(
            str(item.get("normalBall", "")),
            expected_count=int(config["drawnNumbers"]),
            total_numbers=int(config["totalNumbers"]),
        )
    return {
        "sourceIndex": index,
        "id": item.get("id", ""),
        "lotteryId": item.get("lotteryId", ""),
        "lotteryCountry": item.get("lotteryCountry", ""),
        "drawEventId": item.get("drawEventId", ""),
        "drawTimeMs": parse_int(item.get("drawTime"), 0),
        "drawTimeUtc": fetch_bc_keno_history.draw_time_iso(item.get("drawTime")),
        "status": str(item.get("status", "")),
        "bonusBall": item.get("bonusBall", ""),
        "numbers": balls,
        "isCancelled": is_cancelled,
    }


def rows_to_draws_oldest_first(rows: list[dict[str, Any]]) -> list[tuple[int, ...]]:
    return [tuple(row["numbers"]) for row in reversed(rows)]


def probability_summary(config: dict[str, Any]) -> dict[str, Any]:
    p3 = hit_probability_for(config, 3)
    default_three_odds = DEFAULT_MAIN_ODDS_BY_GAME.get(str(config.get("key")), {}).get(3, 60)
    drawn_numbers = int(config["drawnNumbers"])
    total_numbers = int(config["totalNumbers"])
    draw_interval = float(config["drawIntervalMinutes"])
    pay_table = {
        picks: odds
        for picks, odds in keno_triple_omission.PAY_TABLE.items()
        if picks <= drawn_numbers
    }
    total_draws = math.comb(
        total_numbers,
        drawn_numbers,
    )
    no_run = keno_triple_omission.no_three_run_count(
        total_numbers,
        drawn_numbers,
    )
    triples = triple_groups(config)
    return {
        "payTable": [
            {
                "picks": picks,
                "probability": hit_probability_for(config, picks),
                "fairTotalOdds": 1 / hit_probability_for(config, picks),
                "screenOdds": odds,
                "evTotalPayout": hit_probability_for(config, picks) * odds - 1,
                "evProfitOnly": hit_probability_for(config, picks) * odds - 1,
            }
            for picks, odds in pay_table.items()
        ],
        "threePick": {
            "probability": p3,
            "fairTotalOdds": 1 / p3,
            "expectedDraws": 1 / p3,
            "expectedMinutes": draw_interval / p3,
            "defaultOdds": default_three_odds,
            "evAtDefaultOdds": p3 * default_three_odds - 1,
        },
        "consecutiveTriples": {
            "groups": len(triples),
            "expectedWindowsPerDraw": len(triples) * p3,
            "anyRunProbability": 1 - no_run / total_draws,
        },
    }


def miss_stats_from_hits(
    draw_count: int,
    hit_draws: list[int],
) -> tuple[int, int, int | None, int | None]:
    if not hit_draws:
        return draw_count, draw_count, None, None

    current_miss = draw_count - hit_draws[-1]
    max_miss = hit_draws[0] - 1
    for previous, current in zip(hit_draws, hit_draws[1:]):
        max_miss = max(max_miss, current - previous - 1)
    max_miss = max(max_miss, current_miss)
    last_miss = hit_draws[-1] - hit_draws[-2] - 1 if len(hit_draws) > 1 else hit_draws[0] - 1
    return current_miss, max_miss, last_miss, hit_draws[-1]


def triple_stats_payload(
    rows: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    triples = triple_groups(config)
    draws = rows_to_draws_oldest_first(rows)
    draw_count = len(draws)
    hit_draws_by_triple = {triple: [] for triple in triples}
    observed_windows = 0
    for draw_index, draw in enumerate(draws, start=1):
        draw_set = set(draw)
        triple_windows = find_run_windows(draw_set, 3, int(config["totalNumbers"]))
        observed_windows += len(triple_windows)
        for triple in triple_windows:
            if triple in hit_draws_by_triple:
                hit_draws_by_triple[triple].append(draw_index)

    p3 = hit_probability_for(config, 3)
    payload = []
    for triple, hit_draws in hit_draws_by_triple.items():
        current_miss, max_miss, last_miss, last_hit_draw = miss_stats_from_hits(
            draw_count,
            hit_draws,
        )
        payload.append(
            {
                "triple": "-".join(str(number) for number in triple),
                "numbers": list(triple),
                "hits": len(hit_draws),
                "currentMiss": current_miss,
                "maxMiss": max_miss,
                "lastMiss": last_miss,
                "lastHitDraw": last_hit_draw,
                "hitRate": len(hit_draws) / draw_count if draw_count else 0,
                "recentHitRate": recent_hit_rate(hit_draws, draw_count),
                "missTailProbability": keno_triple_omission.tail_probability(
                    current_miss, p3
                ),
            }
        )
    add_miss_z_scores(payload)
    payload.sort(key=lambda item: (-item["currentMiss"], -item["maxMiss"], item["numbers"]))
    return {
        "items": payload,
        "observedWindowsPerDraw": observed_windows / draw_count if draw_count else 0,
    }


def number_frequency(
    rows: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    total_numbers = int(config["totalNumbers"])
    drawn_numbers = int(config["drawnNumbers"])
    counts = {number: 0 for number in range(1, total_numbers + 1)}
    miss = {number: 0 for number in range(1, total_numbers + 1)}
    last_seen = {number: None for number in range(1, total_numbers + 1)}
    draws = rows_to_draws_oldest_first(rows)
    for index, draw in enumerate(draws, start=1):
        draw_set = set(draw)
        for number in range(1, total_numbers + 1):
            if number in draw_set:
                counts[number] += 1
                last_seen[number] = index
                miss[number] = 0
            else:
                miss[number] += 1

    draw_count = len(draws)
    expected_hits = draw_count * drawn_numbers / total_numbers if draw_count else 0
    return [
        {
            "number": number,
            "hits": counts[number],
            "hitRate": counts[number] / draw_count if draw_count else 0,
            "expectedHits": expected_hits,
            "deltaFromExpected": counts[number] - expected_hits,
            "currentMiss": miss[number],
            "lastSeenDraw": last_seen[number],
        }
        for number in range(1, total_numbers + 1)
    ]


def bonus_ball_stats(
    rows: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    if not config.get("hasBonusBall"):
        return {
            "enabled": False,
            "total": 0,
            "overlapDraws": 0,
            "overlapShare": 0,
            "latest": None,
            "items": [],
        }
    total_numbers = int(config.get("bonusBallTotalNumbers") or config["totalNumbers"])
    counts = {number: 0 for number in range(1, total_numbers + 1)}
    total = 0
    overlap_draws = 0
    latest: dict[str, Any] | None = None
    for row in rows:
        bonus = parse_int(row.get("bonusBall"), 0)
        if bonus < 1 or bonus > total_numbers:
            continue
        total += 1
        counts[bonus] += 1
        if bonus in set(row.get("numbers") or []):
            overlap_draws += 1
        if latest is None:
            latest = {
                "number": bonus,
                "drawEventId": row.get("drawEventId", ""),
                "drawTimeUtc": row.get("drawTimeUtc", ""),
                "overlapsMainNumbers": bonus in set(row.get("numbers") or []),
            }
    items = [
        {
            "number": number,
            "draws": count,
            "share": count / total if total else 0,
        }
        for number, count in counts.items()
    ]
    items.sort(key=lambda item: (-item["draws"], item["number"]))
    return {
        "enabled": total > 0,
        "total": total,
        "overlapDraws": overlap_draws,
        "overlapShare": overlap_draws / total if total else 0,
        "latest": latest,
        "items": items,
    }


def current_miss_for_condition(
    rows: list[dict[str, Any]],
    condition_key: str,
    total_numbers: int,
) -> int:
    miss = 0
    for row in rows:
        draw_set = set(row["numbers"])
        pair_windows = find_run_windows(draw_set, 2, total_numbers)
        triple_windows = find_run_windows(draw_set, 3, total_numbers)
        quad_windows = find_run_windows(draw_set, 4, total_numbers)
        pair_set_count = max_disjoint_count(pair_windows)
        triple_set_count = max_disjoint_count(triple_windows)
        flags = {
            "hasDoublePair": pair_set_count >= 2,
            "hasTriplePairSet": pair_set_count >= 3,
            "hasQuadPairSet": pair_set_count >= 4,
            "hasFivePairSet": pair_set_count >= 5,
            "hasPairTriple": has_disjoint_groups(pair_windows, triple_windows),
            "hasDoubleTriple": triple_set_count >= 2,
            "hasTripleDoublePair": has_triple_with_pair_count(
                triple_windows, pair_windows, 2
            ),
        }
        if flags.get(condition_key, False):
            return miss
        miss += 1
    return miss


def normalize_score(value: float, values: list[float]) -> float:
    if not values:
        return 0
    low = min(values)
    high = max(values)
    if high <= low:
        return 0
    return (value - low) / (high - low)


def recent_number_counts(
    rows: list[dict[str, Any]],
    window: int,
    config: dict[str, Any] | None = None,
) -> dict[int, int]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    counts = {number: 0 for number in range(1, int(config["totalNumbers"]) + 1)}
    for row in rows[:window]:
        for number in row["numbers"]:
            counts[number] += 1
    return counts


def recent_hit_rate(hit_draws: list[int], draw_count: int, window: int = 2000) -> float:
    if draw_count <= 0:
        return 0
    recent_window = min(window, draw_count)
    first_recent_draw = draw_count - recent_window + 1
    recent_hits = sum(1 for draw_index in hit_draws if draw_index >= first_recent_draw)
    return recent_hits / recent_window if recent_window else 0


def add_miss_z_scores(items: list[dict[str, Any]]) -> None:
    if not items:
        return
    misses = [float(item["currentMiss"]) for item in items]
    mean = sum(misses) / len(misses)
    variance = sum((value - mean) ** 2 for value in misses) / len(misses)
    std = math.sqrt(variance)
    for item in items:
        item["missZScore"] = (item["currentMiss"] - mean) / std if std > 0 else 0


def scored_numbers(
    numbers: list[int],
    weights: dict[str, float],
    frequency: dict[int, dict[str, Any]],
    recent_counts: dict[int, int],
    recent_window: int,
    draw_count: int,
) -> list[dict[str, Any]]:
    misses = [frequency[number]["currentMiss"] for number in numbers]
    momentums = []
    for number in numbers:
        item = frequency[number]
        global_rate = item["hits"] / draw_count if draw_count else 0
        recent_rate = recent_counts[number] / recent_window if recent_window else 0
        momentums.append(recent_rate / global_rate if global_rate > 0 else 0)
    history_values = [frequency[number]["deltaFromExpected"] for number in numbers]
    scored = []
    for number, momentum in zip(numbers, momentums):
        item = frequency[number]
        miss_score = normalize_score(item["currentMiss"], misses)
        momentum_score = normalize_score(momentum, momentums)
        history_score = normalize_score(item["deltaFromExpected"], history_values)
        score = (
            weights["miss"] * miss_score
            + weights["momentum"] * momentum_score
            + weights["history"] * history_score
        )
        scored.append(
            {
                "number": number,
                "score": score,
                "hits": item["hits"],
                "hitRate": item["hitRate"],
                "currentMiss": item["currentMiss"],
                "recentHits": recent_counts[number],
                "momentum": momentum,
                "deltaFromExpected": item["deltaFromExpected"],
            }
        )
    scored.sort(
        key=lambda item: (
            -item["score"],
            -item["currentMiss"],
            -item["hitRate"],
            item["number"],
        )
    )
    return scored


def bonus_ball_prediction_sets(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    recent_window: int,
) -> list[list[dict[str, Any]]]:
    if not config.get("hasBonusBall"):
        return []
    total_numbers = int(config.get("bonusBallTotalNumbers") or config["totalNumbers"])
    draws: list[int] = []
    for row in reversed(rows):
        bonus = parse_int(row.get("bonusBall"), 0)
        if 1 <= bonus <= total_numbers:
            draws.append(bonus)
    draw_count = len(draws)
    if draw_count == 0:
        return []

    hit_draws_by_number: dict[int, list[int]] = {
        number: [] for number in range(1, total_numbers + 1)
    }
    for draw_index, bonus in enumerate(draws, start=1):
        hit_draws_by_number[bonus].append(draw_index)

    recent_values = draws[-recent_window:] if recent_window > 0 else []
    recent_counts = {
        number: sum(1 for value in recent_values if value == number)
        for number in range(1, total_numbers + 1)
    }
    expected_hits = draw_count / total_numbers if total_numbers else 0
    frequency: dict[int, dict[str, Any]] = {}
    for number, hit_draws in hit_draws_by_number.items():
        current_miss, max_miss, last_miss, last_hit_draw = miss_stats_from_hits(
            draw_count,
            hit_draws,
        )
        frequency[number] = {
            "number": number,
            "hits": len(hit_draws),
            "hitRate": len(hit_draws) / draw_count if draw_count else 0,
            "expectedHits": expected_hits,
            "deltaFromExpected": len(hit_draws) - expected_hits,
            "currentMiss": current_miss,
            "maxMiss": max_miss,
            "lastMiss": last_miss,
            "lastHitDraw": last_hit_draw,
        }

    numbers = list(range(1, total_numbers + 1))
    pick_count = bonus_ball_prediction_count(config, total_numbers)
    sets = [
        with_bonus_roles(
            scored_numbers(numbers, weights, frequency, recent_counts, recent_window, draw_count)[:pick_count]
        )
        for weights in PREDICTION_NUMBER_WEIGHTS
    ]
    return sets


def bonus_ball_prediction_count(config: dict[str, Any], total_numbers: int | None = None) -> int:
    total = int(total_numbers or config.get("bonusBallTotalNumbers") or config["totalNumbers"])
    requested = parse_int(config.get("bonusBallPredictionCount"), min(5, total))
    return max(1, min(requested, total, 5))


def bonus_ball_prediction_label(config: dict[str, Any], count: int | None = None) -> str:
    if config.get("bonusBallPredictionLabel"):
        return str(config["bonusBallPredictionLabel"])
    count = count or bonus_ball_prediction_count(config)
    support = max(0, count - 1)
    return f"1主{support}辅" if support else "1主"


def with_bonus_roles(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    count = len(items)
    ranked = []
    for index, item in enumerate(items):
        role_label = "主" if index == 0 else ("辅" if count == 2 else f"辅{index}")
        ranked.append(
            {
                **item,
                "rank": index + 1,
                "role": "main" if index == 0 else "support",
                "roleLabel": role_label,
            }
        )
    return ranked


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return 0, 0
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return max(0, center - margin), min(1, center + margin)


def ticket_hit(row: dict[str, Any], numbers: tuple[int, ...], bonus_number: int | None = None) -> bool:
    draw_set = set(row.get("numbers") or [])
    if not all(number in draw_set for number in numbers):
        return False
    if bonus_number is None:
        return True
    return parse_int(row.get("bonusBall"), 0) == bonus_number


def ticket_stats(
    rows: list[dict[str, Any]],
    numbers: tuple[int, ...],
    bonus_number: int | None,
    *,
    recent_window: int,
) -> dict[str, Any]:
    draws = list(reversed(rows))
    hit_draws = [
        draw_index
        for draw_index, row in enumerate(draws, start=1)
        if ticket_hit(row, numbers, bonus_number)
    ]
    current_miss, max_miss, last_miss, last_hit_draw = miss_stats_from_hits(len(draws), hit_draws)
    recent_rows = rows[:recent_window]
    recent_hits = sum(1 for row in recent_rows if ticket_hit(row, numbers, bonus_number))
    ci_low, ci_high = wilson_interval(recent_hits, len(recent_rows))
    return {
        "hits": len(hit_draws),
        "hitRate": len(hit_draws) / len(draws) if draws else 0,
        "currentMiss": current_miss,
        "maxMiss": max_miss,
        "lastMiss": last_miss,
        "lastHitDraw": last_hit_draw,
        "recentWindow": len(recent_rows),
        "recentHits": recent_hits,
        "recentHitRate": recent_hits / len(recent_rows) if recent_rows else 0,
        "recentHitRateCi": [ci_low, ci_high],
    }


def prediction_ticket_strategy_specs(config: dict[str, Any]) -> list[dict[str, Any]]:
    raw = PREDICTION_TICKET_STRATEGIES.get(str(config.get("key")))
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def prediction_strategy_tickets_for_spec(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    spec: dict[str, Any],
    frequency: dict[int, dict[str, Any]],
    recent_counts: dict[int, int],
    recent_window: int,
    bonus_sets: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    if not spec or not rows:
        return []
    mode = str(spec["mode"])
    pick_count = int(spec["pickCount"])
    game_key = str(config["key"])
    odds = (
        DEFAULT_BONUS_ODDS_BY_GAME.get(game_key, {}).get(pick_count)
        if mode == "bonus"
        else DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(pick_count)
    )
    if not odds:
        return []

    total_numbers = int(config["totalNumbers"])
    draw_count = len(rows)
    scored = scored_numbers(
        list(range(1, total_numbers + 1)),
        PREDICTION_NUMBER_WEIGHTS[0],
        frequency,
        recent_counts,
        recent_window,
        draw_count,
    )
    main_pool_size = min(total_numbers, 8 if pick_count == 1 else 12)
    main_pool = scored[:main_pool_size]
    score_by_number = {int(item["number"]): float(item["score"]) for item in scored}
    main_combos = [
        tuple(sorted(int(item["number"]) for item in combo))
        for combo in combinations(main_pool, pick_count)
    ]
    if not main_combos:
        return []

    bonus_pool: list[dict[str, Any] | None]
    if mode == "bonus":
        if not config.get("hasBonusBall") or not bonus_sets:
            return []
        bonus_pool = bonus_sets[0][: min(3, len(bonus_sets[0]))]
    else:
        bonus_pool = [None]

    recent_eval_window = min(PREDICTION_TICKET_BACKTEST_WINDOW, draw_count)
    theoretical_hit_rate = hit_probability_for(config, pick_count)
    if mode == "bonus":
        theoretical_hit_rate *= 1 / int(config.get("bonusBallTotalNumbers") or config["totalNumbers"])
    fair_odds = 1 / theoretical_hit_rate if theoretical_hit_rate > 0 else 0
    break_even_hit_rate = 1 / float(odds)
    candidates: list[dict[str, Any]] = []
    for numbers in main_combos:
        main_score = sum(score_by_number.get(number, 0) for number in numbers) / max(len(numbers), 1)
        for bonus_item in bonus_pool:
            bonus_number = int(bonus_item["number"]) if bonus_item else None
            bonus_score = float(bonus_item.get("score", 0)) if bonus_item else 0
            stats = ticket_stats(
                rows,
                numbers,
                bonus_number,
                recent_window=recent_eval_window,
            )
            candidates.append(
                {
                    "numbers": list(numbers),
                    "bonusNumber": bonus_number,
                    "heuristicScore": main_score * (0.82 if bonus_item else 1) + bonus_score * (0.18 if bonus_item else 0),
                    **stats,
                }
            )

    miss_values = [item["currentMiss"] for item in candidates]
    edge_values = [item["recentHitRate"] - theoretical_hit_rate for item in candidates]
    for item in candidates:
        item["score"] = (
            0.55 * float(item["heuristicScore"])
            + 0.25 * normalize_score(int(item["currentMiss"]), miss_values)
            + 0.20 * normalize_score(float(item["recentHitRate"]) - theoretical_hit_rate, edge_values)
        )
        item["theoreticalHitRate"] = theoretical_hit_rate
        item["fairOdds"] = fair_odds
        item["odds"] = float(odds)
        item["breakEvenHitRate"] = break_even_hit_rate
        item["evAtOdds"] = theoretical_hit_rate * float(odds) - 1
        item["chasePeriods"] = PREDICTION_TICKET_CHASE_PERIODS
        item["missAllProbability"] = (1 - theoretical_hit_rate) ** PREDICTION_TICKET_CHASE_PERIODS
        item["sampleWarning"] = draw_count < 500 or int(item["recentWindow"]) < 200
        item["label"] = str(spec["label"])
        item["mode"] = mode
        item["pickCount"] = pick_count
        item["ticketLabel"] = "-".join(str(number) for number in item["numbers"])
        if item.get("bonusNumber"):
            item["ticketLabel"] = f"{item['ticketLabel']} + {item['bonusNumber']}"

    candidates.sort(
        key=lambda item: (
            -float(item["score"]),
            -int(item["currentMiss"]),
            -float(item["recentHitRate"]),
            item["numbers"],
            item.get("bonusNumber") or 0,
        )
    )
    return candidates[:PREDICTION_TICKET_TOP_COUNT]


def prediction_strategy_tickets(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    frequency: dict[int, dict[str, Any]],
    recent_counts: dict[int, int],
    recent_window: int,
    bonus_sets: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    tickets: list[dict[str, Any]] = []
    for spec in prediction_ticket_strategy_specs(config):
        tickets.extend(
            prediction_strategy_tickets_for_spec(
                rows,
                config,
                spec,
                frequency,
                recent_counts,
                recent_window,
                bonus_sets,
            )
        )
    return tickets


def group_prediction_items(
    groups: list[dict[str, Any]],
    label_key: str,
    horizon: int,
) -> list[dict[str, Any]]:
    if not groups:
        return []
    miss_values = [item["currentMiss"] for item in groups]
    max_values = [item["maxMiss"] for item in groups]
    hit_deltas = [
        item.get("recentHitRate", item["hitRate"]) - item["hitRate"]
        for item in groups
    ]
    miss_weight = max(0.30, 0.52 - horizon * 0.04)
    max_weight = 0.18
    hit_weight = max(0, 1 - miss_weight - max_weight)
    scored = []
    for item, hit_delta in zip(groups, hit_deltas):
        miss_pressure = normalize_score(item["currentMiss"], miss_values)
        max_pressure = normalize_score(item["maxMiss"], max_values)
        hit_score = normalize_score(hit_delta, hit_deltas)
        score = miss_weight * miss_pressure + max_weight * max_pressure + hit_weight * hit_score
        scored.append({**item, "score": score})
    scored.sort(
        key=lambda item: (
            -item["score"],
            -item["currentMiss"],
            -item.get("recentHitRate", item["hitRate"]),
            item["numbers"],
        )
    )
    selected = scored[:3]
    return [
        {
            "label": item[label_key],
            "numbers": item["numbers"],
            "score": item["score"],
            "currentMiss": item["currentMiss"],
            "maxMiss": item["maxMiss"],
            "hits": item["hits"],
            "hitRate": item["hitRate"],
            "recentHitRate": item.get("recentHitRate", item["hitRate"]),
            "missZScore": item.get("missZScore", 0),
        }
        for item in selected
    ]


def condition_prediction_item(
    rows: list[dict[str, Any]],
    summary_items: list[dict[str, Any]],
    key: str,
) -> dict[str, Any] | None:
    source = next((item for item in summary_items if item["key"] == key), None)
    if source is None:
        return None
    return {
        "label": PREDICTION_PATTERN_LABELS[key],
        "key": key,
        "score": 0.58 * normalize_score(source["currentMiss"], [0, source["maxMiss"]])
        + 0.42 * source["share"],
        "currentMiss": source["currentMiss"],
        "maxMiss": source["maxMiss"],
        "draws": source["draws"],
        "share": source["share"],
    }


def prediction_payload(
    rows: list[dict[str, Any]],
    triples: dict[str, Any],
    pattern_summary: list[dict[str, Any]],
    pair_stats: dict[str, Any],
    quad_stats: dict[str, Any],
    config: dict[str, Any] | None = None,
    timeline_newest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    total_numbers = int(config["totalNumbers"])
    half = total_numbers // 2
    big_numbers = list(range(half + 1, total_numbers + 1))
    small_numbers = list(range(1, half + 1))
    frequency = {item["number"]: item for item in number_frequency(rows, config)}
    recent_window = min(PREDICTION_RECENT_WINDOW, len(rows))
    recent_counts = recent_number_counts(rows, recent_window, config)
    draw_count = len(rows)
    big_sets = [
        scored_numbers(big_numbers, weights, frequency, recent_counts, recent_window, draw_count)[:5]
        for weights in PREDICTION_NUMBER_WEIGHTS
    ]
    small_sets = [
        scored_numbers(small_numbers, weights, frequency, recent_counts, recent_window, draw_count)[:5]
        for weights in PREDICTION_NUMBER_WEIGHTS
    ]
    bonus_sets = bonus_ball_prediction_sets(rows, config, recent_window)
    strategy_tickets = prediction_strategy_tickets(
        rows,
        config,
        frequency,
        recent_counts,
        recent_window,
        bonus_sets,
    )
    condition_keys = list(
        config.get(
            "predictionConditionKeys",
            [
                "hasDoublePair",
                "hasTriplePairSet",
                "hasTriple",
                "hasQuadPairSet",
                "hasFivePairSet",
                "hasPairTriple",
                "hasDoubleTriple",
                "hasTripleDoublePair",
                "hasQuad",
                "hasQuadPair",
                "hasFive",
                "hasSix",
            ],
        )
    )
    forecasts = []
    newest = timeline_newest or (rows[0] if rows else None)
    newest_ms = parse_int(newest.get("drawTimeMs") if newest else 0, 0)
    forecast_times = future_prediction_draw_times(newest_ms, config)
    first_ms = parse_int(forecast_times[0].get("drawTimeMs"), 0) if forecast_times else 0
    end_ms = parse_int(forecast_times[-1].get("drawTimeMs"), 0) if forecast_times else 0
    condition_items = [
        item
        for key in condition_keys
        if (item := condition_prediction_item(rows, pattern_summary, key)) is not None
    ]
    condition_items.sort(
        key=lambda item: (-item["score"], -item["currentMiss"], -item["share"])
    )
    for index, forecast_time in enumerate(forecast_times):
        forecasts.append(
            {
                "drawOffset": parse_int(forecast_time.get("drawOffset"), index + 1),
                "drawTimeMs": parse_int(forecast_time.get("drawTimeMs"), 0),
                "drawTimeUtc": str(forecast_time.get("drawTimeUtc") or ""),
                "bigNumbers": big_sets[index],
                "smallNumbers": small_sets[index],
                "bonusBallNumbers": bonus_sets[index] if bonus_sets else [],
                "patterns": {
                    "pairs": group_prediction_items(pair_stats["items"], "pair", index + 1),
                    "triples": group_prediction_items(triples["items"], "triple", index + 1),
                    "quads": group_prediction_items(quad_stats["items"], "quad", index + 1),
                    "conditions": condition_items[:10],
                },
            }
        )
    return {
        "method": "当前遗漏 + 近240期动量偏差 + 全样本偏差 + 连号遗漏 z-score 的启发式排序",
        "recentWindow": min(PREDICTION_RECENT_WINDOW, len(rows)),
        "smallRange": [1, half],
        "bigRange": [half + 1, total_numbers],
        "timeWindowUtc": {
            "start": datetime.fromtimestamp(first_ms / 1000, tz=UTC).isoformat(
                timespec="seconds"
            )
            if first_ms
            else "",
            "end": datetime.fromtimestamp(end_ms / 1000, tz=UTC).isoformat(
                timespec="seconds"
            )
            if end_ms
            else "",
        },
        "topBigNumbers": big_sets[0],
        "topSmallNumbers": small_sets[0],
        "bonusBall": {
            "enabled": bool(bonus_sets),
            "range": [1, int(config.get("bonusBallTotalNumbers") or config["totalNumbers"])],
            "count": bonus_ball_prediction_count(config),
            "label": bonus_ball_prediction_label(config),
            "topNumbers": bonus_sets[0] if bonus_sets else [],
        },
        "strategyTickets": strategy_tickets,
        "forecasts": forecasts,
    }


def run_length_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[int, int] = {}
    draw_count = len(rows)
    for row in rows:
        numbers = sorted(row["numbers"])
        current = 1
        longest = 1
        for prev, current_number in zip(numbers, numbers[1:]):
            if current_number == prev + 1:
                current += 1
            else:
                longest = max(longest, current)
                current = 1
        longest = max(longest, current)
        counts[longest] = counts.get(longest, 0) + 1
    return [
        {
            "runLength": length,
            "draws": count,
            "share": count / draw_count if draw_count else 0,
        }
        for length, count in sorted(counts.items())
    ]


def find_run_windows(
    draw_set: set[int],
    length: int,
    total_numbers: int,
) -> list[tuple[int, ...]]:
    limit = total_numbers - length + 1
    return [
        tuple(range(start, start + length))
        for start in range(1, limit + 1)
        if all(number in draw_set for number in range(start, start + length))
    ]


def has_disjoint_groups(
    first_groups: list[tuple[int, ...]],
    second_groups: list[tuple[int, ...]] | None = None,
) -> bool:
    if second_groups is None:
        for index, first in enumerate(first_groups):
            first_set = set(first)
            for second in first_groups[index + 1 :]:
                if first_set.isdisjoint(second):
                    return True
        return False

    for first in first_groups:
        first_set = set(first)
        for second in second_groups:
            if first_set.isdisjoint(second):
                return True
    return False


def max_disjoint_count(groups: list[tuple[int, ...]]) -> int:
    ordered = sorted(groups, key=lambda group: (group[-1], group[0], len(group)))
    used: set[int] = set()
    count = 0
    for group in ordered:
        group_set = set(group)
        if used.isdisjoint(group_set):
            used.update(group_set)
            count += 1
    return count


def has_triple_with_pair_count(
    triple_groups: list[tuple[int, ...]],
    pair_groups: list[tuple[int, ...]],
    required_pairs: int,
) -> bool:
    for triple in triple_groups:
        triple_set = set(triple)
        available_pairs = [
            pair for pair in pair_groups if triple_set.isdisjoint(pair)
        ]
        if max_disjoint_count(available_pairs) >= required_pairs:
            return True
    return False


def game_sum_ranges(config: dict[str, Any]) -> list[tuple[str, int, int]]:
    return list(config.get("sumRanges") or SUM_RANGES)


def sum_bucket(total: int, ranges: list[tuple[str, int, int]] | None = None) -> str:
    for label, low, high in ranges or SUM_RANGES:
        if low <= total <= high:
            return label
    return "其他"


def ratio_label(left: int, right: int) -> str:
    return f"{left}:{right}"


def empty_count_map(labels: list[str]) -> dict[str, int]:
    return {label: 0 for label in labels}


def share_items(counts: dict[str, int], draw_count: int) -> list[dict[str, Any]]:
    return [
        {"label": label, "draws": count, "share": count / draw_count if draw_count else 0}
        for label, count in counts.items()
    ]


def increment_cross(
    cross: dict[str, dict[str, int]],
    category: str,
    condition: str,
    label: str,
) -> None:
    key = f"{category}|{condition}|{label}"
    cross.setdefault(
        key,
        {
            "category": category,
            "condition": condition,
            "label": label,
            "draws": 0,
        },
    )
    cross[key]["draws"] += 1


def update_pattern_streaks(
    streaks: dict[str, dict[str, Any]],
    flags: dict[str, bool],
    draw_index: int,
) -> None:
    for key, matched in flags.items():
        if key not in streaks:
            continue
        item = streaks[key]
        if matched:
            item["hits"] += 1
            item["lastHitDraw"] = draw_index
            item["maxMiss"] = max(item["maxMiss"], item["currentMiss"])
            item["currentMiss"] = 0
        else:
            item["currentMiss"] += 1
            item["maxMiss"] = max(item["maxMiss"], item["currentMiss"])


def streak_stats_for_groups(
    rows: list[dict[str, Any]],
    groups: tuple[tuple[int, ...], ...],
    label_key: str,
    limit: int,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    if not groups:
        return {"items": [], "totalItems": 0}

    draw_count = len(rows)
    group_length = len(groups[0])
    hit_draws_by_group = {group: [] for group in groups}

    for draw_index, draw in enumerate(rows_to_draws_oldest_first(rows), start=1):
        draw_set = set(draw)
        for group in find_run_windows(draw_set, group_length, int(config["totalNumbers"])):
            if group in hit_draws_by_group:
                hit_draws_by_group[group].append(draw_index)

    items = []
    for group, hit_draws in hit_draws_by_group.items():
        current_miss, max_miss, _last_miss, last_hit_draw = miss_stats_from_hits(
            draw_count,
            hit_draws,
        )
        items.append(
            {
                label_key: "-".join(str(number) for number in group),
                "numbers": list(group),
                "hits": len(hit_draws),
                "currentMiss": current_miss,
                "maxMiss": max_miss,
                "lastHitDraw": last_hit_draw,
                "hitRate": len(hit_draws) / draw_count if draw_count else 0,
                "recentHitRate": recent_hit_rate(hit_draws, draw_count),
            }
        )

    add_miss_z_scores(items)
    items.sort(key=lambda item: (-item["currentMiss"], -item["maxMiss"], item["numbers"]))
    return {"items": items[:limit], "totalItems": len(items)}


def run_pattern_summary_stats(
    rows: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    total_numbers = int(config["totalNumbers"])
    draw_count = len(rows)
    pattern_streaks = {
        key: {
            "key": key,
            "label": label,
            "hits": 0,
            "currentMiss": 0,
            "maxMiss": 0,
            "lastHitDraw": None,
        }
        for key, label in game_run_conditions(config, include_all=False)
        if key != "all"
    }

    for draw_index, draw in enumerate(rows_to_draws_oldest_first(rows), start=1):
        draw_set = set(draw)
        pair_windows = find_run_windows(draw_set, 2, total_numbers)
        triple_windows = find_run_windows(draw_set, 3, total_numbers)
        quad_windows = find_run_windows(draw_set, 4, total_numbers)
        five_windows = find_run_windows(draw_set, 5, total_numbers)
        six_windows = find_run_windows(draw_set, 6, total_numbers)
        pair_set_count = max_disjoint_count(pair_windows)
        triple_set_count = max_disjoint_count(triple_windows)
        flags = {
            "hasPair": bool(pair_windows),
            "hasDoublePair": pair_set_count >= 2,
            "hasTriplePairSet": pair_set_count >= 3,
            "hasTriple": bool(triple_windows),
            "hasQuadPairSet": pair_set_count >= 4,
            "hasFivePairSet": pair_set_count >= 5,
            "hasPairTriple": has_disjoint_groups(pair_windows, triple_windows),
            "hasDoubleTriple": triple_set_count >= 2,
            "hasTripleDoublePair": has_triple_with_pair_count(
                triple_windows, pair_windows, 2
            ),
            "hasQuad": bool(quad_windows),
            "hasQuadPair": has_disjoint_groups(pair_windows, quad_windows),
            "hasFive": bool(five_windows),
            "hasSix": bool(six_windows),
        }
        update_pattern_streaks(pattern_streaks, flags, draw_index)

    pattern_summary = []
    for key, _label in game_run_conditions(config, include_all=False):
        item = dict(pattern_streaks[key])
        item["draws"] = item.pop("hits")
        item["share"] = item["draws"] / draw_count if draw_count else 0
        pattern_summary.append(item)
    return pattern_summary


def advanced_stats_payload(
    rows: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    total_numbers = int(config["totalNumbers"])
    drawn_numbers = int(config["drawnNumbers"])
    half = total_numbers // 2
    draw_count = len(rows)
    sum_ranges = game_sum_ranges(config)
    sum_labels = [label for label, _, _ in sum_ranges]
    ratio_labels = [ratio_label(value, drawn_numbers - value) for value in range(drawn_numbers + 1)]
    sum_counts = empty_count_map(sum_labels)
    size_counts = empty_count_map(ratio_labels)
    odd_even_counts = empty_count_map(ratio_labels)
    pattern_streaks = {
        key: {
            "key": key,
            "label": label,
            "hits": 0,
            "currentMiss": 0,
            "maxMiss": 0,
            "lastHitDraw": None,
        }
        for key, label in game_run_conditions(config, include_all=False)
        if key != "all"
    }
    run_window_totals = {"pairs": 0, "triples": 0, "quads": 0}
    cross: dict[str, dict[str, Any]] = {}

    for draw_index, draw in enumerate(rows_to_draws_oldest_first(rows), start=1):
        numbers = list(draw)
        draw_set = set(draw)
        pair_windows = find_run_windows(draw_set, 2, total_numbers)
        triple_windows = find_run_windows(draw_set, 3, total_numbers)
        quad_windows = find_run_windows(draw_set, 4, total_numbers)
        five_windows = find_run_windows(draw_set, 5, total_numbers)
        six_windows = find_run_windows(draw_set, 6, total_numbers)
        pair_set_count = max_disjoint_count(pair_windows)
        triple_set_count = max_disjoint_count(triple_windows)
        flags = {
            "hasPair": bool(pair_windows),
            "hasDoublePair": pair_set_count >= 2,
            "hasTriplePairSet": pair_set_count >= 3,
            "hasTriple": bool(triple_windows),
            "hasQuadPairSet": pair_set_count >= 4,
            "hasFivePairSet": pair_set_count >= 5,
            "hasPairTriple": has_disjoint_groups(pair_windows, triple_windows),
            "hasDoubleTriple": triple_set_count >= 2,
            "hasTripleDoublePair": has_triple_with_pair_count(
                triple_windows, pair_windows, 2
            ),
            "hasQuad": bool(quad_windows),
            "hasQuadPair": has_disjoint_groups(pair_windows, quad_windows),
            "hasFive": bool(five_windows),
            "hasSix": bool(six_windows),
        }
        update_pattern_streaks(pattern_streaks, flags, draw_index)

        run_window_totals["pairs"] += len(pair_windows)
        run_window_totals["triples"] += len(triple_windows)
        run_window_totals["quads"] += len(quad_windows)

        total = sum(numbers)
        sum_label = sum_bucket(total, sum_ranges)
        big = sum(1 for number in numbers if number > half)
        odd = sum(1 for number in numbers if number % 2 == 1)
        size_label = ratio_label(big, drawn_numbers - big)
        odd_even_label = ratio_label(odd, drawn_numbers - odd)

        if sum_label in sum_counts:
            sum_counts[sum_label] += 1
        size_counts[size_label] += 1
        odd_even_counts[odd_even_label] += 1

        for condition, _label in game_run_conditions(config):
            if condition != "all" and not flags[condition]:
                continue
            increment_cross(cross, "sumRange", condition, sum_label)
            increment_cross(cross, "sizeRatio", condition, size_label)
            increment_cross(cross, "oddEvenRatio", condition, odd_even_label)

    for item in cross.values():
        item["share"] = item["draws"] / draw_count if draw_count else 0
        condition = item["condition"]
        if condition == "all":
            condition_hits = draw_count
        else:
            condition_hits = int(pattern_streaks[condition]["hits"])
        item["conditionShare"] = item["draws"] / condition_hits if condition_hits else 0

    pair_stats = streak_stats_for_groups(rows, pair_groups(config), "pair", 20, config)
    quad_stats = streak_stats_for_groups(rows, quad_groups(config), "quad", 20, config)
    pattern_summary = []
    for key, _label in game_run_conditions(config, include_all=False):
        item = dict(pattern_streaks[key])
        item["draws"] = item.pop("hits")
        item["share"] = item["draws"] / draw_count if draw_count else 0
        pattern_summary.append(item)

    return {
        "runPatterns": {
            "summary": pattern_summary,
            "windowAverages": {
                key: value / draw_count if draw_count else 0
                for key, value in run_window_totals.items()
            },
            "pairs": pair_stats,
            "quads": quad_stats,
        },
        "sumRanges": share_items(sum_counts, draw_count),
        "sizeRatios": share_items(size_counts, draw_count),
        "oddEvenRatios": share_items(odd_even_counts, draw_count),
        "bonusBall": bonus_ball_stats(rows, config),
        "cross": sorted(
            cross.values(),
            key=lambda item: (item["category"], item["condition"], item["label"]),
        ),
        "definitions": {
            "smallNumbers": f"1-{half}",
            "bigNumbers": f"{half + 1}-{total_numbers}",
            "doublePair": "at least two disjoint pair runs",
            "pairTriple": "at least one pair run and one disjoint triple run",
            "triplePairSet": "at least three disjoint pair runs",
            "quadPairSet": "at least four disjoint pair runs",
            "fivePairSet": "at least five disjoint pair runs",
            "doubleTriple": "at least two disjoint triple runs",
            "tripleDoublePair": "at least one triple run and two pair runs, all disjoint",
        },
    }


def filter_triples(items: list[dict[str, Any]], params: dict[str, list[str]]) -> list[dict[str, Any]]:
    minimum_current_miss = parse_int(params.get("minCurrentMiss", ["0"])[0], 0)
    minimum_hits = parse_int(params.get("minHits", ["0"])[0], 0)
    maximum_tail = parse_float(params.get("maxTail", ["1"])[0], 1)
    search = params.get("q", [""])[0].strip()
    sort = params.get("sort", ["currentMiss"])[0]
    order = params.get("order", ["desc"])[0]
    limit = parse_int(params.get("limit", ["78"])[0], 78)

    filtered = [
        item
        for item in items
        if item["currentMiss"] >= minimum_current_miss
        and item["hits"] >= minimum_hits
        and item["missTailProbability"] <= maximum_tail
        and (not search or search in item["triple"])
    ]
    sort_keys = {
        "currentMiss": lambda item: item["currentMiss"],
        "maxMiss": lambda item: item["maxMiss"],
        "hits": lambda item: item["hits"],
        "hitRate": lambda item: item["hitRate"],
        "tail": lambda item: item["missTailProbability"],
        "triple": lambda item: item["numbers"][0],
    }
    key = sort_keys.get(sort, sort_keys["currentMiss"])
    reverse = order != "asc"
    filtered.sort(key=key, reverse=reverse)
    return filtered[: max(1, min(limit, 500))]


def analysis_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_analysis_supported(config)
    history_path = game_history_path(config)
    row_limit = parse_int(query.get("drawLimit", ["0"])[0], 0)
    with DATA_LOCK:
        try:
            stat = history_path.stat()
            cache_key = (config["key"], stat.st_mtime_ns, stat.st_size, row_limit)
        except FileNotFoundError:
            cache_key = (config["key"], 0, 0, row_limit)

    with ANALYSIS_CACHE_LOCK:
        cached = lru_cache_get(ANALYSIS_CACHE, cache_key)
    if cached is not None:
        payload = dict(cached)
        payload["cacheHit"] = True
        triples = payload["triples"]
        triples = dict(triples)
        triples["items"] = filter_triples(triples["allItems"], query)
        payload["triples"] = triples
        payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
        return payload

    with DATA_LOCK:
        all_rows = load_history_rows(history_path, config)
    data_integrity = history_data_integrity(all_rows, config)
    rows = valid_draw_rows(all_rows, config)
    if row_limit > 0:
        rows = rows[:row_limit]
    latest_timeline = all_rows[0] if all_rows else None

    triples = triple_stats_payload(rows, config)
    filtered_triples = filter_triples(triples["items"], query)
    advanced = advanced_stats_payload(rows, config)
    newest = rows[0] if rows else None
    oldest = rows[-1] if rows else None

    payload = {
        "generatedAt": utc_now_iso(),
        "cacheHit": False,
        "game": game_public_config(config),
        "historyFile": file_info(history_path),
        "dataIntegrity": data_integrity,
        "drawCount": len(rows),
        "newestDraw": newest,
        "oldestDraw": oldest,
        "recentDraws": rows[:12],
        "probabilities": probability_summary(config),
        "triples": {
            "items": filtered_triples,
            "allItems": triples["items"],
            "totalItems": len(triples["items"]),
            "observedWindowsPerDraw": triples["observedWindowsPerDraw"],
        },
        "advanced": advanced,
        "numberFrequency": number_frequency(rows, config),
        "runLengthDistribution": run_length_distribution(rows),
        "gapAudit": gap_audit(all_rows, config),
    }
    payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
    with ANALYSIS_CACHE_LOCK:
        lru_cache_set(ANALYSIS_CACHE, cache_key, payload, ANALYSIS_CACHE_MAX_ITEMS)
    return payload


def predictions_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_predictions_supported(config)
    history_path = game_history_path(config)
    row_limit = parse_int(query.get("drawLimit", ["0"])[0], 0)
    schedule_bucket = prediction_schedule_cache_bucket(config)
    with DATA_LOCK:
        try:
            stat = history_path.stat()
            cache_key = (config["key"], stat.st_mtime_ns, stat.st_size, row_limit, schedule_bucket)
        except FileNotFoundError:
            cache_key = (config["key"], 0, 0, row_limit, schedule_bucket)

    with PREDICTION_CACHE_LOCK:
        cached = lru_cache_get(PREDICTION_CACHE, cache_key)
    if cached is not None:
        payload = dict(cached)
        payload["cacheHit"] = True
        payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
        payload["predictionTracking"] = touch_prediction_tracking_for_payload(payload, config)
        return payload

    with DATA_LOCK:
        all_rows = load_history_rows(history_path, config)
    data_integrity = history_data_integrity(all_rows, config)
    rows = valid_draw_rows(all_rows, config)
    if row_limit > 0:
        rows = rows[:row_limit]
    latest_timeline = all_rows[0] if all_rows else None

    triples = triple_stats_payload(rows, config)
    pattern_summary = run_pattern_summary_stats(rows, config)
    pairs = pair_groups(config)
    quads = quad_groups(config)
    pair_stats = streak_stats_for_groups(rows, pairs, "pair", len(pairs), config)
    quad_stats = streak_stats_for_groups(rows, quads, "quad", len(quads), config)
    newest = rows[0] if rows else None
    oldest = rows[-1] if rows else None
    payload = {
        "generatedAt": utc_now_iso(),
        "cacheHit": False,
        "game": game_public_config(config),
        "historyFile": file_info(history_path),
        "dataIntegrity": data_integrity,
        "drawCount": len(rows),
        "newestDraw": newest,
        "newestTimelineDraw": latest_timeline,
        "oldestDraw": oldest,
        "predictions": prediction_payload(
            rows,
            triples,
            pattern_summary,
            pair_stats,
            quad_stats,
            config,
            latest_timeline,
        ),
        "gapAudit": gap_audit(all_rows, config),
    }
    payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
    with PREDICTION_CACHE_LOCK:
        lru_cache_set(PREDICTION_CACHE, cache_key, payload, PREDICTION_CACHE_MAX_ITEMS)
    payload["predictionTracking"] = touch_prediction_tracking_for_payload(payload, config, rows)
    return payload


def draws_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    history_path = game_history_path(config)
    with DATA_LOCK:
        all_rows = load_history_rows(history_path, config)
    data_integrity = history_data_integrity(all_rows, config)
    valid_rows = valid_draw_rows(all_rows, config)
    newest = valid_rows[0] if valid_rows else None
    oldest = valid_rows[-1] if valid_rows else None
    rows = list(all_rows)
    search = query.get("q", [""])[0].strip()
    sort = query.get("sort", ["desc"])[0]
    page = max(1, parse_int(query.get("page", ["1"])[0], 1))
    page_size = max(10, min(parse_int(query.get("pageSize", ["100"])[0], 100), 500))

    if search:
        numbers = [int(value) for value in re.findall(r"\d+", search)]
        search_lower = search.lower()

        def matches(row: dict[str, Any]) -> bool:
            if search_lower in str(row.get("drawEventId", "")).lower():
                return True
            if search_lower in str(row.get("drawTimeUtc", "")).lower():
                return True
            if numbers and all(number in row["numbers"] for number in numbers):
                return True
            if config.get("hasBonusBall") and numbers and any(
                number == parse_int(row.get("bonusBall"), 0) for number in numbers
            ):
                return True
            return False

        rows = [row for row in rows if matches(row)]

    if sort == "asc":
        rows = list(reversed(rows))

    total = len(rows)
    total_page = max(1, math.ceil(total / page_size))
    page = min(page, total_page)
    start = (page - 1) * page_size
    items = rows[start : start + page_size]

    return {
        "generatedAt": utc_now_iso(),
        "game": game_public_config(config),
        "historyFile": file_info(history_path),
        "dataIntegrity": data_integrity,
        "drawCount": len(valid_rows),
        "newestDraw": newest,
        "oldestDraw": oldest,
        "page": page,
        "pageSize": page_size,
        "total": total,
        "totalPage": total_page,
        "items": items,
    }


def parse_iso_to_ms(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text:
        return 0
    if re.fullmatch(r"\d+", text):
        return int(text)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.timestamp() * 1000)


def ms_to_utc_iso(value: int) -> str:
    if value <= 0:
        return ""
    return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat(timespec="seconds")


def parse_bet_numbers(value: Any, total_numbers: int = 80) -> list[int]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_values: list[Any] = re.findall(r"\d+", value)
    elif isinstance(value, list):
        raw_values = value
    else:
        raw_values = [value]

    numbers: list[int] = []
    seen: set[int] = set()
    for raw in raw_values:
        try:
            number = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"号码必须是 1-{total_numbers} 的整数") from exc
        if number < 1 or number > total_numbers:
            raise ValueError(f"号码必须在 1-{total_numbers} 之间")
        if number not in seen:
            seen.add(number)
            numbers.append(number)
    return numbers


def validate_run_numbers(numbers: list[int], expected_length: int) -> None:
    if len(numbers) != expected_length:
        raise ValueError(f"该玩法需要填写 {expected_length} 个连续号码")
    ordered = sorted(numbers)
    expected = list(range(ordered[0], ordered[0] + expected_length))
    if ordered != expected:
        raise ValueError(f"该玩法需要填写 {expected_length} 个连续号码")


def default_odds_for_bet_type(
    config: dict[str, Any],
    bet_type: str,
    numbers: list[int] | None = None,
) -> float:
    bet_config = BET_TYPES[bet_type]
    pick_count = None
    if bet_type == "numbers":
        pick_count = len(numbers or []) or 3
    elif bet_config.get("exactNumbers"):
        pick_count = int(bet_config["exactNumbers"])
    if pick_count:
        game_odds = DEFAULT_MAIN_ODDS_BY_GAME.get(str(config.get("key")), {})
        return float(game_odds.get(pick_count, bet_config["defaultOdds"]))
    return float(bet_config["defaultOdds"])


def bet_type_options(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "label": bet_config["label"],
            "requiresNumbers": bet_config["requiresNumbers"],
            "defaultOdds": default_odds_for_bet_type(config, key),
            "exactNumbers": bet_config.get("exactNumbers"),
            "minNumbers": bet_config.get("minNumbers"),
            "maxNumbers": bet_config.get("maxNumbers"),
        }
        for key, bet_config in BET_TYPES.items()
    ]


def load_sim_bets(path: Path = DEFAULT_BETS) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    bets: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            try:
                item = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and item.get("id"):
                bets.append(item)
    return bets


def write_sim_bets(bets: list[dict[str, Any]], path: Path = DEFAULT_BETS) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as fh:
        for bet in bets:
            fh.write(json.dumps(bet, ensure_ascii=False, separators=(",", ":")))
            fh.write("\n")
    replace_path_with_retry(temp_path, path)


def bet_game_key(bet: dict[str, Any]) -> str:
    return game_key_from_value(
        bet.get("gameKey")
        or bet.get("game")
        or bet.get("lotteryId")
        or DEFAULT_GAME_KEY
    )


def normalize_bet_payload(
    payload: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or game_from_options(payload)
    bet_type = str(payload.get("betType") or "").strip()
    if bet_type not in BET_TYPES:
        raise ValueError("未知投注类型")

    target_ms = parse_int(payload.get("targetDrawTimeMs"), 0)
    if target_ms <= 0:
        try:
            target_ms = parse_iso_to_ms(payload.get("targetDrawTimeUtc"))
        except (TypeError, ValueError) as exc:
            raise ValueError("目标开奖时间无效") from exc
    if target_ms <= 0:
        raise ValueError("必须选择目标开奖时间")

    bet_config = BET_TYPES[bet_type]
    numbers = parse_bet_numbers(payload.get("numbers"), int(config["totalNumbers"]))
    if bet_config["requiresNumbers"] and not numbers:
        raise ValueError("该玩法需要填写号码")
    if bet_type == "numbers":
        minimum = int(bet_config.get("minNumbers") or 1)
        maximum = int(bet_config.get("maxNumbers") or int(config["drawnNumbers"]))
        maximum = min(maximum, int(config["drawnNumbers"]))
        if len(numbers) < minimum or len(numbers) > maximum:
            raise ValueError(f"号码组选需要填写 {minimum}-{maximum} 个号码")
    if bet_config.get("exactNumbers"):
        validate_run_numbers(numbers, int(bet_config["exactNumbers"]))

    stake = parse_float(payload.get("stake"), 1)
    odds = parse_float(payload.get("odds"), default_odds_for_bet_type(config, bet_type, numbers))
    if stake <= 0:
        raise ValueError("投入金额必须大于 0")
    if odds <= 1:
        raise ValueError("赔率必须大于 1")

    note = str(payload.get("note") or "").strip()
    return {
        "id": uuid.uuid4().hex,
        "createdAt": utc_now_iso(),
        "targetDrawTimeMs": target_ms,
        "targetDrawTimeUtc": ms_to_utc_iso(target_ms),
        "gameKey": config["key"],
        "lotteryId": config["lotteryId"],
        "gameShortName": config["shortName"],
        "betType": bet_type,
        "betLabel": bet_config["label"],
        "numbers": numbers,
        "stake": round(stake, 4),
        "odds": round(odds, 4),
        "note": note[:160],
        "status": "pending",
        "settledAt": "",
        "payout": 0,
        "profit": 0,
        "result": None,
    }


def format_groups(groups: list[tuple[int, ...]], limit: int = 8) -> list[str]:
    return ["-".join(str(number) for number in group) for group in groups[:limit]]


def draw_result_snapshot(draw: dict[str, Any]) -> dict[str, Any]:
    return {
        "drawEventId": draw.get("drawEventId", ""),
        "drawTimeMs": draw.get("drawTimeMs", 0),
        "drawTimeUtc": draw.get("drawTimeUtc", ""),
        "numbers": draw.get("numbers", []),
        "bonusBall": draw.get("bonusBall", ""),
    }


def evaluate_bet_against_draw(
    bet: dict[str, Any],
    draw: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or LOTTERY_GAMES[bet_game_key(bet)]
    total_numbers = int(config["totalNumbers"])
    draw_numbers = list(draw.get("numbers") or [])
    draw_set = set(draw_numbers)
    bet_type = str(bet.get("betType") or "")
    numbers = [int(number) for number in bet.get("numbers") or []]
    matched_numbers = [number for number in numbers if number in draw_set]
    matched_groups: list[str] = []
    reason = ""

    if bet_type == "numbers":
        won = bool(numbers) and len(matched_numbers) == len(numbers)
        reason = f"命中 {len(matched_numbers)}/{len(numbers)} 个指定号码"
    elif bet_type in {"pair", "triple", "quad"}:
        ordered = sorted(numbers)
        won = bool(ordered) and all(number in draw_set for number in ordered)
        if won:
            matched_groups = ["-".join(str(number) for number in ordered)]
        reason = f"{'-'.join(str(number) for number in ordered)} {'命中' if won else '未命中'}"
    else:
        flags = run_condition_flags_for(draw_set, total_numbers)
        won = flags.get(bet_type, False)
        pair_windows = find_run_windows(draw_set, 2, total_numbers)
        triple_windows = find_run_windows(draw_set, 3, total_numbers)
        quad_windows = find_run_windows(draw_set, 4, total_numbers)
        five_windows = find_run_windows(draw_set, 5, total_numbers)
        six_windows = find_run_windows(draw_set, 6, total_numbers)
        if bet_type in {"hasPair", "hasDoublePair", "hasTriplePairSet", "hasQuadPairSet", "hasFivePairSet"}:
            matched_groups = format_groups(pair_windows)
        elif bet_type in {"hasTriple", "hasPairTriple", "hasDoubleTriple", "hasTripleDoublePair"}:
            matched_groups = format_groups(triple_windows) + format_groups(pair_windows)
        elif bet_type == "hasQuad":
            matched_groups = format_groups(quad_windows)
        elif bet_type == "hasQuadPair":
            matched_groups = format_groups(quad_windows) + format_groups(pair_windows)
        elif bet_type == "hasFive":
            matched_groups = format_groups(five_windows)
        elif bet_type == "hasSix":
            matched_groups = format_groups(six_windows)
        reason = f"{BET_TYPES.get(bet_type, {}).get('label', bet_type)} {'出现' if won else '未出现'}"

    stake = parse_float(bet.get("stake"), 0)
    odds = parse_float(bet.get("odds"), 0)
    payout = round(stake * odds, 4) if won else 0
    profit = round(payout - stake, 4) if won else round(-stake, 4)
    return {
        "won": won,
        "reason": reason,
        "matchedNumbers": matched_numbers,
        "matchedGroups": matched_groups,
        "draw": draw_result_snapshot(draw),
        "payout": payout,
        "profit": profit,
        "settledAt": utc_now_iso(),
    }


def settle_sim_bets(
    bets: list[dict[str, Any]],
    rows: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
) -> int:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    rows = rows if rows is not None else load_history_rows(game_history_path(config), config)
    rows = valid_draw_rows(rows, config)
    rows_by_time = {
        parse_int(row.get("drawTimeMs"), 0): row
        for row in rows
        if parse_int(row.get("drawTimeMs"), 0) > 0
    }
    settled = 0
    for bet in bets:
        if bet_game_key(bet) != config["key"]:
            continue
        if bet.get("status") != "pending":
            continue
        target_ms = parse_int(bet.get("targetDrawTimeMs"), 0)
        draw = rows_by_time.get(target_ms)
        if draw is None:
            continue
        result = evaluate_bet_against_draw(bet, draw, config)
        bet["status"] = "won" if result["won"] else "lost"
        bet["settledAt"] = result["settledAt"]
        bet["payout"] = result["payout"]
        bet["profit"] = result["profit"]
        bet["result"] = result
        settled += 1
    return settled


def sim_bets_summary(bets: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(bets)
    pending = sum(1 for bet in bets if bet.get("status") == "pending")
    won = sum(1 for bet in bets if bet.get("status") == "won")
    lost = sum(1 for bet in bets if bet.get("status") == "lost")
    settled = won + lost
    stake_total = sum(parse_float(bet.get("stake"), 0) for bet in bets)
    pending_stake = sum(
        parse_float(bet.get("stake"), 0)
        for bet in bets
        if bet.get("status") == "pending"
    )
    payout_total = sum(parse_float(bet.get("payout"), 0) for bet in bets)
    profit_total = sum(parse_float(bet.get("profit"), 0) for bet in bets)
    return {
        "total": total,
        "pending": pending,
        "won": won,
        "lost": lost,
        "settled": settled,
        "stakeTotal": round(stake_total, 4),
        "pendingStake": round(pending_stake, 4),
        "payoutTotal": round(payout_total, 4),
        "profitTotal": round(profit_total, 4),
        "hitRate": won / settled if settled else 0,
    }


def sim_bets_response(
    bets: list[dict[str, Any]],
    *,
    settled_now: int = 0,
    created: dict[str, Any] | None = None,
    deleted: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if config is not None:
        scoped_bets = [bet for bet in bets if bet_game_key(bet) == config["key"]]
    else:
        scoped_bets = bets
    ordered = sorted(
        scoped_bets,
        key=lambda bet: (
            str(bet.get("createdAt") or ""),
            parse_int(bet.get("targetDrawTimeMs"), 0),
        ),
        reverse=True,
    )
    all_ordered = sorted(
        bets,
        key=lambda bet: (
            str(bet.get("createdAt") or ""),
            parse_int(bet.get("targetDrawTimeMs"), 0),
        ),
        reverse=True,
    )
    return {
        "ok": True,
        "game": game_public_config(config) if config is not None else None,
        "generatedAt": utc_now_iso(),
        "betFile": file_info(DEFAULT_BETS),
        "betTypes": bet_type_options(config or LOTTERY_GAMES[DEFAULT_GAME_KEY]),
        "settledNow": settled_now,
        "created": created,
        "deleted": deleted,
        "summary": sim_bets_summary(scoped_bets),
        "allSummary": sim_bets_summary(bets),
        "items": ordered[:500],
        "allItems": all_ordered[:500],
    }


def sim_bets_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_sim_bets_supported(config)
    with DATA_LOCK:
        rows = load_history_rows(game_history_path(config), config)
    with BETS_LOCK:
        bets = load_sim_bets()
        settled_now = settle_sim_bets(bets, rows, config)
        if settled_now:
            write_sim_bets(bets)
        return sim_bets_response(bets, settled_now=settled_now, config=config)


def create_sim_bet(payload: dict[str, Any]) -> dict[str, Any]:
    config = game_from_options(payload)
    ensure_sim_bets_supported(config)
    bet = normalize_bet_payload(payload, config)
    with DATA_LOCK:
        rows = load_history_rows(game_history_path(config), config)
    with BETS_LOCK:
        bets = load_sim_bets()
        bets.append(bet)
        settled_now = settle_sim_bets(bets, rows, config)
        write_sim_bets(bets)
        return sim_bets_response(bets, settled_now=settled_now, created=bet, config=config)


def delete_sim_bet(bet_id: str, query: dict[str, list[str]]) -> dict[str, Any]:
    bet_id = str(bet_id or "").strip()
    if not bet_id:
        raise ValueError("投注记录 ID 无效")
    config = game_from_query(query)
    ensure_sim_bets_supported(config)
    with BETS_LOCK:
        bets = load_sim_bets()
        deleted: dict[str, Any] | None = None
        remaining: list[dict[str, Any]] = []
        for bet in bets:
            if str(bet.get("id") or "") == bet_id and bet_game_key(bet) == config["key"]:
                deleted = bet
                continue
            remaining.append(bet)
        if deleted is None:
            raise KeyError("投注记录不存在或不属于当前彩种")
        write_sim_bets(remaining)
        return sim_bets_response(remaining, deleted=deleted, config=config)


def settle_sim_bet_store(
    rows: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
) -> int:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    with BETS_LOCK:
        bets = load_sim_bets()
        if not bets:
            return 0
        settled_now = settle_sim_bets(bets, rows, config)
        if settled_now:
            write_sim_bets(bets)
        return settled_now


def load_prediction_tracking_json(path: Path = DEFAULT_PREDICTION_TRACKING) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        record_id = str(item.get("id") or "").strip()
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        records.append(item)
    return records


def prediction_tracking_db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DEFAULT_PREDICTION_TRACKING_DB, timeout=3)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=3000")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_prediction_tracking_db() -> None:
    global PREDICTION_DB_INITIALIZED
    if PREDICTION_DB_INITIALIZED:
        return
    with PREDICTION_DB_INIT_LOCK:
        if PREDICTION_DB_INITIALIZED:
            return
        with prediction_tracking_db_connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_records (
                    id TEXT PRIMARY KEY,
                    game_key TEXT NOT NULL,
                    target_draw_time_ms INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    strategy_label TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prediction_records_game_target ON prediction_records(game_key, target_draw_time_ms DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prediction_records_game_status ON prediction_records(game_key, status)"
            )
            count = conn.execute("SELECT COUNT(*) FROM prediction_records").fetchone()[0]
            if count == 0:
                migrated = load_prediction_tracking_json()
                if migrated:
                    insert_prediction_tracking_records(conn, migrated)
            conn.commit()
        PREDICTION_DB_INITIALIZED = True


def insert_prediction_tracking_records(
    conn: sqlite3.Connection,
    records: list[dict[str, Any]],
) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO prediction_records (
            id, game_key, target_draw_time_ms, status, strategy_label, created_at, record_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                str(record.get("id") or ""),
                prediction_tracking_game_key(record),
                parse_int(record.get("targetDrawTimeMs"), 0),
                str(record.get("status") or "pending"),
                str(record.get("strategyLabel") or ""),
                str(record.get("createdAt") or ""),
                json.dumps(record, ensure_ascii=False, separators=(",", ":")),
            )
            for record in records
            if record.get("id")
        ],
    )


def prediction_tracking_records_from_rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        try:
            item = json.loads(row["record_json"])
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("id"):
            result = item.get("result")
            if isinstance(result, dict):
                reason = str(result.get("reason") or "")
                if reason in LEGACY_VOID_REASONS:
                    result["reason"] = LEGACY_VOID_REASONS[reason]
            records.append(item)
    return records


def load_prediction_tracking() -> list[dict[str, Any]]:
    init_prediction_tracking_db()
    with prediction_tracking_db_connect() as conn:
        rows = conn.execute(
            """
            SELECT record_json
            FROM prediction_records
            ORDER BY target_draw_time_ms DESC, created_at DESC, id DESC
            """
        ).fetchall()
    return prediction_tracking_records_from_rows(rows)


def load_prediction_tracking_for_game(
    game_key: str,
    *,
    status_filter: str = "all",
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
    init_prediction_tracking_db()
    params: list[Any] = [game_key]
    where = "game_key = ?"
    if status_filter != "all":
        where += " AND status = ?"
        params.append(status_filter)
    sql = f"""
        SELECT record_json
        FROM prediction_records
        WHERE {where}
        ORDER BY target_draw_time_ms DESC, created_at DESC, id DESC
    """
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, max(0, offset)])
    with prediction_tracking_db_connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return prediction_tracking_records_from_rows(rows)


def prediction_tracking_count(game_key: str | None = None, status_filter: str = "all") -> int:
    init_prediction_tracking_db()
    params: list[Any] = []
    where_parts: list[str] = []
    if game_key is not None:
        where_parts.append("game_key = ?")
        params.append(game_key)
    if status_filter != "all":
        where_parts.append("status = ?")
        params.append(status_filter)
    where = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
    with prediction_tracking_db_connect() as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM prediction_records{where}", params).fetchone()[0])


def write_prediction_tracking(
    records: list[dict[str, Any]],
) -> None:
    if not records:
        return
    init_prediction_tracking_db()
    with prediction_tracking_db_connect() as conn:
        insert_prediction_tracking_records(conn, records)
        conn.commit()


def delete_prediction_tracking_records(record_ids: list[str]) -> None:
    ids = [str(record_id or "").strip() for record_id in record_ids if str(record_id or "").strip()]
    if not ids:
        return
    init_prediction_tracking_db()
    with prediction_tracking_db_connect() as conn:
        conn.executemany("DELETE FROM prediction_records WHERE id = ?", [(record_id,) for record_id in ids])
        conn.commit()


def prediction_tracking_game_key(record: dict[str, Any]) -> str:
    return game_key_from_value(
        record.get("gameKey")
        or record.get("game")
        or record.get("lotteryId")
        or DEFAULT_GAME_KEY
    )


def prediction_tracking_record_id(fields: dict[str, Any]) -> str:
    key = {
        "gameKey": fields.get("gameKey"),
        "methodVersion": fields.get("methodVersion"),
        "basedOnDrawTimeMs": parse_int(fields.get("basedOnDrawTimeMs"), 0),
        "targetDrawTimeMs": parse_int(fields.get("targetDrawTimeMs"), 0),
        "mode": fields.get("mode"),
        "pickCount": parse_int(fields.get("pickCount"), 0),
        "numbers": [int(number) for number in fields.get("numbers") or []],
        "bonusNumber": fields.get("bonusNumber"),
    }
    text = json.dumps(key, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"pt_{hashlib.sha1(text.encode('utf-8')).hexdigest()[:20]}"


def prediction_tracking_batch_key(record: dict[str, Any]) -> tuple[str, str, int]:
    return (
        prediction_tracking_game_key(record),
        str(record.get("methodVersion") or ""),
        parse_int(record.get("targetDrawTimeMs"), 0),
    )


def prediction_tracking_records_from_payload(
    payload: dict[str, Any],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    predictions = payload.get("predictions") if isinstance(payload.get("predictions"), dict) else {}
    tickets = predictions.get("strategyTickets") if isinstance(predictions.get("strategyTickets"), list) else []
    forecasts = predictions.get("forecasts") if isinstance(predictions.get("forecasts"), list) else []
    target = forecasts[0] if forecasts else {}
    newest = (
        payload.get("newestTimelineDraw")
        if isinstance(payload.get("newestTimelineDraw"), dict)
        else payload.get("newestDraw")
        if isinstance(payload.get("newestDraw"), dict)
        else {}
    )
    target_ms = parse_int(target.get("drawTimeMs"), 0)
    based_ms = parse_int(newest.get("drawTimeMs"), 0)
    if target_ms <= 0 or based_ms <= 0 or not tickets:
        return []

    generated_at = str(payload.get("generatedAt") or utc_now_iso())
    method = str(predictions.get("method") or "")
    records: list[dict[str, Any]] = []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        numbers = [int(number) for number in ticket.get("numbers") or []]
        if not numbers:
            continue
        bonus_number_raw = ticket.get("bonusNumber")
        bonus_number = parse_int(bonus_number_raw, 0) if bonus_number_raw not in (None, "") else None
        mode = str(ticket.get("mode") or "main")
        pick_count = parse_int(ticket.get("pickCount"), len(numbers))
        odds = parse_float(ticket.get("odds"), 0)
        theoretical_hit_rate = parse_float(ticket.get("theoreticalHitRate"), 0)
        record = {
            "createdAt": utc_now_iso(),
            "predictionGeneratedAt": generated_at,
            "methodVersion": PREDICTION_TRACKING_METHOD_VERSION,
            "method": method,
            "gameKey": config["key"],
            "lotteryId": config["lotteryId"],
            "gameShortName": config["shortName"],
            "basedOnDrawTimeMs": based_ms,
            "basedOnDrawTimeUtc": newest.get("drawTimeUtc", ""),
            "basedOnDrawEventId": newest.get("drawEventId", ""),
            "targetDrawTimeMs": target_ms,
            "targetDrawTimeUtc": target.get("drawTimeUtc", ""),
            "targetDrawOffset": parse_int(target.get("drawOffset"), 1),
            "strategyLabel": str(ticket.get("label") or ""),
            "ticketLabel": str(ticket.get("ticketLabel") or "-".join(str(number) for number in numbers)),
            "mode": mode,
            "pickCount": pick_count,
            "numbers": numbers,
            "bonusNumber": bonus_number,
            "odds": round(odds, 4),
            "stake": 1,
            "theoreticalHitRate": theoretical_hit_rate,
            "breakEvenHitRate": parse_float(ticket.get("breakEvenHitRate"), 0),
            "fairOdds": parse_float(ticket.get("fairOdds"), 0),
            "evAtOdds": theoretical_hit_rate * odds - 1 if odds > 0 else 0,
            "recentWindow": parse_int(ticket.get("recentWindow"), 0),
            "recentHits": parse_int(ticket.get("recentHits"), 0),
            "recentHitRate": parse_float(ticket.get("recentHitRate"), 0),
            "recentHitRateCi": ticket.get("recentHitRateCi") or [0, 0],
            "currentMiss": parse_int(ticket.get("currentMiss"), 0),
            "maxMiss": parse_int(ticket.get("maxMiss"), 0),
            "chasePeriods": parse_int(ticket.get("chasePeriods"), 0),
            "missAllProbability": parse_float(ticket.get("missAllProbability"), 0),
            "score": parse_float(ticket.get("score"), 0),
            "status": "pending",
            "settledAt": "",
            "payout": 0,
            "profit": 0,
            "result": None,
        }
        if bonus_number:
            record["ticketLabel"] = f"{'-'.join(str(number) for number in numbers)} + {bonus_number}"
        record["id"] = prediction_tracking_record_id(record)
        records.append(record)
    return records


def add_prediction_tracking_snapshot(
    records: list[dict[str, Any]],
    payload: dict[str, Any],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    existing_ids = {str(record.get("id") or "") for record in records}
    existing_pending_batches = {
        prediction_tracking_batch_key(record)
        for record in records
        if str(record.get("status") or "pending") == "pending"
    }
    created: list[dict[str, Any]] = []
    for record in prediction_tracking_records_from_payload(payload, config):
        if prediction_tracking_batch_key(record) in existing_pending_batches:
            continue
        if record["id"] in existing_ids:
            continue
        records.append(record)
        existing_ids.add(record["id"])
        created.append(record)
    return created


def void_superseded_prediction_batches(
    records: list[dict[str, Any]],
    config: dict[str, Any],
    changed_records: list[dict[str, Any]] | None = None,
) -> int:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for record in records:
        if prediction_tracking_game_key(record) != config["key"]:
            continue
        if record.get("status") != "pending":
            continue
        key = prediction_tracking_batch_key(record)
        if not key[2]:
            continue
        grouped.setdefault(key, []).append(record)

    voided = 0
    for batch_records in grouped.values():
        base_times = {
            parse_int(record.get("basedOnDrawTimeMs"), 0)
            for record in batch_records
        }
        if len(base_times) <= 1:
            continue
        keep_base = max(base_times)
        for record in batch_records:
            if parse_int(record.get("basedOnDrawTimeMs"), 0) == keep_base:
                continue
            result = void_prediction_tracking_result(record, PREDICTION_VOID_REASON_SUPERSEDED)
            record["status"] = "void"
            record["settledAt"] = result["settledAt"]
            record["payout"] = result["payout"]
            record["profit"] = result["profit"]
            record["result"] = result
            if changed_records is not None:
                changed_records.append(record)
            voided += 1
    return voided


def evaluate_prediction_tracking_record(
    record: dict[str, Any],
    draw: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    numbers = tuple(int(number) for number in record.get("numbers") or [])
    bonus_raw = record.get("bonusNumber")
    bonus_number = parse_int(bonus_raw, 0) if bonus_raw not in (None, "") else None
    won = ticket_hit(draw, numbers, bonus_number)
    stake = parse_float(record.get("stake"), 1)
    odds = parse_float(record.get("odds"), 0)
    payout = round(stake * odds, 4) if won else 0
    profit = round(payout - stake, 4) if won else round(-stake, 4)
    draw_set = set(draw.get("numbers") or [])
    matched_numbers = [number for number in numbers if number in draw_set]
    if bonus_number:
        bonus_hit = parse_int(draw.get("bonusBall"), 0) == bonus_number
        reason = (
            f"主号命中 {len(matched_numbers)}/{len(numbers)}，"
            f"特殊号 {'命中' if bonus_hit else '未中'}"
        )
    else:
        reason = f"命中 {len(matched_numbers)}/{len(numbers)} 个指定号码"
    return {
        "won": won,
        "reason": reason,
        "matchedNumbers": matched_numbers,
        "draw": draw_result_snapshot(draw),
        "payout": payout,
        "profit": profit,
        "settledAt": utc_now_iso(),
    }


def cancelled_prediction_tracking_result(draw: dict[str, Any]) -> dict[str, Any]:
    return {
        "won": False,
        "cancelled": True,
        "reason": "当期开奖取消，追踪作废",
        "matchedNumbers": [],
        "draw": draw_result_snapshot(draw),
        "payout": 0,
        "profit": 0,
        "settledAt": utc_now_iso(),
    }


def void_prediction_tracking_result(record: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "won": False,
        "void": True,
        "reason": reason,
        "matchedNumbers": [],
        "draw": None,
        "payout": 0,
        "profit": 0,
        "settledAt": utc_now_iso(),
    }


def settle_prediction_tracking(
    records: list[dict[str, Any]],
    rows: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
    changed_records: list[dict[str, Any]] | None = None,
) -> int:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    rows = rows if rows is not None else load_history_rows(game_history_path(config), config)
    rows_by_time = {
        parse_int(row.get("drawTimeMs"), 0): row
        for row in rows
        if parse_int(row.get("drawTimeMs"), 0) > 0
    }
    latest_timeline_ms = max(rows_by_time.keys(), default=0)
    interval_ms = int(float(config.get("drawIntervalMinutes") or 0) * 60000)
    missing_target_grace_ms = max(interval_ms, 60000) if interval_ms > 0 else 60000
    settled = void_superseded_prediction_batches(records, config, changed_records)
    for record in records:
        if prediction_tracking_game_key(record) != config["key"]:
            continue
        if record.get("status") != "pending":
            continue
        target_ms = parse_int(record.get("targetDrawTimeMs"), 0)
        created_ms = parse_datetime_ms(record.get("createdAt"))
        if target_ms > 0 and created_ms > 0 and created_ms >= target_ms:
            result = void_prediction_tracking_result(record, PREDICTION_VOID_REASON_PAST_TARGET)
            record["status"] = "void"
            record["settledAt"] = result["settledAt"]
            record["payout"] = result["payout"]
            record["profit"] = result["profit"]
            record["result"] = result
            if changed_records is not None:
                changed_records.append(record)
            settled += 1
            continue
        draw = rows_by_time.get(target_ms)
        if draw is None:
            if target_ms > 0 and latest_timeline_ms >= target_ms + missing_target_grace_ms:
                result = void_prediction_tracking_result(record, PREDICTION_VOID_REASON_MISSING_TARGET)
                record["status"] = "void"
                record["settledAt"] = result["settledAt"]
                record["payout"] = result["payout"]
                record["profit"] = result["profit"]
                record["result"] = result
                if changed_records is not None:
                    changed_records.append(record)
                settled += 1
            continue
        if draw.get("isCancelled") or is_cancelled_status(draw.get("status")):
            result = cancelled_prediction_tracking_result(draw)
            record["status"] = "cancelled"
        else:
            result = evaluate_prediction_tracking_record(record, draw, config)
            record["status"] = "won" if result["won"] else "lost"
        record["settledAt"] = result["settledAt"]
        record["payout"] = result["payout"]
        record["profit"] = result["profit"]
        record["result"] = result
        if changed_records is not None:
            changed_records.append(record)
        settled += 1
    return settled


def prediction_tracking_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    pending = sum(1 for record in records if record.get("status") == "pending")
    won = sum(1 for record in records if record.get("status") == "won")
    lost = sum(1 for record in records if record.get("status") == "lost")
    cancelled = sum(1 for record in records if record.get("status") == "cancelled")
    void = sum(1 for record in records if record.get("status") == "void")
    settled = won + lost
    settled_records = [record for record in records if record.get("status") in {"won", "lost"}]
    expected_hits = sum(parse_float(record.get("theoreticalHitRate"), 0) for record in settled_records)
    theoretical_hit_rate = expected_hits / settled if settled else 0
    break_even_hit_rate = (
        sum(parse_float(record.get("breakEvenHitRate"), 0) for record in settled_records) / settled
        if settled
        else 0
    )
    stake_total = sum(parse_float(record.get("stake"), 1) for record in settled_records)
    payout_total = sum(parse_float(record.get("payout"), 0) for record in settled_records)
    profit_total = sum(parse_float(record.get("profit"), 0) for record in settled_records)
    hit_rate = won / settled if settled else 0
    ci_low, ci_high = wilson_interval(won, settled)
    warning = ""
    if settled >= 30 and theoretical_hit_rate > 0 and ci_high < theoretical_hit_rate:
        warning = "已结算样本的 95% 置信区间上沿低于理论命中率，当前候选票表现显著偏弱。"
    elif settled >= 30 and hit_rate < theoretical_hit_rate:
        warning = "已结算命中率低于理论命中率，继续观察样本外表现。"
    return {
        "total": total,
        "pending": pending,
        "won": won,
        "lost": lost,
        "cancelled": cancelled,
        "void": void,
        "settled": settled,
        "closed": settled + cancelled + void,
        "hitRate": hit_rate,
        "hitRateCi": [ci_low, ci_high],
        "theoreticalHitRate": theoretical_hit_rate,
        "expectedHits": expected_hits,
        "breakEvenHitRate": break_even_hit_rate,
        "stakeTotal": round(stake_total, 4),
        "payoutTotal": round(payout_total, 4),
        "profitTotal": round(profit_total, 4),
        "roi": profit_total / stake_total if stake_total > 0 else 0,
        "warning": warning,
    }


def prediction_tracking_group_summaries(
    records: list[dict[str, Any]],
    limit: int = 20,
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        key = "|".join(
            [
                prediction_tracking_game_key(record),
                str(record.get("methodVersion") or ""),
                str(record.get("strategyLabel") or ""),
                str(record.get("mode") or ""),
                str(record.get("pickCount") or ""),
            ]
        )
        groups.setdefault(key, []).append(record)

    summaries: list[dict[str, Any]] = []
    for grouped in groups.values():
        first = grouped[0]
        summary = prediction_tracking_summary(grouped)
        summary.update(
            {
                "gameKey": prediction_tracking_game_key(first),
                "gameShortName": first.get("gameShortName", ""),
                "strategyLabel": first.get("strategyLabel", ""),
                "mode": first.get("mode", ""),
                "pickCount": parse_int(first.get("pickCount"), 0),
                "odds": parse_float(first.get("odds"), 0),
            }
        )
        summaries.append(summary)
    summaries.sort(
        key=lambda item: (
            -parse_int(item.get("settled"), 0),
            -parse_int(item.get("total"), 0),
            str(item.get("gameShortName") or ""),
            str(item.get("strategyLabel") or ""),
        )
    )
    return summaries[:limit]


def adjacent_neighbors(number: int, total_numbers: int, distance: int = 1) -> list[int]:
    candidates = [number - distance, number + distance]
    return [candidate for candidate in candidates if 1 <= candidate <= total_numbers]


def adjacent_pair_candidates(number: int, total_numbers: int) -> list[tuple[str, str, tuple[int, ...]]]:
    candidates: list[tuple[str, str, tuple[int, ...]]] = []
    if number > 1:
        candidates.append(("adjacent_pair_left", "左邻二码", (number - 1, number)))
    if number < total_numbers:
        candidates.append(("adjacent_pair_right", "右邻二码", (number, number + 1)))
    return candidates


def adjacent_outer_pair_candidates(number: int, total_numbers: int) -> list[tuple[str, str, tuple[int, ...]]]:
    candidates: list[tuple[str, str, tuple[int, ...]]] = []
    if number > 2:
        candidates.append(("outer_pair_left", "外侧左邻二码", (number - 2, number - 1)))
    if number < total_numbers - 1:
        candidates.append(("outer_pair_right", "外侧右邻二码", (number + 1, number + 2)))
    return candidates


def adjacent_cross_halo_candidates(numbers: list[int], total_numbers: int) -> list[tuple[int, ...]]:
    if len(numbers) != 2:
        return []
    left_pool = [candidate for candidate in (numbers[0] - 1, numbers[0], numbers[0] + 1) if 1 <= candidate <= total_numbers]
    right_pool = [candidate for candidate in (numbers[1] - 1, numbers[1], numbers[1] + 1) if 1 <= candidate <= total_numbers]
    combos = {
        tuple(sorted((left, right)))
        for left in left_pool
        for right in right_pool
        if left != right
    }
    return sorted(combos)


def adjacent_four_ball_candidates(numbers: list[int], total_numbers: int) -> list[tuple[int, ...]]:
    if len(numbers) != 2:
        return []
    left_pairs = [pair for _key, _label, pair in adjacent_pair_candidates(numbers[0], total_numbers)]
    right_pairs = [pair for _key, _label, pair in adjacent_pair_candidates(numbers[1], total_numbers)]
    combos = {
        tuple(sorted((*left_pair, *right_pair)))
        for left_pair in left_pairs
        for right_pair in right_pairs
        if len(set((*left_pair, *right_pair))) == 4
    }
    return sorted(combos)


def adjacent_ticket_candidates_for_numbers(
    numbers: list[int],
    pick_count: int,
    total_numbers: int,
) -> list[tuple[str, str, tuple[int, ...]]]:
    candidates: list[tuple[str, str, tuple[int, ...]]] = []
    if pick_count == 1 and len(numbers) == 1:
        number = numbers[0]
        for variant_key, variant_label, pair in adjacent_pair_candidates(number, total_numbers):
            candidates.append((f"p1_{variant_key}", f"1球{variant_label}", pair))
    if pick_count == 2 and len(numbers) == 2:
        for number in numbers:
            for variant_key, variant_label, pair in adjacent_pair_candidates(number, total_numbers):
                candidates.append((f"p2_anchor_{variant_key}", f"2球锚点{variant_label}", pair))
            for variant_key, variant_label, pair in adjacent_outer_pair_candidates(number, total_numbers):
                candidates.append((f"p2_anchor_{variant_key}", f"2球锚点{variant_label}", pair))
        for combo in adjacent_cross_halo_candidates(numbers, total_numbers):
            candidates.append(("p2_cross_halo_pair", "2球交叉临码二码", combo))
        for combo in adjacent_four_ball_candidates(numbers, total_numbers):
            candidates.append(("p2_local_four_ball", "2球局部四码全中", combo))
    return candidates


def adjacent_derived_stats_summary(
    *,
    key: str,
    label: str,
    category: str,
    source_pick_count: int,
    derived_pick_count: int,
    odds: float,
    hits: int,
    samples: int,
    source_records: int,
    source_hit_records: int,
    stake_total: float,
    payout_total: float,
    examples: list[dict[str, Any]],
    hit_examples: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    theoretical = hit_probability_for(config, derived_pick_count) if category == "ticket" else 0
    break_even = 1 / odds if category == "ticket" and odds > 0 else 0
    profit_total = payout_total - stake_total
    ci_low, ci_high = wilson_interval(hits, samples)
    source_ci_low, source_ci_high = wilson_interval(source_hit_records, source_records)
    return {
        "key": key,
        "label": label,
        "category": category,
        "sourcePickCount": source_pick_count,
        "derivedPickCount": derived_pick_count,
        "odds": round(odds, 4),
        "samples": samples,
        "hits": hits,
        "hitRate": hits / samples if samples else 0,
        "hitRateCi": [ci_low, ci_high],
        "independentSamples": source_records,
        "sourceHitRecords": source_hit_records,
        "sourceHitRate": source_hit_records / source_records if source_records else 0,
        "sourceHitRateCi": [source_ci_low, source_ci_high],
        "theoreticalHitRate": theoretical,
        "hitRateVsTheory": hits / samples - theoretical if samples and theoretical else 0,
        "breakEvenHitRate": break_even,
        "stakeTotal": round(stake_total, 4),
        "payoutTotal": round(payout_total, 4),
        "profitTotal": round(profit_total, 4),
        "roi": profit_total / stake_total if stake_total > 0 else 0,
        "examples": examples[:ADJACENT_DERIVED_EXAMPLE_LIMIT],
        "hitExamples": hit_examples[:ADJACENT_DERIVED_HIT_DETAIL_LIMIT],
    }


def adjacent_source_record_id(record: dict[str, Any]) -> str:
    record_id = str(record.get("id") or "").strip()
    if record_id:
        return record_id
    source = {
        "game": prediction_tracking_game_key(record),
        "targetDrawTimeMs": parse_int(record.get("targetDrawTimeMs"), 0),
        "numbers": record.get("numbers") or [],
        "mode": record.get("mode") or "main",
        "pickCount": parse_int(record.get("pickCount"), 0),
    }
    text = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:20]


def add_adjacent_derived_stat_sample(
    groups: dict[str, dict[str, Any]],
    *,
    key: str,
    label: str,
    category: str,
    source_pick_count: int,
    derived_numbers: tuple[int, ...],
    draw_set: set[int],
    record: dict[str, Any],
    config: dict[str, Any],
    hit: bool | None = None,
) -> None:
    derived_numbers = tuple(sorted(int(number) for number in derived_numbers))
    derived_pick_count = len(derived_numbers)
    odds = (
        float(DEFAULT_MAIN_ODDS_BY_GAME.get(str(config.get("key")), {}).get(derived_pick_count, 0))
        if category == "ticket"
        else 0.0
    )
    group = groups.setdefault(
        key,
        {
            "key": key,
            "label": label,
            "category": category,
            "sourcePickCount": source_pick_count,
            "derivedPickCount": derived_pick_count,
            "odds": odds,
            "hits": 0,
            "samples": 0,
            "sourceIds": set(),
            "sourceHitIds": set(),
            "stakeTotal": 0.0,
            "payoutTotal": 0.0,
            "examples": [],
            "hitExamples": [],
        },
    )
    won = bool(hit) if hit is not None else all(number in draw_set for number in derived_numbers)
    source_id = adjacent_source_record_id(record)
    group["samples"] += 1
    group["hits"] += 1 if won else 0
    group["sourceIds"].add(source_id)
    if won:
        group["sourceHitIds"].add(source_id)
    if category == "ticket":
        group["stakeTotal"] += 1
        group["payoutTotal"] += odds if won else 0
    if len(group["examples"]) < ADJACENT_DERIVED_EXAMPLE_LIMIT:
        group["examples"].append(
            {
                "recordId": record.get("id", ""),
                "targetDrawTimeUtc": record.get("targetDrawTimeUtc", ""),
                "sourceNumbers": record.get("numbers") or [],
                "derivedNumbers": list(derived_numbers),
                "hit": won,
            }
        )
    if won and len(group["hitExamples"]) < ADJACENT_DERIVED_HIT_DETAIL_LIMIT:
        group["hitExamples"].append(
            {
                "recordId": record.get("id", ""),
                "targetDrawTimeUtc": record.get("targetDrawTimeUtc", ""),
                "sourceNumbers": record.get("numbers") or [],
                "derivedNumbers": list(derived_numbers),
                "drawNumbers": sorted(draw_set),
                "payout": odds if category == "ticket" else 0,
                "profit": (odds - 1) if category == "ticket" else 0,
            }
        )


def adjacent_scheme_summary(
    records: list[dict[str, Any]],
    config: dict[str, Any],
    total_numbers: int,
) -> dict[str, Any]:
    schemes: dict[int, dict[str, Any]] = {}
    for record in records:
        numbers = sorted(int(number) for number in record.get("numbers") or [])
        pick_count = parse_int(record.get("pickCount"), len(numbers))
        draw = (record.get("result") or {}).get("draw") or {}
        draw_set = {int(number) for number in draw.get("numbers") or []}
        if not numbers or not draw_set:
            continue
        candidates = adjacent_ticket_candidates_for_numbers(numbers, pick_count, total_numbers)
        if not candidates:
            continue
        stake = 0.0
        payout = 0.0
        winning_tickets: list[dict[str, Any]] = []
        for key, label, derived_numbers in candidates:
            derived_numbers = tuple(sorted(derived_numbers))
            odds = float(DEFAULT_MAIN_ODDS_BY_GAME.get(str(config.get("key")), {}).get(len(derived_numbers), 0))
            won = all(number in draw_set for number in derived_numbers)
            stake += 1
            if won:
                payout += odds
                item = {
                    "recordId": record.get("id", ""),
                    "targetDrawTimeUtc": record.get("targetDrawTimeUtc", ""),
                    "sourceNumbers": numbers,
                    "strategyKey": key,
                    "strategyLabel": label,
                    "derivedNumbers": list(derived_numbers),
                    "drawNumbers": sorted(draw_set),
                    "payout": odds,
                    "profit": odds - 1,
                }
                winning_tickets.append(item)
        scheme = schemes.setdefault(
            pick_count,
            {
                "key": f"source_p{pick_count}_scheme",
                "label": f"{pick_count}球整套派生方案",
                "sourcePickCount": pick_count,
                "records": 0,
                "winningRecords": 0,
                "stakeTotal": 0.0,
                "payoutTotal": 0.0,
                "ticketTotal": 0,
                "hitTickets": 0,
            },
        )
        scheme["records"] += 1
        scheme["ticketTotal"] += len(candidates)
        scheme["stakeTotal"] += stake
        scheme["payoutTotal"] += payout
        scheme["hitTickets"] += len(winning_tickets)
        if winning_tickets:
            scheme["winningRecords"] += 1

    items: list[dict[str, Any]] = []
    for item in schemes.values():
        stake_total = parse_float(item.get("stakeTotal"), 0)
        payout_total = parse_float(item.get("payoutTotal"), 0)
        profit_total = payout_total - stake_total
        records = parse_int(item.get("records"), 0)
        winning_records = parse_int(item.get("winningRecords"), 0)
        ticket_total = parse_int(item.get("ticketTotal"), 0)
        hit_tickets = parse_int(item.get("hitTickets"), 0)
        ci_low, ci_high = wilson_interval(winning_records, records)
        item.update(
            {
                "stakeTotal": round(stake_total, 4),
                "payoutTotal": round(payout_total, 4),
                "profitTotal": round(profit_total, 4),
                "roi": profit_total / stake_total if stake_total > 0 else 0,
                "recordHitRate": winning_records / records if records else 0,
                "recordHitRateCi": [ci_low, ci_high],
                "ticketHitRate": hit_tickets / ticket_total if ticket_total else 0,
                "avgTicketsPerRecord": ticket_total / records if records else 0,
            }
        )
        items.append(item)
    items.sort(key=lambda item: parse_int(item.get("sourcePickCount"), 0))
    return {"items": items}


def adjacent_derived_stats(records: list[dict[str, Any]], config: dict[str, Any] | None) -> dict[str, Any]:
    if config is None or str(config.get("key")) not in ADJACENT_DERIVED_STATS_GAME_KEYS:
        return {"enabled": False, "items": [], "note": "当前彩种暂未启用临码派生统计"}

    total_numbers = int(config["totalNumbers"])
    groups: dict[str, dict[str, Any]] = {}
    source_records = [
        record
        for record in records
        if prediction_tracking_game_key(record) == config["key"]
        and record.get("status") in {"won", "lost"}
        and str(record.get("mode") or "main") == "main"
        and parse_int(record.get("pickCount"), 0) in {1, 2}
        and isinstance(record.get("result"), dict)
        and isinstance((record.get("result") or {}).get("draw"), dict)
    ]

    for record in source_records:
        numbers = sorted(int(number) for number in record.get("numbers") or [])
        pick_count = parse_int(record.get("pickCount"), len(numbers))
        draw = (record.get("result") or {}).get("draw") or {}
        draw_set = {int(number) for number in draw.get("numbers") or []}
        if not numbers or not draw_set:
            continue

        if pick_count == 1 and len(numbers) == 1:
            number = numbers[0]
            neighbors = adjacent_neighbors(number, total_numbers)
            add_adjacent_derived_stat_sample(
                groups,
                key="p1_original_single_hit",
                label="1球原号命中",
                category="diagnostic",
                source_pick_count=1,
                derived_numbers=(number,),
                draw_set=draw_set,
                record=record,
                config=config,
            )
            if number > 1:
                add_adjacent_derived_stat_sample(
                    groups,
                    key="p1_left_adjacent_hit",
                    label="1球左临命中",
                    category="diagnostic",
                    source_pick_count=1,
                    derived_numbers=(number - 1,),
                    draw_set=draw_set,
                    record=record,
                    config=config,
                )
            if number < total_numbers:
                add_adjacent_derived_stat_sample(
                    groups,
                    key="p1_right_adjacent_hit",
                    label="1球右临命中",
                    category="diagnostic",
                    source_pick_count=1,
                    derived_numbers=(number + 1,),
                    draw_set=draw_set,
                    record=record,
                    config=config,
                )
            add_adjacent_derived_stat_sample(
                groups,
                key="p1_any_adjacent_hit",
                label="1球任一临码命中",
                category="diagnostic",
                source_pick_count=1,
                derived_numbers=tuple(neighbors),
                draw_set=draw_set,
                record=record,
                config=config,
                hit=any(candidate in draw_set for candidate in neighbors),
            )
            zone = tuple(sorted({number, *neighbors}))
            add_adjacent_derived_stat_sample(
                groups,
                key="p1_local_zone_hit",
                label="1球三号区间命中",
                category="diagnostic",
                source_pick_count=1,
                derived_numbers=zone,
                draw_set=draw_set,
                record=record,
                config=config,
                hit=any(candidate in draw_set for candidate in zone),
            )
            for variant_key, variant_label, pair in adjacent_ticket_candidates_for_numbers(numbers, pick_count, total_numbers):
                add_adjacent_derived_stat_sample(
                    groups,
                    key=variant_key,
                    label=variant_label,
                    category="ticket",
                    source_pick_count=1,
                    derived_numbers=pair,
                    draw_set=draw_set,
                    record=record,
                    config=config,
                )

        if pick_count == 2 and len(numbers) == 2:
            for variant_key, variant_label, combo in adjacent_ticket_candidates_for_numbers(numbers, pick_count, total_numbers):
                add_adjacent_derived_stat_sample(
                    groups,
                    key=variant_key,
                    label=variant_label,
                    category="ticket",
                    source_pick_count=2,
                    derived_numbers=combo,
                    draw_set=draw_set,
                    record=record,
                    config=config,
                )

    scheme_summary = adjacent_scheme_summary(source_records, config, total_numbers)
    items = [
        adjacent_derived_stats_summary(
            key=str(group["key"]),
            label=str(group["label"]),
            category=str(group["category"]),
            source_pick_count=parse_int(group.get("sourcePickCount"), 0),
            derived_pick_count=parse_int(group.get("derivedPickCount"), 0),
            odds=parse_float(group.get("odds"), 0),
            hits=parse_int(group.get("hits"), 0),
            samples=parse_int(group.get("samples"), 0),
            source_records=len(group.get("sourceIds") or set()),
            source_hit_records=len(group.get("sourceHitIds") or set()),
            stake_total=parse_float(group.get("stakeTotal"), 0),
            payout_total=parse_float(group.get("payoutTotal"), 0),
            examples=group.get("examples") or [],
            hit_examples=group.get("hitExamples") or [],
            config=config,
        )
        for group in groups.values()
    ]
    items = [item for item in items if item["category"] == "ticket"]
    items.sort(
        key=lambda item: (
            0 if item["category"] == "ticket" else 1,
            item["sourcePickCount"],
            item["derivedPickCount"],
            str(item["label"]),
        )
    )
    return {
        "enabled": True,
        "gameKey": config["key"],
        "sourceSettledRecords": len(source_records),
        "items": items,
        "schemeSummary": scheme_summary,
        "note": "临码派生统计由已结算预测记录按固定规则计算；投注类按单位注额估算 ROI。",
    }


def adjacent_derived_hit_rows(records: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    if str(config.get("key")) not in ADJACENT_DERIVED_STATS_GAME_KEYS:
        return []
    total_numbers = int(config["totalNumbers"])
    rows: list[dict[str, Any]] = []
    source_records = [
        record
        for record in records
        if prediction_tracking_game_key(record) == config["key"]
        and record.get("status") in {"won", "lost"}
        and str(record.get("mode") or "main") == "main"
        and parse_int(record.get("pickCount"), 0) in {1, 2}
        and isinstance(record.get("result"), dict)
        and isinstance((record.get("result") or {}).get("draw"), dict)
    ]
    for record in source_records:
        numbers = sorted(int(number) for number in record.get("numbers") or [])
        pick_count = parse_int(record.get("pickCount"), len(numbers))
        draw = (record.get("result") or {}).get("draw") or {}
        draw_set = {int(number) for number in draw.get("numbers") or []}
        if not numbers or not draw_set:
            continue
        candidates = adjacent_ticket_candidates_for_numbers(
            numbers,
            pick_count,
            total_numbers,
        )
        stake_total = len(candidates)
        for strategy_key, strategy_label, derived_numbers in candidates:
            derived_numbers = tuple(sorted(derived_numbers))
            won = all(number in draw_set for number in derived_numbers)
            if not won:
                continue
            odds = float(DEFAULT_MAIN_ODDS_BY_GAME.get(str(config.get("key")), {}).get(len(derived_numbers), 0))
            rows.append(
                {
                    "recordId": record.get("id", ""),
                    "targetDrawTimeUtc": record.get("targetDrawTimeUtc", ""),
                    "targetDrawTimeMs": parse_int(record.get("targetDrawTimeMs"), 0),
                    "sourcePickCount": pick_count,
                    "sourceNumbers": numbers,
                    "stakeTotal": stake_total,
                    "strategyKey": strategy_key,
                    "strategyLabel": strategy_label,
                    "derivedNumbers": list(derived_numbers),
                    "drawNumbers": sorted(draw_set),
                    "payout": odds,
                    "profit": odds - 1,
                }
            )
    rows.sort(key=lambda item: (parse_int(item.get("targetDrawTimeMs"), 0), str(item.get("recordId") or "")), reverse=True)
    return rows


def adjacent_derived_hit_group_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        record_id = str(row.get("recordId") or "")
        group = groups.setdefault(
            record_id,
            {
                "recordId": record_id,
                "targetDrawTimeUtc": row.get("targetDrawTimeUtc", ""),
                "targetDrawTimeMs": parse_int(row.get("targetDrawTimeMs"), 0),
                "sourcePickCount": parse_int(row.get("sourcePickCount"), 0),
                "sourceNumbers": row.get("sourceNumbers") or [],
                "stakeTotal": parse_float(row.get("stakeTotal"), 0),
                "hitTickets": 0,
                "payoutTotal": 0.0,
                "profitTotal": 0.0,
                "derivedTickets": [],
                "drawNumbers": row.get("drawNumbers") or [],
            },
        )
        group["hitTickets"] += 1
        group["payoutTotal"] += parse_float(row.get("payout"), 0)
        group["profitTotal"] += parse_float(row.get("profit"), 0)
        group["derivedTickets"].append(
            {
                "strategyKey": row.get("strategyKey", ""),
                "strategyLabel": row.get("strategyLabel", ""),
                "derivedNumbers": row.get("derivedNumbers") or [],
                "payout": row.get("payout", 0),
                "profit": row.get("profit", 0),
            }
        )
    result = list(groups.values())
    for item in result:
        stake_total = parse_float(item.get("stakeTotal"), 0)
        payout_total = parse_float(item.get("payoutTotal"), 0)
        hit_only_profit_total = parse_float(item.get("profitTotal"), 0)
        item["stakeTotal"] = round(stake_total, 4)
        item["payoutTotal"] = round(payout_total, 4)
        item["profitTotal"] = round(payout_total - stake_total, 4)
        item["hitOnlyProfitTotal"] = round(hit_only_profit_total, 4)
    result.sort(key=lambda item: (parse_int(item.get("targetDrawTimeMs"), 0), str(item.get("recordId") or "")), reverse=True)
    return result


def adjacent_derived_hits_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_prediction_tracking_supported(config)
    page = max(1, parse_int(query.get("page", ["1"])[0], 1))
    page_size = max(10, min(parse_int(query.get("pageSize", ["50"])[0], 50), 200))
    search = str(query.get("q", [""])[0] or "").strip().lower()
    strategy = str(query.get("strategy", ["all"])[0] or "all").strip()
    group_by = str(query.get("groupBy", ["record"])[0] or "record").strip()
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
    rows = adjacent_derived_hit_rows(records, config)
    if strategy != "all":
        rows = [row for row in rows if str(row.get("strategyKey") or "") == strategy]
    if search:
        rows = [
            row
            for row in rows
            if search
            in " ".join(
                [
                    str(row.get("strategyLabel") or ""),
                    "-".join(str(number) for number in row.get("sourceNumbers") or []),
                    "-".join(str(number) for number in row.get("derivedNumbers") or []),
                    "-".join(str(number) for number in row.get("drawNumbers") or []),
                    str(row.get("targetDrawTimeUtc") or ""),
                ]
            ).lower()
        ]
    if group_by == "record":
        rows = adjacent_derived_hit_group_rows(rows)
    total = len(rows)
    total_page = max(1, math.ceil(total / page_size))
    page = max(1, min(page, total_page))
    start = (page - 1) * page_size
    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "game": game_public_config(config),
        "q": search,
        "strategy": strategy,
        "groupBy": group_by,
        "page": page,
        "pageSize": page_size,
        "total": total,
        "totalPage": total_page,
        "items": rows[start : start + page_size],
    }


def adjacent_derived_stats_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_prediction_tracking_supported(config)
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "game": game_public_config(config),
        "adjacentStats": adjacent_derived_stats(records, config),
    }


def prediction_tracking_response(
    records: list[dict[str, Any]],
    *,
    settled_now: int = 0,
    created: list[dict[str, Any]] | None = None,
    deleted: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    page: int = 1,
    page_size: int = 50,
    status_filter: str = "all",
    page_items: list[dict[str, Any]] | None = None,
    total_items: int | None = None,
    all_total: int | None = None,
    auto_sync: dict[str, Any] | None = None,
    groups: list[dict[str, Any]] | None = None,
    adjacent_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scoped_records = (
        [record for record in records if prediction_tracking_game_key(record) == config["key"]]
        if config is not None
        else records
    )
    allowed_statuses = {"pending", "won", "lost", "cancelled", "void"}
    status_filter = status_filter if status_filter in allowed_statuses else "all"
    page_size = max(10, min(page_size, 200))
    if page_items is None:
        filtered_records = (
            [record for record in scoped_records if record.get("status") == status_filter]
            if status_filter != "all"
            else scoped_records
        )
        ordered = sorted(
            filtered_records,
            key=lambda record: (
                parse_int(record.get("targetDrawTimeMs"), 0),
                str(record.get("createdAt") or ""),
            ),
            reverse=True,
        )
        total_items = len(ordered)
    else:
        ordered = list(page_items)
        total_items = len(ordered) if total_items is None else total_items
    total_page = max(1, math.ceil(total_items / page_size))
    page = max(1, min(page, total_page))
    start = (page - 1) * page_size
    end = start + page_size
    summary = prediction_tracking_summary(scoped_records)
    all_summary = {"total": all_total} if all_total is not None else prediction_tracking_summary(records)
    group_items = groups if groups is not None else prediction_tracking_group_summaries(scoped_records)
    return {
        "ok": True,
        "game": game_public_config(config) if config is not None else None,
        "generatedAt": utc_now_iso(),
        "trackingFile": file_info(DEFAULT_PREDICTION_TRACKING),
        "trackingDb": file_info(DEFAULT_PREDICTION_TRACKING_DB),
        "settledNow": settled_now,
        "autoSync": auto_sync,
        "createdNow": len(created or []),
        "created": (created or [])[:10],
        "deleted": deleted,
        "summary": summary,
        "allSummary": all_summary,
        "groups": group_items,
        "allGroups": group_items,
        "adjacentStats": adjacent_stats,
        "statusFilter": status_filter,
        "page": page,
        "pageSize": page_size,
        "total": total_items,
        "totalPage": total_page,
        "items": ordered if page_items is not None else ordered[start:end],
        "allItems": [],
    }


def prediction_tracking_touch_response(
    records: list[dict[str, Any]],
    *,
    settled_now: int = 0,
    created: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scoped_records = (
        [record for record in records if prediction_tracking_game_key(record) == config["key"]]
        if config is not None
        else records
    )
    return {
        "settledNow": settled_now,
        "createdNow": len(created or []),
        "summary": prediction_tracking_summary(scoped_records),
        "allSummary": {"total": prediction_tracking_count()},
    }


def prediction_tracking_needs_auto_sync(
    records: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> bool:
    if not records:
        return False
    latest_ms = max(
        (parse_int(row.get("drawTimeMs"), 0) for row in rows),
        default=0,
    )
    now_ms = int(time.time() * 1000)
    interval_ms = int(float(config.get("drawIntervalMinutes") or 0) * 60000)
    grace_ms = max(15000, min(interval_ms // 2 if interval_ms > 0 else 15000, 60000))
    for record in records:
        if prediction_tracking_game_key(record) != config["key"]:
            continue
        if record.get("status") != "pending":
            continue
        target_ms = parse_int(record.get("targetDrawTimeMs"), 0)
        if target_ms > 0 and target_ms + grace_ms <= now_ms and latest_ms < target_ms:
            return True
    return False


def maybe_auto_sync_prediction_tracking(
    config: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
    if not prediction_tracking_needs_auto_sync(records, rows, config):
        return rows, None

    now = time.monotonic()
    with PREDICTION_TRACKING_AUTO_SYNC_LOCK:
        last_attempt = PREDICTION_TRACKING_AUTO_SYNC_LAST_ATTEMPT.get(config["key"], 0.0)
        interval_minutes = float(config.get("drawIntervalMinutes") or 0)
        cooldown_seconds = max(PREDICTION_TRACKING_AUTO_SYNC_COOLDOWN_SECONDS, interval_minutes * 30)
        if now - last_attempt < cooldown_seconds:
            return rows, {"skipped": True, "reason": "cooldown"}
        PREDICTION_TRACKING_AUTO_SYNC_LAST_ATTEMPT[config["key"]] = now

    result = refresh_history(
        {
            "game": config["key"],
            "mode": "incremental",
            "pageSize": 100,
            "maxPages": 2,
            "sleep": 0.05,
            "skipSupplement": False,
        }
    )
    with DATA_LOCK:
        refreshed_rows = load_history_rows(game_history_path(config), config)
    return refreshed_rows, result


def touch_prediction_tracking_for_payload(
    payload: dict[str, Any],
    config: dict[str, Any],
    rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if rows is None:
        with DATA_LOCK:
            rows = load_history_rows(game_history_path(config), config)
    auto_sync: dict[str, Any] | None = None
    try:
        rows, auto_sync = maybe_auto_sync_prediction_tracking(config, rows)
    except Exception as exc:
        auto_sync = {"ok": False, "error": str(exc)}
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
        changed_records: list[dict[str, Any]] = []
        settled_now = settle_prediction_tracking(records, rows, config, changed_records)
        created = add_prediction_tracking_snapshot(records, payload, config)
        if settled_now or created:
            write_prediction_tracking(changed_records + created)
        return prediction_tracking_touch_response(
            records,
            settled_now=settled_now,
            created=created,
            config=config,
        ) | {"autoSync": auto_sync}


def prediction_tracking_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_prediction_tracking_supported(config)
    page = max(1, parse_int(query.get("page", ["1"])[0], 1))
    page_size = max(10, min(parse_int(query.get("pageSize", ["50"])[0], 50), 200))
    status_filter = str(query.get("status", ["all"])[0] or "all")
    allowed_statuses = {"pending", "won", "lost", "cancelled", "void"}
    status_filter = status_filter if status_filter in allowed_statuses else "all"
    with DATA_LOCK:
        rows = load_history_rows(game_history_path(config), config)
    auto_sync: dict[str, Any] | None = None
    try:
        rows, auto_sync = maybe_auto_sync_prediction_tracking(config, rows)
    except Exception as exc:
        auto_sync = {"ok": False, "error": str(exc)}
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
        changed_records: list[dict[str, Any]] = []
        settled_now = settle_prediction_tracking(records, rows, config, changed_records)
        if settled_now:
            write_prediction_tracking(changed_records)
        total_items = prediction_tracking_count(config["key"], status_filter)
        total_page = max(1, math.ceil(total_items / page_size))
        page = max(1, min(page, total_page))
        page_items = load_prediction_tracking_for_game(
            config["key"],
            status_filter=status_filter,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
    groups = prediction_tracking_group_summaries(records)
    all_total = prediction_tracking_count()
    return prediction_tracking_response(
        records,
        settled_now=settled_now,
        config=config,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        page_items=page_items,
        total_items=total_items,
        all_total=all_total,
        auto_sync=auto_sync,
        groups=groups,
    )


def settle_prediction_tracking_store(
    rows: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
) -> int:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
        if not records:
            return 0
        changed_records: list[dict[str, Any]] = []
        settled_now = settle_prediction_tracking(records, rows, config, changed_records)
        if settled_now:
            write_prediction_tracking(changed_records)
        return settled_now


def settle_prediction_tracking_request(payload: dict[str, Any]) -> dict[str, Any]:
    config = game_from_options(payload)
    with DATA_LOCK:
        rows = load_history_rows(game_history_path(config), config)
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
        changed_records: list[dict[str, Any]] = []
        settled_now = settle_prediction_tracking(records, rows, config, changed_records)
        if settled_now:
            write_prediction_tracking(changed_records)
        return prediction_tracking_response(records, settled_now=settled_now, config=config)


def delete_prediction_tracking(record_id: str, query: dict[str, list[str]]) -> dict[str, Any]:
    record_id = str(record_id or "").strip()
    if not record_id:
        raise ValueError("追踪记录 ID 无效")
    config = game_from_query(query)
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
        deleted: dict[str, Any] | None = None
        remaining: list[dict[str, Any]] = []
        for record in records:
            if str(record.get("id") or "") == record_id and prediction_tracking_game_key(record) == config["key"]:
                deleted = record
                continue
            remaining.append(record)
        if deleted is None:
            raise KeyError("追踪记录不存在或不属于当前彩种")
        delete_prediction_tracking_records([record_id])
        return prediction_tracking_response(remaining, deleted=deleted, config=config)


def default_prediction_auto_config() -> dict[str, Any]:
    return {
        "enabled": False,
        "pollSeconds": 60,
        "sync": True,
        "maxPages": 2,
        "pageSize": 100,
        "sleep": 0.05,
        "skipSupplement": True,
        "games": {
            key: {"enabled": supports_predictions(config)}
            for key, config in LOTTERY_GAMES.items()
        },
    }


def load_prediction_auto_config() -> dict[str, Any]:
    config = default_prediction_auto_config()
    if DEFAULT_PREDICTION_AUTO_CONFIG.exists():
        try:
            with DEFAULT_PREDICTION_AUTO_CONFIG.open("r", encoding="utf-8") as fh:
                stored = json.load(fh)
        except (OSError, json.JSONDecodeError):
            stored = {}
        if isinstance(stored, dict):
            config.update({key: value for key, value in stored.items() if key != "games"})
            stored_games = stored.get("games") if isinstance(stored.get("games"), dict) else {}
            for key, value in stored_games.items():
                if key in config["games"] and isinstance(value, dict):
                    config["games"][key].update(value)
    for key, game_config in LOTTERY_GAMES.items():
        if not supports_predictions(game_config):
            config["games"].setdefault(key, {})["enabled"] = False
    config["pollSeconds"] = max(30, min(parse_int(config.get("pollSeconds"), 60), 3600))
    config["maxPages"] = max(1, min(parse_int(config.get("maxPages"), 2), 20))
    config["pageSize"] = max(10, min(parse_int(config.get("pageSize"), 100), 100))
    config["sleep"] = max(0, min(parse_float(config.get("sleep"), 0.05), 5))
    return config


def write_prediction_auto_config(config: dict[str, Any]) -> None:
    temp_path = DEFAULT_PREDICTION_AUTO_CONFIG.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    replace_path_with_retry(temp_path, DEFAULT_PREDICTION_AUTO_CONFIG)


def set_prediction_auto_status(**updates: Any) -> None:
    with PREDICTION_AUTO_LOCK:
        PREDICTION_AUTO_STATUS.update(updates)


def prediction_auto_status_payload() -> dict[str, Any]:
    config = load_prediction_auto_config()
    with PREDICTION_AUTO_LOCK:
        status = dict(PREDICTION_AUTO_STATUS)
        thread_alive = PREDICTION_AUTO_THREAD is not None and PREDICTION_AUTO_THREAD.is_alive()
    status.update(
        {
            "ok": True,
            "enabled": bool(config.get("enabled")),
            "running": thread_alive,
            "config": config,
            "configFile": file_info(DEFAULT_PREDICTION_AUTO_CONFIG),
        }
    )
    return status


def prediction_auto_enabled_games(config: dict[str, Any]) -> list[str]:
    games = config.get("games") if isinstance(config.get("games"), dict) else {}
    return [
        key
        for key, game_config in games.items()
        if key in LOTTERY_GAMES
        and supports_predictions(LOTTERY_GAMES[key])
        and isinstance(game_config, dict)
        and game_config.get("enabled")
    ]


def prediction_auto_history_marker(config: dict[str, Any]) -> tuple[int, int, str, str]:
    with DATA_LOCK:
        rows = load_history_rows(game_history_path(config), config)
    latest = rows[0] if rows else {}
    return (
        len(rows),
        parse_int(latest.get("drawTimeMs"), 0),
        str(latest.get("drawEventId") or ""),
        str(latest.get("status") or ""),
    )


def prediction_tracking_summary_for_config(config: dict[str, Any]) -> dict[str, Any]:
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
    return prediction_tracking_summary(records)


def run_prediction_auto_once(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for key in prediction_auto_enabled_games(config):
        try:
            game_config = LOTTERY_GAMES[key]
            refresh_result: dict[str, Any] | None = None
            if config.get("sync", True):
                refresh_result = refresh_history(
                    {
                        "game": key,
                        "mode": "incremental",
                        "pageSize": parse_int(config.get("pageSize"), 100),
                        "maxPages": parse_int(config.get("maxPages"), 2),
                        "sleep": parse_float(config.get("sleep"), 0.05),
                        "skipSupplement": bool(config.get("skipSupplement", True)),
                    }
                )
            new_rows = parse_int((refresh_result or {}).get("newRows"), 0)
            settled_from_refresh = parse_int((refresh_result or {}).get("settledPredictions"), 0)
            marker = prediction_auto_history_marker(game_config)
            previous_marker = PREDICTION_AUTO_HISTORY_MARKERS.get(key)
            should_generate_prediction = (
                not config.get("sync", True)
                or previous_marker is None
                or previous_marker != marker
                or new_rows > 0
                or settled_from_refresh > 0
            )
            skipped_prediction = False
            if should_generate_prediction:
                prediction = predictions_payload({"game": [key]})
                tracking = prediction.get("predictionTracking") or {}
                PREDICTION_AUTO_HISTORY_MARKERS[key] = marker
            else:
                tracking = {
                    "settledNow": 0,
                    "createdNow": 0,
                    "summary": prediction_tracking_summary_for_config(game_config),
                }
                skipped_prediction = True
            results.append(
                {
                    "game": key,
                    "shortName": game_config["shortName"],
                    "newRows": new_rows,
                    "settledPredictions": settled_from_refresh + parse_int(tracking.get("settledNow"), 0),
                    "createdPredictions": parse_int(tracking.get("createdNow"), 0),
                    "trackingTotal": parse_int((tracking.get("summary") or {}).get("total"), 0),
                    "skippedPrediction": skipped_prediction,
                    "generatedAt": utc_now_iso(),
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "game": key,
                    "shortName": str(LOTTERY_GAMES[key].get("shortName") or key),
                    "error": str(exc),
                    "errorType": type(exc).__name__,
                }
            )
    return results, errors


def prediction_auto_worker() -> None:
    while not PREDICTION_AUTO_STOP.is_set():
        config = load_prediction_auto_config()
        if not config.get("enabled"):
            break
        started_at = utc_now_iso()
        set_prediction_auto_status(
            status="running",
            running=True,
            enabled=True,
            lastRunAt=started_at,
            message="自动追踪运行中",
        )
        results, errors = run_prediction_auto_once(config)
        poll_seconds = parse_int(config.get("pollSeconds"), 60)
        next_run_ts = time.time() + poll_seconds
        set_prediction_auto_status(
            status="running",
            running=True,
            enabled=True,
            lastRunAt=started_at,
            nextRunAt=datetime.fromtimestamp(next_run_ts, tz=UTC).isoformat(timespec="seconds"),
            message=f"自动追踪完成：{len(results)} 个彩种，{len(errors)} 个错误",
            results=results,
            errors=errors,
        )
        if PREDICTION_AUTO_STOP.wait(poll_seconds):
            break
    set_prediction_auto_status(
        status="stopped",
        running=False,
        enabled=False,
        nextRunAt="",
        message="自动追踪已停止",
    )


def start_prediction_auto(config_update: dict[str, Any] | None = None) -> dict[str, Any]:
    global PREDICTION_AUTO_THREAD
    config = load_prediction_auto_config()
    if config_update:
        config.update({key: value for key, value in config_update.items() if key != "games"})
        if isinstance(config_update.get("games"), dict):
            for key, value in config_update["games"].items():
                if key in config["games"] and isinstance(value, dict):
                    config["games"][key].update(value)
    config["enabled"] = True
    write_prediction_auto_config(config)
    already_running = False
    with PREDICTION_AUTO_LOCK:
        if PREDICTION_AUTO_THREAD is not None and PREDICTION_AUTO_THREAD.is_alive():
            already_running = True
        else:
            PREDICTION_AUTO_STOP.clear()
            PREDICTION_AUTO_THREAD = threading.Thread(target=prediction_auto_worker, daemon=True)
            PREDICTION_AUTO_THREAD.start()
    if not already_running:
        set_prediction_auto_status(status="starting", running=True, enabled=True, message="自动追踪启动中")
    return prediction_auto_status_payload()


def stop_prediction_auto() -> dict[str, Any]:
    config = load_prediction_auto_config()
    config["enabled"] = False
    write_prediction_auto_config(config)
    PREDICTION_AUTO_STOP.set()
    set_prediction_auto_status(status="stopping", running=False, enabled=False, message="自动追踪停止中")
    return prediction_auto_status_payload()


def prediction_auto_request(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip().lower()
    if action == "start":
        return start_prediction_auto(payload.get("config") if isinstance(payload.get("config"), dict) else None)
    if action == "stop":
        return stop_prediction_auto()
    if action == "runonce":
        config = load_prediction_auto_config()
        if isinstance(payload.get("config"), dict):
            config.update({key: value for key, value in payload["config"].items() if key != "games"})
        results, errors = run_prediction_auto_once(config)
        set_prediction_auto_status(
            status="stopped",
            running=False,
            lastRunAt=utc_now_iso(),
            message=f"手动自动追踪轮询完成：{len(results)} 个彩种，{len(errors)} 个错误",
            results=results,
            errors=errors,
        )
        return prediction_auto_status_payload()
    if action == "save":
        config = load_prediction_auto_config()
        update = payload.get("config") if isinstance(payload.get("config"), dict) else {}
        config.update({key: value for key, value in update.items() if key != "games"})
        if isinstance(update.get("games"), dict):
            for key, value in update["games"].items():
                if key in config["games"] and isinstance(value, dict):
                    config["games"][key].update(value)
        write_prediction_auto_config(config)
        return prediction_auto_status_payload()
    raise ValueError("未知自动追踪操作")


def history_cache_identity(path: Path = DEFAULT_HISTORY) -> dict[str, Any]:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return {"mtimeNs": 0, "size": 0}
    return {"mtimeNs": stat.st_mtime_ns, "size": stat.st_size}


def response_etag(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def normalize_backtest_request(
    payload: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or game_from_options(payload)
    ensure_backtest_supported(config)
    strategy = str(payload.get("strategy") or "triple_top_n").strip()
    params = payload.get("params") if isinstance(payload.get("params"), dict) else {}

    if strategy.startswith("condition_fixed:"):
        params = {**params, "condition": strategy.split(":", 1)[1]}
        strategy = "condition_fixed"
    if strategy.startswith("shape_top_n:"):
        params = {**params, "condition": strategy.split(":", 1)[1]}
        strategy = "shape_top_n"
    if strategy not in BACKTEST_STRATEGIES:
        raise ValueError("未知回测策略")

    window = payload.get("window") if isinstance(payload.get("window"), dict) else {}
    top_n = max(1, parse_int(params.get("top_n"), 3))
    miss_threshold = max(0, parse_int(params.get("miss_threshold"), 0))
    train_window = max(
        100,
        min(parse_int(window.get("train"), 10000), BACKTEST_MAX_TRAIN_WINDOW),
    )
    test_window = max(
        10,
        min(parse_int(window.get("test"), 1000), BACKTEST_MAX_TEST_WINDOW),
    )
    stake = parse_float(payload.get("stake"), 1.0)
    odds = parse_float(payload.get("odds"), 60.0)
    if stake <= 0:
        raise ValueError("每注投入必须大于 0")
    if odds <= 1:
        raise ValueError("赔率必须大于 1")

    if strategy == "pair_top_n":
        top_n = min(top_n, len(pair_groups(config)))
    elif strategy == "triple_top_n":
        top_n = min(top_n, len(triple_groups(config)))
    elif strategy == "quad_top_n":
        top_n = min(top_n, len(quad_groups(config)))
    elif strategy == "exact_numbers":
        numbers = parse_bet_numbers(
            params.get("numbers") or payload.get("numbers"),
            int(config["totalNumbers"]),
        )
        if not numbers:
            raise ValueError("指定号码组回测需要填写号码")
        if len(numbers) > int(config["drawnNumbers"]):
            raise ValueError(f"指定号码最多填写 {config['drawnNumbers']} 个")
        top_n = 1
        params = {**params, "numbers": numbers, "condition": "auto"}
    elif strategy == "shape_top_n":
        condition = str(params.get("condition") or params.get("condition_key") or "").strip()
        condition_keys = game_condition_keys(config)
        if not condition or condition not in condition_keys:
            raise ValueError("形态组合遗漏回测需要选择一个形态")
        groups = condition_shape_groups(config, condition)
        if not groups:
            raise ValueError("该形态组合数量过大或不可用，无法回测")
        top_n = min(top_n, len(groups))
        params = {**params, "condition": condition}
    else:
        if strategy == "condition":
            legacy_condition = str(
                params.get("condition") or params.get("condition_key") or "auto"
            ).strip()
            strategy = "condition_top_n" if legacy_condition in {"", "auto"} else "condition_fixed"
            params = {**params, "condition": legacy_condition or "auto"}
        condition = str(
            params.get("condition") or params.get("condition_key") or "auto"
        ).strip()
        condition_keys = game_condition_keys(config)
        if strategy == "condition_top_n":
            condition = "auto"
        if not condition:
            condition = "auto"
        if strategy == "condition_fixed" and condition == "auto":
            raise ValueError("形态事件固定回测需要选择一个条件")
        if condition != "auto" and condition not in condition_keys:
            raise ValueError("未知连号条件")
        top_n = 1 if strategy == "condition_fixed" else min(top_n, len(condition_keys))
        params = {**params, "condition": condition}

    return {
        "game": config["key"],
        "strategy": strategy,
        "params": {
            "top_n": top_n,
            "miss_threshold": miss_threshold,
            "condition": str(params.get("condition") or "auto"),
            "numbers": params.get("numbers") if strategy == "exact_numbers" else [],
        },
        "window": {"train": train_window, "test": test_window},
        "stake": round(stake, 4),
        "odds": round(odds, 4),
    }


def backtest_cache_key(request: dict[str, Any]) -> str:
    config = LOTTERY_GAMES[game_key_from_value(request.get("game"))]
    return json.dumps(
        {"history": history_cache_identity(game_history_path(config)), "request": request},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def prune_backtest_cache(now: float | None = None) -> None:
    now = time.monotonic() if now is None else now
    expired = [
        key
        for key, item in BACKTEST_CACHE.items()
        if now - float(item.get("createdMonotonic", 0)) > BACKTEST_CACHE_TTL_SECONDS
    ]
    for key in expired:
        BACKTEST_CACHE.pop(key, None)


def set_backtest_status(job_id: str | None = None, **updates: Any) -> None:
    with BACKTEST_STATUS_LOCK:
        current_job = str(BACKTEST_STATUS.get("jobId") or "")
        if job_id and current_job and current_job != job_id:
            return
        BACKTEST_STATUS.update(updates)
        BACKTEST_STATUS["generatedAt"] = utc_now_iso()


def backtest_status_payload() -> dict[str, Any]:
    with BACKTEST_STATUS_LOCK:
        return dict(BACKTEST_STATUS)


def group_train_stats(
    hit_positions: list[int],
    train_start: int,
    train_end: int,
) -> dict[str, Any]:
    train_size = max(0, train_end - train_start)
    lo = bisect_left(hit_positions, train_start)
    hi = bisect_left(hit_positions, train_end)
    hits = hi - lo
    if train_size <= 0:
        return {"currentMiss": 0, "maxMiss": 0, "hits": 0, "hitRate": 0}
    if hits <= 0:
        return {
            "currentMiss": train_size,
            "maxMiss": train_size,
            "hits": 0,
            "hitRate": 0,
        }

    first_hit = hit_positions[lo]
    previous_hit = first_hit
    max_miss = first_hit - train_start
    for index in range(lo + 1, hi):
        current_hit = hit_positions[index]
        max_miss = max(max_miss, current_hit - previous_hit - 1)
        previous_hit = current_hit
    current_miss = train_end - previous_hit - 1
    max_miss = max(max_miss, current_miss)
    return {
        "currentMiss": current_miss,
        "maxMiss": max_miss,
        "hits": hits,
        "hitRate": hits / train_size,
    }


def rank_backtest_groups(
    groups: tuple[Any, ...],
    hit_positions_by_group: dict[Any, list[int]],
    train_start: int,
    train_end: int,
    top_n: int,
    miss_threshold: int,
) -> list[dict[str, Any]]:
    candidates = []
    for group in groups:
        stats = group_train_stats(hit_positions_by_group[group], train_start, train_end)
        if stats["currentMiss"] < miss_threshold:
            continue
        candidates.append(
            {
                "group": group,
                **stats,
            }
        )
    candidates.sort(
        key=lambda item: (
            -item["currentMiss"],
            -item["maxMiss"],
            -item["hitRate"],
            item["group"],
        )
    )
    return candidates[:top_n]


def build_run_hit_index(
    draw_sets: list[set[int]],
    groups: tuple[tuple[int, ...], ...],
) -> dict[tuple[int, ...], list[int]]:
    group_length = len(groups[0]) if groups else 0
    total_numbers = max((group[-1] for group in groups), default=0)
    hit_positions_by_group = {group: [] for group in groups}
    for draw_index, draw_set in enumerate(draw_sets):
        for group in find_run_windows(draw_set, group_length, total_numbers):
            if group in hit_positions_by_group:
                hit_positions_by_group[group].append(draw_index)
    return hit_positions_by_group


def build_exact_group_hit_index(
    draw_sets: list[set[int]],
    groups: tuple[tuple[int, ...], ...],
) -> dict[tuple[int, ...], list[int]]:
    hit_positions_by_group = {group: [] for group in groups}
    for draw_index, draw_set in enumerate(draw_sets):
        for group in groups:
            if all(number in draw_set for number in group):
                hit_positions_by_group[group].append(draw_index)
    return hit_positions_by_group


def run_condition_flags_for(draw_set: set[int], total_numbers: int = 80) -> dict[str, bool]:
    pair_windows = find_run_windows(draw_set, 2, total_numbers)
    triple_windows = find_run_windows(draw_set, 3, total_numbers)
    quad_windows = find_run_windows(draw_set, 4, total_numbers)
    five_windows = find_run_windows(draw_set, 5, total_numbers)
    six_windows = find_run_windows(draw_set, 6, total_numbers)
    pair_set_count = max_disjoint_count(pair_windows)
    triple_set_count = max_disjoint_count(triple_windows)
    return {
        "pair": bool(pair_windows),
        "triple": bool(triple_windows),
        "quad": bool(quad_windows),
        "hasPair": bool(pair_windows),
        "hasDoublePair": pair_set_count >= 2,
        "hasTriplePairSet": pair_set_count >= 3,
        "hasTriple": bool(triple_windows),
        "hasQuadPairSet": pair_set_count >= 4,
        "hasFivePairSet": pair_set_count >= 5,
        "hasPairTriple": has_disjoint_groups(pair_windows, triple_windows),
        "hasDoubleTriple": triple_set_count >= 2,
        "hasTripleDoublePair": has_triple_with_pair_count(
            triple_windows, pair_windows, 2
        ),
        "hasQuad": bool(quad_windows),
        "hasQuadPair": has_disjoint_groups(pair_windows, quad_windows),
        "hasFive": bool(five_windows),
        "hasSix": bool(six_windows),
    }


def build_condition_hit_index(
    draw_sets: list[set[int]],
    total_numbers: int = 80,
    condition_keys: tuple[str, ...] = BACKTEST_CONDITION_KEYS,
) -> tuple[dict[str, list[int]], list[dict[str, bool]]]:
    hit_positions_by_key = {key: [] for key in condition_keys}
    flags_by_draw: list[dict[str, bool]] = []
    for draw_index, draw_set in enumerate(draw_sets):
        flags = run_condition_flags_for(draw_set, total_numbers)
        flags_by_draw.append(flags)
        for key in condition_keys:
            if flags.get(key, False):
                hit_positions_by_key[key].append(draw_index)
    return hit_positions_by_key, flags_by_draw


def windows_are_disjoint(windows: tuple[tuple[int, ...], ...]) -> bool:
    used: set[int] = set()
    for window in windows:
        current = set(window)
        if used & current:
            return False
        used.update(current)
    return True


def limited_disjoint_combinations(
    windows: tuple[tuple[int, ...], ...],
    count: int,
    limit: int = BACKTEST_SHAPE_GROUP_LIMIT,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    groups: list[tuple[tuple[int, ...], ...]] = []
    for combo in combinations(windows, count):
        if not windows_are_disjoint(combo):
            continue
        groups.append(tuple(combo))
        if len(groups) >= limit:
            break
    return tuple(groups)


def condition_shape_groups(
    config: dict[str, Any],
    condition: str,
    limit: int = BACKTEST_SHAPE_GROUP_LIMIT,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    pairs = pair_groups(config)
    triples = triple_groups(config)
    quads = quad_groups(config)
    fives = run_groups(config, 5)
    sixes = run_groups(config, 6)

    if condition == "hasPair":
        return tuple((group,) for group in pairs[:limit])
    if condition == "hasTriple":
        return tuple((group,) for group in triples[:limit])
    if condition == "hasQuad":
        return tuple((group,) for group in quads[:limit])
    if condition == "hasFive":
        return tuple((group,) for group in fives[:limit])
    if condition == "hasSix":
        return tuple((group,) for group in sixes[:limit])
    if condition == "hasDoublePair":
        return limited_disjoint_combinations(pairs, 2, limit)
    if condition == "hasTriplePairSet":
        return limited_disjoint_combinations(pairs, 3, limit)
    if condition == "hasQuadPairSet":
        return limited_disjoint_combinations(pairs, 4, limit)
    if condition == "hasFivePairSet":
        return limited_disjoint_combinations(pairs, 5, limit)
    if condition == "hasDoubleTriple":
        return limited_disjoint_combinations(triples, 2, limit)

    groups: list[tuple[tuple[int, ...], ...]] = []
    if condition == "hasPairTriple":
        for pair in pairs:
            for triple in triples:
                combo = (pair, triple)
                if windows_are_disjoint(combo):
                    groups.append(combo)
                    if len(groups) >= limit:
                        return tuple(groups)
    elif condition == "hasQuadPair":
        for quad in quads:
            for pair in pairs:
                combo = (quad, pair)
                if windows_are_disjoint(combo):
                    groups.append(combo)
                    if len(groups) >= limit:
                        return tuple(groups)
    elif condition == "hasTripleDoublePair":
        pair_sets = limited_disjoint_combinations(pairs, 2, limit)
        for triple in triples:
            for pair_set in pair_sets:
                combo = (triple, *pair_set)
                if windows_are_disjoint(combo):
                    groups.append(combo)
                    if len(groups) >= limit:
                        return tuple(groups)
    return tuple(groups)


def shape_group_label(group: Any) -> str:
    if not isinstance(group, tuple):
        return str(group)
    parts = []
    for window in group:
        if isinstance(window, tuple):
            parts.append("-".join(str(number) for number in window))
        else:
            parts.append(str(window))
    return " + ".join(parts)


def shape_group_hit(group: tuple[tuple[int, ...], ...], draw_set: set[int]) -> bool:
    return all(all(number in draw_set for number in window) for window in group)


def build_shape_hit_index(
    draw_sets: list[set[int]],
    groups: tuple[tuple[tuple[int, ...], ...], ...],
) -> dict[tuple[tuple[int, ...], ...], list[int]]:
    hit_positions_by_group = {group: [] for group in groups}
    for draw_index, draw_set in enumerate(draw_sets):
        for group in groups:
            if shape_group_hit(group, draw_set):
                hit_positions_by_group[group].append(draw_index)
    return hit_positions_by_group


def backtest_strategy_label(request: dict[str, Any]) -> str:
    strategy = request["strategy"]
    if strategy == "pair_top_n":
        return "两连号遗漏 Top N"
    if strategy == "triple_top_n":
        return "三连号遗漏 Top N"
    if strategy == "quad_top_n":
        return "四连号遗漏 Top N"
    if strategy == "exact_numbers":
        numbers = request["params"].get("numbers") or []
        label = " ".join(str(number) for number in numbers)
        return f"指定号码组 {label}".strip()
    if strategy == "condition_fixed":
        condition = request["params"].get("condition") or "auto"
        return f"形态事件：{BET_TYPES.get(condition, {}).get('label', condition)}"
    if strategy == "condition_top_n":
        return "形态事件遗漏 Top N"
    if strategy == "shape_top_n":
        condition = request["params"].get("condition") or "auto"
        return f"{BET_TYPES.get(condition, {}).get('label', condition)}遗漏 Top N"
    return "回测结果"


def backtest_strategy_note(strategy: str) -> str:
    if strategy == "shape_top_n":
        return "形态组合遗漏按具体形态组合结算，例如三双两连会拆成三组不重叠两连的具体组合。"
    if strategy in {"condition_fixed", "condition_top_n"}:
        return "形态事件回测只判断开奖是否出现该形态，不等同于指定号码组合投注。"
    if strategy == "exact_numbers":
        return "指定号码组回测按填写号码全中结算。"
    return "连号组合回测按具体号码窗口结算。"


def run_backtest(
    request: dict[str, Any],
    job_id: str,
) -> dict[str, Any]:
    config = LOTTERY_GAMES[game_key_from_value(request.get("game"))]
    set_backtest_status(job_id, progress=0.02, message="读取历史数据")
    with DATA_LOCK:
        all_rows = load_history_rows(game_history_path(config), config)
    rows = valid_draw_rows(all_rows, config)
    chronological_rows = list(reversed(rows))
    train_window = int(request["window"]["train"])
    requested_test_window = int(request["window"]["test"])
    gap_report = gap_audit(all_rows, config)
    missing_intervals = int(gap_report.get("missingIntervals") or 0)
    gap_warning_threshold = max(1, math.ceil(train_window * 0.05))
    gap_warning = None
    if (
        gap_report.get("authoritativeMissingCheck")
        and gap_report.get("hasGaps")
        and missing_intervals > gap_warning_threshold
    ):
        gap_warning = {
            "message": (
                f"固定间隔扫描发现 {missing_intervals} 个时间间隔异常，"
                f"超过训练窗口 5% 阈值 {gap_warning_threshold}。这不等同于本地缺数据，"
                "可能包含停开、官方跳期或上游源未提供的期次；回测按实际已入库记录运行。"
            ),
            "missingIntervals": missing_intervals,
            "thresholdIntervals": gap_warning_threshold,
            "samples": gap_report.get("samples", []),
        }
    if len(chronological_rows) <= train_window:
        raise ValueError(
            f"历史数据不足：至少需要训练窗口 {train_window} 期以上，当前 {len(chronological_rows)} 期"
        )

    test_window = min(requested_test_window, len(chronological_rows) - train_window)
    start_index = len(chronological_rows) - train_window - test_window
    working_rows = chronological_rows[start_index:]
    draw_sets = [set(row["numbers"]) for row in working_rows]
    test_start = train_window
    test_end = train_window + test_window
    top_n = int(request["params"]["top_n"])
    miss_threshold = int(request["params"]["miss_threshold"])
    strategy = request["strategy"]
    stake = float(request["stake"])
    odds = float(request["odds"])

    set_backtest_status(job_id, progress=0.05, message="建立命中索引")
    theoretical_fixed_hit_rate: float | None = None
    flags_by_draw: list[dict[str, bool]] = []
    if strategy == "pair_top_n":
        groups = pair_groups(config)
        hit_positions_by_group = build_run_hit_index(draw_sets, groups)
        theoretical_fixed_hit_rate = hit_probability_for(config, 2)
    elif strategy == "triple_top_n":
        groups = triple_groups(config)
        hit_positions_by_group = build_run_hit_index(draw_sets, groups)
        theoretical_fixed_hit_rate = hit_probability_for(config, 3)
    elif strategy == "quad_top_n":
        groups = quad_groups(config)
        hit_positions_by_group = build_run_hit_index(draw_sets, groups)
        theoretical_fixed_hit_rate = hit_probability_for(config, 4)
    elif strategy == "exact_numbers":
        exact_group = tuple(int(number) for number in request["params"].get("numbers") or [])
        groups = (exact_group,)
        hit_positions_by_group = build_exact_group_hit_index(draw_sets, groups)
        theoretical_fixed_hit_rate = hit_probability_for(config, len(exact_group))
    elif strategy == "shape_top_n":
        condition = request["params"].get("condition") or "auto"
        groups = condition_shape_groups(config, str(condition))
        if not groups:
            raise ValueError("该形态组合数量过大或不可用，无法回测")
        hit_positions_by_group = build_shape_hit_index(draw_sets, groups)
        theoretical_fixed_hit_rate = None
    else:
        condition = request["params"].get("condition") or "auto"
        condition_keys = game_condition_keys(config)
        groups = (
            condition_keys
            if strategy == "condition_top_n"
            else (condition,)
        )
        hit_positions_by_group, flags_by_draw = build_condition_hit_index(
            draw_sets,
            int(config["totalNumbers"]),
            groups,
        )
        theoretical_fixed_hit_rate = None

    total_bets = 0
    won = 0
    cumulative_profit = 0.0
    cumulative_stake = 0.0
    current_loss_streak = 0
    max_loss_streak = 0
    theoretical_hit_sum = 0.0
    roi_curve = []
    curve_step = max(1, min(BACKTEST_CURVE_STEP, test_window // 50))
    selection_samples = []
    last_progress_update = 0.0

    for offset, draw_index in enumerate(range(test_start, test_end), start=1):
        train_start = draw_index - train_window
        train_end = draw_index
        selections = rank_backtest_groups(
            groups,
            hit_positions_by_group,
            train_start,
            train_end,
            top_n,
            miss_threshold,
        )
        draw_set = draw_sets[draw_index]
        draw_row = working_rows[draw_index]

        for selection in selections:
            group = selection["group"]
            if strategy in {"condition_fixed", "condition_top_n"}:
                is_hit = flags_by_draw[draw_index].get(str(group), False)
                theoretical_hit = selection["hitRate"]
                label = BET_TYPES.get(str(group), {}).get("label", str(group))
            elif strategy == "shape_top_n":
                is_hit = shape_group_hit(group, draw_set)
                theoretical_hit = selection["hitRate"]
                label = shape_group_label(group)
            else:
                is_hit = all(number in draw_set for number in group)
                theoretical_hit = theoretical_fixed_hit_rate or 0
                label = "-".join(str(number) for number in group)

            total_bets += 1
            cumulative_stake += stake
            theoretical_hit_sum += theoretical_hit
            if is_hit:
                won += 1
                cumulative_profit += stake * odds - stake
                current_loss_streak = 0
            else:
                cumulative_profit -= stake
                current_loss_streak += 1
                max_loss_streak = max(max_loss_streak, current_loss_streak)

            if len(selection_samples) < 20:
                selection_samples.append(
                    {
                        "drawIndex": offset,
                        "drawTimeUtc": draw_row.get("drawTimeUtc", ""),
                        "label": label,
                        "won": is_hit,
                        "currentMiss": selection["currentMiss"],
                        "maxMiss": selection["maxMiss"],
                        "trainHitRate": selection["hitRate"],
                    }
                )

        if offset % curve_step == 0 or offset == test_window:
            roi_curve.append(
                {
                    "drawIndex": offset,
                    "bets": total_bets,
                    "cumulativeProfit": round(cumulative_profit, 4),
                    "roi": cumulative_profit / cumulative_stake if cumulative_stake else 0,
                }
            )

        now = time.monotonic()
        if now - last_progress_update > 0.35 or offset == test_window:
            progress = 0.05 + 0.9 * (offset / test_window)
            set_backtest_status(
                job_id,
                progress=round(progress, 4),
                message=f"回测中：{offset}/{test_window} 期",
            )
            last_progress_update = now

    hit_rate = won / total_bets if total_bets else 0
    theoretical_hit_rate = theoretical_hit_sum / total_bets if total_bets else 0
    hit_rate_ci = wilson_interval(won, total_bets)
    roi = cumulative_profit / cumulative_stake if cumulative_stake else 0
    theoretical_roi = theoretical_hit_rate * odds - 1 if total_bets else 0
    result = {
        "ok": True,
        "status": "complete",
        "game": game_public_config(config),
        "strategy": strategy,
        "strategyLabel": backtest_strategy_label(request),
        "strategyNote": backtest_strategy_note(strategy),
        "params": request["params"],
        "trainWindow": train_window,
        "testWindow": test_window,
        "requestedTestWindow": requested_test_window,
        "maxSelectionsPerDraw": top_n,
        "stake": stake,
        "odds": odds,
        "totalBets": total_bets,
        "won": won,
        "lost": total_bets - won,
        "hitRate": hit_rate,
        "hitRateCi": list(hit_rate_ci),
        "hitRateVsTheory": hit_rate - theoretical_hit_rate,
        "theoreticalHitRate": theoretical_hit_rate,
        "roi": roi,
        "theoreticalRoi": theoretical_roi,
        "excessRoi": roi - theoretical_roi if total_bets else 0,
        "profit": round(cumulative_profit, 4),
        "stakeTotal": round(cumulative_stake, 4),
        "maxLossStreak": max_loss_streak,
        "roiCurve": roi_curve,
        "roiCurveStep": curve_step,
        "selectionSamples": selection_samples,
        "gapAudit": gap_report,
        "gapWarning": gap_warning,
        "historyWindow": {
            "startDrawTimeUtc": working_rows[0].get("drawTimeUtc", "") if working_rows else "",
            "testStartDrawTimeUtc": working_rows[test_start].get("drawTimeUtc", "")
            if test_window
            else "",
            "endDrawTimeUtc": working_rows[-1].get("drawTimeUtc", "") if working_rows else "",
            "rows": len(working_rows),
        },
        "cacheHit": False,
        "generatedAt": utc_now_iso(),
    }
    return result


def backtest_worker(job_id: str, cache_key: str, request: dict[str, Any]) -> None:
    started = time.monotonic()
    try:
        result = run_backtest(request, job_id)
        result["jobId"] = job_id
        result["elapsedMs"] = round((time.monotonic() - started) * 1000)
        with BACKTEST_CACHE_LOCK:
            prune_backtest_cache()
            BACKTEST_CACHE[cache_key] = {
                "createdMonotonic": time.monotonic(),
                "result": result,
            }
        set_backtest_status(
            job_id,
            ok=True,
            status="complete",
            progress=1,
            message="回测完成",
            result=result,
        )
    except ValueError as exc:
        set_backtest_status(
            job_id,
            ok=False,
            status="failed",
            progress=1,
            message=str(exc),
            error=str(exc),
            errorType="validation",
        )
    except Exception as exc:
        print(traceback.format_exc(), flush=True)
        set_backtest_status(
            job_id,
            ok=False,
            status="failed",
            progress=1,
            message="回测失败",
            error=str(exc),
            errorType=type(exc).__name__,
        )


def start_backtest(payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    request = normalize_backtest_request(payload)
    cache_key = backtest_cache_key(request)
    now = time.monotonic()
    with BACKTEST_CACHE_LOCK:
        prune_backtest_cache(now)
        cached = BACKTEST_CACHE.get(cache_key)
        if cached is not None:
            result = dict(cached["result"])
            result["cacheHit"] = True
            return result, 200

    with BACKTEST_STATUS_LOCK:
        current_status = str(BACKTEST_STATUS.get("status") or "idle")
        current_cache_key = str(BACKTEST_STATUS.get("cacheKey") or "")
        if current_status == "running":
            if current_cache_key == cache_key:
                return dict(BACKTEST_STATUS), 202
            return {
                "ok": False,
                "status": "running",
                "error": "已有回测任务正在运行，请完成后再提交新的回测",
                "current": dict(BACKTEST_STATUS),
            }, 409
        job_id = uuid.uuid4().hex
        BACKTEST_STATUS.clear()
        BACKTEST_STATUS.update(
            {
                "ok": True,
                "status": "running",
                "jobId": job_id,
                "cacheKey": cache_key,
                "request": request,
                "progress": 0,
                "message": "回测任务已启动",
                "generatedAt": utc_now_iso(),
            }
        )

    worker = threading.Thread(
        target=backtest_worker,
        args=(job_id, cache_key, request),
        daemon=True,
    )
    worker.start()
    return backtest_status_payload(), 202


def normalize_int_list(
    value: Any,
    defaults: tuple[int, ...],
    *,
    min_value: int,
    max_value: int,
) -> list[int]:
    raw_items: list[Any]
    if isinstance(value, str):
        raw_items = [item for item in re.split(r"[\s,，]+", value) if item]
    elif isinstance(value, list):
        raw_items = value
    elif value is None:
        raw_items = list(defaults)
    else:
        raw_items = [value]
    numbers: list[int] = []
    for item in raw_items:
        number = parse_int(item, min_value)
        if number < min_value or number > max_value:
            continue
        if number not in numbers:
            numbers.append(number)
    return numbers or list(defaults)


def normalize_backtest_scan_request(payload: dict[str, Any]) -> dict[str, Any]:
    config = game_from_options(payload)
    ensure_backtest_supported(config)
    params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
    window = payload.get("window") if isinstance(payload.get("window"), dict) else {}
    scan = payload.get("scan") if isinstance(payload.get("scan"), dict) else {}

    train_window = max(
        100,
        min(parse_int(window.get("train"), 10000), BACKTEST_MAX_TRAIN_WINDOW),
    )
    test_window = max(
        10,
        min(parse_int(window.get("test"), 1000), BACKTEST_MAX_TEST_WINDOW),
    )
    stake = parse_float(payload.get("stake"), 1.0)
    odds = parse_float(payload.get("odds"), 60.0)
    if stake <= 0:
        raise ValueError("每注投入必须大于 0")
    if odds <= 1:
        raise ValueError("赔率必须大于 1")

    top_ns = normalize_int_list(
        scan.get("top_ns") or scan.get("topNs"),
        BACKTEST_SCAN_DEFAULT_TOP_NS,
        min_value=1,
        max_value=20,
    )
    base_miss = max(0, parse_int(params.get("miss_threshold"), 0))
    miss_thresholds = normalize_int_list(
        scan.get("miss_thresholds") or scan.get("missThresholds"),
        BACKTEST_SCAN_DEFAULT_MISS_THRESHOLDS,
        min_value=0,
        max_value=train_window,
    )
    if base_miss not in miss_thresholds:
        miss_thresholds.append(base_miss)
        miss_thresholds.sort()

    return {
        "game": config["key"],
        "window": {"train": train_window, "test": test_window},
        "stake": round(stake, 4),
        "odds": round(odds, 4),
        "scan": {
            "topNs": top_ns,
            "missThresholds": miss_thresholds,
            "maxResults": max(1, min(parse_int(scan.get("max_results") or scan.get("maxResults"), 50), BACKTEST_SCAN_MAX_RESULTS)),
            "minBets": max(0, parse_int(scan.get("min_bets") or scan.get("minBets"), 0)),
            "exactRunLengths": [
                length
                for length in normalize_int_list(
                    scan.get("exact_run_lengths") or scan.get("exactRunLengths"),
                    BACKTEST_SCAN_EXACT_RUN_LENGTHS,
                    min_value=2,
                    max_value=6,
                )
                if length <= int(config["drawnNumbers"])
            ],
        },
    }


def backtest_scan_cache_key(request: dict[str, Any]) -> str:
    config = LOTTERY_GAMES[game_key_from_value(request.get("game"))]
    return json.dumps(
        {"history": history_cache_identity(game_history_path(config)), "request": request},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def prune_backtest_scan_cache(now: float | None = None) -> None:
    now = time.monotonic() if now is None else now
    expired = [
        key
        for key, item in BACKTEST_SCAN_CACHE.items()
        if now - float(item.get("createdMonotonic", 0)) > BACKTEST_SCAN_CACHE_TTL_SECONDS
    ]
    for key in expired:
        BACKTEST_SCAN_CACHE.pop(key, None)


def set_backtest_scan_status(job_id: str | None = None, **updates: Any) -> None:
    with BACKTEST_SCAN_STATUS_LOCK:
        current_job = str(BACKTEST_SCAN_STATUS.get("jobId") or "")
        if job_id and current_job and current_job != job_id:
            return
        BACKTEST_SCAN_STATUS.update(updates)
        BACKTEST_SCAN_STATUS["generatedAt"] = utc_now_iso()


def backtest_scan_status_payload() -> dict[str, Any]:
    with BACKTEST_SCAN_STATUS_LOCK:
        return dict(BACKTEST_SCAN_STATUS)


def prepare_backtest_context(
    config: dict[str, Any],
    train_window: int,
    requested_test_window: int,
) -> dict[str, Any]:
    with DATA_LOCK:
        all_rows = load_history_rows(game_history_path(config), config)
    rows = valid_draw_rows(all_rows, config)
    chronological_rows = list(reversed(rows))
    if len(chronological_rows) <= train_window:
        raise ValueError(
            f"历史数据不足：至少需要训练窗口 {train_window} 期以上，当前 {len(chronological_rows)} 期"
        )
    test_window = min(requested_test_window, len(chronological_rows) - train_window)
    start_index = len(chronological_rows) - train_window - test_window
    working_rows = chronological_rows[start_index:]
    return {
        "allRows": all_rows,
        "workingRows": working_rows,
        "drawSets": [set(row["numbers"]) for row in working_rows],
        "trainWindow": train_window,
        "testWindow": test_window,
        "requestedTestWindow": requested_test_window,
        "testStart": train_window,
        "testEnd": train_window + test_window,
    }


def evaluate_backtest_candidate(
    *,
    config: dict[str, Any],
    request: dict[str, Any],
    context: dict[str, Any],
    groups: tuple[Any, ...],
    hit_positions_by_group: dict[Any, list[int]],
    flags_by_draw: list[dict[str, bool]] | None = None,
    scan_category: str = "",
    scan_kind: str = "",
) -> dict[str, Any]:
    train_window = int(context["trainWindow"])
    test_window = int(context["testWindow"])
    test_start = int(context["testStart"])
    test_end = int(context["testEnd"])
    working_rows = context["workingRows"]
    draw_sets = context["drawSets"]
    strategy = request["strategy"]
    top_n = int(request["params"]["top_n"])
    miss_threshold = int(request["params"]["miss_threshold"])
    stake = float(request["stake"])
    odds = float(request["odds"])
    flags_by_draw = flags_by_draw or []

    theoretical_fixed_hit_rate: float | None = None
    if strategy in {"pair_top_n", "triple_top_n", "quad_top_n", "exact_numbers"}:
        if strategy == "pair_top_n":
            theoretical_fixed_hit_rate = hit_probability_for(config, 2)
        elif strategy == "triple_top_n":
            theoretical_fixed_hit_rate = hit_probability_for(config, 3)
        elif strategy == "quad_top_n":
            theoretical_fixed_hit_rate = hit_probability_for(config, 4)
        else:
            theoretical_fixed_hit_rate = hit_probability_for(
                config,
                len(request["params"].get("numbers") or []),
            )

    total_bets = 0
    won = 0
    cumulative_profit = 0.0
    cumulative_stake = 0.0
    current_loss_streak = 0
    max_loss_streak = 0
    theoretical_hit_sum = 0.0

    for draw_index in range(test_start, test_end):
        train_start = draw_index - train_window
        train_end = draw_index
        selections = rank_backtest_groups(
            groups,
            hit_positions_by_group,
            train_start,
            train_end,
            top_n,
            miss_threshold,
        )
        draw_set = draw_sets[draw_index]

        for selection in selections:
            group = selection["group"]
            if strategy in {"condition_fixed", "condition_top_n"}:
                is_hit = flags_by_draw[draw_index].get(str(group), False)
                theoretical_hit = selection["hitRate"]
            elif strategy == "shape_top_n":
                is_hit = shape_group_hit(group, draw_set)
                theoretical_hit = selection["hitRate"]
            else:
                is_hit = all(number in draw_set for number in group)
                theoretical_hit = theoretical_fixed_hit_rate or 0

            total_bets += 1
            cumulative_stake += stake
            theoretical_hit_sum += theoretical_hit
            if is_hit:
                won += 1
                cumulative_profit += stake * odds - stake
                current_loss_streak = 0
            else:
                cumulative_profit -= stake
                current_loss_streak += 1
                max_loss_streak = max(max_loss_streak, current_loss_streak)

    hit_rate = won / total_bets if total_bets else 0
    theoretical_hit_rate = theoretical_hit_sum / total_bets if total_bets else 0
    hit_rate_ci = wilson_interval(won, total_bets)
    roi = cumulative_profit / cumulative_stake if cumulative_stake else 0
    theoretical_roi = theoretical_hit_rate * odds - 1 if total_bets else 0
    return {
        "game": game_public_config(config),
        "strategy": strategy,
        "strategyLabel": backtest_strategy_label(request),
        "strategyNote": backtest_strategy_note(strategy),
        "scanCategory": scan_category,
        "scanKind": scan_kind,
        "params": request["params"],
        "trainWindow": train_window,
        "testWindow": test_window,
        "requestedTestWindow": int(context["requestedTestWindow"]),
        "maxSelectionsPerDraw": top_n,
        "stake": stake,
        "odds": odds,
        "totalBets": total_bets,
        "won": won,
        "lost": total_bets - won,
        "hitRate": hit_rate,
        "hitRateCi": list(hit_rate_ci),
        "hitRateVsTheory": hit_rate - theoretical_hit_rate,
        "theoreticalHitRate": theoretical_hit_rate,
        "roi": roi,
        "theoreticalRoi": theoretical_roi,
        "excessRoi": roi - theoretical_roi if total_bets else 0,
        "profit": round(cumulative_profit, 4),
        "stakeTotal": round(cumulative_stake, 4),
        "maxLossStreak": max_loss_streak,
    }


def candidate_request(
    base_request: dict[str, Any],
    *,
    strategy: str,
    top_n: int,
    miss_threshold: int,
    condition: str = "auto",
    numbers: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "game": base_request["game"],
        "strategy": strategy,
        "params": {
            "top_n": top_n,
            "miss_threshold": miss_threshold,
            "condition": condition,
            "numbers": numbers or [],
        },
        "window": dict(base_request["window"]),
        "stake": base_request["stake"],
        "odds": base_request["odds"],
    }


def backtest_scan_rank_key(item: dict[str, Any]) -> tuple[float, float, float, int]:
    return (
        float(item.get("roi") or 0),
        float(item.get("profit") or 0),
        float(item.get("hitRate") or 0),
        int(item.get("totalBets") or 0),
    )


def backtest_scan_dedupe_key(item: dict[str, Any]) -> tuple[Any, ...]:
    params = item.get("params") if isinstance(item.get("params"), dict) else {}
    numbers = params.get("numbers") if isinstance(params, dict) else []
    if isinstance(numbers, list) and numbers:
        return ("numbers", tuple(int(number) for number in numbers))

    strategy = str(item.get("strategy") or "")
    condition = str(params.get("condition") or "")
    top_n = int(item.get("maxSelectionsPerDraw") or params.get("top_n") or 0)
    scan_kind = str(item.get("scanKind") or "")
    if strategy in {"pair_top_n", "triple_top_n", "quad_top_n"}:
        return (strategy, top_n)
    return (strategy, condition, top_n, scan_kind)


def dedupe_backtest_scan_results(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in items:
        key = backtest_scan_dedupe_key(item)
        current = best_by_key.get(key)
        if current is None or backtest_scan_rank_key(item) > backtest_scan_rank_key(current):
            best_by_key[key] = item
    return list(best_by_key.values())


def run_backtest_scan(request: dict[str, Any], job_id: str) -> dict[str, Any]:
    config = LOTTERY_GAMES[game_key_from_value(request.get("game"))]
    train_window = int(request["window"]["train"])
    requested_test_window = int(request["window"]["test"])
    scan_params = request["scan"]
    top_ns = list(scan_params["topNs"])
    miss_thresholds = list(scan_params["missThresholds"])
    exact_run_lengths = list(scan_params["exactRunLengths"])

    set_backtest_scan_status(job_id, progress=0.02, message="读取历史数据")
    context = prepare_backtest_context(config, train_window, requested_test_window)
    draw_sets = context["drawSets"]
    test_window = int(context["testWindow"])
    requested_min_bets = int(scan_params["minBets"])
    min_bets = requested_min_bets if requested_min_bets > 0 else max(10, min(100, test_window // 5))
    max_results = int(scan_params["maxResults"])
    condition_keys = game_condition_keys(config)

    run_specs: list[tuple[str, str, tuple[tuple[int, ...], ...]]] = []
    if 2 in exact_run_lengths:
        run_specs.append(("pair_top_n", "二连", pair_groups(config)))
    if 3 in exact_run_lengths:
        run_specs.append(("triple_top_n", "三连", triple_groups(config)))
    if 4 in exact_run_lengths:
        run_specs.append(("quad_top_n", "四连", quad_groups(config)))
    for length in exact_run_lengths:
        if length not in {2, 3, 4}:
            run_specs.append((f"exact_run_{length}", f"{length}连", run_groups(config, length)))

    shape_specs: list[tuple[str, str, tuple[tuple[tuple[int, ...], ...], ...]]] = []
    for condition in condition_keys:
        if BACKTEST_SIMPLE_SHAPE_RUN_LENGTHS.get(condition) in exact_run_lengths:
            continue
        groups = condition_shape_groups(config, condition)
        if groups:
            shape_specs.append(
                (
                    condition,
                    BET_TYPES.get(condition, {}).get("label", condition),
                    groups,
                )
            )

    skipped_fixed_shape_scans = [
        {
            "condition": condition,
            "label": label,
            "groups": len(groups),
            "candidates": len(groups) * len(miss_thresholds),
            "limit": BACKTEST_SHAPE_FIXED_SCAN_LIMIT,
        }
        for condition, label, groups in shape_specs
        if len(groups) > BACKTEST_SHAPE_FIXED_SCAN_LIMIT
    ]
    total_candidates = (
        sum(len(groups) for _strategy, _label, groups in run_specs) * len(miss_thresholds)
        + sum(
            len(top_ns) * len(miss_thresholds)
            for strategy, _label, _groups in run_specs
            if strategy in {"pair_top_n", "triple_top_n", "quad_top_n"}
        )
        + sum(len(top_ns) * len(miss_thresholds) for _condition, _label, _groups in shape_specs)
        + sum(
            len(groups) * len(miss_thresholds)
            for _condition, _label, groups in shape_specs
            if len(groups) <= BACKTEST_SHAPE_FIXED_SCAN_LIMIT
        )
    )
    total_candidates = max(1, total_candidates)
    completed = 0
    results: list[dict[str, Any]] = []

    def add_result(result: dict[str, Any]) -> None:
        nonlocal completed
        completed += 1
        result.pop("game", None)
        result["rankEligible"] = int(result.get("totalBets") or 0) >= min_bets
        results.append(result)
        if completed % 25 == 0 or completed == total_candidates:
            set_backtest_scan_status(
                job_id,
                progress=round(0.05 + 0.9 * min(completed / total_candidates, 1), 4),
                message=f"自动扫描中：{completed}/{total_candidates}",
            )

    set_backtest_scan_status(job_id, progress=0.05, message="建立命中索引")
    run_indexes: dict[str, dict[tuple[int, ...], list[int]]] = {}
    for strategy, _label, groups in run_specs:
        index_key = strategy if strategy in {"pair_top_n", "triple_top_n", "quad_top_n"} else _label
        run_indexes[index_key] = build_run_hit_index(draw_sets, groups)

    for strategy, label, groups in run_specs:
        index_key = strategy if strategy in {"pair_top_n", "triple_top_n", "quad_top_n"} else label
        hit_index = run_indexes[index_key]
        if strategy in {"pair_top_n", "triple_top_n", "quad_top_n"}:
            for miss_threshold in miss_thresholds:
                for top_n in top_ns:
                    req = candidate_request(
                        request,
                        strategy=strategy,
                        top_n=min(top_n, len(groups)),
                        miss_threshold=miss_threshold,
                    )
                    add_result(
                        evaluate_backtest_candidate(
                            config=config,
                            request=req,
                            context=context,
                            groups=groups,
                            hit_positions_by_group=hit_index,
                            scan_category="动态连号遗漏",
                            scan_kind=label,
                        )
                    )
        for group in groups:
            for miss_threshold in miss_thresholds:
                req = candidate_request(
                    request,
                    strategy="exact_numbers",
                    top_n=1,
                    miss_threshold=miss_threshold,
                    numbers=list(group),
                )
                add_result(
                    evaluate_backtest_candidate(
                        config=config,
                        request=req,
                        context=context,
                        groups=(group,),
                        hit_positions_by_group=hit_index,
                        scan_category="固定连号组合",
                        scan_kind=label,
                    )
                )

    for condition, label, shape_groups in shape_specs:
        hit_index = build_shape_hit_index(draw_sets, shape_groups)
        for miss_threshold in miss_thresholds:
            for top_n in top_ns:
                req = candidate_request(
                    request,
                    strategy="shape_top_n",
                    top_n=min(top_n, len(shape_groups)),
                    miss_threshold=miss_threshold,
                    condition=condition,
                )
                add_result(
                    evaluate_backtest_candidate(
                        config=config,
                        request=req,
                        context=context,
                        groups=shape_groups,
                        hit_positions_by_group=hit_index,
                        scan_category="形态组合遗漏",
                        scan_kind=label,
                    )
                )
        if len(shape_groups) <= BACKTEST_SHAPE_FIXED_SCAN_LIMIT:
            for group in shape_groups:
                for miss_threshold in miss_thresholds:
                    req = candidate_request(
                        request,
                        strategy="shape_top_n",
                        top_n=1,
                        miss_threshold=miss_threshold,
                        condition=condition,
                    )
                    add_result(
                        evaluate_backtest_candidate(
                            config=config,
                            request=req,
                            context=context,
                            groups=(group,),
                            hit_positions_by_group=hit_index,
                            scan_category="固定形态组合",
                            scan_kind=f"{label}：{shape_group_label(group)}",
                        )
                    )

    raw_eligible = [item for item in results if item["rankEligible"]]
    eligible = dedupe_backtest_scan_results(raw_eligible)
    eligible.sort(
        key=backtest_scan_rank_key,
        reverse=True,
    )
    top_results = eligible[:max_results]
    for index, item in enumerate(top_results, start=1):
        item["rank"] = index

    working_rows = context["workingRows"]
    return {
        "ok": True,
        "status": "complete",
        "game": game_public_config(config),
        "request": request,
        "trainWindow": train_window,
        "testWindow": test_window,
        "requestedTestWindow": requested_test_window,
        "stake": request["stake"],
        "odds": request["odds"],
        "topNs": top_ns,
        "missThresholds": miss_thresholds,
        "minBets": min_bets,
        "maxResults": max_results,
        "candidateCount": len(results),
        "eligibleCount": len(eligible),
        "filteredLowBets": len(results) - len(raw_eligible),
        "dedupedRankResults": len(raw_eligible) - len(eligible),
        "skippedFixedShapeScans": skipped_fixed_shape_scans,
        "skippedFixedShapeGroups": sum(item["groups"] for item in skipped_fixed_shape_scans),
        "skippedFixedShapeCandidates": sum(item["candidates"] for item in skipped_fixed_shape_scans),
        "results": top_results,
        "best": top_results[0] if top_results else None,
        "notes": [
            "形态类已按具体组合遗漏结算，例如三双两连会拆成 1-2 + 5-6 + 9-10 这种组合。",
            "固定连号组合按具体号码窗口结算，例如 1-2-3-4。",
            "ROI 按当前输入赔率统一计算，换玩法赔率后需要重扫。",
            "自动扫描会在多组参数中挑选 ROI 靠前的结果，存在数据挖掘偏差，请结合样本量和理论命中率判断。",
        ],
        "historyWindow": {
            "startDrawTimeUtc": working_rows[0].get("drawTimeUtc", "") if working_rows else "",
            "testStartDrawTimeUtc": working_rows[int(context["testStart"])].get("drawTimeUtc", "")
            if test_window
            else "",
            "endDrawTimeUtc": working_rows[-1].get("drawTimeUtc", "") if working_rows else "",
            "rows": len(working_rows),
        },
        "cacheHit": False,
        "generatedAt": utc_now_iso(),
    }


def backtest_scan_worker(job_id: str, cache_key: str, request: dict[str, Any]) -> None:
    started = time.monotonic()
    try:
        result = run_backtest_scan(request, job_id)
        result["jobId"] = job_id
        result["elapsedMs"] = round((time.monotonic() - started) * 1000)
        with BACKTEST_SCAN_CACHE_LOCK:
            prune_backtest_scan_cache()
            BACKTEST_SCAN_CACHE[cache_key] = {
                "createdMonotonic": time.monotonic(),
                "result": result,
            }
        set_backtest_scan_status(
            job_id,
            ok=True,
            status="complete",
            progress=1,
            message="自动扫描完成",
            result=result,
        )
    except ValueError as exc:
        set_backtest_scan_status(
            job_id,
            ok=False,
            status="failed",
            progress=1,
            message=str(exc),
            error=str(exc),
            errorType="validation",
        )
    except Exception as exc:
        print(traceback.format_exc(), flush=True)
        set_backtest_scan_status(
            job_id,
            ok=False,
            status="failed",
            progress=1,
            message="自动扫描失败",
            error=str(exc),
            errorType=type(exc).__name__,
        )


def start_backtest_scan(payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    request = normalize_backtest_scan_request(payload)
    cache_key = backtest_scan_cache_key(request)
    now = time.monotonic()
    with BACKTEST_SCAN_CACHE_LOCK:
        prune_backtest_scan_cache(now)
        cached = BACKTEST_SCAN_CACHE.get(cache_key)
        if cached is not None:
            result = dict(cached["result"])
            result["cacheHit"] = True
            return result, 200

    with BACKTEST_SCAN_STATUS_LOCK:
        current_status = str(BACKTEST_SCAN_STATUS.get("status") or "idle")
        current_cache_key = str(BACKTEST_SCAN_STATUS.get("cacheKey") or "")
        if current_status == "running":
            if current_cache_key == cache_key:
                return dict(BACKTEST_SCAN_STATUS), 202
            return {
                "ok": False,
                "status": "running",
                "error": "已有自动扫描任务正在运行，请完成后再提交新的扫描",
                "current": dict(BACKTEST_SCAN_STATUS),
            }, 409
        job_id = uuid.uuid4().hex
        BACKTEST_SCAN_STATUS.clear()
        BACKTEST_SCAN_STATUS.update(
            {
                "ok": True,
                "status": "running",
                "jobId": job_id,
                "cacheKey": cache_key,
                "request": request,
                "progress": 0,
                "message": "自动扫描任务已启动",
                "generatedAt": utc_now_iso(),
            }
        )

    worker = threading.Thread(
        target=backtest_scan_worker,
        args=(job_id, cache_key, request),
        daemon=True,
    )
    worker.start()
    return backtest_scan_status_payload(), 202


def refresh_history(options: dict[str, Any]) -> dict[str, Any]:
    config = game_from_options(options)
    mode = str(options.get("mode") or "incremental")
    limit = parse_int(options.get("limit"), 1000)
    page_size = max(1, min(parse_int(options.get("pageSize"), DEFAULT_PAGE_SIZE), 100))
    lottery_id = str(config["lotteryId"])
    fetch_all = bool(options.get("all")) or mode == "full"
    out = game_history_path(config)
    sleep = parse_float(options.get("sleep"), DEFAULT_SYNC_SLEEP)
    timeout = parse_float(options.get("timeout"), 30)
    retries = parse_int(options.get("retries"), 2)
    retry_sleep = parse_float(options.get("retrySleep"), 1.0)
    skip_supplement = bool(options.get("skipSupplement"))

    with DATA_LOCK:
        existing_rows = load_history_rows(out, config)
        etipos_meta: dict[str, Any] = {}
        fetched_rows: list[dict[str, Any]] = []
        meta: dict[str, Any] = {}
        rows: list[dict[str, Any]] = list(existing_rows)
        sync_meta: dict[str, Any] = {
            "hitExisting": False,
            "pagesFetched": 0,
            "maxPages": 0,
            "catchUpMaxPages": 0,
            "catchUpTriggered": False,
            "stoppedByMaxPages": False,
            "stoppedByCatchUpLimit": False,
            "stoppedByTotalPage": False,
            "possibleGap": False,
            "oldestFetchedUtc": "",
            "newestExistingUtc": "",
            "stopReason": "",
        }

        if fetch_all:
            namespace = type(
                "FetchArgs",
                (),
                {
                    "lottery_id": lottery_id,
                    "out": out,
                    "limit": limit,
                    "all": True,
                    "page_size": page_size,
                    "sleep": sleep,
                    "timeout": timeout,
                    "retries": retries,
                    "retry_sleep": retry_sleep,
                    "expected_count": int(config["drawnNumbers"]),
                    "total_numbers": int(config["totalNumbers"]),
                },
            )()
            written_rows, meta = fetch_bc_keno_history.fetch_history_to_csv(namespace, out)
            rows = load_history_rows(out, config)
            written_rows = len(rows) if rows else written_rows
            if skip_supplement:
                etipos_rows = []
                etipos_meta = {"source": config.get("officialSupplement", ""), "status": "skipped", "newRows": 0}
            else:
                try:
                    etipos_rows, etipos_meta = fetch_official_supplement(config, rows)
                except Exception as exc:
                    etipos_rows = []
                    etipos_meta = {"source": config.get("officialSupplement", ""), "error": str(exc), "newRows": 0}
            if etipos_rows:
                rows = merge_history_rows(rows, etipos_rows)
                write_dashboard_rows(out, rows, config)
                written_rows = len(rows)
            new_rows = max(0, written_rows - len(existing_rows))
            oldest_row = meta.get("oldest_row") or {}
            newest_existing_ms = max(
                (parse_int(row.get("drawTimeMs"), 0) for row in existing_rows),
                default=0,
            )
            sync_meta.update(
                {
                    "pagesFetched": parse_int(meta.get("page"), 0),
                    "hitExisting": True,
                    "oldestFetchedUtc": oldest_row.get("draw_time_utc", ""),
                    "newestExistingUtc": draw_time_utc_from_ms(newest_existing_ms),
                    "stopReason": "full_sync_complete",
                }
            )
        else:
            existing_ids = {
                str(row.get("drawEventId"))
                for row in existing_rows
                if str(row.get("drawEventId") or "")
            }
            existing_times = {
                parse_int(row.get("drawTimeMs"), 0)
                for row in existing_rows
                if parse_int(row.get("drawTimeMs"), 0) > 0
            }
            existing_official_times = {
                parse_int(row.get("drawTimeMs"), 0)
                for row in existing_rows
                if row_source_rank(row) >= 2 and parse_int(row.get("drawTimeMs"), 0) > 0
            }
            newest_existing_ms = max(existing_times, default=0)
            page = 1
            hit_existing = False
            max_pages = parse_int(
                options.get("maxPages"),
                1 if not existing_rows else 10,
            )
            catch_up_max_pages = parse_int(options.get("catchUpMaxPages"), 0)
            pages_fetched = 0
            catch_up_triggered = False
            stopped_by_max_pages = False
            stopped_by_catch_up_limit = False
            stopped_by_total_page = False
            oldest_fetched_ms = 0
            newest_fetched_ms = 0
            stop_reason = "unknown"
            while True:
                page_rows, meta = fetch_rows_page(
                    lottery_id=lottery_id,
                    page=page,
                    page_size=page_size,
                    sleep=sleep,
                    timeout=timeout,
                    retries=retries,
                    retry_sleep=retry_sleep,
                )
                pages_fetched += 1
                if not page_rows:
                    stop_reason = "empty_page"
                    break
                for row in page_rows:
                    draw_time_ms = parse_int(row.get("drawTimeMs"), 0)
                    if draw_time_ms > 0:
                        newest_fetched_ms = max(newest_fetched_ms, draw_time_ms)
                        oldest_fetched_ms = (
                            draw_time_ms
                            if oldest_fetched_ms == 0
                            else min(oldest_fetched_ms, draw_time_ms)
                        )
                    has_existing_id = str(row.get("drawEventId") or "") in existing_ids
                    has_existing_official_time = draw_time_ms in existing_official_times
                    has_existing_temporary_time = (
                        draw_time_ms in existing_times and draw_time_ms not in existing_official_times
                    )
                    if has_existing_id or has_existing_official_time:
                        hit_existing = True
                        stop_reason = "hit_existing"
                        break
                    if has_existing_temporary_time:
                        fetched_rows.append(row)
                        continue
                    fetched_rows.append(row)
                total_page = int(meta.get("totalPage") or 0)
                if hit_existing:
                    break
                if total_page and page >= total_page:
                    stopped_by_total_page = True
                    stop_reason = "total_page"
                    break
                if max_pages > 0 and page >= max_pages:
                    if existing_rows:
                        catch_up_triggered = True
                        effective_catch_up_max_pages = catch_up_max_pages or total_page
                        if (
                            effective_catch_up_max_pages > 0
                            and page >= effective_catch_up_max_pages
                        ):
                            stopped_by_catch_up_limit = True
                            stop_reason = "catch_up_limit"
                            break
                    else:
                        stopped_by_max_pages = True
                        stop_reason = "max_pages"
                        break
                page += 1
                if sleep > 0:
                    time.sleep(sleep)

            merged_before_etipos = merge_history_rows(existing_rows, fetched_rows)
            if skip_supplement:
                etipos_rows = []
                etipos_meta = {"source": config.get("officialSupplement", ""), "status": "skipped", "newRows": 0}
            else:
                try:
                    etipos_rows, etipos_meta = fetch_official_supplement(config, merged_before_etipos)
                except Exception as exc:
                    etipos_rows = []
                    etipos_meta = {"source": config.get("officialSupplement", ""), "error": str(exc), "newRows": 0}
            rows = merge_history_rows(merged_before_etipos, etipos_rows)
            write_dashboard_rows(out, rows, config)
            written_rows = len(rows)
            new_rows = max(0, written_rows - len(existing_rows))
            possible_gap = bool(existing_rows and not hit_existing)
            effective_catch_up_max_pages = catch_up_max_pages or int(meta.get("totalPage") or 0)
            sync_meta.update(
                {
                    "hitExisting": hit_existing,
                    "pagesFetched": pages_fetched,
                    "maxPages": max_pages,
                    "catchUpMaxPages": effective_catch_up_max_pages,
                    "catchUpTriggered": catch_up_triggered,
                    "stoppedByMaxPages": stopped_by_max_pages,
                    "stoppedByCatchUpLimit": stopped_by_catch_up_limit,
                    "stoppedByTotalPage": stopped_by_total_page,
                    "possibleGap": possible_gap,
                    "oldestFetchedUtc": draw_time_utc_from_ms(oldest_fetched_ms),
                    "newestFetchedUtc": draw_time_utc_from_ms(newest_fetched_ms),
                    "newestExistingUtc": draw_time_utc_from_ms(newest_existing_ms),
                    "stopReason": stop_reason,
                }
            )

        sync_meta["gapAudit"] = gap_audit(rows, config)
        sync_meta["dataIntegrity"] = history_data_integrity(rows, config, meta)
        meta = dict(meta)
        meta.update(sync_meta)
        settled_bets = settle_sim_bet_store(rows, config)
        settled_predictions = settle_prediction_tracking_store(rows, config)

    return {
        "ok": True,
        "game": game_public_config(config),
        "mode": "full" if fetch_all else "incremental",
        "newRows": new_rows,
        "bcNewRows": len(fetched_rows) if not fetch_all else new_rows,
        "etiposNewRows": etipos_meta.get("newRows", 0),
        "writtenRows": written_rows,
        "settledBets": settled_bets,
        "settledPredictions": settled_predictions,
        "hitExisting": sync_meta["hitExisting"],
        "pagesFetched": sync_meta["pagesFetched"],
        "stoppedByMaxPages": sync_meta["stoppedByMaxPages"],
        "possibleGap": sync_meta["possibleGap"],
        "oldestFetchedUtc": sync_meta["oldestFetchedUtc"],
        "newestExistingUtc": sync_meta["newestExistingUtc"],
        "syncMeta": sync_meta,
        "gapAudit": sync_meta["gapAudit"],
        "dataIntegrity": sync_meta["dataIntegrity"],
        "meta": meta,
        "etiposMeta": etipos_meta,
        "historyFile": file_info(out),
        "generatedAt": utc_now_iso(),
    }


def refresh_all_games(options: dict[str, Any]) -> dict[str, Any]:
    current_key = game_key_from_value(options.get("game"))
    ordered_keys = [current_key] + [key for key in LOTTERY_GAMES if key != current_key]
    mode = str(options.get("mode") or "incremental")
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for key in ordered_keys:
        game_options = dict(options)
        game_options["game"] = key
        try:
            results.append(refresh_history(game_options))
        except Exception as exc:
            errors.append(
                {
                    "game": key,
                    "shortName": str(LOTTERY_GAMES[key].get("shortName") or key),
                    "error": str(exc),
                }
            )

    current_result = next(
        (item for item in results if item.get("game", {}).get("key") == current_key),
        results[0] if results else None,
    )
    totals = {
        "newRows": sum(parse_int(item.get("newRows"), 0) for item in results),
        "bcNewRows": sum(parse_int(item.get("bcNewRows"), 0) for item in results),
        "etiposNewRows": sum(parse_int(item.get("etiposNewRows"), 0) for item in results),
        "settledBets": sum(parse_int(item.get("settledBets"), 0) for item in results),
        "settledPredictions": sum(parse_int(item.get("settledPredictions"), 0) for item in results),
        "writtenRows": sum(parse_int(item.get("writtenRows"), 0) for item in results),
    }
    possible_gap_games = [
        item.get("game", {}).get("shortName") or item.get("game", {}).get("key")
        for item in results
        if item.get("possibleGap")
    ]
    integrity_issue_games = [
        item.get("game", {}).get("shortName") or item.get("game", {}).get("key")
        for item in results
        if item.get("dataIntegrity", {}).get("status") in {"missing", "behind_latest"}
    ]
    return {
        "ok": bool(results),
        "allGames": True,
        "mode": "full" if mode == "full" else "incremental",
        "game": game_public_config(LOTTERY_GAMES[current_key]),
        "currentResult": current_result,
        "results": results,
        "errors": errors,
        "successCount": len(results),
        "errorCount": len(errors),
        "totalCount": len(ordered_keys),
        "newRows": totals["newRows"],
        "bcNewRows": totals["bcNewRows"],
        "etiposNewRows": totals["etiposNewRows"],
        "settledBets": totals["settledBets"],
        "settledPredictions": totals["settledPredictions"],
        "writtenRows": totals["writtenRows"],
        "possibleGap": bool(possible_gap_games),
        "possibleGapGames": possible_gap_games,
        "dataIntegrityOk": not integrity_issue_games,
        "integrityIssueGames": integrity_issue_games,
        "generatedAt": utc_now_iso(),
    }


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "KenoDashboard/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self.send_json(
                {
                    "ok": True,
                    "generatedAt": utc_now_iso(),
                    "defaultGame": DEFAULT_GAME_KEY,
                    "games": [game_public_config(config) for config in LOTTERY_GAMES.values()],
                    "historyFile": file_info(DEFAULT_HISTORY),
                }
            )
            return
        if parsed.path == "/api/games":
            self.send_json(games_payload())
            return
        if parsed.path == "/api/integrity":
            try:
                self.send_json(integrity_payload(parse_qs(parsed.query)))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/analysis":
            try:
                self.send_json(analysis_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/predictions":
            try:
                self.send_json(predictions_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/prediction-tracking":
            try:
                self.send_json(prediction_tracking_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/adjacent-derived-hits":
            try:
                self.send_json(adjacent_derived_hits_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/adjacent-derived-stats":
            try:
                self.send_json(adjacent_derived_stats_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/prediction-auto":
            try:
                self.send_json(prediction_auto_status_payload())
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/draws":
            try:
                self.send_json(draws_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/sim-bets":
            try:
                self.send_json(sim_bets_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/backtest/status":
            self.send_json(backtest_status_payload())
            return
        if parsed.path == "/api/backtest/scan/status":
            self.send_json(backtest_scan_status_payload())
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/refresh":
            try:
                options = self.read_json_body()
                self.send_json(refresh_history(options))
            except RequestBodyTooLarge as exc:
                self.send_error_json(413, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/refresh-all":
            try:
                options = self.read_json_body()
                self.send_json(refresh_all_games(options))
            except RequestBodyTooLarge as exc:
                self.send_error_json(413, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/sim-bets":
            try:
                self.send_json(create_sim_bet(self.read_json_body()))
            except RequestBodyTooLarge as exc:
                self.send_error_json(413, str(exc))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/prediction-tracking/settle":
            try:
                self.send_json(settle_prediction_tracking_request(self.read_json_body()))
            except RequestBodyTooLarge as exc:
                self.send_error_json(413, str(exc))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/prediction-auto":
            try:
                self.send_json(prediction_auto_request(self.read_json_body()))
            except RequestBodyTooLarge as exc:
                self.send_error_json(413, str(exc))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/backtest":
            try:
                payload, status = start_backtest(self.read_json_body())
                self.send_json(payload, status=status)
            except RequestBodyTooLarge as exc:
                self.send_error_json(413, str(exc))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/backtest/scan":
            try:
                payload, status = start_backtest_scan(self.read_json_body())
                self.send_json(payload, status=status)
            except RequestBodyTooLarge as exc:
                self.send_error_json(413, str(exc))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        self.send_error_json(404, "Not found")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/prediction-tracking/"):
            try:
                record_id = unquote(parsed.path.rsplit("/", 1)[-1])
                self.send_json(delete_prediction_tracking(record_id, parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except KeyError as exc:
                self.send_error_json(404, str(exc).strip("'"))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path.startswith("/api/sim-bets/"):
            try:
                bet_id = unquote(parsed.path.rsplit("/", 1)[-1])
                self.send_json(delete_sim_bet(bet_id, parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except KeyError as exc:
                self.send_error_json(404, str(exc).strip("'"))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        self.send_error_json(404, "Not found")

    def read_json_body(self) -> dict[str, Any]:
        length = parse_int(self.headers.get("Content-Length"), 0)
        if length <= 0:
            return {}
        if length > 1_000_000:
            raise RequestBodyTooLarge("Request body too large")
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def serve_static(self, path: str) -> None:
        if path in ("", "/"):
            target = WEB_ROOT / "index.html"
        else:
            target = (WEB_ROOT / path.lstrip("/")).resolve()
            if WEB_ROOT.resolve() not in target.parents and target != WEB_ROOT.resolve():
                self.send_error_json(403, "Forbidden")
                return
        if not target.exists() or not target.is_file():
            self.send_error_json(404, "Not found")
            return

        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {
            "application/javascript",
            "application/json",
        }:
            content_type = f"{content_type}; charset=utf-8"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: int, message: str) -> None:
        self.send_json({"ok": False, "error": message}, status=status)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{utc_now_iso()}] {self.address_string()} {fmt % args}")


def main() -> int:
    WEB_ROOT.mkdir(exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"Keno dashboard running at http://{HOST}:{PORT}")
    print(f"Serving files from {WEB_ROOT}")
    if load_prediction_auto_config().get("enabled"):
        start_prediction_auto()
        print("Prediction auto tracking resumed from config")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        print("Stopping server...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
