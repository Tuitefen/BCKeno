#!/usr/bin/env python3
"""
Local web dashboard API for BC.Game multi-market Keno analysis and tracking.

No third-party dependencies are required. The server serves static frontend files
from ./web and exposes JSON endpoints for data refresh and analysis.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import mimetypes
import os
import re
import sqlite3
import threading
import time
import traceback
import uuid
from bisect import bisect_left
from collections import Counter
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable
from urllib import error as urllib_error
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import fetch_bc_keno_history
import fetch_official_supplements
import keno_triple_omission


UTC = timezone.utc


class RequestBodyTooLarge(ValueError):
    pass


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
DATA_ROOT = Path(os.environ.get("BCKENO_DATA_DIR", ROOT / "data")).resolve()
LOG_ROOT = Path(os.environ.get("BCKENO_LOG_DIR", ROOT / "logs")).resolve()
BACKUP_ROOT = Path(os.environ.get("BCKENO_BACKUP_DIR", ROOT / "backups")).resolve()
DEFAULT_HISTORY = DATA_ROOT / "bc_spain_l_express_20_70_history.csv"
DEFAULT_PREDICTION_TRACKING = DATA_ROOT / "prediction_tracking.json"
DEFAULT_PREDICTION_TRACKING_DB = DATA_ROOT / "prediction_tracking.sqlite3"
DEFAULT_PREDICTION_AUTO_CONFIG = DATA_ROOT / "prediction_auto_config.json"
DEFAULT_TELEGRAM_CONFIG = DATA_ROOT / "telegram_bot_config.local.json"
DEFAULT_TELEGRAM_STATE = DATA_ROOT / "telegram_bot_state.local.json"
DEFAULT_LOTTERY_ID = "115889"
DEFAULT_GAME_KEY = "spain_l_express_20_70"
TELEGRAM_DEFAULT_DRAW_LINKS_BY_GAME = {
    "spain_l_express_20_70": "https://lotodate.ro/Extrageri/5-l-express-spania-20-70",
    "poland_keno_20_70": "https://lotodate.ro/Extrageri/4-keno-polonia-20-70",
    "italy_win_for_life_10_20": "https://lotodate.ro/Extrageri/11-win-for-life-classico-italia-10-20",
}
TELEGRAM_ROOT_DRAW_LINKS = {"https://lotodate.ro", "https://lotodate.ro/"}
HOST = "127.0.0.1"
PORT = 8787
DEFAULT_PAGE_SIZE = 100
DEFAULT_SYNC_SLEEP = 0.25

MAX_NUMBER_COLUMNS = 20
NUMBER_COLUMNS = [f"n{i}" for i in range(1, MAX_NUMBER_COLUMNS + 1)]
SUPPLEMENT_ID_PREFIXES = ("etipos-", "lotodate-", "polonia-loto-", "yesplay-", "winforlife-", "wflcloud-")
DATA_LOCK = threading.Lock()
ANALYSIS_CACHE_LOCK = threading.Lock()
PREDICTION_CACHE_LOCK = threading.Lock()
BACKTEST_CACHE_LOCK = threading.Lock()
BACKTEST_STATUS_LOCK = threading.Lock()
BACKTEST_SCAN_CACHE_LOCK = threading.Lock()
BACKTEST_SCAN_STATUS_LOCK = threading.Lock()
KILL_BACKTEST_CACHE_LOCK = threading.Lock()
STRATEGY_AUDIT_CACHE_LOCK = threading.Lock()
HISTORY_CACHE_LOCK = threading.Lock()
PREDICTION_TRACKING_LOCK = threading.Lock()
PREDICTION_TRACKING_AUTO_SYNC_LOCK = threading.Lock()
PREDICTION_DB_INIT_LOCK = threading.Lock()
PREDICTION_AUTO_LOCK = threading.Lock()
PREDICTION_PREWARM_LOCK = threading.Lock()
PREDICTION_AUTO_STOP = threading.Event()
PREDICTION_AUTO_THREAD: threading.Thread | None = None
TELEGRAM_BOT_STOP = threading.Event()
TELEGRAM_BOT_THREAD: threading.Thread | None = None
PREDICTION_DB_INITIALIZED = False
HISTORY_CACHE_MAX_ITEMS = 5
ANALYSIS_CACHE_MAX_ITEMS = 5
PREDICTION_CACHE_MAX_ITEMS = 40
KILL_BACKTEST_CACHE_MAX_ITEMS = 10
STRATEGY_AUDIT_CACHE_MAX_ITEMS = 8
HISTORY_CACHE: dict[tuple[str, int, int], list[dict[str, Any]]] = {}
ANALYSIS_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}
PREDICTION_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}
BACKTEST_CACHE: dict[str, dict[str, Any]] = {}
BACKTEST_SCAN_CACHE: dict[str, dict[str, Any]] = {}
KILL_BACKTEST_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}
STRATEGY_AUDIT_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}
PREDICTION_PREWARM_IN_FLIGHT: set[tuple[Any, ...]] = set()
PREDICTION_PREWARM_LAST: dict[str, dict[str, Any]] = {}
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
    "lastCompletedAt": "",
    "nextRunAt": "",
    "message": "自动追踪未启动",
    "results": [],
    "errors": [],
}
PREDICTION_AUTO_HISTORY_MARKERS: dict[str, tuple[int, int, str, str]] = {}
PREDICTION_TRACKING_AUTO_SYNC_LAST_ATTEMPT: dict[str, float] = {}
PREDICTION_BACKGROUND_SYNC_IN_FLIGHT: set[str] = set()
PREDICTION_BACKGROUND_SYNC_LAST_ATTEMPT: dict[str, float] = {}
PREDICTION_VOID_REASON_MISSING_TARGET = "目标期开奖缺失，且后续期次已到达，追踪作废"
PREDICTION_VOID_REASON_STALE_SOURCE = "上一期开奖结果未同步，计划基准不连续，追踪作废"
PREDICTION_VOID_REASON_PAST_TARGET = "预测创建晚于目标期开奖，追踪作废"
PREDICTION_VOID_REASON_SUPERSEDED = "同期开奖已有更新预测批次，较早批次作废"
LEGACY_VOID_REASONS = {
    "Target draw was skipped after later draws arrived; tracking voided": PREDICTION_VOID_REASON_MISSING_TARGET,
}

LOTTERY_GAMES: dict[str, dict[str, Any]] = {
    "spain_l_express_20_70": {
        "key": "spain_l_express_20_70",
        "lotteryId": "115889",
        "name": "西班牙快车 L Express",
        "shortName": "西班牙快车 20/70",
        "country": "Spain",
        "drawnNumbers": 20,
        "totalNumbers": 70,
        "drawIntervalMinutes": 4,
        "historyPath": DATA_ROOT / "bc_spain_l_express_20_70_history.csv",
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
        "historyPath": DATA_ROOT / "bc_poland_keno_20_70_history.csv",
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
        "historyPath": DATA_ROOT / "bc_russia_rapido_8_20_history.csv",
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
        "historyPath": DATA_ROOT / "bc_italy_win_for_life_10_20_history.csv",
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
PREDICTION_TRACKING_LEAD_SECONDS = 90
PREDICTION_TRACKING_AUTO_SYNC_COOLDOWN_SECONDS = 45
PREDICTION_TRACKING_OVERDUE_AUTO_SYNC_COOLDOWN_SECONDS = 5
PREDICTION_AUTO_SINGLE_GAME_CATCHUP_SECONDS = 5
PREDICTION_AUTO_MULTI_GAME_CATCHUP_SECONDS = 60
PREDICTION_AUTO_CATCHUP_MAX_SECONDS = 300
PREDICTION_DRAW_SYNC_GRACE_SECONDS = 10
PREDICTION_TRACKING_TOUCH_LOCK_TIMEOUT_SECONDS = 1.5
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
        {"mode": "main", "pickCount": 2, "label": "意大利 2球候选票"},
    ],
    "russia_rapido_8_20": [
        {"mode": "main", "pickCount": 2, "label": "俄罗斯 2球候选票"},
        {"mode": "bonus", "pickCount": 2, "label": "俄罗斯 2+1特殊球候选票"},
    ],
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
PREDICTION_PANEL_DEFAULT = "a"
PREDICTION_PANEL_B = "b"
PREDICTION_PANEL_C = "c"
PREDICTION_PANEL_D = "d"
PREDICTION_PANEL_E = "e"
PREDICTION_PANEL_M = "m"
PREDICTION_PANEL_F = "f"
PREDICTION_PANEL_G = "g"
PREDICTION_TRACKING_METHOD_BY_PANEL = {
    PREDICTION_PANEL_DEFAULT: PREDICTION_TRACKING_METHOD_VERSION,
    PREDICTION_PANEL_B: "strategy-ticket-b-v1",
    PREDICTION_PANEL_C: "strategy-ticket-c-v1",
    PREDICTION_PANEL_D: "strategy-ticket-d-observe-23-v1",
    PREDICTION_PANEL_E: "strategy-ticket-e-dprofit-five-v1",
    PREDICTION_PANEL_M: "strategy-ticket-m-lowgroup-v1",
    PREDICTION_PANEL_F: "strategy-ticket-f-v2",
    PREDICTION_PANEL_G: "strategy-ticket-g-v1",
}
PREDICTION_PANEL_LABELS = {
    PREDICTION_PANEL_DEFAULT: "A计划",
    PREDICTION_PANEL_B: "B计划",
    PREDICTION_PANEL_C: "旧C计划",
    PREDICTION_PANEL_D: "D计划",
    PREDICTION_PANEL_E: "E计划",
    PREDICTION_PANEL_M: "C计划",
    PREDICTION_PANEL_F: "旧F计划",
    PREDICTION_PANEL_G: "旧G计划",
}
PREDICTION_RETIRED_PANELS = {
    PREDICTION_PANEL_C,
    PREDICTION_PANEL_E,
    PREDICTION_PANEL_F,
    PREDICTION_PANEL_G,
}
PREDICTION_ACTIVE_TRACKING_PANELS = (
    PREDICTION_PANEL_DEFAULT,
    PREDICTION_PANEL_B,
    PREDICTION_PANEL_M,
    PREDICTION_PANEL_D,
)
PREDICTION_CURRENT_METHOD_FILTER_PANELS = {
    PREDICTION_PANEL_D,
    PREDICTION_PANEL_E,
}
PREDICTION_TICKET_BACKTEST_WINDOW = 1000
PREDICTION_TICKET_CHASE_PERIODS = 10
PREDICTION_TICKET_TOP_COUNT = 3
PREDICTION_STAKING_SIMULATION_LOOKBACK = PREDICTION_TICKET_BACKTEST_WINDOW
PREDICTION_STAKING_BASE_STAKE = 1.0
PREDICTION_STAKING_MAX_MULTIPLIER = 64
PREDICTION_STAKING_DOUBLE_AFTER_RANGE = range(1, 31)
STAKING_BACKTEST_DEFAULT_WINDOW = 1000
STAKING_BACKTEST_MAX_WINDOW = 50000
STAKING_BACKTEST_MAX_MANUAL_TICKETS = 20
STAKING_BACKTEST_DEFAULT_TIMEZONE = "Asia/Shanghai"
STAKING_BACKTEST_SEGMENT_HOURS = (1, 2, 4, 6)
STAKING_BACKTEST_SEGMENT_SAMPLE_MIN = 100
STAKING_BACKTEST_SEGMENT_SAMPLE_OK = 300
STAKING_BACKTEST_POLICY_DEFAULTS = {
    "flat": {"label": "平买", "kind": "flat", "stepMisses": 0, "maxStake": 1.0},
    "conservative": {"label": "保守", "kind": "ladder", "stepMisses": 30, "maxStake": 5.0},
    "standard": {"label": "标准", "kind": "ladder", "stepMisses": 20, "maxStake": 8.0},
    "aggressive": {"label": "激进", "kind": "ladder", "stepMisses": 10, "maxStake": 12.0},
    "custom": {"label": "自定义", "kind": "ladder", "stepMisses": 20, "maxStake": 8.0},
}
PREDICTION_PANEL_M_PICK_COUNTS = (2, 3)
PREDICTION_PANEL_M_TICKETS_PER_PICK = 2
PREDICTION_PANEL_M_PREFILTER_LIMIT = 320
PREDICTION_PANEL_M_POOL_SIZE_BY_PICK = {
    2: 18,
    3: 16,
}
PREDICTION_PANEL_M_SOURCE_PRIORITY = (
    "ab_source",
    "ab_union",
    "score_pool",
    "recent_hot",
    "miss_pool",
    "adjacent_run",
)
PREDICTION_PANEL_M_SOURCE_LABELS = {
    "ab_source": "A/B源票",
    "ab_union": "A/B合并池",
    "score_pool": "综合分池",
    "recent_hot": "近窗热号",
    "miss_pool": "遗漏池",
    "adjacent_run": "连号形态",
}
PREDICTION_PANEL_D_PICK_COUNTS = (2, 3)
PREDICTION_PANEL_D_RULES = (
    ("consensus", "共识"),
    ("decompose", "拆解"),
    ("reverse", "逆向"),
    ("shape", "形态"),
)
PREDICTION_PANEL_D_RULE_PRIORITY_NEW = {
    "consensus": 1.00,
    "decompose": 0.94,
    "reverse": 0.88,
    "shape": 0.82,
}
PREDICTION_PANEL_D_POOL_SIZE_BY_PICK = {
    2: 18,
    3: 16,
}
FREQUENCY_OBSERVATION_MIN_PICK = 3
FREQUENCY_OBSERVATION_MAX_PICK = 8
FREQUENCY_OBSERVATION_MAX_CANDIDATES = 240000
FREQUENCY_OBSERVATION_POOL_SIZE_BY_PICK = {
    4: 18,
    5: 16,
    6: 14,
    7: 13,
    8: 12,
}
PREDICTION_PANEL_C_TOP_COUNT = 8
PREDICTION_PANEL_C_CORE_PAIR_LIMIT = 6
PREDICTION_PANEL_C_COMPANION_LIMIT = 2
PREDICTION_PANEL_C_PREFILTER_LIMIT = 60
PREDICTION_PANEL_C_OFFSETS = (2, 3, 5, 7, 10, 14, 20)
PREDICTION_PANEL_C_BAND_DISTANCES = tuple(range(5, 11))
PREDICTION_PANEL_C_STRUCTURE_PRIORITY = {
    "cohit_free": 1.0,
    "band_5_10": 0.88,
    "offset_10": 0.78,
    "same_tail": 0.72,
    "adjacent_1": 0.68,
    "offset_d": 0.62,
}
PREDICTION_PANEL_C_STRUCTURE_LABELS = {
    "adjacent_1": "左右临码四码",
    "offset_10": "±10同列四码",
    "offset_d": "固定间隔四码",
    "band_5_10": "5-10位窗口四码",
    "same_tail": "同尾四码",
    "cohit_free": "历史共现四码",
}
PREDICTION_PANEL_D_TOP_COUNT = 48
PREDICTION_PANEL_D_POOL_SIZE = 18
PREDICTION_PANEL_D_PREFILTER_LIMIT = 80
PREDICTION_PANEL_D_DERIVED_PREFILTER_LIMIT = 180
PREDICTION_PANEL_D_RULE_LIMIT = 8
PREDICTION_PANEL_D_PAIR_SOURCE_LIMIT = 8
PREDICTION_PANEL_D_C_SOURCE_LIMIT = 8
PREDICTION_PANEL_D_RULE_PRIORITY = {
    "ab_pm": 0.92,
    "ab_shift": 0.88,
    "ab_tail": 0.82,
    "ab_mirror": 0.78,
    "ab_interval": 0.74,
    "c_original": 0.90,
    "c_shift": 0.80,
    "c_mirror": 0.76,
}
PREDICTION_PANEL_D_DISABLED_STRUCTURE_TYPES_BY_GAME = {
    "spain_l_express_20_70": {
        "d_ab_mirror",
        "d_ab_pm_1",
        "d_ab_pm_3",
        "d_ab_pm_4",
        "d_ab_pm_7",
        "d_ab_pm_9",
        "d_ab_shift_minus_2",
        "d_ab_shift_minus_4",
        "d_ab_shift_minus_6",
        "d_ab_shift_minus_8",
        "d_ab_shift_plus_1",
        "d_ab_shift_plus_3",
        "d_ab_shift_plus_7",
        "d_ab_tail_plus_10",
        "d_c_original_offset_d",
    },
    "poland_keno_20_70": {
        "d_ab_interval_mid_pm1",
        "d_ab_pm_3",
        "d_ab_pm_5",
        "d_ab_pm_6",
        "d_ab_pm_7",
        "d_ab_pm_8",
        "d_ab_shift_minus_2",
        "d_ab_shift_minus_3",
        "d_ab_shift_minus_4",
        "d_ab_shift_minus_8",
        "d_ab_shift_plus_1",
        "d_ab_shift_plus_3",
        "d_ab_shift_plus_4",
        "d_ab_shift_plus_5",
        "d_ab_shift_plus_7",
        "d_ab_tail_minus_20",
        "d_c_mirror_band_5_10",
        "d_c_original_band_5_10",
        "d_c_original_cohit_free",
        "d_c_original_offset_d",
        "d_c_original_same_tail",
        "d_c_shift_minus_1_band_5_10",
        "d_c_shift_plus_10_band_5_10",
        "d_c_shift_plus_10_cohit_free",
    },
    "russia_rapido_8_20": {
        "d_ab_shift_minus_1",
        "d_ab_shift_minus_3",
        "d_ab_shift_minus_4",
        "d_ab_shift_plus_3",
        "d_c_shift_minus_1_cohit_free",
        "d_c_shift_plus_1_cohit_free",
    },
    "italy_win_for_life_10_20": {
        "d_c_shift_minus_1_cohit_free",
    },
}
PREDICTION_PANEL_E_TOP_COUNT = 32
PREDICTION_PANEL_E_D_SOURCE_LIMIT = 48
PREDICTION_PANEL_E_DERIVED_PREFILTER_LIMIT = 240
PREDICTION_PANEL_E_RULE_LIMIT = 4
PREDICTION_PANEL_E_SOURCE_MIN_SETTLED = 30
PREDICTION_PANEL_E_SOURCE_CACHE_TTL_SECONDS = 60
PREDICTION_PANEL_E_SOURCE_CACHE: dict[str, tuple[float, set[str]]] = {}
PREDICTION_PANEL_E_FALLBACK_SOURCE_STRUCTURE_TYPES_BY_GAME = {
    "spain_l_express_20_70": {
        "d_c_shift_minus_10_cohit_free",
        "d_c_shift_plus_1_cohit_free",
        "d_c_original_band_5_10",
        "d_c_original_cohit_free",
        "d_ab_shift_plus_2",
        "d_ab_shift_minus_1",
        "d_ab_tail_minus_10",
        "d_ab_tail_minus_20",
        "d_ab_pm_2",
        "d_ab_shift_minus_9",
        "d_ab_interval_mid_pm1",
        "d_ab_shift_plus_5",
        "d_c_shift_minus_1_cohit_free",
        "d_c_shift_minus_10_band_5_10",
        "d_ab_shift_plus_9",
        "d_c_mirror_cohit_free",
        "d_ab_shift_plus_4",
        "d_c_shift_minus_1_band_5_10",
        "d_c_mirror_band_5_10",
        "d_ab_shift_minus_3",
        "d_ab_shift_plus_6",
        "d_c_shift_plus_10_cohit_free",
    },
    "poland_keno_20_70": {
        "d_ab_shift_minus_9",
        "d_c_shift_minus_10_cohit_free",
        "d_ab_shift_minus_5",
        "d_ab_pm_2",
        "d_c_shift_plus_1_cohit_free",
        "d_ab_shift_plus_6",
        "d_ab_pm_4",
        "d_ab_pm_1",
        "d_ab_tail_plus_10",
        "d_ab_shift_minus_1",
        "d_ab_shift_plus_2",
        "d_ab_tail_minus_10",
        "d_ab_mirror",
        "d_ab_shift_plus_8",
        "d_ab_interval_thirds",
        "d_c_shift_plus_1_band_5_10",
        "d_c_shift_minus_1_cohit_free",
        "d_ab_tail_plus_20",
        "d_ab_shift_plus_9",
        "d_ab_pm_9",
        "d_c_shift_minus_10_band_5_10",
    },
    "russia_rapido_8_20": {
        "d_ab_pm_1",
        "d_c_mirror_cohit_free",
        "d_ab_shift_plus_1",
        "d_c_original_cohit_free",
        "d_c_original_band_5_10",
        "d_ab_shift_minus_2",
        "d_ab_pm_3",
        "d_ab_interval_mid_pm1",
        "d_ab_shift_plus_2",
    },
    "italy_win_for_life_10_20": {
        "d_c_mirror_cohit_free",
    },
}
PREDICTION_PANEL_E_GAME_KEYS = {
    "spain_l_express_20_70",
    "poland_keno_20_70",
    "russia_rapido_8_20",
    "italy_win_for_life_10_20",
}
PREDICTION_PANEL_F_TOP_COUNT = 1
PREDICTION_PANEL_G_TOP_COUNT = 1
PREDICTION_PREWARM_GAME_KEYS = (
    "spain_l_express_20_70",
    "poland_keno_20_70",
)
PREDICTION_PREWARM_PANELS = (
    PREDICTION_PANEL_M,
)
PREDICTION_PANEL_D_KILL_C_ONLY_GAME_KEYS = {
    "russia_rapido_8_20",
    "italy_win_for_life_10_20",
}
ADJACENT_DERIVED_STATS_GAME_KEYS = {
    "spain_l_express_20_70",
    "poland_keno_20_70",
    "italy_win_for_life_10_20",
    "russia_rapido_8_20",
}
ADJACENT_DERIVED_SOURCE_PICK_COUNTS = {1, 2, 4}
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


def prediction_panel_from_value(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"g", "panel_g", "prediction_g", "predictiong", "kill_cde", "clean_cde"}:
        return PREDICTION_PANEL_G
    if text in {
        "f",
        "panel_f",
        "prediction_f",
        "predictionf",
        "reversal_cd",
        "kill_pool_reversal",
        "resonance_cd",
        "overlap_cd",
    }:
        return PREDICTION_PANEL_F
    if text in {"e", "panel_e", "prediction_e", "predictione"}:
        return PREDICTION_PANEL_E
    if text in {
        "m",
        "panel_m",
        "prediction_m",
        "predictionm",
        "martingale_candidates",
        "low_group",
        "lowgroup",
        "low_ticket",
    }:
        return PREDICTION_PANEL_M
    if text in {"d", "panel_d", "prediction_d", "predictiond", "kill_abc", "clean_abc", "kill_cd", "clean_cd"}:
        return PREDICTION_PANEL_D
    if text in {"c", "panel_c", "prediction_c", "predictionc", "structure", "structure_c"}:
        return PREDICTION_PANEL_C
    if text in {"b", "panel_b", "prediction_b", "predictionb", "kill_a", "reverse_a"}:
        return PREDICTION_PANEL_B
    return PREDICTION_PANEL_DEFAULT


def prediction_panel_from_query(query: dict[str, list[str]]) -> str:
    return prediction_panel_from_value(query.get("panel", [PREDICTION_PANEL_DEFAULT])[0])


def prediction_panel_is_retired(panel: str | None) -> bool:
    return panel is not None and prediction_panel_from_value(panel) in PREDICTION_RETIRED_PANELS


def ensure_prediction_tracking_panel_active(panel: str | None) -> None:
    if prediction_panel_is_retired(panel):
        raise ValueError("旧C/D/E/F/G计划追踪已停用")


def query_bool(query: dict[str, list[str]], key: str, default: bool) -> bool:
    values = query.get(key)
    if not values:
        return default
    text = str(values[0] or "").strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def prediction_panel_label(panel: str) -> str:
    return PREDICTION_PANEL_LABELS.get(prediction_panel_from_value(panel), PREDICTION_PANEL_LABELS[PREDICTION_PANEL_DEFAULT])


def prediction_method_version_for_panel(panel: str) -> str:
    return PREDICTION_TRACKING_METHOD_BY_PANEL.get(
        prediction_panel_from_value(panel),
        PREDICTION_TRACKING_METHOD_VERSION,
    )


def prediction_record_panel(record: dict[str, Any]) -> str:
    panel = prediction_panel_from_value(record.get("panel"))
    if panel in {
        PREDICTION_PANEL_B,
        PREDICTION_PANEL_C,
        PREDICTION_PANEL_D,
        PREDICTION_PANEL_E,
        PREDICTION_PANEL_M,
        PREDICTION_PANEL_F,
        PREDICTION_PANEL_G,
    }:
        return panel
    method_version = str(record.get("methodVersion") or "")
    if method_version == prediction_method_version_for_panel(PREDICTION_PANEL_G):
        return PREDICTION_PANEL_G
    if method_version == prediction_method_version_for_panel(PREDICTION_PANEL_F):
        return PREDICTION_PANEL_F
    if method_version == prediction_method_version_for_panel(PREDICTION_PANEL_E):
        return PREDICTION_PANEL_E
    if method_version == prediction_method_version_for_panel(PREDICTION_PANEL_M):
        return PREDICTION_PANEL_M
    if method_version == prediction_method_version_for_panel(PREDICTION_PANEL_D):
        return PREDICTION_PANEL_D
    if method_version == prediction_method_version_for_panel(PREDICTION_PANEL_C):
        return PREDICTION_PANEL_C
    if method_version == prediction_method_version_for_panel(PREDICTION_PANEL_B):
        return PREDICTION_PANEL_B
    return PREDICTION_PANEL_DEFAULT


def prediction_record_matches_panel(record: dict[str, Any], panel: str | None) -> bool:
    if panel is None:
        return True
    return prediction_record_panel(record) == prediction_panel_from_value(panel)


def prediction_records_for_panel(records: list[dict[str, Any]], panel: str | None) -> list[dict[str, Any]]:
    if panel is None:
        return records
    return [record for record in records if prediction_record_matches_panel(record, panel)]


def prediction_record_is_retired(record: dict[str, Any]) -> bool:
    return prediction_record_panel(record) in PREDICTION_RETIRED_PANELS


def prediction_record_is_active_tracking(record: dict[str, Any]) -> bool:
    return prediction_record_panel(record) in PREDICTION_ACTIVE_TRACKING_PANELS


def prediction_tracking_current_method_where(
    panel: str | None,
    *,
    include_retired: bool = False,
) -> tuple[str, list[Any]]:
    if include_retired:
        return "", []
    panel_key = prediction_panel_from_value(panel) if panel is not None else None
    current_methods = {
        filter_panel: prediction_method_version_for_panel(filter_panel)
        for filter_panel in sorted(PREDICTION_CURRENT_METHOD_FILTER_PANELS)
        if filter_panel in PREDICTION_ACTIVE_TRACKING_PANELS
    }
    if panel_key in current_methods:
        return " AND method_version = ?", [current_methods[panel_key]]
    if panel_key is None and current_methods:
        clauses: list[str] = []
        params: list[Any] = []
        for filter_panel, method_version in current_methods.items():
            clauses.append("(panel <> ? OR method_version = ?)")
            params.extend([filter_panel, method_version])
        return f" AND {' AND '.join(clauses)}", params
    return "", []


def game_public_config(config: dict[str, Any]) -> dict[str, Any]:
    analysis_supported = supports_analysis(config)
    predictions_supported = supports_predictions(config)
    prediction_tracking_supported = supports_prediction_tracking(config)
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
    # Prediction cache keys include game, history mtime/size, target draw time, and panel.
    # Keeping them avoids one game's refresh wiping another game's prewarmed tickets.
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
    with KILL_BACKTEST_CACHE_LOCK:
        KILL_BACKTEST_CACHE.clear()
    with STRATEGY_AUDIT_CACHE_LOCK:
        STRATEGY_AUDIT_CACHE.clear()
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


def dashboard_rows_signature(
    rows: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> tuple[tuple[str, ...], ...]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    fieldnames = history_fieldnames()
    ordered = sorted(rows, key=lambda item: parse_int(item.get("drawTimeMs"), 0), reverse=True)
    return tuple(
        tuple(str(dashboard_row_to_csv_row(row, config).get(field, "")) for field in fieldnames)
        for row in ordered
    )


def dashboard_rows_changed(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> bool:
    return dashboard_rows_signature(before, config) != dashboard_rows_signature(after, config)


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


def prediction_draw_interval_ms(config: dict[str, Any]) -> int:
    return int(float(config.get("drawIntervalMinutes") or 0) * 60000)


def prediction_draw_sync_grace_ms(config: dict[str, Any]) -> int:
    interval_ms = prediction_draw_interval_ms(config)
    if interval_ms <= 0:
        return PREDICTION_DRAW_SYNC_GRACE_SECONDS * 1000
    return max(5000, min(PREDICTION_DRAW_SYNC_GRACE_SECONDS * 1000, interval_ms // 6))


def next_operating_draw_after_ms(newest_ms: int, config: dict[str, Any]) -> tuple[int, int]:
    interval_ms = prediction_draw_interval_ms(config)
    if newest_ms <= 0 or interval_ms <= 0:
        return 0, 0
    max_offset = max(2, int(math.ceil((36 * 60 * 60000) / interval_ms)))
    for offset in range(1, max_offset + 1):
        draw_time_ms = newest_ms + offset * interval_ms
        if is_inside_operating_hours(draw_time_ms, config):
            return draw_time_ms, offset
    return newest_ms + interval_ms, 1


def future_prediction_draw_times(
    newest_ms: int,
    config: dict[str, Any],
    *,
    count: int = PREDICTION_HORIZONS,
    now_ms: int | None = None,
) -> list[dict[str, Any]]:
    interval_ms = prediction_draw_interval_ms(config)
    if newest_ms <= 0 or interval_ms <= 0 or count <= 0:
        return []
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    minimum_target_ms = now_ms + PREDICTION_TRACKING_LEAD_SECONDS * 1000
    first_offset = max(1, math.ceil((minimum_target_ms - newest_ms) / interval_ms))
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
    interval_ms = prediction_draw_interval_ms(config)
    if interval_ms <= 0:
        return 0
    return int((int(time.time() * 1000) + PREDICTION_TRACKING_LEAD_SECONDS * 1000) // interval_ms)


def prediction_target_cache_ms(
    all_rows: list[dict[str, Any]],
    config: dict[str, Any],
    now_ms: int,
) -> int:
    latest_timeline = all_rows[0] if all_rows else None
    newest_ms = parse_int(latest_timeline.get("drawTimeMs") if latest_timeline else 0, 0)
    forecast_times = future_prediction_draw_times(newest_ms, config, count=1, now_ms=now_ms)
    return parse_int(forecast_times[0].get("drawTimeMs"), 0) if forecast_times else 0


def prediction_prewarm_now_values(config: dict[str, Any], now_ms: int | None = None) -> tuple[int, ...]:
    now_value = now_ms if now_ms is not None else int(time.time() * 1000)
    interval_ms = prediction_draw_interval_ms(config)
    if interval_ms <= 0:
        return (now_value,)
    return (now_value, now_value + interval_ms)


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
    *,
    timeout: float = 30,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    recent, meta = fetch_official_supplements.fetch_recent_official(config, timeout=timeout)
    dashboard_recent = [official_row_to_dashboard_row(row, config) for row in recent]
    dashboard_rows = select_supplement_rows(dashboard_recent, existing_rows)
    meta = dict(meta)
    meta["checkedRows"] = len(recent)
    meta["newRows"] = len(dashboard_rows)
    meta["newestOfficialUtc"] = (
        recent[0]["drawTimeUtc"] if recent else meta.get("newestOfficialUtc", "")
    )
    return dashboard_rows, meta


def refresh_official_history_only(
    config: dict[str, Any],
    *,
    timeout: float = 6,
) -> dict[str, Any]:
    path = game_history_path(config)
    with DATA_LOCK:
        existing_rows = load_history_rows(path, config)
    before_count = len(existing_rows)
    before_latest_ms = max((parse_int(row.get("drawTimeMs"), 0) for row in existing_rows), default=0)
    try:
        cache_rows: list[dict[str, Any]] = []
        cache_meta: dict[str, Any] = {}
        if str(config.get("officialSupplement") or "") == "lotodate":
            recent_rows, cache_meta = fetch_official_supplements.fetch_lotodate_cached_due_rows(
                str(config.get("supplementUrl") or ""),
                newest_existing_ms=before_latest_ms,
                expected_count=int(config["drawnNumbers"]),
                total_numbers=int(config["totalNumbers"]),
                timeout=min(timeout, 2),
            )
            cache_dashboard_rows = [official_row_to_dashboard_row(row, config) for row in recent_rows]
            cache_rows = select_supplement_rows(cache_dashboard_rows, existing_rows)
        next_cached_ms = parse_int(cache_meta.get("nextCachedDrawTimeMs"), 0) if cache_meta else 0
        now_ms = int(time.time() * 1000)
        interval_ms = prediction_draw_interval_ms(config)
        tolerance_ms = prediction_tracking_freshness_tolerance_ms(config)
        expected_next_ms, _expected_offset = next_operating_draw_after_ms(before_latest_ms, config)
        cache_skip_reason = ""
        cache_rows_are_continuous = bool(cache_rows and before_latest_ms > 0 and interval_ms > 0)
        cache_cursor_ms = before_latest_ms
        for cache_row in sorted(cache_rows, key=lambda item: parse_int(item.get("drawTimeMs"), 0)):
            cache_row_ms = parse_int(cache_row.get("drawTimeMs"), 0)
            expected_cache_row_ms, _cache_row_offset = next_operating_draw_after_ms(cache_cursor_ms, config)
            if cache_row_ms <= 0 or expected_cache_row_ms <= 0 or abs(cache_row_ms - expected_cache_row_ms) > tolerance_ms:
                cache_rows_are_continuous = False
                cache_skip_reason = "cached_due_rows_not_continuous_with_local_history"
                break
            cache_cursor_ms = cache_row_ms
        if cache_rows and cache_rows_are_continuous:
            next_after_cache_ms, _next_after_cache_offset = next_operating_draw_after_ms(cache_cursor_ms, config)
            if next_after_cache_ms > 0 and next_after_cache_ms + prediction_draw_sync_grace_ms(config) <= now_ms:
                cache_rows_are_continuous = False
                cache_skip_reason = "cached_due_rows_still_leave_history_overdue"
        cache_wait_is_next_draw = (
            next_cached_ms > now_ms
            and before_latest_ms > 0
            and interval_ms > 0
            and expected_next_ms > 0
            and abs(next_cached_ms - expected_next_ms) <= tolerance_ms
        )
        if cache_rows and cache_rows_are_continuous:
            supplement_rows = cache_rows
            supplement_meta = dict(cache_meta)
            supplement_meta["newRows"] = len(cache_rows)
        elif cache_meta and not cache_rows and cache_wait_is_next_draw:
            supplement_meta = dict(cache_meta)
            supplement_meta["newRows"] = 0
            supplement_meta["status"] = "waiting_for_cached_draw"
            return {
                "ok": True,
                "game": game_public_config(config),
                "mode": "official_only",
                "newRows": 0,
                "bcNewRows": 0,
                "etiposNewRows": 0,
                "writtenRows": before_count,
                "historyFileChanged": False,
                "settledPredictions": 0,
                "previousNewestUtc": draw_time_utc_from_ms(before_latest_ms),
                "newestLocalUtc": draw_time_utc_from_ms(before_latest_ms),
                "meta": supplement_meta,
                "etiposMeta": supplement_meta,
                "predictionPrewarm": {"scheduled": False, "reason": "waiting_for_cached_draw", "game": config["key"]},
                "historyFile": file_info(path),
                "generatedAt": utc_now_iso(),
            }
        else:
            supplement_rows, supplement_meta = fetch_official_supplement(config, existing_rows, timeout=timeout)
            if cache_meta:
                supplement_meta = dict(supplement_meta)
                supplement_meta["cacheCheck"] = cache_meta
                if cache_rows and not cache_rows_are_continuous:
                    supplement_meta["cacheSkippedReason"] = cache_skip_reason or "cached_due_rows_not_continuous_with_local_history"
                elif next_cached_ms > now_ms and before_latest_ms > 0 and interval_ms > 0:
                    supplement_meta["cacheSkippedReason"] = "cached_next_not_continuous_with_local_history"
    except Exception as exc:
        supplement_rows = []
        supplement_meta = {
            "source": config.get("officialSupplement", ""),
            "status": "error",
            "error": str(exc),
            "newRows": 0,
        }
    with DATA_LOCK:
        rows = merge_history_rows(existing_rows, supplement_rows)
        history_file_changed = dashboard_rows_changed(existing_rows, rows, config)
        if history_file_changed:
            write_dashboard_rows(path, rows, config)
        after_latest_ms = max((parse_int(row.get("drawTimeMs"), 0) for row in rows), default=0)
    settled_predictions = settle_prediction_tracking_store(rows, config) if history_file_changed else 0
    prediction_prewarm = {"scheduled": False, "reason": "official_fast_sync", "game": config["key"]}
    new_rows = max(0, len(rows) - before_count)
    return {
        "ok": True,
        "game": game_public_config(config),
        "mode": "official_only",
        "newRows": new_rows,
        "bcNewRows": 0,
        "etiposNewRows": parse_int(supplement_meta.get("newRows"), 0),
        "writtenRows": len(rows),
        "historyFileChanged": history_file_changed,
        "settledPredictions": settled_predictions,
        "previousNewestUtc": draw_time_utc_from_ms(before_latest_ms),
        "newestLocalUtc": draw_time_utc_from_ms(after_latest_ms),
        "meta": supplement_meta,
        "etiposMeta": supplement_meta,
        "predictionPrewarm": prediction_prewarm,
        "historyFile": file_info(path),
        "generatedAt": utc_now_iso(),
    }


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


def byte_hit_stats(value: int) -> tuple[int, int, int, int, int] | None:
    positions = [index for index in range(8) if value & (1 << index)]
    if not positions:
        return None
    max_inner_miss = 0
    previous = positions[0]
    for current in positions[1:]:
        gap = current - previous - 1
        if gap > max_inner_miss:
            max_inner_miss = gap
        previous = current
    last_miss = positions[-1] - positions[-2] - 1 if len(positions) > 1 else positions[0]
    return positions[0], positions[-1], max_inner_miss, last_miss, len(positions)


BYTE_HIT_STATS = tuple(byte_hit_stats(value) for value in range(256))


def miss_stats_from_hit_mask(
    draw_count: int,
    hit_mask: int,
) -> tuple[int, int, int | None, int | None]:
    if hit_mask <= 0:
        return draw_count, draw_count, None, None

    max_miss = 0
    last_miss: int | None = None
    zero_run = 0
    seen_hit = False
    last_hit_draw = 0
    mask_bytes = hit_mask.to_bytes((hit_mask.bit_length() + 7) // 8, "little")
    for byte_index, byte_value in enumerate(mask_bytes):
        byte_stats = BYTE_HIT_STATS[byte_value]
        if byte_stats is None:
            zero_run += 8
            continue
        first_hit, last_hit, max_inner_miss, byte_last_miss, hit_count = byte_stats
        gap_to_first = zero_run + first_hit
        if seen_hit:
            if gap_to_first > max_miss:
                max_miss = gap_to_first
            last_miss = gap_to_first
        else:
            max_miss = gap_to_first
            last_miss = gap_to_first
            seen_hit = True
        if hit_count > 1:
            if max_inner_miss > max_miss:
                max_miss = max_inner_miss
            last_miss = byte_last_miss
        last_hit_draw = byte_index * 8 + last_hit + 1
        zero_run = 7 - last_hit
    current_miss = draw_count - last_hit_draw
    if current_miss > max_miss:
        max_miss = current_miss
    return current_miss, max_miss, last_miss, last_hit_draw


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


def ticket_stats_from_draw_sets(
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    numbers: tuple[int, ...],
    bonus_number: int | None,
    stats_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if stats_index is not None:
        return ticket_stats_from_index(stats_index, numbers, bonus_number)

    def hit(draw_set: set[int], bonus_value: int) -> bool:
        if not all(number in draw_set for number in numbers):
            return False
        return bonus_number is None or bonus_value == bonus_number

    hit_draws = [
        draw_index
        for draw_index, (draw_set, bonus_value) in enumerate(zip(draw_sets_oldest, bonus_values_oldest), start=1)
        if hit(draw_set, bonus_value)
    ]
    current_miss, max_miss, last_miss, last_hit_draw = miss_stats_from_hits(len(draw_sets_oldest), hit_draws)
    recent_hits = sum(
        1
        for draw_set, bonus_value in zip(recent_draw_sets, recent_bonus_values)
        if hit(draw_set, bonus_value)
    )
    ci_low, ci_high = wilson_interval(recent_hits, len(recent_draw_sets))
    return {
        "hits": len(hit_draws),
        "hitRate": len(hit_draws) / len(draw_sets_oldest) if draw_sets_oldest else 0,
        "currentMiss": current_miss,
        "maxMiss": max_miss,
        "lastMiss": last_miss,
        "lastHitDraw": last_hit_draw,
        "recentWindow": len(recent_draw_sets),
        "recentHits": recent_hits,
        "recentHitRate": recent_hits / len(recent_draw_sets) if recent_draw_sets else 0,
        "recentHitRateCi": [ci_low, ci_high],
    }


def ticket_stats_index(
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
) -> dict[str, Any]:
    number_masks: dict[int, int] = {}
    bonus_masks: dict[int, int] = {}
    for draw_index, (draw_set, bonus_value) in enumerate(zip(draw_sets_oldest, bonus_values_oldest), start=1):
        bit = 1 << (draw_index - 1)
        for number in draw_set:
            parsed = int(number)
            number_masks[parsed] = number_masks.get(parsed, 0) | bit
        if bonus_value:
            parsed_bonus = int(bonus_value)
            bonus_masks[parsed_bonus] = bonus_masks.get(parsed_bonus, 0) | bit
    draw_count = len(draw_sets_oldest)
    recent_window = len(recent_draw_sets)
    recent_mask = (
        ((1 << recent_window) - 1) << max(0, draw_count - recent_window)
        if recent_window > 0 and draw_count >= recent_window
        else 0
    )
    return {
        "drawCount": draw_count,
        "recentWindow": recent_window,
        "recentMask": recent_mask,
        "numberMasks": number_masks,
        "bonusMasks": bonus_masks,
    }


def ticket_hit_mask_from_index(
    stats_index: dict[str, Any],
    numbers: tuple[int, ...],
    bonus_number: int | None,
) -> int:
    draw_count = int(stats_index.get("drawCount") or 0)
    number_masks = stats_index.get("numberMasks") if isinstance(stats_index.get("numberMasks"), dict) else {}
    bonus_masks = stats_index.get("bonusMasks") if isinstance(stats_index.get("bonusMasks"), dict) else {}
    hit_mask = (1 << draw_count) - 1 if draw_count > 0 else 0
    for number in numbers:
        hit_mask &= int(number_masks.get(int(number), 0))
        if hit_mask == 0:
            break
    if hit_mask and bonus_number is not None:
        hit_mask &= int(bonus_masks.get(int(bonus_number), 0))
    return hit_mask


def ticket_recent_hits_from_index(
    stats_index: dict[str, Any],
    numbers: tuple[int, ...],
    bonus_number: int | None,
) -> int:
    recent_mask = int(stats_index.get("recentMask") or 0)
    if recent_mask <= 0:
        return 0
    number_masks = stats_index.get("numberMasks") if isinstance(stats_index.get("numberMasks"), dict) else {}
    bonus_masks = stats_index.get("bonusMasks") if isinstance(stats_index.get("bonusMasks"), dict) else {}
    hit_mask = recent_mask
    for number in numbers:
        hit_mask &= int(number_masks.get(int(number), 0))
        if hit_mask == 0:
            return 0
    if bonus_number is not None:
        hit_mask &= int(bonus_masks.get(int(bonus_number), 0))
    return hit_mask.bit_count()


def ticket_stats_from_index(
    stats_index: dict[str, Any],
    numbers: tuple[int, ...],
    bonus_number: int | None,
) -> dict[str, Any]:
    draw_count = int(stats_index.get("drawCount") or 0)
    recent_window = int(stats_index.get("recentWindow") or 0)
    hit_mask = ticket_hit_mask_from_index(stats_index, numbers, bonus_number)
    current_miss, max_miss, last_miss, last_hit_draw = miss_stats_from_hit_mask(draw_count, hit_mask)
    hit_count = hit_mask.bit_count()
    recent_mask = int(stats_index.get("recentMask") or 0)
    recent_hits = (hit_mask & recent_mask).bit_count() if recent_mask else 0
    ci_low, ci_high = wilson_interval(recent_hits, recent_window)
    return {
        "hits": hit_count,
        "hitRate": hit_count / draw_count if draw_count else 0,
        "currentMiss": current_miss,
        "maxMiss": max_miss,
        "lastMiss": last_miss,
        "lastHitDraw": last_hit_draw,
        "recentWindow": recent_window,
        "recentHits": recent_hits,
        "recentHitRate": recent_hits / recent_window if recent_window else 0,
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
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    *,
    panel: str = PREDICTION_PANEL_DEFAULT,
    excluded_numbers: set[int] | None = None,
    stats_index: dict[str, Any] | None = None,
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
    excluded_numbers = {int(number) for number in (excluded_numbers or set()) if int(number) > 0}
    scored = scored_numbers(
        list(range(1, total_numbers + 1)),
        PREDICTION_NUMBER_WEIGHTS[0],
        frequency,
        recent_counts,
        recent_window,
        draw_count,
    )
    if excluded_numbers:
        scored = [item for item in scored if int(item["number"]) not in excluded_numbers]
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
            stats = ticket_stats_from_draw_sets(
                draw_sets_oldest,
                bonus_values_oldest,
                recent_draw_sets,
                recent_bonus_values,
                numbers,
                bonus_number,
                stats_index=stats_index,
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
        item["label"] = str(spec["label"]) if panel == PREDICTION_PANEL_DEFAULT else f"B {spec['label']}"
        item["mode"] = mode
        item["pickCount"] = pick_count
        item["panel"] = prediction_panel_from_value(panel)
        item["excludedNumbers"] = sorted(excluded_numbers)
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
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    *,
    panel: str = PREDICTION_PANEL_DEFAULT,
    excluded_numbers: set[int] | None = None,
    stats_index: dict[str, Any] | None = None,
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
                draw_sets_oldest,
                bonus_values_oldest,
                recent_draw_sets,
                recent_bonus_values,
                panel=panel,
                excluded_numbers=excluded_numbers,
                stats_index=stats_index,
            )
        )
    return tickets


def prediction_panel_m_candidate_key(
    numbers: Iterable[Any],
    pick_count: int,
    total_numbers: int,
) -> tuple[int, ...]:
    parsed = tuple(
        sorted(
            {
                parse_int(number, 0)
                for number in numbers
                if 1 <= parse_int(number, 0) <= total_numbers
            }
        )
    )
    return parsed if len(parsed) == pick_count else ()


def prediction_panel_m_source_label(source_types: Iterable[str]) -> str:
    source_set = {str(source_type or "") for source_type in source_types}
    labels = [
        PREDICTION_PANEL_M_SOURCE_LABELS[source_type]
        for source_type in PREDICTION_PANEL_M_SOURCE_PRIORITY
        if source_type in source_set
    ]
    return " + ".join(labels[:3]) if labels else "历史审计"


def prediction_panel_m_follow_decision(item: dict[str, Any]) -> str:
    recent_hit_rate = parse_float(item.get("recentHitRate"), 0)
    hit_rate = parse_float(item.get("hitRate"), 0)
    break_even_hit_rate = parse_float(item.get("breakEvenHitRate"), 0)
    theoretical_hit_rate = parse_float(item.get("theoreticalHitRate"), 0)
    if break_even_hit_rate > 0 and recent_hit_rate >= break_even_hit_rate and hit_rate >= theoretical_hit_rate:
        return "可小注跟"
    if theoretical_hit_rate > 0 and recent_hit_rate >= theoretical_hit_rate and hit_rate >= theoretical_hit_rate * 0.98:
        return "只观察"
    return "不跟"


def prediction_staking_multiplier(
    miss_streak: int,
    miss_before_double: int | None,
    max_multiplier: int,
) -> int:
    if miss_before_double is None or miss_before_double <= 0 or max_multiplier <= 1:
        return 1
    if miss_streak < miss_before_double:
        return 1
    power = miss_streak - miss_before_double + 1
    max_power = int(math.floor(math.log2(max_multiplier))) if max_multiplier > 1 else 0
    return min(max_multiplier, 2 ** min(max(power, 0), max_power))


def prediction_staking_policy_rank(policy: dict[str, Any]) -> tuple[float, float, float, float, float, int]:
    threshold = 999 if str(policy.get("kind") or "") == "flat" else parse_int(policy.get("missBeforeDouble"), 0)
    return (
        parse_float(policy.get("netProfit"), 0),
        parse_float(policy.get("roi"), 0),
        -parse_float(policy.get("maxDrawdown"), 0),
        -parse_float(policy.get("totalStake"), 0),
        -parse_float(policy.get("maxStake"), 0),
        threshold,
    )


def prediction_staking_policy_simulation(
    draw_rows_oldest: list[dict[str, Any]],
    numbers: tuple[int, ...],
    odds: float,
    *,
    base_stake: float,
    max_multiplier: int,
    miss_before_double: int | None,
) -> dict[str, Any]:
    number_set = set(numbers)
    total_stake = 0.0
    total_payout = 0.0
    balance = 0.0
    peak_balance = 0.0
    max_drawdown = 0.0
    max_stake = 0.0
    max_multiplier_used = 1
    miss_streak = 0
    longest_miss_streak = 0
    wins = 0
    double_rounds = 0
    capped_rounds = 0
    first_double_round: int | None = None
    last_double_round: int | None = None
    double_events: list[dict[str, Any]] = []

    for round_index, row in enumerate(draw_rows_oldest, start=1):
        multiplier = prediction_staking_multiplier(miss_streak, miss_before_double, max_multiplier)
        stake = base_stake * multiplier
        if multiplier > 1:
            double_rounds += 1
            if first_double_round is None:
                first_double_round = round_index
            last_double_round = round_index
            if multiplier >= max_multiplier:
                capped_rounds += 1
            if len(double_events) < 8:
                double_events.append(
                    {
                        "round": round_index,
                        "drawTimeUtc": str(row.get("drawTimeUtc") or ""),
                        "missStreakBefore": miss_streak,
                        "stake": round(stake, 4),
                        "multiplier": multiplier,
                    }
                )

        won = number_set.issubset({parse_int(number, 0) for number in row.get("numbers") or []})
        payout = stake * odds if won else 0.0
        total_stake += stake
        total_payout += payout
        balance += payout - stake
        peak_balance = max(peak_balance, balance)
        max_drawdown = max(max_drawdown, peak_balance - balance)
        max_stake = max(max_stake, stake)
        max_multiplier_used = max(max_multiplier_used, multiplier)

        if won:
            wins += 1
            miss_streak = 0
        else:
            miss_streak += 1
            longest_miss_streak = max(longest_miss_streak, miss_streak)

    rounds = len(draw_rows_oldest)
    net_profit = total_payout - total_stake
    next_multiplier = prediction_staking_multiplier(miss_streak, miss_before_double, max_multiplier)
    kind = "flat" if miss_before_double is None else "double"
    label = "平买不加倍" if kind == "flat" else f"连挂{miss_before_double}期后加倍"
    return {
        "kind": kind,
        "label": label,
        "baseStake": round(base_stake, 4),
        "missBeforeDouble": miss_before_double,
        "maxMultiplier": max_multiplier,
        "rounds": rounds,
        "wins": wins,
        "losses": max(0, rounds - wins),
        "hitRate": wins / rounds if rounds else 0,
        "totalStake": round(total_stake, 4),
        "totalPayout": round(total_payout, 4),
        "netProfit": round(net_profit, 4),
        "roi": net_profit / total_stake if total_stake else 0,
        "maxStake": round(max_stake, 4),
        "maxMultiplierUsed": max_multiplier_used,
        "maxDrawdown": round(max_drawdown, 4),
        "longestMissStreak": longest_miss_streak,
        "currentMissStreak": miss_streak,
        "nextStake": round(base_stake * next_multiplier, 4),
        "nextMultiplier": next_multiplier,
        "doubleRounds": double_rounds,
        "cappedRounds": capped_rounds,
        "firstDoubleRound": first_double_round,
        "lastDoubleRound": last_double_round,
        "doubleEvents": double_events,
    }


def prediction_ticket_staking_simulation(
    rows: list[dict[str, Any]],
    ticket: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    total_numbers = int(config["totalNumbers"])
    pick_count = parse_int(ticket.get("pickCount"), len(ticket.get("numbers") or []))
    numbers = prediction_panel_m_candidate_key(ticket.get("numbers") or [], pick_count, total_numbers)
    game_key = str(config["key"])
    odds = parse_float(ticket.get("odds"), DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(pick_count, 0))
    if not rows or not numbers or odds <= 1:
        return {
            "enabled": False,
            "reason": "历史数据、候选号码或赔率不足，无法回放倍投。",
        }

    scoped_rows = [
        row
        for row in rows[:PREDICTION_STAKING_SIMULATION_LOOKBACK]
        if is_valid_draw_row(row, config)
    ]
    draw_rows_oldest = sorted(scoped_rows, key=lambda row: parse_int(row.get("drawTimeMs"), 0))
    if not draw_rows_oldest:
        return {
            "enabled": False,
            "reason": "没有可用于回放的有效开奖。",
        }

    base_stake = PREDICTION_STAKING_BASE_STAKE
    max_multiplier = PREDICTION_STAKING_MAX_MULTIPLIER
    flat = prediction_staking_policy_simulation(
        draw_rows_oldest,
        numbers,
        odds,
        base_stake=base_stake,
        max_multiplier=max_multiplier,
        miss_before_double=None,
    )
    double_policies = [
        prediction_staking_policy_simulation(
            draw_rows_oldest,
            numbers,
            odds,
            base_stake=base_stake,
            max_multiplier=max_multiplier,
            miss_before_double=miss_before_double,
        )
        for miss_before_double in PREDICTION_STAKING_DOUBLE_AFTER_RANGE
    ]
    best_double = max(double_policies, key=prediction_staking_policy_rank) if double_policies else None
    policies = [flat, *double_policies]
    best = max(policies, key=prediction_staking_policy_rank)
    top_policies = sorted(policies, key=prediction_staking_policy_rank, reverse=True)[:5]
    return {
        "enabled": True,
        "method": "当前候选票固定不变，按最近历史从旧到新回放；命中后下一期重置为1元。",
        "objective": "按历史净收益优先，回撤、总投入、最大单注作为次级排序。",
        "lookback": len(draw_rows_oldest),
        "requestedLookback": PREDICTION_STAKING_SIMULATION_LOOKBACK,
        "startDrawTimeUtc": str(draw_rows_oldest[0].get("drawTimeUtc") or ""),
        "endDrawTimeUtc": str(draw_rows_oldest[-1].get("drawTimeUtc") or ""),
        "numbers": list(numbers),
        "pickCount": pick_count,
        "odds": round(odds, 4),
        "baseStake": round(base_stake, 4),
        "maxMultiplier": max_multiplier,
        "flat": flat,
        "bestDouble": best_double,
        "best": best,
        "topPolicies": top_policies,
    }


def staking_backtest_query_float(
    query: dict[str, list[str]],
    key: str,
    default: float,
    *,
    min_value: float = 0.0,
    max_value: float = 1_000_000.0,
) -> float:
    value = parse_float(query.get(key, [default])[0], default)
    return min(max_value, max(min_value, value))


def staking_backtest_query_int(
    query: dict[str, list[str]],
    key: str,
    default: int,
    *,
    min_value: int = 0,
    max_value: int = 100000,
) -> int:
    value = parse_int(query.get(key, [default])[0], default)
    return min(max_value, max(min_value, value))


def staking_backtest_window_from_query(
    query: dict[str, list[str]],
    available_rows: int,
) -> tuple[int, str]:
    requested = str(query.get("window", [str(STAKING_BACKTEST_DEFAULT_WINDOW)])[0] or "").strip().lower()
    if requested in {"all", "full", "全部"}:
        return min(available_rows, STAKING_BACKTEST_MAX_WINDOW), "all"
    window = staking_backtest_query_int(
        query,
        "window",
        STAKING_BACKTEST_DEFAULT_WINDOW,
        min_value=30,
        max_value=STAKING_BACKTEST_MAX_WINDOW,
    )
    return min(available_rows, window), str(window)


def staking_backtest_timezone(query: dict[str, list[str]]) -> ZoneInfo:
    name = str(query.get("timeZone", [STAKING_BACKTEST_DEFAULT_TIMEZONE])[0] or STAKING_BACKTEST_DEFAULT_TIMEZONE).strip()
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo(STAKING_BACKTEST_DEFAULT_TIMEZONE)


def staking_backtest_datetime_ms(value: Any, tz: ZoneInfo) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return 0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    return int(parsed.astimezone(UTC).timestamp() * 1000)


def staking_backtest_time_minutes(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    match = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?$", text)
    if not match:
        return None
    hour = parse_int(match.group(1), -1)
    minute = parse_int(match.group(2), -1)
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return hour * 60 + minute


def staking_backtest_row_local_minutes(row: dict[str, Any], tz: ZoneInfo) -> int:
    draw_time_ms = parse_int(row.get("drawTimeMs"), 0)
    if draw_time_ms <= 0:
        return 0
    local_dt = datetime.fromtimestamp(draw_time_ms / 1000, tz=UTC).astimezone(tz)
    return local_dt.hour * 60 + local_dt.minute


def staking_backtest_minutes_in_range(
    minute: int,
    start_minute: int | None,
    end_minute: int | None,
) -> bool:
    if start_minute is None and end_minute is None:
        return True
    start = 0 if start_minute is None else start_minute
    end = 1439 if end_minute is None else end_minute
    if start == end:
        return True
    if start < end:
        return start <= minute <= end
    return minute >= start or minute <= end


def staking_backtest_filter_absolute_rows(
    rows: list[dict[str, Any]],
    *,
    start_ms: int,
    end_ms: int,
) -> list[dict[str, Any]]:
    if start_ms <= 0 and end_ms <= 0:
        return rows
    result = []
    for row in rows:
        draw_time_ms = parse_int(row.get("drawTimeMs"), 0)
        if start_ms > 0 and draw_time_ms < start_ms:
            continue
        if end_ms > 0 and draw_time_ms > end_ms:
            continue
        result.append(row)
    return result


def staking_backtest_filter_daily_rows(
    rows: list[dict[str, Any]],
    *,
    tz: ZoneInfo,
    start_minute: int | None,
    end_minute: int | None,
) -> list[dict[str, Any]]:
    if start_minute is None and end_minute is None:
        return rows
    return [
        row
        for row in rows
        if staking_backtest_minutes_in_range(
            staking_backtest_row_local_minutes(row, tz),
            start_minute,
            end_minute,
        )
    ]


def staking_backtest_hhmm(minute: int) -> str:
    minute = max(0, min(1440, int(minute)))
    if minute == 1440:
        return "24:00"
    return f"{minute // 60:02d}:{minute % 60:02d}"


def staking_backtest_time_filter_from_query(
    query: dict[str, list[str]],
) -> dict[str, Any]:
    tz = staking_backtest_timezone(query)
    start_text = str(query.get("startDateTime", [""])[0] or "").strip()
    end_text = str(query.get("endDateTime", [""])[0] or "").strip()
    daily_start_text = str(query.get("dailyStart", [""])[0] or "").strip()
    daily_end_text = str(query.get("dailyEnd", [""])[0] or "").strip()
    slice_hours = staking_backtest_query_int(query, "sliceHours", 2, min_value=1, max_value=6)
    if slice_hours not in STAKING_BACKTEST_SEGMENT_HOURS:
        slice_hours = 2
    return {
        "timeZone": str(tz.key),
        "tz": tz,
        "startDateTime": start_text,
        "endDateTime": end_text,
        "startMs": staking_backtest_datetime_ms(start_text, tz),
        "endMs": staking_backtest_datetime_ms(end_text, tz),
        "dailyStart": daily_start_text,
        "dailyEnd": daily_end_text,
        "dailyStartMinute": staking_backtest_time_minutes(daily_start_text),
        "dailyEndMinute": staking_backtest_time_minutes(daily_end_text),
        "sliceHours": slice_hours,
    }


def staking_backtest_policy_profiles(query: dict[str, list[str]]) -> list[dict[str, Any]]:
    base_stake = staking_backtest_query_float(query, "baseStake", 1.0, min_value=0.01, max_value=100000)
    step_stake = staking_backtest_query_float(query, "stepStake", 1.0, min_value=0.01, max_value=100000)
    policies: list[dict[str, Any]] = []
    for key in ("flat", "conservative", "standard", "aggressive", "custom"):
        defaults = STAKING_BACKTEST_POLICY_DEFAULTS[key]
        if key == "flat":
            policies.append(
                {
                    "key": key,
                    "label": defaults["label"],
                    "kind": "flat",
                    "baseStake": round(base_stake, 4),
                    "stepMisses": 0,
                    "stepStake": 0.0,
                    "maxStake": round(base_stake, 4),
                }
            )
            continue

        prefix = key
        step_misses = staking_backtest_query_int(
            query,
            f"{prefix}StepMisses",
            int(defaults["stepMisses"]),
            min_value=1,
            max_value=10000,
        )
        max_stake = staking_backtest_query_float(
            query,
            f"{prefix}MaxStake",
            float(defaults["maxStake"]),
            min_value=base_stake,
            max_value=1_000_000,
        )
        policy_step_stake = staking_backtest_query_float(
            query,
            f"{prefix}StepStake",
            step_stake,
            min_value=0.01,
            max_value=100000,
        )
        policies.append(
            {
                "key": key,
                "label": defaults["label"],
                "kind": "ladder",
                "baseStake": round(base_stake, 4),
                "stepMisses": step_misses,
                "stepStake": round(policy_step_stake, 4),
                "maxStake": round(max_stake, 4),
            }
        )
    return policies


def staking_backtest_stake_for_miss(policy: dict[str, Any], miss_streak: int) -> float:
    base_stake = parse_float(policy.get("baseStake"), 1.0)
    if str(policy.get("kind") or "") == "flat":
        return base_stake
    step_misses = max(1, parse_int(policy.get("stepMisses"), 1))
    step_stake = max(0.0, parse_float(policy.get("stepStake"), 0.0))
    max_stake = max(base_stake, parse_float(policy.get("maxStake"), base_stake))
    stake = base_stake + (max(0, miss_streak) // step_misses) * step_stake
    return min(max_stake, max(base_stake, stake))


def staking_backtest_policy_rank(policy: dict[str, Any]) -> tuple[float, float, float, float, float]:
    return (
        parse_float(policy.get("netProfit"), 0),
        parse_float(policy.get("roi"), 0),
        -parse_float(policy.get("maxDrawdown"), 0),
        -parse_float(policy.get("totalStake"), 0),
        -parse_float(policy.get("nextStake"), 0),
    )


def staking_backtest_policy_simulation(
    draw_rows_oldest: list[dict[str, Any]],
    numbers: tuple[int, ...],
    odds: float,
    policy: dict[str, Any],
) -> dict[str, Any]:
    number_set = set(numbers)
    total_stake = 0.0
    total_payout = 0.0
    balance = 0.0
    peak_balance = 0.0
    max_drawdown = 0.0
    max_stake_used = 0.0
    miss_streak = 0
    longest_miss_streak = 0
    wins = 0
    ladder_rounds = 0
    capped_rounds = 0
    first_ladder_round: int | None = None
    last_ladder_round: int | None = None
    step_events: list[dict[str, Any]] = []
    base_stake = parse_float(policy.get("baseStake"), 1.0)
    max_stake_limit = parse_float(policy.get("maxStake"), base_stake)

    for round_index, row in enumerate(draw_rows_oldest, start=1):
        stake = staking_backtest_stake_for_miss(policy, miss_streak)
        if stake > base_stake:
            ladder_rounds += 1
            if first_ladder_round is None:
                first_ladder_round = round_index
            last_ladder_round = round_index
            if stake >= max_stake_limit:
                capped_rounds += 1
            if len(step_events) < 8:
                step_events.append(
                    {
                        "round": round_index,
                        "drawTimeUtc": str(row.get("drawTimeUtc") or ""),
                        "missStreakBefore": miss_streak,
                        "stake": round(stake, 4),
                    }
                )

        won = number_set.issubset({parse_int(number, 0) for number in row.get("numbers") or []})
        payout = stake * odds if won else 0.0
        total_stake += stake
        total_payout += payout
        balance += payout - stake
        peak_balance = max(peak_balance, balance)
        max_drawdown = max(max_drawdown, peak_balance - balance)
        max_stake_used = max(max_stake_used, stake)

        if won:
            wins += 1
            miss_streak = 0
        else:
            miss_streak += 1
            longest_miss_streak = max(longest_miss_streak, miss_streak)

    rounds = len(draw_rows_oldest)
    net_profit = total_payout - total_stake
    next_stake = staking_backtest_stake_for_miss(policy, miss_streak)
    result = {
        "key": str(policy.get("key") or ""),
        "label": str(policy.get("label") or ""),
        "kind": str(policy.get("kind") or ""),
        "baseStake": round(base_stake, 4),
        "stepMisses": parse_int(policy.get("stepMisses"), 0),
        "stepStake": round(parse_float(policy.get("stepStake"), 0), 4),
        "maxStakeLimit": round(max_stake_limit, 4),
        "rounds": rounds,
        "wins": wins,
        "losses": max(0, rounds - wins),
        "hitRate": wins / rounds if rounds else 0,
        "totalStake": round(total_stake, 4),
        "totalPayout": round(total_payout, 4),
        "netProfit": round(net_profit, 4),
        "roi": net_profit / total_stake if total_stake else 0,
        "maxStake": round(max_stake_used, 4),
        "maxDrawdown": round(max_drawdown, 4),
        "longestMissStreak": longest_miss_streak,
        "currentMissStreak": miss_streak,
        "nextStake": round(next_stake, 4),
        "ladderRounds": ladder_rounds,
        "cappedRounds": capped_rounds,
        "firstLadderRound": first_ladder_round,
        "lastLadderRound": last_ladder_round,
        "stepEvents": step_events,
    }
    result["profitPerRound"] = net_profit / rounds if rounds else 0
    return result


def staking_backtest_parse_manual_tickets(
    raw: Any,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    total_numbers = int(config["totalNumbers"])
    drawn_numbers = int(config["drawnNumbers"])
    text = str(raw or "").strip()
    if not text:
        raise ValueError("手动号码不能为空")
    groups = [part.strip() for part in re.split(r"[,;|\n\r]+", text) if part.strip()]
    tickets: list[dict[str, Any]] = []
    for index, group in enumerate(groups[:STAKING_BACKTEST_MAX_MANUAL_TICKETS], start=1):
        numbers = sorted({parse_int(item, 0) for item in re.findall(r"\d+", group)})
        numbers = [number for number in numbers if 1 <= number <= total_numbers]
        pick_count = len(numbers)
        if pick_count < 1:
            continue
        if pick_count > drawn_numbers:
            raise ValueError(f"手动号码最多 {drawn_numbers} 个")
        odds = DEFAULT_MAIN_ODDS_BY_GAME.get(str(config["key"]), {}).get(pick_count)
        if not odds:
            raise ValueError(f"当前彩种不支持 {pick_count} 码赔率")
        tickets.append(
            {
                "numbers": numbers,
                "mode": "main",
                "pickCount": pick_count,
                "panel": "manual",
                "label": f"手动 {pick_count}码 #{index}",
                "ticketLabel": "-".join(str(number) for number in numbers),
                "odds": float(odds),
                "sourcePanel": "manual",
                "auditSourceLabel": "手动输入",
            }
        )
    if not tickets:
        raise ValueError("没有解析到可用的手动号码")
    return tickets


def staking_backtest_c_plan_tickets(config: dict[str, Any]) -> list[dict[str, Any]]:
    payload = predictions_payload(
        {"game": [str(config["key"])], "panel": [PREDICTION_PANEL_M]},
        touch_tracking=False,
    )
    predictions = payload.get("predictions") if isinstance(payload.get("predictions"), dict) else {}
    tickets = predictions.get("strategyTickets") if isinstance(predictions.get("strategyTickets"), list) else []
    return [ticket for ticket in tickets if isinstance(ticket, dict)]


def staking_backtest_verdict(
    policy_results: dict[str, dict[str, Any]],
    rows_count: int,
) -> dict[str, Any]:
    reasons: list[str] = []
    flat = policy_results.get("flat") or {}
    conservative = policy_results.get("conservative") or {}
    standard = policy_results.get("standard") or {}
    aggressive = policy_results.get("aggressive") or {}
    custom = policy_results.get("custom") or {}
    result_list = [item for item in policy_results.values() if isinstance(item, dict)]
    best = max(result_list, key=staking_backtest_policy_rank) if result_list else {}
    best_key = str(best.get("key") or "")
    next_stake = parse_float(best.get("nextStake"), 0)
    max_stake_limit = parse_float(best.get("maxStakeLimit"), 0)
    best_net = parse_float(best.get("netProfit"), 0)
    flat_net = parse_float(flat.get("netProfit"), 0)

    if rows_count < 300:
        return {
            "key": "watch",
            "label": "只观察",
            "tone": "warn",
            "bestPolicy": best_key,
            "reasons": ["样本不足 300 期，先不跟"],
        }

    if max_stake_limit > 0 and next_stake >= max_stake_limit * 0.8 and best_key != "flat":
        reasons.append("当前下一注接近最高档")
    if flat_net < 0 and best_key in {"aggressive", "custom"} and best_net > 0:
        reasons.append("收益主要依赖高档位资金规则")
    if best_net > 0 and parse_float(best.get("maxDrawdown"), 0) > abs(best_net) * 3:
        reasons.append("最大回撤明显大于净收益")

    if reasons:
        return {
            "key": "no_follow",
            "label": "不跟",
            "tone": "bad",
            "bestPolicy": best_key,
            "reasons": reasons,
        }

    if (
        flat_net >= 0
        and parse_float(conservative.get("netProfit"), 0) > 0
        and parse_float(standard.get("netProfit"), 0) > 0
    ):
        return {
            "key": "focus",
            "label": "重点观察",
            "tone": "good",
            "bestPolicy": best_key,
            "reasons": ["平买、保守、标准均未亏"],
        }

    if parse_float(conservative.get("netProfit"), 0) > 0 or parse_float(standard.get("netProfit"), 0) > 0:
        return {
            "key": "watch",
            "label": "只观察",
            "tone": "warn",
            "bestPolicy": best_key,
            "reasons": ["固定档位有正收益，但平买或另一档未确认"],
        }

    if parse_float(aggressive.get("netProfit"), 0) > 0 or parse_float(custom.get("netProfit"), 0) > 0:
        return {
            "key": "watch",
            "label": "只观察",
            "tone": "warn",
            "bestPolicy": best_key,
            "reasons": ["只有激进/自定义档位为正，不能直接跟"],
        }

    return {
        "key": "no_follow",
        "label": "不跟",
        "tone": "bad",
        "bestPolicy": best_key,
        "reasons": ["固定档位整体未跑出正收益"],
    }


def staking_backtest_ticket_items(
    scoped_rows: list[dict[str, Any]],
    tickets: list[dict[str, Any]],
    policies: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    draw_rows_oldest = sorted(scoped_rows, key=lambda row: parse_int(row.get("drawTimeMs"), 0))
    if not draw_rows_oldest:
        return []
    total_numbers = int(config["totalNumbers"])
    recent_window = min(PREDICTION_TICKET_BACKTEST_WINDOW, len(scoped_rows))
    ticket_items: list[dict[str, Any]] = []
    for index, ticket in enumerate(tickets, start=1):
        pick_count = parse_int(ticket.get("pickCount"), len(ticket.get("numbers") or []))
        numbers = prediction_panel_m_candidate_key(ticket.get("numbers") or [], pick_count, total_numbers)
        if not numbers:
            continue
        odds = parse_float(ticket.get("odds"), DEFAULT_MAIN_ODDS_BY_GAME.get(str(config["key"]), {}).get(pick_count, 0))
        if odds <= 1:
            continue
        theoretical_hit_rate = hit_probability_for(config, pick_count)
        stats = ticket_stats(scoped_rows, numbers, None, recent_window=recent_window)
        policy_results = {
            str(policy["key"]): staking_backtest_policy_simulation(draw_rows_oldest, numbers, odds, policy)
            for policy in policies
        }
        result_list = [item for item in policy_results.values() if isinstance(item, dict)]
        best = max(result_list, key=staking_backtest_policy_rank) if result_list else {}
        ticket_items.append(
            {
                "index": index,
                "label": str(ticket.get("label") or f"{pick_count}码候选"),
                "ticketLabel": str(ticket.get("ticketLabel") or "-".join(str(number) for number in numbers)),
                "numbers": list(numbers),
                "pickCount": pick_count,
                "mode": str(ticket.get("mode") or "main"),
                "odds": round(odds, 4),
                "theoreticalHitRate": theoretical_hit_rate,
                "breakEvenHitRate": 1 / odds if odds else 0,
                "fairOdds": 1 / theoretical_hit_rate if theoretical_hit_rate > 0 else 0,
                "auditSourceLabel": str(ticket.get("auditSourceLabel") or ticket.get("derivedRule") or ""),
                "score": parse_float(ticket.get("score"), 0),
                "recentWindow": stats["recentWindow"],
                "recentHits": stats["recentHits"],
                "recentHitRate": stats["recentHitRate"],
                "recentHitRateCi": stats["recentHitRateCi"],
                "hits": stats["hits"],
                "hitRate": stats["hitRate"],
                "currentMiss": stats["currentMiss"],
                "maxMiss": stats["maxMiss"],
                "policies": policy_results,
                "bestPolicy": best,
                "verdict": staking_backtest_verdict(policy_results, len(draw_rows_oldest)),
            }
        )
    return ticket_items


def staking_backtest_verdict_counts(ticket_items: list[dict[str, Any]]) -> dict[str, int]:
    verdict_counts: dict[str, int] = {}
    for item in ticket_items:
        key = str((item.get("verdict") or {}).get("key") or "unknown")
        verdict_counts[key] = verdict_counts.get(key, 0) + 1
    return verdict_counts


def staking_backtest_aggregate_policies(
    ticket_items: list[dict[str, Any]],
    policies: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    aggregates: dict[str, dict[str, Any]] = {}
    for policy in policies:
        key = str(policy.get("key") or "")
        policy_items = [
            (ticket.get("policies") or {}).get(key)
            for ticket in ticket_items
            if isinstance((ticket.get("policies") or {}).get(key), dict)
        ]
        total_stake = sum(parse_float(item.get("totalStake"), 0) for item in policy_items)
        total_payout = sum(parse_float(item.get("totalPayout"), 0) for item in policy_items)
        net_profit = total_payout - total_stake
        rounds = sum(parse_int(item.get("rounds"), 0) for item in policy_items)
        wins = sum(parse_int(item.get("wins"), 0) for item in policy_items)
        aggregates[key] = {
            "key": key,
            "label": str(policy.get("label") or key),
            "rounds": rounds,
            "wins": wins,
            "hitRate": wins / rounds if rounds else 0,
            "totalStake": round(total_stake, 4),
            "totalPayout": round(total_payout, 4),
            "netProfit": round(net_profit, 4),
            "roi": net_profit / total_stake if total_stake else 0,
            "maxDrawdown": round(sum(parse_float(item.get("maxDrawdown"), 0) for item in policy_items), 4),
            "nextStake": round(sum(parse_float(item.get("nextStake"), 0) for item in policy_items), 4),
            "maxStake": round(sum(parse_float(item.get("maxStake"), 0) for item in policy_items), 4),
            "longestMissStreak": max((parse_int(item.get("longestMissStreak"), 0) for item in policy_items), default=0),
        }
    return aggregates


def staking_backtest_segment_verdict(
    rows_count: int,
    aggregate_policies: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    standard = aggregate_policies.get("standard") or {}
    conservative = aggregate_policies.get("conservative") or {}
    flat = aggregate_policies.get("flat") or {}
    standard_net = parse_float(standard.get("netProfit"), 0)
    conservative_net = parse_float(conservative.get("netProfit"), 0)
    flat_net = parse_float(flat.get("netProfit"), 0)
    if rows_count <= 0:
        return {"key": "empty", "label": "无样本", "tone": "muted", "reasons": ["该时段没有开奖样本"]}
    if rows_count < STAKING_BACKTEST_SEGMENT_SAMPLE_MIN:
        return {"key": "low_sample", "label": "样本不足", "tone": "warn", "reasons": ["少于100期，只展示不下结论"]}
    if rows_count < STAKING_BACKTEST_SEGMENT_SAMPLE_OK:
        return {"key": "watch", "label": "只观察", "tone": "warn", "reasons": ["少于300期，防过拟合"]}
    if flat_net >= 0 and (standard_net > 0 or conservative_net > 0):
        return {"key": "focus", "label": "重点观察", "tone": "good", "reasons": ["平买不亏且固定档位为正"]}
    if standard_net > 0 or conservative_net > 0:
        return {"key": "watch", "label": "只观察", "tone": "warn", "reasons": ["固定档位为正但平买未确认"]}
    return {"key": "no_follow", "label": "不跟", "tone": "bad", "reasons": ["固定时段未跑出正收益"]}


def staking_backtest_time_segments(
    segment_source_rows: list[dict[str, Any]],
    tickets: list[dict[str, Any]],
    policies: list[dict[str, Any]],
    config: dict[str, Any],
    time_filter: dict[str, Any],
) -> list[dict[str, Any]]:
    tz = time_filter["tz"]
    slice_hours = parse_int(time_filter.get("sliceHours"), 2)
    slice_minutes = max(60, min(360, slice_hours * 60))
    segments: list[dict[str, Any]] = []
    for start_minute in range(0, 1440, slice_minutes):
        end_minute = min(1440, start_minute + slice_minutes)
        rows = [
            row
            for row in segment_source_rows
            if start_minute <= staking_backtest_row_local_minutes(row, tz) < end_minute
        ]
        ticket_items = staking_backtest_ticket_items(rows, tickets, policies, config) if rows else []
        aggregate_policies = staking_backtest_aggregate_policies(ticket_items, policies)
        standard = aggregate_policies.get("standard") or {}
        verdict = staking_backtest_segment_verdict(len(rows), aggregate_policies)
        segments.append(
            {
                "key": f"{staking_backtest_hhmm(start_minute)}-{staking_backtest_hhmm(end_minute)}",
                "label": f"{staking_backtest_hhmm(start_minute)}-{staking_backtest_hhmm(end_minute)}",
                "startMinute": start_minute,
                "endMinute": end_minute,
                "rows": len(rows),
                "ticketCount": len(ticket_items),
                "policies": aggregate_policies,
                "verdict": verdict,
                "sortNetProfit": parse_float(standard.get("netProfit"), 0),
                "sortRoi": parse_float(standard.get("roi"), 0),
            }
        )
    segments.sort(
        key=lambda item: (
            item["rows"] >= STAKING_BACKTEST_SEGMENT_SAMPLE_OK,
            parse_float(item.get("sortNetProfit"), 0),
            parse_float(item.get("sortRoi"), 0),
            -parse_int(item.get("startMinute"), 0),
        ),
        reverse=True,
    )
    for index, item in enumerate(segments, start=1):
        item["rank"] = index
    return segments


def staking_backtest_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_predictions_supported(config)
    source = str(query.get("source", ["c_plan"])[0] or "c_plan").strip().lower()
    history_path = game_history_path(config)
    with DATA_LOCK:
        all_rows = load_history_rows(history_path, config)
    rows = valid_draw_rows(all_rows, config)
    time_filter = staking_backtest_time_filter_from_query(query)
    date_scoped_rows = staking_backtest_filter_absolute_rows(
        rows,
        start_ms=parse_int(time_filter.get("startMs"), 0),
        end_ms=parse_int(time_filter.get("endMs"), 0),
    )
    window_count, requested_window = staking_backtest_window_from_query(query, len(date_scoped_rows))
    segment_source_rows = date_scoped_rows[:window_count]
    scoped_rows = staking_backtest_filter_daily_rows(
        segment_source_rows,
        tz=time_filter["tz"],
        start_minute=time_filter.get("dailyStartMinute"),
        end_minute=time_filter.get("dailyEndMinute"),
    )
    draw_rows_oldest = sorted(scoped_rows, key=lambda row: parse_int(row.get("drawTimeMs"), 0))
    if source in {"manual", "custom"}:
        tickets = staking_backtest_parse_manual_tickets(query.get("numbers", [""])[0], config)
        source = "manual"
        source_label = "手动号码"
    else:
        tickets = staking_backtest_c_plan_tickets(config)
        source = "c_plan"
        source_label = "当前C计划"

    if not draw_rows_oldest:
        raise ValueError("没有可用于回放的有效历史开奖")
    if not tickets:
        raise ValueError("当前来源没有可回放的候选票")

    policies = staking_backtest_policy_profiles(query)
    ticket_items = staking_backtest_ticket_items(scoped_rows, tickets, policies, config)
    verdict_counts = staking_backtest_verdict_counts(ticket_items)
    time_segments = staking_backtest_time_segments(segment_source_rows, tickets, policies, config, time_filter)

    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "game": game_public_config(config),
        "source": source,
        "sourceLabel": source_label,
        "policyMethod": "固定阶梯资金规则：命中后下一期回到起始金额，未中按固定连挂间隔每档加固定金额，最高不超过单注上限。",
        "window": {
            "requested": requested_window,
            "availableRows": len(rows),
            "dateFilteredRows": len(date_scoped_rows),
            "segmentSourceRows": len(segment_source_rows),
            "rows": len(draw_rows_oldest),
            "startDrawTimeUtc": str(draw_rows_oldest[0].get("drawTimeUtc") or ""),
            "endDrawTimeUtc": str(draw_rows_oldest[-1].get("drawTimeUtc") or ""),
        },
        "timeFilter": {
            "timeZone": time_filter["timeZone"],
            "startDateTime": time_filter["startDateTime"],
            "endDateTime": time_filter["endDateTime"],
            "startDrawTimeMs": time_filter["startMs"],
            "endDrawTimeMs": time_filter["endMs"],
            "dailyStart": time_filter["dailyStart"],
            "dailyEnd": time_filter["dailyEnd"],
            "dailyStartMinute": time_filter["dailyStartMinute"],
            "dailyEndMinute": time_filter["dailyEndMinute"],
            "sliceHours": time_filter["sliceHours"],
        },
        "policies": policies,
        "tickets": ticket_items,
        "timeSegments": time_segments,
        "summary": {
            "ticketCount": len(ticket_items),
            "focusCount": verdict_counts.get("focus", 0),
            "watchCount": verdict_counts.get("watch", 0),
            "noFollowCount": verdict_counts.get("no_follow", 0),
            "verdictCounts": verdict_counts,
            "segmentCount": len(time_segments),
        },
    }


def staking_backtest_local_datetime(draw_time_ms: int, tz: ZoneInfo) -> datetime:
    return datetime.fromtimestamp(max(0, draw_time_ms) / 1000, tz=UTC).astimezone(tz)


def staking_backtest_local_date_key(draw_time_ms: int, tz: ZoneInfo) -> str:
    if draw_time_ms <= 0:
        return ""
    return staking_backtest_local_datetime(draw_time_ms, tz).date().isoformat()


def staking_backtest_ms_iso(draw_time_ms: int) -> str:
    if draw_time_ms <= 0:
        return ""
    return datetime.fromtimestamp(draw_time_ms / 1000, tz=UTC).isoformat(timespec="seconds")


def current_backtest_source_panel(value: Any) -> tuple[str, str]:
    source = str(value or PREDICTION_PANEL_M).strip().lower()
    if source in {"d", "panel_d", "prediction_d", "predictiond"}:
        return PREDICTION_PANEL_D, "D计划"
    return PREDICTION_PANEL_M, "C计划"


def current_backtest_slot_selection(value: Any) -> tuple[set[str], str]:
    slot = str(value or "p3_1").strip().lower()
    labels = {
        "p2_1": "2码候选#1",
        "p2_2": "2码候选#2",
        "p2_3": "2码候选#3",
        "p2_4": "2码候选#4",
        "p2_all": "全部2码候选",
        "p3_1": "3码候选#3",
        "p3_2": "3码候选#4",
        "p3_3": "3码候选#5",
        "p3_4": "3码候选#6",
        "p3_all": "全部3码候选",
        "all": "全部候选",
    }
    if slot == "p2_all":
        return {"p2_1", "p2_2", "p2_3", "p2_4"}, labels[slot]
    if slot == "p3_all":
        return {"p3_1", "p3_2", "p3_3", "p3_4"}, labels[slot]
    if slot == "all":
        return set(), labels[slot]
    if slot not in labels:
        slot = "p3_1"
    return {slot}, labels[slot]


def current_backtest_candidate_label(record: dict[str, Any], rank: int) -> str:
    pick_count = parse_int(record.get("pickCount"), len(record.get("numbers") or []))
    if pick_count > 0 and rank > 0:
        return f"{pick_count}码候选#{rank}"
    if pick_count > 0:
        return f"{pick_count}码候选"
    return "候选票"


def current_backtest_candidate_slots(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slot_ranks, rank_sources = prediction_tracking_daily_slot_rank_info(records)
    ordered = sorted(
        records,
        key=lambda record: (
            slot_ranks.get(str(record.get("id") or ""), 0) or prediction_tracking_slot_rank(record) or 999,
            parse_int(record.get("pickCount"), len(record.get("numbers") or [])),
            prediction_tracking_ticket_number_key(record),
            str(record.get("ticketLabel") or ""),
            str(record.get("id") or ""),
        ),
    )
    pick_counts: dict[int, int] = {}
    result: list[dict[str, Any]] = []
    for index, record in enumerate(ordered, start=1):
        record_id = str(record.get("id") or "")
        rank = slot_ranks.get(record_id) or prediction_tracking_slot_rank(record) or index
        pick_count = parse_int(record.get("pickCount"), len(record.get("numbers") or []))
        pick_counts[pick_count] = pick_counts.get(pick_count, 0) + 1
        slot = pick_counts[pick_count]
        result.append(
            {
                "key": f"p{pick_count}_{slot}",
                "slotLabel": current_backtest_candidate_label(record, rank),
                "ticketRank": rank,
                "rankSource": rank_sources.get(record_id, "stored" if prediction_tracking_slot_rank(record) > 0 else "fallback"),
                "record": record,
            }
        )
    return result


def load_current_backtest_tracking_records(
    config: dict[str, Any],
    time_filter: dict[str, Any],
    *,
    panel: str,
    max_records: int,
) -> list[dict[str, Any]]:
    init_prediction_tracking_db()
    panel = prediction_panel_from_value(panel)
    params: list[Any] = [
        str(config["key"]),
        panel,
        prediction_method_version_for_panel(panel),
    ]
    where = "game_key = ? AND panel = ? AND method_version = ? AND status IN ('won', 'lost')"
    start_ms = parse_int(time_filter.get("startMs"), 0)
    end_ms = parse_int(time_filter.get("endMs"), 0)
    if start_ms > 0:
        where += " AND target_draw_time_ms >= ?"
        params.append(start_ms)
    if end_ms > 0:
        where += " AND target_draw_time_ms <= ?"
        params.append(end_ms)
    params.append(max(1, max_records))
    order_direction = "DESC" if start_ms <= 0 and end_ms <= 0 else "ASC"
    with prediction_tracking_db_connect() as conn:
        rows = conn.execute(
            f"""
            SELECT record_json
            FROM prediction_records
            WHERE {where}
            ORDER BY target_draw_time_ms {order_direction}, created_at {order_direction}, id {order_direction}
            LIMIT ?
            """,
            params,
        ).fetchall()
    records = sorted(
        prediction_tracking_records_from_rows(rows),
        key=lambda record: (
            parse_int(record.get("targetDrawTimeMs"), 0),
            str(record.get("createdAt") or ""),
            str(record.get("id") or ""),
        ),
    )
    game_day_tz = telegram_game_day_timezone(config)
    start_minute = time_filter.get("dailyStartMinute")
    end_minute = time_filter.get("dailyEndMinute")
    if start_minute is None and end_minute is None:
        return records
    return [
            record
            for record in records
            if staking_backtest_minutes_in_range(
            staking_backtest_row_local_minutes({"drawTimeMs": parse_int(record.get("targetDrawTimeMs"), 0)}, game_day_tz),
            start_minute,
            end_minute,
        )
    ]


def current_backtest_group_entries(
    records: list[dict[str, Any]],
    selected_slots: set[str],
    *,
    select_all: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for record in records:
        target_ms = parse_int(record.get("targetDrawTimeMs"), 0)
        if target_ms <= 0:
            continue
        grouped.setdefault(target_ms, []).append(record)

    entries: list[dict[str, Any]] = []
    slot_counts: dict[str, int] = {}
    missing_targets = 0
    for target_ms in sorted(grouped):
        batch = grouped[target_ms]
        slots = current_backtest_candidate_slots(batch)
        selected: list[dict[str, Any]] = []
        for item in slots:
            key = str(item.get("key") or "")
            record = item.get("record") if isinstance(item.get("record"), dict) else {}
            if not select_all and key not in selected_slots:
                continue
            if str(record.get("status") or "") not in {"won", "lost"}:
                continue
            selected.append(
                {
                    "slotKey": key,
                    "slotLabel": str(item.get("slotLabel") or key),
                    "ticketRank": parse_int(item.get("ticketRank"), 0),
                    "rankSource": str(item.get("rankSource") or ""),
                    "record": record,
                }
            )
            slot_counts[key] = slot_counts.get(key, 0) + 1
        if not selected:
            missing_targets += 1
            continue
        entries.append({"targetDrawTimeMs": target_ms, "tickets": selected})
    return entries, {
        "targetDraws": len(grouped),
        "selectedDraws": len(entries),
        "missingTargets": missing_targets,
        "slotCounts": slot_counts,
    }


def current_backtest_policy_simulation(
    draw_entries: list[dict[str, Any]],
    policy: dict[str, Any],
    *,
    include_ledger: bool = False,
) -> dict[str, Any]:
    total_stake = 0.0
    total_payout = 0.0
    balance = 0.0
    peak_balance = 0.0
    peak_time_ms = 0
    max_drawdown = 0.0
    max_stake_used = 0.0
    wins = 0
    bets = 0
    miss_by_slot: dict[str, int] = {}
    longest_miss_by_slot: dict[str, int] = {}
    next_stake_by_slot: dict[str, float] = {}
    wins_by_slot: dict[str, int] = {}
    max_stake_by_slot: dict[str, float] = {}
    hit_ledger: list[dict[str, Any]] = []
    milestones = {50: 0, 100: 0, 150: 0, 200: 0}

    for entry in draw_entries:
        target_ms = parse_int(entry.get("targetDrawTimeMs"), 0)
        for item in entry.get("tickets") or []:
            if not isinstance(item, dict):
                continue
            record = item.get("record") if isinstance(item.get("record"), dict) else {}
            slot_key = str(item.get("slotKey") or "")
            if not slot_key:
                continue
            current_miss = miss_by_slot.get(slot_key, 0)
            stake = staking_backtest_stake_for_miss(policy, current_miss)
            odds = parse_float(record.get("odds"), 0)
            if odds <= 0:
                pick_count = parse_int(record.get("pickCount"), len(record.get("numbers") or []))
                odds = parse_float(
                    DEFAULT_MAIN_ODDS_BY_GAME.get(prediction_tracking_game_key(record), {}).get(pick_count),
                    0,
                )
            won = str(record.get("status") or "") == "won"
            payout = stake * odds if won else 0.0
            total_stake += stake
            total_payout += payout
            balance += payout - stake
            max_stake_used = max(max_stake_used, stake)
            max_stake_by_slot[slot_key] = max(max_stake_by_slot.get(slot_key, 0.0), stake)
            bets += 1
            if won:
                wins += 1
                wins_by_slot[slot_key] = wins_by_slot.get(slot_key, 0) + 1
                if include_ledger and len(hit_ledger) < 200:
                    hit_ledger.append(
                        {
                            "drawTimeMs": target_ms,
                            "drawTimeUtc": staking_backtest_ms_iso(target_ms),
                            "slotKey": slot_key,
                            "slotLabel": str(item.get("slotLabel") or slot_key),
                            "ticketRank": parse_int(item.get("ticketRank"), 0),
                            "rankSource": str(item.get("rankSource") or ""),
                            "ticketLabel": str(record.get("ticketLabel") or ""),
                            "missBefore": current_miss,
                            "stake": round(stake, 4),
                            "odds": round(odds, 4),
                            "payout": round(payout, 4),
                            "ticketProfit": round(payout - stake, 4),
                            "balanceAfterTicket": round(balance, 4),
                        }
                    )
                miss_by_slot[slot_key] = 0
            else:
                next_miss = current_miss + 1
                miss_by_slot[slot_key] = next_miss
                longest_miss_by_slot[slot_key] = max(longest_miss_by_slot.get(slot_key, 0), next_miss)

        if balance > peak_balance:
            peak_balance = balance
            peak_time_ms = target_ms
        max_drawdown = max(max_drawdown, peak_balance - balance)
        for threshold in milestones:
            if not milestones[threshold] and balance >= threshold:
                milestones[threshold] = target_ms

    for slot_key, miss_streak in miss_by_slot.items():
        next_stake_by_slot[slot_key] = round(staking_backtest_stake_for_miss(policy, miss_streak), 4)

    net_profit = total_payout - total_stake
    rounds = len(draw_entries)
    result = {
        "key": str(policy.get("key") or ""),
        "label": str(policy.get("label") or ""),
        "kind": str(policy.get("kind") or ""),
        "baseStake": round(parse_float(policy.get("baseStake"), 1), 4),
        "stepMisses": parse_int(policy.get("stepMisses"), 0),
        "stepStake": round(parse_float(policy.get("stepStake"), 0), 4),
        "maxStakeLimit": round(parse_float(policy.get("maxStake"), 0), 4),
        "rounds": rounds,
        "bets": bets,
        "wins": wins,
        "losses": max(0, bets - wins),
        "hitRate": wins / bets if bets else 0,
        "totalStake": round(total_stake, 4),
        "totalPayout": round(total_payout, 4),
        "netProfit": round(net_profit, 4),
        "roi": net_profit / total_stake if total_stake else 0,
        "peakProfit": round(peak_balance, 4),
        "peakTimeMs": peak_time_ms,
        "peakTimeUtc": staking_backtest_ms_iso(peak_time_ms),
        "maxDrawdown": round(max_drawdown, 4),
        "maxStake": round(max_stake_used, 4),
        "longestMissStreak": max(longest_miss_by_slot.values(), default=0),
        "currentMissStreak": max(miss_by_slot.values(), default=0),
        "winsBySlot": wins_by_slot,
        "currentMissBySlot": {slot: int(value) for slot, value in sorted(miss_by_slot.items())},
        "longestMissBySlot": {slot: int(value) for slot, value in sorted(longest_miss_by_slot.items())},
        "maxStakeBySlot": {slot: round(value, 4) for slot, value in sorted(max_stake_by_slot.items())},
        "nextStake": round(sum(next_stake_by_slot.values()), 4),
        "nextStakeBySlot": next_stake_by_slot,
        "milestones": {
            str(threshold): {
                "threshold": threshold,
                "timeMs": hit_ms,
                "timeUtc": staking_backtest_ms_iso(hit_ms),
            }
            for threshold, hit_ms in milestones.items()
        },
    }
    if include_ledger:
        result["hitLedger"] = hit_ledger
    result["profitPerRound"] = net_profit / rounds if rounds else 0
    return result


def current_backtest_verdict(day: dict[str, Any]) -> dict[str, Any]:
    policies = day.get("policies") if isinstance(day.get("policies"), dict) else {}
    conservative = policies.get("conservative") if isinstance(policies.get("conservative"), dict) else {}
    flat = policies.get("flat") if isinstance(policies.get("flat"), dict) else {}
    standard = policies.get("standard") if isinstance(policies.get("standard"), dict) else {}
    rounds = parse_int(day.get("rounds"), 0)
    conservative_net = parse_float(conservative.get("netProfit"), 0)
    flat_net = parse_float(flat.get("netProfit"), 0)
    standard_net = parse_float(standard.get("netProfit"), 0)
    peak = parse_float(conservative.get("peakProfit"), 0)
    if rounds < 50:
        return {"key": "low_sample", "label": "样本不足", "tone": "warn", "reasons": ["当天有效推荐少于50期"]}
    if flat_net > 0 and conservative_net > 0:
        return {"key": "good", "label": "跟踪优先", "tone": "good", "reasons": ["平买和保守都为正"]}
    if conservative_net > 0 and standard_net > 0:
        return {"key": "watch", "label": "只观察", "tone": "warn", "reasons": ["保守和标准为正，平买未确认"]}
    if conservative_net > 0 or peak >= 100:
        return {"key": "watch", "label": "只观察", "tone": "warn", "reasons": ["有正收益或日内峰值，但稳定性不足"]}
    return {"key": "no_follow", "label": "不跟", "tone": "bad", "reasons": ["真实逐期推荐当天未跑出正收益"]}


def current_staking_backtest_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_prediction_tracking_supported(config)
    time_filter = staking_backtest_time_filter_from_query(query)
    max_records = staking_backtest_query_int(query, "maxRecords", 100000, min_value=100, max_value=300000)
    source_panel, source_label = current_backtest_source_panel(query.get("source", [PREDICTION_PANEL_M])[0])
    selected_slots, selection_label = current_backtest_slot_selection(query.get("slot", ["p3_1"])[0])
    records = load_current_backtest_tracking_records(config, time_filter, panel=source_panel, max_records=max_records)
    entries, coverage = current_backtest_group_entries(records, selected_slots, select_all=not selected_slots)
    game_day_tz = telegram_game_day_timezone(config)
    policies = staking_backtest_policy_profiles(query)
    include_ledger = query_bool(query, "ledger", False) or query_bool(query, "debugLedger", False)

    day_entries: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        day_key = staking_backtest_local_date_key(parse_int(entry.get("targetDrawTimeMs"), 0), game_day_tz)
        if not day_key:
            continue
        day_entries.setdefault(day_key, []).append(entry)

    days: list[dict[str, Any]] = []
    summary_policy_lists: dict[str, list[dict[str, Any]]] = {str(policy.get("key") or ""): [] for policy in policies}
    for day_key in sorted(day_entries):
        rows = sorted(day_entries[day_key], key=lambda item: parse_int(item.get("targetDrawTimeMs"), 0))
        policy_results = {
            str(policy["key"]): current_backtest_policy_simulation(rows, policy, include_ledger=include_ledger)
            for policy in policies
        }
        for key, item in policy_results.items():
            summary_policy_lists.setdefault(key, []).append(item)
        ticket_count = sum(len(entry.get("tickets") or []) for entry in rows)
        day = {
            "date": day_key,
            "rounds": len(rows),
            "bets": ticket_count,
            "startTimeMs": parse_int(rows[0].get("targetDrawTimeMs"), 0) if rows else 0,
            "endTimeMs": parse_int(rows[-1].get("targetDrawTimeMs"), 0) if rows else 0,
            "startTimeUtc": staking_backtest_ms_iso(parse_int(rows[0].get("targetDrawTimeMs"), 0)) if rows else "",
            "endTimeUtc": staking_backtest_ms_iso(parse_int(rows[-1].get("targetDrawTimeMs"), 0)) if rows else "",
            "policies": policy_results,
        }
        day["verdict"] = current_backtest_verdict(day)
        days.append(day)

    summary_policies: dict[str, dict[str, Any]] = {}
    for policy in policies:
        key = str(policy.get("key") or "")
        items = summary_policy_lists.get(key) or []
        total_stake = sum(parse_float(item.get("totalStake"), 0) for item in items)
        total_payout = sum(parse_float(item.get("totalPayout"), 0) for item in items)
        net_profit = total_payout - total_stake
        bets = sum(parse_int(item.get("bets"), 0) for item in items)
        wins = sum(parse_int(item.get("wins"), 0) for item in items)
        best_day = max(items, key=lambda item: parse_float(item.get("netProfit"), 0), default={})
        peak_day = max(items, key=lambda item: parse_float(item.get("peakProfit"), 0), default={})
        summary_policies[key] = {
            "key": key,
            "label": str(policy.get("label") or key),
            "days": len(items),
            "rounds": sum(parse_int(item.get("rounds"), 0) for item in items),
            "bets": bets,
            "wins": wins,
            "losses": max(0, bets - wins),
            "hitRate": wins / bets if bets else 0,
            "totalStake": round(total_stake, 4),
            "totalPayout": round(total_payout, 4),
            "netProfit": round(net_profit, 4),
            "roi": net_profit / total_stake if total_stake else 0,
            "peakProfit": round(max((parse_float(item.get("peakProfit"), 0) for item in items), default=0), 4),
            "maxDrawdown": round(max((parse_float(item.get("maxDrawdown"), 0) for item in items), default=0), 4),
            "bestDayProfit": round(parse_float(best_day.get("netProfit"), 0), 4),
            "peakDayProfit": round(parse_float(peak_day.get("peakProfit"), 0), 4),
        }

    coverage_start = parse_int(entries[0].get("targetDrawTimeMs"), 0) if entries else 0
    coverage_end = parse_int(entries[-1].get("targetDrawTimeMs"), 0) if entries else 0
    warnings: list[str] = []
    if not records:
        warnings.append(f"当前没有 {source_label} 已结算追踪记录；只能从追踪库存在的日期开始回放。")
    elif len(entries) < 300:
        warnings.append("真实逐期推荐样本少于300期，只能观察，不能定自动投注参数。")
    if coverage.get("missingTargets"):
        warnings.append(f"有 {coverage['missingTargets']} 个目标开奖没有匹配到所选槽位。")

    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "game": game_public_config(config),
        "method": f"真实逐期推荐回测：每期开奖使用当时追踪库里已经生成并结算的 {source_label} 候选，不固定当前号码。",
        "selection": {
            "source": source_panel,
            "sourceLabel": source_label,
            "slot": str(query.get("slot", ["p3_1"])[0] or "p3_1"),
            "label": selection_label,
            "selectedSlots": sorted(selected_slots),
        },
        "timeFilter": {
            "timeZone": time_filter["timeZone"],
            "gameDayTimeZone": str(game_day_tz.key),
            "startDateTime": time_filter["startDateTime"],
            "endDateTime": time_filter["endDateTime"],
            "startDrawTimeMs": time_filter["startMs"],
            "endDrawTimeMs": time_filter["endMs"],
            "dailyStart": time_filter["dailyStart"],
            "dailyEnd": time_filter["dailyEnd"],
            "dailyStartMinute": time_filter["dailyStartMinute"],
            "dailyEndMinute": time_filter["dailyEndMinute"],
        },
        "coverage": {
            **coverage,
            "records": len(records),
            "days": len(days),
            "startTimeMs": coverage_start,
            "endTimeMs": coverage_end,
            "startTimeUtc": staking_backtest_ms_iso(coverage_start),
            "endTimeUtc": staking_backtest_ms_iso(coverage_end),
        },
        "policies": policies,
        "summary": {
            "days": len(days),
            "rounds": sum(parse_int(day.get("rounds"), 0) for day in days),
            "bets": sum(parse_int(day.get("bets"), 0) for day in days),
            "positiveConservativeDays": sum(
                1
                for day in days
                if parse_float(((day.get("policies") or {}).get("conservative") or {}).get("netProfit"), 0) > 0
            ),
            "policies": summary_policies,
        },
        "days": list(reversed(days)),
        "warnings": warnings,
    }


def fixed_triple_day_rows(
    rows: list[dict[str, Any]],
    tz: ZoneInfo,
    *,
    start_minute: int | None = None,
    end_minute: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        draw_ms = parse_int(row.get("drawTimeMs"), 0)
        if draw_ms <= 0:
            continue
        if not staking_backtest_minutes_in_range(
            staking_backtest_row_local_minutes(row, tz),
            start_minute,
            end_minute,
        ):
            continue
        day_key = staking_backtest_local_date_key(draw_ms, tz)
        if not day_key:
            continue
        grouped.setdefault(day_key, []).append(row)
    for key in grouped:
        grouped[key].sort(key=lambda item: parse_int(item.get("drawTimeMs"), 0))
    return grouped


def fixed_triple_forward_rows(
    rows_by_day: dict[str, list[dict[str, Any]]],
    day_key: str,
    forward_days: int,
) -> list[dict[str, Any]]:
    days = [key for key in sorted(rows_by_day) if key > day_key]
    selected_days = days[: max(0, forward_days)]
    result: list[dict[str, Any]] = []
    for key in selected_days:
        result.extend(rows_by_day.get(key) or [])
    return sorted(result, key=lambda item: parse_int(item.get("drawTimeMs"), 0))


def fixed_triple_day_reset_policy_simulation(
    rows_by_day: dict[str, list[dict[str, Any]]],
    day_keys: list[str],
    numbers: tuple[int, ...],
    odds: float,
    policy: dict[str, Any],
) -> dict[str, Any]:
    day_results = [
        staking_backtest_policy_simulation(rows_by_day.get(day_key) or [], numbers, odds, policy)
        for day_key in day_keys
        if rows_by_day.get(day_key)
    ]
    total_stake = sum(parse_float(item.get("totalStake"), 0) for item in day_results)
    total_payout = sum(parse_float(item.get("totalPayout"), 0) for item in day_results)
    net_profit = total_payout - total_stake
    rounds = sum(parse_int(item.get("rounds"), 0) for item in day_results)
    wins = sum(parse_int(item.get("wins"), 0) for item in day_results)
    best_day = max(day_results, key=lambda item: parse_float(item.get("netProfit"), 0), default={})
    worst_day = min(day_results, key=lambda item: parse_float(item.get("netProfit"), 0), default={})
    return {
        "key": str(policy.get("key") or ""),
        "label": str(policy.get("label") or ""),
        "kind": str(policy.get("kind") or ""),
        "days": len(day_results),
        "positiveDays": sum(1 for item in day_results if parse_float(item.get("netProfit"), 0) > 0),
        "rounds": rounds,
        "wins": wins,
        "losses": max(0, rounds - wins),
        "hitRate": wins / rounds if rounds else 0,
        "totalStake": round(total_stake, 4),
        "totalPayout": round(total_payout, 4),
        "netProfit": round(net_profit, 4),
        "roi": net_profit / total_stake if total_stake else 0,
        "maxStake": round(max((parse_float(item.get("maxStake"), 0) for item in day_results), default=0), 4),
        "maxDrawdown": round(max((parse_float(item.get("maxDrawdown"), 0) for item in day_results), default=0), 4),
        "longestMissStreak": max((parse_int(item.get("longestMissStreak"), 0) for item in day_results), default=0),
        "bestDayProfit": round(parse_float(best_day.get("netProfit"), 0), 4),
        "worstDayProfit": round(parse_float(worst_day.get("netProfit"), 0), 4),
    }


def frequency_observation_join_candidates(
    previous: dict[tuple[int, ...], int],
    pick_count: int,
) -> set[tuple[int, ...]]:
    previous_keys = sorted(previous)
    previous_set = set(previous_keys)
    candidates: set[tuple[int, ...]] = set()
    for left_index, left in enumerate(previous_keys):
        for right in previous_keys[left_index + 1 :]:
            if left[:-1] != right[:-1]:
                if right[:-1] > left[:-1]:
                    break
                continue
            combo = tuple(sorted(set(left) | set(right)))
            if len(combo) != pick_count:
                continue
            if all(tuple(subset) in previous_set for subset in combinations(combo, pick_count - 1)):
                candidates.add(combo)
    return candidates


def frequency_observation_day_counts(
    day_rows: list[dict[str, Any]],
    pick_count: int,
    min_daily_hits: int,
    total_numbers: int,
    pool_numbers: set[int] | None = None,
) -> tuple[Counter[tuple[int, ...]], bool]:
    if pick_count < 1 or not day_rows:
        return Counter(), False
    min_daily_hits = max(1, min_daily_hits)
    one_counter: Counter[tuple[int, ...]] = Counter()
    draw_sets: list[set[int]] = []
    for row in day_rows:
        draw_numbers = {
            parse_int(number, 0)
            for number in row.get("numbers") or []
            if 1 <= parse_int(number, 0) <= total_numbers
        }
        if not draw_numbers:
            continue
        draw_sets.append(draw_numbers)
        for number in draw_numbers:
            one_counter[(number,)] += 1
    frequent: dict[tuple[int, ...], int] = {
        combo: count
        for combo, count in one_counter.items()
        if count >= min_daily_hits
    }
    if pick_count == 1:
        return Counter(frequent), False
    capped = False
    frequent_one_numbers = {combo[0] for combo in frequent}
    if pick_count <= 3:
        counter: Counter[tuple[int, ...]] = Counter()
        for draw_numbers in draw_sets:
            eligible = sorted(number for number in draw_numbers if number in frequent_one_numbers)
            if len(eligible) < pick_count:
                continue
            for combo in combinations(eligible, pick_count):
                counter[combo] += 1
        return Counter(
            {
                combo: count
                for combo, count in counter.items()
                if count >= min_daily_hits
            }
        ), False

    if pool_numbers is None:
        pool_size = FREQUENCY_OBSERVATION_POOL_SIZE_BY_PICK.get(pick_count, 12)
        pool_numbers = {
            combo[0]
            for combo, _count in sorted(
                frequent.items(),
                key=lambda item: (-item[1], item[0]),
            )[:pool_size]
        }
    counter: Counter[tuple[int, ...]] = Counter()
    for draw_numbers in draw_sets:
        eligible = sorted(number for number in draw_numbers if number in pool_numbers)
        if len(eligible) < pick_count:
            continue
        for combo in combinations(eligible, pick_count):
            counter[combo] += 1
    return Counter(
        {
            combo: count
            for combo, count in counter.items()
            if count >= min_daily_hits
        }
    ), True

    previous = frequent
    for level in range(2, pick_count + 1):
        candidates = frequency_observation_join_candidates(previous, level)
        if not candidates:
            return Counter(), capped
        if len(candidates) > FREQUENCY_OBSERVATION_MAX_CANDIDATES:
            capped = True
            candidates = set(
                sorted(
                    candidates,
                    key=lambda combo: (
                        -sum(previous.get(tuple(subset), 0) for subset in combinations(combo, level - 1)),
                        combo,
                    ),
                )[:FREQUENCY_OBSERVATION_MAX_CANDIDATES]
            )
        counter: Counter[tuple[int, ...]] = Counter()
        for draw_numbers in draw_sets:
            eligible = sorted(number for number in draw_numbers if number in frequent_one_numbers)
            if len(eligible) < level:
                continue
            for combo in combinations(eligible, level):
                if combo in candidates:
                    counter[combo] += 1
        previous = {
            combo: count
            for combo, count in counter.items()
            if count >= min_daily_hits
        }
        if not previous:
            return Counter(), capped
    return Counter(previous), capped


def fixed_triple_daily_counts(
    rows_by_day: dict[str, list[dict[str, Any]]],
    day_keys: list[str],
    pick_count: int,
    min_daily_hits: int,
    total_numbers: int,
) -> tuple[dict[str, Counter[tuple[int, ...]]], set[tuple[int, ...]], dict[str, Any]]:
    counters: dict[str, Counter[tuple[int, ...]]] = {}
    all_combos: set[tuple[int, ...]] = set()
    capped_days: list[str] = []
    global_pool_numbers: set[int] | None = None
    pool_size = FREQUENCY_OBSERVATION_POOL_SIZE_BY_PICK.get(pick_count, 0)
    if pick_count >= 4 and pool_size > 0:
        pool_counter: Counter[int] = Counter()
        for day_key in day_keys:
            for row in rows_by_day.get(day_key) or []:
                for number in {
                    parse_int(value, 0)
                    for value in row.get("numbers") or []
                    if 1 <= parse_int(value, 0) <= total_numbers
                }:
                    pool_counter[number] += 1
        global_pool_numbers = {
            number
            for number, _count in sorted(pool_counter.items(), key=lambda item: (-item[1], item[0]))[:pool_size]
        }
    for day_key in day_keys:
        counter, capped = frequency_observation_day_counts(
            rows_by_day.get(day_key) or [],
            pick_count,
            min_daily_hits,
            total_numbers,
            pool_numbers=global_pool_numbers,
        )
        counters[day_key] = counter
        all_combos.update(counter.keys())
        if capped:
            capped_days.append(day_key)
    return counters, all_combos, {
        "cappedDays": capped_days,
        "candidateCap": FREQUENCY_OBSERVATION_MAX_CANDIDATES,
        "poolSize": FREQUENCY_OBSERVATION_POOL_SIZE_BY_PICK.get(pick_count, 0),
        "poolNumbers": sorted(global_pool_numbers or []),
    }


def fixed_triple_observation_verdict(
    item: dict[str, Any],
    *,
    forward_has_rows: bool,
) -> dict[str, Any]:
    history_conservative = item.get("historyConservative") if isinstance(item.get("historyConservative"), dict) else {}
    forward_conservative = item.get("forwardConservative") if isinstance(item.get("forwardConservative"), dict) else {}
    min_hits = parse_int(item.get("minDailyHits"), 0)
    history_net = parse_float(history_conservative.get("netProfit"), 0)
    history_positive_days = parse_int(history_conservative.get("positiveDays"), 0)
    source_days = parse_int(item.get("sourceDays"), 0)
    if source_days <= 0:
        return {"key": "empty", "label": "无样本", "tone": "warn", "reasons": ["历史窗口没有有效开奖日"]}
    if min_hits <= 0:
        return {"key": "no_follow", "label": "剔除", "tone": "bad", "reasons": ["没有做到每天命中"]}
    if history_positive_days < max(1, source_days // 2):
        return {"key": "watch", "label": "只观察", "tone": "warn", "reasons": ["每天有出现，但保守档正收益天数不足"]}
    if not forward_has_rows:
        return {"key": "pending", "label": "待观察", "tone": "warn", "reasons": ["历史窗口合格，后续开奖还未形成观察样本"]}
    forward_net = parse_float(forward_conservative.get("netProfit"), 0)
    if history_net > 0 and forward_net > 0:
        return {"key": "good", "label": "继续强", "tone": "good", "reasons": ["历史稳定且后续保守档为正"]}
    if history_net > 0:
        return {"key": "watch", "label": "只观察", "tone": "warn", "reasons": ["历史稳定，后续仍需确认"]}
    return {"key": "no_follow", "label": "不跟", "tone": "bad", "reasons": ["固定守号历史资金结果不够好"]}


def fixed_triple_observation_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_analysis_supported(config)
    pick_count = staking_backtest_query_int(
        query,
        "pickCount",
        3,
        min_value=FREQUENCY_OBSERVATION_MIN_PICK,
        max_value=min(FREQUENCY_OBSERVATION_MAX_PICK, int(config.get("drawnNumbers") or FREQUENCY_OBSERVATION_MAX_PICK)),
    )
    if int(config.get("drawnNumbers") or 0) < pick_count:
        raise ValueError(f"当前彩种不支持{pick_count}码频次观察")
    top_n = staking_backtest_query_int(query, "top", 3, min_value=1, max_value=20)
    days_limit = staking_backtest_query_int(query, "days", 31, min_value=1, max_value=120)
    forward_days = staking_backtest_query_int(query, "forwardDays", 3, min_value=1, max_value=14)
    min_daily_hits = staking_backtest_query_int(query, "minDailyHits", 3, min_value=1, max_value=50)
    time_filter = staking_backtest_time_filter_from_query(query)
    game_day_tz = telegram_game_day_timezone(config)
    policies = staking_backtest_policy_profiles(query)
    policy_by_key = {str(policy.get("key") or ""): policy for policy in policies}
    flat_policy = policy_by_key.get("flat") or policies[0]
    conservative_policy = policy_by_key.get("conservative") or policies[0]

    history_path = game_history_path(config)
    with DATA_LOCK:
        all_rows = load_history_rows(history_path, config)
    rows = sorted(valid_draw_rows(all_rows, config), key=lambda row: parse_int(row.get("drawTimeMs"), 0))
    date_scoped_rows = staking_backtest_filter_absolute_rows(
        rows,
        start_ms=parse_int(time_filter.get("startMs"), 0),
        end_ms=parse_int(time_filter.get("endMs"), 0),
    )
    all_rows_by_day = fixed_triple_day_rows(
        rows,
        game_day_tz,
        start_minute=time_filter.get("dailyStartMinute"),
        end_minute=time_filter.get("dailyEndMinute"),
    )
    scoped_rows_by_day = fixed_triple_day_rows(
        date_scoped_rows,
        game_day_tz,
        start_minute=time_filter.get("dailyStartMinute"),
        end_minute=time_filter.get("dailyEndMinute"),
    )
    selected_day_keys = sorted(scoped_rows_by_day)[-days_limit:]
    if not selected_day_keys:
        raise ValueError("历史窗口没有可统计的有效开奖日")
    odds = parse_float(DEFAULT_MAIN_ODDS_BY_GAME.get(str(config["key"]), {}).get(pick_count), 0)
    if odds <= 1:
        raise ValueError(f"当前彩种没有可用{pick_count}码赔率")

    daily_counts, all_combos, frequency_meta = fixed_triple_daily_counts(
        scoped_rows_by_day,
        selected_day_keys,
        pick_count,
        min_daily_hits,
        int(config["totalNumbers"]),
    )
    source_draws = sum(len(scoped_rows_by_day.get(day_key) or []) for day_key in selected_day_keys)
    filtered_items: list[dict[str, Any]] = []
    for combo in all_combos:
        daily_hits = [parse_int(daily_counts.get(day_key, {}).get(combo), 0) for day_key in selected_day_keys]
        if len(daily_hits) != len(selected_day_keys):
            continue
        min_hits = min(daily_hits) if daily_hits else 0
        if min_hits < min_daily_hits:
            continue
        total_hits = sum(daily_hits)
        average_hits = total_hits / len(daily_hits) if daily_hits else 0
        filtered_items.append(
            {
                "numbers": combo,
                "dailyHits": daily_hits,
                "totalHits": total_hits,
                "averageDailyHits": average_hits,
                "minDailyHits": min_hits,
                "maxDailyHits": max(daily_hits) if daily_hits else 0,
                "sourceDays": len(selected_day_keys),
                "sourceDraws": source_draws,
            }
        )

    filtered_items.sort(
        key=lambda item: (
            parse_float(item.get("averageDailyHits"), 0),
            parse_int(item.get("minDailyHits"), 0),
            parse_int(item.get("totalHits"), 0),
            tuple(-number for number in item.get("numbers") or ()),
        ),
        reverse=True,
    )
    selected = filtered_items[:top_n]
    latest_day = selected_day_keys[-1]
    forward_day_keys = [key for key in sorted(all_rows_by_day) if key > latest_day][:forward_days]
    forward_rows = [row for day_key in forward_day_keys for row in (all_rows_by_day.get(day_key) or [])]
    items: list[dict[str, Any]] = []
    for rank, item in enumerate(selected, start=1):
        numbers = tuple(item["numbers"])
        history_flat = fixed_triple_day_reset_policy_simulation(
            scoped_rows_by_day,
            selected_day_keys,
            numbers,
            odds,
            flat_policy,
        )
        history_conservative = fixed_triple_day_reset_policy_simulation(
            scoped_rows_by_day,
            selected_day_keys,
            numbers,
            odds,
            conservative_policy,
        )
        forward_flat = fixed_triple_day_reset_policy_simulation(
            all_rows_by_day,
            forward_day_keys,
            numbers,
            odds,
            flat_policy,
        ) if forward_day_keys else {}
        forward_conservative = fixed_triple_day_reset_policy_simulation(
            all_rows_by_day,
            forward_day_keys,
            numbers,
            odds,
            conservative_policy,
        ) if forward_day_keys else {}
        output_item = {
            "rank": rank,
            "pickCount": pick_count,
            "numbers": list(numbers),
            "odds": round(odds, 4),
            "sourceStartDay": selected_day_keys[0],
            "sourceEndDay": selected_day_keys[-1],
            "sourceDays": item["sourceDays"],
            "sourceDraws": item["sourceDraws"],
            "dailyHits": item["dailyHits"],
            "totalHits": item["totalHits"],
            "averageDailyHits": item["averageDailyHits"],
            "minDailyHits": item["minDailyHits"],
            "maxDailyHits": item["maxDailyHits"],
            "historyFlat": history_flat,
            "historyConservative": history_conservative,
            "forwardDays": len(forward_day_keys),
            "forwardRequestedDays": forward_days,
            "forwardStartDay": forward_day_keys[0] if forward_day_keys else "",
            "forwardEndDay": forward_day_keys[-1] if forward_day_keys else "",
            "forwardDraws": len(forward_rows),
            "forwardHits": sum(1 for row in forward_rows if ticket_hit(row, numbers)),
            "forwardFlat": forward_flat,
            "forwardConservative": forward_conservative,
        }
        output_item["forwardHitRate"] = (
            parse_int(output_item.get("forwardHits"), 0) / len(forward_rows) if forward_rows else 0
        )
        output_item["verdict"] = fixed_triple_observation_verdict(output_item, forward_has_rows=bool(forward_day_keys))
        items.append(output_item)

    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "game": game_public_config(config),
        "method": f"固定{pick_count}码跨天稳定观察：3码全量统计，4-8码使用每日高频号码池剪枝统计；只保留每天都达到最低出现次数的固定组合，再用于后续固定守号观察。",
        "timeFilter": {
            "timeZone": time_filter["timeZone"],
            "gameDayTimeZone": str(game_day_tz.key),
            "startDateTime": time_filter["startDateTime"],
            "endDateTime": time_filter["endDateTime"],
            "dailyStart": time_filter["dailyStart"],
            "dailyEnd": time_filter["dailyEnd"],
        },
        "settings": {
            "pickCount": pick_count,
            "top": top_n,
            "days": days_limit,
            "actualDays": len(selected_day_keys),
            "forwardDays": forward_days,
            "minDailyHits": min_daily_hits,
        },
        "summary": {
            "days": len(selected_day_keys),
            "items": len(items),
            "filteredCombos": len(filtered_items),
            "allCombos": len(all_combos),
            "sourceStartDay": selected_day_keys[0],
            "sourceEndDay": selected_day_keys[-1],
            "forwardDays": len(forward_day_keys),
            "forwardStartDay": forward_day_keys[0] if forward_day_keys else "",
            "forwardEndDay": forward_day_keys[-1] if forward_day_keys else "",
            "historyRows": len(rows),
            "dateFilteredRows": len(date_scoped_rows),
            "sourceDraws": source_draws,
            "cappedDays": frequency_meta.get("cappedDays") or [],
            "candidateCap": parse_int(frequency_meta.get("candidateCap"), 0),
            "poolSize": parse_int(frequency_meta.get("poolSize"), 0),
            "poolNumbers": frequency_meta.get("poolNumbers") or [],
            "profitableHistoryConservative": sum(
                1 for item in items if parse_float((item.get("historyConservative") or {}).get("netProfit"), 0) > 0
            ),
            "profitableForwardConservative": sum(
                1 for item in items if parse_float((item.get("forwardConservative") or {}).get("netProfit"), 0) > 0
            ),
        },
        "items": items,
    }


def fixed_triple_query_numbers(query: dict[str, list[str]], config: dict[str, Any]) -> tuple[int, ...]:
    raw = query.get("numbers", [""])[0]
    numbers = sorted(parse_bet_numbers(raw, int(config["totalNumbers"])))
    requested_pick = parse_int(query.get("pickCount", ["0"])[0], 0)
    if requested_pick > 0 and len(numbers) != requested_pick:
        raise ValueError(f"遗漏查询需要输入正好{requested_pick}个号码")
    if len(numbers) < FREQUENCY_OBSERVATION_MIN_PICK or len(numbers) > FREQUENCY_OBSERVATION_MAX_PICK:
        raise ValueError("遗漏查询需要输入3-8个号码，例如 3-51-61")
    return tuple(numbers)


def fixed_triple_omission_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_analysis_supported(config)
    numbers = fixed_triple_query_numbers(query, config)
    display_tz = staking_backtest_timezone(query)
    game_day_tz = telegram_game_day_timezone(config)
    date_text = str(query.get("date", [""])[0] or "").strip()
    if not date_text:
        date_text = datetime.now(tz=game_day_tz).date().isoformat()

    history_path = game_history_path(config)
    with DATA_LOCK:
        all_rows = load_history_rows(history_path, config)
    rows = sorted(valid_draw_rows(all_rows, config), key=lambda row: parse_int(row.get("drawTimeMs"), 0))
    rows_by_day = fixed_triple_day_rows(rows, game_day_tz)
    day_rows = rows_by_day.get(date_text) or []
    hit_positions: list[int] = []
    hit_rows: list[dict[str, Any]] = []
    for index, row in enumerate(day_rows, start=1):
        if ticket_hit(row, numbers):
            hit_positions.append(index)
            hit_rows.append(row)

    current_miss, max_miss, last_miss, last_hit_draw = miss_stats_from_hits(len(day_rows), hit_positions)
    last_hit_row = day_rows[last_hit_draw - 1] if last_hit_draw else None
    pick_count = len(numbers)
    odds = parse_float(DEFAULT_MAIN_ODDS_BY_GAME.get(str(config["key"]), {}).get(pick_count), 0)
    policies = staking_backtest_policy_profiles(query)
    policy_by_key = {str(policy.get("key") or ""): policy for policy in policies}
    flat_policy = policy_by_key.get("flat") or policies[0]
    conservative_policy = policy_by_key.get("conservative") or policies[0]
    flat = staking_backtest_policy_simulation(day_rows, numbers, odds, flat_policy) if day_rows and odds > 1 else {}
    conservative = (
        staking_backtest_policy_simulation(day_rows, numbers, odds, conservative_policy)
        if day_rows and odds > 1
        else {}
    )
    latest_row = day_rows[-1] if day_rows else {}
    first_row = day_rows[0] if day_rows else {}
    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "game": game_public_config(config),
        "method": f"固定{pick_count}码遗漏查询：按指定日期检查该{pick_count}码当天命中、当前遗漏和固定追投结果。",
        "timeZone": str(display_tz.key),
        "gameDayTimeZone": str(game_day_tz.key),
        "date": date_text,
        "pickCount": pick_count,
        "numbers": list(numbers),
        "ticketLabel": "-".join(str(number) for number in numbers),
        "odds": round(odds, 4),
        "draws": len(day_rows),
        "hits": len(hit_rows),
        "hitRate": len(hit_rows) / len(day_rows) if day_rows else 0,
        "currentMiss": current_miss,
        "maxMiss": max_miss,
        "lastMiss": last_miss,
        "lastHitDraw": last_hit_draw,
        "firstDrawTimeUtc": str(first_row.get("drawTimeUtc") or ""),
        "latestDrawTimeUtc": str(latest_row.get("drawTimeUtc") or ""),
        "lastHitTimeUtc": str(last_hit_row.get("drawTimeUtc") if last_hit_row else ""),
        "lastHitDrawEventId": str(last_hit_row.get("drawEventId") if last_hit_row else ""),
        "recentHitTimes": [
            {
                "drawIndex": hit_positions[index],
                "drawTimeUtc": str(row.get("drawTimeUtc") or ""),
                "drawEventId": str(row.get("drawEventId") or ""),
            }
            for index, row in list(enumerate(hit_rows))[-12:]
        ],
        "flat": flat,
        "conservative": conservative,
        "verdict": fixed_triple_omission_verdict(len(day_rows), len(hit_rows), current_miss, conservative),
    }


def fixed_triple_omission_verdict(
    draws: int,
    hits: int,
    current_miss: int,
    conservative: dict[str, Any],
) -> dict[str, Any]:
    if draws <= 0:
        return {"key": "empty", "label": "无开奖", "tone": "warn", "reasons": ["当天还没有有效开奖样本"]}
    conservative_net = parse_float(conservative.get("netProfit"), 0)
    next_stake = parse_float(conservative.get("nextStake"), 0)
    if hits <= 0:
        return {"key": "watch", "label": "等首中", "tone": "warn", "reasons": [f"今天尚未命中，当前遗漏 {current_miss} 期"]}
    if conservative_net > 0:
        return {"key": "good", "label": "今天可看", "tone": "good", "reasons": ["今天保守档已为正"]}
    return {
        "key": "watch",
        "label": "只观察",
        "tone": "warn",
        "reasons": [f"今天已命中 {hits} 次，但保守档仍未转正；下一注 {next_stake:g}"],
    }


def prediction_panel_m_add_candidate(
    candidates: dict[tuple[int, ...], dict[str, Any]],
    numbers: Iterable[Any],
    pick_count: int,
    total_numbers: int,
    source_type: str,
    *,
    source_numbers: Iterable[Any] | None = None,
    heuristic_score: float = 0,
) -> None:
    key = prediction_panel_m_candidate_key(numbers, pick_count, total_numbers)
    if not key:
        return
    item = candidates.setdefault(
        key,
        {
            "numbers": key,
            "sourceTypes": set(),
            "sourceNumbers": set(),
            "heuristicScores": [],
        },
    )
    item["sourceTypes"].add(source_type)
    item["heuristicScores"].append(float(heuristic_score))
    for number in source_numbers or key:
        parsed = parse_int(number, 0)
        if 1 <= parsed <= total_numbers:
            item["sourceNumbers"].add(parsed)


def prediction_panel_m_select_diverse(
    candidates: list[dict[str, Any]],
    pick_count: int,
    limit: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[int, ...]] = set()
    max_overlap = 0 if pick_count == 2 else 1
    for item in candidates:
        numbers = tuple(int(number) for number in item.get("numbers") or [])
        if numbers in selected_keys:
            continue
        number_set = set(numbers)
        if all(len(number_set & set(selected_item.get("numbers") or [])) <= max_overlap for selected_item in selected):
            selected.append(item)
            selected_keys.add(numbers)
        if len(selected) >= limit:
            return selected
    for item in candidates:
        numbers = tuple(int(number) for number in item.get("numbers") or [])
        if numbers in selected_keys:
            continue
        selected.append(item)
        selected_keys.add(numbers)
        if len(selected) >= limit:
            break
    return selected


def prediction_panel_m_low_group_tickets(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    base_strategy_tickets: list[dict[str, Any]],
    b_strategy_tickets: list[dict[str, Any]],
    frequency: dict[int, dict[str, Any]],
    recent_counts: dict[int, int],
    recent_window: int,
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    *,
    stats_index: dict[str, Any] | None = None,
    include_staking_simulation: bool = False,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    game_key = str(config["key"])
    total_numbers = int(config["totalNumbers"])
    draw_count = len(rows)
    number_range = list(range(1, total_numbers + 1))
    scored = scored_numbers(
        number_range,
        PREDICTION_NUMBER_WEIGHTS[0],
        frequency,
        recent_counts,
        recent_window,
        draw_count,
    )
    score_by_number = {int(item["number"]): parse_float(item.get("score"), 0) for item in scored}
    scored_numbers_ranked = [int(item["number"]) for item in scored]
    recent_ranked = sorted(
        number_range,
        key=lambda number: (
            -parse_int(recent_counts.get(number), 0),
            -parse_float(frequency.get(number, {}).get("hitRate"), 0),
            number,
        ),
    )
    miss_ranked = sorted(
        number_range,
        key=lambda number: (
            -parse_int(frequency.get(number, {}).get("currentMiss"), 0),
            -parse_float(frequency.get(number, {}).get("hitRate"), 0),
            number,
        ),
    )
    source_ticket_numbers = {
        parse_int(number, 0)
        for ticket in [*base_strategy_tickets, *b_strategy_tickets]
        if isinstance(ticket, dict) and str(ticket.get("mode") or "main") == "main"
        for number in ticket.get("numbers") or []
        if 1 <= parse_int(number, 0) <= total_numbers
    }
    source_pool = sorted(
        source_ticket_numbers,
        key=lambda number: (-score_by_number.get(number, 0), number),
    )

    result: list[dict[str, Any]] = []
    for pick_count in PREDICTION_PANEL_M_PICK_COUNTS:
        odds = DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(pick_count)
        if not odds:
            continue
        pool_size = min(total_numbers, PREDICTION_PANEL_M_POOL_SIZE_BY_PICK.get(pick_count, 16))
        candidate_map: dict[tuple[int, ...], dict[str, Any]] = {}
        pools = [
            ("score_pool", scored_numbers_ranked[:pool_size]),
            ("recent_hot", recent_ranked[:pool_size]),
            ("miss_pool", miss_ranked[:pool_size]),
        ]
        for source_type, pool in pools:
            for combo in combinations(pool, pick_count):
                combo_score = sum(score_by_number.get(int(number), 0) for number in combo) / max(pick_count, 1)
                prediction_panel_m_add_candidate(
                    candidate_map,
                    combo,
                    pick_count,
                    total_numbers,
                    source_type,
                    source_numbers=pool,
                    heuristic_score=combo_score,
                )
        for start in range(1, total_numbers - pick_count + 2):
            combo = tuple(range(start, start + pick_count))
            combo_score = sum(score_by_number.get(int(number), 0) for number in combo) / max(pick_count, 1)
            prediction_panel_m_add_candidate(
                candidate_map,
                combo,
                pick_count,
                total_numbers,
                "adjacent_run",
                heuristic_score=combo_score,
            )
        for ticket in [*base_strategy_tickets, *b_strategy_tickets]:
            if not isinstance(ticket, dict) or str(ticket.get("mode") or "main") != "main":
                continue
            numbers = prediction_panel_m_candidate_key(ticket.get("numbers") or [], pick_count, total_numbers)
            if not numbers:
                continue
            prediction_panel_m_add_candidate(
                candidate_map,
                numbers,
                pick_count,
                total_numbers,
                "ab_source",
                source_numbers=ticket.get("numbers") or [],
                heuristic_score=parse_float(ticket.get("score"), 0),
            )
        if len(source_pool) >= pick_count:
            union_pool = source_pool[:pool_size]
            for combo in combinations(union_pool, pick_count):
                combo_score = sum(score_by_number.get(int(number), 0) for number in combo) / max(pick_count, 1)
                prediction_panel_m_add_candidate(
                    candidate_map,
                    combo,
                    pick_count,
                    total_numbers,
                    "ab_union",
                    source_numbers=union_pool,
                    heuristic_score=combo_score,
                )

        theoretical_hit_rate = hit_probability_for(config, pick_count)
        fair_odds = 1 / theoretical_hit_rate if theoretical_hit_rate > 0 else 0
        break_even_hit_rate = 1 / float(odds)
        candidates: list[dict[str, Any]] = []
        for raw_item in candidate_map.values():
            numbers = tuple(int(number) for number in raw_item["numbers"])
            stats = ticket_stats_from_draw_sets(
                draw_sets_oldest,
                bonus_values_oldest,
                recent_draw_sets,
                recent_bonus_values,
                numbers,
                None,
                stats_index=stats_index,
            )
            heuristic_scores = [parse_float(value, 0) for value in raw_item.get("heuristicScores") or []]
            source_types = set(raw_item.get("sourceTypes") or set())
            source_numbers = sorted({int(number) for number in raw_item.get("sourceNumbers") or set()})
            source_label = prediction_panel_m_source_label(source_types)
            candidates.append(
                {
                    "numbers": list(numbers),
                    "bonusNumber": None,
                    "mode": "main",
                    "pickCount": pick_count,
                    "panel": PREDICTION_PANEL_M,
                    "label": f"C计划 {pick_count}码低组候选",
                    "sourcePanel": "ab_history_lowgroup",
                    "sourcePanels": [PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B],
                    "sourceCoreTicketLabels": [
                        PREDICTION_PANEL_M_SOURCE_LABELS[source_type]
                        for source_type in PREDICTION_PANEL_M_SOURCE_PRIORITY
                        if source_type in source_types
                    ],
                    "structureType": f"m_lowgroup_p{pick_count}",
                    "structureLabel": f"{pick_count}码低组数审计",
                    "derivedRule": source_label,
                    "auditSourceLabel": source_label,
                    "sourcePoolNumbers": source_numbers,
                    "sourcePoolCount": len(source_numbers),
                    "coreNumbers": list(numbers),
                    "companionNumbers": [],
                    "heuristicScore": sum(heuristic_scores) / max(len(heuristic_scores), 1),
                    **stats,
                    "theoreticalHitRate": theoretical_hit_rate,
                    "fairOdds": fair_odds,
                    "odds": float(odds),
                    "breakEvenHitRate": break_even_hit_rate,
                    "evAtOdds": theoretical_hit_rate * float(odds) - 1,
                    "chasePeriods": PREDICTION_TICKET_CHASE_PERIODS,
                    "missAllProbability": (1 - theoretical_hit_rate) ** PREDICTION_TICKET_CHASE_PERIODS,
                    "sampleWarning": draw_count < 500 or len(recent_draw_sets) < 200,
                    "ticketLabel": "-".join(str(number) for number in numbers),
                }
            )

        if not candidates:
            continue
        recent_edge_values = [
            parse_float(item.get("recentHitRate"), 0) - parse_float(item.get("breakEvenHitRate"), 0)
            for item in candidates
        ]
        full_edge_values = [
            parse_float(item.get("hitRate"), 0) - parse_float(item.get("theoreticalHitRate"), 0)
            for item in candidates
        ]
        ci_edge_values = [
            parse_float((item.get("recentHitRateCi") or [0])[0], 0) - parse_float(item.get("theoreticalHitRate"), 0)
            for item in candidates
        ]
        heuristic_values = [parse_float(item.get("heuristicScore"), 0) for item in candidates]
        max_miss_values = [parse_float(item.get("maxMiss"), 0) for item in candidates]
        current_miss_values = [parse_float(item.get("currentMiss"), 0) for item in candidates]
        max_miss_span = max(max_miss_values) - min(max_miss_values)
        current_miss_span = max(current_miss_values) - min(current_miss_values)
        for item, recent_edge, full_edge, ci_edge in zip(
            candidates,
            recent_edge_values,
            full_edge_values,
            ci_edge_values,
        ):
            max_miss_score = 1 - normalize_score(parse_float(item.get("maxMiss"), 0), max_miss_values) if max_miss_span > 0 else 0.5
            current_miss_score = (
                1 - normalize_score(parse_float(item.get("currentMiss"), 0), current_miss_values)
                if current_miss_span > 0
                else 0.5
            )
            source_bonus = min(0.10, 0.025 * len(item.get("sourceCoreTicketLabels") or []))
            score = (
                0.30 * normalize_score(recent_edge, recent_edge_values)
                + 0.22 * normalize_score(full_edge, full_edge_values)
                + 0.10 * normalize_score(ci_edge, ci_edge_values)
                + 0.16 * max_miss_score
                + 0.10 * current_miss_score
                + 0.12 * normalize_score(parse_float(item.get("heuristicScore"), 0), heuristic_values)
                + source_bonus
            )
            item["score"] = score
            item["auditScore"] = score
            item["followDecision"] = prediction_panel_m_follow_decision(item)
        candidates.sort(
            key=lambda item: (
                -parse_float(item.get("score"), 0),
                -parse_float(item.get("recentHitRate"), 0),
                parse_int(item.get("maxMiss"), 0),
                parse_int(item.get("currentMiss"), 0),
                item.get("numbers") or [],
            )
        )
        selected = prediction_panel_m_select_diverse(
            candidates[:PREDICTION_PANEL_M_PREFILTER_LIMIT],
            pick_count,
            PREDICTION_PANEL_M_TICKETS_PER_PICK,
        )
        if include_staking_simulation:
            for item in selected:
                item["stakingSimulation"] = prediction_ticket_staking_simulation(rows, item, config)
        result.extend(selected)
    return result


def prediction_panel_d_add_candidate(
    candidates: dict[tuple[str, int, tuple[int, ...]], dict[str, Any]],
    numbers: Iterable[Any],
    pick_count: int,
    total_numbers: int,
    rule_key: str,
    *,
    source_panels: Iterable[str] | None = None,
    source_labels: Iterable[str] | None = None,
    source_numbers: Iterable[Any] | None = None,
    heuristic_score: float = 0,
) -> None:
    key = prediction_panel_m_candidate_key(numbers, pick_count, total_numbers)
    if not key:
        return
    item_key = (rule_key, pick_count, key)
    item = candidates.setdefault(
        item_key,
        {
            "numbers": key,
            "ruleKey": rule_key,
            "pickCount": pick_count,
            "sourcePanels": set(),
            "sourceLabels": [],
            "sourceNumbers": set(),
            "heuristicScores": [],
        },
    )
    for panel in source_panels or []:
        panel_key = prediction_panel_from_value(panel)
        if panel_key:
            item["sourcePanels"].add(panel_key)
    for label in source_labels or []:
        text = str(label or "").strip()
        if text and text not in item["sourceLabels"]:
            item["sourceLabels"].append(text)
    for number in source_numbers or key:
        parsed = parse_int(number, 0)
        if 1 <= parsed <= total_numbers:
            item["sourceNumbers"].add(parsed)
    item["heuristicScores"].append(float(heuristic_score))


def prediction_panel_d_ticket_sources(
    tickets_by_panel: list[tuple[str, list[dict[str, Any]]]],
    total_numbers: int,
) -> tuple[dict[int, set[str]], dict[int, int], dict[int, list[str]]]:
    panels_by_number: dict[int, set[str]] = {}
    counts_by_number: dict[int, int] = {}
    labels_by_number: dict[int, list[str]] = {}
    for panel, tickets in tickets_by_panel:
        panel_key = prediction_panel_from_value(panel)
        for ticket in tickets:
            if not isinstance(ticket, dict) or str(ticket.get("mode") or "main") != "main":
                continue
            label = str(ticket.get("ticketLabel") or "-".join(str(number) for number in ticket.get("numbers") or []))
            for number in ticket.get("numbers") or []:
                parsed = parse_int(number, 0)
                if not 1 <= parsed <= total_numbers:
                    continue
                panels_by_number.setdefault(parsed, set()).add(panel_key)
                counts_by_number[parsed] = counts_by_number.get(parsed, 0) + 1
                bucket = labels_by_number.setdefault(parsed, [])
                if label and label not in bucket:
                    bucket.append(label)
    return panels_by_number, counts_by_number, labels_by_number


def prediction_panel_d_observation_tickets(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    a_tickets: list[dict[str, Any]],
    b_tickets: list[dict[str, Any]],
    m_tickets: list[dict[str, Any]],
    frequency: dict[int, dict[str, Any]],
    recent_counts: dict[int, int],
    recent_window: int,
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    *,
    stats_index: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    game_key = str(config["key"])
    total_numbers = int(config["totalNumbers"])
    draw_count = len(rows)
    number_range = list(range(1, total_numbers + 1))
    scored = scored_numbers(
        number_range,
        PREDICTION_NUMBER_WEIGHTS[0],
        frequency,
        recent_counts,
        recent_window,
        draw_count,
    )
    score_values = [parse_float(item.get("score"), 0) for item in scored]
    max_score = max(score_values, default=1) or 1
    score_by_number = {int(item["number"]): parse_float(item.get("score"), 0) / max_score for item in scored}
    miss_by_number = {
        number: parse_int((frequency.get(number) or {}).get("currentMiss"), 0)
        for number in number_range
    }
    hit_rate_by_number = {
        number: parse_float((frequency.get(number) or {}).get("hitRate"), 0)
        for number in number_range
    }
    recent_rate_by_number = {
        number: (parse_int(recent_counts.get(number), 0) / recent_window if recent_window else 0)
        for number in number_range
    }
    source_tickets = [
        (PREDICTION_PANEL_DEFAULT, a_tickets),
        (PREDICTION_PANEL_B, b_tickets),
        (PREDICTION_PANEL_M, m_tickets),
    ]
    panels_by_number, source_counts_by_number, labels_by_number = prediction_panel_d_ticket_sources(
        source_tickets,
        total_numbers,
    )
    candidates: dict[tuple[str, int, tuple[int, ...]], dict[str, Any]] = {}

    def combo_score(numbers: Iterable[int]) -> float:
        values = [score_by_number.get(int(number), 0.0) for number in numbers]
        recent_values = [recent_rate_by_number.get(int(number), 0.0) for number in numbers]
        miss_values = [miss_by_number.get(int(number), 0) for number in numbers]
        source_values = [len(panels_by_number.get(int(number), set())) / 3 for number in numbers]
        return (
            0.40 * (sum(values) / max(len(values), 1))
            + 0.24 * (sum(recent_values) / max(len(recent_values), 1))
            + 0.18 * (sum(source_values) / max(len(source_values), 1))
            + 0.18 * normalize_score(sum(miss_values) / max(len(miss_values), 1), list(miss_by_number.values()))
        )

    def source_meta(numbers: Iterable[int]) -> tuple[list[str], list[str]]:
        panels: set[str] = set()
        labels: list[str] = []
        for number in numbers:
            panels.update(panels_by_number.get(int(number), set()))
            for label in labels_by_number.get(int(number), [])[:3]:
                if label not in labels:
                    labels.append(label)
        return sorted(panels), labels[:6]

    consensus_pool = sorted(
        number_range,
        key=lambda number: (
            -len(panels_by_number.get(number, set())),
            -source_counts_by_number.get(number, 0),
            -score_by_number.get(number, 0),
            number,
        ),
    )
    hot_pool = sorted(
        number_range,
        key=lambda number: (
            -recent_rate_by_number.get(number, 0),
            -score_by_number.get(number, 0),
            number,
        ),
    )
    reverse_pool = sorted(
        number_range,
        key=lambda number: (
            -miss_by_number.get(number, 0),
            -hit_rate_by_number.get(number, 0),
            -score_by_number.get(number, 0),
            number,
        ),
    )

    for pick_count in PREDICTION_PANEL_D_PICK_COUNTS:
        if not DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(pick_count):
            continue
        pool_size = PREDICTION_PANEL_D_POOL_SIZE_BY_PICK.get(pick_count, 16)

        for combo in combinations(consensus_pool[:pool_size], pick_count):
            panels, labels = source_meta(combo)
            prediction_panel_d_add_candidate(
                candidates,
                combo,
                pick_count,
                total_numbers,
                "consensus",
                source_panels=panels,
                source_labels=labels or [f"ABC共识池{pick_count}码"],
                source_numbers=consensus_pool[:pool_size],
                heuristic_score=combo_score(combo),
            )

        c_like_tickets = [
            ticket
            for ticket in m_tickets
            if isinstance(ticket, dict) and str(ticket.get("mode") or "main") == "main"
        ]
        if not c_like_tickets:
            c_like_tickets = [
                ticket
                for ticket in [*a_tickets, *b_tickets]
                if isinstance(ticket, dict) and str(ticket.get("mode") or "main") == "main"
            ]
        for ticket in c_like_tickets:
            source_numbers = [
                parse_int(number, 0)
                for number in ticket.get("numbers") or []
                if 1 <= parse_int(number, 0) <= total_numbers
            ]
            if not source_numbers:
                continue
            source_label = str(ticket.get("ticketLabel") or "-".join(str(number) for number in source_numbers))
            if len(source_numbers) >= pick_count:
                for combo in combinations(sorted(set(source_numbers)), pick_count):
                    prediction_panel_d_add_candidate(
                        candidates,
                        combo,
                        pick_count,
                        total_numbers,
                        "decompose",
                        source_panels=[str(ticket.get("panel") or PREDICTION_PANEL_M)],
                        source_labels=[source_label],
                        source_numbers=source_numbers,
                        heuristic_score=combo_score(combo) + 0.08,
                    )
            else:
                extension_pool = [number for number in [*hot_pool, *reverse_pool] if number not in set(source_numbers)]
                for extension in extension_pool[: min(12, len(extension_pool))]:
                    combo = tuple(sorted({*source_numbers, extension}))
                    if len(combo) == pick_count:
                        prediction_panel_d_add_candidate(
                            candidates,
                            combo,
                            pick_count,
                            total_numbers,
                            "decompose",
                            source_panels=[str(ticket.get("panel") or PREDICTION_PANEL_M)],
                            source_labels=[source_label],
                            source_numbers=[*source_numbers, extension],
                            heuristic_score=combo_score(combo),
                        )

        for combo in combinations(reverse_pool[:pool_size], pick_count):
            panels, labels = source_meta(combo)
            prediction_panel_d_add_candidate(
                candidates,
                combo,
                pick_count,
                total_numbers,
                "reverse",
                source_panels=panels,
                source_labels=labels or [f"稳定遗漏池{pick_count}码"],
                source_numbers=reverse_pool[:pool_size],
                heuristic_score=combo_score(combo) + 0.05,
            )

        for start in range(1, total_numbers - pick_count + 2):
            combo = tuple(range(start, start + pick_count))
            panels, labels = source_meta(combo)
            prediction_panel_d_add_candidate(
                candidates,
                combo,
                pick_count,
                total_numbers,
                "shape",
                source_panels=panels,
                source_labels=labels or [f"{pick_count}连形态"],
                source_numbers=combo,
                heuristic_score=combo_score(combo) + 0.04,
            )
        if pick_count == 3:
            for anchor in consensus_pool[: min(12, len(consensus_pool))]:
                for distance in (10, 20):
                    combo = tuple(sorted({anchor, anchor + distance, anchor - distance}))
                    if len(combo) == 3 and all(1 <= number <= total_numbers for number in combo):
                        panels, labels = source_meta(combo)
                        prediction_panel_d_add_candidate(
                            candidates,
                            combo,
                            pick_count,
                            total_numbers,
                            "shape",
                            source_panels=panels,
                            source_labels=labels or [f"对称间隔{distance}"],
                            source_numbers=combo,
                            heuristic_score=combo_score(combo),
                        )

    raw_items = list(candidates.values())
    if not raw_items:
        return []

    evaluated: list[dict[str, Any]] = []
    for raw_item in raw_items:
        pick_count = parse_int(raw_item.get("pickCount"), len(raw_item.get("numbers") or []))
        odds = parse_float(DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(pick_count), 0)
        if odds <= 1:
            continue
        numbers = tuple(int(number) for number in raw_item.get("numbers") or [])
        theoretical_hit_rate = hit_probability_for(config, pick_count)
        fair_odds = 1 / theoretical_hit_rate if theoretical_hit_rate > 0 else 0
        break_even_hit_rate = 1 / odds if odds > 0 else 0
        stats = ticket_stats_from_draw_sets(
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            numbers,
            None,
            stats_index=stats_index,
        )
        rule_key = str(raw_item.get("ruleKey") or "consensus")
        heuristic_scores = [parse_float(value, 0) for value in raw_item.get("heuristicScores") or []]
        heuristic_score = sum(heuristic_scores) / max(len(heuristic_scores), 1)
        source_panels = sorted(raw_item.get("sourcePanels") or [])
        source_bonus = min(0.18, 0.06 * len(source_panels))
        recent_ratio = (
            parse_float(stats.get("recentHitRate"), 0) / theoretical_hit_rate
            if theoretical_hit_rate > 0
            else 0
        )
        full_ratio = (
            parse_float(stats.get("hitRate"), 0) / theoretical_hit_rate
            if theoretical_hit_rate > 0
            else 0
        )
        miss_score = normalize_score(parse_int(stats.get("currentMiss"), 0), [*miss_by_number.values(), 1])
        rule_priority = PREDICTION_PANEL_D_RULE_PRIORITY_NEW.get(rule_key, 0.75)
        score = (
            0.30 * rule_priority
            + 0.20 * min(1.5, recent_ratio) / 1.5
            + 0.16 * min(1.5, full_ratio) / 1.5
            + 0.16 * heuristic_score
            + 0.10 * miss_score
            + 0.08 * source_bonus
        )
        label = dict(PREDICTION_PANEL_D_RULES).get(rule_key, rule_key)
        item = {
            "numbers": list(numbers),
            "bonusNumber": None,
            "mode": "main",
            "pickCount": pick_count,
            "panel": PREDICTION_PANEL_D,
            "label": f"D计划 {label}{pick_count}码观察",
            "sourcePanel": "abc_observation",
            "sourcePanels": source_panels or [PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B, PREDICTION_PANEL_M],
            "sourceCoreTicketLabels": list(raw_item.get("sourceLabels") or [])[:8],
            "structureType": f"d_{rule_key}_p{pick_count}",
            "structureLabel": f"{label}规则 {pick_count}码",
            "derivedRule": rule_key,
            "auditSourceLabel": label,
            "sourcePoolNumbers": sorted(raw_item.get("sourceNumbers") or []),
            "sourcePoolCount": len(raw_item.get("sourceNumbers") or []),
            "coreNumbers": list(numbers),
            "companionNumbers": [],
            "heuristicScore": heuristic_score,
            **stats,
            "theoreticalHitRate": theoretical_hit_rate,
            "fairOdds": fair_odds,
            "odds": float(odds),
            "breakEvenHitRate": break_even_hit_rate,
            "evAtOdds": theoretical_hit_rate * float(odds) - 1,
            "chasePeriods": PREDICTION_TICKET_CHASE_PERIODS,
            "missAllProbability": (1 - theoretical_hit_rate) ** PREDICTION_TICKET_CHASE_PERIODS,
            "sampleWarning": draw_count < 500 or parse_int(stats.get("recentWindow"), 0) < 200,
            "ticketLabel": "-".join(str(number) for number in numbers),
            "score": score,
            "auditScore": score,
            "followDecision": "观察：新D计划先跑完整开奖日，不直接投注",
        }
        evaluated.append(item)

    selected: list[dict[str, Any]] = []
    selected_numbers: set[tuple[int, ...]] = set()
    for pick_count in PREDICTION_PANEL_D_PICK_COUNTS:
        pick_items = [item for item in evaluated if parse_int(item.get("pickCount"), 0) == pick_count]
        for rule_key, _rule_label in PREDICTION_PANEL_D_RULES:
            rule_items = [
                item
                for item in pick_items
                if str(item.get("derivedRule") or "") == rule_key
            ]
            rule_items.sort(
                key=lambda item: (
                    -parse_float(item.get("score"), 0),
                    -parse_float(item.get("recentHitRate"), 0),
                    parse_int(item.get("maxMiss"), 0),
                    item.get("numbers") or [],
                )
            )
            for item in rule_items:
                key = tuple(int(number) for number in item.get("numbers") or [])
                if key in selected_numbers:
                    continue
                selected.append(item)
                selected_numbers.add(key)
                break
        if sum(1 for item in selected if parse_int(item.get("pickCount"), 0) == pick_count) < len(PREDICTION_PANEL_D_RULES):
            pick_items.sort(
                key=lambda item: (
                    -parse_float(item.get("score"), 0),
                    -parse_float(item.get("recentHitRate"), 0),
                    item.get("numbers") or [],
                )
            )
            for item in pick_items:
                key = tuple(int(number) for number in item.get("numbers") or [])
                if key in selected_numbers:
                    continue
                selected.append(item)
                selected_numbers.add(key)
                if sum(1 for candidate in selected if parse_int(candidate.get("pickCount"), 0) == pick_count) >= len(PREDICTION_PANEL_D_RULES):
                    break

    selected.sort(
        key=lambda item: (
            parse_int(item.get("pickCount"), 0),
            next(
                (index for index, (rule_key, _label) in enumerate(PREDICTION_PANEL_D_RULES) if rule_key == str(item.get("derivedRule") or "")),
                99,
            ),
            -parse_float(item.get("score"), 0),
        )
    )
    return selected


def prediction_kill_numbers_from_tickets(tickets: list[dict[str, Any]]) -> list[int]:
    numbers: set[int] = set()
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        for number in ticket.get("numbers") or []:
            parsed = parse_int(number, 0)
            if parsed > 0:
                numbers.add(parsed)
    return sorted(numbers)


def prediction_source_ticket_summaries(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for index, ticket in enumerate(tickets, start=1):
        if not isinstance(ticket, dict):
            continue
        numbers = [
            parse_int(number, 0)
            for number in ticket.get("numbers") or []
            if parse_int(number, 0) > 0
        ]
        if not numbers:
            continue
        summaries.append(
            {
                "index": index,
                "panel": prediction_panel_from_value(ticket.get("panel")),
                "label": str(ticket.get("label") or ""),
                "ticketLabel": str(ticket.get("ticketLabel") or "-".join(str(number) for number in numbers)),
                "numbers": numbers,
                "structureType": str(ticket.get("structureType") or ""),
                "structureLabel": str(ticket.get("structureLabel") or ""),
                "coreNumbers": [parse_int(number, 0) for number in ticket.get("coreNumbers") or [] if parse_int(number, 0) > 0],
                "companionNumbers": [
                    parse_int(number, 0)
                    for number in ticket.get("companionNumbers") or []
                    if parse_int(number, 0) > 0
                ],
            }
        )
    return summaries


def prediction_panel_c_ticket_sources(
    tickets: list[dict[str, Any]],
    source_panel: str,
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        if str(ticket.get("mode") or "main") != "main":
            continue
        numbers = sorted(
            {
                parse_int(number, 0)
                for number in ticket.get("numbers") or []
                if parse_int(number, 0) > 0
            }
        )
        if not numbers:
            continue
        sources.append(
            {
                "panel": source_panel,
                "numbers": numbers,
                "pickCount": parse_int(ticket.get("pickCount"), len(numbers)),
                "score": parse_float(ticket.get("score"), 0),
                "label": str(ticket.get("ticketLabel") or "-".join(str(number) for number in numbers)),
                "strategyLabel": str(ticket.get("label") or ""),
            }
        )
    return sources


def prediction_panel_c_core_pairs(
    a_tickets: list[dict[str, Any]],
    b_tickets: list[dict[str, Any]],
    total_numbers: int,
) -> list[dict[str, Any]]:
    sources = prediction_panel_c_ticket_sources(a_tickets, PREDICTION_PANEL_DEFAULT) + prediction_panel_c_ticket_sources(
        b_tickets,
        PREDICTION_PANEL_B,
    )
    number_scores: dict[int, list[float]] = {}
    number_panels: dict[int, set[str]] = {}
    for source in sources:
        score = parse_float(source.get("score"), 0)
        panel = str(source.get("panel") or "")
        for number in source.get("numbers") or []:
            if 1 <= int(number) <= total_numbers:
                number_scores.setdefault(int(number), []).append(score)
                number_panels.setdefault(int(number), set()).add(panel)

    pairs: dict[tuple[int, int], dict[str, Any]] = {}
    for source in sources:
        numbers = [number for number in source.get("numbers") or [] if 1 <= int(number) <= total_numbers]
        if len(numbers) != 2 or parse_int(source.get("pickCount"), len(numbers)) != 2:
            continue
        pair = tuple(sorted(int(number) for number in numbers))
        item = pairs.setdefault(
            pair,
            {
                "numbers": pair,
                "sourcePanels": set(),
                "sourceLabels": [],
                "scoreParts": [],
            },
        )
        item["sourcePanels"].add(str(source.get("panel") or ""))
        source_label = str(source.get("label") or "")
        if source_label and source_label not in item["sourceLabels"]:
            item["sourceLabels"].append(source_label)
        item["scoreParts"].append(parse_float(source.get("score"), 0))

    ranked_numbers = sorted(
        number_scores,
        key=lambda number: (
            -(sum(number_scores[number]) / max(len(number_scores[number]), 1)),
            number,
        ),
    )[:12]
    for first, second in combinations(ranked_numbers, 2):
        pair = tuple(sorted((int(first), int(second))))
        if pair[0] == pair[1]:
            continue
        if pair not in pairs:
            first_score = sum(number_scores.get(pair[0], [0])) / max(len(number_scores.get(pair[0], [])), 1)
            second_score = sum(number_scores.get(pair[1], [0])) / max(len(number_scores.get(pair[1], [])), 1)
            pairs[pair] = {
                "numbers": pair,
                "sourcePanels": set(number_panels.get(pair[0], set()) | number_panels.get(pair[1], set())),
                "sourceLabels": [f"{pair[0]}-{pair[1]}"],
                "scoreParts": [(first_score + second_score) / 2],
            }

    result: list[dict[str, Any]] = []
    for pair, item in pairs.items():
        score_parts = [parse_float(value, 0) for value in item.get("scoreParts") or []]
        source_panels = sorted(panel for panel in item.get("sourcePanels", set()) if panel)
        result.append(
            {
                "numbers": pair,
                "sourcePanels": source_panels,
                "sourceLabels": item.get("sourceLabels") or [f"{pair[0]}-{pair[1]}"],
                "score": sum(score_parts) / max(len(score_parts), 1),
                "sourceCount": len(score_parts),
            }
        )
    result.sort(
        key=lambda item: (
            -parse_float(item.get("score"), 0),
            -parse_int(item.get("sourceCount"), 0),
            item.get("numbers") or (),
        )
    )
    return result[:PREDICTION_PANEL_C_CORE_PAIR_LIMIT]


def prediction_panel_c_cohit_scores(
    rows: list[dict[str, Any]],
    total_numbers: int,
    eval_window: int,
    core_numbers: set[int] | None = None,
) -> dict[int, dict[int, dict[str, Any]]]:
    eval_rows = rows[:eval_window]
    draw_count = len(eval_rows)
    draw_sets = [set(row.get("numbers") or []) for row in eval_rows]
    number_hits = {
        number: sum(1 for draw_set in draw_sets if number in draw_set)
        for number in range(1, total_numbers + 1)
    }
    scores: dict[int, dict[int, dict[str, Any]]] = {}
    if core_numbers:
        cores = sorted(number for number in core_numbers if 1 <= number <= total_numbers)
    else:
        cores = list(range(1, total_numbers + 1))
    for core in cores:
        core_hits = number_hits.get(core, 0)
        core_scores: dict[int, dict[str, Any]] = {}
        if core_hits <= 0 or draw_count <= 0:
            scores[core] = core_scores
            continue
        for companion in range(1, total_numbers + 1):
            if companion == core:
                continue
            companion_hits = number_hits.get(companion, 0)
            co_hits = sum(1 for draw_set in draw_sets if core in draw_set and companion in draw_set)
            conditional = co_hits / core_hits if core_hits else 0
            baseline = companion_hits / draw_count if draw_count else 0
            lift = conditional - baseline
            support = min(co_hits, 30) / 30
            score = 0.58 * lift + 0.27 * conditional + 0.15 * support
            core_scores[companion] = {
                "score": score,
                "coHits": co_hits,
                "conditionalRate": conditional,
                "baselineRate": baseline,
                "lift": lift,
            }
        scores[core] = core_scores
    return scores


def prediction_panel_c_valid_companions(
    core: int,
    candidates: list[int] | set[int],
    total_numbers: int,
    excluded: set[int],
    cohit_scores: dict[int, dict[int, dict[str, Any]]],
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for candidate in sorted(set(int(number) for number in candidates)):
        if candidate < 1 or candidate > total_numbers or candidate in excluded:
            continue
        score_item = cohit_scores.get(core, {}).get(candidate, {})
        items.append(
            {
                "number": candidate,
                "score": parse_float(score_item.get("score"), 0),
                "coHits": parse_int(score_item.get("coHits"), 0),
                "conditionalRate": parse_float(score_item.get("conditionalRate"), 0),
                "baselineRate": parse_float(score_item.get("baselineRate"), 0),
                "lift": parse_float(score_item.get("lift"), 0),
            }
        )
    items.sort(
        key=lambda item: (
            -parse_float(item.get("score"), 0),
            -parse_int(item.get("coHits"), 0),
            parse_int(item.get("number"), 0),
        )
    )
    return items[:limit] if limit is not None else items


def prediction_panel_c_candidates_for_structure(
    structure_type: str,
    core_pair: tuple[int, int],
    total_numbers: int,
    cohit_scores: dict[int, dict[int, dict[str, Any]]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    first, second = core_pair
    excluded = {first, second}

    def offset_candidates(core: int, offsets: tuple[int, ...]) -> set[int]:
        result: set[int] = set()
        for offset in offsets:
            result.add(core - offset)
            result.add(core + offset)
        return result

    if structure_type == "adjacent_1":
        first_items = prediction_panel_c_valid_companions(first, {first - 1, first + 1}, total_numbers, excluded, cohit_scores)
        second_items = prediction_panel_c_valid_companions(second, {second - 1, second + 1}, total_numbers, excluded, cohit_scores)
    elif structure_type == "offset_10":
        first_items = prediction_panel_c_valid_companions(first, {first - 10, first + 10}, total_numbers, excluded, cohit_scores)
        second_items = prediction_panel_c_valid_companions(second, {second - 10, second + 10}, total_numbers, excluded, cohit_scores)
    elif structure_type == "offset_d":
        first_items = prediction_panel_c_valid_companions(
            first,
            offset_candidates(first, PREDICTION_PANEL_C_OFFSETS),
            total_numbers,
            excluded,
            cohit_scores,
            limit=PREDICTION_PANEL_C_COMPANION_LIMIT,
        )
        second_items = prediction_panel_c_valid_companions(
            second,
            offset_candidates(second, PREDICTION_PANEL_C_OFFSETS),
            total_numbers,
            excluded,
            cohit_scores,
            limit=PREDICTION_PANEL_C_COMPANION_LIMIT,
        )
    elif structure_type == "band_5_10":
        first_items = prediction_panel_c_valid_companions(
            first,
            offset_candidates(first, PREDICTION_PANEL_C_BAND_DISTANCES),
            total_numbers,
            excluded,
            cohit_scores,
            limit=PREDICTION_PANEL_C_COMPANION_LIMIT,
        )
        second_items = prediction_panel_c_valid_companions(
            second,
            offset_candidates(second, PREDICTION_PANEL_C_BAND_DISTANCES),
            total_numbers,
            excluded,
            cohit_scores,
            limit=PREDICTION_PANEL_C_COMPANION_LIMIT,
        )
    elif structure_type == "same_tail":
        first_items = prediction_panel_c_valid_companions(
            first,
            {number for number in range(1, total_numbers + 1) if number != first and number % 10 == first % 10},
            total_numbers,
            excluded,
            cohit_scores,
            limit=PREDICTION_PANEL_C_COMPANION_LIMIT,
        )
        second_items = prediction_panel_c_valid_companions(
            second,
            {number for number in range(1, total_numbers + 1) if number != second and number % 10 == second % 10},
            total_numbers,
            excluded,
            cohit_scores,
            limit=PREDICTION_PANEL_C_COMPANION_LIMIT,
        )
    elif structure_type == "cohit_free":
        all_candidates = set(range(1, total_numbers + 1))
        first_items = prediction_panel_c_valid_companions(
            first,
            all_candidates,
            total_numbers,
            excluded,
            cohit_scores,
            limit=PREDICTION_PANEL_C_COMPANION_LIMIT,
        )
        second_items = prediction_panel_c_valid_companions(
            second,
            all_candidates,
            total_numbers,
            excluded,
            cohit_scores,
            limit=PREDICTION_PANEL_C_COMPANION_LIMIT,
        )
    else:
        return []

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for first_item in first_items:
        for second_item in second_items:
            if parse_int(first_item.get("number"), 0) == parse_int(second_item.get("number"), 0):
                continue
            pairs.append((first_item, second_item))
    return pairs


def prediction_panel_c_structure_tickets(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    a_tickets: list[dict[str, Any]],
    b_tickets: list[dict[str, Any]],
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    stats_index: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    game_key = str(config["key"])
    odds = DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(4)
    if not odds:
        return []

    total_numbers = int(config["totalNumbers"])
    draw_count = len(rows)
    recent_eval_window = min(PREDICTION_TICKET_BACKTEST_WINDOW, draw_count)
    theoretical_hit_rate = hit_probability_for(config, 4)
    fair_odds = 1 / theoretical_hit_rate if theoretical_hit_rate > 0 else 0
    break_even_hit_rate = 1 / float(odds)
    core_pairs = prediction_panel_c_core_pairs(a_tickets, b_tickets, total_numbers)
    if not core_pairs:
        return []

    cohit_core_numbers = {
        parse_int(number, 0)
        for item in core_pairs
        for number in (item.get("numbers") or [])
    }
    cohit_scores = prediction_panel_c_cohit_scores(rows, total_numbers, recent_eval_window, cohit_core_numbers)
    recent_sets = recent_draw_sets
    recent_window_for_prefilter = (
        int(stats_index.get("recentWindow") or 0)
        if isinstance(stats_index, dict)
        else len(recent_sets)
    )
    candidates_by_numbers: dict[tuple[int, ...], dict[str, Any]] = {}
    for core_item in core_pairs:
        core_pair = tuple(int(number) for number in core_item.get("numbers") or [])
        if len(core_pair) != 2:
            continue
        for structure_type in PREDICTION_PANEL_C_STRUCTURE_LABELS:
            companion_pairs = prediction_panel_c_candidates_for_structure(
                structure_type,
                core_pair,
                total_numbers,
                cohit_scores,
            )
            for first_companion, second_companion in companion_pairs:
                companion_numbers = (
                    parse_int(first_companion.get("number"), 0),
                    parse_int(second_companion.get("number"), 0),
                )
                numbers = tuple(sorted((*core_pair, *companion_numbers)))
                if len(numbers) != 4 or any(number < 1 or number > total_numbers for number in numbers):
                    continue
                companion_score = (
                    parse_float(first_companion.get("score"), 0) + parse_float(second_companion.get("score"), 0)
                ) / 2
                recent_hits = (
                    ticket_recent_hits_from_index(stats_index, numbers, None)
                    if isinstance(stats_index, dict)
                    else sum(1 for draw_set in recent_sets if all(number in draw_set for number in numbers))
                )
                recent_hit_rate = recent_hits / recent_window_for_prefilter if recent_window_for_prefilter else 0
                item = {
                    "numbers": list(numbers),
                    "bonusNumber": None,
                    "mode": "main",
                    "pickCount": 4,
                    "panel": PREDICTION_PANEL_C,
                    "sourcePanel": "ab",
                    "sourcePanels": core_item.get("sourcePanels") or [PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B],
                    "sourceCoreTicketLabels": core_item.get("sourceLabels") or [],
                    "structureType": structure_type,
                    "structureLabel": PREDICTION_PANEL_C_STRUCTURE_LABELS[structure_type],
                    "coreNumbers": list(core_pair),
                    "companionNumbers": list(companion_numbers),
                    "sourceCoreScore": parse_float(core_item.get("score"), 0),
                    "companionScore": companion_score,
                    "structurePriority": PREDICTION_PANEL_C_STRUCTURE_PRIORITY.get(structure_type, 0),
                    "recentWindow": recent_window_for_prefilter,
                    "recentHits": recent_hits,
                    "recentHitRate": recent_hit_rate,
                    "prefilterScore": 0,
                }
                existing = candidates_by_numbers.get(numbers)
                if existing is None or (
                    parse_float(item.get("structurePriority"), 0),
                    parse_float(item.get("companionScore"), 0),
                    parse_float(item.get("sourceCoreScore"), 0),
                ) > (
                    parse_float(existing.get("structurePriority"), 0),
                    parse_float(existing.get("companionScore"), 0),
                    parse_float(existing.get("sourceCoreScore"), 0),
                ):
                    candidates_by_numbers[numbers] = item

    candidates = list(candidates_by_numbers.values())
    if not candidates:
        return []

    core_scores = [parse_float(item.get("sourceCoreScore"), 0) for item in candidates]
    companion_scores = [parse_float(item.get("companionScore"), 0) for item in candidates]
    edge_values = [parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate for item in candidates]
    for item in candidates:
        item["prefilterScore"] = (
            0.25 * normalize_score(parse_float(item.get("sourceCoreScore"), 0), core_scores)
            + 0.25 * normalize_score(parse_float(item.get("companionScore"), 0), companion_scores)
            + 0.30 * normalize_score(parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate, edge_values)
            + 0.20 * parse_float(item.get("structurePriority"), 0)
        )

    candidates.sort(
        key=lambda item: (
            -parse_float(item.get("prefilterScore"), 0),
            -parse_float(item.get("structurePriority"), 0),
            -parse_float(item.get("companionScore"), 0),
            item.get("numbers") or [],
        )
    )
    candidates = candidates[:PREDICTION_PANEL_C_PREFILTER_LIMIT]

    miss_values: list[int] = []
    for item in candidates:
        stats = ticket_stats_from_draw_sets(
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            tuple(int(number) for number in item.get("numbers") or []),
            None,
            stats_index=stats_index,
        )
        item.update(stats)
        miss_values.append(parse_int(item.get("currentMiss"), 0))

    core_scores = [parse_float(item.get("sourceCoreScore"), 0) for item in candidates]
    companion_scores = [parse_float(item.get("companionScore"), 0) for item in candidates]
    edge_values = [parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate for item in candidates]
    for item in candidates:
        item["score"] = (
            0.22 * normalize_score(parse_float(item.get("sourceCoreScore"), 0), core_scores)
            + 0.22 * normalize_score(parse_float(item.get("companionScore"), 0), companion_scores)
            + 0.22 * normalize_score(parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate, edge_values)
            + 0.16 * normalize_score(parse_int(item.get("currentMiss"), 0), miss_values)
            + 0.18 * parse_float(item.get("structurePriority"), 0)
        )
        item["label"] = f"C {item['structureLabel']}"
        item["theoreticalHitRate"] = theoretical_hit_rate
        item["fairOdds"] = fair_odds
        item["odds"] = float(odds)
        item["breakEvenHitRate"] = break_even_hit_rate
        item["evAtOdds"] = theoretical_hit_rate * float(odds) - 1
        item["chasePeriods"] = PREDICTION_TICKET_CHASE_PERIODS
        item["missAllProbability"] = (1 - theoretical_hit_rate) ** PREDICTION_TICKET_CHASE_PERIODS
        item["sampleWarning"] = draw_count < 500 or parse_int(item.get("recentWindow"), 0) < 200
        item["ticketLabel"] = "-".join(str(number) for number in item["numbers"])

    candidates.sort(
        key=lambda item: (
            -parse_float(item.get("score"), 0),
            -parse_float(item.get("structurePriority"), 0),
            -parse_float(item.get("companionScore"), 0),
            -parse_int(item.get("currentMiss"), 0),
            item.get("numbers") or [],
        )
    )
    return candidates[:PREDICTION_PANEL_C_TOP_COUNT]


def prediction_panel_d_clean_four_tickets(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    excluded_numbers: set[int],
    frequency: dict[int, dict[str, Any]],
    recent_counts: dict[int, int],
    recent_window: int,
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    *,
    panel: str = PREDICTION_PANEL_D,
    top_count: int = PREDICTION_PANEL_D_TOP_COUNT,
    pool_size: int = PREDICTION_PANEL_D_POOL_SIZE,
    prefilter_limit: int = PREDICTION_PANEL_D_PREFILTER_LIMIT,
    label: str = "D ABC杀号四码",
    source_panel: str = "abc",
    source_panels: list[str] | None = None,
    structure_type: str = "kill_abc_four",
    structure_label: str = "ABC杀号四码",
    stats_index: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    game_key = str(config["key"])
    odds = DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(4)
    if not odds:
        return []

    total_numbers = int(config["totalNumbers"])
    draw_count = len(rows)
    clean_numbers = [
        number
        for number in range(1, total_numbers + 1)
        if number not in excluded_numbers
    ]
    if len(clean_numbers) < 4:
        return []

    scored = scored_numbers(
        clean_numbers,
        PREDICTION_NUMBER_WEIGHTS[0],
        frequency,
        recent_counts,
        recent_window,
        draw_count,
    )
    pool = scored[: min(pool_size, len(scored))]
    score_by_number = {int(item["number"]): float(item["score"]) for item in scored}
    miss_by_number = {int(item["number"]): int(item["currentMiss"]) for item in scored}
    recent_by_number = {
        int(item["number"]): parse_int(item.get("recentHits"), 0) / recent_window if recent_window else 0
        for item in scored
    }
    pool_miss_values = [miss_by_number.get(int(item["number"]), 0) for item in scored]
    pool_recent_values = [recent_by_number.get(int(item["number"]), 0.0) for item in scored]
    miss_low = min(pool_miss_values) if pool_miss_values else 0
    miss_high = max(pool_miss_values) if pool_miss_values else 0
    recent_low = min(pool_recent_values) if pool_recent_values else 0.0
    recent_high = max(pool_recent_values) if pool_recent_values else 0.0
    miss_score_by_number = {
        number: ((value - miss_low) / (miss_high - miss_low) if miss_high > miss_low else 0)
        for number, value in miss_by_number.items()
    }
    recent_score_by_number = {
        number: ((value - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0)
        for number, value in recent_by_number.items()
    }

    theoretical_hit_rate = hit_probability_for(config, 4)
    fair_odds = 1 / theoretical_hit_rate if theoretical_hit_rate > 0 else 0
    break_even_hit_rate = 1 / float(odds)
    rough_candidates: list[dict[str, Any]] = []
    for combo in combinations((int(item["number"]) for item in pool), 4):
        numbers = tuple(sorted(combo))
        number_scores = [score_by_number.get(number, 0.0) for number in numbers]
        number_recent = [recent_by_number.get(number, 0.0) for number in numbers]
        rough_score = (
            0.46 * (sum(number_scores) / len(number_scores))
            + 0.34 * (sum(miss_score_by_number.get(number, 0.0) for number in numbers) / len(numbers))
            + 0.20 * (sum(recent_score_by_number.get(number, 0.0) for number in numbers) / len(numbers))
        )
        rough_candidates.append(
            {
                "numbers": list(numbers),
                "roughScore": rough_score,
                "sourceCoreScore": sum(number_scores) / len(number_scores),
                "companionScore": sum(number_recent) / len(number_recent),
            }
        )

    rough_candidates.sort(
        key=lambda item: (
            -parse_float(item.get("roughScore"), 0),
            item.get("numbers") or [],
        )
    )
    candidates = rough_candidates[:prefilter_limit]
    if not candidates:
        return []

    miss_values: list[int] = []
    edge_values: list[float] = []
    for item in candidates:
        stats = ticket_stats_from_draw_sets(
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            tuple(int(number) for number in item.get("numbers") or []),
            None,
            stats_index=stats_index,
        )
        item.update(stats)
        miss_values.append(parse_int(item.get("currentMiss"), 0))
        edge_values.append(parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate)

    rough_scores = [parse_float(item.get("roughScore"), 0) for item in candidates]
    for item in candidates:
        item["score"] = (
            0.36 * normalize_score(parse_float(item.get("roughScore"), 0), rough_scores)
            + 0.34 * normalize_score(parse_int(item.get("currentMiss"), 0), miss_values)
            + 0.30 * normalize_score(parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate, edge_values)
        )
        item["label"] = label
        item["bonusNumber"] = None
        item["mode"] = "main"
        item["pickCount"] = 4
        item["panel"] = panel
        item["sourcePanel"] = source_panel
        item["sourcePanels"] = source_panels or []
        item["structureType"] = structure_type
        item["structureLabel"] = structure_label
        item["coreNumbers"] = []
        item["companionNumbers"] = []
        item["excludedNumbers"] = sorted(excluded_numbers)
        item["theoreticalHitRate"] = theoretical_hit_rate
        item["fairOdds"] = fair_odds
        item["odds"] = float(odds)
        item["breakEvenHitRate"] = break_even_hit_rate
        item["evAtOdds"] = theoretical_hit_rate * float(odds) - 1
        item["chasePeriods"] = PREDICTION_TICKET_CHASE_PERIODS
        item["missAllProbability"] = (1 - theoretical_hit_rate) ** PREDICTION_TICKET_CHASE_PERIODS
        item["sampleWarning"] = draw_count < 500 or parse_int(item.get("recentWindow"), 0) < 200
        item["ticketLabel"] = "-".join(str(number) for number in item["numbers"])

    candidates.sort(
        key=lambda item: (
            -parse_float(item.get("score"), 0),
            -parse_int(item.get("currentMiss"), 0),
            -parse_float(item.get("recentHitRate"), 0),
            item.get("numbers") or [],
        )
    )
    return candidates[:top_count]


def prediction_panel_d_valid_four(numbers: list[int] | tuple[int, ...], total_numbers: int) -> tuple[int, ...] | None:
    parsed: list[int] = []
    for number in numbers:
        value = parse_int(number, 0)
        if value < 1 or value > total_numbers:
            return None
        parsed.append(value)
    unique = tuple(sorted(set(parsed)))
    if len(unique) != 4:
        return None
    return unique


def prediction_panel_d_rule_priority(rule_key: str) -> float:
    for prefix, priority in PREDICTION_PANEL_D_RULE_PRIORITY.items():
        if rule_key.startswith(prefix):
            return float(priority)
    return 0.60


def prediction_panel_d_ab_pair_sources(
    a_tickets: list[dict[str, Any]],
    b_tickets: list[dict[str, Any]],
    total_numbers: int,
) -> list[dict[str, Any]]:
    pairs: dict[tuple[int, int], dict[str, Any]] = {}
    for panel, tickets in (
        (PREDICTION_PANEL_DEFAULT, a_tickets),
        (PREDICTION_PANEL_B, b_tickets),
    ):
        for ticket in tickets:
            if not isinstance(ticket, dict):
                continue
            if str(ticket.get("mode") or "main") != "main":
                continue
            numbers = sorted(
                {
                    parse_int(number, 0)
                    for number in ticket.get("numbers") or []
                    if 1 <= parse_int(number, 0) <= total_numbers
                }
            )
            if len(numbers) != 2 or parse_int(ticket.get("pickCount"), len(numbers)) != 2:
                continue
            pair = tuple(int(number) for number in numbers)
            item = pairs.setdefault(
                pair,
                {
                    "numbers": pair,
                    "sourcePanels": set(),
                    "sourceLabels": [],
                    "scoreParts": [],
                },
            )
            item["sourcePanels"].add(panel)
            label = str(ticket.get("ticketLabel") or "-".join(str(number) for number in pair))
            if label and label not in item["sourceLabels"]:
                item["sourceLabels"].append(label)
            item["scoreParts"].append(parse_float(ticket.get("score"), 0))

    result: list[dict[str, Any]] = []
    for pair, item in pairs.items():
        score_parts = [parse_float(value, 0) for value in item.get("scoreParts") or []]
        result.append(
            {
                "numbers": pair,
                "sourcePanels": sorted(panel for panel in item.get("sourcePanels", set()) if panel),
                "sourceLabels": item.get("sourceLabels") or [f"{pair[0]}-{pair[1]}"],
                "score": sum(score_parts) / max(len(score_parts), 1),
                "sourceCount": len(score_parts),
            }
        )
    result.sort(
        key=lambda item: (
            -parse_float(item.get("score"), 0),
            -parse_int(item.get("sourceCount"), 0),
            item.get("numbers") or (),
        )
    )
    return result[:PREDICTION_PANEL_D_PAIR_SOURCE_LIMIT]


def prediction_panel_d_pair_rule_candidates(pair: tuple[int, int], total_numbers: int) -> list[dict[str, Any]]:
    if len(pair) != 2:
        return []
    left, right = sorted((int(pair[0]), int(pair[1])))
    items: list[dict[str, Any]] = []

    def add(rule_key: str, label: str, numbers: list[int] | tuple[int, ...]) -> None:
        normalized = prediction_panel_d_valid_four(numbers, total_numbers)
        if normalized is None:
            return
        companion = [number for number in normalized if number not in {left, right}]
        items.append(
            {
                "ruleKey": rule_key,
                "structureLabel": label,
                "numbers": normalized,
                "coreNumbers": [left, right],
                "companionNumbers": companion or list(normalized),
            }
        )

    for distance in range(1, 10):
        add(
            f"ab_pm_{distance}",
            f"AB ±{distance} 外扩四码",
            [left - distance, left + distance, right - distance, right + distance],
        )
        add(
            f"ab_shift_plus_{distance}",
            f"AB +{distance} 平移四码",
            [left, right, left + distance, right + distance],
        )
        add(
            f"ab_shift_minus_{distance}",
            f"AB -{distance} 平移四码",
            [left, right, left - distance, right - distance],
        )

    for shift in (10, 20):
        add(f"ab_tail_plus_{shift}", f"AB 同尾 +{shift} 四码", [left, right, left + shift, right + shift])
        add(f"ab_tail_minus_{shift}", f"AB 同尾 -{shift} 四码", [left, right, left - shift, right - shift])

    add("ab_mirror", "AB 镜像四码", [left, right, total_numbers + 1 - left, total_numbers + 1 - right])

    gap = right - left
    if gap >= 4:
        middle = (left + right) // 2
        add("ab_interval_mid_pm1", "AB 中位夹击四码", [left, middle - 1, middle + 1, right])
    if gap >= 6:
        add("ab_interval_thirds", "AB 区间三分四码", [left, left + gap // 3, left + (gap * 2) // 3, right])

    deduped: dict[tuple[int, ...], dict[str, Any]] = {}
    for item in items:
        deduped.setdefault(tuple(item["numbers"]), item)
    return list(deduped.values())


def prediction_panel_d_c_rule_candidates(ticket: dict[str, Any], total_numbers: int) -> list[dict[str, Any]]:
    numbers = prediction_panel_d_valid_four(tuple(parse_int(number, 0) for number in ticket.get("numbers") or []), total_numbers)
    if numbers is None:
        return []
    source_structure = str(ticket.get("structureType") or "unknown")
    source_label = str(ticket.get("structureLabel") or "C四码结构")
    source_core = [
        parse_int(number, 0)
        for number in ticket.get("coreNumbers") or []
        if 1 <= parse_int(number, 0) <= total_numbers
    ]
    source_companion = [
        parse_int(number, 0)
        for number in ticket.get("companionNumbers") or []
        if 1 <= parse_int(number, 0) <= total_numbers
    ]
    items: list[dict[str, Any]] = []

    def add(
        rule_key: str,
        label: str,
        candidate_numbers: list[int] | tuple[int, ...],
        companion_numbers: list[int] | None = None,
    ) -> None:
        normalized = prediction_panel_d_valid_four(candidate_numbers, total_numbers)
        if normalized is None:
            return
        items.append(
            {
                "ruleKey": rule_key,
                "structureLabel": label,
                "numbers": normalized,
                "coreNumbers": source_core or list(numbers),
                "companionNumbers": companion_numbers or source_companion or list(normalized),
            }
        )

    add(
        f"c_original_{source_structure}",
        f"C 原结构：{source_label}",
        numbers,
        source_companion,
    )
    for shift in (1, -1, 10, -10):
        direction = f"+{shift}" if shift > 0 else str(shift)
        add(
            f"c_shift_{'plus' if shift > 0 else 'minus'}_{abs(shift)}_{source_structure}",
            f"C 整体{direction}：{source_label}",
            [number + shift for number in numbers],
            [number + shift for number in numbers],
        )
    add(
        f"c_mirror_{source_structure}",
        f"C 镜像：{source_label}",
        [total_numbers + 1 - number for number in numbers],
        [total_numbers + 1 - number for number in numbers],
    )
    return items


def prediction_panel_d_derived_four_tickets(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    a_tickets: list[dict[str, Any]],
    b_tickets: list[dict[str, Any]],
    c_tickets: list[dict[str, Any]],
    frequency: dict[int, dict[str, Any]],
    recent_counts: dict[int, int],
    recent_window: int,
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    *,
    stats_index: dict[str, Any] | None = None,
    top_count: int = PREDICTION_PANEL_D_TOP_COUNT,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    game_key = str(config["key"])
    odds = DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(4)
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
    score_by_number = {int(item["number"]): parse_float(item.get("score"), 0) for item in scored}
    theoretical_hit_rate = hit_probability_for(config, 4)
    fair_odds = 1 / theoretical_hit_rate if theoretical_hit_rate > 0 else 0
    break_even_hit_rate = 1 / float(odds)
    candidates_by_numbers: dict[tuple[int, ...], dict[str, Any]] = {}
    disabled_structure_types = PREDICTION_PANEL_D_DISABLED_STRUCTURE_TYPES_BY_GAME.get(game_key, set())

    def add_candidate(
        *,
        numbers: tuple[int, ...],
        rule_key: str,
        structure_label: str,
        source_panel: str,
        source_panels: list[str],
        source_labels: list[str],
        core_numbers: list[int],
        companion_numbers: list[int],
        source_score: float,
    ) -> None:
        normalized = prediction_panel_d_valid_four(numbers, total_numbers)
        if normalized is None:
            return
        structure_type = f"d_{rule_key}"
        if structure_type in disabled_structure_types:
            return
        companion_score_numbers = companion_numbers or [number for number in normalized if number not in set(core_numbers)]
        companion_score = (
            sum(score_by_number.get(number, 0.0) for number in companion_score_numbers) / len(companion_score_numbers)
            if companion_score_numbers
            else 0.0
        )
        structure_priority = prediction_panel_d_rule_priority(rule_key)
        item = {
            "numbers": list(normalized),
            "bonusNumber": None,
            "mode": "main",
            "pickCount": 4,
            "panel": PREDICTION_PANEL_D,
            "sourcePanel": source_panel,
            "sourcePanels": source_panels,
            "sourceCoreTicketLabels": source_labels,
            "structureType": structure_type,
            "structureLabel": structure_label,
            "derivedRule": rule_key,
            "coreNumbers": core_numbers,
            "companionNumbers": companion_numbers,
            "sourceCoreScore": source_score,
            "companionScore": companion_score,
            "structurePriority": structure_priority,
            "prefilterScore": 0,
        }
        existing = candidates_by_numbers.get(normalized)
        if existing is None or (
            structure_priority,
            source_score,
            companion_score,
        ) > (
            parse_float(existing.get("structurePriority"), 0),
            parse_float(existing.get("sourceCoreScore"), 0),
            parse_float(existing.get("companionScore"), 0),
        ):
            candidates_by_numbers[normalized] = item

    for pair_item in prediction_panel_d_ab_pair_sources(a_tickets, b_tickets, total_numbers):
        pair = tuple(int(number) for number in pair_item.get("numbers") or [])
        if len(pair) != 2:
            continue
        for rule_item in prediction_panel_d_pair_rule_candidates(pair, total_numbers):
            add_candidate(
                numbers=tuple(rule_item["numbers"]),
                rule_key=str(rule_item["ruleKey"]),
                structure_label=str(rule_item["structureLabel"]),
                source_panel="ab",
                source_panels=pair_item.get("sourcePanels") or [PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B],
                source_labels=pair_item.get("sourceLabels") or [f"{pair[0]}-{pair[1]}"],
                core_numbers=list(pair),
                companion_numbers=list(rule_item.get("companionNumbers") or []),
                source_score=parse_float(pair_item.get("score"), 0),
            )

    for ticket in c_tickets[:PREDICTION_PANEL_D_C_SOURCE_LIMIT]:
        if not isinstance(ticket, dict):
            continue
        source_score = parse_float(ticket.get("score"), 0)
        source_labels = [str(ticket.get("ticketLabel") or "-".join(str(number) for number in ticket.get("numbers") or []))]
        for rule_item in prediction_panel_d_c_rule_candidates(ticket, total_numbers):
            add_candidate(
                numbers=tuple(rule_item["numbers"]),
                rule_key=str(rule_item["ruleKey"]),
                structure_label=str(rule_item["structureLabel"]),
                source_panel=PREDICTION_PANEL_C,
                source_panels=[PREDICTION_PANEL_C],
                source_labels=source_labels,
                core_numbers=list(rule_item.get("coreNumbers") or []),
                companion_numbers=list(rule_item.get("companionNumbers") or []),
                source_score=source_score,
            )

    candidates = list(candidates_by_numbers.values())
    if not candidates:
        return []

    source_scores = [parse_float(item.get("sourceCoreScore"), 0) for item in candidates]
    companion_scores = [parse_float(item.get("companionScore"), 0) for item in candidates]
    for item in candidates:
        item["prefilterScore"] = (
            0.34 * parse_float(item.get("structurePriority"), 0)
            + 0.33 * normalize_score(parse_float(item.get("sourceCoreScore"), 0), source_scores)
            + 0.33 * normalize_score(parse_float(item.get("companionScore"), 0), companion_scores)
        )

    candidates.sort(
        key=lambda item: (
            -parse_float(item.get("prefilterScore"), 0),
            -parse_float(item.get("structurePriority"), 0),
            -parse_float(item.get("sourceCoreScore"), 0),
            item.get("numbers") or [],
        )
    )
    candidates = candidates[:PREDICTION_PANEL_D_DERIVED_PREFILTER_LIMIT]

    miss_values: list[int] = []
    edge_values: list[float] = []
    for item in candidates:
        stats = ticket_stats_from_draw_sets(
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            tuple(int(number) for number in item.get("numbers") or []),
            None,
            stats_index=stats_index,
        )
        item.update(stats)
        miss_values.append(parse_int(item.get("currentMiss"), 0))
        edge_values.append(parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate)

    source_scores = [parse_float(item.get("sourceCoreScore"), 0) for item in candidates]
    companion_scores = [parse_float(item.get("companionScore"), 0) for item in candidates]
    for item in candidates:
        item["score"] = (
            0.24 * parse_float(item.get("structurePriority"), 0)
            + 0.22 * normalize_score(parse_float(item.get("sourceCoreScore"), 0), source_scores)
            + 0.18 * normalize_score(parse_float(item.get("companionScore"), 0), companion_scores)
            + 0.22 * normalize_score(parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate, edge_values)
            + 0.14 * normalize_score(parse_int(item.get("currentMiss"), 0), miss_values)
        )
        item["label"] = f"D {item['structureLabel']}"
        item["theoreticalHitRate"] = theoretical_hit_rate
        item["fairOdds"] = fair_odds
        item["odds"] = float(odds)
        item["breakEvenHitRate"] = break_even_hit_rate
        item["evAtOdds"] = theoretical_hit_rate * float(odds) - 1
        item["chasePeriods"] = PREDICTION_TICKET_CHASE_PERIODS
        item["missAllProbability"] = (1 - theoretical_hit_rate) ** PREDICTION_TICKET_CHASE_PERIODS
        item["sampleWarning"] = draw_count < 500 or parse_int(item.get("recentWindow"), 0) < 200
        item["ticketLabel"] = "-".join(str(number) for number in item["numbers"])

    candidates.sort(
        key=lambda item: (
            -parse_float(item.get("score"), 0),
            -parse_float(item.get("structurePriority"), 0),
            -parse_int(item.get("currentMiss"), 0),
            item.get("numbers") or [],
        )
    )
    selected: list[dict[str, Any]] = []
    rule_counts: dict[str, int] = {}
    for item in candidates:
        rule = str(item.get("structureType") or "")
        if rule_counts.get(rule, 0) >= PREDICTION_PANEL_D_RULE_LIMIT:
            continue
        selected.append(item)
        rule_counts[rule] = rule_counts.get(rule, 0) + 1
        if len(selected) >= top_count:
            break
    return selected


def prediction_panel_e_valid_five(numbers: list[int] | tuple[int, ...], total_numbers: int) -> tuple[int, ...] | None:
    normalized = tuple(sorted({int(number) for number in numbers if 1 <= int(number) <= total_numbers}))
    return normalized if len(normalized) == 5 else None


def prediction_panel_e_source_structure_types_for_game(game_key: str) -> set[str]:
    now_ts = time.time()
    cached = PREDICTION_PANEL_E_SOURCE_CACHE.get(game_key)
    if cached is not None and now_ts - cached[0] <= PREDICTION_PANEL_E_SOURCE_CACHE_TTL_SECONDS:
        return set(cached[1])

    disabled = PREDICTION_PANEL_D_DISABLED_STRUCTURE_TYPES_BY_GAME.get(game_key, set())
    fallback = set(PREDICTION_PANEL_E_FALLBACK_SOURCE_STRUCTURE_TYPES_BY_GAME.get(game_key, set()))
    selected: set[str] = set()
    try:
        init_prediction_tracking_db()
        with prediction_tracking_db_connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    COALESCE(json_extract(record_json, '$.structureType'), '') AS structure_type,
                    COUNT(*) AS settled,
                    COALESCE(SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END), 0) AS won,
                    COALESCE(SUM(
                        COALESCE(CAST(NULLIF(json_extract(record_json, '$.theoreticalHitRate'), '') AS REAL), 0)
                    ), 0) AS expected_hits,
                    COALESCE(SUM(
                        COALESCE(CAST(NULLIF(json_extract(record_json, '$.stake'), '') AS REAL), 1)
                    ), 0) AS stake_total,
                    COALESCE(SUM(
                        COALESCE(CAST(NULLIF(json_extract(record_json, '$.profit'), '') AS REAL), 0)
                    ), 0) AS profit_total
                FROM prediction_records
                WHERE game_key = ?
                  AND panel = ?
                  AND method_version = ?
                  AND status IN ('won', 'lost')
                GROUP BY structure_type
                """,
                [game_key, PREDICTION_PANEL_D, prediction_method_version_for_panel(PREDICTION_PANEL_D)],
            ).fetchall()
        for row in rows:
            structure_type = str(row["structure_type"] or "")
            settled = parse_int(row["settled"], 0)
            won = parse_int(row["won"], 0)
            stake_total = parse_float(row["stake_total"], 0)
            profit_total = parse_float(row["profit_total"], 0)
            expected_hits = parse_float(row["expected_hits"], 0)
            if not structure_type or structure_type in disabled:
                continue
            if settled < PREDICTION_PANEL_E_SOURCE_MIN_SETTLED or stake_total <= 0:
                continue
            hit_rate = won / settled if settled else 0
            theoretical_hit_rate = expected_hits / settled if settled else 0
            if profit_total > 0 and hit_rate >= theoretical_hit_rate:
                selected.add(structure_type)
    except Exception:
        selected = set()

    if not selected:
        selected = fallback
    selected = {structure_type for structure_type in selected if structure_type and structure_type not in disabled}
    PREDICTION_PANEL_E_SOURCE_CACHE[game_key] = (now_ts, set(selected))
    return set(selected)


def prediction_panel_e_d_profit_five_tickets(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    d_tickets: list[dict[str, Any]],
    frequency: dict[int, dict[str, Any]],
    recent_counts: dict[int, int],
    recent_window: int,
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    *,
    stats_index: dict[str, Any] | None = None,
    top_count: int = PREDICTION_PANEL_E_TOP_COUNT,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    game_key = str(config["key"])
    odds = DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(5)
    if not odds:
        return []

    total_numbers = int(config["totalNumbers"])
    draw_count = len(rows)
    allowed_structure_types = prediction_panel_e_source_structure_types_for_game(game_key)
    if not allowed_structure_types:
        return []

    scored = scored_numbers(
        list(range(1, total_numbers + 1)),
        PREDICTION_NUMBER_WEIGHTS[0],
        frequency,
        recent_counts,
        recent_window,
        draw_count,
    )
    score_by_number = {int(item["number"]): parse_float(item.get("score"), 0) for item in scored}

    source_tickets: list[dict[str, Any]] = []
    for ticket in d_tickets:
        if not isinstance(ticket, dict):
            continue
        structure_type = str(ticket.get("structureType") or "")
        if structure_type not in allowed_structure_types:
            continue
        numbers = prediction_panel_d_valid_four(
            tuple(parse_int(number, 0) for number in ticket.get("numbers") or []),
            total_numbers,
        )
        if numbers is None:
            continue
        source_tickets.append(
            {
                **ticket,
                "numbers": list(numbers),
                "_numberSet": set(numbers),
                "_structureType": structure_type,
                "_structureLabel": str(ticket.get("structureLabel") or structure_type),
                "_score": parse_float(ticket.get("score"), 0),
                "_ticketLabel": str(ticket.get("ticketLabel") or "-".join(str(number) for number in numbers)),
            }
        )
    source_tickets.sort(
        key=lambda item: (
            -parse_float(item.get("_score"), 0),
            -parse_float(item.get("structurePriority"), 0),
            item.get("numbers") or [],
        )
    )
    source_tickets = source_tickets[:PREDICTION_PANEL_E_D_SOURCE_LIMIT]
    if len(source_tickets) < 2:
        return []

    theoretical_hit_rate = hit_probability_for(config, 5)
    fair_odds = 1 / theoretical_hit_rate if theoretical_hit_rate > 0 else 0
    break_even_hit_rate = 1 / float(odds)
    candidates_by_numbers: dict[tuple[int, ...], dict[str, Any]] = {}

    def add_candidate(
        base_ticket: dict[str, Any],
        extension_ticket: dict[str, Any],
        extra_number: int,
        overlap_numbers: set[int],
    ) -> None:
        base_numbers = tuple(int(number) for number in base_ticket.get("numbers") or [])
        extension_numbers = tuple(int(number) for number in extension_ticket.get("numbers") or [])
        normalized = prediction_panel_e_valid_five([*base_numbers, extra_number], total_numbers)
        if normalized is None:
            return
        overlap_count = len(overlap_numbers)
        if overlap_count < 2:
            return
        source_structure = str(base_ticket.get("_structureType") or "")
        extension_structure = str(extension_ticket.get("_structureType") or "")
        if not source_structure or not extension_structure:
            return
        source_label = str(base_ticket.get("_structureLabel") or source_structure)
        extension_label = str(extension_ticket.get("_structureLabel") or extension_structure)
        structure_type = (
            f"e_d_overlap{overlap_count}_"
            f"{source_structure.removeprefix('d_')}__{extension_structure.removeprefix('d_')}"
        )
        structure_priority = 1.0 if overlap_count >= 3 else 0.72
        source_score = (
            parse_float(base_ticket.get("_score"), 0)
            + parse_float(extension_ticket.get("_score"), 0)
        ) / 2
        companion_score = score_by_number.get(extra_number, 0.0)
        item = {
            "numbers": list(normalized),
            "bonusNumber": None,
            "mode": "main",
            "pickCount": 5,
            "panel": PREDICTION_PANEL_E,
            "sourcePanel": PREDICTION_PANEL_D,
            "sourcePanels": [PREDICTION_PANEL_D],
            "sourceCoreTicketLabels": [
                str(base_ticket.get("_ticketLabel") or ""),
                str(extension_ticket.get("_ticketLabel") or ""),
            ],
            "structureType": structure_type,
            "structureLabel": f"D重叠{overlap_count}补码：{source_label} + {extension_label}",
            "derivedRule": f"d_overlap_{overlap_count}_extra_from_d",
            "sourceStructureType": source_structure,
            "sourceStructureLabel": source_label,
            "extensionStructureType": extension_structure,
            "extensionStructureLabel": extension_label,
            "extensionNumbers": list(extension_numbers),
            "overlapNumbers": sorted(overlap_numbers),
            "coreNumbers": list(base_numbers),
            "companionNumbers": [extra_number],
            "sourcePoolNumbers": sorted(set(base_numbers) | set(extension_numbers)),
            "sourcePoolCount": len(set(base_numbers) | set(extension_numbers)),
            "sourceCoreScore": source_score,
            "companionScore": companion_score,
            "structurePriority": structure_priority,
            "prefilterScore": (
                0.36 * structure_priority
                + 0.30 * source_score
                + 0.22 * companion_score
                + 0.12 * (overlap_count / 4)
            ),
        }
        existing = candidates_by_numbers.get(normalized)
        if existing is None or (
            parse_float(item.get("prefilterScore"), 0),
            parse_float(item.get("sourceCoreScore"), 0),
            parse_float(item.get("companionScore"), 0),
        ) > (
            parse_float(existing.get("prefilterScore"), 0),
            parse_float(existing.get("sourceCoreScore"), 0),
            parse_float(existing.get("companionScore"), 0),
        ):
            candidates_by_numbers[normalized] = item

    for base_index, base_ticket in enumerate(source_tickets):
        base_set = set(base_ticket.get("_numberSet") or set())
        if len(base_set) != 4:
            continue
        for extension_index, extension_ticket in enumerate(source_tickets):
            if base_index == extension_index:
                continue
            extension_set = set(extension_ticket.get("_numberSet") or set())
            if len(extension_set) != 4:
                continue
            overlap_numbers = base_set & extension_set
            if len(overlap_numbers) < 2:
                continue
            for extra_number in sorted(extension_set - base_set):
                add_candidate(base_ticket, extension_ticket, int(extra_number), overlap_numbers)

    candidates = list(candidates_by_numbers.values())
    if not candidates:
        return []
    candidates.sort(
        key=lambda item: (
            -parse_float(item.get("prefilterScore"), 0),
            -parse_float(item.get("structurePriority"), 0),
            -parse_float(item.get("sourceCoreScore"), 0),
            item.get("numbers") or [],
        )
    )
    candidates = candidates[:PREDICTION_PANEL_E_DERIVED_PREFILTER_LIMIT]

    miss_values: list[int] = []
    edge_values: list[float] = []
    for item in candidates:
        stats = ticket_stats_from_draw_sets(
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            tuple(int(number) for number in item.get("numbers") or []),
            None,
            stats_index=stats_index,
        )
        item.update(stats)
        miss_values.append(parse_int(item.get("currentMiss"), 0))
        edge_values.append(parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate)

    source_scores = [parse_float(item.get("sourceCoreScore"), 0) for item in candidates]
    companion_scores = [parse_float(item.get("companionScore"), 0) for item in candidates]
    for item in candidates:
        item["score"] = (
            0.24 * parse_float(item.get("structurePriority"), 0)
            + 0.22 * normalize_score(parse_float(item.get("sourceCoreScore"), 0), source_scores)
            + 0.18 * normalize_score(parse_float(item.get("companionScore"), 0), companion_scores)
            + 0.22 * normalize_score(parse_float(item.get("recentHitRate"), 0) - theoretical_hit_rate, edge_values)
            + 0.14 * normalize_score(parse_int(item.get("currentMiss"), 0), miss_values)
        )
        item["label"] = f"E {item['structureLabel']}"
        item["theoreticalHitRate"] = theoretical_hit_rate
        item["fairOdds"] = fair_odds
        item["odds"] = float(odds)
        item["breakEvenHitRate"] = break_even_hit_rate
        item["evAtOdds"] = theoretical_hit_rate * float(odds) - 1
        item["chasePeriods"] = PREDICTION_TICKET_CHASE_PERIODS
        item["missAllProbability"] = (1 - theoretical_hit_rate) ** PREDICTION_TICKET_CHASE_PERIODS
        item["sampleWarning"] = draw_count < 500 or parse_int(item.get("recentWindow"), 0) < 200
        item["ticketLabel"] = "-".join(str(number) for number in item["numbers"])

    candidates.sort(
        key=lambda item: (
            -parse_float(item.get("score"), 0),
            -parse_float(item.get("structurePriority"), 0),
            -parse_int(item.get("currentMiss"), 0),
            item.get("numbers") or [],
        )
    )
    selected: list[dict[str, Any]] = []
    rule_counts: dict[str, int] = {}
    for item in candidates:
        rule = str(item.get("structureType") or "")
        if rule_counts.get(rule, 0) >= PREDICTION_PANEL_E_RULE_LIMIT:
            continue
        selected.append(item)
        rule_counts[rule] = rule_counts.get(rule, 0) + 1
        if len(selected) >= top_count:
            break
    return selected


def prediction_ticket_number_counts(tickets: list[dict[str, Any]]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        seen: set[int] = set()
        for number in ticket.get("numbers") or []:
            parsed = parse_int(number, 0)
            if parsed > 0:
                seen.add(parsed)
        for number in seen:
            counts[number] = counts.get(number, 0) + 1
    return counts


def prediction_panel_source_number_map(
    source_tickets_by_panel: dict[str, list[dict[str, Any]]],
) -> tuple[list[int], dict[int, set[str]], dict[int, dict[str, int]], dict[int, int]]:
    source_panels_by_number: dict[int, set[str]] = {}
    source_counts_by_number: dict[int, dict[str, int]] = {}
    source_ticket_counts_by_number: dict[int, int] = {}
    for panel, tickets in source_tickets_by_panel.items():
        panel_key = prediction_panel_from_value(panel)
        counts = prediction_ticket_number_counts(tickets)
        for number, count in counts.items():
            if count <= 0:
                continue
            source_panels_by_number.setdefault(number, set()).add(panel_key)
            source_counts_by_number.setdefault(number, {})[panel_key] = count
            source_ticket_counts_by_number[number] = source_ticket_counts_by_number.get(number, 0) + count
    return (
        sorted(source_panels_by_number),
        source_panels_by_number,
        source_counts_by_number,
        source_ticket_counts_by_number,
    )


def prediction_panel_f_false_kill_recall_ticket(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    source_tickets_by_panel: dict[str, list[dict[str, Any]]],
    frequency: dict[int, dict[str, Any]],
    recent_counts: dict[int, int],
    recent_window: int,
    draw_sets_oldest: list[set[int]],
    bonus_values_oldest: list[int],
    recent_draw_sets: list[set[int]],
    recent_bonus_values: list[int],
    stats_index: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    game_key = str(config["key"])
    odds = DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(4)
    if not odds:
        return []

    total_numbers = int(config["totalNumbers"])
    draw_count = len(rows)
    source_pool, source_panels_by_number, source_counts_by_number, source_ticket_counts_by_number = (
        prediction_panel_source_number_map(source_tickets_by_panel)
    )
    if not source_pool:
        return []

    scored = scored_numbers(
        list(range(1, total_numbers + 1)),
        PREDICTION_NUMBER_WEIGHTS[0],
        frequency,
        recent_counts,
        recent_window,
        draw_count,
    )
    score_by_number = {int(item["number"]): float(item["score"]) for item in scored}
    miss_by_number = {int(item["number"]): int(item["currentMiss"]) for item in scored}
    recent_by_number = {
        int(item["number"]): parse_int(item.get("recentHits"), 0) / recent_window if recent_window else 0
        for item in scored
    }

    source_count_values = [len(source_panels_by_number.get(number, set())) for number in source_pool]
    source_ticket_count_values = [source_ticket_counts_by_number.get(number, 0) for number in source_pool]
    number_score_values = [score_by_number.get(number, 0.0) for number in source_pool]
    miss_values_all = [miss_by_number.get(number, 0) for number in source_pool]
    recent_values_all = [recent_by_number.get(number, 0.0) for number in source_pool]
    candidate_scores: dict[int, float] = {}
    for number in source_pool:
        source_count = len(source_panels_by_number.get(number, set()))
        source_ticket_count = source_ticket_counts_by_number.get(number, 0)
        candidate_scores[number] = (
            0.32 * normalize_score(source_count, source_count_values)
            + 0.22 * normalize_score(source_ticket_count, source_ticket_count_values)
            + 0.22 * normalize_score(score_by_number.get(number, 0.0), number_score_values)
            + 0.14 * normalize_score(miss_by_number.get(number, 0), miss_values_all)
            + 0.10 * normalize_score(recent_by_number.get(number, 0.0), recent_values_all)
        )

    selected = sorted(
        source_pool,
        key=lambda number: (
            candidate_scores.get(number, 0.0),
            len(source_panels_by_number.get(number, set())),
            source_ticket_counts_by_number.get(number, 0),
            score_by_number.get(number, 0.0),
            recent_by_number.get(number, 0.0),
            -number,
        ),
        reverse=True,
    )[:4]
    numbers = tuple(sorted(selected[:4]))
    if len(numbers) != 4:
        return []

    theoretical_hit_rate = hit_probability_for(config, 4)
    fair_odds = 1 / theoretical_hit_rate if theoretical_hit_rate > 0 else 0
    break_even_hit_rate = 1 / float(odds)
    stats = ticket_stats_from_draw_sets(
        draw_sets_oldest,
        bonus_values_oldest,
        recent_draw_sets,
        recent_bonus_values,
        numbers,
        None,
        stats_index=stats_index,
    )
    source_counts = [source_ticket_counts_by_number.get(number, 0) for number in numbers]
    miss_values = [miss_by_number.get(number, 0) for number in numbers]
    recent_values = [recent_by_number.get(number, 0.0) for number in numbers]
    average_score = sum(score_by_number.get(number, 0.0) for number in numbers) / 4
    average_miss = sum(miss_values) / 4
    average_recent = sum(recent_values) / 4
    item = {
        "numbers": list(numbers),
        "roughScore": average_score,
        "sourceCoreScore": sum(source_counts) / max(1, len(numbers)),
        "companionScore": average_recent,
        **stats,
        "score": (
            sum(candidate_scores.get(number, 0.0) for number in numbers) / 4
        ),
        "label": "F ABCDE误杀号召回四码",
        "bonusNumber": None,
        "mode": "main",
        "pickCount": 4,
        "panel": PREDICTION_PANEL_F,
        "sourcePanel": "abcde_false_kill_pool",
        "sourcePanels": [
            PREDICTION_PANEL_DEFAULT,
            PREDICTION_PANEL_B,
            PREDICTION_PANEL_C,
            PREDICTION_PANEL_D,
            PREDICTION_PANEL_E,
        ],
        "structureType": "abcde_false_kill_recall_four",
        "structureLabel": "ABCDE误杀召回四码",
        "coreNumbers": [],
        "companionNumbers": list(numbers),
        "recallNumbers": list(numbers),
        "reversalNumbers": list(numbers),
        "sourcePoolNumbers": source_pool,
        "sourcePoolCount": len(source_pool),
        "excludedNumbers": source_pool,
        "falseKillSourceNumbers": source_pool,
        "numberSourcePanels": {
            str(number): sorted(source_panels_by_number.get(number, set()))
            for number in source_pool
        },
        "numberSourceCounts": {
            str(number): dict(sorted(source_counts_by_number.get(number, {}).items()))
            for number in source_pool
        },
        "sourceCounts": {str(number): source_ticket_counts_by_number.get(number, 0) for number in numbers},
        "corePoolNumbers": [],
        "fillPoolNumbers": source_pool,
        "theoreticalHitRate": theoretical_hit_rate,
        "fairOdds": fair_odds,
        "odds": float(odds),
        "breakEvenHitRate": break_even_hit_rate,
        "evAtOdds": theoretical_hit_rate * float(odds) - 1,
        "chasePeriods": PREDICTION_TICKET_CHASE_PERIODS,
        "missAllProbability": (1 - theoretical_hit_rate) ** PREDICTION_TICKET_CHASE_PERIODS,
        "sampleWarning": draw_count < 500 or parse_int(stats.get("recentWindow"), 0) < 200,
        "ticketLabel": "-".join(str(number) for number in numbers),
    }
    return [item]


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
    config: dict[str, Any] | None = None,
    timeline_newest: dict[str, Any] | None = None,
    panel: str = PREDICTION_PANEL_DEFAULT,
    now_ms: int | None = None,
    include_staking_simulation: bool = False,
) -> dict[str, Any]:
    config = config or LOTTERY_GAMES[DEFAULT_GAME_KEY]
    panel = prediction_panel_from_value(panel)
    total_numbers = int(config["totalNumbers"])
    half = total_numbers // 2
    frequency = {item["number"]: item for item in number_frequency(rows, config)}
    recent_window = min(PREDICTION_RECENT_WINDOW, len(rows))
    recent_counts = recent_number_counts(rows, recent_window, config)
    draw_count = len(rows)
    bonus_sets = bonus_ball_prediction_sets(rows, config, recent_window)
    recent_eval_window = min(PREDICTION_TICKET_BACKTEST_WINDOW, draw_count)
    draw_sets_oldest = [set(row.get("numbers") or []) for row in reversed(rows)]
    bonus_values_oldest = [parse_int(row.get("bonusBall"), 0) for row in reversed(rows)]
    recent_rows = rows[:recent_eval_window]
    recent_draw_sets = [set(row.get("numbers") or []) for row in recent_rows]
    recent_bonus_values = [parse_int(row.get("bonusBall"), 0) for row in recent_rows]
    stats_index = ticket_stats_index(draw_sets_oldest, bonus_values_oldest, recent_draw_sets)
    base_strategy_tickets = prediction_strategy_tickets(
        rows,
        config,
        frequency,
        recent_counts,
        recent_window,
        bonus_sets,
        draw_sets_oldest,
        bonus_values_oldest,
        recent_draw_sets,
        recent_bonus_values,
        panel=PREDICTION_PANEL_DEFAULT,
        stats_index=stats_index,
    )
    game_key = str(config["key"])
    needs_b_tickets = panel in {
        PREDICTION_PANEL_B,
        PREDICTION_PANEL_C,
        PREDICTION_PANEL_D,
        PREDICTION_PANEL_E,
        PREDICTION_PANEL_M,
    }
    needs_c_tickets = panel in {
        PREDICTION_PANEL_C,
        PREDICTION_PANEL_E,
    }
    needs_m_tickets = panel in {
        PREDICTION_PANEL_M,
        PREDICTION_PANEL_D,
    }
    e_supported = game_key in PREDICTION_PANEL_E_GAME_KEYS
    excluded_numbers = prediction_kill_numbers_from_tickets(base_strategy_tickets) if needs_b_tickets else []
    b_strategy_tickets = (
        prediction_strategy_tickets(
            rows,
            config,
            frequency,
            recent_counts,
            recent_window,
            bonus_sets,
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            panel=PREDICTION_PANEL_B,
            excluded_numbers=set(excluded_numbers),
            stats_index=stats_index,
        )
        if needs_b_tickets
        else []
    )
    c_strategy_tickets: list[dict[str, Any]] = []
    if needs_c_tickets:
        c_strategy_tickets = prediction_panel_c_structure_tickets(
            rows,
            config,
            base_strategy_tickets,
            b_strategy_tickets,
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            stats_index=stats_index,
        )
    m_strategy_tickets = (
        prediction_panel_m_low_group_tickets(
            rows,
            config,
            base_strategy_tickets,
            b_strategy_tickets,
            frequency,
            recent_counts,
            recent_window,
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            stats_index=stats_index,
            include_staking_simulation=panel == PREDICTION_PANEL_M and include_staking_simulation,
        )
        if needs_m_tickets
        else []
    )
    d_source_tickets: list[dict[str, Any]] = []
    e_source_tickets: list[dict[str, Any]] = []
    if panel == PREDICTION_PANEL_D:
        excluded_numbers = []
    if panel in {PREDICTION_PANEL_E, PREDICTION_PANEL_F, PREDICTION_PANEL_G} and e_supported:
        excluded_numbers = []
    elif panel in {PREDICTION_PANEL_E, PREDICTION_PANEL_F, PREDICTION_PANEL_G}:
        excluded_numbers = []
    if panel == PREDICTION_PANEL_D:
        d_source_tickets = prediction_panel_d_observation_tickets(
            rows,
            config,
            base_strategy_tickets,
            b_strategy_tickets,
            m_strategy_tickets,
            frequency,
            recent_counts,
            recent_window,
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            stats_index=stats_index,
        )
    elif panel == PREDICTION_PANEL_E:
        d_source_tickets = prediction_panel_d_derived_four_tickets(
            rows,
            config,
            base_strategy_tickets,
            b_strategy_tickets,
            c_strategy_tickets,
            frequency,
            recent_counts,
            recent_window,
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            stats_index=stats_index,
        )
    if panel == PREDICTION_PANEL_B:
        strategy_tickets = b_strategy_tickets
    elif panel == PREDICTION_PANEL_C:
        strategy_tickets = c_strategy_tickets
    elif panel == PREDICTION_PANEL_D:
        strategy_tickets = d_source_tickets
    elif panel == PREDICTION_PANEL_E:
        e_source_tickets = (
            prediction_panel_e_d_profit_five_tickets(
                rows,
                config,
                d_source_tickets,
                frequency,
                recent_counts,
                recent_window,
                draw_sets_oldest,
                bonus_values_oldest,
                recent_draw_sets,
                recent_bonus_values,
                stats_index=stats_index,
            )
            if e_supported
            else []
        )
        strategy_tickets = e_source_tickets
    elif panel == PREDICTION_PANEL_M:
        strategy_tickets = m_strategy_tickets
    elif panel == PREDICTION_PANEL_F:
        source_tickets_by_panel = {
            PREDICTION_PANEL_DEFAULT: base_strategy_tickets,
            PREDICTION_PANEL_B: b_strategy_tickets,
            PREDICTION_PANEL_C: c_strategy_tickets,
            PREDICTION_PANEL_D: d_source_tickets,
            PREDICTION_PANEL_E: e_source_tickets,
        }
        excluded_numbers = prediction_panel_source_number_map(source_tickets_by_panel)[0] if e_supported else []
        strategy_tickets = (
            prediction_panel_f_false_kill_recall_ticket(
                rows,
                config,
                source_tickets_by_panel,
                frequency,
                recent_counts,
                recent_window,
                draw_sets_oldest,
                bonus_values_oldest,
                recent_draw_sets,
                recent_bonus_values,
                stats_index=stats_index,
            )
            if e_supported
            else []
        )
    elif panel == PREDICTION_PANEL_G:
        g_source_tickets_by_panel = {
            PREDICTION_PANEL_C: c_strategy_tickets,
            PREDICTION_PANEL_D: d_source_tickets,
            PREDICTION_PANEL_E: e_source_tickets,
        }
        excluded_numbers = prediction_panel_source_number_map(g_source_tickets_by_panel)[0] if e_supported else []
        strategy_tickets = (
            prediction_panel_d_clean_four_tickets(
                rows,
                config,
                set(excluded_numbers),
                frequency,
                recent_counts,
                recent_window,
                draw_sets_oldest,
                bonus_values_oldest,
                recent_draw_sets,
                recent_bonus_values,
                panel=PREDICTION_PANEL_G,
                top_count=PREDICTION_PANEL_G_TOP_COUNT,
                label="G CDE杀号后四码",
                source_panel="cde",
                source_panels=[PREDICTION_PANEL_C, PREDICTION_PANEL_D, PREDICTION_PANEL_E],
                structure_type="kill_cde_follow_four",
                structure_label="CDE候选杀号后四码",
                stats_index=stats_index,
            )
            if e_supported
            else []
        )
    else:
        strategy_tickets = base_strategy_tickets
    forecasts = []
    newest = timeline_newest or (rows[0] if rows else None)
    newest_ms = parse_int(newest.get("drawTimeMs") if newest else 0, 0)
    forecast_times = future_prediction_draw_times(newest_ms, config, now_ms=now_ms)
    first_ms = parse_int(forecast_times[0].get("drawTimeMs"), 0) if forecast_times else 0
    end_ms = parse_int(forecast_times[-1].get("drawTimeMs"), 0) if forecast_times else 0
    for index, forecast_time in enumerate(forecast_times):
        forecasts.append(
            {
                "drawOffset": parse_int(forecast_time.get("drawOffset"), index + 1),
                "drawTimeMs": parse_int(forecast_time.get("drawTimeMs"), 0),
                "drawTimeUtc": str(forecast_time.get("drawTimeUtc") or ""),
                "bonusBallNumbers": bonus_sets[index] if bonus_sets else [],
                "patterns": {},
            }
        )
    method = "当前遗漏 + 近240期动量偏差 + 全样本偏差 + 连号遗漏 z-score 的启发式排序"
    if panel == PREDICTION_PANEL_B:
        method = f"B计划：先排除A计划候选票主球 {len(excluded_numbers)} 个，再按同一排序逻辑生成候选票"
    if panel == PREDICTION_PANEL_C:
        method = "旧C计划：用A/B计划主号候选形成核心对，再按临码、±10、固定间隔、5-10窗口、同尾和历史共现派生4码结构票"
    if panel == PREDICTION_PANEL_D:
        method = (
            "D计划：观察型2码/3码实验池；每期固定输出共识、拆解、逆向、形态四类规则，"
            "各1组2码和1组3码。D只用于完整开奖日观察，不直接替代C计划。"
        )
    if panel == PREDICTION_PANEL_E:
        allowed_e_rules = prediction_panel_e_source_structure_types_for_game(game_key)
        method = (
            f"E计划：只拿D计划当前盈利规则 {len(allowed_e_rules)} 个作为来源；"
            "两张D盈利四码票互相组合，第五码也从D票差集中补入；"
            "按D母规则+扩展规则分组追踪，先只观察"
            if e_supported
            else "E计划：当前彩种未启用D盈利规则五码组合"
        )
    if panel == PREDICTION_PANEL_M:
        method = (
            "C计划：从A/B源票、A/B合并池、综合分池、近窗热号、遗漏池和连号形态中审计2码/3码；"
            "按近窗命中、全样本命中、置信下沿、最大连挂和当前遗漏排序；"
            "每期最多保留2组2码+2组3码，并对当前候选做1元起步倍投历史回放"
        )
    if panel == PREDICTION_PANEL_F:
        method = (
            f"预测面板F：从A/B/C/D/E排除链路的 {len(excluded_numbers)} 个候选号码中按来源强度、综合分、遗漏和近窗表现召回，生成1张4码预测票"
            if e_supported
            else "预测面板F：当前仅用于西班牙和波兰，俄罗斯/意大利先使用原预测面板"
        )
    if panel == PREDICTION_PANEL_G:
        method = (
            f"预测面板G：统计面板C/D/E候选票里的唯一主球 {len(excluded_numbers)} 个并杀掉，再从剩余号码生成1张4码预测票"
            if e_supported
            else "预测面板G：当前仅用于西班牙和波兰，俄罗斯/意大利先使用原预测面板"
        )
    source_panel = ""
    source_panels: list[str] = []
    if panel == PREDICTION_PANEL_B:
        source_panel = PREDICTION_PANEL_DEFAULT
    elif panel == PREDICTION_PANEL_C:
        source_panel = "ab"
        source_panels = [PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B]
    elif panel == PREDICTION_PANEL_D:
        source_panel = "abc_observation"
        source_panels = [PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B, PREDICTION_PANEL_M]
    elif panel == PREDICTION_PANEL_E:
        source_panel = "d_profit_overlap_five"
        source_panels = [PREDICTION_PANEL_D]
    elif panel == PREDICTION_PANEL_M:
        source_panel = "ab_history_lowgroup"
        source_panels = [PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B]
    elif panel == PREDICTION_PANEL_F:
        source_panel = "abcde_false_kill_pool"
        source_panels = [
            PREDICTION_PANEL_DEFAULT,
            PREDICTION_PANEL_B,
            PREDICTION_PANEL_C,
            PREDICTION_PANEL_D,
            PREDICTION_PANEL_E,
        ]
    elif panel == PREDICTION_PANEL_G:
        source_panel = "cde_candidate_kill_pool"
        source_panels = [PREDICTION_PANEL_C, PREDICTION_PANEL_D, PREDICTION_PANEL_E]
    source_tickets: dict[str, list[dict[str, Any]]] = {}
    if panel == PREDICTION_PANEL_D:
        source_tickets = {
            PREDICTION_PANEL_DEFAULT: prediction_source_ticket_summaries(base_strategy_tickets),
            PREDICTION_PANEL_B: prediction_source_ticket_summaries(b_strategy_tickets),
            PREDICTION_PANEL_M: prediction_source_ticket_summaries(m_strategy_tickets),
        }
    elif panel == PREDICTION_PANEL_E and e_supported:
        source_tickets = {
            PREDICTION_PANEL_D: prediction_source_ticket_summaries(d_source_tickets),
        }
    elif panel == PREDICTION_PANEL_M:
        source_tickets = {
            PREDICTION_PANEL_DEFAULT: prediction_source_ticket_summaries(base_strategy_tickets),
            PREDICTION_PANEL_B: prediction_source_ticket_summaries(b_strategy_tickets),
        }
    elif panel == PREDICTION_PANEL_F and e_supported:
        source_tickets = {
            PREDICTION_PANEL_DEFAULT: prediction_source_ticket_summaries(base_strategy_tickets),
            PREDICTION_PANEL_B: prediction_source_ticket_summaries(b_strategy_tickets),
            PREDICTION_PANEL_C: prediction_source_ticket_summaries(c_strategy_tickets),
            PREDICTION_PANEL_D: prediction_source_ticket_summaries(d_source_tickets),
            PREDICTION_PANEL_E: prediction_source_ticket_summaries(e_source_tickets),
        }
    elif panel == PREDICTION_PANEL_G and e_supported:
        source_tickets = {
            PREDICTION_PANEL_C: prediction_source_ticket_summaries(c_strategy_tickets),
            PREDICTION_PANEL_D: prediction_source_ticket_summaries(d_source_tickets),
            PREDICTION_PANEL_E: prediction_source_ticket_summaries(e_source_tickets),
        }
    return {
        "panel": panel,
        "panelLabel": prediction_panel_label(panel),
        "sourcePanel": source_panel,
        "sourcePanels": source_panels,
        "sourceTickets": source_tickets,
        "excludedNumbers": excluded_numbers,
        "disabledStructureTypes": [],
        "sourceStructureTypes": sorted(prediction_panel_e_source_structure_types_for_game(game_key))
        if panel == PREDICTION_PANEL_E
        else [],
        "method": method,
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


def predictions_payload(
    query: dict[str, list[str]],
    *,
    touch_tracking: bool = True,
    now_ms: int | None = None,
    allow_auto_sync: bool = False,
) -> dict[str, Any]:
    perf_started = time.monotonic()
    perf: dict[str, Any] = {
        "cacheHit": False,
        "touchTracking": touch_tracking,
        "allowAutoSync": allow_auto_sync,
    }
    config = game_from_query(query)
    ensure_predictions_supported(config)
    history_path = game_history_path(config)
    row_limit = parse_int(query.get("drawLimit", ["0"])[0], 0)
    panel = prediction_panel_from_query(query)
    include_staking_simulation = panel == PREDICTION_PANEL_M and query_bool(query, "staking", False)
    perf["game"] = config["key"]
    perf["panel"] = panel
    perf["includeStakingSimulation"] = include_staking_simulation
    if panel in PREDICTION_RETIRED_PANELS:
        raise ValueError("旧C/D/E/F/G计划已停用，不再生成新预测")
    now_value = now_ms if now_ms is not None else int(time.time() * 1000)
    history_identity_started = time.monotonic()
    try:
        stat = history_path.stat()
        history_identity = (stat.st_mtime_ns, stat.st_size)
    except FileNotFoundError:
        history_identity = (0, 0)
    perf["historyIdentityMs"] = round((time.monotonic() - history_identity_started) * 1000)
    history_load_started = time.monotonic()
    all_rows = load_history_rows(history_path, config)
    perf["historyLoadMs"] = round((time.monotonic() - history_load_started) * 1000)
    perf["historyRows"] = len(all_rows)
    prediction_auto_sync: dict[str, Any] | None = None
    if allow_auto_sync and now_ms is None:
        try:
            auto_sync_started = time.monotonic()
            all_rows, prediction_auto_sync = maybe_auto_sync_prediction_tracking(config, all_rows)
            perf["autoSyncMs"] = round((time.monotonic() - auto_sync_started) * 1000)
            try:
                stat = history_path.stat()
                history_identity = (stat.st_mtime_ns, stat.st_size)
            except FileNotFoundError:
                history_identity = (0, 0)
            history_reload_started = time.monotonic()
            all_rows = load_history_rows(history_path, config)
            perf["postSyncHistoryReloadMs"] = round((time.monotonic() - history_reload_started) * 1000)
            perf["historyRows"] = len(all_rows)
        except Exception as exc:
            prediction_auto_sync = {"ok": False, "error": str(exc), "errorType": type(exc).__name__}
            perf["autoSyncError"] = prediction_auto_sync
    target_cache_ms = prediction_target_cache_ms(all_rows, config, now_value)
    cache_key = (
        config["key"],
        *history_identity,
        row_limit,
        target_cache_ms,
        panel,
        include_staking_simulation,
    )

    cache_lookup_started = time.monotonic()
    with PREDICTION_CACHE_LOCK:
        cached = lru_cache_get(PREDICTION_CACHE, cache_key)
    perf["cacheLookupMs"] = round((time.monotonic() - cache_lookup_started) * 1000)
    cached_predictions = cached.get("predictions") if isinstance(cached, dict) else {}
    cached_ready = (
        cached_predictions.get("trackingReady")
        if isinstance(cached_predictions, dict)
        else None
    )
    if cached is not None and cached_ready is not False:
        payload = dict(cached)
        payload = attach_prediction_payload_daily_miss_streaks(payload, config)
        payload["cacheHit"] = True
        payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
        if prediction_auto_sync is not None:
            payload["predictionAutoSync"] = prediction_auto_sync
        tracking_started = time.monotonic()
        if touch_tracking:
            payload["predictionTracking"] = touch_prediction_tracking_for_payload(
                payload,
                config,
                allow_auto_sync=allow_auto_sync,
            )
        perf["trackingTouchMs"] = round((time.monotonic() - tracking_started) * 1000)
        perf["cacheHit"] = True
        perf["totalMs"] = round((time.monotonic() - perf_started) * 1000)
        payload["performance"] = perf
        return payload

    data_prep_started = time.monotonic()
    data_integrity = history_data_integrity(all_rows, config)
    rows = valid_draw_rows(all_rows, config)
    if row_limit > 0:
        rows = rows[:row_limit]
    latest_timeline = all_rows[0] if all_rows else None

    newest = rows[0] if rows else None
    oldest = rows[-1] if rows else None
    perf["dataPrepMs"] = round((time.monotonic() - data_prep_started) * 1000)
    target_started = time.monotonic()
    early_target_context = prediction_tracking_target_context_from_latest(
        latest_timeline,
        config,
        now_ms=now_value,
    )
    perf["targetContextMs"] = round((time.monotonic() - target_started) * 1000)
    if not early_target_context["ready"]:
        payload = {
            "generatedAt": utc_now_iso(),
            "cacheHit": False,
            "panel": panel,
            "panelLabel": prediction_panel_label(panel),
            "game": game_public_config(config),
            "historyFile": file_info(history_path),
            "dataIntegrity": data_integrity,
            "drawCount": len(rows),
            "newestDraw": newest,
            "newestTimelineDraw": latest_timeline,
            "oldestDraw": oldest,
            "predictionAutoSync": prediction_auto_sync,
            "predictions": {
                "panel": panel,
                "panelLabel": prediction_panel_label(panel),
                "sourcePanel": "",
                "sourcePanels": [],
                "sourceTickets": {},
                "excludedNumbers": [],
                "method": "",
                "recentWindow": min(PREDICTION_RECENT_WINDOW, len(rows)),
                "smallRange": [],
                "bigRange": [],
                "timeWindowUtc": {"start": "", "end": ""},
                "forecasts": [],
                "strategyTickets": [],
            },
            "stakingSimulationIncluded": include_staking_simulation,
        }
        mark_prediction_payload_waiting_for_sync(payload, early_target_context)
        payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
        tracking_started = time.monotonic()
        if touch_tracking:
            payload["predictionTracking"] = {
                "panel": panel,
                "panelLabel": prediction_panel_label(panel),
                "settledNow": 0,
                "createdNow": 0,
                "summary": {},
                "allSummary": {},
                "lightweight": True,
                "skipped": True,
                "reason": "prediction_target_not_ready",
                "autoSync": {"skipped": True, "reason": "prediction_target_not_ready"},
            }
        perf["trackingTouchMs"] = round((time.monotonic() - tracking_started) * 1000)
        perf["predictionComputeMs"] = 0
        perf["totalMs"] = round((time.monotonic() - perf_started) * 1000)
        payload["performance"] = perf
        return payload
    prediction_started = time.monotonic()
    predictions = prediction_payload(
        rows,
        config,
        latest_timeline,
        panel=panel,
        now_ms=now_value,
        include_staking_simulation=include_staking_simulation,
    )
    perf["predictionComputeMs"] = round((time.monotonic() - prediction_started) * 1000)
    payload = {
        "generatedAt": utc_now_iso(),
        "cacheHit": False,
        "panel": panel,
        "panelLabel": prediction_panel_label(panel),
        "game": game_public_config(config),
        "historyFile": file_info(history_path),
        "dataIntegrity": data_integrity,
        "drawCount": len(rows),
        "newestDraw": newest,
        "newestTimelineDraw": latest_timeline,
        "oldestDraw": oldest,
        "predictionAutoSync": prediction_auto_sync,
        "predictions": predictions,
        "stakingSimulationIncluded": include_staking_simulation,
    }
    target_after_compute_started = time.monotonic()
    target_context = prediction_tracking_target_context(payload, config, now_ms=now_value)
    perf["targetContextAfterComputeMs"] = round((time.monotonic() - target_after_compute_started) * 1000)
    if not target_context["ready"]:
        mark_prediction_payload_waiting_for_sync(payload, target_context)
        reason = str(target_context.get("reason") or "")
        if now_ms is None and reason in {"history_not_synced_to_previous_draw", "target_is_not_next_open_draw_after_latest_history"}:
            payload["predictionBackgroundSync"] = schedule_prediction_background_sync(config, reason)
    else:
        payload["predictions"]["trackingReady"] = True
        payload["predictions"]["syncStatus"] = prediction_tracking_target_context_public(target_context)
        payload["predictionTarget"] = prediction_tracking_target_context_public(target_context)
    payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
    if target_context["ready"]:
        cache_store_started = time.monotonic()
        with PREDICTION_CACHE_LOCK:
            lru_cache_set(PREDICTION_CACHE, cache_key, payload, PREDICTION_CACHE_MAX_ITEMS)
        perf["cacheStoreMs"] = round((time.monotonic() - cache_store_started) * 1000)
    payload = attach_prediction_payload_daily_miss_streaks(payload, config)
    tracking_started = time.monotonic()
    if touch_tracking:
        payload["predictionTracking"] = touch_prediction_tracking_for_payload(
            payload,
            config,
            rows,
            allow_auto_sync=allow_auto_sync,
        )
    perf["trackingTouchMs"] = round((time.monotonic() - tracking_started) * 1000)
    perf["totalMs"] = round((time.monotonic() - perf_started) * 1000)
    payload["performance"] = perf
    return payload


def prediction_prewarm_identity(
    config: dict[str, Any],
    panels: tuple[str, ...],
    now_values: tuple[int, ...],
) -> tuple[Any, ...]:
    history_path = game_history_path(config)
    with DATA_LOCK:
        try:
            stat = history_path.stat()
            history_identity = (stat.st_mtime_ns, stat.st_size)
        except FileNotFoundError:
            history_identity = (0, 0)
        all_rows = load_history_rows(history_path, config)
    target_cache_values = tuple(
        sorted(
            {
                prediction_target_cache_ms(all_rows, config, now_value)
                for now_value in now_values
            }
        )
    )
    return (config["key"], *history_identity, target_cache_values, panels)


def prediction_prewarm_identity_public(identity: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "game": str(identity[0]) if len(identity) > 0 else "",
        "historyMtimeNs": parse_int(identity[1] if len(identity) > 1 else 0, 0),
        "historySize": parse_int(identity[2] if len(identity) > 2 else 0, 0),
        "targetDrawTimesMs": list(identity[3]) if len(identity) > 3 and isinstance(identity[3], tuple) else [],
        "targetDrawTimesUtc": [
            draw_time_utc_from_ms(parse_int(target_ms, 0))
            for target_ms in (identity[3] if len(identity) > 3 and isinstance(identity[3], tuple) else [])
        ],
        "panels": list(identity[4]) if len(identity) > 4 and isinstance(identity[4], tuple) else [],
    }


def run_prediction_prewarm(
    game_key: str,
    identity: tuple[Any, ...],
    panels: tuple[str, ...],
    now_values: tuple[int, ...],
    reason: str,
) -> None:
    started = time.monotonic()
    started_at = utc_now_iso()
    with PREDICTION_PREWARM_LOCK:
        PREDICTION_PREWARM_LAST[game_key] = {
            "ok": True,
            "status": "running",
            "scheduled": True,
            "game": game_key,
            "panels": list(panels),
            "identity": prediction_prewarm_identity_public(identity),
            "reason": reason,
            "startedAt": started_at,
            "generatedAt": started_at,
        }

    items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    try:
        for now_value in now_values:
            for panel in panels:
                panel_started = time.monotonic()
                try:
                    payload = predictions_payload(
                        {"game": [game_key], "panel": [panel]},
                        touch_tracking=False,
                        now_ms=now_value,
                    )
                    predictions = payload.get("predictions") if isinstance(payload.get("predictions"), dict) else {}
                    tickets = predictions.get("strategyTickets") if isinstance(predictions.get("strategyTickets"), list) else []
                    forecasts = predictions.get("forecasts") if isinstance(predictions.get("forecasts"), list) else []
                    target = forecasts[0] if forecasts and isinstance(forecasts[0], dict) else {}
                    items.append(
                        {
                            "panel": panel,
                            "panelLabel": prediction_panel_label(panel),
                            "cacheHit": bool(payload.get("cacheHit")),
                            "ticketCount": len(tickets),
                            "prewarmNowMs": now_value,
                            "prewarmNowUtc": draw_time_utc_from_ms(now_value),
                            "targetDrawTimeMs": parse_int(target.get("drawTimeMs"), 0),
                            "targetDrawTimeUtc": str(target.get("drawTimeUtc") or ""),
                            "elapsedMs": round((time.monotonic() - panel_started) * 1000),
                        }
                    )
                except Exception as exc:
                    errors.append(
                        {
                            "panel": panel,
                            "panelLabel": prediction_panel_label(panel),
                            "prewarmNowMs": now_value,
                            "prewarmNowUtc": draw_time_utc_from_ms(now_value),
                            "error": str(exc),
                            "errorType": type(exc).__name__,
                            "elapsedMs": round((time.monotonic() - panel_started) * 1000),
                        }
                    )
    finally:
        finished_at = utc_now_iso()
        with PREDICTION_PREWARM_LOCK:
            PREDICTION_PREWARM_IN_FLIGHT.discard(identity)
            PREDICTION_PREWARM_LAST[game_key] = {
                "ok": not errors,
                "status": "complete" if not errors else "failed",
                "scheduled": True,
                "game": game_key,
                "panels": list(panels),
                "identity": prediction_prewarm_identity_public(identity),
                "reason": reason,
                "startedAt": started_at,
                "finishedAt": finished_at,
                "elapsedMs": round((time.monotonic() - started) * 1000),
                "items": items,
                "errors": errors,
                "generatedAt": finished_at,
            }


def schedule_prediction_prewarm(config: dict[str, Any], *, reason: str = "history_refresh") -> dict[str, Any]:
    game_key = str(config.get("key") or "")
    panels = tuple(PREDICTION_PREWARM_PANELS)
    if game_key not in PREDICTION_PREWARM_GAME_KEYS:
        return {
            "ok": True,
            "scheduled": False,
            "skipped": True,
            "reason": "game_not_configured",
            "game": game_key,
            "generatedAt": utc_now_iso(),
        }
    if not supports_predictions(config):
        return {
            "ok": True,
            "scheduled": False,
            "skipped": True,
            "reason": "predictions_unsupported",
            "game": game_key,
            "generatedAt": utc_now_iso(),
        }

    now_values = prediction_prewarm_now_values(config)
    identity = prediction_prewarm_identity(config, panels, now_values)
    with PREDICTION_PREWARM_LOCK:
        last = PREDICTION_PREWARM_LAST.get(game_key)
        if identity in PREDICTION_PREWARM_IN_FLIGHT:
            return {
                "ok": True,
                "scheduled": False,
                "inFlight": True,
                "reason": "already_running",
                "game": game_key,
                "panels": list(panels),
                "identity": prediction_prewarm_identity_public(identity),
                "last": last,
                "generatedAt": utc_now_iso(),
            }
        if last and last.get("ok") and last.get("identity") == prediction_prewarm_identity_public(identity):
            return {
                "ok": True,
                "scheduled": False,
                "skipped": True,
                "reason": "already_warm",
                "game": game_key,
                "panels": list(panels),
                "identity": prediction_prewarm_identity_public(identity),
                "last": last,
                "generatedAt": utc_now_iso(),
            }
        PREDICTION_PREWARM_IN_FLIGHT.add(identity)
        PREDICTION_PREWARM_LAST[game_key] = {
            "ok": True,
            "status": "scheduled",
            "scheduled": True,
            "game": game_key,
            "panels": list(panels),
            "nowValues": list(now_values),
            "identity": prediction_prewarm_identity_public(identity),
            "reason": reason,
            "generatedAt": utc_now_iso(),
        }

    worker = threading.Thread(
        target=run_prediction_prewarm,
        args=(game_key, identity, panels, now_values, reason),
        daemon=True,
    )
    worker.start()
    return {
        "ok": True,
        "scheduled": True,
        "status": "scheduled",
        "game": game_key,
        "panels": list(panels),
        "nowValues": list(now_values),
        "identity": prediction_prewarm_identity_public(identity),
        "reason": reason,
        "generatedAt": utc_now_iso(),
    }


def schedule_startup_prediction_prewarm() -> list[dict[str, Any]]:
    auto_config = load_prediction_auto_config()
    enabled_keys = prediction_auto_enabled_games(auto_config)
    if not enabled_keys:
        enabled_keys = [
            key
            for key in PREDICTION_PREWARM_GAME_KEYS
            if key in LOTTERY_GAMES and supports_predictions(LOTTERY_GAMES[key])
        ]
    results: list[dict[str, Any]] = []
    for key in enabled_keys:
        game_config = LOTTERY_GAMES.get(key)
        if game_config is None:
            continue
        results.append(schedule_prediction_prewarm(game_config, reason="server_startup"))
    return results


CDE_KILL_BACKTEST_GAME_KEYS = {
    "spain_l_express_20_70",
    "poland_keno_20_70",
}
CDE_KILL_BACKTEST_MAX_WINDOW = 60
CDE_KILL_BACKTEST_MAX_TRAIN_WINDOW = 360
CDE_KILL_BACKTEST_MAX_DETAIL_LIMIT = 60


def prediction_context_tickets(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    include_c: bool = False,
    include_d: bool = False,
) -> dict[str, Any]:
    frequency = {item["number"]: item for item in number_frequency(rows, config)}
    recent_window = min(PREDICTION_RECENT_WINDOW, len(rows))
    recent_counts = recent_number_counts(rows, recent_window, config)
    draw_count = len(rows)
    bonus_sets = bonus_ball_prediction_sets(rows, config, recent_window)
    recent_eval_window = min(PREDICTION_TICKET_BACKTEST_WINDOW, draw_count)
    draw_sets_oldest = [set(row.get("numbers") or []) for row in reversed(rows)]
    bonus_values_oldest = [parse_int(row.get("bonusBall"), 0) for row in reversed(rows)]
    recent_rows = rows[:recent_eval_window]
    recent_draw_sets = [set(row.get("numbers") or []) for row in recent_rows]
    recent_bonus_values = [parse_int(row.get("bonusBall"), 0) for row in recent_rows]
    stats_index = ticket_stats_index(draw_sets_oldest, bonus_values_oldest, recent_draw_sets)
    a_tickets = prediction_strategy_tickets(
        rows,
        config,
        frequency,
        recent_counts,
        recent_window,
        bonus_sets,
        draw_sets_oldest,
        bonus_values_oldest,
        recent_draw_sets,
        recent_bonus_values,
        panel=PREDICTION_PANEL_DEFAULT,
        stats_index=stats_index,
    )
    a_kill_numbers = prediction_kill_numbers_from_tickets(a_tickets)
    b_tickets = prediction_strategy_tickets(
        rows,
        config,
        frequency,
        recent_counts,
        recent_window,
        bonus_sets,
        draw_sets_oldest,
        bonus_values_oldest,
        recent_draw_sets,
        recent_bonus_values,
        panel=PREDICTION_PANEL_B,
        excluded_numbers=set(a_kill_numbers),
        stats_index=stats_index,
    )
    c_tickets = (
        prediction_panel_c_structure_tickets(
            rows,
            config,
            a_tickets,
            b_tickets,
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            stats_index=stats_index,
        )
        if include_c
        else []
    )
    c_kill_numbers = prediction_kill_numbers_from_tickets(c_tickets)
    m_tickets = prediction_panel_m_low_group_tickets(
        rows,
        config,
        a_tickets,
        b_tickets,
        frequency,
        recent_counts,
        recent_window,
        draw_sets_oldest,
        bonus_values_oldest,
        recent_draw_sets,
        recent_bonus_values,
        stats_index=stats_index,
    )
    d_tickets = (
        prediction_panel_d_observation_tickets(
            rows,
            config,
            a_tickets,
            b_tickets,
            m_tickets,
            frequency,
            recent_counts,
            recent_window,
            draw_sets_oldest,
            bonus_values_oldest,
            recent_draw_sets,
            recent_bonus_values,
            stats_index=stats_index,
        )
        if include_d
        else []
    )
    d_excluded_numbers: list[int] = []
    number_signals = {
        number: {
            "number": number,
            "currentMiss": parse_int(item.get("currentMiss"), 0),
            "longHits": parse_int(item.get("hits"), 0),
            "longHitRate": parse_float(item.get("hitRate"), 0),
            "recentHits": parse_int(recent_counts.get(number, 0), 0),
            "recentWindow": recent_window,
            "recentHitRate": parse_int(recent_counts.get(number, 0), 0) / recent_window if recent_window else 0,
        }
        for number, item in frequency.items()
    }
    return {
        "aTickets": a_tickets,
        "bTickets": b_tickets,
        "cTickets": c_tickets,
        "dTickets": d_tickets,
        "mTickets": m_tickets,
        "cKillNumbers": c_kill_numbers,
        "dKillNumbers": d_excluded_numbers,
        "numberSignals": number_signals,
    }


def cde_kill_backtest_panel_result(kill_numbers: list[int], target_row: dict[str, Any]) -> dict[str, Any]:
    kill_numbers = sorted({int(number) for number in kill_numbers if int(number) > 0})
    draw_numbers = sorted({int(number) for number in target_row.get("numbers") or []})
    draw_set = set(draw_numbers)
    wrong_numbers = [number for number in kill_numbers if number in draw_set]
    right_numbers = [number for number in kill_numbers if number not in draw_set]
    kill_count = len(kill_numbers)
    wrong_count = len(wrong_numbers)
    right_count = len(right_numbers)
    return {
        "killNumbers": kill_numbers,
        "killCount": kill_count,
        "rightKilledNumbers": right_numbers,
        "rightKillCount": right_count,
        "wrongKilledNumbers": wrong_numbers,
        "wrongKillCount": wrong_count,
        "rightKillRate": right_count / kill_count if kill_count else 0,
        "wrongKillRate": wrong_count / kill_count if kill_count else 0,
    }


def cde_prediction_backtest_panel_result(numbers: list[int], target_row: dict[str, Any]) -> dict[str, Any]:
    numbers = sorted({int(number) for number in numbers if int(number) > 0})
    draw_numbers = sorted({int(number) for number in target_row.get("numbers") or []})
    draw_set = set(draw_numbers)
    hit_numbers = [number for number in numbers if number in draw_set]
    miss_numbers = [number for number in numbers if number not in draw_set]
    pick_count = len(numbers)
    hit_count = len(hit_numbers)
    miss_count = len(miss_numbers)
    return {
        "pickNumbers": numbers,
        "pickCount": pick_count,
        "hitNumbers": hit_numbers,
        "hitCount": hit_count,
        "missNumbers": miss_numbers,
        "missCount": miss_count,
        "hitRate": hit_count / pick_count if pick_count else 0,
        "missRate": miss_count / pick_count if pick_count else 0,
        "killNumbers": numbers,
        "killCount": pick_count,
        "rightKilledNumbers": miss_numbers,
        "rightKillCount": miss_count,
        "wrongKilledNumbers": hit_numbers,
        "wrongKillCount": hit_count,
        "rightKillRate": miss_count / pick_count if pick_count else 0,
        "wrongKillRate": hit_count / pick_count if pick_count else 0,
    }


def cde_kill_backtest_summary(panel_results: list[dict[str, Any]], panel: str, label: str) -> dict[str, Any]:
    rounds = len(panel_results)
    kill_total = sum(parse_int(item.get("killCount"), 0) for item in panel_results)
    right_total = sum(parse_int(item.get("rightKillCount"), 0) for item in panel_results)
    wrong_total = sum(parse_int(item.get("wrongKillCount"), 0) for item in panel_results)
    wrong_counts: dict[int, int] = {}
    kill_counts: dict[int, int] = {}
    for item in panel_results:
        wrong_count = parse_int(item.get("wrongKillCount"), 0)
        kill_count = parse_int(item.get("killCount"), 0)
        wrong_counts[wrong_count] = wrong_counts.get(wrong_count, 0) + 1
        kill_counts[kill_count] = kill_counts.get(kill_count, 0) + 1
    average_wrong = wrong_total / rounds if rounds else 0
    average_right = right_total / rounds if rounds else 0
    average_kill = kill_total / rounds if rounds else 0
    zero_wrong = wrong_counts.get(0, 0)
    one_or_less_wrong = sum(count for wrong_count, count in wrong_counts.items() if wrong_count <= 1)
    two_or_less_wrong = sum(count for wrong_count, count in wrong_counts.items() if wrong_count <= 2)
    return {
        "panel": panel,
        "label": label,
        "rounds": rounds,
        "killTotal": kill_total,
        "rightKillTotal": right_total,
        "wrongKillTotal": wrong_total,
        "averageKillCount": average_kill,
        "averageRightKillCount": average_right,
        "averageWrongKillCount": average_wrong,
        "rightKillRate": right_total / kill_total if kill_total else 0,
        "wrongKillRate": wrong_total / kill_total if kill_total else 0,
        "zeroWrongRounds": zero_wrong,
        "zeroWrongRate": zero_wrong / rounds if rounds else 0,
        "oneOrLessWrongRounds": one_or_less_wrong,
        "oneOrLessWrongRate": one_or_less_wrong / rounds if rounds else 0,
        "twoOrLessWrongRounds": two_or_less_wrong,
        "twoOrLessWrongRate": two_or_less_wrong / rounds if rounds else 0,
        "wrongDistribution": [
            {"wrongKillCount": count, "rounds": rounds_count, "share": rounds_count / rounds if rounds else 0}
            for count, rounds_count in sorted(wrong_counts.items())
        ],
        "killCountDistribution": [
            {"killCount": count, "rounds": rounds_count, "share": rounds_count / rounds if rounds else 0}
            for count, rounds_count in sorted(kill_counts.items())
        ],
    }


def prediction_hit_backtest_summary(panel_results: list[dict[str, Any]], panel: str, label: str) -> dict[str, Any]:
    summary = cde_kill_backtest_summary(panel_results, panel, label)
    summary["metricType"] = "prediction_hit"
    summary["hitTotal"] = summary["wrongKillTotal"]
    summary["missTotal"] = summary["rightKillTotal"]
    summary["averageHitCount"] = summary["averageWrongKillCount"]
    summary["averageMissCount"] = summary["averageRightKillCount"]
    summary["hitRate"] = summary["wrongKillRate"]
    summary["missRate"] = summary["rightKillRate"]
    summary["zeroHitRounds"] = summary["zeroWrongRounds"]
    summary["zeroHitRate"] = summary["zeroWrongRate"]
    summary["hitDistribution"] = [
        {
            "hitCount": parse_int(item.get("wrongKillCount"), 0),
            "rounds": parse_int(item.get("rounds"), 0),
            "share": parse_float(item.get("share"), 0),
        }
        for item in summary.get("wrongDistribution", [])
    ]
    return summary


def cde_bucket_miss_label(current_miss: int) -> str:
    if current_miss <= 3:
        return "遗漏0-3"
    if current_miss <= 8:
        return "遗漏4-8"
    if current_miss <= 16:
        return "遗漏9-16"
    if current_miss <= 32:
        return "遗漏17-32"
    return "遗漏33+"


def cde_bucket_recent_label(recent_hit_rate: float, baseline_rate: float) -> str:
    if recent_hit_rate >= baseline_rate * 1.2:
        return "近期热"
    if recent_hit_rate <= baseline_rate * 0.8:
        return "近期冷"
    return "近期平"


def cde_bucket_consensus_label(consensus_count: int) -> str:
    if consensus_count >= 3:
        return "多池共杀"
    if consensus_count == 2:
        return "两池共杀"
    return "C单池"


def cde_bucket_number_range_label(number: int, total_numbers: int) -> str:
    if total_numbers <= 0:
        return "区间--"
    bucket_size = 10
    start = ((max(1, number) - 1) // bucket_size) * bucket_size + 1
    end = min(total_numbers, start + bucket_size - 1)
    return f"{start}-{end}区"


def cde_bucket_add(
    buckets: dict[tuple[str, str, str], dict[str, Any]],
    dimension: str,
    key: str,
    label: str,
    *,
    killed: bool,
    baseline_rate: float,
) -> None:
    bucket_key = (dimension, key, label)
    bucket = buckets.setdefault(
        bucket_key,
        {
            "dimension": dimension,
            "key": key,
            "label": label,
            "killTotal": 0,
            "wrongTotal": 0,
            "rightTotal": 0,
            "baselineWrongTotal": 0.0,
        },
    )
    bucket["killTotal"] += 1
    if killed:
        bucket["wrongTotal"] += 1
    else:
        bucket["rightTotal"] += 1
    bucket["baselineWrongTotal"] += baseline_rate


def cde_bucket_finalize(
    buckets: dict[tuple[str, str, str], dict[str, Any]],
    *,
    rounds: int,
    baseline_rate: float,
    min_samples: int = 20,
    limit: int = 40,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in buckets.values():
        kill_total = parse_int(item.get("killTotal"), 0)
        if kill_total < min_samples:
            continue
        wrong_total = parse_int(item.get("wrongTotal"), 0)
        right_total = parse_int(item.get("rightTotal"), 0)
        wrong_rate = wrong_total / kill_total if kill_total else 0
        baseline_wrong_total = parse_float(item.get("baselineWrongTotal"), 0)
        wrong_lift = wrong_rate - baseline_rate
        rows.append(
            {
                **item,
                "rounds": rounds,
                "wrongRate": wrong_rate,
                "baselineWrongRate": baseline_rate,
                "wrongRateLift": wrong_lift,
                "expectedWrongTotal": baseline_wrong_total,
                "wrongTotalLift": wrong_total - baseline_wrong_total,
                "averageKillPerRound": kill_total / rounds if rounds else 0,
                "rescueWrongSaved": wrong_total,
                "rescueRightLost": right_total,
                "rescueTradeoff": wrong_total / right_total if right_total else None,
                "verdict": "可救观察" if wrong_lift >= 0.02 else "可杀观察" if wrong_lift <= -0.02 else "接近随机",
            }
        )
    rows.sort(
        key=lambda item: (
            -abs(parse_float(item.get("wrongRateLift"), 0)),
            -parse_int(item.get("killTotal"), 0),
            str(item.get("dimension") or ""),
            str(item.get("label") or ""),
        )
    )
    return rows[:limit]


def cde_kill_bucket_audit(
    samples: list[dict[str, Any]],
    config: dict[str, Any],
    rounds: int,
) -> dict[str, Any]:
    baseline_rate = int(config["drawnNumbers"]) / int(config["totalNumbers"])
    buckets: dict[tuple[str, str, str], dict[str, Any]] = {}
    for sample in samples:
        panel = str(sample.get("panel") or "")
        number = parse_int(sample.get("number"), 0)
        if not panel or number <= 0:
            continue
        wrong = bool(sample.get("wrong"))
        current_miss = parse_int(sample.get("currentMiss"), 0)
        recent_hit_rate = parse_float(sample.get("recentHitRate"), 0)
        consensus_count = parse_int(sample.get("consensusCount"), 0)
        previous_repeat = bool(sample.get("previousRepeat"))
        panel_label = prediction_panel_label(panel).replace("预测面板", "")
        cde_bucket_add(buckets, "面板", panel, panel_label, killed=wrong, baseline_rate=baseline_rate)
        miss_label = cde_bucket_miss_label(current_miss)
        cde_bucket_add(buckets, "遗漏", miss_label, miss_label, killed=wrong, baseline_rate=baseline_rate)
        recent_label = cde_bucket_recent_label(recent_hit_rate, baseline_rate)
        cde_bucket_add(buckets, "冷热", recent_label, recent_label, killed=wrong, baseline_rate=baseline_rate)
        repeat_label = "上期重复" if previous_repeat else "非上期重复"
        cde_bucket_add(buckets, "重复", repeat_label, repeat_label, killed=wrong, baseline_rate=baseline_rate)
        consensus_label = cde_bucket_consensus_label(consensus_count)
        cde_bucket_add(buckets, "共识", consensus_label, consensus_label, killed=wrong, baseline_rate=baseline_rate)
        range_label = cde_bucket_number_range_label(number, int(config["totalNumbers"]))
        cde_bucket_add(buckets, "区间", range_label, range_label, killed=wrong, baseline_rate=baseline_rate)

    rows = cde_bucket_finalize(buckets, rounds=rounds, baseline_rate=baseline_rate)
    rescue_candidates = [item for item in rows if parse_float(item.get("wrongRateLift"), 0) >= 0.02]
    kill_candidates = [item for item in rows if parse_float(item.get("wrongRateLift"), 0) <= -0.02]
    return {
        "baselineWrongRate": baseline_rate,
        "sampleTotal": len(samples),
        "wrongTotal": sum(1 for item in samples if item.get("wrong")),
        "rightTotal": sum(1 for item in samples if not item.get("wrong")),
        "buckets": rows,
        "rescueCandidates": rescue_candidates[:8],
        "killCandidates": kill_candidates[:8],
        "notes": [
            "分桶只统计 C 被杀号码；错杀率高于随机的桶适合观察救出，低于随机的桶才更像有效杀号。",
            "救出效果表示如果这个桶不杀，理论上少错杀多少，同时少杀对多少。",
        ],
    }


def cde_kill_backtest_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_predictions_supported(config)
    if str(config["key"]) not in CDE_KILL_BACKTEST_GAME_KEYS:
        raise ValueError("C 杀号回测当前只支持西班牙和波兰")
    history_path = game_history_path(config)
    window = max(10, min(parse_int(query.get("window", ["30"])[0], 30), CDE_KILL_BACKTEST_MAX_WINDOW))
    train_window = max(80, min(parse_int(query.get("trainWindow", ["240"])[0], 240), CDE_KILL_BACKTEST_MAX_TRAIN_WINDOW))
    detail_limit = max(20, min(parse_int(query.get("detailLimit", ["60"])[0], 60), CDE_KILL_BACKTEST_MAX_DETAIL_LIMIT))
    with DATA_LOCK:
        try:
            stat = history_path.stat()
            cache_key = (config["key"], stat.st_mtime_ns, stat.st_size, window, train_window, detail_limit)
        except FileNotFoundError:
            cache_key = (config["key"], 0, 0, window, train_window, detail_limit)

    with KILL_BACKTEST_CACHE_LOCK:
        cached = lru_cache_get(KILL_BACKTEST_CACHE, cache_key)
    if cached is not None:
        payload = dict(cached)
        payload["cacheHit"] = True
        payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
        return payload

    started = time.monotonic()
    with DATA_LOCK:
        all_rows = load_history_rows(history_path, config)
    data_integrity = history_data_integrity(all_rows, config)
    rows = valid_draw_rows(all_rows, config)
    if len(rows) < 100:
        raise ValueError("有效历史少于 100 期，暂不能做 C 杀号回测")

    rows_oldest = list(reversed(rows))
    max_rounds = max(0, min(window, len(rows_oldest) - 80))
    start_index = max(80, len(rows_oldest) - max_rounds)
    detail_items: list[dict[str, Any]] = []
    panel_items: dict[str, list[dict[str, Any]]] = {
        PREDICTION_PANEL_C: [],
    }
    cde_bucket_samples: list[dict[str, Any]] = []
    skipped = 0
    for index in range(start_index, len(rows_oldest)):
        target = rows_oldest[index]
        history_slice_oldest = rows_oldest[max(0, index - train_window) : index]
        history_rows = list(reversed(history_slice_oldest))
        if len(history_rows) < 80:
            skipped += 1
            continue
        tickets = prediction_context_tickets(history_rows, config, include_c=True)
        panel_result_map = {
            PREDICTION_PANEL_C: cde_kill_backtest_panel_result(tickets["cKillNumbers"], target),
        }
        for panel, panel_result in panel_result_map.items():
            panel_items[panel].append(panel_result)
        target_draw_set = {parse_int(number, 0) for number in target.get("numbers") or []}
        previous_draw_set = {parse_int(number, 0) for number in (history_rows[0].get("numbers") if history_rows else []) or []}
        number_signals = tickets.get("numberSignals") if isinstance(tickets.get("numberSignals"), dict) else {}
        kill_sets = {
            PREDICTION_PANEL_C: {parse_int(number, 0) for number in tickets.get("cKillNumbers") or []},
        }
        cde_panels = (PREDICTION_PANEL_C,)
        for panel in cde_panels:
            for number in sorted(number for number in kill_sets[panel] if number > 0):
                signal = number_signals.get(number) or number_signals.get(str(number)) or {}
                cde_bucket_samples.append(
                    {
                        "panel": panel,
                        "number": number,
                        "wrong": number in target_draw_set,
                        "currentMiss": parse_int(signal.get("currentMiss"), 0),
                        "recentHits": parse_int(signal.get("recentHits"), 0),
                        "recentWindow": parse_int(signal.get("recentWindow"), 0),
                        "recentHitRate": parse_float(signal.get("recentHitRate"), 0),
                        "longHitRate": parse_float(signal.get("longHitRate"), 0),
                        "previousRepeat": number in previous_draw_set,
                        "consensusCount": sum(1 for candidate_panel in cde_panels if number in kill_sets[candidate_panel]),
                    }
                )
        detail_items.append(
            {
                "drawIndex": index + 1,
                "drawEventId": target.get("drawEventId", ""),
                "drawTimeMs": parse_int(target.get("drawTimeMs"), 0),
                "drawTimeUtc": target.get("drawTimeUtc", ""),
                "drawNumbers": target.get("numbers") or [],
                "panels": panel_result_map,
            }
        )

    kill_panel_summaries = [
        cde_kill_backtest_summary(panel_items[PREDICTION_PANEL_C], PREDICTION_PANEL_C, "C 四码票唯一号"),
    ]
    panel_summaries = kill_panel_summaries
    best_panel = min(
        kill_panel_summaries,
        key=lambda item: (
            parse_float(item.get("averageWrongKillCount"), 999),
            parse_float(item.get("wrongKillRate"), 999),
            -parse_float(item.get("averageRightKillCount"), 0),
        ),
    ) if kill_panel_summaries else None
    newest = rows[0] if rows else None
    oldest = rows[-1] if rows else None
    detail_items = sorted(detail_items, key=lambda item: parse_int(item.get("drawTimeMs"), 0), reverse=True)[:detail_limit]
    actual_rounds = sum(1 for _ in panel_items[PREDICTION_PANEL_C])
    kill_bucket_audit = cde_kill_bucket_audit(cde_bucket_samples, config, actual_rounds)
    payload = {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "cacheHit": False,
        "game": game_public_config(config),
        "historyFile": file_info(history_path),
        "dataIntegrity": data_integrity,
        "drawCount": len(rows),
        "newestDraw": newest,
        "oldestDraw": oldest,
        "window": window,
        "actualRounds": actual_rounds,
        "skippedRounds": skipped,
        "trainWindow": train_window,
        "detailLimit": detail_limit,
        "elapsedMs": round((time.monotonic() - started) * 1000),
        "bestPanel": best_panel,
        "summaries": panel_summaries,
        "killBucketAudit": kill_bucket_audit,
        "items": detail_items,
        "notes": [
            "杀错 = 杀号池与当期开奖主号的交集，数字越低越好。",
            "杀对 = 杀号池中没有开出的号码，数字越高说明排除池避开了开奖号。",
            "错杀分桶只做观察，不会自动救号或修改正式预测。",
            "每期只使用目标开奖之前的历史生成 C 结果，不读取未来开奖。",
        ],
    }
    payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
    with KILL_BACKTEST_CACHE_LOCK:
        lru_cache_set(KILL_BACKTEST_CACHE, cache_key, payload, KILL_BACKTEST_CACHE_MAX_ITEMS)
    return payload


STRATEGY_SIGNAL_AUDIT_GAME_KEYS = {
    "spain_l_express_20_70",
    "poland_keno_20_70",
    "russia_rapido_8_20",
    "italy_win_for_life_10_20",
}
STRATEGY_SIGNAL_AUDIT_MAX_WINDOW = 360
STRATEGY_SIGNAL_AUDIT_MAX_TRAIN_WINDOW = 600
STRATEGY_SIGNAL_AUDIT_MIN_TRAIN_WINDOW = 120
STRATEGY_SIGNAL_AUDIT_WINDOWS = (60, 180, 360)
STRATEGY_SIGNAL_AUDIT_TICKET_PANELS = (
    PREDICTION_PANEL_DEFAULT,
    PREDICTION_PANEL_B,
    PREDICTION_PANEL_M,
)
STRATEGY_SIGNAL_AUDIT_E_TOP_COUNTS = (1, 2, 3, 5, 8)
STRATEGY_SIGNAL_AUDIT_MIXED_BUY_RULES = (
    {
        "key": "e_top8",
        "label": "E Top8 原规则",
        "referenceKey": "e_top8",
        "category": "e_cost",
        "description": "E 原始8组四码，作为成本压缩基准。",
    },
    {
        "key": "e_top5",
        "label": "E Top5 压缩",
        "referenceKey": "e_top8",
        "category": "e_cost",
        "description": "只保留E前5组四码，观察少买3组后的漏中。",
    },
)
STRATEGY_SIGNAL_AUDIT_MIXED_KILL_RULES = (
    {
        "key": "kill_c",
        "label": "C 单池主杀",
        "category": "single_kill",
        "description": "C候选杀号池单独作为主杀。",
    },
    {
        "key": "kill_d",
        "label": "D 单池主杀",
        "category": "single_kill",
        "description": "D候选杀号池单独作为主杀。",
    },
    {
        "key": "kill_e",
        "label": "E 单池主杀",
        "category": "single_kill",
        "description": "E候选杀号池单独作为主杀。",
    },
    {
        "key": "kill_cd_union",
        "label": "C∪D 合并主杀",
        "category": "cde_union",
        "description": "C和D杀号池取并集，观察扩大杀池后的错杀。",
    },
    {
        "key": "kill_de_union",
        "label": "D∪E 合并主杀",
        "category": "cde_union",
        "description": "D和E杀号池取并集，观察嵌套链路中后段合并效果。",
    },
    {
        "key": "kill_cde_union",
        "label": "C∪D∪E 合并主杀",
        "category": "cde_union",
        "description": "C/D/E杀号池取并集，通常成本最低但误伤风险最高。",
    },
    {
        "key": "kill_cd_intersection",
        "label": "C∩D 共识主杀",
        "category": "cde_intersection",
        "description": "C和D同时给出的号码才杀，观察小池稳定性。",
    },
    {
        "key": "kill_de_intersection",
        "label": "D∩E 共识主杀",
        "category": "cde_intersection",
        "description": "D和E同时给出的号码才杀，观察后段共识稳定性。",
    },
    {
        "key": "kill_cde_intersection",
        "label": "C∩D∩E 共识主杀",
        "category": "cde_intersection",
        "description": "C/D/E三者都给出的号码才杀，观察极小共识池。",
    },
)


def strategy_audit_hit_distribution(max_hits: int = 4) -> dict[int, int]:
    return {index: 0 for index in range(max_hits + 1)}


def strategy_audit_eval_ticket(
    ticket: dict[str, Any],
    target_row: dict[str, Any],
    previous_row: dict[str, Any] | None,
) -> dict[str, Any]:
    numbers = sorted({parse_int(number, 0) for number in ticket.get("numbers") or [] if parse_int(number, 0) > 0})
    draw_set = set(target_row.get("numbers") or [])
    previous_set = set(previous_row.get("numbers") or []) if previous_row else set()
    hit_numbers = [number for number in numbers if number in draw_set]
    previous_numbers = [number for number in numbers if number in previous_set]
    return {
        "numbers": numbers,
        "pickCount": len(numbers),
        "hitNumbers": hit_numbers,
        "hitCount": len(hit_numbers),
        "previousNumbers": previous_numbers,
        "previousOverlap": len(previous_numbers),
    }


def strategy_audit_add_ticket_result(
    summary: dict[str, Any],
    result: dict[str, Any],
    *,
    stake: float = 1.0,
    odds: float = 150.0,
) -> None:
    pick_count = parse_int(result.get("pickCount"), 0)
    hit_count = parse_int(result.get("hitCount"), 0)
    previous_overlap = parse_int(result.get("previousOverlap"), 0)
    won = hit_count >= pick_count and pick_count > 0
    summary["tickets"] += 1
    summary["stake"] += stake
    summary["numberPicks"] += pick_count
    summary["numberHits"] += hit_count
    summary["won"] += 1 if won else 0
    summary["twoPlus"] += 1 if hit_count >= 2 else 0
    summary["threePlus"] += 1 if hit_count >= 3 else 0
    summary["payout"] += stake * odds if won else 0
    summary["profit"] += stake * odds - stake if won else -stake
    hit_distribution = summary.setdefault("hitDistribution", strategy_audit_hit_distribution(pick_count or 4))
    hit_distribution[hit_count] = hit_distribution.get(hit_count, 0) + 1
    overlap_distribution = summary.setdefault("previousOverlapDistribution", {})
    overlap_item = overlap_distribution.setdefault(
        previous_overlap,
        {
            "previousOverlap": previous_overlap,
            "tickets": 0,
            "numberPicks": 0,
            "numberHits": 0,
            "won": 0,
            "twoPlus": 0,
            "threePlus": 0,
        },
    )
    overlap_item["tickets"] += 1
    overlap_item["numberPicks"] += pick_count
    overlap_item["numberHits"] += hit_count
    overlap_item["won"] += 1 if won else 0
    overlap_item["twoPlus"] += 1 if hit_count >= 2 else 0
    overlap_item["threePlus"] += 1 if hit_count >= 3 else 0


def strategy_audit_empty_ticket_summary(label: str, top_count: int | None = None) -> dict[str, Any]:
    return {
        "label": label,
        "topCount": top_count,
        "tickets": 0,
        "stake": 0.0,
        "numberPicks": 0,
        "numberHits": 0,
        "won": 0,
        "twoPlus": 0,
        "threePlus": 0,
        "payout": 0.0,
        "profit": 0.0,
        "hitDistribution": strategy_audit_hit_distribution(4),
        "previousOverlapDistribution": {},
    }


def strategy_audit_finalize_ticket_summary(
    summary: dict[str, Any],
    config: dict[str, Any],
    *,
    pick_count: int = 4,
    odds: float = 150.0,
) -> dict[str, Any]:
    tickets = parse_int(summary.get("tickets"), 0)
    stake = parse_float(summary.get("stake"), 0)
    number_picks = parse_int(summary.get("numberPicks"), 0)
    won = parse_int(summary.get("won"), 0)
    theoretical = hit_probability_for(config, pick_count)
    result = dict(summary)
    result["hitRate"] = won / tickets if tickets else 0
    ci_low, ci_high = wilson_interval(won, tickets)
    result["hitRateCi"] = [ci_low, ci_high]
    result["numberHitRate"] = parse_int(summary.get("numberHits"), 0) / number_picks if number_picks else 0
    result["twoPlusRate"] = parse_int(summary.get("twoPlus"), 0) / tickets if tickets else 0
    result["threePlusRate"] = parse_int(summary.get("threePlus"), 0) / tickets if tickets else 0
    result["roi"] = parse_float(summary.get("profit"), 0) / stake if stake else 0
    result["theoreticalHitRate"] = theoretical
    result["hitRateVsTheory"] = result["hitRate"] - theoretical
    result["expectedWins"] = tickets * theoretical
    result["winLift"] = won - result["expectedWins"]
    result["breakEvenHitRate"] = 1 / odds if odds > 0 else 0
    result["theoreticalRoi"] = theoretical * odds - 1 if odds > 0 else 0
    result["hitDistribution"] = [
        {
            "hitCount": count,
            "tickets": rounds,
            "share": rounds / tickets if tickets else 0,
        }
        for count, rounds in sorted((summary.get("hitDistribution") or {}).items())
    ]
    overlap_items = []
    for _, item in sorted((summary.get("previousOverlapDistribution") or {}).items()):
        item_tickets = parse_int(item.get("tickets"), 0)
        item_picks = parse_int(item.get("numberPicks"), 0)
        overlap_items.append(
            {
                **item,
                "numberHitRate": parse_int(item.get("numberHits"), 0) / item_picks if item_picks else 0,
                "fourHitRate": parse_int(item.get("won"), 0) / item_tickets if item_tickets else 0,
                "twoPlusRate": parse_int(item.get("twoPlus"), 0) / item_tickets if item_tickets else 0,
                "threePlusRate": parse_int(item.get("threePlus"), 0) / item_tickets if item_tickets else 0,
            }
        )
    result["previousOverlapDistribution"] = overlap_items
    return result


def strategy_audit_empty_panel_ticket_summary(
    *,
    key: str,
    panel: str,
    mode: str,
    pick_count: int,
    label: str,
    odds: float,
) -> dict[str, Any]:
    summary = strategy_audit_empty_ticket_summary(label)
    summary.update(
        {
            "key": key,
            "panel": prediction_panel_from_value(panel),
            "mode": mode,
            "pickCount": pick_count,
            "odds": odds,
            "hitDistribution": strategy_audit_hit_distribution(pick_count),
        }
    )
    return summary


def strategy_audit_ticket_summary_key(panel: str, ticket: dict[str, Any]) -> tuple[str, str, int]:
    panel_key = prediction_panel_from_value(panel)
    mode = str(ticket.get("mode") or "main")
    pick_count = parse_int(ticket.get("pickCount"), len(ticket.get("numbers") or []))
    return panel_key, mode, pick_count


def strategy_audit_add_ticket_panel_results(
    ticket_data: dict[str, dict[str, dict[str, Any]]],
    *,
    panel: str,
    tickets: list[dict[str, Any]],
    target_row: dict[str, Any],
    previous_row: dict[str, Any] | None,
    config: dict[str, Any],
) -> None:
    panel_key = prediction_panel_from_value(panel)
    panel_bucket = ticket_data.setdefault(panel_key, {})
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        numbers = [parse_int(number, 0) for number in ticket.get("numbers") or [] if parse_int(number, 0) > 0]
        if not numbers:
            continue
        current_panel, mode, pick_count = strategy_audit_ticket_summary_key(panel_key, ticket)
        if pick_count <= 0 or mode != "main":
            continue
        key = f"{current_panel}:{mode}:{pick_count}"
        odds = parse_float(
            ticket.get("odds"),
            DEFAULT_MAIN_ODDS_BY_GAME.get(str(config.get("key")), {}).get(pick_count, 0),
        )
        summary = panel_bucket.setdefault(
            key,
            strategy_audit_empty_panel_ticket_summary(
                key=key,
                panel=current_panel,
                mode=mode,
                pick_count=pick_count,
                label=f"{prediction_panel_label(current_panel)} {pick_count}码官方票",
                odds=odds,
            ),
        )
        strategy_audit_add_ticket_result(
            summary,
            strategy_audit_eval_ticket(ticket, target_row, previous_row),
            stake=1,
            odds=odds,
        )


def strategy_audit_finalize_panel_ticket_summary(
    summary: dict[str, Any],
    config: dict[str, Any],
    *,
    rounds: int,
) -> dict[str, Any]:
    pick_count = parse_int(summary.get("pickCount"), 0)
    odds = parse_float(summary.get("odds"), DEFAULT_MAIN_ODDS_BY_GAME.get(str(config.get("key")), {}).get(pick_count, 0))
    result = strategy_audit_finalize_ticket_summary(
        summary,
        config,
        pick_count=pick_count,
        odds=odds,
    )
    result["rounds"] = rounds
    result["averageTicketsPerRound"] = parse_int(result.get("tickets"), 0) / rounds if rounds else 0
    return result


def strategy_audit_empty_kill_summary(panel: str, label: str) -> dict[str, Any]:
    return {
        "panel": panel,
        "label": label,
        "rounds": 0,
        "poolTotal": 0,
        "wrongTotal": 0,
        "rightTotal": 0,
        "zeroWrongRounds": 0,
        "oneOrLessWrongRounds": 0,
        "twoOrLessWrongRounds": 0,
        "wrongDistribution": {},
        "poolSizeDistribution": {},
    }


def strategy_audit_add_kill_result(summary: dict[str, Any], kill_numbers: list[int], target_row: dict[str, Any]) -> None:
    numbers = sorted({int(number) for number in kill_numbers if int(number) > 0})
    draw_set = set(target_row.get("numbers") or [])
    wrong_count = sum(1 for number in numbers if number in draw_set)
    pool_size = len(numbers)
    summary["rounds"] += 1
    summary["poolTotal"] += pool_size
    summary["wrongTotal"] += wrong_count
    summary["rightTotal"] += pool_size - wrong_count
    summary["zeroWrongRounds"] += 1 if wrong_count == 0 else 0
    summary["oneOrLessWrongRounds"] += 1 if wrong_count <= 1 else 0
    summary["twoOrLessWrongRounds"] += 1 if wrong_count <= 2 else 0
    summary["wrongDistribution"][wrong_count] = summary["wrongDistribution"].get(wrong_count, 0) + 1
    summary["poolSizeDistribution"][pool_size] = summary["poolSizeDistribution"].get(pool_size, 0) + 1


def strategy_audit_finalize_kill_summary(summary: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    rounds = parse_int(summary.get("rounds"), 0)
    pool_total = parse_int(summary.get("poolTotal"), 0)
    baseline = parse_int(config.get("drawnNumbers"), 0) / parse_int(config.get("totalNumbers"), 1)
    wrong_rate = parse_int(summary.get("wrongTotal"), 0) / pool_total if pool_total else 0
    return {
        **summary,
        "averagePoolSize": pool_total / rounds if rounds else 0,
        "averageWrong": parse_int(summary.get("wrongTotal"), 0) / rounds if rounds else 0,
        "averageRight": parse_int(summary.get("rightTotal"), 0) / rounds if rounds else 0,
        "wrongRate": wrong_rate,
        "rightRate": parse_int(summary.get("rightTotal"), 0) / pool_total if pool_total else 0,
        "baselineWrongRate": baseline,
        "wrongRateLift": wrong_rate - baseline,
        "zeroWrongRate": parse_int(summary.get("zeroWrongRounds"), 0) / rounds if rounds else 0,
        "oneOrLessWrongRate": parse_int(summary.get("oneOrLessWrongRounds"), 0) / rounds if rounds else 0,
        "twoOrLessWrongRate": parse_int(summary.get("twoOrLessWrongRounds"), 0) / rounds if rounds else 0,
        "wrongDistribution": [
            {"wrongCount": count, "rounds": value, "share": value / rounds if rounds else 0}
            for count, value in sorted((summary.get("wrongDistribution") or {}).items())
        ],
        "poolSizeDistribution": [
            {"poolSize": count, "rounds": value, "share": value / rounds if rounds else 0}
            for count, value in sorted((summary.get("poolSizeDistribution") or {}).items())
        ],
    }


def strategy_audit_repeat_baseline(config: dict[str, Any]) -> dict[str, Any]:
    total_numbers = parse_int(config.get("totalNumbers"), 0)
    drawn_numbers = parse_int(config.get("drawnNumbers"), 0)
    if total_numbers <= 0 or drawn_numbers <= 0:
        return {"expectedOverlap": 0, "singleNumberRate": 0, "distribution": []}
    denominator = math.comb(total_numbers, drawn_numbers)
    low = max(0, drawn_numbers - (total_numbers - drawn_numbers))
    high = min(drawn_numbers, drawn_numbers)
    distribution = []
    for overlap in range(low, high + 1):
        probability = (
            math.comb(drawn_numbers, overlap)
            * math.comb(total_numbers - drawn_numbers, drawn_numbers - overlap)
            / denominator
        )
        distribution.append({"overlap": overlap, "probability": probability})
    expected = drawn_numbers * drawn_numbers / total_numbers
    variance = (
        drawn_numbers
        * (drawn_numbers / total_numbers)
        * (1 - drawn_numbers / total_numbers)
        * ((total_numbers - drawn_numbers) / (total_numbers - 1))
        if total_numbers > 1
        else 0
    )
    return {
        "expectedOverlap": expected,
        "sdOverlap": math.sqrt(variance),
        "singleNumberRate": drawn_numbers / total_numbers,
        "distribution": distribution,
    }


def strategy_audit_empty_repeat_summary(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "pairs": 0,
        "contiguousPairs": 0,
        "overlapTotal": 0,
        "overlapDistribution": {},
        "baseline": strategy_audit_repeat_baseline(config),
    }


def strategy_audit_add_repeat_result(
    summary: dict[str, Any],
    target_row: dict[str, Any],
    previous_row: dict[str, Any] | None,
    config: dict[str, Any],
) -> None:
    if previous_row is None:
        return
    previous_set = set(previous_row.get("numbers") or [])
    target_set = set(target_row.get("numbers") or [])
    overlap = len(previous_set & target_set)
    summary["pairs"] += 1
    summary["overlapTotal"] += overlap
    summary["overlapDistribution"][overlap] = summary["overlapDistribution"].get(overlap, 0) + 1
    interval_ms = int(float(config.get("drawIntervalMinutes") or 0) * 60000)
    gap_ms = parse_int(target_row.get("drawTimeMs"), 0) - parse_int(previous_row.get("drawTimeMs"), 0)
    if interval_ms <= 0 or (gap_ms > 0 and gap_ms <= int(interval_ms * 1.5)):
        summary["contiguousPairs"] += 1


def strategy_audit_finalize_repeat_summary(summary: dict[str, Any]) -> dict[str, Any]:
    pairs = parse_int(summary.get("pairs"), 0)
    baseline = summary.get("baseline") or {}
    expected = parse_float(baseline.get("expectedOverlap"), 0)
    sd = parse_float(baseline.get("sdOverlap"), 0)
    mean = parse_int(summary.get("overlapTotal"), 0) / pairs if pairs else 0
    drawn_numbers = parse_int(LOTTERY_GAMES.get(DEFAULT_GAME_KEY, {}).get("drawnNumbers"), 0)
    single_rate = parse_float(baseline.get("singleNumberRate"), 0)
    if single_rate > 0 and expected > 0:
        drawn_numbers = round(expected / single_rate)
    return {
        **summary,
        "averageOverlap": mean,
        "expectedOverlap": expected,
        "overlapLift": mean - expected,
        "meanZ": (mean - expected) / (sd / math.sqrt(pairs)) if pairs and sd > 0 else 0,
        "previousNumberHitRate": mean / drawn_numbers if drawn_numbers else 0,
        "baselinePreviousNumberHitRate": single_rate,
        "overlapDistribution": [
            {"overlap": count, "rounds": value, "share": value / pairs if pairs else 0}
            for count, value in sorted((summary.get("overlapDistribution") or {}).items())
        ],
    }


def strategy_audit_dedupe_ticket_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[int, ...]] = set()
    for result in results:
        numbers = tuple(sorted(parse_int(number, 0) for number in result.get("numbers") or [] if parse_int(number, 0) > 0))
        if not numbers or numbers in seen:
            continue
        seen.add(numbers)
        deduped.append(result)
    return deduped


def strategy_audit_ticket_results_by_previous_overlap(
    results: list[dict[str, Any]],
    minimum_overlap: int,
) -> list[dict[str, Any]]:
    return [result for result in results if parse_int(result.get("previousOverlap"), 0) >= minimum_overlap]


def strategy_audit_numbers_from_results(results: list[dict[str, Any]]) -> list[int]:
    numbers: set[int] = set()
    for result in results:
        numbers.update(parse_int(number, 0) for number in result.get("numbers") or [] if parse_int(number, 0) > 0)
    return sorted(numbers)


def strategy_audit_empty_mixed_buy_summary(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": rule["key"],
        "label": rule["label"],
        "referenceKey": rule.get("referenceKey") or rule["key"],
        "category": rule.get("category", ""),
        "description": rule.get("description", ""),
        "mode": "buy",
        "rounds": 0,
        "playedRounds": 0,
        "skippedRounds": 0,
        "ticketSummary": strategy_audit_empty_ticket_summary(str(rule["label"])),
        "maxHitDistribution": strategy_audit_hit_distribution(4),
        "ticketsPerRoundDistribution": {},
        "_playedRoundIds": set(),
        "_twoPlusRoundIds": set(),
        "_threePlusRoundIds": set(),
        "_fourHitRoundIds": set(),
    }


def strategy_audit_add_mixed_buy_round(
    summary: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    round_id: int,
    odds: float,
) -> None:
    deduped = strategy_audit_dedupe_ticket_results(results)
    ticket_count = len(deduped)
    summary["rounds"] += 1
    summary["ticketsPerRoundDistribution"][ticket_count] = summary["ticketsPerRoundDistribution"].get(ticket_count, 0) + 1
    if not deduped:
        summary["skippedRounds"] += 1
        summary["maxHitDistribution"][0] = summary["maxHitDistribution"].get(0, 0) + 1
        return

    summary["playedRounds"] += 1
    summary["_playedRoundIds"].add(round_id)
    max_hit = 0
    for result in deduped:
        hit_count = parse_int(result.get("hitCount"), 0)
        max_hit = max(max_hit, hit_count)
        strategy_audit_add_ticket_result(summary["ticketSummary"], result, odds=odds)
    summary["maxHitDistribution"][max_hit] = summary["maxHitDistribution"].get(max_hit, 0) + 1
    if max_hit >= 2:
        summary["_twoPlusRoundIds"].add(round_id)
    if max_hit >= 3:
        summary["_threePlusRoundIds"].add(round_id)
    if max_hit >= 4:
        summary["_fourHitRoundIds"].add(round_id)


def strategy_audit_mixed_buy_round_results(e_results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    e_top5 = e_results[:5]
    return {
        "e_top8": e_results[:8],
        "e_top5": e_top5,
    }


def strategy_audit_finalize_mixed_buy_summaries(
    summaries: dict[str, dict[str, Any]],
    config: dict[str, Any],
    *,
    odds: float,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    for rule in STRATEGY_SIGNAL_AUDIT_MIXED_BUY_RULES:
        summary = summaries[str(rule["key"])]
        rounds = parse_int(summary.get("rounds"), 0)
        played_rounds = parse_int(summary.get("playedRounds"), 0)
        ticket_summary = strategy_audit_finalize_ticket_summary(
            summary["ticketSummary"],
            config,
            pick_count=4,
            odds=odds,
        )
        max_hit_distribution = [
            {"hitCount": hit_count, "rounds": count, "share": count / rounds if rounds else 0}
            for hit_count, count in sorted((summary.get("maxHitDistribution") or {}).items())
        ]
        tickets_per_round_distribution = [
            {"tickets": tickets, "rounds": count, "share": count / rounds if rounds else 0}
            for tickets, count in sorted((summary.get("ticketsPerRoundDistribution") or {}).items())
        ]
        result = {
            **ticket_summary,
            "key": rule["key"],
            "label": rule["label"],
            "referenceKey": rule.get("referenceKey") or rule["key"],
            "category": rule.get("category", ""),
            "description": rule.get("description", ""),
            "mode": "buy",
            "rounds": rounds,
            "playedRounds": played_rounds,
            "skippedRounds": parse_int(summary.get("skippedRounds"), 0),
            "playedRoundRate": played_rounds / rounds if rounds else 0,
            "averageTicketsPerRound": parse_int(ticket_summary.get("tickets"), 0) / rounds if rounds else 0,
            "averageTicketsPerPlayedRound": parse_int(ticket_summary.get("tickets"), 0) / played_rounds
            if played_rounds
            else 0,
            "roundTwoPlus": len(summary["_twoPlusRoundIds"]),
            "roundThreePlus": len(summary["_threePlusRoundIds"]),
            "roundFourHit": len(summary["_fourHitRoundIds"]),
            "roundTwoPlusRate": len(summary["_twoPlusRoundIds"]) / rounds if rounds else 0,
            "roundThreePlusRate": len(summary["_threePlusRoundIds"]) / rounds if rounds else 0,
            "roundFourHitRate": len(summary["_fourHitRoundIds"]) / rounds if rounds else 0,
            "maxHitDistribution": max_hit_distribution,
            "ticketsPerRoundDistribution": tickets_per_round_distribution,
            "_playedRoundIds": set(summary["_playedRoundIds"]),
            "_twoPlusRoundIds": set(summary["_twoPlusRoundIds"]),
            "_threePlusRoundIds": set(summary["_threePlusRoundIds"]),
            "_fourHitRoundIds": set(summary["_fourHitRoundIds"]),
        }
        results.append(result)
        by_key[str(rule["key"])] = result

    for result in results:
        reference = by_key.get(str(result.get("referenceKey") or result.get("key")))
        if reference and reference is not result:
            reference_tickets = parse_int(reference.get("tickets"), 0)
            reference_stake = parse_float(reference.get("stake"), 0)
            reference_four_ids = reference.get("_fourHitRoundIds") or set()
            four_ids = result.get("_fourHitRoundIds") or set()
            reference_three_ids = reference.get("_threePlusRoundIds") or set()
            three_ids = result.get("_threePlusRoundIds") or set()
            missed_four = len(reference_four_ids - four_ids)
            covered_four = len(reference_four_ids & four_ids)
            missed_three = len(reference_three_ids - three_ids)
            result["reference"] = {
                "key": reference.get("key"),
                "label": reference.get("label"),
                "ticketChangeRate": parse_int(result.get("tickets"), 0) / reference_tickets - 1
                if reference_tickets
                else 0,
                "stakeChangeRate": parse_float(result.get("stake"), 0) / reference_stake - 1 if reference_stake else 0,
                "roiDelta": parse_float(result.get("roi"), 0) - parse_float(reference.get("roi"), 0),
                "roundFourHitRateDelta": parse_float(result.get("roundFourHitRate"), 0)
                - parse_float(reference.get("roundFourHitRate"), 0),
                "roundThreePlusRateDelta": parse_float(result.get("roundThreePlusRate"), 0)
                - parse_float(reference.get("roundThreePlusRate"), 0),
                "missedFourHitRounds": missed_four,
                "coveredFourHitRounds": covered_four,
                "missRateWhenReferenceFourHit": missed_four / len(reference_four_ids) if reference_four_ids else 0,
                "missedThreePlusRounds": missed_three,
                "missRateWhenReferenceThreePlus": missed_three / len(reference_three_ids) if reference_three_ids else 0,
                "addedFourHitRounds": len(four_ids - reference_four_ids),
            }
        else:
            result["reference"] = {
                "key": result.get("key"),
                "label": result.get("label"),
                "ticketChangeRate": 0,
                "stakeChangeRate": 0,
                "roiDelta": 0,
                "roundFourHitRateDelta": 0,
                "roundThreePlusRateDelta": 0,
                "missedFourHitRounds": 0,
                "coveredFourHitRounds": len(result.get("_fourHitRoundIds") or set()),
                "missRateWhenReferenceFourHit": 0,
                "missedThreePlusRounds": 0,
                "missRateWhenReferenceThreePlus": 0,
                "addedFourHitRounds": 0,
            }

    for result in results:
        for key in list(result.keys()):
            if key.startswith("_"):
                result.pop(key, None)
    return results


def strategy_audit_empty_mixed_kill_summary(rule: dict[str, Any]) -> dict[str, Any]:
    summary = strategy_audit_empty_kill_summary(str(rule["key"]), str(rule["label"]))
    summary.update(
        {
            "key": rule["key"],
            "category": rule.get("category", ""),
            "description": rule.get("description", ""),
            "mode": "kill",
            "triggeredRounds": 0,
        }
    )
    return summary


def strategy_audit_add_mixed_kill_round(
    summary: dict[str, Any],
    kill_numbers: list[int],
    target_row: dict[str, Any],
) -> None:
    numbers = sorted({parse_int(number, 0) for number in kill_numbers if parse_int(number, 0) > 0})
    if numbers:
        summary["triggeredRounds"] += 1
    strategy_audit_add_kill_result(summary, numbers, target_row)


def strategy_audit_mixed_kill_round_pools(
    c_numbers: list[int],
    d_numbers: list[int],
    e_numbers: list[int],
) -> dict[str, list[int]]:
    c_set = {parse_int(number, 0) for number in c_numbers if parse_int(number, 0) > 0}
    d_set = {parse_int(number, 0) for number in d_numbers if parse_int(number, 0) > 0}
    e_set = {parse_int(number, 0) for number in e_numbers if parse_int(number, 0) > 0}
    return {
        "kill_c": sorted(c_set),
        "kill_d": sorted(d_set),
        "kill_e": sorted(e_set),
        "kill_cd_union": sorted(c_set | d_set),
        "kill_de_union": sorted(d_set | e_set),
        "kill_cde_union": sorted(c_set | d_set | e_set),
        "kill_cd_intersection": sorted(c_set & d_set),
        "kill_de_intersection": sorted(d_set & e_set),
        "kill_cde_intersection": sorted(c_set & d_set & e_set),
    }


def strategy_audit_finalize_mixed_kill_summaries(
    summaries: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for rule in STRATEGY_SIGNAL_AUDIT_MIXED_KILL_RULES:
        summary = summaries[str(rule["key"])]
        finalized = strategy_audit_finalize_kill_summary(summary, config)
        rounds = parse_int(finalized.get("rounds"), 0)
        triggered = parse_int(summary.get("triggeredRounds"), 0)
        pool_total = parse_int(finalized.get("poolTotal"), 0)
        baseline = parse_float(finalized.get("baselineWrongRate"), 0)
        wrong_total = parse_int(finalized.get("wrongTotal"), 0)
        result = {
            **finalized,
            "key": rule["key"],
            "label": rule["label"],
            "category": rule.get("category", ""),
            "description": rule.get("description", ""),
            "mode": "kill",
            "triggeredRounds": triggered,
            "triggeredRoundRate": triggered / rounds if rounds else 0,
            "averagePoolSizeWhenTriggered": pool_total / triggered if triggered else 0,
            "expectedWrongTotal": pool_total * baseline,
            "wrongTotalLift": wrong_total - pool_total * baseline,
        }
        results.append(result)
    return results


def strategy_audit_tracking_summary(game_key: str) -> dict[str, Any]:
    if not DEFAULT_PREDICTION_TRACKING_DB.exists():
        return {"available": False, "panels": []}
    try:
        uri = f"file:{DEFAULT_PREDICTION_TRACKING_DB.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=3) as conn:
            conn.row_factory = sqlite3.Row
            placeholders = ",".join("?" for _ in PREDICTION_ACTIVE_TRACKING_PANELS)
            rows = conn.execute(
                f"""
                SELECT panel, status, record_json
                FROM prediction_records
                WHERE game_key = ?
                  AND panel IN ({placeholders})
                """,
                [game_key, *PREDICTION_ACTIVE_TRACKING_PANELS],
            ).fetchall()
    except sqlite3.Error as exc:
        return {"available": False, "error": str(exc), "panels": []}

    summaries: dict[tuple[str, int], dict[str, Any]] = {}
    status_counts: dict[tuple[str, int], dict[str, int]] = {}
    for row in rows:
        panel = prediction_panel_from_value(row["panel"])
        if panel not in PREDICTION_ACTIVE_TRACKING_PANELS:
            continue
        status = str(row["status"] or "")
        try:
            record = json.loads(row["record_json"])
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        numbers = record.get("numbers") or []
        pick_count = len(numbers)
        if pick_count <= 0:
            continue
        key = (panel, pick_count)
        status_counts.setdefault(key, {})
        status_counts[key][status] = status_counts[key].get(status, 0) + 1
        summary = summaries.setdefault(
            key,
            strategy_audit_empty_panel_ticket_summary(
                key=f"tracking:{panel}:{pick_count}",
                panel=panel,
                mode="tracking",
                pick_count=pick_count,
                label=f"{prediction_panel_label(panel)} {pick_count}码真实追踪",
                odds=parse_float(
                    record.get("odds"),
                    DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(pick_count, 0),
                ),
            ),
        )
        if status not in {"won", "lost"}:
            continue
        result = record.get("result") if isinstance(record.get("result"), dict) else {}
        matched_numbers = result.get("matchedNumbers") if isinstance(result, dict) else []
        hit_count = len(matched_numbers or [])
        strategy_audit_add_ticket_result(
            summary,
            {
                "pickCount": pick_count,
                "hitCount": hit_count,
                "previousOverlap": len(record.get("previousNumbers") or []),
            },
            stake=parse_float(record.get("stake"), 1),
            odds=parse_float(record.get("odds"), DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(pick_count, 150)),
        )

    panel_rows = []
    for key in sorted(summaries, key=lambda item: (PREDICTION_ACTIVE_TRACKING_PANELS.index(item[0]), item[1])):
        panel, pick_count = key
        panel_rows.append(
            {
                **strategy_audit_finalize_ticket_summary(
                    summaries[key],
                    LOTTERY_GAMES[game_key],
                    pick_count=pick_count,
                    odds=parse_float(
                        summaries[key].get("odds"),
                        DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(pick_count, 0),
                    ),
                ),
                "panel": panel,
                "pickCount": pick_count,
                "statusCounts": status_counts.get(key, {}),
            }
        )
    return {
        "available": True,
        "panels": panel_rows,
    }


def strategy_signal_audit_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_predictions_supported(config)
    game_key = str(config["key"])
    if game_key not in STRATEGY_SIGNAL_AUDIT_GAME_KEYS:
        raise ValueError("该彩种当前不支持策略审计")
        raise ValueError("策略信号审计当前只支持西班牙和波兰")
    history_path = game_history_path(config)
    window = max(30, min(parse_int(query.get("window", ["180"])[0], 180), STRATEGY_SIGNAL_AUDIT_MAX_WINDOW))
    train_window = max(
        STRATEGY_SIGNAL_AUDIT_MIN_TRAIN_WINDOW,
        min(parse_int(query.get("trainWindow", ["360"])[0], 360), STRATEGY_SIGNAL_AUDIT_MAX_TRAIN_WINDOW),
    )
    with DATA_LOCK:
        try:
            stat = history_path.stat()
            cache_key = (game_key, stat.st_mtime_ns, stat.st_size, window, train_window)
        except FileNotFoundError:
            cache_key = (game_key, 0, 0, window, train_window)

    with STRATEGY_AUDIT_CACHE_LOCK:
        cached = lru_cache_get(STRATEGY_AUDIT_CACHE, cache_key)
    if cached is not None:
        payload = dict(cached)
        payload["cacheHit"] = True
        payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
        return payload

    started = time.monotonic()
    with DATA_LOCK:
        all_rows = load_history_rows(history_path, config)
    data_integrity = history_data_integrity(all_rows, config)
    rows = valid_draw_rows(all_rows, config)
    if len(rows) < train_window + 30:
        raise ValueError("有效历史不足，暂不能做策略信号审计")

    rows_oldest = list(reversed(rows))
    max_rounds = max(0, min(window, len(rows_oldest) - train_window))
    start_index = max(train_window, len(rows_oldest) - max_rounds)
    actual_window = len(rows_oldest) - start_index
    odds = float(DEFAULT_MAIN_ODDS_BY_GAME.get(game_key, {}).get(4, 150))
    window_order = [item for item in STRATEGY_SIGNAL_AUDIT_WINDOWS if item <= actual_window]
    if actual_window and actual_window not in window_order:
        window_order.append(actual_window)
    window_order = sorted(set(window_order))

    window_data: dict[int, dict[str, Any]] = {}
    for window_size in window_order:
        window_data[window_size] = {
            "rounds": 0,
            "kill": {},
            "tickets": {panel: {} for panel in STRATEGY_SIGNAL_AUDIT_TICKET_PANELS},
            "repeat": strategy_audit_empty_repeat_summary(config),
        }

    detail_items: list[dict[str, Any]] = []
    skipped = 0
    for index in range(start_index, len(rows_oldest)):
        target = rows_oldest[index]
        previous = rows_oldest[index - 1] if index > 0 else None
        history_slice_oldest = rows_oldest[max(0, index - train_window) : index]
        history_rows = list(reversed(history_slice_oldest))
        if len(history_rows) < STRATEGY_SIGNAL_AUDIT_MIN_TRAIN_WINDOW:
            skipped += 1
            continue
        tickets = prediction_context_tickets(history_rows, config)
        round_offset_from_end = len(rows_oldest) - index

        for window_size, target_data in window_data.items():
            if round_offset_from_end > window_size:
                continue
            target_data["rounds"] += 1
            strategy_audit_add_ticket_panel_results(
                target_data["tickets"],
                panel=PREDICTION_PANEL_DEFAULT,
                tickets=tickets.get("aTickets") or [],
                target_row=target,
                previous_row=previous,
                config=config,
            )
            strategy_audit_add_ticket_panel_results(
                target_data["tickets"],
                panel=PREDICTION_PANEL_B,
                tickets=tickets.get("bTickets") or [],
                target_row=target,
                previous_row=previous,
                config=config,
            )
            strategy_audit_add_ticket_panel_results(
                target_data["tickets"],
                panel=PREDICTION_PANEL_M,
                tickets=tickets.get("mTickets") or [],
                target_row=target,
                previous_row=previous,
                config=config,
            )
            strategy_audit_add_repeat_result(target_data["repeat"], target, previous, config)

        if len(detail_items) < 40:
            a_two_hits = [
                strategy_audit_eval_ticket(ticket, target, previous)
                for ticket in tickets.get("aTickets") or []
                if str(ticket.get("mode") or "main") == "main"
                and parse_int(ticket.get("pickCount"), len(ticket.get("numbers") or [])) == 2
            ]
            b_two_hits = [
                strategy_audit_eval_ticket(ticket, target, previous)
                for ticket in tickets.get("bTickets") or []
                if str(ticket.get("mode") or "main") == "main"
                and parse_int(ticket.get("pickCount"), len(ticket.get("numbers") or [])) == 2
            ]
            m_two_hits = [
                strategy_audit_eval_ticket(ticket, target, previous)
                for ticket in tickets.get("mTickets") or []
                if str(ticket.get("mode") or "main") == "main"
                and parse_int(ticket.get("pickCount"), len(ticket.get("numbers") or [])) == 2
            ]
            m_three_hits = [
                strategy_audit_eval_ticket(ticket, target, previous)
                for ticket in tickets.get("mTickets") or []
                if str(ticket.get("mode") or "main") == "main"
                and parse_int(ticket.get("pickCount"), len(ticket.get("numbers") or [])) == 3
            ]
            detail_items.append(
                {
                    "drawIndex": index + 1,
                    "drawEventId": target.get("drawEventId", ""),
                    "drawTimeMs": parse_int(target.get("drawTimeMs"), 0),
                    "drawTimeUtc": target.get("drawTimeUtc", ""),
                    "drawNumbers": target.get("numbers") or [],
                    "previousOverlap": len(set(previous.get("numbers") or []) & set(target.get("numbers") or [])) if previous else 0,
                    "aTwoWon": sum(1 for item in a_two_hits if parse_int(item.get("hitCount"), 0) >= 2),
                    "bTwoWon": sum(1 for item in b_two_hits if parse_int(item.get("hitCount"), 0) >= 2),
                    "mTwoWon": sum(1 for item in m_two_hits if parse_int(item.get("hitCount"), 0) >= 2),
                    "mThreeWon": sum(1 for item in m_three_hits if parse_int(item.get("hitCount"), 0) >= 3),
                }
            )

    windows = []
    for window_size in window_order:
        target_data = window_data[window_size]
        windows.append(
            {
                "window": window_size,
                "rounds": target_data["rounds"],
                "killPanels": [],
                "ticketPanels": [
                    strategy_audit_finalize_panel_ticket_summary(summary, config, rounds=target_data["rounds"])
                    for panel in STRATEGY_SIGNAL_AUDIT_TICKET_PANELS
                    for summary in sorted(
                        (target_data["tickets"].get(panel) or {}).values(),
                        key=lambda item: (
                            prediction_panel_from_value(item.get("panel")),
                            str(item.get("mode") or ""),
                            parse_int(item.get("pickCount"), 0),
                        ),
                    )
                ],
                "eTopTickets": [],
                "repeat": strategy_audit_finalize_repeat_summary(target_data["repeat"]),
                "mixedBuyExperiments": [],
                "mixedKillExperiments": [],
            }
        )

    payload = {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "cacheHit": False,
        "game": game_public_config(config),
        "historyFile": file_info(history_path),
        "dataIntegrity": data_integrity,
        "drawCount": len(rows),
        "newestDraw": rows[0] if rows else None,
        "oldestDraw": rows[-1] if rows else None,
        "window": window,
        "actualRounds": actual_window,
        "skippedRounds": skipped,
        "trainWindow": train_window,
        "odds": odds,
        "windows": windows,
        "tracking": strategy_audit_tracking_summary(game_key),
        "items": detail_items,
        "notes": [
            "只读审计：不创建追踪记录，不修改预测规则。",
            "A/B 官方票命中率按前向回放统计：每期只使用目标期开奖之前的历史生成票。",
            "B 2码官方票理论基线使用当前彩种配置计算；Spain/Poland 20/70 为约 7.87%，不是 8.33%。",
            "旧C/D/E/F/G 已从 active 预测和自动追踪中退休；本页仅保留旧方向的只读复盘证据。",
            "重复号只作为观察特征统计，当前不参与加权选号。",
            "每期只使用目标开奖之前的历史生成 C，避免读取未来开奖。",
        ],
        "elapsedMs": round((time.monotonic() - started) * 1000),
    }
    payload["notes"] = [
        "只读审计：不创建追踪记录，不修改预测规则。",
        "当前审计范围只包含 A计划、B计划、C计划(实现键M) 的前向票与真实追踪。",
        "旧C/D/E/F/G 与 C回测已退出当前决策链，本页不再把旧计划作为评分或结论来源。",
        "A/B/C计划 前向回放每期只使用目标期开奖之前的历史生成票，避免读取未来开奖。",
        "重复号只作为观察特征统计，当前不参与加权选号。",
    ]
    payload["eTag"] = response_etag((cache_key, sorted((key, tuple(value)) for key, value in query.items())))
    with STRATEGY_AUDIT_CACHE_LOCK:
        lru_cache_set(STRATEGY_AUDIT_CACHE, cache_key, payload, STRATEGY_AUDIT_CACHE_MAX_ITEMS)
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

    run_stats = history_run_stats(rows, config)

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
        "runStats": run_stats,
        "items": items,
    }


def history_run_stats(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    total_numbers = int(config.get("totalNumbers") or 0)
    lengths = (2, 3, 4, 5, 6, 7)
    items = {
        length: {
            "length": length,
            "label": f"{length}连",
            "draws": 0,
            "occurrences": 0,
            "drawShare": 0.0,
            "avgOccurrencesPerDraw": 0.0,
            "maxOccurrencesInDraw": 0,
            "latestDrawEventId": "",
            "latestDrawTimeUtc": "",
            "latestDrawTimeMs": 0,
        }
        for length in lengths
    }
    valid_rows = [row for row in rows if is_valid_draw_row(row, config)]
    for row in valid_rows:
        numbers = sorted({
            parse_int(number, 0)
            for number in row.get("numbers") or []
            if 1 <= parse_int(number, 0) <= total_numbers
        })
        if not numbers:
            continue
        segment_lengths: list[int] = []
        current_length = 1
        for previous, current in zip(numbers, numbers[1:]):
            if current == previous + 1:
                current_length += 1
            else:
                segment_lengths.append(current_length)
                current_length = 1
        segment_lengths.append(current_length)
        draw_ms = parse_int(row.get("drawTimeMs"), 0)
        for length in lengths:
            count = sum(max(0, segment_length - length + 1) for segment_length in segment_lengths)
            if count <= 0:
                continue
            item = items[length]
            item["draws"] += 1
            item["occurrences"] += count
            item["maxOccurrencesInDraw"] = max(parse_int(item.get("maxOccurrencesInDraw"), 0), count)
            if draw_ms > parse_int(item.get("latestDrawTimeMs"), 0):
                item["latestDrawTimeMs"] = draw_ms
                item["latestDrawTimeUtc"] = str(row.get("drawTimeUtc") or "")
                item["latestDrawEventId"] = str(row.get("drawEventId") or "")
    draw_count = len(valid_rows)
    result_items = []
    for length in lengths:
        item = items[length]
        item["drawShare"] = parse_int(item.get("draws"), 0) / draw_count if draw_count else 0
        item["avgOccurrencesPerDraw"] = parse_int(item.get("occurrences"), 0) / draw_count if draw_count else 0
        item.pop("latestDrawTimeMs", None)
        result_items.append(item)
    return {
        "drawCount": draw_count,
        "lengths": list(lengths),
        "items": result_items,
    }


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


def draw_result_snapshot(draw: dict[str, Any]) -> dict[str, Any]:
    return {
        "drawEventId": draw.get("drawEventId", ""),
        "drawTimeMs": draw.get("drawTimeMs", 0),
        "drawTimeUtc": draw.get("drawTimeUtc", ""),
        "numbers": draw.get("numbers", []),
        "bonusBall": draw.get("bonusBall", ""),
    }


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
                    panel TEXT NOT NULL DEFAULT 'a',
                    method_version TEXT NOT NULL DEFAULT '',
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
            columns = {
                str(row["name"])
                for row in conn.execute("PRAGMA table_info(prediction_records)").fetchall()
            }
            schema_changed = False
            if "panel" not in columns:
                conn.execute("ALTER TABLE prediction_records ADD COLUMN panel TEXT NOT NULL DEFAULT 'a'")
                schema_changed = True
            if "method_version" not in columns:
                conn.execute("ALTER TABLE prediction_records ADD COLUMN method_version TEXT NOT NULL DEFAULT ''")
                schema_changed = True
            if schema_changed:
                backfill_prediction_tracking_db_columns(conn)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prediction_records_game_panel_status_target "
                "ON prediction_records(game_key, panel, status, target_draw_time_ms DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prediction_records_panel_status "
                "ON prediction_records(panel, status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prediction_records_game_method_target_status "
                "ON prediction_records(game_key, method_version, target_draw_time_ms, status)"
            )
            count = conn.execute("SELECT COUNT(*) FROM prediction_records").fetchone()[0]
            if count == 0:
                migrated = load_prediction_tracking_json()
                if migrated:
                    insert_prediction_tracking_records(conn, migrated)
            cancel_retired_prediction_tracking_records(conn)
            conn.commit()
        PREDICTION_DB_INITIALIZED = True


def backfill_prediction_tracking_db_columns(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT id, panel, method_version, record_json
        FROM prediction_records
        """
    ).fetchall()
    updates: list[tuple[str, str, str]] = []
    for row in rows:
        try:
            record = json.loads(row["record_json"])
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        panel = prediction_record_panel(record)
        method_version = str(record.get("methodVersion") or "")
        if str(row["panel"] or "") != panel or str(row["method_version"] or "") != method_version:
            updates.append((panel, method_version, str(row["id"] or "")))
    if updates:
        conn.executemany(
            "UPDATE prediction_records SET panel = ?, method_version = ? WHERE id = ?",
            updates,
        )


def cancel_retired_prediction_tracking_records(conn: sqlite3.Connection) -> int:
    retired_panels = tuple(PREDICTION_RETIRED_PANELS)
    if not retired_panels:
        return 0
    placeholders = ",".join("?" for _ in retired_panels)
    rows = conn.execute(
        f"""
        SELECT id, record_json
        FROM prediction_records
        WHERE status = 'pending'
          AND panel IN ({placeholders})
        """,
        retired_panels,
    ).fetchall()
    if not rows:
        return 0
    settled_at = utc_now_iso()
    updates: list[tuple[str, float, float, str, str]] = []
    for row in rows:
        try:
            record = json.loads(row["record_json"])
        except json.JSONDecodeError:
            record = {}
        if not isinstance(record, dict):
            record = {}
        record["status"] = "cancelled"
        record["settledAt"] = settled_at
        record["payout"] = 0
        record["profit"] = 0
        record["result"] = {
            "won": False,
            "cancelled": True,
            "reason": "计划已停用，追踪取消",
            "matchedNumbers": [],
            "draw": None,
            "payout": 0,
            "profit": 0,
            "settledAt": settled_at,
        }
        updates.append(
            (
                "cancelled",
                0.0,
                0.0,
                json.dumps(record, ensure_ascii=False, separators=(",", ":")),
                str(row["id"] or ""),
            )
        )
    conn.executemany(
        """
        UPDATE prediction_records
        SET status = ?, record_json = ?
        WHERE id = ?
        """,
        [(status, record_json, record_id) for status, _payout, _profit, record_json, record_id in updates],
    )
    return len(updates)


def insert_prediction_tracking_records(
    conn: sqlite3.Connection,
    records: list[dict[str, Any]],
) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO prediction_records (
            id, game_key, panel, method_version, target_draw_time_ms,
            status, strategy_label, created_at, record_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                str(record.get("id") or ""),
                prediction_tracking_game_key(record),
                prediction_record_panel(record),
                str(record.get("methodVersion") or ""),
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
    panel: str | None = None,
    include_retired: bool = False,
) -> list[dict[str, Any]]:
    init_prediction_tracking_db()
    params: list[Any] = [game_key]
    where = "game_key = ?"
    panel_key = prediction_panel_from_value(panel) if panel is not None else None
    if panel is not None:
        where += " AND panel = ?"
        params.append(panel_key)
    elif not include_retired:
        placeholders = ",".join("?" for _ in PREDICTION_ACTIVE_TRACKING_PANELS)
        where += f" AND panel IN ({placeholders})"
        params.extend(PREDICTION_ACTIVE_TRACKING_PANELS)
    method_where, method_params = prediction_tracking_current_method_where(panel_key, include_retired=include_retired)
    where += method_where
    params.extend(method_params)
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


def load_prediction_tracking_for_ids(record_ids: list[str]) -> list[dict[str, Any]]:
    ids = [str(record_id or "").strip() for record_id in record_ids if str(record_id or "").strip()]
    if not ids:
        return []
    init_prediction_tracking_db()
    records: list[dict[str, Any]] = []
    with prediction_tracking_db_connect() as conn:
        for start in range(0, len(ids), 200):
            chunk = ids[start : start + 200]
            placeholders = ",".join("?" for _ in chunk)
            rows = conn.execute(
                f"SELECT record_json FROM prediction_records WHERE id IN ({placeholders})",
                chunk,
            ).fetchall()
            records.extend(prediction_tracking_records_from_rows(rows))
    return records


def load_pending_prediction_tracking_for_batch_keys(
    batch_keys: set[tuple[str, str, int]],
) -> list[dict[str, Any]]:
    wanted = {
        (str(game_key), str(method_version), int(target_ms))
        for game_key, method_version, target_ms in batch_keys
        if game_key and method_version and int(target_ms) > 0
    }
    if not wanted:
        return []
    target_methods: dict[tuple[str, int], set[str]] = {}
    for game_key, method_version, target_ms in wanted:
        target_methods.setdefault((game_key, target_ms), set()).add(method_version)
    records: list[dict[str, Any]] = []
    init_prediction_tracking_db()
    with prediction_tracking_db_connect() as conn:
        for (game_key, target_ms), methods in sorted(target_methods.items()):
            placeholders = ",".join("?" for _ in methods)
            rows = conn.execute(
                f"""
                SELECT record_json
                FROM prediction_records
                WHERE game_key = ?
                  AND target_draw_time_ms = ?
                  AND status = 'pending'
                  AND method_version IN ({placeholders})
                """,
                [game_key, target_ms, *sorted(methods)],
            ).fetchall()
            for record in prediction_tracking_records_from_rows(rows):
                if prediction_tracking_batch_key(record) in wanted:
                    records.append(record)
    return records


def prediction_tracking_count(
    game_key: str | None = None,
    status_filter: str = "all",
    panel: str | None = None,
    include_retired: bool = False,
) -> int:
    init_prediction_tracking_db()
    params: list[Any] = []
    where_parts: list[str] = []
    if game_key is not None:
        where_parts.append("game_key = ?")
        params.append(game_key)
    panel_key = prediction_panel_from_value(panel) if panel is not None else None
    if panel is not None:
        where_parts.append("panel = ?")
        params.append(panel_key)
    elif not include_retired:
        placeholders = ",".join("?" for _ in PREDICTION_ACTIVE_TRACKING_PANELS)
        where_parts.append(f"panel IN ({placeholders})")
        params.extend(PREDICTION_ACTIVE_TRACKING_PANELS)
    method_where, method_params = prediction_tracking_current_method_where(panel_key, include_retired=include_retired)
    if method_where:
        where_parts.append(method_where[5:])
        params.extend(method_params)
    if status_filter != "all":
        where_parts.append("status = ?")
        params.append(status_filter)
    where = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
    with prediction_tracking_db_connect() as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM prediction_records{where}", params).fetchone()[0])


def prediction_tracking_db_where(
    game_key: str | None = None,
    *,
    panel: str | None = None,
    status_filter: str = "all",
    include_retired: bool = False,
) -> tuple[str, list[Any]]:
    where_parts: list[str] = []
    params: list[Any] = []
    if game_key is not None:
        where_parts.append("game_key = ?")
        params.append(game_key)
    panel_key = prediction_panel_from_value(panel) if panel is not None else None
    if panel is not None:
        where_parts.append("panel = ?")
        params.append(panel_key)
    elif not include_retired:
        placeholders = ",".join("?" for _ in PREDICTION_ACTIVE_TRACKING_PANELS)
        where_parts.append(f"panel IN ({placeholders})")
        params.extend(PREDICTION_ACTIVE_TRACKING_PANELS)
    method_where, method_params = prediction_tracking_current_method_where(panel_key, include_retired=include_retired)
    if method_where:
        where_parts.append(method_where[5:])
        params.extend(method_params)
    if status_filter != "all":
        where_parts.append("status = ?")
        params.append(status_filter)
    where = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
    return where, params


def prediction_tracking_summary_from_db(
    game_key: str | None = None,
    *,
    panel: str | None = None,
) -> dict[str, Any]:
    init_prediction_tracking_db()
    where, params = prediction_tracking_db_where(game_key, panel=panel)
    with prediction_tracking_db_connect() as conn:
        row = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0) AS pending,
                COALESCE(SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END), 0) AS won,
                COALESCE(SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END), 0) AS lost,
                COALESCE(SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END), 0) AS cancelled,
                COALESCE(SUM(CASE WHEN status = 'void' THEN 1 ELSE 0 END), 0) AS void,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.theoreticalHitRate'), '') AS REAL), 0)
                    ELSE 0 END
                ), 0) AS expected_hits,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.breakEvenHitRate'), '') AS REAL), 0)
                    ELSE 0 END
                ), 0) AS break_even_sum,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.stake'), '') AS REAL), 1)
                    ELSE 0 END
                ), 0) AS stake_total,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.payout'), '') AS REAL), 0)
                    ELSE 0 END
                ), 0) AS payout_total,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.profit'), '') AS REAL), 0)
                    ELSE 0 END
                ), 0) AS profit_total
            FROM prediction_records{where}
            """,
            params,
        ).fetchone()
    return prediction_tracking_summary_from_values(
        row["total"],
        row["pending"],
        row["won"],
        row["lost"],
        row["cancelled"],
        row["void"],
        row["expected_hits"],
        row["break_even_sum"],
        row["stake_total"],
        row["payout_total"],
        row["profit_total"],
    )


def prediction_tracking_group_summaries_from_db(
    game_key: str | None = None,
    *,
    panel: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    init_prediction_tracking_db()
    where, params = prediction_tracking_db_where(game_key, panel=panel)
    with prediction_tracking_db_connect() as conn:
        rows = conn.execute(
            f"""
            WITH scoped AS (
                SELECT
                    game_key,
                    method_version,
                    strategy_label,
                    COALESCE(json_extract(record_json, '$.gameShortName'), '') AS game_short_name,
                    COALESCE(json_extract(record_json, '$.structureType'), '') AS structure_type,
                    COALESCE(json_extract(record_json, '$.structureLabel'), '') AS structure_label,
                    COALESCE(json_extract(record_json, '$.mode'), '') AS mode,
                    COALESCE(CAST(NULLIF(json_extract(record_json, '$.pickCount'), '') AS INTEGER), 0) AS pick_count,
                    COALESCE(CAST(NULLIF(json_extract(record_json, '$.odds'), '') AS REAL), 0) AS odds,
                    status,
                    record_json
                FROM prediction_records{where}
            )
            SELECT
                game_key,
                method_version,
                strategy_label,
                MAX(game_short_name) AS game_short_name,
                structure_type,
                MAX(structure_label) AS structure_label,
                mode,
                pick_count,
                MAX(odds) AS odds,
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0) AS pending,
                COALESCE(SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END), 0) AS won,
                COALESCE(SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END), 0) AS lost,
                COALESCE(SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END), 0) AS cancelled,
                COALESCE(SUM(CASE WHEN status = 'void' THEN 1 ELSE 0 END), 0) AS void,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.theoreticalHitRate'), '') AS REAL), 0)
                    ELSE 0 END
                ), 0) AS expected_hits,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.breakEvenHitRate'), '') AS REAL), 0)
                    ELSE 0 END
                ), 0) AS break_even_sum,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.stake'), '') AS REAL), 1)
                    ELSE 0 END
                ), 0) AS stake_total,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.payout'), '') AS REAL), 0)
                    ELSE 0 END
                ), 0) AS payout_total,
                COALESCE(SUM(
                    CASE WHEN status IN ('won', 'lost')
                    THEN COALESCE(CAST(NULLIF(json_extract(record_json, '$.profit'), '') AS REAL), 0)
                    ELSE 0 END
                ), 0) AS profit_total
            FROM scoped
            GROUP BY game_key, method_version, strategy_label, structure_type, mode, pick_count
            ORDER BY (won + lost) DESC, total DESC, game_short_name, strategy_label
            LIMIT ?
            """,
            [*params, max(1, limit)],
        ).fetchall()
    summaries: list[dict[str, Any]] = []
    for row in rows:
        summary = prediction_tracking_summary_from_values(
            row["total"],
            row["pending"],
            row["won"],
            row["lost"],
            row["cancelled"],
            row["void"],
            row["expected_hits"],
            row["break_even_sum"],
            row["stake_total"],
            row["payout_total"],
            row["profit_total"],
        )
        summary.update(
            {
                "gameKey": str(row["game_key"] or ""),
                "gameShortName": str(row["game_short_name"] or ""),
                "strategyLabel": str(row["strategy_label"] or ""),
                "structureType": str(row["structure_type"] or ""),
                "structureLabel": str(row["structure_label"] or ""),
                "mode": str(row["mode"] or ""),
                "pickCount": parse_int(row["pick_count"], 0),
                "odds": parse_float(row["odds"], 0),
            }
        )
        summaries.append(summary)
    return summaries


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
        "panel": prediction_panel_from_value(fields.get("panel")),
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


def prediction_tracking_freshness_tolerance_ms(config: dict[str, Any]) -> int:
    interval_ms = prediction_draw_interval_ms(config)
    if interval_ms <= 0:
        return 1000
    return max(1000, min(interval_ms // 20, 5000))


def prediction_tracking_record_source_ready(record: dict[str, Any], config: dict[str, Any]) -> bool:
    target_ms = parse_int(record.get("targetDrawTimeMs"), 0)
    based_ms = parse_int(record.get("basedOnDrawTimeMs"), 0)
    expected_target_ms, expected_offset = next_operating_draw_after_ms(based_ms, config)
    if target_ms <= 0 or based_ms <= 0 or expected_target_ms <= 0:
        return False
    offset = parse_int(record.get("targetDrawOffset"), 0)
    tolerance_ms = prediction_tracking_freshness_tolerance_ms(config)
    if offset and expected_offset and offset != expected_offset:
        return False
    return abs(target_ms - expected_target_ms) <= tolerance_ms


def prediction_tracking_target_context(
    payload: dict[str, Any],
    config: dict[str, Any],
    now_ms: int | None = None,
) -> dict[str, Any]:
    predictions = payload.get("predictions") if isinstance(payload.get("predictions"), dict) else {}
    forecasts = predictions.get("forecasts") if isinstance(predictions.get("forecasts"), list) else []
    target = forecasts[0] if forecasts and isinstance(forecasts[0], dict) else {}
    newest = (
        payload.get("newestTimelineDraw")
        if isinstance(payload.get("newestTimelineDraw"), dict)
        else payload.get("newestDraw")
        if isinstance(payload.get("newestDraw"), dict)
        else {}
    )
    target_ms = parse_int(target.get("drawTimeMs"), 0)
    based_ms = parse_int(newest.get("drawTimeMs"), 0)
    interval_ms = prediction_draw_interval_ms(config)
    tolerance_ms = prediction_tracking_freshness_tolerance_ms(config)
    draw_offset = parse_int(target.get("drawOffset"), 0)
    expected_target_ms, expected_offset = next_operating_draw_after_ms(based_ms, config)
    now_value = now_ms if now_ms is not None else int(time.time() * 1000)
    minimum_target_ms = now_value + PREDICTION_TRACKING_LEAD_SECONDS * 1000
    expected_target_overdue = (
        expected_target_ms > 0
        and expected_target_ms + prediction_draw_sync_grace_ms(config) <= now_value
    )
    ready = (
        target_ms > 0
        and based_ms > 0
        and interval_ms > 0
        and expected_target_ms > 0
        and not expected_target_overdue
        and (draw_offset == 0 or draw_offset == expected_offset)
        and abs(target_ms - expected_target_ms) <= tolerance_ms
        and target_ms >= minimum_target_ms
    )
    reason = ""
    if target_ms <= 0:
        reason = "missing_target_draw"
    elif based_ms <= 0:
        reason = "missing_base_draw"
    elif interval_ms <= 0:
        reason = "missing_draw_interval"
    elif expected_target_ms <= 0:
        reason = "missing_expected_target_draw"
    elif expected_target_overdue:
        reason = "history_not_synced_to_previous_draw"
    elif expected_target_ms < minimum_target_ms:
        reason = "next_draw_inside_betting_cutoff"
    elif draw_offset and expected_offset and draw_offset != expected_offset:
        reason = "history_not_synced_to_previous_draw"
    elif abs(target_ms - expected_target_ms) > tolerance_ms:
        reason = "target_is_not_next_open_draw_after_latest_history"
    elif target_ms < minimum_target_ms:
        reason = "target_inside_betting_cutoff"
    return {
        "ready": ready,
        "reason": reason,
        "targetDrawTimeMs": target_ms,
        "targetDrawTimeUtc": draw_time_utc_from_ms(target_ms),
        "basedOnDrawTimeMs": based_ms,
        "basedOnDrawTimeUtc": draw_time_utc_from_ms(based_ms),
        "expectedTargetDrawTimeMs": expected_target_ms,
        "expectedTargetDrawTimeUtc": draw_time_utc_from_ms(expected_target_ms),
        "drawOffset": draw_offset,
        "expectedDrawOffset": expected_offset,
        "intervalMs": interval_ms,
        "toleranceMs": tolerance_ms,
        "leadSeconds": PREDICTION_TRACKING_LEAD_SECONDS,
        "minimumTargetDrawTimeMs": minimum_target_ms,
        "minimumTargetDrawTimeUtc": draw_time_utc_from_ms(minimum_target_ms),
        "secondsUntilExpectedTarget": round((expected_target_ms - now_value) / 1000, 3)
        if expected_target_ms
        else None,
        "expectedTargetOverdue": expected_target_overdue,
        "target": target,
        "newest": newest,
    }


def prediction_tracking_target_context_from_latest(
    latest_timeline: dict[str, Any] | None,
    config: dict[str, Any],
    now_ms: int | None = None,
) -> dict[str, Any]:
    newest_ms = parse_int(latest_timeline.get("drawTimeMs") if latest_timeline else 0, 0)
    target_ms, target_offset = next_operating_draw_after_ms(newest_ms, config)
    target = (
        {
            "drawOffset": target_offset,
            "drawTimeMs": target_ms,
            "drawTimeUtc": draw_time_utc_from_ms(target_ms),
        }
        if target_ms > 0
        else {}
    )
    return prediction_tracking_target_context(
        {
            "newestDraw": latest_timeline or {},
            "newestTimelineDraw": latest_timeline or {},
            "predictions": {"forecasts": [target] if target else []},
        },
        config,
        now_ms=now_ms,
    )


def prediction_tracking_target_context_public(context: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in context.items()
        if key not in {"target", "newest"}
    }


def mark_prediction_payload_waiting_for_sync(payload: dict[str, Any], context: dict[str, Any]) -> None:
    predictions = payload.get("predictions") if isinstance(payload.get("predictions"), dict) else {}
    sync_status = prediction_tracking_target_context_public(context)
    reason = str(sync_status.get("reason") or "")
    if reason in {"next_draw_inside_betting_cutoff", "target_inside_betting_cutoff"}:
        message = "下一期已接近封盘，跳过本期，等待该期开奖结果同步后再生成下一期计划"
    else:
        message = "等待上一期开奖结果同步，暂不生成可下注候选"
    sync_status["message"] = message
    predictions["trackingReady"] = False
    predictions["syncStatus"] = sync_status
    predictions["strategyTickets"] = []
    predictions["forecasts"] = []
    predictions["timeWindowUtc"] = {"start": "", "end": ""}
    predictions["method"] = f"等待开奖同步：{message}"
    payload["predictionTarget"] = sync_status


def prediction_tracking_pending_batch_blocks(
    record: dict[str, Any],
    pending_records: list[dict[str, Any]],
) -> bool:
    key = prediction_tracking_batch_key(record)
    based_ms = parse_int(record.get("basedOnDrawTimeMs"), 0)
    for existing in pending_records:
        if prediction_tracking_batch_key(existing) != key:
            continue
        if parse_int(existing.get("basedOnDrawTimeMs"), 0) >= based_ms:
            return True
    return False


def prediction_tracking_records_from_payload(
    payload: dict[str, Any],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    predictions = payload.get("predictions") if isinstance(payload.get("predictions"), dict) else {}
    panel = prediction_panel_from_value(predictions.get("panel") or payload.get("panel"))
    method_version = prediction_method_version_for_panel(panel)
    tickets = predictions.get("strategyTickets") if isinstance(predictions.get("strategyTickets"), list) else []
    target_context = prediction_tracking_target_context(payload, config)
    if not target_context["ready"]:
        return []
    target = target_context["target"] if isinstance(target_context.get("target"), dict) else {}
    newest = target_context["newest"] if isinstance(target_context.get("newest"), dict) else {}
    target_ms = parse_int(target_context.get("targetDrawTimeMs"), 0)
    based_ms = parse_int(target_context.get("basedOnDrawTimeMs"), 0)
    if target_ms <= 0 or based_ms <= 0 or not tickets:
        return []

    generated_at = str(payload.get("generatedAt") or utc_now_iso())
    method = str(predictions.get("method") or "")
    records: list[dict[str, Any]] = []
    for ticket_index, ticket in enumerate(tickets, start=1):
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
            "methodVersion": method_version,
            "panel": panel,
            "panelLabel": prediction_panel_label(panel),
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
            "ticketRank": parse_int(ticket.get("ticketRank"), ticket_index),
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
            "excludedNumbers": [int(number) for number in ticket.get("excludedNumbers") or predictions.get("excludedNumbers") or []],
            "sourcePanel": str(ticket.get("sourcePanel") or predictions.get("sourcePanel") or ""),
            "sourcePanels": ticket.get("sourcePanels") or predictions.get("sourcePanels") or [],
            "sourceCoreTicketLabels": ticket.get("sourceCoreTicketLabels") or [],
            "structureType": str(ticket.get("structureType") or ""),
            "structureLabel": str(ticket.get("structureLabel") or ""),
            "derivedRule": str(ticket.get("derivedRule") or ""),
            "auditSourceLabel": str(ticket.get("auditSourceLabel") or ""),
            "auditScore": parse_float(ticket.get("auditScore"), 0),
            "followDecision": str(ticket.get("followDecision") or ""),
            "sourceStructureType": str(ticket.get("sourceStructureType") or ""),
            "sourceStructureLabel": str(ticket.get("sourceStructureLabel") or ""),
            "extensionStructureType": str(ticket.get("extensionStructureType") or ""),
            "extensionStructureLabel": str(ticket.get("extensionStructureLabel") or ""),
            "coreNumbers": [int(number) for number in ticket.get("coreNumbers") or []],
            "companionNumbers": [int(number) for number in ticket.get("companionNumbers") or []],
            "extensionNumbers": [int(number) for number in ticket.get("extensionNumbers") or []],
            "overlapNumbers": [int(number) for number in ticket.get("overlapNumbers") or []],
            "recallNumbers": [int(number) for number in ticket.get("recallNumbers") or []],
            "reversalNumbers": [int(number) for number in ticket.get("reversalNumbers") or []],
            "sourcePoolNumbers": [int(number) for number in ticket.get("sourcePoolNumbers") or []],
            "sourcePoolCount": parse_int(ticket.get("sourcePoolCount"), 0),
            "sourceCoreScore": parse_float(ticket.get("sourceCoreScore"), 0),
            "companionScore": parse_float(ticket.get("companionScore"), 0),
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
    pending_records = [record for record in records if str(record.get("status") or "pending") == "pending"]
    existing_pending_batches = {prediction_tracking_batch_key(record) for record in pending_records}
    created: list[dict[str, Any]] = []
    for record in prediction_tracking_records_from_payload(payload, config):
        if prediction_tracking_batch_key(record) in existing_pending_batches and prediction_tracking_pending_batch_blocks(
            record,
            pending_records,
        ):
            continue
        if record["id"] in existing_ids:
            continue
        records.append(record)
        existing_ids.add(record["id"])
        created.append(record)
    return created


def add_prediction_tracking_snapshot_lightweight(
    payload: dict[str, Any],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_records = prediction_tracking_records_from_payload(payload, config)
    if not candidate_records:
        return []
    existing_records = load_prediction_tracking_for_ids(
        [str(record.get("id") or "") for record in candidate_records]
    )
    existing_ids = {str(record.get("id") or "") for record in existing_records}
    pending_records = load_pending_prediction_tracking_for_batch_keys(
        {prediction_tracking_batch_key(record) for record in candidate_records}
    )
    existing_pending_batches = {prediction_tracking_batch_key(record) for record in pending_records}
    created: list[dict[str, Any]] = []
    for record in candidate_records:
        if prediction_tracking_batch_key(record) in existing_pending_batches and prediction_tracking_pending_batch_blocks(
            record,
            pending_records,
        ):
            continue
        if str(record.get("id") or "") in existing_ids:
            continue
        existing_ids.add(str(record.get("id") or ""))
        created.append(record)
    if created:
        write_prediction_tracking(created)
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
        if not prediction_tracking_record_source_ready(record, config):
            result = void_prediction_tracking_result(record, PREDICTION_VOID_REASON_STALE_SOURCE)
            record["status"] = "void"
            record["settledAt"] = result["settledAt"]
            record["payout"] = result["payout"]
            record["profit"] = result["profit"]
            record["result"] = result
            if changed_records is not None:
                changed_records.append(record)
            settled += 1
            continue
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
    break_even_sum = sum(parse_float(record.get("breakEvenHitRate"), 0) for record in settled_records)
    stake_total = sum(parse_float(record.get("stake"), 1) for record in settled_records)
    payout_total = sum(parse_float(record.get("payout"), 0) for record in settled_records)
    profit_total = sum(parse_float(record.get("profit"), 0) for record in settled_records)
    return prediction_tracking_summary_from_values(
        total,
        pending,
        won,
        lost,
        cancelled,
        void,
        expected_hits,
        break_even_sum,
        stake_total,
        payout_total,
        profit_total,
    )


def prediction_tracking_summary_from_values(
    total: Any,
    pending: Any,
    won: Any,
    lost: Any,
    cancelled: Any,
    void: Any,
    expected_hits: Any,
    break_even_sum: Any,
    stake_total: Any,
    payout_total: Any,
    profit_total: Any,
) -> dict[str, Any]:
    total = parse_int(total, 0)
    pending = parse_int(pending, 0)
    won = parse_int(won, 0)
    lost = parse_int(lost, 0)
    cancelled = parse_int(cancelled, 0)
    void = parse_int(void, 0)
    settled = won + lost
    expected_hits = parse_float(expected_hits, 0)
    break_even_sum = parse_float(break_even_sum, 0)
    stake_total = parse_float(stake_total, 0)
    payout_total = parse_float(payout_total, 0)
    profit_total = parse_float(profit_total, 0)
    theoretical_hit_rate = expected_hits / settled if settled else 0
    break_even_hit_rate = break_even_sum / settled if settled else 0
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
                str(record.get("structureType") or ""),
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
                "structureType": first.get("structureType", ""),
                "structureLabel": first.get("structureLabel", ""),
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
    if pick_count == 4 and len(numbers) == 4:
        candidates.append(("p4_original_ticket", "4球原结构四码", tuple(sorted(numbers))))
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


def adjacent_derived_stats(
    records: list[dict[str, Any]],
    config: dict[str, Any] | None,
    *,
    panel: str | None = None,
) -> dict[str, Any]:
    if config is None or str(config.get("key")) not in ADJACENT_DERIVED_STATS_GAME_KEYS:
        return {"enabled": False, "items": [], "note": "当前彩种暂未启用临码派生统计"}

    total_numbers = int(config["totalNumbers"])
    groups: dict[str, dict[str, Any]] = {}
    source_records = [
        record
        for record in records
        if prediction_tracking_game_key(record) == config["key"]
        and prediction_record_matches_panel(record, panel)
        and record.get("status") in {"won", "lost"}
        and str(record.get("mode") or "main") == "main"
        and parse_int(record.get("pickCount"), 0) in ADJACENT_DERIVED_SOURCE_PICK_COUNTS
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

        if pick_count == 4 and len(numbers) == 4:
            for variant_key, variant_label, combo in adjacent_ticket_candidates_for_numbers(numbers, pick_count, total_numbers):
                add_adjacent_derived_stat_sample(
                    groups,
                    key=variant_key,
                    label=variant_label,
                    category="ticket",
                    source_pick_count=4,
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
        "panel": prediction_panel_from_value(panel),
        "panelLabel": prediction_panel_label(prediction_panel_from_value(panel)),
        "sourceSettledRecords": len(source_records),
        "items": items,
        "schemeSummary": scheme_summary,
        "note": "临码派生统计由已结算预测记录按固定规则计算；投注类按单位注额估算 ROI。",
    }


def adjacent_derived_hit_rows(
    records: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    panel: str | None = None,
) -> list[dict[str, Any]]:
    if str(config.get("key")) not in ADJACENT_DERIVED_STATS_GAME_KEYS:
        return []
    total_numbers = int(config["totalNumbers"])
    rows: list[dict[str, Any]] = []
    source_records = [
        record
        for record in records
        if prediction_tracking_game_key(record) == config["key"]
        and prediction_record_matches_panel(record, panel)
        and record.get("status") in {"won", "lost"}
        and str(record.get("mode") or "main") == "main"
        and parse_int(record.get("pickCount"), 0) in ADJACENT_DERIVED_SOURCE_PICK_COUNTS
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
    panel = prediction_panel_from_query(query)
    ensure_prediction_tracking_panel_active(panel)
    page = max(1, parse_int(query.get("page", ["1"])[0], 1))
    page_size = max(10, min(parse_int(query.get("pageSize", ["50"])[0], 50), 200))
    search = str(query.get("q", [""])[0] or "").strip().lower()
    strategy = str(query.get("strategy", ["all"])[0] or "all").strip()
    group_by = str(query.get("groupBy", ["record"])[0] or "record").strip()
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
    rows = adjacent_derived_hit_rows(records, config, panel=panel)
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
        "panel": panel,
        "panelLabel": prediction_panel_label(panel),
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
    panel = prediction_panel_from_query(query)
    ensure_prediction_tracking_panel_active(panel)
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "game": game_public_config(config),
        "panel": panel,
        "panelLabel": prediction_panel_label(panel),
        "adjacentStats": adjacent_derived_stats(records, config, panel=panel),
    }


def prediction_tracking_slot_rank(record: dict[str, Any]) -> int:
    rank = parse_int(record.get("ticketRank"), 0)
    return rank if rank > 0 else 0


def prediction_tracking_ticket_number_key(record: dict[str, Any]) -> tuple[int, ...]:
    numbers = [
        parse_int(number, 0)
        for number in (record.get("numbers") or [])
        if parse_int(number, 0) > 0
    ]
    if numbers:
        return tuple(numbers)
    return tuple(
        parse_int(number, 0)
        for number in re.findall(r"\d+", str(record.get("ticketLabel") or ""))
    )


def prediction_tracking_unranked_sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    panel = prediction_panel_from_value(record.get("panel"))
    pick_count = parse_int(record.get("pickCount"), len(record.get("numbers") or []))
    if panel == PREDICTION_PANEL_M:
        return (
            pick_count,
            -parse_float(record.get("score"), 0),
            -parse_float(record.get("recentHitRate"), 0),
            parse_int(record.get("maxMiss"), 0),
            parse_int(record.get("currentMiss"), 0),
            prediction_tracking_ticket_number_key(record),
            str(record.get("ticketLabel") or ""),
            str(record.get("id") or ""),
        )
    return (
        pick_count,
        prediction_tracking_ticket_number_key(record),
        str(record.get("ticketLabel") or ""),
        str(record.get("id") or ""),
    )


def prediction_tracking_daily_window(
    record: dict[str, Any],
    config: dict[str, Any],
) -> tuple[int, int, str] | None:
    target_ms = parse_int(record.get("targetDrawTimeMs"), 0)
    if target_ms <= 0:
        return None
    tz = telegram_game_day_timezone(config)
    local_dt = datetime.fromtimestamp(target_ms / 1000, tz=UTC).astimezone(tz)
    start_local = datetime(local_dt.year, local_dt.month, local_dt.day, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return (
        int(start_local.astimezone(UTC).timestamp() * 1000),
        int(end_local.astimezone(UTC).timestamp() * 1000),
        local_dt.date().isoformat(),
    )


def load_prediction_tracking_day_records(
    config: dict[str, Any],
    panel: str | None,
    start_ms: int,
    end_ms: int,
) -> list[dict[str, Any]]:
    if start_ms <= 0 or end_ms <= start_ms:
        return []
    init_prediction_tracking_db()
    panel_key = prediction_panel_from_value(panel) if panel is not None else None
    params: list[Any] = [str(config["key"]), start_ms, end_ms]
    where = "game_key = ? AND target_draw_time_ms >= ? AND target_draw_time_ms < ?"
    if panel is not None:
        where += " AND panel = ?"
        params.append(panel_key)
    method_where, method_params = prediction_tracking_current_method_where(panel_key)
    where += method_where
    params.extend(method_params)
    with prediction_tracking_db_connect() as conn:
        rows = conn.execute(
            f"""
            SELECT record_json
            FROM prediction_records
            WHERE {where}
            ORDER BY target_draw_time_ms ASC, created_at ASC, id ASC
            """,
            params,
        ).fetchall()
    return prediction_tracking_records_from_rows(rows)


def prediction_tracking_daily_slot_rank_info(records: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, str]]:
    groups: dict[tuple[str, str, str, int], list[dict[str, Any]]] = {}
    for record in records:
        record_id = str(record.get("id") or "")
        if not record_id:
            continue
        key = (
            prediction_tracking_game_key(record),
            prediction_panel_from_value(record.get("panel")),
            str(record.get("methodVersion") or ""),
            parse_int(record.get("targetDrawTimeMs"), 0),
        )
        groups.setdefault(key, []).append(record)

    ranks: dict[str, int] = {}
    rank_sources: dict[str, str] = {}
    for records_for_target in groups.values():
        used_ranks: set[int] = set()
        unranked: list[dict[str, Any]] = []
        for record in records_for_target:
            record_id = str(record.get("id") or "")
            rank = parse_int(record.get("ticketRank"), 0)
            if rank > 0:
                ranks[record_id] = rank
                rank_sources[record_id] = "stored"
                used_ranks.add(rank)
            else:
                unranked.append(record)
        unranked.sort(key=prediction_tracking_unranked_sort_key)
        next_rank = 1
        for record in unranked:
            while next_rank in used_ranks:
                next_rank += 1
            record_id = str(record.get("id") or "")
            ranks[record_id] = next_rank
            rank_sources[record_id] = "fallback"
            used_ranks.add(next_rank)
            next_rank += 1
    return ranks, rank_sources


def prediction_tracking_daily_slot_ranks(records: list[dict[str, Any]]) -> dict[str, int]:
    ranks, _rank_sources = prediction_tracking_daily_slot_rank_info(records)
    return ranks


def prediction_tracking_daily_key(
    record: dict[str, Any],
    config: dict[str, Any] | None,
    slot_ranks: dict[str, int] | None = None,
) -> tuple[str, str, str, int] | None:
    if config is None:
        return None
    target_ms = parse_int(record.get("targetDrawTimeMs"), 0)
    if target_ms <= 0:
        return None
    tz = telegram_game_day_timezone(config)
    day_key = datetime.fromtimestamp(target_ms / 1000, tz=UTC).astimezone(tz).date().isoformat()
    panel = prediction_panel_from_value(record.get("panel"))
    record_id = str(record.get("id") or "")
    rank = (slot_ranks or {}).get(record_id) or prediction_tracking_slot_rank(record)
    if rank <= 0:
        return None
    return (
        prediction_tracking_game_key(record),
        panel,
        day_key,
        rank,
    )


def attach_prediction_tracking_daily_miss_streaks(
    page_items: list[dict[str, Any]],
    scoped_records: list[dict[str, Any]],
    config: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if config is None or not page_items:
        return page_items
    target_items = [
        record
        for record in page_items
        if prediction_panel_from_value(record.get("panel")) == PREDICTION_PANEL_M
    ]
    if not target_items:
        return page_items
    all_records_by_id: dict[str, dict[str, Any]] = {}
    for record in [*scoped_records, *page_items]:
        record_id = str(record.get("id") or "")
        if record_id:
            all_records_by_id[record_id] = record

    day_windows: dict[tuple[str, str, int, int], None] = {}
    for record in target_items:
        window = prediction_tracking_daily_window(record, config)
        if window is None:
            continue
        start_ms, end_ms, _day_key = window
        day_windows[(prediction_tracking_game_key(record), prediction_panel_from_value(record.get("panel")), start_ms, end_ms)] = None
    for game_key, panel, start_ms, end_ms in day_windows:
        if game_key != str(config["key"]):
            continue
        for record in load_prediction_tracking_day_records(config, panel, start_ms, end_ms):
            record_id = str(record.get("id") or "")
            if record_id:
                all_records_by_id.setdefault(record_id, record)

    context_records = list(all_records_by_id.values())
    slot_ranks, rank_sources = prediction_tracking_daily_slot_rank_info(context_records)
    requested_keys = {
        key
        for key in (prediction_tracking_daily_key(record, config, slot_ranks) for record in target_items)
        if key is not None
    }
    if not requested_keys:
        return page_items

    groups: dict[tuple[str, str, str, int], list[dict[str, Any]]] = {}
    for record in context_records:
        key = prediction_tracking_daily_key(record, config, slot_ranks)
        if key in requested_keys:
            groups.setdefault(key, []).append(record)

    streak_by_id: dict[str, int] = {}
    start_by_key: dict[tuple[str, str, str, int], int] = {}
    for key, records in groups.items():
        miss_streak = 0
        sorted_records = sorted(
            records,
            key=lambda record: (
                parse_int(record.get("targetDrawTimeMs"), 0),
                str(record.get("createdAt") or ""),
                str(record.get("id") or ""),
            ),
        )
        start_by_key[key] = min((parse_int(record.get("targetDrawTimeMs"), 0) for record in sorted_records), default=0)
        for record in sorted_records:
            status = str(record.get("status") or "pending")
            if status == "won":
                miss_streak = 0
            elif status == "lost":
                miss_streak += 1
            elif status == "pending":
                pass
            elif status in {"cancelled", "void"}:
                pass
            else:
                pass
            record_id = str(record.get("id") or "")
            if record_id:
                streak_by_id[record_id] = miss_streak

    result: list[dict[str, Any]] = []
    for record in page_items:
        item = dict(record)
        if prediction_panel_from_value(item.get("panel")) != PREDICTION_PANEL_M:
            result.append(item)
            continue
        key = prediction_tracking_daily_key(item, config, slot_ranks)
        record_id = str(item.get("id") or "")
        item["ticketRank"] = slot_ranks.get(record_id) or prediction_tracking_slot_rank(item)
        item["rankSource"] = rank_sources.get(record_id, "stored" if prediction_tracking_slot_rank(item) > 0 else "fallback")
        has_daily_tracking = record_id in streak_by_id
        if has_daily_tracking:
            daily_miss_streak = streak_by_id.get(record_id, 0)
            item["dailyMissStreak"] = daily_miss_streak
            item["dailyMissDisplayStreak"] = (
                daily_miss_streak + 1
                if str(item.get("status") or "pending") == "pending"
                else daily_miss_streak
            )
            item["dailyMissSource"] = "tracking_day_slot"
        item["dailyMissStartDrawTimeMs"] = start_by_key.get(key, 0) if key is not None else 0
        if item["dailyMissStartDrawTimeMs"]:
            item["dailyMissStartDrawTimeUtc"] = datetime.fromtimestamp(
                item["dailyMissStartDrawTimeMs"] / 1000,
                tz=UTC,
            ).isoformat(timespec="seconds")
        else:
            item["dailyMissStartDrawTimeUtc"] = ""
        result.append(item)
    return result


def attach_prediction_payload_daily_miss_streaks(
    payload: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    predictions = payload.get("predictions") if isinstance(payload.get("predictions"), dict) else {}
    panel = prediction_panel_from_value(predictions.get("panel") or payload.get("panel"))
    if panel != PREDICTION_PANEL_M:
        return payload
    tickets = predictions.get("strategyTickets") if isinstance(predictions.get("strategyTickets"), list) else []
    if not tickets:
        return payload
    target_context = payload.get("predictionTarget") if isinstance(payload.get("predictionTarget"), dict) else {}
    forecasts = predictions.get("forecasts") if isinstance(predictions.get("forecasts"), list) else []
    first_forecast = forecasts[0] if forecasts and isinstance(forecasts[0], dict) else {}
    target_ms = parse_int(target_context.get("targetDrawTimeMs"), 0) or parse_int(first_forecast.get("drawTimeMs"), 0)
    if target_ms <= 0:
        return payload

    copied_payload = dict(payload)
    copied_predictions = dict(predictions)
    copied_tickets: list[dict[str, Any]] = []
    pseudo_records: list[dict[str, Any]] = []
    method_version = prediction_method_version_for_panel(panel)
    target_utc = draw_time_utc_from_ms(target_ms)
    for index, ticket in enumerate(tickets, start=1):
        if not isinstance(ticket, dict):
            continue
        item = dict(ticket)
        rank = parse_int(item.get("ticketRank"), index)
        item["ticketRank"] = rank
        copied_tickets.append(item)
        pseudo_records.append(
            {
                "id": f"prediction_ticket_{index}",
                "createdAt": "",
                "gameKey": config["key"],
                "panel": panel,
                "methodVersion": method_version,
                "targetDrawTimeMs": target_ms,
                "targetDrawTimeUtc": target_utc,
                "status": "pending",
                "ticketRank": rank,
                "strategyLabel": str(item.get("label") or ""),
                "ticketLabel": str(item.get("ticketLabel") or "-".join(str(number) for number in item.get("numbers") or [])),
                "mode": str(item.get("mode") or "main"),
                "pickCount": parse_int(item.get("pickCount"), len(item.get("numbers") or [])),
                "numbers": [int(number) for number in item.get("numbers") or []],
                "bonusNumber": item.get("bonusNumber"),
            }
        )

    enriched_records = attach_prediction_tracking_daily_miss_streaks(pseudo_records, [], config)
    enriched_by_rank = {
        parse_int(record.get("ticketRank"), 0): record
        for record in enriched_records
        if parse_int(record.get("ticketRank"), 0) > 0
    }
    for item in copied_tickets:
        rank = parse_int(item.get("ticketRank"), 0)
        enriched = enriched_by_rank.get(rank)
        if not enriched:
            continue
        item["dailyMissStreak"] = parse_int(enriched.get("dailyMissStreak"), 0)
        item["dailyMissDisplayStreak"] = parse_int(enriched.get("dailyMissDisplayStreak"), item["dailyMissStreak"] + 1)
        item["dailyMissSource"] = str(enriched.get("dailyMissSource") or "tracking_day_slot")
        item["dailyMissStartDrawTimeMs"] = parse_int(enriched.get("dailyMissStartDrawTimeMs"), 0)
        item["dailyMissStartDrawTimeUtc"] = str(enriched.get("dailyMissStartDrawTimeUtc") or "")
    copied_predictions["strategyTickets"] = copied_tickets
    copied_payload["predictions"] = copied_predictions
    return copied_payload


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
    summary: dict[str, Any] | None = None,
    all_summary: dict[str, Any] | None = None,
    groups: list[dict[str, Any]] | None = None,
    adjacent_stats: dict[str, Any] | None = None,
    panel: str | None = PREDICTION_PANEL_DEFAULT,
) -> dict[str, Any]:
    panel_key = prediction_panel_from_value(panel) if panel is not None else None
    scoped_records = (
        [record for record in records if prediction_tracking_game_key(record) == config["key"]]
        if config is not None
        else records
    )
    scoped_records = prediction_records_for_panel(scoped_records, panel_key)
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
        ordered = prediction_records_for_panel(list(page_items), panel_key)
        total_items = len(ordered) if total_items is None else total_items
    total_page = max(1, math.ceil(total_items / page_size))
    page = max(1, min(page, total_page))
    start = (page - 1) * page_size
    end = start + page_size
    summary_item = summary if summary is not None else prediction_tracking_summary(scoped_records)
    all_summary_item = all_summary if all_summary is not None else (
        {"total": all_total}
        if all_total is not None
        else prediction_tracking_summary(prediction_records_for_panel(records, panel_key))
    )
    created_items = prediction_records_for_panel(created or [], panel_key)
    group_items = groups if groups is not None else prediction_tracking_group_summaries(scoped_records)
    response_items = ordered if page_items is not None else ordered[start:end]
    response_items = attach_prediction_tracking_daily_miss_streaks(response_items, scoped_records, config)
    return {
        "ok": True,
        "game": game_public_config(config) if config is not None else None,
        "panel": panel_key,
        "panelLabel": prediction_panel_label(panel_key),
        "generatedAt": utc_now_iso(),
        "trackingFile": file_info(DEFAULT_PREDICTION_TRACKING),
        "trackingDb": file_info(DEFAULT_PREDICTION_TRACKING_DB),
        "settledNow": settled_now,
        "autoSync": auto_sync,
        "createdNow": len(created_items),
        "created": created_items[:10],
        "deleted": deleted,
        "summary": summary_item,
        "allSummary": all_summary_item,
        "groups": group_items,
        "allGroups": group_items,
        "adjacentStats": adjacent_stats,
        "statusFilter": status_filter,
        "page": page,
        "pageSize": page_size,
        "total": total_items,
        "totalPage": total_page,
        "items": response_items,
        "allItems": [],
    }


def prediction_tracking_touch_response(
    records: list[dict[str, Any]],
    *,
    settled_now: int = 0,
    created: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
    panel: str | None = PREDICTION_PANEL_DEFAULT,
) -> dict[str, Any]:
    panel_key = prediction_panel_from_value(panel) if panel is not None else None
    scoped_records = (
        [record for record in records if prediction_tracking_game_key(record) == config["key"]]
        if config is not None
        else records
    )
    scoped_records = prediction_records_for_panel(scoped_records, panel_key)
    return {
        "panel": panel_key,
        "panelLabel": prediction_panel_label(panel_key),
        "settledNow": settled_now,
        "createdNow": len(prediction_records_for_panel(created or [], panel_key)),
        "summary": prediction_tracking_summary(scoped_records),
        "allSummary": {"total": prediction_tracking_count(panel=panel_key)},
    }


def skipped_prediction_tracking_touch_response(
    panel: str | None,
    reason: str,
    *,
    waited_ms: int = 0,
    lightweight: bool = True,
    auto_sync: dict[str, Any] | None = None,
) -> dict[str, Any]:
    panel_key = prediction_panel_from_value(panel)
    response = {
        "panel": panel_key,
        "panelLabel": prediction_panel_label(panel_key),
        "settledNow": 0,
        "createdNow": 0,
        "summary": {},
        "allSummary": {},
        "lightweight": lightweight,
        "skipped": True,
        "reason": reason,
    }
    if waited_ms:
        response["lockWaitMs"] = waited_ms
    if auto_sync is not None:
        response["autoSync"] = auto_sync
    return response


def prediction_tracking_auto_sync_status(
    records: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    latest_ms = max(
        (parse_int(row.get("drawTimeMs"), 0) for row in rows),
        default=0,
    )
    now_ms = int(time.time() * 1000)
    grace_ms = prediction_draw_sync_grace_ms(config)
    overdue_targets: list[int] = []
    overdue_records = 0
    if records:
        for record in records:
            if prediction_tracking_game_key(record) != config["key"]:
                continue
            if record.get("status") != "pending":
                continue
            target_ms = parse_int(record.get("targetDrawTimeMs"), 0)
            if target_ms > 0 and target_ms + grace_ms <= now_ms and latest_ms < target_ms:
                overdue_records += 1
                overdue_targets.append(target_ms)
    oldest_overdue_target = min(overdue_targets, default=0)
    newest_overdue_target = max(overdue_targets, default=0)
    return {
        "needsSync": overdue_records > 0,
        "reason": "history_behind_target" if overdue_records > 0 else "",
        "latestDrawTimeMs": latest_ms,
        "latestDrawTimeUtc": draw_time_utc_from_ms(latest_ms),
        "oldestOverdueTargetTimeMs": oldest_overdue_target,
        "oldestOverdueTargetTimeUtc": draw_time_utc_from_ms(oldest_overdue_target),
        "newestOverdueTargetTimeMs": newest_overdue_target,
        "newestOverdueTargetTimeUtc": draw_time_utc_from_ms(newest_overdue_target),
        "overduePendingRecords": overdue_records,
        "graceSeconds": round(grace_ms / 1000, 3),
    }


def prediction_history_waiting_for_latest_draw(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    latest_ms = max((parse_int(row.get("drawTimeMs"), 0) for row in rows), default=0)
    interval_ms = prediction_draw_interval_ms(config)
    if latest_ms <= 0 or interval_ms <= 0:
        return {"waiting": False, "reason": "missing_history_or_interval"}
    now_ms = int(time.time() * 1000)
    grace_ms = prediction_draw_sync_grace_ms(config)
    next_expected_ms, expected_offset = next_operating_draw_after_ms(latest_ms, config)
    waiting = next_expected_ms > 0 and next_expected_ms + grace_ms <= now_ms
    return {
        "waiting": waiting,
        "reason": "history_latest_draw_overdue" if waiting else "",
        "latestDrawTimeMs": latest_ms,
        "latestDrawTimeUtc": draw_time_utc_from_ms(latest_ms),
        "nextExpectedDrawTimeMs": next_expected_ms,
        "nextExpectedDrawTimeUtc": draw_time_utc_from_ms(next_expected_ms),
        "nextExpectedDrawOffset": expected_offset,
        "graceSeconds": round(grace_ms / 1000, 3),
    }


def prediction_tracking_needs_auto_sync(
    records: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> bool:
    return bool(prediction_tracking_auto_sync_status(records, rows, config)["needsSync"])


def maybe_auto_sync_prediction_tracking(
    config: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
    auto_sync_status = prediction_tracking_auto_sync_status(records, rows, config)
    history_wait = prediction_history_waiting_for_latest_draw(rows, config)
    needs_sync = bool(auto_sync_status["needsSync"] or history_wait.get("waiting"))
    if not needs_sync:
        return rows, None
    trigger_status = {
        **auto_sync_status,
        "needsSync": True,
        "reason": auto_sync_status["reason"] or history_wait.get("reason") or "history_latest_draw_overdue",
        "trackingWait": auto_sync_status if auto_sync_status["needsSync"] else None,
        "historyWait": history_wait if history_wait.get("waiting") else None,
    }

    now = time.monotonic()
    with PREDICTION_TRACKING_AUTO_SYNC_LOCK:
        last_attempt = PREDICTION_TRACKING_AUTO_SYNC_LAST_ATTEMPT.get(config["key"], 0.0)
        cooldown_seconds = PREDICTION_TRACKING_OVERDUE_AUTO_SYNC_COOLDOWN_SECONDS
        if now - last_attempt < cooldown_seconds:
            retry_after = max(0.0, cooldown_seconds - (now - last_attempt))
            return rows, {
                **trigger_status,
                "skipped": True,
                "reason": "cooldown",
                "triggerReason": trigger_status["reason"],
                "cooldownSeconds": cooldown_seconds,
                "retryAfterSeconds": round(retry_after, 1),
            }
        PREDICTION_TRACKING_AUTO_SYNC_LAST_ATTEMPT[config["key"]] = now

    result = refresh_official_history_only(config, timeout=5)
    with DATA_LOCK:
        refreshed_rows = load_history_rows(game_history_path(config), config)
    result = dict(result)
    result.update(
        {
            "skipped": False,
            "reason": trigger_status["reason"],
            "cooldownSeconds": cooldown_seconds,
            "trigger": trigger_status,
        }
    )
    return refreshed_rows, result


def prediction_background_sync_worker(game_key: str) -> None:
    try:
        refresh_history(
            {
                "game": game_key,
                "mode": "incremental",
                "pageSize": 100,
                "maxPages": 2,
                "sleep": 0.05,
                "timeout": 5,
                "retries": 0,
                "retrySleep": 0.5,
                "skipSupplement": False,
            }
        )
    finally:
        with PREDICTION_TRACKING_AUTO_SYNC_LOCK:
            PREDICTION_BACKGROUND_SYNC_IN_FLIGHT.discard(game_key)


def schedule_prediction_background_sync(
    config: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    game_key = str(config.get("key") or "")
    auto_config = load_prediction_auto_config()
    if game_key not in prediction_auto_enabled_games(auto_config):
        return {
            "scheduled": False,
            "skipped": True,
            "reason": "auto_tracking_game_disabled",
            "game": game_key,
        }
    with PREDICTION_AUTO_LOCK:
        auto_status = dict(PREDICTION_AUTO_STATUS)
    auto_last_run = str(auto_status.get("lastRunAt") or "")
    auto_last_completed = str(auto_status.get("lastCompletedAt") or "")
    auto_cycle_running = bool(
        auto_status.get("running")
        and auto_last_run
        and (not auto_last_completed or auto_last_run > auto_last_completed)
    )
    if auto_cycle_running:
        return {
            "scheduled": False,
            "skipped": True,
            "reason": "auto_worker_running",
            "game": game_key,
        }
    now = time.monotonic()
    cooldown_seconds = PREDICTION_TRACKING_OVERDUE_AUTO_SYNC_COOLDOWN_SECONDS
    with PREDICTION_TRACKING_AUTO_SYNC_LOCK:
        if game_key in PREDICTION_BACKGROUND_SYNC_IN_FLIGHT:
            return {
                "scheduled": False,
                "inFlight": True,
                "reason": "already_running",
                "game": game_key,
            }
        last_attempt = PREDICTION_BACKGROUND_SYNC_LAST_ATTEMPT.get(game_key, 0.0)
        if now - last_attempt < cooldown_seconds:
            return {
                "scheduled": False,
                "skipped": True,
                "reason": "cooldown",
                "game": game_key,
                "retryAfterSeconds": round(cooldown_seconds - (now - last_attempt), 1),
            }
        PREDICTION_BACKGROUND_SYNC_LAST_ATTEMPT[game_key] = now
        PREDICTION_BACKGROUND_SYNC_IN_FLIGHT.add(game_key)
    worker = threading.Thread(
        target=prediction_background_sync_worker,
        args=(game_key,),
        daemon=True,
    )
    worker.start()
    return {
        "scheduled": True,
        "reason": reason,
        "game": game_key,
        "cooldownSeconds": cooldown_seconds,
    }


def touch_prediction_tracking_for_payload(
    payload: dict[str, Any],
    config: dict[str, Any],
    rows: list[dict[str, Any]] | None = None,
    *,
    allow_auto_sync: bool = False,
) -> dict[str, Any]:
    predictions = payload.get("predictions") if isinstance(payload.get("predictions"), dict) else {}
    panel = prediction_panel_from_value(predictions.get("panel") or payload.get("panel"))
    auto_sync: dict[str, Any] | None = None
    if not allow_auto_sync:
        auto_sync = {"skipped": True, "reason": "prediction_payload_no_auto_sync"}
        lock_started = time.monotonic()
        lock_acquired = PREDICTION_TRACKING_LOCK.acquire(
            timeout=PREDICTION_TRACKING_TOUCH_LOCK_TIMEOUT_SECONDS
        )
        lock_wait_ms = round((time.monotonic() - lock_started) * 1000)
        if not lock_acquired:
            return skipped_prediction_tracking_touch_response(
                panel,
                "prediction_tracking_lock_busy",
                waited_ms=lock_wait_ms,
                auto_sync=auto_sync,
            )
        try:
            created = add_prediction_tracking_snapshot_lightweight(payload, config)
        finally:
            PREDICTION_TRACKING_LOCK.release()
        return {
            "panel": panel,
            "panelLabel": prediction_panel_label(panel),
            "settledNow": 0,
            "createdNow": len(prediction_records_for_panel(created, panel)),
            "summary": {},
            "allSummary": {},
            "lightweight": True,
            "autoSync": auto_sync,
            "lockWaitMs": lock_wait_ms,
        }

    if rows is None:
        with DATA_LOCK:
            rows = load_history_rows(game_history_path(config), config)
    if allow_auto_sync:
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
        settled_for_panel = len(prediction_records_for_panel(changed_records, panel)) if settled_now else 0
        return prediction_tracking_touch_response(
            records,
            settled_now=settled_for_panel,
            created=created,
            config=config,
            panel=panel,
        ) | {"autoSync": auto_sync}


def prediction_tracking_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    config = game_from_query(query)
    ensure_prediction_tracking_supported(config)
    panel = prediction_panel_from_query(query)
    ensure_prediction_tracking_panel_active(panel)
    page = max(1, parse_int(query.get("page", ["1"])[0], 1))
    page_size = max(10, min(parse_int(query.get("pageSize", ["50"])[0], 50), 200))
    status_filter = str(query.get("status", ["all"])[0] or "all")
    allowed_statuses = {"pending", "won", "lost", "cancelled", "void"}
    status_filter = status_filter if status_filter in allowed_statuses else "all"
    allow_auto_sync = query_bool(query, "autoSync", True)
    auto_sync: dict[str, Any] | None = None
    settled_for_panel = 0
    summary: dict[str, Any] | None = None
    all_summary: dict[str, Any] | None = None
    groups: list[dict[str, Any]] | None = None
    if allow_auto_sync:
        with DATA_LOCK:
            rows = load_history_rows(game_history_path(config), config)
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
            settled_for_panel = len(prediction_records_for_panel(changed_records, panel)) if settled_now else 0
            total_items = prediction_tracking_count(config["key"], status_filter, panel=panel)
            total_page = max(1, math.ceil(total_items / page_size))
            page = max(1, min(page, total_page))
            page_items = load_prediction_tracking_for_game(
                config["key"],
                status_filter=status_filter,
                limit=page_size,
                offset=(page - 1) * page_size,
                panel=panel,
            )
        panel_records = prediction_records_for_panel(records, panel)
        groups = prediction_tracking_group_summaries(panel_records)
        all_total = prediction_tracking_count(panel=panel)
    else:
        auto_sync = {"skipped": True, "reason": "request_disabled"}
        total_items = prediction_tracking_count(config["key"], status_filter, panel=panel)
        total_page = max(1, math.ceil(total_items / page_size))
        page = max(1, min(page, total_page))
        page_items = load_prediction_tracking_for_game(
            config["key"],
            status_filter=status_filter,
            limit=page_size,
            offset=(page - 1) * page_size,
            panel=panel,
        )
        records = []
        summary = prediction_tracking_summary_from_db(config["key"], panel=panel)
        all_total = prediction_tracking_count(panel=panel)
        all_summary = {"total": all_total}
        groups = prediction_tracking_group_summaries_from_db(config["key"], panel=panel)
    return prediction_tracking_response(
        records,
        settled_now=settled_for_panel,
        config=config,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        page_items=page_items,
        total_items=total_items,
        all_total=all_total,
        auto_sync=auto_sync,
        summary=summary,
        all_summary=all_summary,
        groups=groups,
        panel=panel,
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
    panel = prediction_panel_from_value(payload.get("panel"))
    ensure_prediction_tracking_panel_active(panel)
    with DATA_LOCK:
        rows = load_history_rows(game_history_path(config), config)
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
        changed_records: list[dict[str, Any]] = []
        settled_now = settle_prediction_tracking(records, rows, config, changed_records)
        if settled_now:
            write_prediction_tracking(changed_records)
        settled_for_panel = len(prediction_records_for_panel(changed_records, panel)) if settled_now else 0
        return prediction_tracking_response(records, settled_now=settled_for_panel, config=config, panel=panel)


def delete_prediction_tracking(record_id: str, query: dict[str, list[str]]) -> dict[str, Any]:
    record_id = str(record_id or "").strip()
    if not record_id:
        raise ValueError("追踪记录 ID 无效")
    config = game_from_query(query)
    panel = prediction_panel_from_query(query)
    ensure_prediction_tracking_panel_active(panel)
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
        return prediction_tracking_response(remaining, deleted=deleted, config=config, panel=panel)


def default_telegram_config() -> dict[str, Any]:
    return {
        "enabled": False,
        "channelChatId": "@Keno100x",
        "adminIds": ["988670752"],
        "inviteLink": "https://playglobal4.com/i-23u4bw0u7-n/",
        "drawLink": "",
        "drawLinksByGame": dict(TELEGRAM_DEFAULT_DRAW_LINKS_BY_GAME),
        "botPollingEnabled": True,
        "stakingProfile": "conservative",
        "baseStake": 1.0,
        "stepStake": 1.0,
        "conservativeStepMisses": 30,
        "conservativeMaxStake": 5.0,
        "standardStepMisses": 20,
        "standardMaxStake": 8.0,
        "aggressiveStepMisses": 10,
        "aggressiveMaxStake": 12.0,
        "profitPinStep": 50.0,
        "pinProfitMilestones": True,
        "pinDailySummary": True,
        "dailySummaryHour": 23,
        "dailySummaryMinute": 55,
        "allGames": False,
        "games": {
            key: {"enabled": key == DEFAULT_GAME_KEY and supports_predictions(config)}
            for key, config in LOTTERY_GAMES.items()
        },
    }


def load_telegram_config() -> dict[str, Any]:
    config = default_telegram_config()
    if DEFAULT_TELEGRAM_CONFIG.exists():
        try:
            with DEFAULT_TELEGRAM_CONFIG.open("r", encoding="utf-8") as fh:
                stored = json.load(fh)
        except (OSError, json.JSONDecodeError):
            stored = {}
        if isinstance(stored, dict):
            config.update({key: value for key, value in stored.items() if key not in {"games", "drawLinksByGame"}})
            stored_games = stored.get("games") if isinstance(stored.get("games"), dict) else {}
            for key, value in stored_games.items():
                if key in config["games"] and isinstance(value, dict):
                    config["games"][key].update(value)
            stored_draw_links = stored.get("drawLinksByGame") if isinstance(stored.get("drawLinksByGame"), dict) else {}
            for key, value in stored_draw_links.items():
                if key in LOTTERY_GAMES:
                    config["drawLinksByGame"][key] = str(value or "").strip()
    for key, game_config in LOTTERY_GAMES.items():
        if not supports_predictions(game_config):
            config["games"].setdefault(key, {})["enabled"] = False
    config["adminIds"] = [str(item) for item in config.get("adminIds") or [] if str(item or "").strip()]
    config["channelChatId"] = str(config.get("channelChatId") or "").strip() or "@Keno100x"
    config["inviteLink"] = str(config.get("inviteLink") or "").strip()
    config["drawLink"] = str(config.get("drawLink") or "").strip()
    if config["drawLink"].rstrip("/") in {link.rstrip("/") for link in TELEGRAM_ROOT_DRAW_LINKS}:
        config["drawLink"] = ""
    draw_links = config.get("drawLinksByGame") if isinstance(config.get("drawLinksByGame"), dict) else {}
    config["drawLinksByGame"] = dict(TELEGRAM_DEFAULT_DRAW_LINKS_BY_GAME)
    for key, value in draw_links.items():
        if key in LOTTERY_GAMES:
            text = str(value or "").strip()
            config["drawLinksByGame"][key] = "" if text.rstrip("/") in {link.rstrip("/") for link in TELEGRAM_ROOT_DRAW_LINKS} else text
    config["profitPinStep"] = max(1.0, parse_float(config.get("profitPinStep"), 50.0))
    config["dailySummaryHour"] = max(0, min(parse_int(config.get("dailySummaryHour"), 23), 23))
    config["dailySummaryMinute"] = max(0, min(parse_int(config.get("dailySummaryMinute"), 55), 59))
    config["baseStake"] = max(0.01, parse_float(config.get("baseStake"), 1.0))
    config["stepStake"] = max(0.01, parse_float(config.get("stepStake"), 1.0))
    staking_profile = str(config.get("stakingProfile") or "conservative").strip().lower()
    if staking_profile not in STAKING_BACKTEST_POLICY_DEFAULTS:
        staking_profile = "conservative"
    config["stakingProfile"] = staking_profile
    config["conservativeStepMisses"] = max(1, parse_int(config.get("conservativeStepMisses"), 30))
    config["conservativeMaxStake"] = max(config["baseStake"], parse_float(config.get("conservativeMaxStake"), 5.0))
    config["standardStepMisses"] = max(1, parse_int(config.get("standardStepMisses"), 20))
    config["standardMaxStake"] = max(config["baseStake"], parse_float(config.get("standardMaxStake"), 8.0))
    config["aggressiveStepMisses"] = max(1, parse_int(config.get("aggressiveStepMisses"), 10))
    config["aggressiveMaxStake"] = max(config["baseStake"], parse_float(config.get("aggressiveMaxStake"), 12.0))
    config["customStepMisses"] = max(1, parse_int(config.get("customStepMisses"), config["standardStepMisses"]))
    config["customMaxStake"] = max(config["baseStake"], parse_float(config.get("customMaxStake"), config["standardMaxStake"]))
    if config.get("enabled") and not str(config.get("enabledAt") or "").strip():
        try:
            config["enabledAt"] = datetime.fromtimestamp(DEFAULT_TELEGRAM_CONFIG.stat().st_mtime, tz=UTC).isoformat()
        except OSError:
            config["enabledAt"] = utc_now_iso()
    return config


def write_telegram_config(config: dict[str, Any]) -> None:
    temp_path = DEFAULT_TELEGRAM_CONFIG.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    replace_path_with_retry(temp_path, DEFAULT_TELEGRAM_CONFIG)


def telegram_public_config(config: dict[str, Any]) -> dict[str, Any]:
    public = {key: value for key, value in config.items() if key != "botToken"}
    public["tokenConfigured"] = bool(telegram_bot_token(config))
    return public


def load_telegram_state() -> dict[str, Any]:
    if DEFAULT_TELEGRAM_STATE.exists():
        try:
            with DEFAULT_TELEGRAM_STATE.open("r", encoding="utf-8") as fh:
                state = json.load(fh)
        except (OSError, json.JSONDecodeError):
            state = {}
    else:
        state = {}
    if not isinstance(state, dict):
        state = {}
    state.setdefault("sentPlanBatches", [])
    state.setdefault("sentResultBatches", [])
    state.setdefault("pinnedMilestones", {})
    state.setdefault("dailySummaries", {})
    state.setdefault("lastErrors", [])
    return state


def write_telegram_state(state: dict[str, Any]) -> None:
    for key in ("sentPlanBatches", "sentResultBatches"):
        values = [str(item) for item in state.get(key) or [] if str(item or "").strip()]
        state[key] = values[-1000:]
    if len(state.get("lastErrors") or []) > 30:
        state["lastErrors"] = state["lastErrors"][-30:]
    temp_path = DEFAULT_TELEGRAM_STATE.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    replace_path_with_retry(temp_path, DEFAULT_TELEGRAM_STATE)


def telegram_state_contains(state: dict[str, Any], key: str, value: str) -> bool:
    return str(value) in {str(item) for item in state.get(key) or []}


def telegram_state_add(state: dict[str, Any], key: str, value: str) -> None:
    items = [str(item) for item in state.get(key) or [] if str(item or "").strip()]
    if value not in items:
        items.append(value)
    state[key] = items[-1000:]


def telegram_bot_token(config: dict[str, Any]) -> str:
    return str(os.environ.get("TELEGRAM_BOT_TOKEN") or config.get("botToken") or "").strip()


def telegram_api_request(method: str, payload: dict[str, Any], config: dict[str, Any], *, timeout: int = 10) -> dict[str, Any]:
    token = telegram_bot_token(config)
    if not token:
        raise ValueError("Telegram bot token 未配置")
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram HTTP {exc.code}: {detail}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"Telegram network error: {exc.reason}") from exc
    data = json.loads(raw)
    if not data.get("ok"):
        raise RuntimeError(str(data.get("description") or "Telegram API error"))
    return data


def telegram_send_message(
    config: dict[str, Any],
    text: str,
    *,
    chat_id: Any | None = None,
    disable_preview: bool = True,
    parse_mode: str | None = None,
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "chat_id": chat_id if chat_id not in (None, "") else config.get("channelChatId"),
        "text": text,
        "disable_web_page_preview": disable_preview,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram_api_request(
        "sendMessage",
        payload,
        config,
    )


def telegram_edit_message_text(
    config: dict[str, Any],
    chat_id: Any,
    message_id: int,
    text: str,
    *,
    parse_mode: str | None = None,
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram_api_request("editMessageText", payload, config)


def telegram_answer_callback_query(config: dict[str, Any], callback_id: str, text: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    return telegram_api_request("answerCallbackQuery", payload, config)


def telegram_set_bot_commands(config: dict[str, Any]) -> dict[str, Any]:
    return telegram_api_request(
        "setMyCommands",
        {
            "commands": [
                {"command": "menu", "description": "打开 CPGAME 控制菜单"},
                {"command": "status", "description": "查看推送状态"},
            ]
        },
        config,
    )


def telegram_pin_message(config: dict[str, Any], message_id: int) -> dict[str, Any]:
    return telegram_api_request(
        "pinChatMessage",
        {
            "chat_id": config.get("channelChatId"),
            "message_id": message_id,
            "disable_notification": True,
        },
        config,
    )


def telegram_game_enabled(config: dict[str, Any], game_key: str) -> bool:
    if not config.get("enabled"):
        return False
    if config.get("allGames"):
        return game_key in LOTTERY_GAMES and supports_predictions(LOTTERY_GAMES[game_key])
    games = config.get("games") if isinstance(config.get("games"), dict) else {}
    item = games.get(game_key) if isinstance(games.get(game_key), dict) else {}
    return bool(item.get("enabled"))


def telegram_staking_policy(config: dict[str, Any]) -> dict[str, Any]:
    profile = str(config.get("stakingProfile") or "conservative").strip().lower()
    if profile not in STAKING_BACKTEST_POLICY_DEFAULTS:
        profile = "conservative"
    defaults = STAKING_BACKTEST_POLICY_DEFAULTS[profile]
    base_stake = parse_float(config.get("baseStake"), 1.0)
    if profile == "flat":
        return {
            "key": "flat",
            "label": str(defaults.get("label") or "平买"),
            "kind": "flat",
            "baseStake": base_stake,
            "stepMisses": 0,
            "stepStake": 0.0,
            "maxStake": base_stake,
        }
    step_misses = parse_int(config.get(f"{profile}StepMisses"), parse_int(defaults.get("stepMisses"), 30))
    max_stake = parse_float(config.get(f"{profile}MaxStake"), parse_float(defaults.get("maxStake"), base_stake))
    return {
        "key": profile,
        "label": str(defaults.get("label") or profile),
        "kind": str(defaults.get("kind") or "ladder"),
        "baseStake": base_stake,
        "stepMisses": max(1, step_misses),
        "stepStake": parse_float(config.get("stepStake"), 1.0),
        "maxStake": max(base_stake, max_stake),
    }


def telegram_stake_text(stake: float, policy: dict[str, Any]) -> str:
    base = parse_float(policy.get("baseStake"), 1.0)
    multiple = stake / base if base > 0 else stake
    return f"{stake:g}元 / {multiple:g}倍"


def telegram_record_stake_text(record: dict[str, Any], config: dict[str, Any]) -> str:
    policy = telegram_staking_policy(config)
    current_miss = parse_int(record.get("currentMiss"), 0)
    stake = staking_backtest_stake_for_miss(policy, current_miss)
    return telegram_stake_text(stake, policy)


def telegram_record_numbers_text(record: dict[str, Any]) -> str:
    numbers = "-".join(str(number) for number in record.get("numbers") or [])
    bonus = record.get("bonusNumber")
    if bonus not in (None, "", 0):
        return f"{numbers}+{bonus}"
    return numbers


def telegram_md_code(value: Any) -> str:
    text = str(value if value not in (None, "") else "--").replace("```", "` ` `").strip()
    return f"```\n{text or '--'}\n```"


def telegram_html_text(value: Any) -> str:
    return html.escape(str(value if value not in (None, "") else "--").strip() or "--", quote=False)


def telegram_html_code(value: Any) -> str:
    return f"<code>{telegram_html_text(value)}</code>"


def telegram_signed_amount(value: float) -> str:
    return f"{value:+g}"


def telegram_draw_link_for_game(game_config: dict[str, Any], config: dict[str, Any]) -> str:
    game_key = str(game_config.get("key") or "")
    draw_links = config.get("drawLinksByGame") if isinstance(config.get("drawLinksByGame"), dict) else {}
    link = str(draw_links.get(game_key) or "").strip()
    if not link:
        link = str(config.get("drawLink") or "").strip()
    if link.rstrip("/") in {item.rstrip("/") for item in TELEGRAM_ROOT_DRAW_LINKS}:
        return ""
    return link


def telegram_message_buttons(game_config: dict[str, Any], config: dict[str, Any]) -> dict[str, Any] | None:
    buttons: list[dict[str, str]] = []
    invite_link = str(config.get("inviteLink") or "").strip()
    draw_link = telegram_draw_link_for_game(game_config, config)
    if invite_link:
        buttons.append({"text": "投注地址", "url": invite_link})
    if draw_link:
        buttons.append({"text": "开奖地址", "url": draw_link})
    if not buttons:
        return None
    return {"inline_keyboard": [buttons]}


def telegram_display_timezone() -> ZoneInfo:
    return ZoneInfo(STAKING_BACKTEST_DEFAULT_TIMEZONE)


def telegram_format_utc8_ms(timestamp_ms: int) -> str:
    if timestamp_ms <= 0:
        return "--"
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).astimezone(telegram_display_timezone())
    return f"{dt:%Y-%m-%d %H:%M} UTC+8"


def telegram_format_utc8_hhmm_ms(timestamp_ms: int) -> str:
    if timestamp_ms <= 0:
        return "--:--"
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).astimezone(telegram_display_timezone())
    return f"{dt:%H:%M}"


def telegram_game_day_timezone(game_config: dict[str, Any]) -> ZoneInfo:
    schedule = game_config.get("operatingHours") if isinstance(game_config.get("operatingHours"), dict) else {}
    name = str(schedule.get("timezone") or STAKING_BACKTEST_DEFAULT_TIMEZONE).strip()
    try:
        return ZoneInfo(name)
    except Exception:
        return telegram_display_timezone()


def telegram_records_target_ms(records: list[dict[str, Any]]) -> int:
    values: list[int] = []
    for record in records:
        values.append(parse_int(record.get("targetDrawTimeMs"), 0))
        result = record.get("result") if isinstance(record.get("result"), dict) else {}
        draw = result.get("draw") if isinstance(result.get("draw"), dict) else {}
        values.append(parse_int(draw.get("drawTimeMs"), 0))
    return max(values, default=0)


def telegram_scheduled_daily_start_ms(game_config: dict[str, Any], current_target_ms: int) -> int:
    if current_target_ms <= 0:
        return 0
    schedule = game_config.get("operatingHours") if isinstance(game_config.get("operatingHours"), dict) else {}
    start_minute = staking_backtest_time_minutes(schedule.get("start"))
    if start_minute is None:
        return 0
    tz = telegram_game_day_timezone(game_config)
    current_local = datetime.fromtimestamp(current_target_ms / 1000, tz=UTC).astimezone(tz)
    start_local = datetime(
        current_local.year,
        current_local.month,
        current_local.day,
        start_minute // 60,
        start_minute % 60,
        tzinfo=tz,
    )
    return int(start_local.astimezone(UTC).timestamp() * 1000)


def telegram_daily_draw_window(game_config: dict[str, Any], current_target_ms: int) -> dict[str, Any]:
    if current_target_ms <= 0:
        return {
            "startMs": 0,
            "endMs": 0,
            "startText": "--",
            "endText": "--",
            "rows": [],
            "source": "empty",
        }
    tz = telegram_game_day_timezone(game_config)
    current_local_date = datetime.fromtimestamp(current_target_ms / 1000, tz=UTC).astimezone(tz).date()
    history_path = game_history_path(game_config)
    with DATA_LOCK:
        all_rows = load_history_rows(history_path, game_config)
    rows = valid_draw_rows(all_rows, game_config)
    same_day_rows = []
    for row in rows:
        draw_time_ms = parse_int(row.get("drawTimeMs"), 0)
        if draw_time_ms <= 0 or draw_time_ms > current_target_ms:
            continue
        local_date = datetime.fromtimestamp(draw_time_ms / 1000, tz=UTC).astimezone(tz).date()
        if local_date == current_local_date:
            same_day_rows.append(row)

    start_ms = min((parse_int(row.get("drawTimeMs"), 0) for row in same_day_rows), default=0)
    source = "history"
    if start_ms <= 0:
        start_ms = telegram_scheduled_daily_start_ms(game_config, current_target_ms)
        source = "schedule" if start_ms > 0 else "empty"

    if same_day_rows:
        window_rows = same_day_rows
    elif start_ms > 0:
        window_rows = [
            row
            for row in rows
            if start_ms <= parse_int(row.get("drawTimeMs"), 0) <= current_target_ms
        ]
    else:
        window_rows = []
    window_rows = sorted(window_rows, key=lambda row: parse_int(row.get("drawTimeMs"), 0))
    return {
        "startMs": start_ms,
        "endMs": current_target_ms,
        "startText": telegram_format_utc8_ms(start_ms),
        "endText": telegram_format_utc8_ms(current_target_ms),
        "rows": window_rows,
        "source": source,
        "gameTimeZone": str(tz.key),
        "displayTimeZone": STAKING_BACKTEST_DEFAULT_TIMEZONE,
    }


def telegram_record_ticket_parts(record: dict[str, Any]) -> tuple[tuple[int, ...], int | None]:
    numbers = tuple(
        int(number)
        for number in record.get("numbers") or []
        if parse_int(number, 0) > 0
    )
    bonus_raw = record.get("bonusNumber")
    bonus_number = parse_int(bonus_raw, 0) if bonus_raw not in (None, "") else None
    if bonus_number is not None and bonus_number <= 0:
        bonus_number = None
    return numbers, bonus_number


def telegram_record_window_simulation(
    record: dict[str, Any],
    draw_rows_oldest: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    current_target_ms: int = 0,
) -> dict[str, Any]:
    policy = telegram_staking_policy(config)
    numbers, bonus_number = telegram_record_ticket_parts(record)
    odds = max(0.0, parse_float(record.get("odds"), 0))
    total_stake = 0.0
    total_payout = 0.0
    wins = 0
    miss_streak = 0
    current_seen = False
    current_stake = 0.0
    current_profit = 0.0
    current_won = None
    current_matched: list[int] = []

    for row in draw_rows_oldest:
        draw_time_ms = parse_int(row.get("drawTimeMs"), 0)
        if current_target_ms and draw_time_ms > current_target_ms:
            continue
        stake = staking_backtest_stake_for_miss(policy, miss_streak)
        won = ticket_hit(row, numbers, bonus_number)
        payout = stake * odds if won else 0.0
        profit = payout - stake
        total_stake += stake
        total_payout += payout
        if won:
            wins += 1
        if current_target_ms and draw_time_ms == current_target_ms:
            draw_set = set(row.get("numbers") or [])
            current_seen = True
            current_stake = stake
            current_profit = profit
            current_won = won
            current_matched = [number for number in numbers if number in draw_set]
        miss_streak = 0 if won else miss_streak + 1

    current_row_in_history = any(
        parse_int(row.get("drawTimeMs"), 0) == current_target_ms for row in draw_rows_oldest
    )
    if current_target_ms and not current_seen and record.get("status") in {"won", "lost"}:
        stake = staking_backtest_stake_for_miss(policy, miss_streak)
        won = record.get("status") == "won"
        payout = stake * odds if won else 0.0
        profit = payout - stake
        total_stake += stake
        total_payout += payout
        if won:
            wins += 1
        result = record.get("result") if isinstance(record.get("result"), dict) else {}
        current_seen = True
        current_stake = stake
        current_profit = profit
        current_won = won
        current_matched = [parse_int(number, 0) for number in result.get("matchedNumbers") or []]
        miss_streak = 0 if won else miss_streak + 1

    next_stake = staking_backtest_stake_for_miss(policy, miss_streak)
    rounds = len(draw_rows_oldest) + (1 if current_seen and not current_row_in_history else 0)
    net_profit = total_payout - total_stake
    return {
        "policy": policy,
        "periods": rounds,
        "wins": wins,
        "losses": max(0, rounds - wins),
        "stake": round(total_stake, 4),
        "payout": round(total_payout, 4),
        "profit": round(net_profit, 4),
        "roi": net_profit / total_stake if total_stake > 0 else 0.0,
        "currentStake": round(current_stake if current_seen else next_stake, 4),
        "currentProfit": round(current_profit, 4) if current_seen else 0.0,
        "currentWon": current_won,
        "currentMatchedNumbers": current_matched,
        "nextStake": round(next_stake, 4),
        "currentMissStreak": miss_streak,
    }




def telegram_record_stake_amount(record: dict[str, Any], config: dict[str, Any]) -> float:
    policy = telegram_staking_policy(config)
    current_miss = parse_int(record.get("currentMiss"), 0)
    return max(0.0, staking_backtest_stake_for_miss(policy, current_miss))


def telegram_record_profit_amount(record: dict[str, Any], config: dict[str, Any]) -> float:
    stake = telegram_record_stake_amount(record, config)
    if record.get("status") == "won":
        return stake * max(0.0, parse_float(record.get("odds"), 0)) - stake
    if record.get("status") == "lost":
        return -stake
    return 0.0


def telegram_candidate_slots(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        records,
        key=lambda record: (
            parse_int(record.get("pickCount"), len(record.get("numbers") or [])),
            -parse_float(record.get("score"), 0),
            telegram_record_numbers_text(record),
        ),
    )
    pick_counts: dict[int, int] = {}
    result: list[dict[str, Any]] = []
    for record in ordered:
        pick_count = parse_int(record.get("pickCount"), len(record.get("numbers") or []))
        pick_counts[pick_count] = pick_counts.get(pick_count, 0) + 1
        slot = pick_counts[pick_count]
        result.append(
            {
                "key": f"p{pick_count}_{slot}",
                "slotLabel": f"{pick_count}码{slot}",
                "record": record,
            }
        )
    return result


def telegram_cumulative_candidate_summaries(
    game_config: dict[str, Any],
    config: dict[str, Any],
    current_records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    current_slots = telegram_candidate_slots(current_records)
    current_target_ms = telegram_records_target_ms([item["record"] for item in current_slots])
    window = telegram_daily_draw_window(game_config, current_target_ms)
    draw_rows = [row for row in window.get("rows") or [] if isinstance(row, dict)]
    summaries: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(current_slots, start=1):
        record = item["record"]
        simulation = telegram_record_window_simulation(
            record,
            draw_rows,
            config,
            current_target_ms=current_target_ms,
        )
        summaries[item["key"]] = {
            "candidateLabel": f"候选{index}",
            "slotLabel": item["slotLabel"],
            "numbers": telegram_record_numbers_text(record),
            "startText": str(window.get("startText") or "--"),
            "endText": str(window.get("endText") or "--"),
            "startMs": parse_int(window.get("startMs"), 0),
            "endMs": parse_int(window.get("endMs"), 0),
            "periods": parse_int(simulation.get("periods"), 0),
            "wins": parse_int(simulation.get("wins"), 0),
            "losses": parse_int(simulation.get("losses"), 0),
            "stake": parse_float(simulation.get("stake"), 0),
            "payout": parse_float(simulation.get("payout"), 0),
            "profit": parse_float(simulation.get("profit"), 0),
            "roi": parse_float(simulation.get("roi"), 0),
            "currentStake": parse_float(simulation.get("currentStake"), 0),
            "currentProfit": parse_float(simulation.get("currentProfit"), 0),
            "currentWon": simulation.get("currentWon"),
            "currentMatchedNumbers": simulation.get("currentMatchedNumbers") or [],
            "nextStake": parse_float(simulation.get("nextStake"), 0),
            "currentMissStreak": parse_int(simulation.get("currentMissStreak"), 0),
            "policy": simulation.get("policy") or telegram_staking_policy(config),
            "windowSource": str(window.get("source") or ""),
        }
    return summaries


def telegram_plan_message(game_config: dict[str, Any], records: list[dict[str, Any]], config: dict[str, Any]) -> str:
    slots = telegram_candidate_slots(records)
    target_ms = telegram_records_target_ms([item["record"] for item in slots])
    window = telegram_daily_draw_window(game_config, target_ms)
    draw_rows = [
        row
        for row in window.get("rows") or []
        if isinstance(row, dict) and parse_int(row.get("drawTimeMs"), 0) < target_ms
    ]
    policy = telegram_staking_policy(config)
    ticket_lines: list[str] = []
    for index, item in enumerate(slots, start=1):
        record = item["record"]
        simulation = telegram_record_window_simulation(record, draw_rows, config)
        stake = parse_float(simulation.get("nextStake"), parse_float(simulation.get("currentStake"), 0))
        odds_text = f"{parse_float(record.get('odds'), 0):g}x"
        ticket_lines.append(
            "\n".join(
                [
                    f"候选{index}  {telegram_html_text(item['slotLabel'])}  {telegram_html_code(telegram_record_numbers_text(record))}",
                    (
                        f"赔率 {telegram_html_code(odds_text)}  "
                        f"下注 {telegram_html_code(telegram_stake_text(stake, policy))}  "
                        f"连挂 {telegram_html_code(parse_int(simulation.get('currentMissStreak'), 0))}"
                    ),
                    f"判断 {telegram_html_code(record.get('followDecision') or '只观察')}",
                ]
            )
        )
    policy_line = (
        f"{policy.get('label')} | {parse_int(policy.get('stepMisses'), 0)}期不中+1元"
        f" | 上限{parse_float(policy.get('maxStake'), 0):g}元"
    )
    lines = [
        f"<b>C计划 · {telegram_html_text(game_config['shortName'])}</b>",
        f"首期 {telegram_html_code(window.get('startText') or '--')}",
        f"目标 {telegram_html_code(telegram_format_utc8_ms(target_ms))}",
        f"档位 {telegram_html_code(policy_line)}",
        "",
        "<b>投注号码</b>",
        "\n\n".join(ticket_lines),
    ]
    return "\n".join(lines).strip()


def telegram_result_message(game_config: dict[str, Any], records: list[dict[str, Any]], config: dict[str, Any]) -> str:
    slots = telegram_candidate_slots(records)
    first = slots[0]["record"] if slots else {}
    draw = (first.get("result") or {}).get("draw") if isinstance(first.get("result"), dict) else {}
    draw_time_ms = parse_int(draw.get("drawTimeMs"), telegram_records_target_ms(records))
    draw_numbers = " ".join(str(number) for number in (draw or {}).get("numbers") or [])
    draw_number_line = f"{telegram_format_utc8_hhmm_ms(draw_time_ms)} 开奖号码：{draw_numbers or '--'}"
    summaries = telegram_cumulative_candidate_summaries(game_config, config, records)
    policy = telegram_staking_policy(config)
    result_lines: list[str] = []
    summary_lines: list[str] = []
    for index, item in enumerate(slots, start=1):
        record = item["record"]
        result = record.get("result") if isinstance(record.get("result"), dict) else {}
        summary = summaries.get(item["key"], {})
        current_won = summary.get("currentWon")
        if current_won is None:
            current_won = record.get("status") == "won"
        status = "命中" if current_won else "未中"
        stake = parse_float(summary.get("currentStake"), telegram_record_stake_amount(record, config))
        profit = parse_float(summary.get("currentProfit"), telegram_record_profit_amount(record, config))
        matched_numbers = summary.get("currentMatchedNumbers") or result.get("matchedNumbers") or []
        summary_numbers = summary.get("numbers") or telegram_record_numbers_text(record)
        summary_periods = parse_int(summary.get("periods"), 0)
        summary_wins = parse_int(summary.get("wins"), 0)
        summary_stake = parse_float(summary.get("stake"), 0)
        summary_payout = parse_float(summary.get("payout"), 0)
        summary_profit = parse_float(summary.get("profit"), 0)
        summary_roi = parse_float(summary.get("roi"), 0)
        result_lines.append(
            "\n".join(
                [
                    f"候选{index}  {telegram_html_text(item['slotLabel'])}  {telegram_html_code(telegram_record_numbers_text(record))}",
                    (
                        f"结果 {telegram_html_code(status)}  "
                        f"投入 {telegram_html_code(f'{stake:g}')}  "
                        f"利润 {telegram_html_code(telegram_signed_amount(profit))}"
                    ),
                    f"命中 {telegram_html_code('-'.join(str(number) for number in matched_numbers) or '--')}",
                ]
            )
        )
        summary_lines.append(
            "\n".join(
                [
                    f"候选{index}  {telegram_html_text(item['slotLabel'])}  {telegram_html_code(summary_numbers)}",
                    (
                        f"{telegram_html_code(f'{summary_periods}期')}  "
                        f"命中 {telegram_html_code(str(summary_wins))}  "
                        f"累投 {telegram_html_code(f'{summary_stake:g}')}  "
                        f"中奖 {telegram_html_code(f'{summary_payout:g}')}"
                    ),
                    (
                        f"利润 {telegram_html_code(telegram_signed_amount(summary_profit))}  "
                        f"ROI {telegram_html_code(f'{summary_roi * 100:+.2f}%')}"
                    ),
                ]
            )
        )
    period_stake = sum(parse_float((summaries.get(item["key"]) or {}).get("currentStake"), 0) for item in slots)
    period_profit = sum(parse_float((summaries.get(item["key"]) or {}).get("currentProfit"), 0) for item in slots)
    start_text = next((str(summary.get("startText") or "") for summary in summaries.values()), "全部记录")
    end_text = next((str(summary.get("endText") or "") for summary in summaries.values()), "")
    policy_line = (
        f"{policy.get('label')} | {parse_int(policy.get('stepMisses'), 0)}期不中+1元"
        f" | 上限{parse_float(policy.get('maxStake'), 0):g}元"
    )
    lines = [
        f"<b>开奖结果 · {telegram_html_text(game_config['shortName'])}</b>",
        f"首期 {telegram_html_code(start_text or '--')}",
        f"当前 {telegram_html_code(end_text or telegram_format_utc8_ms(telegram_records_target_ms(records)))}",
        f"范围 {telegram_html_code('含当前开奖')}",
        f"候选 {telegram_html_code('当期推送')}",
        f"档位 {telegram_html_code(policy_line)}",
        "",
        "<b>开奖号码</b>",
        telegram_html_code(draw_number_line),
        "",
        "<b>本期结算</b>",
        "\n\n".join(result_lines),
        f"\n本期合计  投入 {telegram_html_code(f'{period_stake:g}')}  利润 {telegram_html_code(telegram_signed_amount(period_profit))}",
        "",
        "<b>候选独立累计</b>",
        "\n\n".join(summary_lines),
    ]
    return "\n".join(lines).strip()


def telegram_plan_batch_key(game_key: str, records: list[dict[str, Any]]) -> str:
    first = records[0] if records else {}
    return f"{game_key}:{first.get('methodVersion') or ''}:{parse_int(first.get('targetDrawTimeMs'), 0)}"


def telegram_send_latest_plan(game_config: dict[str, Any], config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    pending = load_prediction_tracking_for_game(
        game_config["key"],
        status_filter="pending",
        panel=PREDICTION_PANEL_M,
        limit=20,
    )
    pending = [
        record
        for record in pending
        if prediction_tracking_record_source_ready(record, game_config)
    ]
    if not pending:
        return {"sent": False, "reason": "no_pending"}
    latest_target = max(parse_int(record.get("targetDrawTimeMs"), 0) for record in pending)
    records = [
        record for record in pending
        if parse_int(record.get("targetDrawTimeMs"), 0) == latest_target
    ]
    key = telegram_plan_batch_key(game_config["key"], records)
    if telegram_state_contains(state, "sentPlanBatches", key):
        return {"sent": False, "reason": "already_sent", "key": key}
    message = telegram_plan_message(game_config, records, config)
    response = telegram_send_message(
        config,
        message,
        parse_mode="HTML",
        reply_markup=telegram_message_buttons(game_config, config),
    )
    telegram_state_add(state, "sentPlanBatches", key)
    return {"sent": True, "key": key, "messageId": response.get("result", {}).get("message_id")}


def telegram_send_recent_results(game_config: dict[str, Any], config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    records = load_prediction_tracking_for_game(
        game_config["key"],
        status_filter="all",
        panel=PREDICTION_PANEL_M,
        limit=80,
    )
    now_ms = int(time.time() * 1000)
    recent_cutoff = now_ms - 6 * 60 * 60 * 1000
    grouped: dict[int, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("status") not in {"won", "lost"}:
            continue
        target_ms = parse_int(record.get("targetDrawTimeMs"), 0)
        if target_ms < recent_cutoff:
            continue
        grouped.setdefault(target_ms, []).append(record)
    if not grouped:
        return {"sent": 0, "reason": "no_recent_settled"}
    target_ms = max(grouped)
    target_records = grouped[target_ms]
    key = f"{game_config['key']}:{target_ms}"
    if telegram_state_contains(state, "sentResultBatches", key):
        return {"sent": 0, "reason": "already_sent", "key": key}
    response = telegram_send_message(
        config,
        telegram_result_message(game_config, target_records, config),
        parse_mode="HTML",
        reply_markup=telegram_message_buttons(game_config, config),
    )
    telegram_state_add(state, "sentResultBatches", key)
    return {"sent": 1, "key": key, "messageId": response.get("result", {}).get("message_id")}


def telegram_check_profit_milestone(game_config: dict[str, Any], config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    if not config.get("pinProfitMilestones", True):
        return {"pinned": False, "reason": "disabled"}
    step = parse_float(config.get("profitPinStep"), 50)
    summary = prediction_tracking_summary_for_config(game_config, panel=PREDICTION_PANEL_M)
    profit = parse_float(summary.get("profitTotal"), 0)
    if profit < step:
        return {"pinned": False, "profit": profit}
    milestone = int(profit // step) * int(step)
    key = f"{game_config['key']}:{milestone}"
    pinned = state.setdefault("pinnedMilestones", {})
    if key in pinned:
        return {"pinned": False, "reason": "already_pinned", "profit": profit, "milestone": milestone}
    message = (
        f"📌 利润里程碑\n"
        f"{game_config['shortName']} C计划累计利润达到 +{milestone} 元\n"
        f"当前累计：{profit:+g} 元\n"
        f"统计：命中 {summary.get('won', 0)} / 已结算 {summary.get('settled', 0)}"
    )
    response = telegram_send_message(config, message)
    message_id = parse_int(response.get("result", {}).get("message_id"), 0)
    if message_id:
        telegram_pin_message(config, message_id)
    pinned[key] = {"messageId": message_id, "profit": profit, "pinnedAt": utc_now_iso()}
    return {"pinned": True, "profit": profit, "milestone": milestone, "messageId": message_id}


def telegram_daily_summary_records(game_config: dict[str, Any], date_key: str) -> list[dict[str, Any]]:
    tz = ZoneInfo(STAKING_BACKTEST_DEFAULT_TIMEZONE)
    records = load_prediction_tracking_for_game(
        game_config["key"],
        status_filter="all",
        panel=PREDICTION_PANEL_M,
        limit=500,
    )
    result = []
    for record in records:
        if record.get("status") not in {"won", "lost"}:
            continue
        target_ms = parse_int(record.get("targetDrawTimeMs"), 0)
        if target_ms <= 0:
            continue
        local_date = datetime.fromtimestamp(target_ms / 1000, tz=UTC).astimezone(tz).date().isoformat()
        if local_date == date_key:
            result.append(record)
    return result


def telegram_check_daily_summary(game_config: dict[str, Any], config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    if not config.get("pinDailySummary", True):
        return {"sent": False, "reason": "disabled"}
    tz = ZoneInfo(STAKING_BACKTEST_DEFAULT_TIMEZONE)
    now = datetime.now(tz=tz)
    if (now.hour, now.minute) < (parse_int(config.get("dailySummaryHour"), 23), parse_int(config.get("dailySummaryMinute"), 55)):
        return {"sent": False, "reason": "not_time"}
    date_key = now.date().isoformat()
    state_key = f"{game_config['key']}:{date_key}"
    daily = state.setdefault("dailySummaries", {})
    if state_key in daily:
        return {"sent": False, "reason": "already_sent", "date": date_key}
    records = telegram_daily_summary_records(game_config, date_key)
    won = sum(1 for record in records if record.get("status") == "won")
    lost = sum(1 for record in records if record.get("status") == "lost")
    profit = sum(parse_float(record.get("profit"), 0) for record in records)
    stake = sum(parse_float(record.get("stake"), 1) for record in records)
    roi = profit / stake if stake > 0 else 0
    message = (
        f"📌 日结总结 · {game_config['shortName']}\n"
        f"日期：{date_key}\n"
        f"C计划结算：{won + lost} 笔\n"
        f"命中 / 未中：{won} / {lost}\n"
        f"投入：{stake:g} 元\n"
        f"利润：{profit:+g} 元\n"
        f"ROI：{roi * 100:+.2f}%"
    )
    response = telegram_send_message(config, message)
    message_id = parse_int(response.get("result", {}).get("message_id"), 0)
    if message_id:
        telegram_pin_message(config, message_id)
    daily[state_key] = {"messageId": message_id, "profit": profit, "sentAt": utc_now_iso()}
    return {"sent": True, "date": date_key, "profit": profit, "messageId": message_id}


def telegram_notify_game(game_config: dict[str, Any]) -> dict[str, Any]:
    config = load_telegram_config()
    if not telegram_game_enabled(config, game_config["key"]):
        return {"enabled": False}
    state = load_telegram_state()
    result: dict[str, Any] = {"enabled": True, "game": game_config["key"], "errors": []}
    try:
        result["plan"] = telegram_send_latest_plan(game_config, config, state)
    except Exception as exc:
        result["errors"].append({"stage": "plan", "error": str(exc)})
    try:
        result["results"] = telegram_send_recent_results(game_config, config, state)
    except Exception as exc:
        result["errors"].append({"stage": "results", "error": str(exc)})
    try:
        result["milestone"] = telegram_check_profit_milestone(game_config, config, state)
    except Exception as exc:
        result["errors"].append({"stage": "milestone", "error": str(exc)})
    try:
        result["dailySummary"] = telegram_check_daily_summary(game_config, config, state)
    except Exception as exc:
        result["errors"].append({"stage": "dailySummary", "error": str(exc)})
    if result["errors"]:
        state.setdefault("lastErrors", []).extend(
            [{"game": game_config["key"], **error, "at": utc_now_iso()} for error in result["errors"]]
        )
    write_telegram_state(state)
    return result


def telegram_game_switch_enabled(config: dict[str, Any], game_key: str) -> bool:
    games = config.get("games") if isinstance(config.get("games"), dict) else {}
    item = games.get(game_key) if isinstance(games.get(game_key), dict) else {}
    return bool(item.get("enabled"))


def telegram_admin_allowed(config: dict[str, Any], user: dict[str, Any] | None) -> bool:
    user_id = str((user or {}).get("id") or "").strip()
    return bool(user_id and user_id in {str(item) for item in config.get("adminIds") or []})


def telegram_game_label(game_key: str) -> str:
    game_config = LOTTERY_GAMES.get(game_key) or {}
    return str(game_config.get("shortName") or game_key)


def telegram_status_text(config: dict[str, Any]) -> str:
    lines = [
        "CPGAME Telegram 控制台",
        f"频道：{config.get('channelChatId') or '--'}",
        f"总推送：{'开启' if config.get('enabled') else '关闭'}",
        f"全部彩种：{'开启' if config.get('allGames') else '关闭'}",
        "",
        "彩种结果：",
    ]
    for key, game_config in LOTTERY_GAMES.items():
        if not supports_predictions(game_config):
            continue
        lines.append(f"{'✅' if telegram_game_switch_enabled(config, key) else '⛔'} {telegram_game_label(key)}")
    return "\n".join(lines)


def telegram_games_text(config: dict[str, Any]) -> str:
    lines = [
        "频道彩种结果开关",
        f"总推送：{'开启' if config.get('enabled') else '关闭'}",
        f"全部彩种模式：{'开启' if config.get('allGames') else '关闭'}",
        "",
        "点击按钮切换要发送结果的彩种。",
    ]
    return "\n".join(lines)


def telegram_message_settings_text(config: dict[str, Any]) -> str:
    lines = [
        "频道按钮链接编辑",
        f"频道：{config.get('channelChatId') or '--'}",
        f"投注按钮：{config.get('inviteLink') or '--'}",
        "",
        "开奖按钮：",
    ]
    for key, game_config in LOTTERY_GAMES.items():
        if not supports_predictions(game_config):
            continue
        link = telegram_draw_link_for_game(game_config, config)
        lines.append(f"{telegram_game_label(key)}：{link or '未匹配，消息不附链接'}")
    lines.extend(["", "编辑地址请在私聊机器人中操作。"])
    return "\n".join(lines)


def telegram_main_keyboard(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": f"频道总控：{'开启' if config.get('enabled') else '关闭'}", "callback_data": "tg:toggle_total"}],
            [{"text": "彩种结果开关", "callback_data": "tg:games"}],
            [{"text": "编辑按钮链接", "callback_data": "tg:messages"}],
            [
                {"text": "测试发送", "callback_data": "tg:test"},
                {"text": "立即检查", "callback_data": "tg:notify"},
            ],
            [{"text": "刷新状态", "callback_data": "tg:main"}],
        ]
    }


def telegram_games_keyboard(config: dict[str, Any]) -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = [
        [{"text": f"总推送：{'开启' if config.get('enabled') else '关闭'}", "callback_data": "tg:toggle_total"}],
        [{"text": f"全部彩种模式：{'开启' if config.get('allGames') else '关闭'}", "callback_data": "tg:toggle_all_games"}],
    ]
    for key, game_config in LOTTERY_GAMES.items():
        if not supports_predictions(game_config):
            continue
        rows.append(
            [
                {
                    "text": f"{'✅' if telegram_game_switch_enabled(config, key) else '⛔'} {telegram_game_label(key)}",
                    "callback_data": f"tg:toggle_game:{key}",
                }
            ]
        )
    rows.append([{"text": "返回总控", "callback_data": "tg:main"}])
    return {"inline_keyboard": rows}


def telegram_message_settings_keyboard(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "修改频道", "callback_data": "tg:edit_channel"}],
            [{"text": "修改投注按钮", "callback_data": "tg:edit_invite"}],
            [{"text": "修改开奖按钮", "callback_data": "tg:edit_draw_menu"}],
            [{"text": "返回总控", "callback_data": "tg:main"}],
        ]
    }


def telegram_draw_edit_keyboard(config: dict[str, Any]) -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    for key, game_config in LOTTERY_GAMES.items():
        if supports_predictions(game_config):
            rows.append([{"text": telegram_game_label(key), "callback_data": f"tg:edit_draw:{key}"}])
    rows.append([{"text": "返回消息设置", "callback_data": "tg:messages"}])
    return {"inline_keyboard": rows}


def telegram_set_pending_edit(state: dict[str, Any], user_id: str, field: str) -> None:
    pending = state.setdefault("pendingBotEdits", {})
    pending[str(user_id)] = {"field": field, "at": utc_now_iso()}


def telegram_pop_pending_edit(state: dict[str, Any], user_id: str) -> dict[str, Any] | None:
    pending = state.setdefault("pendingBotEdits", {})
    item = pending.pop(str(user_id), None)
    return item if isinstance(item, dict) else None


def telegram_apply_pending_edit(config: dict[str, Any], field: str, value: str) -> str:
    text = value.strip()
    if text.lower() in {"clear", "reset", "清空"}:
        text = ""
    if field == "channelChatId":
        if not text:
            raise ValueError("频道不能为空")
        config["channelChatId"] = text
        return f"频道已更新为：{text}"
    if field == "inviteLink":
        config["inviteLink"] = text
        return "投注地址已更新"
    if field.startswith("drawLink:"):
        game_key = field.split(":", 1)[1]
        if game_key not in LOTTERY_GAMES:
            raise ValueError("未知彩种")
        links = config.setdefault("drawLinksByGame", {})
        links[game_key] = text
        return f"{telegram_game_label(game_key)} 开奖地址已更新"
    raise ValueError("未知编辑字段")


def telegram_command_name(text: str) -> tuple[str, str]:
    stripped = text.strip()
    if not stripped.startswith("/"):
        return "", stripped
    parts = stripped.split(maxsplit=1)
    command = parts[0].split("@", 1)[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    return command, arg


def telegram_get_updates(config: dict[str, Any], offset: int, timeout: int = 20) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "timeout": timeout,
        "allowed_updates": ["message", "channel_post", "callback_query"],
    }
    if offset > 0:
        payload["offset"] = offset
    return telegram_api_request("getUpdates", payload, config, timeout=timeout + 15)


def telegram_send_control_menu(config: dict[str, Any], chat_id: Any, *, channel_mode: bool = False) -> dict[str, Any]:
    if channel_mode:
        return telegram_send_message(
            config,
            telegram_games_text(config),
            chat_id=chat_id,
            reply_markup=telegram_games_keyboard(config),
        )
    return telegram_send_message(
        config,
        telegram_status_text(config),
        chat_id=chat_id,
        reply_markup=telegram_main_keyboard(config),
    )


def telegram_edit_control_menu(
    config: dict[str, Any],
    chat_id: Any,
    message_id: int,
    text: str,
    keyboard: dict[str, Any],
) -> None:
    telegram_edit_message_text(config, chat_id, message_id, text, reply_markup=keyboard)


def telegram_handle_callback(callback: dict[str, Any], config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    callback_id = str(callback.get("id") or "")
    user = callback.get("from") if isinstance(callback.get("from"), dict) else {}
    if not telegram_admin_allowed(config, user):
        if callback_id:
            telegram_answer_callback_query(config, callback_id, "无权限")
        return {"handled": False, "reason": "not_admin"}
    message = callback.get("message") if isinstance(callback.get("message"), dict) else {}
    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    chat_id = chat.get("id")
    message_id = parse_int(message.get("message_id"), 0)
    data = str(callback.get("data") or "")
    notice = "已更新"

    if data == "tg:toggle_total":
        previous_enabled = bool(config.get("enabled"))
        config["enabled"] = not previous_enabled
        if bool(config.get("enabled")) and not previous_enabled:
            config["enabledAt"] = utc_now_iso()
        write_telegram_config(config)
        text, keyboard = telegram_status_text(config), telegram_main_keyboard(config)
    elif data == "tg:toggle_all_games":
        config["allGames"] = not bool(config.get("allGames"))
        write_telegram_config(config)
        text, keyboard = telegram_games_text(config), telegram_games_keyboard(config)
    elif data.startswith("tg:toggle_game:"):
        game_key = data.split(":", 2)[2]
        if game_key in LOTTERY_GAMES:
            item = config.setdefault("games", {}).setdefault(game_key, {})
            item["enabled"] = not bool(item.get("enabled"))
            write_telegram_config(config)
        text, keyboard = telegram_games_text(config), telegram_games_keyboard(config)
    elif data == "tg:games":
        text, keyboard = telegram_games_text(config), telegram_games_keyboard(config)
        notice = ""
    elif data == "tg:messages":
        text, keyboard = telegram_message_settings_text(config), telegram_message_settings_keyboard(config)
        notice = ""
    elif data == "tg:edit_draw_menu":
        text, keyboard = "选择要修改开奖地址的彩种。", telegram_draw_edit_keyboard(config)
        notice = ""
    elif data in {"tg:edit_channel", "tg:edit_invite"} or data.startswith("tg:edit_draw:"):
        chat_type = str(chat.get("type") or "")
        if chat_type != "private":
            telegram_answer_callback_query(config, callback_id, "请私聊机器人编辑频道消息")
            return {"handled": True, "reason": "private_required"}
        user_id = str(user.get("id") or "")
        if data == "tg:edit_channel":
            telegram_set_pending_edit(state, user_id, "channelChatId")
            prompt = "请直接发送新的频道用户名或 chat_id，例如 @Keno100x。"
        elif data == "tg:edit_invite":
            telegram_set_pending_edit(state, user_id, "inviteLink")
            prompt = "请直接发送新的投注按钮链接。发送 清空 可以清掉。"
        else:
            game_key = data.split(":", 2)[2]
            telegram_set_pending_edit(state, user_id, f"drawLink:{game_key}")
            prompt = f"请直接发送 {telegram_game_label(game_key)} 的开奖按钮链接。发送 清空 可以清掉。"
        write_telegram_state(state)
        telegram_send_message(config, prompt, chat_id=chat_id)
        telegram_answer_callback_query(config, callback_id, "等待输入")
        return {"handled": True, "pending": True}
    elif data == "tg:test":
        message = "<b>CPGAME 机器人已连接</b>\n按钮链接已启用。"
        response = telegram_send_message(
            config,
            message,
            parse_mode="HTML",
            reply_markup=telegram_message_buttons(LOTTERY_GAMES[DEFAULT_GAME_KEY], config),
        )
        notice = f"测试已发送 #{response.get('result', {}).get('message_id')}"
        text, keyboard = telegram_status_text(config), telegram_main_keyboard(config)
    elif data == "tg:notify":
        results = [
            telegram_notify_game(LOTTERY_GAMES[key])
            for key in LOTTERY_GAMES
            if telegram_game_enabled(config, key)
        ]
        notice = f"已检查 {len(results)} 个彩种"
        text, keyboard = telegram_status_text(load_telegram_config()), telegram_main_keyboard(load_telegram_config())
    else:
        text, keyboard = telegram_status_text(config), telegram_main_keyboard(config)
        notice = ""

    if callback_id:
        telegram_answer_callback_query(config, callback_id, notice)
    if chat_id not in (None, "") and message_id:
        telegram_edit_control_menu(config, chat_id, message_id, text, keyboard)
    return {"handled": True, "action": data}


def telegram_handle_message(update: dict[str, Any], config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    message = update.get("message") if isinstance(update.get("message"), dict) else None
    is_channel_post = False
    if message is None and isinstance(update.get("channel_post"), dict):
        message = update.get("channel_post")
        is_channel_post = True
    if not isinstance(message, dict):
        return {"handled": False, "reason": "no_message"}

    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    chat_id = chat.get("id")
    chat_type = str(chat.get("type") or "")
    user = message.get("from") if isinstance(message.get("from"), dict) else {}
    text = str(message.get("text") or "").strip()
    if not text:
        return {"handled": False, "reason": "no_text"}
    command, arg = telegram_command_name(text)
    channel_mode = is_channel_post or chat_type in {"channel", "supergroup", "group"}

    if not channel_mode and not telegram_admin_allowed(config, user):
        if command:
            telegram_send_message(config, "无权限", chat_id=chat_id)
        return {"handled": False, "reason": "not_admin"}

    if not command and not channel_mode:
        user_id = str(user.get("id") or "")
        pending = telegram_pop_pending_edit(state, user_id)
        if pending:
            try:
                message_text = telegram_apply_pending_edit(config, str(pending.get("field") or ""), text)
                write_telegram_config(config)
                write_telegram_state(state)
                telegram_send_message(config, message_text, chat_id=chat_id)
                telegram_send_control_menu(load_telegram_config(), chat_id)
                return {"handled": True, "pendingEdit": True}
            except Exception as exc:
                write_telegram_state(state)
                telegram_send_message(config, f"更新失败：{exc}", chat_id=chat_id)
                return {"handled": False, "error": str(exc)}

    if command in {"/start", "/menu"}:
        telegram_send_control_menu(config, chat_id, channel_mode=channel_mode)
        return {"handled": True, "command": command}
    if command == "/status":
        telegram_send_message(config, telegram_status_text(config), chat_id=chat_id)
        return {"handled": True, "command": command}
    if command == "/set_invite" and arg and not channel_mode:
        config["inviteLink"] = arg
        write_telegram_config(config)
        telegram_send_message(config, "投注地址已更新", chat_id=chat_id)
        return {"handled": True, "command": command}
    if command == "/set_channel" and arg and not channel_mode:
        config["channelChatId"] = arg
        write_telegram_config(config)
        telegram_send_message(config, f"频道已更新为：{arg}", chat_id=chat_id)
        return {"handled": True, "command": command}
    if command == "/set_draw" and arg and not channel_mode:
        parts = arg.split(maxsplit=1)
        if len(parts) == 2 and parts[0] in LOTTERY_GAMES:
            config.setdefault("drawLinksByGame", {})[parts[0]] = parts[1].strip()
            write_telegram_config(config)
            telegram_send_message(config, f"{telegram_game_label(parts[0])} 开奖地址已更新", chat_id=chat_id)
            return {"handled": True, "command": command}
    return {"handled": False, "reason": "ignored"}


def telegram_process_update(update: dict[str, Any], config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    if isinstance(update.get("callback_query"), dict):
        return telegram_handle_callback(update["callback_query"], config, state)
    return telegram_handle_message(update, config, state)


def telegram_process_updates_once(timeout: int = 1) -> dict[str, Any]:
    config = load_telegram_config()
    if not telegram_bot_token(config):
        return {"ok": False, "reason": "token_missing"}
    state = load_telegram_state()
    offset = parse_int(state.get("telegramUpdateOffset"), 0)
    response = telegram_get_updates(config, offset=offset, timeout=timeout)
    updates = response.get("result") if isinstance(response.get("result"), list) else []
    handled = 0
    errors: list[dict[str, Any]] = []
    for update in updates:
        update_id = parse_int(update.get("update_id"), 0)
        if update_id:
            state["telegramUpdateOffset"] = max(parse_int(state.get("telegramUpdateOffset"), 0), update_id + 1)
        try:
            result = telegram_process_update(update, load_telegram_config(), state)
            if result.get("handled"):
                handled += 1
        except Exception as exc:
            errors.append({"stage": "bot_update", "error": str(exc), "at": utc_now_iso()})
    if errors:
        state.setdefault("lastErrors", []).extend(errors)
    write_telegram_state(state)
    return {"ok": True, "updates": len(updates), "handled": handled, "errors": errors}


def telegram_bot_worker() -> None:
    commands_configured = False
    while not TELEGRAM_BOT_STOP.is_set():
        config = load_telegram_config()
        if not telegram_bot_token(config) or not config.get("botPollingEnabled", True):
            commands_configured = False
            if TELEGRAM_BOT_STOP.wait(10):
                break
            continue
        try:
            if not commands_configured:
                telegram_set_bot_commands(config)
                commands_configured = True
            telegram_process_updates_once(timeout=20)
        except Exception as exc:
            if "timed out" in str(exc).lower():
                continue
            state = load_telegram_state()
            state.setdefault("lastErrors", []).append({"stage": "bot_worker", "error": str(exc), "at": utc_now_iso()})
            write_telegram_state(state)
            if TELEGRAM_BOT_STOP.wait(5):
                break


def start_telegram_bot_polling() -> None:
    global TELEGRAM_BOT_THREAD
    if TELEGRAM_BOT_THREAD is not None and TELEGRAM_BOT_THREAD.is_alive():
        return
    TELEGRAM_BOT_STOP.clear()
    TELEGRAM_BOT_THREAD = threading.Thread(target=telegram_bot_worker, daemon=True)
    TELEGRAM_BOT_THREAD.start()


def stop_telegram_bot_polling() -> None:
    TELEGRAM_BOT_STOP.set()


def telegram_status_payload() -> dict[str, Any]:
    config = load_telegram_config()
    state = load_telegram_state()
    return {
        "ok": True,
        "generatedAt": utc_now_iso(),
        "config": telegram_public_config(config),
        "configFile": file_info(DEFAULT_TELEGRAM_CONFIG),
        "stateFile": file_info(DEFAULT_TELEGRAM_STATE),
        "state": {
            "sentPlanBatches": len(state.get("sentPlanBatches") or []),
            "sentResultBatches": len(state.get("sentResultBatches") or []),
            "pinnedMilestones": len(state.get("pinnedMilestones") or {}),
            "dailySummaries": len(state.get("dailySummaries") or {}),
            "telegramUpdateOffset": parse_int(state.get("telegramUpdateOffset"), 0),
            "pendingBotEdits": len(state.get("pendingBotEdits") or {}),
            "lastErrors": (state.get("lastErrors") or [])[-5:],
        },
    }


def telegram_request(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip().lower()
    config = load_telegram_config()
    if action == "save":
        update = payload.get("config") if isinstance(payload.get("config"), dict) else {}
        previous_enabled = bool(config.get("enabled"))
        config.update({key: value for key, value in update.items() if key not in {"botToken", "games"}})
        if isinstance(update.get("games"), dict):
            for key, value in update["games"].items():
                if key in config["games"] and isinstance(value, dict):
                    config["games"][key].update(value)
        if bool(config.get("enabled")) and not previous_enabled:
            config["enabledAt"] = utc_now_iso()
        write_telegram_config(config)
        return telegram_status_payload()
    if action == "test":
        message = "<b>CPGAME 机器人已连接</b>\n按钮链接已启用。"
        response = telegram_send_message(
            config,
            message,
            parse_mode="HTML",
            reply_markup=telegram_message_buttons(LOTTERY_GAMES[DEFAULT_GAME_KEY], config),
        )
        return {"ok": True, "messageId": response.get("result", {}).get("message_id"), "status": telegram_status_payload()}
    if action in {"setupmenu", "setup_menu"}:
        response = telegram_set_bot_commands(config)
        return {"ok": True, "result": response.get("result"), "status": telegram_status_payload()}
    if action in {"sendmenu", "send_menu"}:
        chat_id = payload.get("chatId") or (config.get("adminIds") or [""])[0]
        response = telegram_send_control_menu(config, chat_id, channel_mode=False)
        return {"ok": True, "messageId": response.get("result", {}).get("message_id"), "status": telegram_status_payload()}
    if action == "poll":
        return {"ok": True, "poll": telegram_process_updates_once(timeout=1), "status": telegram_status_payload()}
    if action == "notifynow":
        results = [
            telegram_notify_game(LOTTERY_GAMES[key])
            for key in LOTTERY_GAMES
            if telegram_game_enabled(config, key)
        ]
        return {"ok": True, "results": results, "status": telegram_status_payload()}
    raise ValueError("未知 Telegram 操作")


def default_prediction_auto_config() -> dict[str, Any]:
    return {
        "enabled": False,
        "pollSeconds": 30,
        "catchupPollSeconds": PREDICTION_AUTO_SINGLE_GAME_CATCHUP_SECONDS,
        "sync": True,
        "maxPages": 2,
        "pageSize": 100,
        "sleep": 0.05,
        "timeout": 5,
        "retries": 1,
        "retrySleep": 0.5,
        "skipSupplement": False,
        "autoGameSelectionConfigured": False,
        "games": {
            key: {"enabled": key == "poland_keno_20_70" and supports_predictions(config)}
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
            if not config.get("autoGameSelectionConfigured"):
                for key in config["games"]:
                    config["games"][key]["enabled"] = key == "poland_keno_20_70"
    for key, game_config in LOTTERY_GAMES.items():
        if not supports_predictions(game_config):
            config["games"].setdefault(key, {})["enabled"] = False
    config["pollSeconds"] = max(15, min(parse_int(config.get("pollSeconds"), 30), 3600))
    config["catchupPollSeconds"] = max(
        PREDICTION_AUTO_SINGLE_GAME_CATCHUP_SECONDS,
        min(
            parse_int(config.get("catchupPollSeconds"), PREDICTION_AUTO_SINGLE_GAME_CATCHUP_SECONDS),
            PREDICTION_AUTO_CATCHUP_MAX_SECONDS,
        ),
    )
    config["maxPages"] = max(1, min(parse_int(config.get("maxPages"), 2), 20))
    config["pageSize"] = max(10, min(parse_int(config.get("pageSize"), 100), 100))
    config["sleep"] = max(0, min(parse_float(config.get("sleep"), 0.05), 5))
    config["timeout"] = max(2, min(parse_float(config.get("timeout"), 6), 60))
    config["retries"] = max(0, min(parse_int(config.get("retries"), 0), 4))
    config["retrySleep"] = max(0, min(parse_float(config.get("retrySleep"), 0.5), 10))
    config["skipSupplement"] = bool(config.get("skipSupplement", False))
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
    effective_poll_seconds = prediction_auto_effective_poll_seconds(config)
    effective_catchup_seconds = prediction_auto_effective_catchup_seconds(config)
    status.update(
        {
            "ok": True,
            "enabled": bool(config.get("enabled")),
            "running": thread_alive,
            "config": config,
            "effectivePollSeconds": effective_poll_seconds,
            "effectiveCatchupPollSeconds": effective_catchup_seconds,
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


def prediction_auto_effective_catchup_seconds(config: dict[str, Any]) -> int:
    enabled_count = len(prediction_auto_enabled_games(config))
    configured = parse_int(
        config.get("catchupPollSeconds"),
        PREDICTION_AUTO_SINGLE_GAME_CATCHUP_SECONDS,
    )
    if enabled_count <= 1:
        return PREDICTION_AUTO_SINGLE_GAME_CATCHUP_SECONDS
    return max(
        PREDICTION_AUTO_MULTI_GAME_CATCHUP_SECONDS,
        min(configured, PREDICTION_AUTO_CATCHUP_MAX_SECONDS),
    )


def prediction_auto_effective_poll_seconds(config: dict[str, Any]) -> int:
    configured = parse_int(config.get("pollSeconds"), 30)
    return max(15, configured)


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


def prediction_tracking_summary_for_config(
    config: dict[str, Any],
    *,
    panel: str | None = None,
) -> dict[str, Any]:
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"], panel=panel)
    return prediction_tracking_summary(records)


def prediction_tracking_panel_summaries_for_config(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    with PREDICTION_TRACKING_LOCK:
        records = load_prediction_tracking_for_game(config["key"])
    return {
        panel: prediction_tracking_summary(prediction_records_for_panel(records, panel))
        for panel in [
            PREDICTION_PANEL_DEFAULT,
            PREDICTION_PANEL_B,
            PREDICTION_PANEL_M,
            PREDICTION_PANEL_D,
        ]
    }


def run_prediction_auto_once(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for key in prediction_auto_enabled_games(config):
        try:
            game_config = LOTTERY_GAMES[key]
            refresh_result: dict[str, Any] | None = None
            if config.get("sync", True):
                refresh_result = refresh_official_history_only(
                    game_config,
                    timeout=parse_float(config.get("timeout"), 6),
                )
            new_rows = parse_int((refresh_result or {}).get("newRows"), 0)
            settled_from_refresh = parse_int((refresh_result or {}).get("settledPredictions"), 0)
            marker = prediction_auto_history_marker(game_config)
            previous_marker = PREDICTION_AUTO_HISTORY_MARKERS.get(key)
            with DATA_LOCK:
                tracking_rows = load_history_rows(game_history_path(game_config), game_config)
            with PREDICTION_TRACKING_LOCK:
                tracking_records = load_prediction_tracking_for_game(key)
            tracking_wait = prediction_tracking_auto_sync_status(tracking_records, tracking_rows, game_config)
            history_wait = prediction_history_waiting_for_latest_draw(tracking_rows, game_config)
            refresh_status = str((refresh_result or {}).get("meta", {}).get("status") or "")
            refresh_error = str((refresh_result or {}).get("meta", {}).get("error") or "")
            waiting_for_draw = bool(
                config.get("sync", True)
                and (
                    tracking_wait.get("needsSync")
                    or history_wait.get("waiting")
                    or (refresh_error and refresh_status == "error")
                )
            )
            prediction_waiting_for_target = False
            should_generate_prediction = (
                not config.get("sync", True)
                or previous_marker is None
                or previous_marker != marker
                or new_rows > 0
                or settled_from_refresh > 0
            ) and not waiting_for_draw
            skipped_prediction = False
            if should_generate_prediction:
                prediction_a = predictions_payload({"game": [key], "panel": [PREDICTION_PANEL_DEFAULT]})
                prediction_b = predictions_payload({"game": [key], "panel": [PREDICTION_PANEL_B]})
                prediction_m = predictions_payload({"game": [key], "panel": [PREDICTION_PANEL_M]})
                prediction_d = predictions_payload({"game": [key], "panel": [PREDICTION_PANEL_D]})
                tracking_a = prediction_a.get("predictionTracking") or {}
                tracking_b = prediction_b.get("predictionTracking") or {}
                tracking_m = prediction_m.get("predictionTracking") or {}
                tracking_d = prediction_d.get("predictionTracking") or {}
                panel_summaries = prediction_tracking_panel_summaries_for_config(game_config)
                tracking = {
                    "settledNow": parse_int(tracking_a.get("settledNow"), 0)
                    + parse_int(tracking_b.get("settledNow"), 0)
                    + parse_int(tracking_m.get("settledNow"), 0)
                    + parse_int(tracking_d.get("settledNow"), 0),
                    "createdNow": parse_int(tracking_a.get("createdNow"), 0)
                    + parse_int(tracking_b.get("createdNow"), 0)
                    + parse_int(tracking_m.get("createdNow"), 0)
                    + parse_int(tracking_d.get("createdNow"), 0),
                    "summaryA": panel_summaries.get(PREDICTION_PANEL_DEFAULT) or {},
                    "summaryB": panel_summaries.get(PREDICTION_PANEL_B) or {},
                    "summaryM": panel_summaries.get(PREDICTION_PANEL_M) or {},
                    "summaryD": panel_summaries.get(PREDICTION_PANEL_D) or {},
                }
                prediction_waiting_for_target = any(
                    (
                        isinstance(prediction.get("predictions"), dict)
                        and prediction["predictions"].get("trackingReady") is False
                    )
                    for prediction in [prediction_a, prediction_b, prediction_m, prediction_d]
                )
                if not prediction_waiting_for_target or parse_int(tracking.get("createdNow"), 0) > 0:
                    PREDICTION_AUTO_HISTORY_MARKERS[key] = marker
                prediction_prewarm = schedule_prediction_prewarm(game_config, reason="prediction_auto")
            else:
                panel_summaries = prediction_tracking_panel_summaries_for_config(game_config)
                tracking = {
                    "settledNow": 0,
                    "createdNow": 0,
                    "summaryA": panel_summaries.get(PREDICTION_PANEL_DEFAULT) or {},
                    "summaryB": panel_summaries.get(PREDICTION_PANEL_B) or {},
                    "summaryM": panel_summaries.get(PREDICTION_PANEL_M) or {},
                }
                skipped_prediction = True
                prediction_prewarm = {"scheduled": False, "reason": "prediction_generation_skipped", "game": key}
            tracking_summary_a = tracking.get("summaryA") or {}
            tracking_summary_b = tracking.get("summaryB") or {}
            tracking_summary_m = tracking.get("summaryM") or {}
            tracking_summary_d = tracking.get("summaryD") or {}
            telegram_result = telegram_notify_game(game_config)
            results.append(
                {
                    "game": key,
                    "shortName": game_config["shortName"],
                    "newRows": new_rows,
                    "settledPredictions": settled_from_refresh + parse_int(tracking.get("settledNow"), 0),
                    "createdPredictions": parse_int(tracking.get("createdNow"), 0),
                    "trackingTotal": parse_int(tracking_summary_a.get("total"), 0)
                    + parse_int(tracking_summary_b.get("total"), 0)
                    + parse_int(tracking_summary_m.get("total"), 0)
                    + parse_int(tracking_summary_d.get("total"), 0),
                    "trackingTotalA": parse_int(tracking_summary_a.get("total"), 0),
                    "trackingTotalB": parse_int(tracking_summary_b.get("total"), 0),
                    "trackingTotalM": parse_int(tracking_summary_m.get("total"), 0),
                    "trackingTotalD": parse_int(tracking_summary_d.get("total"), 0),
                    "skippedPrediction": skipped_prediction,
                    "waitingForDraw": waiting_for_draw or prediction_waiting_for_target,
                    "waitingForTarget": prediction_waiting_for_target,
                    "refreshResult": refresh_result,
                    "predictionPrewarm": prediction_prewarm,
                    "trackingWait": tracking_wait if waiting_for_draw else None,
                    "historyWait": history_wait if history_wait.get("waiting") else None,
                    "telegram": telegram_result,
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
        loop_started = time.monotonic()
        results, errors = run_prediction_auto_once(config)
        normal_poll_seconds = prediction_auto_effective_poll_seconds(config)
        has_waiting_draw = any(bool(item.get("waitingForDraw")) for item in results if isinstance(item, dict))
        elapsed_seconds = time.monotonic() - loop_started
        if has_waiting_draw:
            poll_seconds = prediction_auto_effective_catchup_seconds(config)
        else:
            poll_seconds = normal_poll_seconds
        if elapsed_seconds >= poll_seconds:
            poll_seconds = prediction_auto_effective_catchup_seconds(config)
        next_run_ts = time.time() + poll_seconds
        completed_at = utc_now_iso()
        set_prediction_auto_status(
            status="running",
            running=True,
            enabled=True,
            lastRunAt=started_at,
            lastCompletedAt=completed_at,
            nextRunAt=datetime.fromtimestamp(next_run_ts, tz=UTC).isoformat(timespec="seconds"),
            message=(
                f"自动追踪完成：{len(results)} 个彩种，{len(errors)} 个错误；"
                f"{'等待开奖同步，短轮询' if has_waiting_draw else '常规轮询'} {poll_seconds} 秒"
            ),
            results=results,
            errors=errors,
            waitingForDraw=has_waiting_draw,
            pollSeconds=poll_seconds,
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
            config["autoGameSelectionConfigured"] = True
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
            if isinstance(payload["config"].get("games"), dict):
                config["autoGameSelectionConfigured"] = True
                for key, value in payload["config"]["games"].items():
                    if key in config["games"] and isinstance(value, dict):
                        config["games"][key].update(value)
        started_at = utc_now_iso()
        results, errors = run_prediction_auto_once(config)
        completed_at = utc_now_iso()
        set_prediction_auto_status(
            status="stopped",
            running=False,
            lastRunAt=started_at,
            lastCompletedAt=completed_at,
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
            config["autoGameSelectionConfigured"] = True
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
        history_file_changed = False
        bc_fetch_error = ""
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
            "bcFetchFailed": False,
            "bcFetchError": "",
            "oldestFetchedUtc": "",
            "newestExistingUtc": "",
            "stopReason": "",
        }

        if fetch_all:
            existing_signature = dashboard_rows_signature(existing_rows, config)
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
            try:
                written_rows, meta = fetch_bc_keno_history.fetch_history_to_csv(namespace, out)
                rows = load_history_rows(out, config)
                written_rows = len(rows) if rows else written_rows
            except Exception as exc:
                bc_fetch_error = str(exc)
                meta = {"error": bc_fetch_error, "source": "bc.game"}
                rows = list(existing_rows)
                written_rows = len(rows)
            rows_signature = dashboard_rows_signature(rows, config)
            history_file_changed = existing_signature != rows_signature
            if skip_supplement:
                etipos_rows = []
                etipos_meta = {"source": config.get("officialSupplement", ""), "status": "skipped", "newRows": 0}
            else:
                try:
                    etipos_rows, etipos_meta = fetch_official_supplement(config, rows, timeout=timeout)
                except Exception as exc:
                    etipos_rows = []
                    etipos_meta = {"source": config.get("officialSupplement", ""), "error": str(exc), "newRows": 0}
            if etipos_rows:
                merged_rows = merge_history_rows(rows, etipos_rows)
                merged_signature = dashboard_rows_signature(merged_rows, config)
                if rows_signature != merged_signature:
                    rows = merged_rows
                    write_dashboard_rows(out, rows, config)
                    history_file_changed = True
                else:
                    rows = merged_rows
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
                    "historyFileChanged": history_file_changed,
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
                try:
                    page_rows, meta = fetch_rows_page(
                        lottery_id=lottery_id,
                        page=page,
                        page_size=page_size,
                        sleep=sleep,
                        timeout=timeout,
                        retries=retries,
                        retry_sleep=retry_sleep,
                    )
                except Exception as exc:
                    bc_fetch_error = str(exc)
                    meta = {"error": bc_fetch_error, "source": "bc.game", "page": page}
                    stop_reason = "bc_fetch_error"
                    break
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
                    etipos_rows, etipos_meta = fetch_official_supplement(config, merged_before_etipos, timeout=timeout)
                except Exception as exc:
                    etipos_rows = []
                    etipos_meta = {"source": config.get("officialSupplement", ""), "error": str(exc), "newRows": 0}
            rows = merge_history_rows(merged_before_etipos, etipos_rows)
            history_file_changed = dashboard_rows_changed(existing_rows, rows, config)
            if history_file_changed:
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
                    "historyFileChanged": history_file_changed,
                }
            )

        sync_meta["gapAudit"] = gap_audit(rows, config)
        sync_meta["dataIntegrity"] = history_data_integrity(rows, config, meta)
        sync_meta["bcFetchFailed"] = bool(bc_fetch_error)
        sync_meta["bcFetchError"] = bc_fetch_error
        meta = dict(meta)
        meta.update(sync_meta)
        if bc_fetch_error and str(etipos_meta.get("status") or "") != "ok":
            official_error = (
                etipos_meta.get("error")
                or etipos_meta.get("message")
                or etipos_meta.get("status")
                or "official supplement unavailable"
            )
            raise RuntimeError(
                f"BC.Game fetch failed: {bc_fetch_error}; official supplement failed: {official_error}"
            )
        settled_predictions = settle_prediction_tracking_store(rows, config)

    prediction_prewarm = schedule_prediction_prewarm(config, reason="history_refresh")
    return {
        "ok": True,
        "game": game_public_config(config),
        "mode": "full" if fetch_all else "incremental",
        "newRows": new_rows,
        "bcNewRows": len(fetched_rows) if not fetch_all else new_rows,
        "etiposNewRows": etipos_meta.get("newRows", 0),
        "writtenRows": written_rows,
        "historyFileChanged": history_file_changed,
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
        "predictionPrewarm": prediction_prewarm,
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
        if parsed.path == "/api/cde-kill-backtest":
            self.send_error_json(410, "C回测已停用：旧C/D/E 已退出当前 A/B/C计划 决策链")
            return
        if parsed.path == "/api/strategy-signal-audit":
            try:
                self.send_json(strategy_signal_audit_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/predictions":
            try:
                query = parse_qs(parsed.query)
                self.send_json(
                    predictions_payload(
                        query,
                        allow_auto_sync=query_bool(query, "autoSync", False),
                    )
                )
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/staking-backtest":
            try:
                self.send_json(staking_backtest_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/current-staking-backtest":
            try:
                self.send_json(current_staking_backtest_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path in {"/api/fixed-triple-observation", "/api/frequency-observation"}:
            try:
                self.send_json(fixed_triple_observation_payload(parse_qs(parsed.query)))
            except ValueError as exc:
                self.send_error_json(400, str(exc))
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/fixed-triple-omission":
            try:
                self.send_json(fixed_triple_omission_payload(parse_qs(parsed.query)))
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
            self.send_error_json(410, "派生中奖查询已删除")
            return
        if parsed.path == "/api/adjacent-derived-stats":
            self.send_error_json(410, "派生统计已删除")
            return
        if parsed.path == "/api/prediction-auto":
            try:
                self.send_json(prediction_auto_status_payload())
            except Exception as exc:
                self.send_error_json(500, str(exc))
            return
        if parsed.path == "/api/telegram":
            try:
                self.send_json(telegram_status_payload())
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
        if parsed.path == "/api/telegram":
            try:
                self.send_json(telegram_request(self.read_json_body()))
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
    DATA_ROOT.mkdir(exist_ok=True)
    LOG_ROOT.mkdir(exist_ok=True)
    BACKUP_ROOT.mkdir(exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"Keno dashboard running at http://{HOST}:{PORT}")
    print(f"Serving files from {WEB_ROOT}")
    print(f"Data directory: {DATA_ROOT}")
    print(f"Log directory: {LOG_ROOT}")
    print(f"Backup directory: {BACKUP_ROOT}")
    startup_prewarm = schedule_startup_prediction_prewarm()
    if startup_prewarm:
        scheduled = sum(1 for item in startup_prewarm if item.get("scheduled"))
        print(f"Prediction prewarm scheduled for {scheduled}/{len(startup_prewarm)} games")
    if load_prediction_auto_config().get("enabled"):
        start_prediction_auto()
        print("Prediction auto tracking resumed from config")
    start_telegram_bot_polling()
    print("Telegram bot polling worker started")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        print("Stopping server...")
    finally:
        stop_telegram_bot_polling()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
