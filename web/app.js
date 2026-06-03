const state = {
  games: [],
  currentGame: null,
  analysis: null,
  prediction: null,
  predictionTracking: null,
  predictionTrackingPage: 1,
  predictionTrackingStatus: "all",
  adjacentStats: null,
  adjacentHitPage: 1,
  adjacentHitQuery: "",
  adjacentHits: null,
  predictionAuto: null,
  predictionAutoPollTimer: null,
  predictionAutoLastCompletedAt: "",
  predictionTrackingRefreshInFlight: false,
  predictionPanel: "a",
  predictionPanels: {
    a: {
      prediction: null,
      predictionTracking: null,
      predictionTrackingPage: 1,
      predictionTrackingStatus: "all",
      adjacentStats: null,
      adjacentHitPage: 1,
      adjacentHitQuery: "",
      adjacentHits: null,
    },
    b: {
      prediction: null,
      predictionTracking: null,
      predictionTrackingPage: 1,
      predictionTrackingStatus: "all",
      adjacentStats: null,
      adjacentHitPage: 1,
      adjacentHitQuery: "",
      adjacentHits: null,
    },
    c: {
      prediction: null,
      predictionTracking: null,
      predictionTrackingPage: 1,
      predictionTrackingStatus: "all",
      adjacentStats: null,
      adjacentHitPage: 1,
      adjacentHitQuery: "",
      adjacentHits: null,
    },
    d: {
      prediction: null,
      predictionTracking: null,
      predictionTrackingPage: 1,
      predictionTrackingStatus: "all",
      adjacentStats: null,
      adjacentHitPage: 1,
      adjacentHitQuery: "",
      adjacentHits: null,
    },
    e: {
      prediction: null,
      predictionTracking: null,
      predictionTrackingPage: 1,
      predictionTrackingStatus: "all",
      adjacentStats: null,
      adjacentHitPage: 1,
      adjacentHitQuery: "",
      adjacentHits: null,
    },
    f: {
      prediction: null,
      predictionTracking: null,
      predictionTrackingPage: 1,
      predictionTrackingStatus: "all",
      adjacentStats: null,
      adjacentHitPage: 1,
      adjacentHitQuery: "",
      adjacentHits: null,
    },
    g: {
      prediction: null,
      predictionTracking: null,
      predictionTrackingPage: 1,
      predictionTrackingStatus: "all",
      adjacentStats: null,
      adjacentHitPage: 1,
      adjacentHitQuery: "",
      adjacentHits: null,
    },
  },
  backtest: null,
  backtestPollTimer: null,
  backtestScan: null,
  backtestScanPollTimer: null,
  martingaleMode: "main",
  martingalePickCount: 3,
  martingalePlan: null,
  martingaleOddsDirty: false,
  martingaleDefaultKey: "",
  historyPage: 1,
  history: null,
  cdeBacktestPage: 1,
  loading: false,
  activeView: "prediction",
  lastSync: null,
  syncGapWarnings: new Map(),
  responseCache: new Map(),
  currentGapAudit: null,
  currentIntegrity: null,
  activeModal: null,
};

const els = {
  gameSelect: document.querySelector("#gameSelect"),
  gamePills: document.querySelector("#gamePills"),
  gameSubtitle: document.querySelector("#gameSubtitle"),
  dataState: document.querySelector("#dataState"),
  drawCount: document.querySelector("#drawCount"),
  newestDraw: document.querySelector("#newestDraw"),
  fileModified: document.querySelector("#fileModified"),
  lastSyncSummary: document.querySelector("#lastSyncSummary"),
  lastSyncTime: document.querySelector("#lastSyncTime"),
  lastBcRows: document.querySelector("#lastBcRows"),
  lastEtiposRows: document.querySelector("#lastEtiposRows"),
  lastSettledPredictions: document.querySelector("#lastSettledPredictions"),
  lastSyncError: document.querySelector("#lastSyncError"),
  syncBtn: document.querySelector("#syncBtn"),
  fullSyncBtn: document.querySelector("#fullSyncBtn"),
  refreshPageBtn: document.querySelector("#refreshPageBtn"),
  resetBtn: document.querySelector("#resetBtn"),
  drawLimit: document.querySelector("#drawLimit"),
  minCurrentMiss: document.querySelector("#minCurrentMiss"),
  minHits: document.querySelector("#minHits"),
  maxTail: document.querySelector("#maxTail"),
  tripleQuery: document.querySelector("#tripleQuery"),
  sortBy: document.querySelector("#sortBy"),
  sortOrder: document.querySelector("#sortOrder"),
  resultLimit: document.querySelector("#resultLimit"),
  cdeBacktestTrain: document.querySelector("#cdeBacktestTrain"),
  cdeBacktestMeta: document.querySelector("#cdeBacktestMeta"),
  cdeBacktestStats: document.querySelector("#cdeBacktestStats"),
  cdeBacktestPanelCards: document.querySelector("#cdeBacktestPanelCards"),
  cdeBacktestNotes: document.querySelector("#cdeBacktestNotes"),
  cdeBacktestRows: document.querySelector("#cdeBacktestRows"),
  cdeBacktestPrevBtn: document.querySelector("#cdeBacktestPrevBtn"),
  cdeBacktestNextBtn: document.querySelector("#cdeBacktestNextBtn"),
  cdeBacktestPageInfo: document.querySelector("#cdeBacktestPageInfo"),
  applyBtn: document.querySelector("#applyBtn"),
  p3: document.querySelector("#p3"),
  p3Wait: document.querySelector("#p3Wait"),
  ev60: document.querySelector("#ev60"),
  threePickEvLabel: document.querySelector("#threePickEvLabel"),
  threePickEvHint: document.querySelector("#threePickEvHint"),
  anyRun: document.querySelector("#anyRun"),
  observedWindows: document.querySelector("#observedWindows"),
  expectedWindows: document.querySelector("#expectedWindows"),
  predictionTitle: document.querySelector("#predictionTitle"),
  predictionWindow: document.querySelector("#predictionWindow"),
  predictionMethod: document.querySelector("#predictionMethod"),
  predictionKillPanel: document.querySelector("#predictionKillPanel"),
  predictionKillLabel: document.querySelector("#predictionKillLabel"),
  predictionKillSummary: document.querySelector("#predictionKillSummary"),
  predictionKillNumbers: document.querySelector("#predictionKillNumbers"),
  predictionKillSources: document.querySelector("#predictionKillSources"),
  predictionStrategyTickets: document.querySelector("#predictionStrategyTickets"),
  predictionStrategyHealth: document.querySelector("#predictionStrategyHealth"),
  predictionTrackingPanel: document.querySelector("#predictionTrackingPanel"),
  predictionTrackingMeta: document.querySelector("#predictionTrackingMeta"),
  predictionTrackingStats: document.querySelector("#predictionTrackingStats"),
  predictionTrackingWarning: document.querySelector("#predictionTrackingWarning"),
  predictionTrackingGroups: document.querySelector("#predictionTrackingGroups"),
  predictionAdjacentStatsWrap: document.querySelector("#predictionAdjacentStatsWrap"),
  predictionAdjacentStatsSummary: document.querySelector("#predictionAdjacentStatsSummary"),
  predictionAdjacentStats: document.querySelector("#predictionAdjacentStats"),
  predictionTrackingRows: document.querySelector("#predictionTrackingRows"),
  predictionTrackingStatusFilter: document.querySelector("#predictionTrackingStatusFilter"),
  predictionTrackingPrevBtn: document.querySelector("#predictionTrackingPrevBtn"),
  predictionTrackingNextBtn: document.querySelector("#predictionTrackingNextBtn"),
  predictionTrackingPageInfo: document.querySelector("#predictionTrackingPageInfo"),
  predictionAutoStatus: document.querySelector("#predictionAutoStatus"),
  predictionAutoToggleBtn: document.querySelector("#predictionAutoToggleBtn"),
  predictionAutoRunBtn: document.querySelector("#predictionAutoRunBtn"),
  predictionNotice: document.querySelector("#predictionNotice"),
  martingaleView: document.querySelector("#martingaleView"),
  martingaleGameMeta: document.querySelector("#martingaleGameMeta"),
  martingaleModeGroup: document.querySelector("#martingaleModeGroup"),
  martingalePlayGroup: document.querySelector("#martingalePlayGroup"),
  martingaleOdds: document.querySelector("#martingaleOdds"),
  martingaleBankroll: document.querySelector("#martingaleBankroll"),
  martingalePeriods: document.querySelector("#martingalePeriods"),
  martingaleTargetProfit: document.querySelector("#martingaleTargetProfit"),
  martingaleUnit: document.querySelector("#martingaleUnit"),
  martingaleMaxStake: document.querySelector("#martingaleMaxStake"),
  martingaleStopLoss: document.querySelector("#martingaleStopLoss"),
  riskFlatStake: document.querySelector("#riskFlatStake"),
  riskKellyFraction: document.querySelector("#riskKellyFraction"),
  generateMartingaleBtn: document.querySelector("#generateMartingaleBtn"),
  martingaleInputHint: document.querySelector("#martingaleInputHint"),
  martingaleResultMeta: document.querySelector("#martingaleResultMeta"),
  martingaleHitProb: document.querySelector("#martingaleHitProb"),
  martingaleFairOdds: document.querySelector("#martingaleFairOdds"),
  martingalePlanHitProb: document.querySelector("#martingalePlanHitProb"),
  martingaleMissAllProb: document.querySelector("#martingaleMissAllProb"),
  martingaleEv: document.querySelector("#martingaleEv"),
  martingaleOddsGap: document.querySelector("#martingaleOddsGap"),
  martingaleMaxPlanStake: document.querySelector("#martingaleMaxPlanStake"),
  martingaleLastStake: document.querySelector("#martingaleLastStake"),
  martingaleTotalStake: document.querySelector("#martingaleTotalStake"),
  martingaleBankrollUsage: document.querySelector("#martingaleBankrollUsage"),
  martingaleBreakPoint: document.querySelector("#martingaleBreakPoint"),
  martingaleBreakReason: document.querySelector("#martingaleBreakReason"),
  martingaleAlert: document.querySelector("#martingaleAlert"),
  martingaleRows: document.querySelector("#martingaleRows"),
  riskBudgetMeta: document.querySelector("#riskBudgetMeta"),
  riskBudgetBreakEven: document.querySelector("#riskBudgetBreakEven"),
  riskBudgetEdge: document.querySelector("#riskBudgetEdge"),
  riskBudgetKellyFraction: document.querySelector("#riskBudgetKellyFraction"),
  riskBudgetKellyStake: document.querySelector("#riskBudgetKellyStake"),
  riskBudgetFlatExpected: document.querySelector("#riskBudgetFlatExpected"),
  riskBudgetFlatRange: document.querySelector("#riskBudgetFlatRange"),
  riskBudgetPlanExpected: document.querySelector("#riskBudgetPlanExpected"),
  riskBudgetPlanRisk: document.querySelector("#riskBudgetPlanRisk"),
  riskBudgetNote: document.querySelector("#riskBudgetNote"),
  riskBudgetRows: document.querySelector("#riskBudgetRows"),
  backtestStrategy: document.querySelector("#backtestStrategy"),
  backtestNumbersField: document.querySelector("#backtestNumbersField"),
  backtestNumbers: document.querySelector("#backtestNumbers"),
  backtestTopN: document.querySelector("#backtestTopN"),
  backtestMissThreshold: document.querySelector("#backtestMissThreshold"),
  backtestTrain: document.querySelector("#backtestTrain"),
  backtestTest: document.querySelector("#backtestTest"),
  backtestStake: document.querySelector("#backtestStake"),
  backtestOdds: document.querySelector("#backtestOdds"),
  runBacktestBtn: document.querySelector("#runBacktestBtn"),
  runBacktestScanBtn: document.querySelector("#runBacktestScanBtn"),
  backtestStatus: document.querySelector("#backtestStatus"),
  backtestProgressBar: document.querySelector("#backtestProgressBar"),
  backtestProgressText: document.querySelector("#backtestProgressText"),
  backtestResultPanel: document.querySelector("#backtestResultPanel"),
  backtestResultTitle: document.querySelector("#backtestResultTitle"),
  backtestResultMeta: document.querySelector("#backtestResultMeta"),
  backtestHitRate: document.querySelector("#backtestHitRate"),
  backtestTheoryHitRate: document.querySelector("#backtestTheoryHitRate"),
  backtestRoi: document.querySelector("#backtestRoi"),
  backtestTheoryRoi: document.querySelector("#backtestTheoryRoi"),
  backtestBetsWon: document.querySelector("#backtestBetsWon"),
  backtestProfit: document.querySelector("#backtestProfit"),
  backtestMaxLoss: document.querySelector("#backtestMaxLoss"),
  backtestChart: document.querySelector("#backtestChart"),
  backtestSamples: document.querySelector("#backtestSamples"),
  backtestScanPanel: document.querySelector("#backtestScanPanel"),
  backtestScanMeta: document.querySelector("#backtestScanMeta"),
  backtestScanNotice: document.querySelector("#backtestScanNotice"),
  backtestScanRows: document.querySelector("#backtestScanRows"),
  backtestView: document.querySelector("#backtestView"),
  tripleCount: document.querySelector("#tripleCount"),
  runBars: document.querySelector("#runBars"),
  tripleTable: document.querySelector("#tripleTable"),
  runPatternCards: document.querySelector("#runPatternCards"),
  sumRangeBars: document.querySelector("#sumRangeBars"),
  sizeRatioBars: document.querySelector("#sizeRatioBars"),
  oddEvenBars: document.querySelector("#oddEvenBars"),
  bonusBallPanel: document.querySelector("#bonusBallPanel"),
  bonusBallMeta: document.querySelector("#bonusBallMeta"),
  bonusBallBars: document.querySelector("#bonusBallBars"),
  crossCategory: document.querySelector("#crossCategory"),
  crossCondition: document.querySelector("#crossCondition"),
  crossBars: document.querySelector("#crossBars"),
  analysisView: document.querySelector("#analysisView"),
  pairCount: document.querySelector("#pairCount"),
  pairTable: document.querySelector("#pairTable"),
  quadCount: document.querySelector("#quadCount"),
  quadTable: document.querySelector("#quadTable"),
  historyQuery: document.querySelector("#historyQuery"),
  historySort: document.querySelector("#historySort"),
  historyPageSize: document.querySelector("#historyPageSize"),
  historySearchBtn: document.querySelector("#historySearchBtn"),
  historyCount: document.querySelector("#historyCount"),
  historyTable: document.querySelector("#historyTable"),
  historyView: document.querySelector("#historyView"),
  prevPageBtn: document.querySelector("#prevPageBtn"),
  nextPageBtn: document.querySelector("#nextPageBtn"),
  pageInfo: document.querySelector("#pageInfo"),
  toast: document.querySelector("#toast"),
};

const TOOL_MODAL_VIEWS = new Set(["martingale", "backtest", "history"]);
const PREDICTION_PANEL_DEFAULT = "a";
const PREDICTION_PANEL_B = "b";
const PREDICTION_PANEL_C = "c";
const PREDICTION_PANEL_D = "d";
const PREDICTION_PANEL_E = "e";
const PREDICTION_PANEL_F = "f";
const PREDICTION_PANEL_G = "g";
const CDE_KILL_BACKTEST_GAMES = new Set(["spain_l_express_20_70", "poland_keno_20_70"]);
const CDE_BACKTEST_PAGE_SIZE = 25;
const BACKTEST_DUPLICATE_SHAPE_OPTIONS = new Set(["hasPair", "hasTriple", "hasQuad"]);
const BACKTEST_SHAPE_OPTION_LABELS = {
  hasPair: "两连",
  hasDoublePair: "双两连",
  hasTriplePairSet: "三双两连",
  hasTriple: "三连",
  hasQuadPairSet: "四双两连",
  hasFivePairSet: "五双两连",
  hasPairTriple: "两连+三连",
  hasDoubleTriple: "双三连",
  hasTripleDoublePair: "三连+双两连",
  hasQuad: "四连",
  hasQuadPair: "四连+两连",
  hasFive: "五连",
  hasSix: "六连",
};

const MARTINGALE_DEFAULT_ODDS = {
  spain_l_express_20_70: {
    1: 3.2,
    2: 11,
    3: 40,
    4: 150,
    5: 500,
    6: 2000,
    7: 6500,
    8: 18000,
  },
  poland_keno_20_70: {
    1: 3.2,
    2: 11,
    3: 40,
    4: 150,
    5: 500,
    6: 2000,
    7: 6500,
    8: 18000,
  },
  italy_win_for_life_10_20: {
    1: 1.8,
    2: 3.8,
    3: 9,
    4: 20,
    5: 50,
    6: 150,
    7: 500,
    8: 1650,
  },
  russia_rapido_8_20: {
    1: 2.2,
    2: 6,
    3: 18,
    4: 60,
    5: 220,
    6: 1000,
    7: 5000,
  },
};

const MARTINGALE_BONUS_ODDS = {
  russia_rapido_8_20: {
    1: 9,
    2: 25,
    3: 70,
    4: 200,
    5: 700,
    6: 2000,
    7: 8000,
  },
  italy_win_for_life_10_20: {
    1: 35,
    2: 75,
    3: 150,
    4: 300,
    5: 600,
    6: 1500,
    7: 3000,
    8: 10000,
  },
};

function fmtPct(value, digits = 2) {
  if (!Number.isFinite(value)) return "--";
  return `${(value * 100).toFixed(digits)}%`;
}

function fmtNumber(value, digits = 2) {
  if (!Number.isFinite(value)) return "--";
  return value.toFixed(digits);
}

function fmtMoney(value, digits = 2) {
  if (!Number.isFinite(value)) return "--";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(digits)}`;
}

function decimalsFromStep(step) {
  const text = String(step || "");
  if (!text.includes(".")) return 2;
  return Math.min(6, Math.max(0, text.split(".")[1].replace(/0+$/, "").length));
}

function fmtAmount(value, unit = 0.01) {
  if (!Number.isFinite(value)) return "--";
  const digits = Math.max(2, decimalsFromStep(unit));
  return value.toLocaleString("zh-CN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function parseNumberInput(input, fallback = 0) {
  const value = Number(input?.value ?? fallback);
  return Number.isFinite(value) ? value : fallback;
}

function roundUpToUnit(value, unit) {
  const safeUnit = Number.isFinite(unit) && unit > 0 ? unit : 0.01;
  return Math.ceil((value - Number.EPSILON) / safeUnit) * safeUnit;
}

function roundDownToUnit(value, unit) {
  const safeUnit = Number.isFinite(unit) && unit > 0 ? unit : 0.01;
  return Math.max(0, Math.floor((value + Number.EPSILON) / safeUnit) * safeUnit);
}

function clampNumber(value, min, max) {
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, value));
}

function hashString(value) {
  let hash = 2166136261;
  const text = String(value ?? "");
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function seededRandom(seed) {
  let value = seed >>> 0;
  return () => {
    value = (Math.imul(value, 1664525) + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

function percentile(sortedValues, pct) {
  if (!sortedValues.length) return 0;
  const index = clampNumber((sortedValues.length - 1) * pct, 0, sortedValues.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) return sortedValues[lower];
  return sortedValues[lower] + (sortedValues[upper] - sortedValues[lower]) * (index - lower);
}

function combination(n, k) {
  if (!Number.isFinite(n) || !Number.isFinite(k) || k < 0 || k > n) return 0;
  const count = Math.min(k, n - k);
  let value = 1;
  for (let index = 1; index <= count; index += 1) {
    value = (value * (n - count + index)) / index;
  }
  return value;
}

function mainPickHitProbability(pickCount) {
  const game = state.currentGame || {};
  const drawn = Number(game.drawnNumbers || 0);
  const total = Number(game.totalNumbers || 0);
  if (!drawn || !total || pickCount > drawn || pickCount > total) return 0;
  return combination(drawn, pickCount) / combination(total, pickCount);
}

function bonusBallHitProbability() {
  const game = state.currentGame || {};
  if (!game.hasBonusBall) return 0;
  const total = Number(game.bonusBallTotalNumbers || game.totalNumbers || 0);
  return total > 0 ? 1 / total : 0;
}

function pickHitProbability(pickCount, mode = state.martingaleMode) {
  const mainProbability = mainPickHitProbability(pickCount);
  if (mode !== "bonus") return mainProbability;
  return mainProbability * bonusBallHitProbability();
}

function martingaleModeLabel(mode = state.martingaleMode) {
  return mode === "bonus" ? "含特殊球" : "普通主号";
}

function martingalePlayLabel(pickCount = state.martingalePickCount, mode = state.martingaleMode) {
  return mode === "bonus" ? `${pickCount}+1特殊球` : `${pickCount}球`;
}

function currentMartingaleOddsMap() {
  const gameKey = currentGameKey();
  return state.martingaleMode === "bonus"
    ? MARTINGALE_BONUS_ODDS[gameKey] || {}
    : MARTINGALE_DEFAULT_ODDS[gameKey] || {};
}

function currentMainDefaultOddsFor(pickCount) {
  return MARTINGALE_DEFAULT_ODDS[currentGameKey()]?.[pickCount] || null;
}

function currentMartingaleDefaultOdds() {
  return currentMartingaleOddsMap()[state.martingalePickCount] || null;
}

function syncMartingaleDefaultOdds(force = false) {
  if (!els.martingaleOdds) return;
  const defaultOdds = currentMartingaleDefaultOdds();
  const key = `${currentGameKey()}:${state.martingaleMode}:${state.martingalePickCount}`;
  if (!defaultOdds) {
    if (force || (!state.martingaleOddsDirty && state.martingaleDefaultKey !== key)) {
      els.martingaleOdds.value = "";
      state.martingaleOddsDirty = false;
    }
    state.martingaleDefaultKey = key;
    return;
  }
  if (force || (!state.martingaleOddsDirty && state.martingaleDefaultKey !== key)) {
    els.martingaleOdds.value = String(defaultOdds);
    state.martingaleOddsDirty = false;
  }
  state.martingaleDefaultKey = key;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function fmtDate(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleString("zh-CN", {
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function fmtTime(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleTimeString("zh-CN", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
  });
}

function relativeTargetLabel(value, status) {
  if (!value || status !== "pending") return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const diffMs = date.getTime() - Date.now();
  const absMinutes = Math.max(0, Math.round(Math.abs(diffMs) / 60000));
  if (diffMs >= 0) {
    return `+${absMinutes}m`;
  }
  return `!${absMinutes}m`;
}

function buildAnalysisQuery() {
  const params = new URLSearchParams();
  const requestedWindow = els.drawLimit?.value || "30";
  params.set("game", state.currentGame?.key || els.gameSelect.value || "");
  params.set("window", requestedWindow);
  params.set("trainWindow", els.cdeBacktestTrain?.value || "240");
  params.set("detailLimit", requestedWindow);
  return params;
}

function buildHistoryQuery() {
  const params = new URLSearchParams();
  params.set("game", state.currentGame?.key || els.gameSelect.value || "");
  params.set("page", String(state.historyPage));
  params.set("pageSize", els.historyPageSize.value || "100");
  params.set("sort", els.historySort.value || "desc");
  params.set("q", els.historyQuery.value || "");
  return params;
}

function showToast(message, isError = false) {
  els.toast.textContent = message;
  els.toast.style.borderColor = isError ? "var(--risk)" : "var(--line)";
  els.toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => els.toast.classList.add("hidden"), 5200);
}

function currentGameKey() {
  return state.currentGame?.key || els.gameSelect.value || "";
}

function normalizePredictionPanel(panel = state.predictionPanel) {
  if (panel === PREDICTION_PANEL_G) return PREDICTION_PANEL_G;
  if (panel === PREDICTION_PANEL_F) return PREDICTION_PANEL_F;
  if (panel === PREDICTION_PANEL_E) return PREDICTION_PANEL_E;
  if (panel === PREDICTION_PANEL_D) return PREDICTION_PANEL_D;
  if (panel === PREDICTION_PANEL_C) return PREDICTION_PANEL_C;
  return panel === PREDICTION_PANEL_B ? PREDICTION_PANEL_B : PREDICTION_PANEL_DEFAULT;
}

function predictionPanelState(panel = state.predictionPanel) {
  return state.predictionPanels[normalizePredictionPanel(panel)] || state.predictionPanels[PREDICTION_PANEL_DEFAULT];
}

function predictionPanelLabel(panel = state.predictionPanel) {
  const panelKey = normalizePredictionPanel(panel);
  if (panelKey === PREDICTION_PANEL_G) return "预测面板G";
  if (panelKey === PREDICTION_PANEL_F) return "预测面板F";
  if (panelKey === PREDICTION_PANEL_E) return "预测面板E";
  if (panelKey === PREDICTION_PANEL_D) return "预测面板D";
  if (panelKey === PREDICTION_PANEL_C) return "预测面板C";
  return panelKey === PREDICTION_PANEL_B ? "预测面板B" : "预测面板A";
}

function predictionPanelForView(view) {
  if (view === "predictionG") return PREDICTION_PANEL_G;
  if (view === "predictionF") return PREDICTION_PANEL_F;
  if (view === "predictionE") return PREDICTION_PANEL_E;
  if (view === "predictionD") return PREDICTION_PANEL_D;
  if (view === "predictionC") return PREDICTION_PANEL_C;
  if (view === "predictionB") return PREDICTION_PANEL_B;
  return PREDICTION_PANEL_DEFAULT;
}

function syncPredictionPanelMirror(panel = state.predictionPanel) {
  const slot = predictionPanelState(panel);
  state.predictionPanel = normalizePredictionPanel(panel);
  state.prediction = slot.prediction;
  state.predictionTracking = slot.predictionTracking;
  state.predictionTrackingPage = slot.predictionTrackingPage;
  state.predictionTrackingStatus = slot.predictionTrackingStatus;
  state.adjacentStats = slot.adjacentStats;
  state.adjacentHitPage = slot.adjacentHitPage;
  state.adjacentHitQuery = slot.adjacentHitQuery;
  state.adjacentHits = slot.adjacentHits;
  return slot;
}

function updatePredictionPanelState(updates, panel = state.predictionPanel) {
  const panelKey = normalizePredictionPanel(panel);
  const slot = predictionPanelState(panel);
  Object.assign(slot, updates);
  if (state.predictionPanel === panelKey) {
    syncPredictionPanelMirror(panelKey);
  }
  return slot;
}

function setPredictionPanel(panel) {
  syncPredictionPanelMirror(normalizePredictionPanel(panel));
}

function predictionPanelForOptions(options = {}) {
  if (options.panel) return normalizePredictionPanel(options.panel);
  if (state.activeView === "predictionG") return PREDICTION_PANEL_G;
  if (state.activeView === "predictionF") return PREDICTION_PANEL_F;
  if (state.activeView === "predictionE") return PREDICTION_PANEL_E;
  if (state.activeView === "predictionD") return PREDICTION_PANEL_D;
  if (state.activeView === "predictionC") return PREDICTION_PANEL_C;
  if (state.activeView === "predictionB") return PREDICTION_PANEL_B;
  if (state.activeView === "prediction") return PREDICTION_PANEL_DEFAULT;
  return normalizePredictionPanel(state.predictionPanel);
}

function currentGameSupportsAnalysis() {
  return CDE_KILL_BACKTEST_GAMES.has(currentGameKey());
}

function currentGameSupportsPredictions() {
  return state.currentGame?.supportsPredictions !== false;
}

function currentGameSupportsPredictionTracking() {
  return currentGameSupportsPredictions() && state.currentGame?.supportsPredictionTracking !== false;
}

function currentGameSupportsBacktest() {
  return state.currentGame?.supportsBacktest !== false;
}

function currentGameSupportsMartingale() {
  return state.currentGame?.supportsMartingale !== false;
}

function currentGameSupportsView(view) {
  if (view === "history") return true;
  if (
    view === "prediction" ||
    view === "predictionB" ||
    view === "predictionC" ||
    view === "predictionD" ||
    view === "predictionE" ||
    view === "predictionF" ||
    view === "predictionG"
  ) {
    return currentGameSupportsPredictions();
  }
  if (view === "analysis") return currentGameSupportsAnalysis();
  if (view === "backtest") return currentGameSupportsBacktest();
  if (view === "martingale") return currentGameSupportsMartingale();
  return true;
}

function isToolModalView(view) {
  return TOOL_MODAL_VIEWS.has(view);
}

function modalElementForView(view) {
  if (view === "martingale") return els.martingaleView;
  if (view === "backtest") return els.backtestView;
  if (view === "analysis") return els.analysisView;
  if (view === "history") return els.historyView;
  return null;
}

function renderTabState() {
  const activeView = state.activeModal || state.activeView;
  for (const button of document.querySelectorAll(".tab-btn")) {
    button.classList.toggle("active", button.dataset.view === activeView);
  }
}

function closeToolModal() {
  const view = state.activeModal;
  if (!view) return;
  const element = modalElementForView(view);
  if (element) {
    element.classList.remove("modal-open");
    element.classList.remove("active");
  }
  state.activeModal = null;
  document.body.classList.remove("tool-modal-open");
  renderTabState();
}

async function hydrateView(view) {
  if (
    view === "prediction" ||
    view === "predictionB" ||
    view === "predictionC" ||
    view === "predictionD" ||
    view === "predictionE" ||
    view === "predictionF" ||
    view === "predictionG"
  ) {
    const panel = predictionPanelForView(view);
    setPredictionPanel(panel);
    const slot = predictionPanelState(panel);
    if (!slot.prediction) loadPrediction({ panel });
    else {
      renderPredictionPage();
      loadPredictionTracking({ silent: true, panel });
    }
  }
  if (view === "martingale") {
    loadCurrentSummary().catch((error) => showToast(`加载最新开奖失败：${error.message}`, true));
    updateMartingaleMeta();
  }
  if (view === "analysis" && !state.analysis) loadAnalysis();
  if (view === "backtest") {
    loadCurrentSummary().catch((error) => showToast(`加载最新开奖失败：${error.message}`, true));
    if (!state.backtest) loadBacktestStatus();
  }
  if (view === "history" && !state.history) loadHistory();
}

function openToolModal(view) {
  if (!isToolModalView(view)) return;
  if (!currentGameSupportsView(view)) {
    showToast("该彩种当前不开放该工具");
    return;
  }
  const element = modalElementForView(view);
  if (!element) return;
  if (state.activeModal === view && element.classList.contains("modal-open")) {
    renderTabState();
    return;
  }
  if (state.activeModal && state.activeModal !== view) {
    closeToolModal();
  }
  state.activeModal = view;
  element.classList.add("active", "modal-open");
  document.body.classList.add("tool-modal-open");
  renderTabState();
  hydrateView(view);
}

function payloadMatchesCurrentGame(data) {
  const key = data?.game?.key;
  return !key || key === currentGameKey();
}

function isPaginatedPredictionTrackingPayload(data) {
  return Boolean(data && Array.isArray(data.items) && Number(data.pageSize || 0) > 0);
}

function cacheGet(key) {
  return state.responseCache.get(key) || null;
}

function cacheSet(key, payload) {
  state.responseCache.set(key, payload);
  if (state.responseCache.size > 30) {
    state.responseCache.delete(state.responseCache.keys().next().value);
  }
}

function clearResponseCache() {
  state.responseCache.clear();
}

function relativeTime(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  const diffMs = Date.now() - date.getTime();
  const suffix = diffMs >= 0 ? "前" : "后";
  const abs = Math.abs(diffMs);
  const minutes = Math.round(abs / 60000);
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} min ${suffix}`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours} h ${suffix}`;
  return `${Math.round(hours / 24)} d ${suffix}`;
}

function syncResultPossibleGap(result) {
  const meta = result?.syncMeta || result?.meta || {};
  return Boolean(result?.possibleGap || meta.possibleGap);
}

function syncGapWarningFromResult(result, fallbackGameKey = "", rootPayload = null) {
  const meta = result?.syncMeta || result?.meta || {};
  return {
    gameKey: result?.game?.key || fallbackGameKey || "",
    pagesFetched: meta.pagesFetched || result?.pagesFetched || "",
    oldestFetchedUtc: meta.oldestFetchedUtc || result?.oldestFetchedUtc || "",
    newestExistingUtc: meta.newestExistingUtc || result?.newestExistingUtc || "",
    generatedAt: rootPayload?.generatedAt || result?.generatedAt || "",
  };
}

function updateSyncGapWarningForResult(result, fallbackGameKey = "", rootPayload = null) {
  const gameKey = result?.game?.key || fallbackGameKey || "";
  if (!gameKey) return;
  if (syncResultPossibleGap(result)) {
    state.syncGapWarnings.set(gameKey, syncGapWarningFromResult(result, gameKey, rootPayload));
  } else {
    state.syncGapWarnings.delete(gameKey);
  }
}

function updateSyncGapWarnings(payload) {
  if (!payload) return;
  if (payload.allGames) {
    const seen = new Set();
    for (const result of [...(payload.results || []), payload.currentResult].filter(Boolean)) {
      const gameKey = result?.game?.key || "";
      if (gameKey && seen.has(gameKey)) continue;
      if (gameKey) seen.add(gameKey);
      updateSyncGapWarningForResult(result, gameKey, payload);
    }
    return;
  }
  updateSyncGapWarningForResult(payload, payload.game?.key || currentGameKey(), payload);
}

function currentSyncGapWarning() {
  return state.syncGapWarnings.get(currentGameKey()) || null;
}

function syncGapWarningTitle(warning) {
  const parts = ["最近一次增量同步未命中本地已有记录，建议执行全量同步确认历史连续性。"];
  if (warning?.pagesFetched) parts.push(`抓取 ${warning.pagesFetched} 页`);
  if (warning?.oldestFetchedUtc) parts.push(`最旧抓取 ${fmtDate(warning.oldestFetchedUtc)}`);
  if (warning?.newestExistingUtc) parts.push(`原本地最新 ${fmtDate(warning.newestExistingUtc)}`);
  return parts.join("；");
}

function setDataState(html, level = "", title = "") {
  const article = els.dataState?.closest("article");
  if (article) {
    article.classList.toggle("status-warning", level === "warning");
    article.classList.toggle("status-danger", level === "danger");
  }
  if (title) {
    els.dataState.setAttribute("title", title);
  } else {
    els.dataState.removeAttribute("title");
  }
  els.dataState.innerHTML = html;
}

function renderDataState() {
  if (state.loading) return;
  const integrity = state.currentIntegrity;
  const gap = state.currentGapAudit;
  const syncGap = currentSyncGapWarning();
  if (syncGap) {
    setDataState(
      `已加载 <span class="status-badge warn" title="${escapeHtml(
        syncGapWarningTitle(syncGap),
      )}">增量缺口待确认</span>`,
      "warning",
      syncGapWarningTitle(syncGap),
    );
  } else if (integrity?.checkedRemote && integrity.status === "missing") {
    setDataState(`已加载 <span class="status-badge warn">本地少于BC ${Number(
      integrity.missingVsBc || 0,
    ).toLocaleString("zh-CN")}期</span>`, "warning");
  } else if (integrity?.checkedRemote && integrity.status === "behind_latest") {
    setDataState('已加载 <span class="status-badge warn">最新期落后BC</span>', "warning");
  } else if (integrity?.checkedRemote && integrity.status === "aligned") {
    setDataState('已加载 <span class="status-badge ok">BC历史已对齐</span>');
  } else if (gap?.hasGaps && gap.authoritativeMissingCheck) {
    setDataState(`已加载 <span class="status-badge info" title="${escapeHtml(
      gap.note || "固定开奖间隔扫描提示，不等同于本地缺数据",
    )}">时间间隔 ${Number(
      gap.missingIntervals || 0,
    ).toLocaleString("zh-CN")}</span>`);
  } else if (gap?.checked) {
    setDataState('已加载 <span class="status-badge ok">本地结构OK</span>');
  } else {
    setDataState("已加载");
  }
}

function resetPageState() {
  closeToolModal();
  state.analysis = null;
  state.cdeBacktestPage = 1;
  for (const slot of Object.values(state.predictionPanels)) {
    slot.prediction = null;
    slot.predictionTracking = null;
    slot.predictionTrackingPage = 1;
    slot.predictionTrackingStatus = "all";
    slot.adjacentStats = null;
    slot.adjacentHitPage = 1;
    slot.adjacentHitQuery = "";
    slot.adjacentHits = null;
  }
  syncPredictionPanelMirror();
  state.backtest = null;
  state.backtestScan = null;
  state.martingalePlan = null;
  state.martingaleOddsDirty = false;
  state.martingaleDefaultKey = "";
  resetMartingaleResult();
  state.history = null;
  state.historyPage = 1;
  state.currentGapAudit = null;
  state.currentIntegrity = null;
}

function renderGamePills() {
  if (!els.gamePills) return;
  els.gamePills.innerHTML = state.games
    .map((game) => {
      const active = game.key === currentGameKey() ? "active" : "";
      const analysis = game.supportsAnalysis ? "analysis-on" : "analysis-off";
      return `<button type="button" class="game-pill ${active} ${analysis}" data-game="${escapeHtml(
        game.key,
      )}" title="BC.Game ${escapeHtml(game.lotteryId)} · ${escapeHtml(game.country)}">
        <span class="game-pill-dot"></span>${escapeHtml(game.shortName)}
      </button>`;
    })
    .join("");
}

function backtestShapeOptionLabel(item) {
  const mapped = BACKTEST_SHAPE_OPTION_LABELS[item.key];
  if (mapped) return mapped;
  return String(item.label || item.key || "").replace(/^含/, "").replace(/^任意/, "");
}

function uniqueBacktestOptions(options) {
  const seen = new Set();
  return options.filter((item) => {
    const key = `${item.value}\n${item.label}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function renderBacktestStrategyOptions() {
  const conditions = state.currentGame?.runConditions || [];
  if (!els.backtestStrategy) return;
  const selected = els.backtestStrategy.value || "triple_top_n";
  const shapeOptions = conditions
    .filter((item) => !BACKTEST_DUPLICATE_SHAPE_OPTIONS.has(item.key))
    .map((item) => ({
      value: `shape_top_n:${item.key}`,
      label: `${backtestShapeOptionLabel(item)}遗漏 Top N`,
    }));
  const options = uniqueBacktestOptions([
    { value: "exact_numbers", label: "指定号码组回测" },
    { value: "pair_top_n", label: "两连号遗漏 Top N" },
    { value: "triple_top_n", label: "三连号遗漏 Top N" },
    { value: "quad_top_n", label: "四连号遗漏 Top N" },
    ...shapeOptions,
  ]);
  els.backtestStrategy.innerHTML = options
    .map((item) => `<option value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</option>`)
    .join("");
  els.backtestStrategy.value = options.some((item) => item.value === selected) ? selected : "triple_top_n";
  syncBacktestControls();
}

function syncBacktestControls() {
  const strategy = els.backtestStrategy.value;
  const singleTarget = strategy === "exact_numbers";
  const exactNumbers = strategy === "exact_numbers";
  if (els.backtestNumbersField) {
    els.backtestNumbersField.classList.toggle("hidden", !exactNumbers);
  }
  if (els.backtestNumbers) {
    els.backtestNumbers.disabled = !exactNumbers;
  }
  if (singleTarget) {
    if (!els.backtestTopN.dataset.previousValue && els.backtestTopN.value !== "1") {
      els.backtestTopN.dataset.previousValue = els.backtestTopN.value;
    }
    els.backtestTopN.value = "1";
    els.backtestTopN.disabled = true;
    els.backtestTopN.title = exactNumbers
      ? "指定号码组每期只有一个投注目标，实际每期 1 注。"
      : "形态事件单项每期只有一个判断目标，实际每期 1 注。";
  } else {
    if (els.backtestTopN.disabled && els.backtestTopN.dataset.previousValue) {
      els.backtestTopN.value = els.backtestTopN.dataset.previousValue;
    }
    delete els.backtestTopN.dataset.previousValue;
    els.backtestTopN.disabled = false;
    els.backtestTopN.title = "";
  }
}

function syncMartingaleModeControls() {
  if (els.martingaleModeGroup) {
    for (const button of els.martingaleModeGroup.querySelectorAll("[data-martingale-mode]")) {
      button.classList.toggle("active", button.dataset.martingaleMode === state.martingaleMode);
    }
  }
  if (els.martingalePlayGroup) {
    for (const button of els.martingalePlayGroup.querySelectorAll("[data-pick-count]")) {
      const pickCount = Number(button.dataset.pickCount);
      const oddsAvailable = Boolean(currentMartingaleOddsMap()[pickCount]);
      button.textContent = martingalePlayLabel(pickCount);
      button.disabled = state.martingaleMode === "bonus" && !oddsAvailable;
      button.title = button.disabled ? "当前彩种未配置该特殊球玩法赔率" : "";
      button.classList.toggle("active", pickCount === state.martingalePickCount);
    }
  }
}

function setMartingaleMode(mode) {
  state.martingaleMode = mode === "bonus" ? "bonus" : "main";
  const oddsMap = currentMartingaleOddsMap();
  if (!oddsMap[state.martingalePickCount]) {
    const firstPick = Object.keys(oddsMap).map(Number).sort((a, b) => a - b)[0] || 1;
    state.martingalePickCount = firstPick;
  }
  state.martingaleOddsDirty = false;
  syncMartingaleModeControls();
  syncMartingaleDefaultOdds(true);
  updateMartingaleMeta();
  if (state.martingalePlan) renderMartingalePlan({ silent: true });
}

function setMartingalePickCount(count, options = {}) {
  state.martingalePickCount = Math.max(1, Math.min(8, Number(count) || 3));
  syncMartingaleModeControls();
  syncMartingaleDefaultOdds(options.applyDefaultOdds !== false);
  updateMartingaleMeta();
  if (state.martingalePlan) renderMartingalePlan({ silent: true });
}

function updateMartingaleMeta() {
  if (!els.martingaleGameMeta) return;
  const game = state.currentGame || {};
  const pickCount = state.martingalePickCount;
  const probability = pickHitProbability(pickCount, state.martingaleMode);
  const fairOdds = probability > 0 ? 1 / probability : 0;
  const odds = parseNumberInput(els.martingaleOdds, 0);
  const ev = probability > 0 && odds > 0 ? probability * odds - 1 : null;
  const defaultOdds = currentMartingaleDefaultOdds();
  const playLabel = martingalePlayLabel(pickCount);
  els.martingaleGameMeta.textContent =
    probability > 0
      ? `${game.shortName || "--"} · ${playLabel} · 理论 ${fmtPct(probability, 4)} · 公平赔率 ${fmtNumber(
          fairOdds,
          2,
        )}`
      : `${game.shortName || "--"} · ${playLabel}`;
  els.martingaleInputHint.textContent =
    ev === null
      ? "--"
      : `${defaultOdds ? `默认赔率 ${fmtNumber(defaultOdds, 2)} · ` : ""}当前赔率期望 ${fmtPct(ev, 2)}，${
          ev >= 0 ? "高于" : "低于"
        }理论公平线`;
}

function readMartingaleInputs() {
  const pickCount = state.martingalePickCount;
  const odds = parseNumberInput(els.martingaleOdds, 0);
  const bankroll = parseNumberInput(els.martingaleBankroll, 0);
  const periods = Math.max(1, Math.min(200, Math.floor(parseNumberInput(els.martingalePeriods, 1))));
  const targetProfit = parseNumberInput(els.martingaleTargetProfit, 0);
  const unit = parseNumberInput(els.martingaleUnit, 0.01);
  const maxStake = parseNumberInput(els.martingaleMaxStake, 0);
  const stopLossInput = parseNumberInput(els.martingaleStopLoss, 0);
  const flatStake = parseNumberInput(els.riskFlatStake, 1);
  const kellyFraction = parseNumberInput(els.riskKellyFraction, 0.25);
  return {
    pickCount,
    mode: state.martingaleMode,
    odds,
    bankroll,
    periods,
    targetProfit,
    unit: unit > 0 ? unit : 0.01,
    maxStake: maxStake > 0 ? maxStake : Infinity,
    stopLoss: stopLossInput > 0 ? stopLossInput : bankroll,
    flatStake,
    kellyFraction,
  };
}

function validateMartingaleInputs(input) {
  if (input.odds <= 1) return "赔率必须大于 1";
  if (input.bankroll <= 0) return "初始本金必须大于 0";
  if (input.targetProfit <= 0) return "目标净利必须大于 0";
  if (input.unit <= 0) return "投注单位必须大于 0";
  if (input.flatStake <= 0) return "预算单注必须大于 0";
  if (input.kellyFraction < 0 || input.kellyFraction > 1) return "Kelly折扣必须在 0 到 1 之间";
  return "";
}

function buildMartingalePlan(input) {
  const probability = pickHitProbability(input.pickCount, input.mode);
  const fairOdds = probability > 0 ? 1 / probability : 0;
  const rows = [];
  let previousLoss = 0;
  let cumulativeStake = 0;
  let maxPlanStake = 0;
  let firstBreak = null;

  for (let period = 1; period <= input.periods; period += 1) {
    const lossBeforeThisPeriod = previousLoss;
    const stake = roundUpToUnit((lossBeforeThisPeriod + input.targetProfit) / (input.odds - 1), input.unit);
    const payout = stake * input.odds;
    const hitNet = stake * (input.odds - 1) - lossBeforeThisPeriod;
    cumulativeStake += stake;
    previousLoss = lossBeforeThisPeriod + stake;
    maxPlanStake = Math.max(maxPlanStake, stake);
    const remainingBankroll = input.bankroll - cumulativeStake;
    const issues = [];
    if (stake > input.maxStake) issues.push("超单注");
    if (cumulativeStake > input.stopLoss) issues.push("超止损");
    if (cumulativeStake > input.bankroll) issues.push("本金不足");
    if (!firstBreak && issues.length) {
      firstBreak = { period, reason: issues.join(" / ") };
    }
    rows.push({
      period,
      stake,
      cumulativeStake,
      payout,
      hitNet,
      remainingBankroll,
      status: issues.length ? issues.join(" / ") : "可执行",
      level: issues.includes("本金不足") || issues.includes("超止损") ? "danger" : issues.length ? "warn" : "ok",
    });
  }

  return {
    input,
    rows,
    probability,
    fairOdds,
    ev: probability > 0 ? probability * input.odds - 1 : 0,
    planHitProbability: probability > 0 ? 1 - (1 - probability) ** input.periods : 0,
    missAllProbability: probability > 0 ? (1 - probability) ** input.periods : 0,
    totalStake: rows.at(-1)?.cumulativeStake || 0,
    maxPlanStake,
    lastStake: rows.at(-1)?.stake || 0,
    firstBreak,
  };
}

const RISK_BUDGET_SIMULATIONS = 10000;

function profitVariancePerUnit(probability, odds) {
  if (probability <= 0 || odds <= 1) return 0;
  const hitProfit = odds - 1;
  const missProfit = -1;
  const mean = probability * hitProfit + (1 - probability) * missProfit;
  return probability * (hitProfit - mean) ** 2 + (1 - probability) * (missProfit - mean) ** 2;
}

function fullKellyFraction(probability, odds) {
  if (probability <= 0 || odds <= 1) return 0;
  const edge = probability * odds - 1;
  if (edge <= 0) return 0;
  return edge / (odds - 1);
}

function martingaleRowLimitReason(row, input) {
  const issues = [];
  if (row.stake > input.maxStake) issues.push("超单注");
  if (row.cumulativeStake > input.stopLoss) issues.push("超止损");
  if (row.cumulativeStake > input.bankroll) issues.push("本金不足");
  return issues.join(" / ");
}

function martingaleExpectedProfit(plan) {
  const probability = plan.probability;
  const missProbability = 1 - probability;
  let expectedProfit = 0;
  let reachProbability = 1;
  let previousCumulative = 0;

  for (const row of plan.rows) {
    if (martingaleRowLimitReason(row, plan.input)) {
      return expectedProfit - reachProbability * previousCumulative;
    }
    expectedProfit += reachProbability * probability * row.hitNet;
    reachProbability *= missProbability;
    previousCumulative = row.cumulativeStake;
  }

  return expectedProfit - reachProbability * previousCumulative;
}

function martingaleLimitProbability(plan) {
  const missProbability = 1 - plan.probability;
  let reachProbability = 1;
  for (const row of plan.rows) {
    if (martingaleRowLimitReason(row, plan.input)) return reachProbability;
    reachProbability *= missProbability;
  }
  return 0;
}

function martingaleWorstLoss(plan) {
  let previousCumulative = 0;
  for (const row of plan.rows) {
    if (martingaleRowLimitReason(row, plan.input)) return previousCumulative;
    previousCumulative = row.cumulativeStake;
  }
  return previousCumulative;
}

function riskBudgetSeed(input, label) {
  return hashString(
    [
      currentGameKey(),
      label,
      input.mode,
      input.pickCount,
      input.odds,
      input.bankroll,
      input.periods,
      input.targetProfit,
      input.unit,
      Number.isFinite(input.maxStake) ? input.maxStake : "none",
      input.stopLoss,
      input.flatStake,
      input.kellyFraction,
    ].join("|"),
  );
}

function summarizeSimulation(values) {
  if (!values.length) {
    return { mean: 0, p5: 0, p50: 0, p95: 0, min: 0, max: 0 };
  }
  const sorted = [...values].sort((a, b) => a - b);
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  return {
    mean,
    p5: percentile(sorted, 0.05),
    p50: percentile(sorted, 0.5),
    p95: percentile(sorted, 0.95),
    min: sorted[0],
    max: sorted.at(-1),
  };
}

function simulateRiskScenario(input, label, runner) {
  const random = seededRandom(riskBudgetSeed(input, label));
  const profits = [];
  let limited = 0;
  let noStake = 0;
  for (let index = 0; index < RISK_BUDGET_SIMULATIONS; index += 1) {
    const result = runner(random);
    profits.push(Number(result.profit || 0));
    if (result.limited) limited += 1;
    if (result.noStake) noStake += 1;
  }
  return {
    ...summarizeSimulation(profits),
    limitedRate: limited / RISK_BUDGET_SIMULATIONS,
    noStakeRate: noStake / RISK_BUDGET_SIMULATIONS,
  };
}

function runFixedStakeBudget(input, probability, random) {
  let profit = 0;
  for (let period = 1; period <= input.periods; period += 1) {
    const currentBankroll = input.bankroll + profit;
    const currentLoss = Math.max(0, -profit);
    if (
      input.flatStake > input.maxStake ||
      input.flatStake > currentBankroll ||
      currentLoss + input.flatStake > input.stopLoss
    ) {
      return { profit, limited: true };
    }
    profit += random() < probability ? input.flatStake * (input.odds - 1) : -input.flatStake;
  }
  return { profit, limited: false };
}

function runKellyBudget(input, probability, kellyFull, random) {
  if (kellyFull <= 0 || input.kellyFraction <= 0) {
    return { profit: 0, limited: false, noStake: true };
  }

  let profit = 0;
  for (let period = 1; period <= input.periods; period += 1) {
    const currentBankroll = input.bankroll + profit;
    const rawStake = currentBankroll * kellyFull * input.kellyFraction;
    const cappedStake = Number.isFinite(input.maxStake) ? Math.min(rawStake, input.maxStake) : rawStake;
    const stake = roundDownToUnit(cappedStake, input.unit);
    const currentLoss = Math.max(0, -profit);
    if (stake <= 0) return { profit, limited: false, noStake: true };
    if (stake > currentBankroll || currentLoss + stake > input.stopLoss) {
      return { profit, limited: true };
    }
    profit += random() < probability ? stake * (input.odds - 1) : -stake;
  }
  return { profit, limited: false };
}

function runMartingaleBudget(plan, random) {
  let previousCumulative = 0;
  for (const row of plan.rows) {
    if (martingaleRowLimitReason(row, plan.input)) {
      return { profit: -previousCumulative, limited: true };
    }
    if (random() < plan.probability) {
      return { profit: row.hitNet, limited: false };
    }
    previousCumulative = row.cumulativeStake;
  }
  return { profit: -previousCumulative, limited: false };
}

function buildRiskBudget(plan) {
  const input = plan.input;
  const probability = plan.probability;
  const ev = plan.ev;
  const kellyFull = fullKellyFraction(probability, input.odds);
  const kellyStake = roundDownToUnit(input.bankroll * kellyFull * input.kellyFraction, input.unit);
  const fixed = simulateRiskScenario(input, "fixed", (random) => runFixedStakeBudget(input, probability, random));
  const kelly = simulateRiskScenario(input, "kelly", (random) => runKellyBudget(input, probability, kellyFull, random));
  const chase = simulateRiskScenario(input, "martingale", (random) => runMartingaleBudget(plan, random));
  const planExpected = martingaleExpectedProfit(plan);
  const planLimitRisk = martingaleLimitProbability(plan);
  const planWorstLoss = martingaleWorstLoss(plan);

  return {
    probability,
    breakEvenHitRate: input.odds > 1 ? 1 / input.odds : 0,
    ev,
    variancePerUnit: profitVariancePerUnit(probability, input.odds),
    kellyFull,
    kellyStake,
    kellyFraction: input.kellyFraction,
    planExpected,
    planLimitRisk,
    planWorstLoss,
    fixed,
    kelly,
    chase,
    rows: [
      {
        name: "固定单注",
        stake: `${fmtAmount(input.flatStake, input.unit)} / 期`,
        summary: fixed,
        expected: fixed.mean,
        limitRate: fixed.limitedRate,
      },
      {
        name: "Fractional Kelly",
        stake: kellyStake > 0 ? `${fmtAmount(kellyStake, input.unit)} 起步` : "不下注",
        summary: kelly,
        expected: kelly.mean,
        limitRate: kelly.limitedRate,
      },
      {
        name: "倍投追号",
        stake: `最大 ${fmtAmount(plan.maxPlanStake, input.unit)}`,
        summary: chase,
        expected: planExpected,
        limitRate: planLimitRisk,
      },
    ],
  };
}

function renderMartingaleAlert(plan) {
  if (!els.martingaleAlert) return;
  const messages = [];
  if (plan.ev < 0) {
    messages.push("当前赔率低于理论公平赔率，长期期望为负。");
  }
  if (plan.firstBreak) {
    messages.push(`第 ${plan.firstBreak.period} 期触发：${plan.firstBreak.reason}。`);
  }
  if (state.martingaleMode === "bonus") {
    messages.push("特殊球概率按主号命中率 × 1/特殊号池估算；若官方特殊号规则变化需重新核对。");
  }
  if (!messages.length) {
    messages.push("本计划在设定本金、单注上限和止损线内未触发风险断点。");
  }
  els.martingaleAlert.textContent = messages.join(" ");
  els.martingaleAlert.classList.toggle("hidden", false);
  els.martingaleAlert.classList.toggle("danger", Boolean(plan.firstBreak));
  els.martingaleAlert.classList.toggle("warn", !plan.firstBreak && plan.ev < 0);
}

function resetMartingaleResult() {
  if (!els.martingaleRows) return;
  for (const element of [
    els.martingaleHitProb,
    els.martingaleFairOdds,
    els.martingalePlanHitProb,
    els.martingaleMissAllProb,
    els.martingaleEv,
    els.martingaleOddsGap,
    els.martingaleMaxPlanStake,
    els.martingaleLastStake,
    els.martingaleTotalStake,
    els.martingaleBankrollUsage,
    els.martingaleBreakPoint,
    els.martingaleBreakReason,
    els.riskBudgetBreakEven,
    els.riskBudgetEdge,
    els.riskBudgetKellyFraction,
    els.riskBudgetKellyStake,
    els.riskBudgetFlatExpected,
    els.riskBudgetFlatRange,
    els.riskBudgetPlanExpected,
    els.riskBudgetPlanRisk,
  ]) {
    if (!element) continue;
    element.textContent = "--";
    element.classList?.remove("positive", "negative");
  }
  els.martingaleResultMeta.textContent = "尚未生成";
  els.martingaleAlert.classList.add("hidden");
  els.martingaleRows.innerHTML = '<tr><td colspan="7"><span class="muted">等待生成</span></td></tr>';
  if (els.riskBudgetMeta) els.riskBudgetMeta.textContent = "尚未生成";
  if (els.riskBudgetNote) els.riskBudgetNote.classList.add("hidden");
  if (els.riskBudgetRows) {
    els.riskBudgetRows.innerHTML = '<tr><td colspan="7"><span class="muted">等待生成</span></td></tr>';
  }
}

function riskBudgetClass(value) {
  if (!Number.isFinite(value) || Math.abs(value) < 1e-9) return "";
  return value > 0 ? "positive" : "negative";
}

function riskLimitText(rate) {
  if (!Number.isFinite(rate) || rate <= 0) return "0.00%";
  return fmtPct(rate, 2);
}

function renderRiskBudget(plan) {
  if (!els.riskBudgetRows) return;
  const budget = buildRiskBudget(plan);
  const input = plan.input;
  const edgeVsBreakEven = budget.probability - budget.breakEvenHitRate;
  const fixedExpectedExact = input.flatStake * input.periods * budget.ev;
  const kellyLabel = budget.kellyFull > 0 ? fmtPct(budget.kellyFull, 3) : "0.000%";
  const appliedKelly = budget.kellyFull * input.kellyFraction;

  els.riskBudgetMeta.textContent = `${RISK_BUDGET_SIMULATIONS.toLocaleString("zh-CN")} 次确定性模拟 · ${martingalePlayLabel(
    input.pickCount,
    input.mode,
  )}`;
  els.riskBudgetBreakEven.textContent = fmtPct(budget.breakEvenHitRate, 4);
  els.riskBudgetEdge.textContent = `理论命中 ${edgeVsBreakEven >= 0 ? "高于" : "低于"}盈亏线 ${fmtPct(
    Math.abs(edgeVsBreakEven),
    4,
  )}`;
  els.riskBudgetEdge.classList.toggle("positive", edgeVsBreakEven >= 0);
  els.riskBudgetEdge.classList.toggle("negative", edgeVsBreakEven < 0);
  els.riskBudgetKellyFraction.textContent = kellyLabel;
  els.riskBudgetKellyFraction.classList.toggle("positive", budget.kellyFull > 0);
  els.riskBudgetKellyFraction.classList.toggle("negative", budget.kellyFull <= 0);
  els.riskBudgetKellyStake.textContent =
    budget.kellyStake > 0
      ? `${fmtAmount(budget.kellyStake, input.unit)} / 期 · 折扣后 ${fmtPct(appliedKelly, 3)}`
      : "负期望或折扣为 0，建议不下注";
  els.riskBudgetFlatExpected.textContent = fmtMoney(fixedExpectedExact, decimalsFromStep(input.unit));
  els.riskBudgetFlatExpected.classList.toggle("positive", fixedExpectedExact >= 0);
  els.riskBudgetFlatExpected.classList.toggle("negative", fixedExpectedExact < 0);
  els.riskBudgetFlatRange.textContent = `P5 ${fmtMoney(budget.fixed.p5, decimalsFromStep(input.unit))} / P95 ${fmtMoney(
    budget.fixed.p95,
    decimalsFromStep(input.unit),
  )}`;
  els.riskBudgetPlanExpected.textContent = fmtMoney(budget.planExpected, decimalsFromStep(input.unit));
  els.riskBudgetPlanExpected.classList.toggle("positive", budget.planExpected >= 0);
  els.riskBudgetPlanExpected.classList.toggle("negative", budget.planExpected < 0);
  els.riskBudgetPlanRisk.textContent = `限制触发 ${riskLimitText(budget.planLimitRisk)} · 最坏亏损 ${fmtAmount(
    budget.planWorstLoss,
    input.unit,
  )}`;

  const notes = [];
  if (budget.ev < 0) {
    notes.push("Kelly 在负期望赔率下给出的理性仓位是 0；倍投只能改变盈亏分布，不能把负期望变成正期望。");
  } else {
    notes.push("Kelly 仓位只适用于正期望假设；如果命中率来自小样本回测，应继续折扣或不下注。");
  }
  if (budget.planLimitRisk > 0) {
    notes.push(`当前倍投在约 ${fmtPct(budget.planLimitRisk, 2)} 的路径上会先触发本金、止损或单注上限。`);
  }
  els.riskBudgetNote.textContent = notes.join(" ");
  els.riskBudgetNote.classList.remove("hidden", "warn", "danger");
  if (budget.planLimitRisk > 0) {
    els.riskBudgetNote.classList.add("danger");
  } else if (budget.ev < 0) {
    els.riskBudgetNote.classList.add("warn");
  }

  els.riskBudgetRows.innerHTML = budget.rows
    .map((row) => {
      const summary = row.summary;
      return `<tr>
        <td><strong>${escapeHtml(row.name)}</strong></td>
        <td>${escapeHtml(row.stake)}</td>
        <td class="${riskBudgetClass(row.expected)}">${fmtMoney(row.expected, decimalsFromStep(input.unit))}</td>
        <td class="${riskBudgetClass(summary.p5)}">${fmtMoney(summary.p5, decimalsFromStep(input.unit))}</td>
        <td class="${riskBudgetClass(summary.p50)}">${fmtMoney(summary.p50, decimalsFromStep(input.unit))}</td>
        <td class="${riskBudgetClass(summary.p95)}">${fmtMoney(summary.p95, decimalsFromStep(input.unit))}</td>
        <td>${riskLimitText(row.limitRate)}</td>
      </tr>`;
    })
    .join("");
}

function renderMartingalePlan(options = {}) {
  const input = readMartingaleInputs();
  const error = validateMartingaleInputs(input);
  if (error) {
    if (!options.silent) showToast(error, true);
    return;
  }
  const plan = buildMartingalePlan(input);
  state.martingalePlan = plan;
  const unit = input.unit;
  const bankrollUsage = input.bankroll > 0 ? plan.totalStake / input.bankroll : 0;
  const oddsGap = plan.fairOdds > 0 ? input.odds / plan.fairOdds - 1 : 0;

  els.martingaleHitProb.textContent = fmtPct(plan.probability, 4);
  els.martingaleFairOdds.textContent = `公平赔率 ${fmtNumber(plan.fairOdds, 2)}`;
  els.martingalePlanHitProb.textContent = fmtPct(plan.planHitProbability, 2);
  els.martingaleMissAllProb.textContent = `全挂概率 ${fmtPct(plan.missAllProbability, 2)}`;
  els.martingaleEv.textContent = fmtPct(plan.ev, 2);
  els.martingaleEv.classList.toggle("positive", plan.ev >= 0);
  els.martingaleEv.classList.toggle("negative", plan.ev < 0);
  els.martingaleOddsGap.textContent = `${oddsGap >= 0 ? "高于" : "低于"}公平线 ${fmtPct(Math.abs(oddsGap), 2)}`;
  els.martingaleMaxPlanStake.textContent = fmtAmount(plan.maxPlanStake, unit);
  els.martingaleLastStake.textContent = `末期 ${fmtAmount(plan.lastStake, unit)}`;
  els.martingaleTotalStake.textContent = fmtAmount(plan.totalStake, unit);
  els.martingaleBankrollUsage.textContent = `占本金 ${fmtPct(bankrollUsage, 2)}`;
  els.martingaleBreakPoint.textContent = plan.firstBreak ? `第 ${plan.firstBreak.period} 期` : "无";
  els.martingaleBreakReason.textContent = plan.firstBreak ? plan.firstBreak.reason : "未触发限制";
  els.martingaleResultMeta.textContent = `${martingalePlayLabel(input.pickCount, input.mode)} · ${
    input.periods
  }期 · 赔率 ${fmtNumber(input.odds, 2)}`;
  renderMartingaleAlert(plan);

  els.martingaleRows.innerHTML = plan.rows
    .map(
      (row) => `<tr class="martingale-row ${row.level}">
        <td><strong>${row.period}</strong></td>
        <td class="strong-cell">${fmtAmount(row.stake, unit)}</td>
        <td>${fmtAmount(row.cumulativeStake, unit)}</td>
        <td>${fmtAmount(row.payout, unit)}</td>
        <td class="${row.hitNet >= 0 ? "positive" : "negative"}">${fmtMoney(row.hitNet, decimalsFromStep(unit))}</td>
        <td class="${row.remainingBankroll < 0 ? "negative" : ""}">${fmtAmount(row.remainingBankroll, unit)}</td>
        <td><span class="martingale-status ${row.level}">${escapeHtml(row.status)}</span></td>
      </tr>`,
    )
    .join("");
  renderRiskBudget(plan);
}

function selectGame(key) {
  if (state.loading) {
    if (els.gameSelect && state.currentGame) {
      els.gameSelect.value = state.currentGame.key;
    }
    return;
  }
  state.currentGame = state.games.find((game) => game.key === key) || state.currentGame;
  if (!state.currentGame) return;
  els.gameSelect.value = state.currentGame.key;
  localStorage.setItem("keno.currentGame", state.currentGame.key);
  resetPageState();
  updateGameUi();
  refreshCurrentView();
}

function updateGameUi() {
  const game = state.currentGame;
  if (!game) return;
  els.gameSubtitle.textContent = `BC.Game ${game.lotteryId} · ${game.shortName}`;
  renderGamePills();
  renderBacktestStrategyOptions();
  syncMartingaleModeControls();
  syncMartingaleDefaultOdds(false);
  updateMartingaleMeta();
  for (const button of document.querySelectorAll(".tab-btn")) {
    const view = button.dataset.view;
    const disabled = !currentGameSupportsView(view);
    button.disabled = disabled;
    button.title = disabled ? `${game.shortName} 当前不开放该工具` : "";
  }
  renderTabState();
  if (!currentGameSupportsView(state.activeView)) {
    state.activeView = "prediction";
    openToolModal("history");
  }
}

async function loadGames() {
  const response = await fetch("/api/games");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  state.games = data.items || [];
  const selected = localStorage.getItem("keno.currentGame") || data.defaultGame || state.games[0]?.key;
  els.gameSelect.innerHTML = state.games
    .map((game) => `<option value="${game.key}">${game.shortName}</option>`)
    .join("");
  els.gameSelect.value = state.games.some((game) => game.key === selected) ? selected : state.games[0]?.key || "";
  state.currentGame = state.games.find((game) => game.key === els.gameSelect.value) || state.games[0] || null;
  updateGameUi();
}

function setLoading(isLoading, label = "") {
  state.loading = isLoading;
  for (const button of [
    els.refreshPageBtn,
    els.syncBtn,
    els.fullSyncBtn,
    els.applyBtn,
    els.resetBtn,
    els.historySearchBtn,
    els.prevPageBtn,
    els.nextPageBtn,
    els.cdeBacktestPrevBtn,
    els.cdeBacktestNextBtn,
    els.runBacktestBtn,
    els.runBacktestScanBtn,
    els.generateMartingaleBtn,
    els.predictionAutoToggleBtn,
    els.predictionAutoRunBtn,
  ]) {
    if (button) button.disabled = isLoading;
  }
  if (els.gameSelect) els.gameSelect.disabled = isLoading;
  updateGameUi();
  for (const button of document.querySelectorAll(".game-pill")) {
    button.disabled = isLoading;
  }
  for (const button of document.querySelectorAll(".bet-delete-btn")) {
    button.disabled = isLoading;
  }
  if (isLoading) {
    els.dataState.textContent = label || "处理中";
  } else {
    renderDataState();
  }
  els.dataState.classList.toggle("live", !isLoading);
  if (!isLoading && state.predictionTracking && els.predictionTrackingRows) {
    renderPredictionTracking();
  }
  if (!isLoading && state.analysis && els.cdeBacktestRows) {
    renderCdeKillBacktest(state.analysis);
  }
}

function renderAllGamesSyncLog(payload) {
  state.lastSync = payload;
  updateSyncGapWarnings(payload);
  const modeLabel = payload.mode === "full" ? "全量同步" : "增量同步";
  const current = payload.currentResult;
  const currentLabel = current?.game?.shortName || payload.game?.shortName || "";
  const currentRows = Number(current?.newRows || 0);
  const newRows = Number(payload.newRows || 0);
  const bcRows = Number(payload.bcNewRows || 0);
  const etiposRows = Number(payload.etiposNewRows || 0);
  const settledPredictions = Number(payload.settledPredictions || 0);
  els.lastSyncSummary.textContent = `全彩种${modeLabel} · 当前优先 ${currentLabel} +${currentRows} 期 · 总新增 ${newRows} 期 · ${payload.successCount}/${payload.totalCount} 成功`;
  els.lastSyncTime.textContent = fmtDate(payload.generatedAt);
  els.lastBcRows.textContent = bcRows.toLocaleString("zh-CN");
  els.lastEtiposRows.textContent = etiposRows.toLocaleString("zh-CN");
  if (els.lastSettledPredictions) {
    els.lastSettledPredictions.textContent = settledPredictions.toLocaleString("zh-CN");
  }

  const warnings = [];
  if (payload.possibleGapGames?.length) {
    warnings.push(`这些彩种本次增量未命中已有记录，建议全量确认：${payload.possibleGapGames.join("、")}。`);
  }
  if (payload.integrityIssueGames?.length) {
    warnings.push(`历史数据未和 BC 对齐：${payload.integrityIssueGames.join("、")}。`);
  }
  if (payload.errors?.length) {
    warnings.push(`部分彩种同步失败：${payload.errors.map((item) => `${item.shortName}: ${item.error}`).join("；")}`);
  }
  const hasWarning = warnings.length > 0;
  const panel = document.querySelector("#syncLogPanel");
  panel?.classList.toggle("has-warning", hasWarning);
  if (hasWarning) {
    els.lastSyncError.textContent = warnings.join(" ");
    els.lastSyncError.classList.remove("hidden");
    els.lastSyncError.classList.remove("info");
  } else {
    els.lastSyncError.textContent = "全彩种同步完成，当前彩种已优先刷新。";
    els.lastSyncError.classList.remove("hidden");
    els.lastSyncError.classList.add("info");
  }
  renderDataState();
}

function allGamesSyncToastText(payload) {
  const changedGames = (payload.results || [])
    .map((item) => ({
      label: item?.game?.shortName || item?.shortName || item?.game?.key || "未知彩种",
      newRows: Number(item?.newRows || 0),
    }))
    .filter((item) => item.newRows > 0);
  const successText = `${payload.successCount || 0}/${payload.totalCount || 0} 成功`;
  if (!changedGames.length) {
    return `全彩种同步完成：无新增开奖号，${successText}`;
  }
  const detailText = changedGames
    .map((item) => `${item.label}新增${item.newRows.toLocaleString("zh-CN")}期开奖号`)
    .join("；");
  return `全彩种同步完成：${detailText}，${successText}`;
}

function renderSyncLog(payload) {
  if (!payload) return;
  if (payload.allGames) {
    renderAllGamesSyncLog(payload);
    return;
  }
  state.lastSync = payload;
  updateSyncGapWarnings(payload);
  const gameLabel = payload.game?.shortName || state.currentGame?.shortName || "";
  const modeLabel = payload.mode === "full" ? "全量同步" : "增量同步";
  const newRows = Number(payload.newRows || 0);
  const bcRows = Number(payload.bcNewRows || 0);
  const etiposRows = Number(payload.etiposNewRows || 0);
  const settledPredictions = Number(payload.settledPredictions || 0);
  const syncMeta = payload.syncMeta || payload.meta || {};
  const pageText = syncMeta.pagesFetched ? ` · 抓取 ${syncMeta.pagesFetched} 页` : "";
  els.lastSyncSummary.textContent = `${gameLabel ? `${gameLabel} · ` : ""}${modeLabel} · 新增 ${newRows} 期 · 本地 ${payload.writtenRows || "--"} 期${pageText}`;
  els.lastSyncTime.textContent = fmtDate(payload.generatedAt);
  els.lastBcRows.textContent = bcRows.toLocaleString("zh-CN");
  els.lastEtiposRows.textContent = etiposRows.toLocaleString("zh-CN");
  if (els.lastSettledPredictions) {
    els.lastSettledPredictions.textContent = settledPredictions.toLocaleString("zh-CN");
  }

  const warnings = [];
  let noticeLevel = "warning";
  const integrity = payload.dataIntegrity || syncMeta.dataIntegrity;
  if (integrity?.status === "missing") {
    warnings.push(
      `历史数据未和 BC 对齐：本地少 ${Number(integrity.missingVsBc || 0).toLocaleString("zh-CN")} 期。`,
    );
  } else if (integrity?.status === "behind_latest") {
    warnings.push("历史数据最新期落后于 BC，请继续同步。");
  }
  if (syncMeta.possibleGap || payload.possibleGap) {
    const oldestFetched = fmtDate(syncMeta.oldestFetchedUtc || payload.oldestFetchedUtc);
    const newestExisting = fmtDate(syncMeta.newestExistingUtc || payload.newestExistingUtc);
    warnings.push(
      `本次增量同步未命中本地已有记录：抓取 ${syncMeta.pagesFetched || "--"} 页，最旧抓取 ${oldestFetched}，本地原最新 ${newestExisting}。建议执行全量同步确认。`,
    );
  } else if (syncMeta.catchUpTriggered) {
    noticeLevel = "info";
    warnings.push(
      `已自动追页保护：超过默认 ${syncMeta.maxPages || "--"} 页后继续抓取，最终在 ${syncMeta.pagesFetched || "--"} 页内命中已有记录。`,
    );
  }

  const etiposError = payload.etiposMeta?.error;
  if (etiposError) {
    warnings.push(`官网补齐错误：${etiposError}`);
  } else if (payload.etiposMeta?.status === "not_implemented") {
    warnings.push(payload.etiposMeta.message || "该彩种官网补历史抓取暂未启用，本次使用 BC.Game 历史");
  }

  if (warnings.length) {
    document.querySelector("#syncLogPanel")?.classList.toggle("has-warning", noticeLevel !== "info");
    els.lastSyncError.textContent = warnings.join(" ");
    els.lastSyncError.classList.remove("hidden");
    els.lastSyncError.classList.toggle("info", noticeLevel === "info");
  } else {
    document.querySelector("#syncLogPanel")?.classList.remove("has-warning");
    els.lastSyncError.textContent = "";
    els.lastSyncError.classList.add("hidden");
    els.lastSyncError.classList.remove("info");
  }
  renderDataState();
}

function renderPredictionLoading() {
  const panel = normalizePredictionPanel();
  if (els.predictionTitle) {
    els.predictionTitle.textContent = predictionPanelLabel(panel);
  }
  els.predictionWindow.textContent = "预测计算中";
  els.predictionMethod.textContent =
    panel === PREDICTION_PANEL_G
      ? "读取C/D/E候选票并生成G杀号后预测票"
      : panel === PREDICTION_PANEL_F
      ? "读取A/B/C/D/E排除链路并生成F误杀召回票"
      : panel === PREDICTION_PANEL_E
      ? "读取C/D四码票并生成CD杀号4码票"
      : panel === PREDICTION_PANEL_D
      ? "读取A/B/C候选号并生成ABC杀号4码票"
      : panel === PREDICTION_PANEL_C
        ? "读取A/B核心号并生成4码结构票"
        : panel === PREDICTION_PANEL_B
          ? "读取面板A规则并排除A候选号"
          : "读取最新开奖并生成策略候选";
  const showKillPanel = [PREDICTION_PANEL_B, PREDICTION_PANEL_D, PREDICTION_PANEL_E, PREDICTION_PANEL_F, PREDICTION_PANEL_G].includes(panel);
  if (els.predictionKillPanel) {
    els.predictionKillPanel.classList.toggle("hidden", !showKillPanel);
  }
  if (els.predictionKillLabel) {
    els.predictionKillLabel.textContent =
      panel === PREDICTION_PANEL_G
        ? "CDE候选杀号池"
        : panel === PREDICTION_PANEL_F
        ? "ABCDE误杀候选池"
        : panel === PREDICTION_PANEL_E
          ? "CD杀号"
          : panel === PREDICTION_PANEL_D
            ? "ABC/C杀号"
            : "面板A杀号";
  }
  if (els.predictionKillSummary) {
    els.predictionKillSummary.textContent = showKillPanel ? "计算排除号..." : "--";
  }
  if (els.predictionKillNumbers) {
    els.predictionKillNumbers.innerHTML = showKillPanel
      ? `<span class="muted">${
          panel === PREDICTION_PANEL_G
            ? "等待C/D/E候选杀号池"
            : panel === PREDICTION_PANEL_F
            ? "等待ABCDE误杀候选池"
            : panel === PREDICTION_PANEL_E
              ? "等待CD杀号"
              : panel === PREDICTION_PANEL_D
                ? "等待ABC/C杀号"
                : "等待面板A杀号"
        }</span>`
      : "";
  }
  if (els.predictionStrategyHealth) {
    els.predictionStrategyHealth.innerHTML = '<article class="strategy-health-card empty"><span class="muted">读取追踪表现...</span></article>';
  }
  if (els.predictionStrategyTickets) {
    els.predictionStrategyTickets.innerHTML = '<article class="prediction-ticket-card"><span class="loading-inline">生成候选票...</span></article>';
  }
}

async function loadPrediction(options = {}) {
  const panel = predictionPanelForOptions(options);
  const slot = predictionPanelState(panel);
  setPredictionPanel(panel);
  if (!currentGameSupportsPredictions()) {
    updatePredictionPanelState({ prediction: null, predictionTracking: null }, panel);
    openToolModal("history");
    return;
  }
  setLoading(true, "预测中");
  if (!options.preserve || !slot.prediction) {
    renderPredictionLoading();
  }
  try {
    const params = new URLSearchParams({ game: currentGameKey(), panel });
    const url = `/api/predictions?${params.toString()}`;
    const cached = options.force ? null : cacheGet(url);
    if (cached) {
      if (!payloadMatchesCurrentGame(cached)) return;
      updatePredictionPanelState(
        {
          prediction: cached,
          predictionTracking: isPaginatedPredictionTrackingPayload(cached.predictionTracking)
            ? cached.predictionTracking
            : slot.predictionTracking,
        },
        panel,
      );
      if (state.predictionPanel === panel) {
        renderPredictionPage();
      }
      loadPredictionTracking({ silent: true, panel, refreshAdjacent: true });
      return;
    }
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!payloadMatchesCurrentGame(data)) return;
    updatePredictionPanelState(
      {
        prediction: data,
        predictionTracking: isPaginatedPredictionTrackingPayload(data.predictionTracking)
          ? data.predictionTracking
          : slot.predictionTracking,
      },
      panel,
    );
    if (isPaginatedPredictionTrackingPayload(data.predictionTracking) && state.predictionPanel === panel) {
      renderPredictionTracking();
    }
    cacheSet(url, data);
    if (state.predictionPanel === panel) {
      renderPredictionPage();
    }
    loadPredictionTracking({ silent: true, panel, refreshAdjacent: true });
  } catch (error) {
    showToast(`加载预测失败：${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

async function loadPredictionTracking(options = {}) {
  if (!currentGameSupportsPredictionTracking() || !els.predictionTrackingStats) return null;
  const panel = predictionPanelForOptions(options);
  const slot = predictionPanelState(panel);
  const refreshAdjacent = options.refreshAdjacent === true;
  try {
    const params = new URLSearchParams({
      game: currentGameKey(),
      panel,
      status: slot.predictionTrackingStatus || "all",
      page: String(slot.predictionTrackingPage || 1),
      pageSize: "20",
    });
    if (options.autoSync !== true) {
      params.set("autoSync", "0");
    }
    const response = await fetch(`/api/prediction-tracking?${params.toString()}`);
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    if (!payloadMatchesCurrentGame(data)) return null;
    const updates = {
      predictionTracking: data,
      predictionTrackingPage: Number(data.page || 1),
    };
    if (refreshAdjacent) {
      Object.assign(updates, {
        adjacentStats: null,
        adjacentHits: null,
        adjacentHitPage: 1,
      });
    }
    updatePredictionPanelState(updates, panel);
    if (state.predictionPanel === panel) {
      renderPredictionTracking();
    }
    if (refreshAdjacent) {
      loadAdjacentStats({ silent: true, panel });
    }
    if (options.refreshAutoStatus !== false) {
      loadPredictionAutoStatus({ silent: true, refreshTracking: false });
    }
    return data;
  } catch (error) {
    if (!options.silent) {
      showToast(`加载预测追踪失败：${error.message}`, true);
    }
    return null;
  }
}

async function loadAdjacentStats(options = {}) {
  if (!currentGameSupportsPredictionTracking() || !els.predictionAdjacentStats) return null;
  const panel = predictionPanelForOptions(options);
  try {
    const params = new URLSearchParams({ game: currentGameKey(), panel });
    const response = await fetch(`/api/adjacent-derived-stats?${params.toString()}`);
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    if (!payloadMatchesCurrentGame(data)) return null;
    updatePredictionPanelState(
      {
        adjacentStats: data.adjacentStats || null,
        adjacentHits: null,
        adjacentHitPage: 1,
      },
      panel,
    );
    if (state.predictionPanel === panel) {
      renderPredictionAdjacentStats();
    }
    return data;
  } catch (error) {
    if (!options.silent) {
      showToast(`加载临码派生统计失败：${error.message}`, true);
    }
    return null;
  }
}

async function loadAdjacentHits(options = {}) {
  if (!currentGameSupportsPredictionTracking() || !els.predictionAdjacentStats) return null;
  const panel = predictionPanelForOptions(options);
  const slot = predictionPanelState(panel);
  try {
    const params = new URLSearchParams({
      game: currentGameKey(),
      panel,
      q: slot.adjacentHitQuery || "",
      groupBy: "record",
      page: String(slot.adjacentHitPage || 1),
      pageSize: "20",
    });
    const response = await fetch(`/api/adjacent-derived-hits?${params.toString()}`);
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    if (!payloadMatchesCurrentGame(data)) return null;
    updatePredictionPanelState(
      {
        adjacentHits: data,
        adjacentHitPage: Number(data.page || 1),
      },
      panel,
    );
    if (state.predictionPanel === panel) {
      renderPredictionAdjacentStats();
    }
    return data;
  } catch (error) {
    if (!options.silent) {
      showToast(`加载派生中奖查询失败：${error.message}`, true);
    }
    return null;
  }
}

async function loadPredictionAutoStatus(options = {}) {
  if (!els.predictionAutoStatus) return null;
  try {
    const response = await fetch("/api/prediction-auto");
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
    const previousCompletedAt = state.predictionAutoLastCompletedAt || predictionAutoCompletedAt(state.predictionAuto);
    const completedAt = predictionAutoCompletedAt(data);
    state.predictionAuto = data;
    if (!state.predictionAutoLastCompletedAt && completedAt) {
      state.predictionAutoLastCompletedAt = completedAt;
    }
    renderPredictionAutoStatus();
    if (
      options.refreshTracking &&
      completedAt &&
      completedAt !== previousCompletedAt &&
      !state.loading &&
      !state.predictionTrackingRefreshInFlight &&
      isPredictionMainViewActive()
    ) {
      state.predictionAutoLastCompletedAt = completedAt;
      state.predictionTrackingRefreshInFlight = true;
      try {
        await loadPredictionTracking({
          silent: true,
          panel: state.predictionPanel,
          refreshAdjacent: true,
          refreshAutoStatus: false,
        });
      } finally {
        state.predictionTrackingRefreshInFlight = false;
      }
    } else if (completedAt) {
      const shouldHoldRefresh =
        options.refreshTracking &&
        previousCompletedAt &&
        completedAt !== previousCompletedAt &&
        (state.loading || state.predictionTrackingRefreshInFlight || !isPredictionMainViewActive());
      if (!shouldHoldRefresh) {
        state.predictionAutoLastCompletedAt = completedAt;
      }
    }
    return data;
  } catch (error) {
    if (!options.silent) showToast(`读取追踪状态失败：${error.message}`, true);
    return null;
  }
}

function predictionAutoCompletedAt(data) {
  return String(data?.lastCompletedAt || "");
}

function isPredictionMainViewActive() {
  return !state.activeModal && ["prediction", "predictionB", "predictionC", "predictionD", "predictionE", "predictionF", "predictionG"].includes(state.activeView);
}

function startPredictionAutoPolling(delayMs = 12000) {
  if (!els.predictionAutoStatus) return;
  if (state.predictionAutoPollTimer) {
    window.clearTimeout(state.predictionAutoPollTimer);
  }
  state.predictionAutoPollTimer = window.setTimeout(async () => {
    state.predictionAutoPollTimer = null;
    await loadPredictionAutoStatus({ silent: true, refreshTracking: true });
    startPredictionAutoPolling();
  }, delayMs);
}

async function updatePredictionAuto(action) {
  setLoading(true, action === "stop" ? "停止追踪" : action === "runOnce" ? "同步一次" : "追踪处理中");
  try {
    const response = await fetch("/api/prediction-auto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
    state.predictionAuto = data;
    const completedAt = predictionAutoCompletedAt(data);
    if (completedAt) state.predictionAutoLastCompletedAt = completedAt;
    renderPredictionAutoStatus();
    if (action === "runOnce") {
      await loadPredictionTracking({ silent: true, panel: state.predictionPanel, refreshAdjacent: true });
    }
    showToast(
      action === "start"
        ? "追踪已启动"
        : action === "stop"
          ? "追踪已停止"
          : "已立即同步一次",
    );
  } catch (error) {
    showToast(`追踪操作失败：${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

async function loadAnalysis(options = {}) {
  if (!currentGameSupportsAnalysis()) {
    showToast("C/D/E/F/G 回测当前只支持西班牙和波兰", true);
    return;
  }
  if (!options.keepPage) {
    state.cdeBacktestPage = 1;
  }
  setLoading(true, "C/D/E/F/G回测中");
  try {
    const url = `/api/cde-kill-backtest?${buildAnalysisQuery().toString()}`;
    const cached = options.force ? null : cacheGet(url);
    if (cached) {
      if (!payloadMatchesCurrentGame(cached)) return;
      state.analysis = cached;
      renderAnalysis();
      return;
    }
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!payloadMatchesCurrentGame(data)) return;
    state.analysis = data;
    cacheSet(url, data);
    renderAnalysis();
  } catch (error) {
    showToast(`加载C/D/E/F/G回测失败：${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

async function loadHistory() {
  setLoading(true, "查询中");
  try {
    const response = await fetch(`/api/draws?${buildHistoryQuery().toString()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!payloadMatchesCurrentGame(data)) return;
    state.history = data;
    renderHistory();
  } catch (error) {
    showToast(`加载历史失败：${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

async function loadCurrentSummary() {
  const params = new URLSearchParams({
    game: currentGameKey(),
    page: "1",
    pageSize: "10",
    sort: "desc",
  });
  const response = await fetch(`/api/draws?${params.toString()}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  renderSummary(await response.json());
}

function buildBacktestPayload() {
  const selectedStrategy = els.backtestStrategy.value;
  const fixedCondition = selectedStrategy.startsWith("condition_fixed:");
  const shapeCondition = selectedStrategy.startsWith("shape_top_n:");
  const strategy = fixedCondition ? "condition_fixed" : shapeCondition ? "shape_top_n" : selectedStrategy;
  const condition = fixedCondition || shapeCondition ? selectedStrategy.split(":")[1] : "auto";
  const singleTarget = strategy === "exact_numbers" || fixedCondition;
  return {
    game: currentGameKey(),
    strategy,
    params: {
      top_n: singleTarget ? 1 : Number(els.backtestTopN.value || 1),
      miss_threshold: Number(els.backtestMissThreshold.value || 0),
      condition,
      numbers: strategy === "exact_numbers" ? els.backtestNumbers.value : "",
    },
    window: {
      train: Number(els.backtestTrain.value || 10000),
      test: Number(els.backtestTest.value || 1000),
    },
    stake: Number(els.backtestStake.value || 1),
    odds: Number(els.backtestOdds.value || 60),
  };
}

function buildBacktestScanPayload() {
  const payload = buildBacktestPayload();
  payload.scan = {
    topNs: [1, 2, 3, 5],
    missThresholds: [0, 5, 10, 20, 30, Number(els.backtestMissThreshold.value || 0)],
    maxResults: 50,
  };
  return payload;
}

function setBacktestProgress(progress, message) {
  const value = Math.max(0, Math.min(Number(progress || 0), 1));
  els.backtestProgressBar.style.width = `${value * 100}%`;
  els.backtestProgressText.textContent = `${Math.round(value * 100)}% · ${message || "等待"}`;
  els.backtestStatus.textContent = message || "等待";
}

async function runBacktest() {
  if (state.backtestPollTimer) {
    window.clearTimeout(state.backtestPollTimer);
    state.backtestPollTimer = null;
  }
  setLoading(true, "提交回测中");
  setBacktestProgress(0, "提交任务");
  try {
    const response = await fetch("/api/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildBacktestPayload()),
    });
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    if (payload.status === "complete") {
      state.backtest = payload.result || payload;
      renderBacktestResult(state.backtest);
      setBacktestProgress(1, payload.cacheHit ? "读取缓存结果" : "回测完成");
      setLoading(false);
      return;
    }
    state.backtest = payload;
    setBacktestProgress(payload.progress || 0, payload.message || "回测已启动");
    pollBacktestStatus();
  } catch (error) {
    setLoading(false);
    setBacktestProgress(0, "回测失败");
    showToast(`回测失败：${error.message}`, true);
  }
}

async function runBacktestScan() {
  if (state.backtestScanPollTimer) {
    window.clearTimeout(state.backtestScanPollTimer);
    state.backtestScanPollTimer = null;
  }
  setLoading(true, "自动扫描中");
  setBacktestProgress(0, "提交自动扫描");
  try {
    const response = await fetch("/api/backtest/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildBacktestScanPayload()),
    });
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    if (payload.status === "complete") {
      state.backtestScan = payload.result || payload;
      renderBacktestScanResult(state.backtestScan);
      setBacktestProgress(1, payload.cacheHit ? "读取扫描缓存" : "自动扫描完成");
      setLoading(false);
      return;
    }
    state.backtestScan = payload;
    setBacktestProgress(payload.progress || 0, payload.message || "自动扫描已启动");
    pollBacktestScanStatus();
  } catch (error) {
    setLoading(false);
    setBacktestProgress(0, "自动扫描失败");
    showToast(`自动扫描失败：${error.message}`, true);
  }
}

async function pollBacktestStatus() {
  try {
    const response = await fetch("/api/backtest/status");
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    state.backtest = payload.result || payload;
    setBacktestProgress(payload.progress || 0, payload.message || payload.status || "回测中");
    if (payload.status === "complete") {
      renderBacktestResult(payload.result || payload);
      setLoading(false);
      showToast("回测完成");
      return;
    }
    if (payload.status === "failed") {
      setLoading(false);
      showToast(`回测失败：${payload.error || "未知错误"}`, true);
      return;
    }
    state.backtestPollTimer = window.setTimeout(pollBacktestStatus, 900);
  } catch (error) {
    setLoading(false);
    showToast(`读取回测状态失败：${error.message}`, true);
  }
}

async function pollBacktestScanStatus() {
  try {
    const response = await fetch("/api/backtest/scan/status");
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    state.backtestScan = payload.result || payload;
    setBacktestProgress(payload.progress || 0, payload.message || payload.status || "自动扫描中");
    if (payload.status === "complete") {
      renderBacktestScanResult(payload.result || payload);
      setLoading(false);
      showToast("自动扫描完成");
      return;
    }
    if (payload.status === "failed") {
      setLoading(false);
      showToast(`自动扫描失败：${payload.error || "未知错误"}`, true);
      return;
    }
    state.backtestScanPollTimer = window.setTimeout(pollBacktestScanStatus, 900);
  } catch (error) {
    setLoading(false);
    showToast(`读取自动扫描状态失败：${error.message}`, true);
  }
}

async function loadBacktestStatus() {
  if (!currentGameSupportsBacktest()) {
    openToolModal("history");
    return;
  }
  if (state.backtestPollTimer) {
    window.clearTimeout(state.backtestPollTimer);
    state.backtestPollTimer = null;
  }
  setLoading(true, "读取回测中");
  let keepLoading = false;
  try {
    const response = await fetch("/api/backtest/status");
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    state.backtest = payload.result || payload;
    setBacktestProgress(payload.progress || 0, payload.message || payload.status || "等待提交");
    if (payload.status === "complete") {
      renderBacktestResult(payload.result || payload);
    } else {
      els.backtestResultPanel.classList.add("hidden");
      if (payload.status === "running") {
        keepLoading = true;
        pollBacktestStatus();
      }
    }
  } catch (error) {
    showToast(`读取回测状态失败：${error.message}`, true);
  } finally {
    if (!keepLoading) setLoading(false);
  }
}

async function syncData(mode) {
  const isFull = mode === "full";
  if (isFull) {
    const ok = window.confirm(
      "全量同步会抓取全部历史数据，预计 1-3 分钟。期间不要重复点击。是否继续？",
    );
    if (!ok) return;
  }

  setLoading(true, isFull ? "全量同步中" : "全彩种同步中");
  try {
    const endpoint = isFull ? "/api/refresh" : "/api/refresh-all";
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode,
        game: currentGameKey(),
        pageSize: 100,
        sleep: 0.25,
      }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    const text = payload.allGames
      ? allGamesSyncToastText(payload)
      : payload.mode === "full"
        ? `全量同步完成：本地 ${payload.writtenRows} 期`
        : `同步完成：新增 ${payload.newRows} 期，BC ${payload.bcNewRows || 0} 期，官网补齐 ${
            payload.etiposNewRows || 0
          } 期，本地 ${payload.writtenRows} 期`;
    const settledText = payload.settledPredictions ? `，结算预测 ${payload.settledPredictions} 条` : "";
    const gapText = payload.possibleGap ? "，增量未命中已有记录，请查看同步日志" : "";
    showToast(`${text}${settledText}${gapText}`);
    renderSyncLog(payload);
    const syncedIntegrity = payload.allGames
      ? payload.results?.find((item) => item.game?.key === currentGameKey())?.dataIntegrity ||
        payload.currentResult?.dataIntegrity
      : payload.dataIntegrity;
    if (syncedIntegrity) state.currentIntegrity = syncedIntegrity;
    clearResponseCache();
    const preservePrediction = false;
    for (const slot of Object.values(state.predictionPanels)) {
      slot.prediction = null;
      slot.predictionTracking = null;
      slot.predictionTrackingPage = 1;
      slot.predictionTrackingStatus = "all";
      slot.adjacentStats = null;
      slot.adjacentHitPage = 1;
      slot.adjacentHitQuery = "";
      slot.adjacentHits = null;
    }
    syncPredictionPanelMirror();
    state.analysis = null;
    state.history = null;
    state.backtest = null;
    await refreshCurrentView({ preserve: Boolean(preservePrediction) });
  } catch (error) {
    showToast(`同步失败：${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

function renderAnalysis() {
  const data = state.analysis;
  if (!data) return;
  state.currentGame = data.game || state.currentGame;
  updateGameUi();
  renderSummary(data);
  renderCdeKillBacktest(data);
}

function cdePanelLabel(panel) {
  if (panel === PREDICTION_PANEL_G) return "G";
  if (panel === PREDICTION_PANEL_F) return "F";
  if (panel === PREDICTION_PANEL_E) return "E";
  if (panel === PREDICTION_PANEL_D) return "D";
  return "C";
}

function cdeNumberBalls(numbers, extraClass = "") {
  const items = (numbers || []).map((number) => Number(number)).filter(Number.isFinite);
  if (!items.length) return '<span class="muted">--</span>';
  return items
    .map((number) => `<span class="prediction-ball compact ${extraClass}"><strong>${number}</strong></span>`)
    .join("");
}

function cdePanelResultCell(result, panel = "") {
  if (!result) return '<span class="muted">--</span>';
  if (panel === PREDICTION_PANEL_F || panel === PREDICTION_PANEL_G) {
    const hit = Number(result.hitCount ?? result.wrongKillCount ?? 0);
    const miss = Number(result.missCount ?? result.rightKillCount ?? 0);
    const pick = Number(result.pickCount ?? result.killCount ?? 0);
    return `<div class="cde-result-cell">
      <strong class="${hit > 0 ? "positive" : "muted"}">中 ${hit}</strong>
      <span>未中 ${miss}</span>
      <small>${pick}码</small>
    </div>`;
  }
  const wrong = Number(result.wrongKillCount || 0);
  const right = Number(result.rightKillCount || 0);
  const kill = Number(result.killCount || 0);
  return `<div class="cde-result-cell">
    <strong class="${wrong > 0 ? "negative" : "positive"}">${wrong}</strong>
    <span>/ ${right}</span>
    <small>杀 ${kill}</small>
  </div>`;
}

function cdeWrongNumbersCell(panels) {
  const parts = [PREDICTION_PANEL_C, PREDICTION_PANEL_D, PREDICTION_PANEL_E].map((panel) => {
    const result = panels?.[panel];
    const numbers = result?.wrongKilledNumbers || [];
    return `<div class="cde-wrong-group">
      <span>${cdePanelLabel(panel)}</span>
      <div>${cdeNumberBalls(numbers, numbers.length ? "kill wrong" : "safe")}</div>
    </div>`;
  });
  const fResult = panels?.[PREDICTION_PANEL_F];
  const fNumbers = fResult?.hitNumbers || fResult?.wrongKilledNumbers || [];
  parts.push(`<div class="cde-wrong-group">
    <span>F中</span>
    <div>${cdeNumberBalls(fNumbers, fNumbers.length ? "hit" : "safe")}</div>
  </div>`);
  const gResult = panels?.[PREDICTION_PANEL_G];
  const gNumbers = gResult?.hitNumbers || gResult?.wrongKilledNumbers || [];
  parts.push(`<div class="cde-wrong-group">
    <span>G中</span>
    <div>${cdeNumberBalls(gNumbers, gNumbers.length ? "hit" : "safe")}</div>
  </div>`);
  return `<div class="cde-wrong-stack">${parts.join("")}</div>`;
}

function renderCdeKillBacktest(data) {
  const summaries = Array.isArray(data.summaries) ? data.summaries : [];
  const bestPanel = data.bestPanel || summaries[0] || null;
  const allRows = Array.isArray(data.items) ? data.items : [];
  const totalRows = allRows.length;
  const totalPage = Math.max(1, Math.ceil(totalRows / CDE_BACKTEST_PAGE_SIZE));
  const currentPage = Math.max(1, Math.min(Number(state.cdeBacktestPage || 1), totalPage));
  state.cdeBacktestPage = currentPage;
  const pageStart = (currentPage - 1) * CDE_BACKTEST_PAGE_SIZE;
  const rows = allRows.slice(pageStart, pageStart + CDE_BACKTEST_PAGE_SIZE);
  const visibleStart = totalRows ? pageStart + 1 : 0;
  const visibleEnd = pageStart + rows.length;
  if (els.cdeBacktestMeta) {
    els.cdeBacktestMeta.textContent = `${data.game?.shortName || "--"} · 最近 ${Number(data.actualRounds || 0).toLocaleString(
      "zh-CN",
    )} 期 · 每期训练 ${Number(data.trainWindow || 0).toLocaleString("zh-CN")} 期 · ${Number(data.elapsedMs || 0).toLocaleString(
      "zh-CN",
    )}ms`;
  }
  if (els.cdeBacktestStats) {
    const bestIsPredictionHit =
      bestPanel?.metricType === "prediction_hit" || bestPanel?.panel === PREDICTION_PANEL_F || bestPanel?.panel === PREDICTION_PANEL_G;
    const bestMetric = bestIsPredictionHit ? bestPanel?.averageHitCount ?? bestPanel?.averageWrongKillCount : bestPanel?.averageWrongKillCount;
    const bestLabel = bestPanel
      ? `${cdePanelLabel(bestPanel.panel)} · ${fmtNumber(Number(bestMetric || 0), 2)}${bestIsPredictionHit ? "中" : "错"}/期`
      : "--";
    const detailLabel = totalRows ? `${Number(visibleStart).toLocaleString("zh-CN")}-${Number(visibleEnd).toLocaleString("zh-CN")}` : "0";
    els.cdeBacktestStats.innerHTML = `
      <article class="accent"><span>回测期数</span><strong>${Number(data.actualRounds || 0).toLocaleString("zh-CN")}</strong><small>请求 ${Number(
        data.window || 0,
      ).toLocaleString("zh-CN")} 期</small></article>
      <article><span>最佳面板</span><strong>${escapeHtml(bestLabel)}</strong><small>C/D/E看错杀，F/G看命中</small></article>
      <article><span>训练窗口</span><strong>${Number(data.trainWindow || 0).toLocaleString("zh-CN")}</strong><small>每期只用开奖前历史</small></article>
      <article><span>明细</span><strong>${detailLabel}</strong><small>共 ${Number(totalRows).toLocaleString("zh-CN")} 行 · 每页 ${CDE_BACKTEST_PAGE_SIZE}</small></article>
    `;
  }
  if (els.cdeBacktestPanelCards) {
    els.cdeBacktestPanelCards.innerHTML = summaries.length
      ? summaries
          .map((summary) => {
            const isPredictionHit = summary.metricType === "prediction_hit" || summary.panel === PREDICTION_PANEL_F || summary.panel === PREDICTION_PANEL_G;
            const wrong = Number(isPredictionHit ? summary.averageHitCount ?? summary.averageWrongKillCount ?? 0 : summary.averageWrongKillCount || 0);
            const right = Number(isPredictionHit ? summary.averageMissCount ?? summary.averageRightKillCount ?? 0 : summary.averageRightKillCount || 0);
            const zeroWrong = Number(isPredictionHit ? summary.zeroHitRate ?? summary.zeroWrongRate ?? 0 : summary.zeroWrongRate || 0);
            const distributionItems = isPredictionHit ? summary.hitDistribution || summary.wrongDistribution || [] : summary.wrongDistribution || [];
            const dist = distributionItems
              .map(
                (item) =>
                  `<span>${Number((isPredictionHit ? item.hitCount : item.wrongKillCount) || 0)}${isPredictionHit ? "中" : "错"}: ${Number(item.rounds || 0).toLocaleString("zh-CN")}期</span>`,
              )
              .join("");
            return `<article class="cde-panel-card">
              <div class="cde-panel-card-title">
                <strong>${cdePanelLabel(summary.panel)} 面板</strong>
                <span>${escapeHtml(summary.label || "")}</span>
              </div>
              <div class="cde-panel-metrics">
                <div><span>${isPredictionHit ? "平均命中" : "平均错杀"}</span><strong class="${
                  isPredictionHit ? (wrong > 0 ? "positive" : "muted") : wrong > 2 ? "negative" : "positive"
                }">${fmtNumber(wrong, 2)}</strong></div>
                <div><span>${isPredictionHit ? "平均未中" : "平均杀对"}</span><strong>${fmtNumber(right, 2)}</strong></div>
                <div><span>${isPredictionHit ? "命中率" : "错杀率"}</span><strong>${fmtPct(Number(isPredictionHit ? summary.hitRate ?? summary.wrongKillRate ?? 0 : summary.wrongKillRate || 0), 2)}</strong></div>
                <div><span>${isPredictionHit ? "0中期数" : "0错期数"}</span><strong>${fmtPct(zeroWrong, 2)}</strong></div>
              </div>
              <div class="cde-distribution">${dist || '<span class="muted">暂无分布</span>'}</div>
            </article>`;
          })
          .join("")
      : '<article class="cde-panel-card"><span class="muted">暂无回测结果</span></article>';
  }
  if (els.cdeBacktestNotes) {
    els.cdeBacktestNotes.textContent = (data.notes || []).join(" ");
  }
  if (els.cdeBacktestRows) {
    els.cdeBacktestRows.innerHTML = rows.length
      ? rows
          .map((item) => {
            const panels = item.panels || {};
            return `<tr>
              <td><strong>${escapeHtml(item.drawEventId || "--")}</strong><div class="muted">${fmtDate(item.drawTimeUtc)}</div></td>
              <td><div class="history-balls compact">${cdeNumberBalls(item.drawNumbers || [], "draw")}</div></td>
              <td>${cdePanelResultCell(panels[PREDICTION_PANEL_C], PREDICTION_PANEL_C)}</td>
              <td>${cdePanelResultCell(panels[PREDICTION_PANEL_D], PREDICTION_PANEL_D)}</td>
              <td>${cdePanelResultCell(panels[PREDICTION_PANEL_E], PREDICTION_PANEL_E)}</td>
              <td>${cdePanelResultCell(panels[PREDICTION_PANEL_F], PREDICTION_PANEL_F)}</td>
              <td>${cdePanelResultCell(panels[PREDICTION_PANEL_G], PREDICTION_PANEL_G)}</td>
              <td>${cdeWrongNumbersCell(panels)}</td>
            </tr>`;
          })
          .join("")
      : '<tr><td colspan="8"><span class="muted">暂无回测明细</span></td></tr>';
  }
  if (els.cdeBacktestPageInfo) {
    els.cdeBacktestPageInfo.textContent = totalRows
      ? `第 ${currentPage}/${totalPage} 页 · ${Number(visibleStart).toLocaleString("zh-CN")}-${Number(visibleEnd).toLocaleString(
          "zh-CN",
        )} / ${Number(totalRows).toLocaleString("zh-CN")} 条`
      : "第 1/1 页 · 0 条";
  }
  if (els.cdeBacktestPrevBtn) {
    els.cdeBacktestPrevBtn.disabled = state.loading || currentPage <= 1;
  }
  if (els.cdeBacktestNextBtn) {
    els.cdeBacktestNextBtn.disabled = state.loading || currentPage >= totalPage;
  }
}

function renderPredictionPage() {
  syncPredictionPanelMirror();
  const data = state.prediction;
  if (!data) return;
  if (els.predictionTitle) {
    els.predictionTitle.textContent = data.panelLabel || predictionPanelLabel();
  }
  state.currentGame = data.game || state.currentGame;
  updateGameUi();
  renderSummary(data);
  renderPredictions(data.predictions);
}

function renderSummary(data) {
  const drawCount = Number(data.drawCount ?? data.total ?? 0);
  state.currentGapAudit = data.gapAudit || null;
  const incomingIntegrity = data.dataIntegrity || data.integrity || null;
  if (incomingIntegrity?.checkedRemote || !state.currentIntegrity?.checkedRemote) {
    state.currentIntegrity = incomingIntegrity;
  }
  els.drawCount.textContent = data.historyFile.exists
    ? (data.historyFile.size / 1024).toFixed(1) + " KB"
    : "--";
  els.drawCount.innerHTML = `${drawCount.toLocaleString("zh-CN")} <span class="status-badge ok">已同步</span>`;
  els.fileModified.textContent = data.historyFile.exists
    ? fmtDate(data.historyFile.modifiedUtc)
    : "无本地文件";
  els.newestDraw.innerHTML = data.newestDraw
    ? `${escapeHtml(data.newestDraw.drawEventId)} · ${fmtDate(data.newestDraw.drawTimeUtc)} <span class="status-badge info">${relativeTime(
        data.newestDraw.drawTimeUtc,
      )}</span>`
    : "--";
  renderDataState();
}

function renderMetrics(data) {
  const three = data.probabilities.threePick;
  const runs = data.probabilities.consecutiveTriples;
  const threePickOdds = Number(three.defaultOdds || currentMainDefaultOddsFor(3) || 0);
  const threePickEv =
    Number.isFinite(Number(three.evAtDefaultOdds)) && three.defaultOdds
      ? Number(three.evAtDefaultOdds)
      : threePickOdds > 0
        ? Number(three.probability || 0) * threePickOdds - 1
        : 0;
  els.p3.textContent = fmtPct(three.probability, 4);
  els.p3Wait.textContent = `平均等待 ${fmtNumber(three.expectedDraws, 1)} 期`;
  if (els.threePickEvLabel) {
    els.threePickEvLabel.textContent = threePickOdds ? `3球 ${fmtNumber(threePickOdds, 2)}x 期望` : "3球赔率期望";
  }
  if (els.threePickEvHint) {
    els.threePickEvHint.textContent = threePickOdds ? "按当前彩种默认赔率" : "未配置默认赔率";
  }
  els.ev60.textContent = fmtPct(threePickEv, 2);
  els.ev60.style.color = threePickEv < 0 ? "var(--risk)" : "var(--brand)";
  els.anyRun.textContent = fmtPct(runs.anyRunProbability, 2);
  els.observedWindows.textContent = fmtNumber(data.triples.observedWindowsPerDraw, 3);
  els.expectedWindows.textContent = `理论 ${fmtNumber(runs.expectedWindowsPerDraw, 3)}`;
  els.tripleCount.textContent = `${data.triples.items.length}/${data.triples.totalItems}`;
}

function renderRunBars(items) {
  const maxDraws = Math.max(1, ...items.map((item) => item.draws));
  els.runBars.innerHTML = "";
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "mini-row";
    row.innerHTML = `
      <div>${item.runLength} 连</div>
      <div class="mini-track"><div class="mini-fill" style="width:${Math.max(
        3,
        (item.draws / maxDraws) * 100,
      )}%"></div></div>
      <div>${item.draws}</div>
    `;
    row.title = `${item.runLength} 连占比 ${fmtPct(item.share, 2)}`;
    els.runBars.appendChild(row);
  }
}

function tripleBadge(numbers) {
  return `<span class="triple-badge">${numbers
    .map((number) => `<span class="ball hot">${number}</span>`)
    .join("")}</span>`;
}

function numberBadge(numbers, extraClass = "hot") {
  return `<span class="triple-badge">${numbers
    .map((number) => `<span class="ball ${extraClass}">${number}</span>`)
    .join("")}</span>`;
}

function historyResultHtml(draw, numbers, highlights, isCancelled) {
  if (isCancelled) {
    return '<span class="history-cancelled">已取消</span>';
  }
  const mainNumbers = numbers
    .map((number) => `<span class="${historyBallClass(highlights.get(number))}">${number}</span>`)
    .join("");
  if (!state.currentGame?.hasBonusBall) return mainNumbers;
  const bonus = Number(draw.bonusBall || 0);
  if (!Number.isFinite(bonus) || bonus <= 0) return mainNumbers;
  return `${mainNumbers}<span class="bonus-separator">+</span><span class="ball bonus" title="特殊号码，可以和主号重复">${bonus}</span>`;
}

function predictionBall(item, extraClass = "") {
  const recentWindow = state.prediction?.predictions?.recentWindow || 0;
  const title = `评分 ${fmtNumber(item.score, 3)}；当前遗漏 ${item.currentMiss}；近${recentWindow}期 ${item.recentHits} 次；命中率 ${fmtPct(item.hitRate, 2)}`;
  return `<span class="prediction-ball ${extraClass}" title="${title}">
    <strong>${item.number}</strong>
    <small>${item.currentMiss}</small>
  </span>`;
}

function bonusPredictionBall(item, extraClass = "") {
  const recentWindow = state.prediction?.predictions?.recentWindow || 0;
  const role = item.roleLabel || (item.rank === 1 ? "主" : "辅");
  const title = `${role}号 · 评分 ${fmtNumber(item.score, 3)}；当前遗漏 ${item.currentMiss}；近${recentWindow}期 ${item.recentHits} 次；命中率 ${fmtPct(item.hitRate, 2)}`;
  return `<span class="prediction-ball ${extraClass} bonus-ranked" title="${escapeHtml(title)}">
    <strong>${item.number}</strong>
    <small>${escapeHtml(role)}</small>
  </span>`;
}

function sortNumberItems(items) {
  return [...(items || [])].sort((a, b) => Number(a.number || 0) - Number(b.number || 0));
}

function ticketNumberBalls(ticket) {
  const mainBalls = (ticket.numbers || [])
    .map((number) => `<span class="prediction-ball compact ticket-main"><strong>${number}</strong></span>`)
    .join("");
  if (!ticket.bonusNumber) return mainBalls;
  return `${mainBalls}<span class="ticket-plus">+</span><span class="prediction-ball compact bonus ticket-bonus"><strong>${ticket.bonusNumber}</strong></span>`;
}

function ticketRecentClass(ticket) {
  const recentHitRate = Number(ticket.recentHitRate || 0);
  const breakEvenHitRate = Number(ticket.breakEvenHitRate || 0);
  const theoreticalHitRate = Number(ticket.theoreticalHitRate || 0);
  if (breakEvenHitRate > 0 && recentHitRate >= breakEvenHitRate) return "ticket-metric-good";
  if (theoreticalHitRate > 0 && recentHitRate >= theoreticalHitRate) return "ticket-metric-warn";
  return "ticket-metric-risk";
}

function ticketRecentTitle(ticket) {
  const recentHitRate = Number(ticket.recentHitRate || 0);
  const breakEvenHitRate = Number(ticket.breakEvenHitRate || 0);
  const theoreticalHitRate = Number(ticket.theoreticalHitRate || 0);
  if (breakEvenHitRate > 0 && recentHitRate >= breakEvenHitRate) {
    return "近窗命中高于赔率盈亏线";
  }
  if (theoreticalHitRate > 0 && recentHitRate >= theoreticalHitRate) {
    return "近窗命中高于理论概率，但仍低于赔率盈亏线";
  }
  return "近窗命中低于理论概率";
}

function ticketExpectedMetric(ev) {
  const className = ev >= 0 ? "positive" : "negative";
  const label = ev >= 0 ? "期望收益" : "理论期望亏损";
  const value = ev >= 0 ? fmtPct(ev, 2) : fmtPct(Math.abs(ev), 2);
  const title =
    ev >= 0
      ? "按理论命中率和当前赔率估算的单注期望收益"
      : "按理论命中率和当前赔率估算的单注期望亏损";
  return { className, label, value, title };
}

function renderPredictionStrategyTickets(tickets = []) {
  if (!els.predictionStrategyTickets) return;
  if (!tickets.length) {
    const method = state.prediction?.predictions?.method || "当前规则没有生成候选票";
    els.predictionStrategyTickets.innerHTML = `<article class="prediction-ticket-card"><span class="muted">${escapeHtml(method)}</span></article>`;
    return;
  }
  els.predictionStrategyTickets.innerHTML = tickets
    .map((ticket, index) => {
      const ev = Number(ticket.evAtOdds || 0);
      const ci = ticket.recentHitRateCi || [0, 0];
      const expectedMetric = ticketExpectedMetric(ev);
      const recentClass = ticketRecentClass(ticket);
      const recentTitle = ticketRecentTitle(ticket);
      const sampleNote = ticket.sampleWarning ? '<div class="ticket-warning">样本偏少，命中率区间仅作参考。</div>' : "";
      const coreNumbers = Array.isArray(ticket.coreNumbers) ? ticket.coreNumbers : [];
      const companionNumbers = Array.isArray(ticket.companionNumbers) ? ticket.companionNumbers : [];
      const panelKey = normalizePredictionPanel(ticket.panel || state.predictionPanel);
      const isPanelFTicket = panelKey === PREDICTION_PANEL_F;
      const isPanelGTicket = panelKey === PREDICTION_PANEL_G;
      const recallNumbers = Array.isArray(ticket.recallNumbers) && ticket.recallNumbers.length
        ? ticket.recallNumbers
        : Array.isArray(ticket.reversalNumbers) && ticket.reversalNumbers.length
          ? ticket.reversalNumbers
          : companionNumbers;
      const sourcePoolCount = Number(ticket.sourcePoolCount || ticket.sourcePoolNumbers?.length || ticket.excludedNumbers?.length || 0);
      const structureNote = ticket.structureType
        ? `<div class="ticket-structure">
            <span>${escapeHtml(ticket.structureLabel || ticket.structureType)}</span>
            ${
              isPanelFTicket
                ? `<span>召回 ${escapeHtml(recallNumbers.join("-") || "--")}</span>
                   <span>候选池 ${sourcePoolCount ? `${sourcePoolCount.toLocaleString("zh-CN")}个` : "--"}</span>`
                : isPanelGTicket
                  ? `<span>杀号池 ${sourcePoolCount ? `${sourcePoolCount.toLocaleString("zh-CN")}个` : "--"}</span>
                     <span>剩余池预测</span>`
                : `<span>核心 ${escapeHtml(coreNumbers.join("-") || "--")}</span>
                   <span>派生 ${escapeHtml(companionNumbers.join("-") || "--")}</span>`
            }
          </div>`
        : "";
      return `<article class="prediction-ticket-card">
        <div class="prediction-card-title">
          <strong>${escapeHtml(ticket.label || "策略候选票")} #${index + 1}</strong>
          <span>${escapeHtml(ticket.mode === "bonus" ? `${ticket.pickCount}+1特殊` : `${ticket.pickCount}球`)} · ${fmtNumber(Number(ticket.odds || 0), 2)}x</span>
        </div>
        <div class="ticket-balls" title="${escapeHtml(ticket.ticketLabel || "")}">${ticketNumberBalls(ticket)}</div>
        ${structureNote}
        <div class="ticket-metric-grid">
          <div><span>理论命中</span><strong>${fmtPct(Number(ticket.theoreticalHitRate || 0), 3)}</strong></div>
          <div><span>盈亏线</span><strong>${fmtPct(Number(ticket.breakEvenHitRate || 0), 3)}</strong></div>
          <div class="${recentClass}" title="${escapeHtml(recentTitle)}"><span>近窗命中</span><strong>${fmtPct(Number(ticket.recentHitRate || 0), 2)}</strong></div>
          <div title="${escapeHtml(expectedMetric.title)}"><span>${expectedMetric.label}</span><strong class="${expectedMetric.className}">${expectedMetric.value}</strong></div>
        </div>
        <div class="ticket-detail">
          <span>近 ${Number(ticket.recentWindow || 0).toLocaleString("zh-CN")} 期 ${Number(ticket.recentHits || 0).toLocaleString("zh-CN")} 中</span>
          <span>区间 ${fmtPct(Number(ci[0] || 0), 2)} - ${fmtPct(Number(ci[1] || 0), 2)}</span>
          <span>遗漏 ${Number(ticket.currentMiss || 0).toLocaleString("zh-CN")} / 最大 ${Number(ticket.maxMiss || 0).toLocaleString("zh-CN")}</span>
          <span>${Number(ticket.chasePeriods || 0)} 期全挂 ${fmtPct(Number(ticket.missAllProbability || 0), 2)}</span>
        </div>
        ${sampleNote}
      </article>`;
    })
    .join("");
}

function strategyHealthLabel(group) {
  const settled = Number(group.settled || 0);
  const hitRate = Number(group.hitRate || 0);
  const theoretical = Number(group.theoreticalHitRate || 0);
  const roi = Number(group.roi || 0);
  const ci = group.hitRateCi || [0, 0];
  const ciHigh = Number(ci[1] || 0);
  if (settled < 50) {
    return { className: "watch", text: "样本不足", detail: `已结算 ${settled.toLocaleString("zh-CN")} 条，先观察` };
  }
  if (theoretical > 0 && ciHigh < theoretical) {
    return { className: "bad", text: "表现偏弱", detail: "置信区间上沿低于理论命中" };
  }
  if (roi < 0 && theoretical > 0 && hitRate < theoretical) {
    return { className: "bad", text: "暂停观察", detail: "ROI 与命中率均低于基准" };
  }
  if (roi > 0 && theoretical > 0 && hitRate >= theoretical) {
    return { className: "good", text: "继续观察", detail: "样本内暂高于理论基准" };
  }
  return { className: "watch", text: "接近随机", detail: "暂未看到稳定偏离" };
}

function renderPredictionStrategyHealth(groups = []) {
  if (!els.predictionStrategyHealth) return;
  const visibleGroups = groups
    .filter((group) => Number(group.total || 0) > 0)
    .sort((a, b) => Number(b.settled || 0) - Number(a.settled || 0) || Number(b.total || 0) - Number(a.total || 0))
    .slice(0, 4);
  if (!visibleGroups.length) {
    els.predictionStrategyHealth.innerHTML =
      '<article class="strategy-health-card empty"><span class="muted">暂无策略表现数据，等待自动追踪结算。</span></article>';
    return;
  }
  els.predictionStrategyHealth.innerHTML = visibleGroups
    .map((group) => {
      const settled = Number(group.settled || 0);
      const pending = Number(group.pending || 0);
      const roi = Number(group.roi || 0);
      const profit = Number(group.profitTotal || 0);
      const ci = group.hitRateCi || [0, 0];
      const health = strategyHealthLabel(group);
      const playLabel = group.mode === "bonus" ? `${group.pickCount}+1特殊球` : `${group.pickCount}球`;
      return `<article class="strategy-health-card ${health.className}">
        <div class="strategy-health-title">
          <div>
            <strong>${escapeHtml(group.strategyLabel || "--")}</strong>
            <span>${escapeHtml(playLabel)} · ${fmtNumber(Number(group.odds || 0), 2)}x</span>
          </div>
          <span class="strategy-health-badge">${escapeHtml(health.text)}</span>
        </div>
        <div class="strategy-health-metrics">
          <div><span>结算/待结算</span><strong>${settled.toLocaleString("zh-CN")} / ${pending.toLocaleString("zh-CN")}</strong></div>
          <div><span>实际/理论</span><strong>${settled ? fmtPct(Number(group.hitRate || 0), 2) : "--"} / ${
            settled ? fmtPct(Number(group.theoreticalHitRate || 0), 3) : "--"
          }</strong></div>
          <div><span>ROI</span><strong class="${roi > 0 ? "positive" : roi < 0 ? "negative" : ""}">${
            settled ? fmtPct(roi, 2) : "--"
          }</strong></div>
        </div>
        <div class="strategy-health-detail">
          <span>${escapeHtml(health.detail)}</span>
          <span>区间 ${settled ? `${fmtPct(Number(ci[0] || 0), 2)} - ${fmtPct(Number(ci[1] || 0), 2)}` : "--"} · 盈亏 ${
            settled ? fmtMoney(profit, 2) : "--"
          }</span>
        </div>
      </article>`;
    })
    .join("");
}

function trackingTicketContent(record) {
  const numbers = Array.isArray(record.numbers) ? record.numbers : [];
  const main = numbers.length ? numberBadge(numbers, "hot") : '<span class="muted">--</span>';
  const bonus = Number(record.bonusNumber || 0);
  if (!bonus) return main;
  return `${main}<span class="bonus-separator">+</span><span class="ball bonus">${bonus}</span>`;
}

function trackingDrawBalls(record, draw) {
  const matched = new Set((record.result?.matchedNumbers || []).map((number) => Number(number)));
  const numbers = Array.isArray(draw?.numbers) ? draw.numbers : [];
  const main = numbers
    .map((number) => {
      const parsed = Number(number);
      const className = matched.has(parsed) ? "ball matched" : "ball";
      return `<span class="${className}">${escapeHtml(String(number))}</span>`;
    })
    .join("");
  const bonus = Number(draw?.bonusBall || 0);
  const predictedBonus = Number(record.bonusNumber || 0);
  const bonusHit = bonus > 0 && predictedBonus > 0 && bonus === predictedBonus;
  const bonusHtml = bonus
    ? `<span class="bonus-separator">+</span><span class="ball bonus${bonusHit ? " matched" : ""}">${bonus}</span>`
    : "";
  return `${main}${bonusHtml}`;
}

function trackingDrawResult(record) {
  if (record.status === "pending") {
    return '<span class="muted">等待同步开奖结果</span>';
  }
  if (record.status === "void") {
    const reason = record.result?.reason || "追踪已作废";
    const normalizedReason =
      reason === "Target draw was skipped after later draws arrived; tracking voided"
        ? "目标期开奖缺失，且后续期次已到达，追踪作废"
        : reason;
    return `<span class="muted">${escapeHtml(normalizedReason)}</span>`;
  }
  const result = record.result;
  const draw = result?.draw;
  if (!draw) return '<span class="muted">无结果明细</span>';
  return `<div class="bet-result">
    <div>${fmtTime(draw.drawTimeUtc)} · ${escapeHtml(result.reason || "")}</div>
    <div class="history-balls compact">${trackingDrawBalls(record, draw)}</div>
  </div>`;
}

function adjacentEvidenceLabel(samples) {
  if (samples < 300) return "仅展示";
  if (samples < 1000) return "趋势观察";
  if (samples < 2000) return "初步比较";
  return "样本较足";
}

function renderAdjacentExample(example) {
  const source = Array.isArray(example.sourceNumbers) ? example.sourceNumbers.join("-") : "--";
  const derived = Array.isArray(example.derivedNumbers) ? example.derivedNumbers.join("-") : "--";
  return `${fmtTime(example.targetDrawTimeUtc)} ${escapeHtml(source)} -> ${escapeHtml(derived)} ${
    example.hit ? "中" : "未中"
  }`;
}

function adjacentNumbersLabel(numbers) {
  return Array.isArray(numbers) && numbers.length ? numbers.join("-") : "--";
}

function renderAdjacentHitPills(examples = [], limit = 4) {
  const hits = Array.isArray(examples) ? examples.slice(0, limit) : [];
  if (!hits.length) return '<span class="muted">暂无中奖</span>';
  return hits
    .map(
      (example) =>
        `<span class="adjacent-hit-pill" title="来源 ${escapeHtml(adjacentNumbersLabel(example.sourceNumbers))} · 开奖 ${escapeHtml(
          adjacentNumbersLabel(example.drawNumbers),
        )}">${fmtTime(example.targetDrawTimeUtc)} ${escapeHtml(adjacentNumbersLabel(example.derivedNumbers))}</span>`,
    )
    .join("");
}

function renderAdjacentSchemeSummary(schemeSummary) {
  const items = Array.isArray(schemeSummary?.items) ? schemeSummary.items : [];
  if (!items.length) return "";
  return `<div class="adjacent-stat-section">
    <div class="adjacent-section-title">整套派生方案</div>
    <div class="adjacent-scheme-grid">${items
      .map((item) => {
        const roi = Number(item.roi || 0);
        const profit = Number(item.profitTotal || 0);
        return `<article class="adjacent-scheme-card">
          <div class="adjacent-stat-title">
            <div>
              <strong>${escapeHtml(item.label || "--")}</strong>
              <span>${Number(item.records || 0).toLocaleString("zh-CN")} 期 · 平均 ${fmtNumber(
                Number(item.avgTicketsPerRecord || 0),
                1,
              )} 注/期</span>
            </div>
            <span class="adjacent-evidence">${Number(item.winningRecords || 0).toLocaleString("zh-CN")} 期中</span>
          </div>
          <div class="adjacent-stat-metrics">
            <div><span>期命中</span><strong>${fmtPct(Number(item.recordHitRate || 0), 2)}</strong><small>${fmtPct(
              Number(item.recordHitRateCi?.[0] || 0),
              2,
            )} - ${fmtPct(Number(item.recordHitRateCi?.[1] || 0), 2)}</small></div>
            <div><span>注命中</span><strong>${Number(item.hitTickets || 0).toLocaleString("zh-CN")}</strong><small>${Number(
              item.ticketTotal || 0,
            ).toLocaleString("zh-CN")} 注</small></div>
            <div><span>投入/返还</span><strong>${fmtNumber(Number(item.stakeTotal || 0), 0)}</strong><small>返还 ${fmtNumber(
              Number(item.payoutTotal || 0),
              0,
            )}</small></div>
            <div><span>ROI</span><strong class="${roi > 0 ? "positive" : roi < 0 ? "negative" : ""}">${fmtPct(
              roi,
              2,
            )}</strong><small class="${profit > 0 ? "positive" : profit < 0 ? "negative" : ""}">利润 ${fmtMoney(
              profit,
              0,
            )}</small></div>
          </div>
        </article>`;
      })
      .join("")}</div>
  </div>`;
}

function renderAdjacentHitLookup() {
  const data = state.adjacentHits;
  const rows = Array.isArray(data?.items) ? data.items : [];
  const page = Number(data?.page || state.adjacentHitPage || 1);
  const totalPage = Number(data?.totalPage || 1);
  return `<div class="adjacent-hit-lookup">
    <div class="adjacent-hit-toolbar">
      <div>
        <div class="adjacent-section-title">派生中奖查询</div>
        <span class="muted">${data ? `共 ${Number(data.total || 0).toLocaleString("zh-CN")} 条 · ${page} / ${totalPage}` : "等待查询"}</span>
      </div>
      <div class="adjacent-hit-controls">
        <input id="adjacentHitQuery" type="search" placeholder="查号码 / 策略 / 时间" value="${escapeHtml(state.adjacentHitQuery)}" />
        <button id="adjacentHitSearchBtn" class="secondary-btn small" type="button">查询</button>
        <button id="adjacentHitPrevBtn" class="secondary-btn small" type="button" ${page <= 1 ? "disabled" : ""}>上一页</button>
        <button id="adjacentHitNextBtn" class="secondary-btn small" type="button" ${page >= totalPage ? "disabled" : ""}>下一页</button>
      </div>
    </div>
    <div class="table-wrap adjacent-hit-table-wrap">
      <table class="adjacent-hit-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>来源</th>
            <th>中奖派生号码</th>
            <th>命中/总注</th>
            <th>开奖</th>
            <th>返还</th>
            <th>整套利润</th>
          </tr>
        </thead>
        <tbody>${
          rows.length
            ? rows
                .map(
                  (row) => `<tr>
                    <td>${fmtTime(row.targetDrawTimeUtc)}</td>
                    <td>${escapeHtml(adjacentNumbersLabel(row.sourceNumbers))}</td>
                    <td><div class="adjacent-hit-derived-list">${(row.derivedTickets || [])
                      .map(
                        (ticket) =>
                          `<span class="adjacent-hit-derived-pill" title="${escapeHtml(ticket.strategyLabel || "")}">${escapeHtml(
                            adjacentNumbersLabel(ticket.derivedNumbers),
                          )}</span>`,
                      )
                      .join("")}</div></td>
                    <td>${Number(row.hitTickets || 0).toLocaleString("zh-CN")} / ${Number(row.stakeTotal || 0).toLocaleString("zh-CN")}</td>
                    <td>${escapeHtml(adjacentNumbersLabel(row.drawNumbers))}</td>
                    <td>${fmtMoney(Number(row.payoutTotal || 0), 2)}</td>
                    <td class="${Number(row.profitTotal || 0) > 0 ? "positive" : ""}">${fmtMoney(Number(row.profitTotal || 0), 2)}</td>
                  </tr>`,
                )
                .join("")
            : '<tr><td colspan="7"><span class="muted">没有匹配的派生中奖记录</span></td></tr>'
        }</tbody>
      </table>
    </div>
  </div>`;
}

function renderPredictionAdjacentStats() {
  const block = els.predictionAdjacentStats;
  if (!block) return;
  const stats = state.adjacentStats;
  const items = Array.isArray(stats?.items) ? stats.items : [];
  const enabled = Boolean(stats?.enabled);
  if (els.predictionAdjacentStatsWrap) {
    els.predictionAdjacentStatsWrap.classList.toggle("hidden", !enabled && !currentGameSupportsPredictionTracking());
  }
  block.classList.toggle("hidden", !enabled);
  if (!enabled) {
    if (els.predictionAdjacentStatsSummary) {
      els.predictionAdjacentStatsSummary.textContent = "等待加载";
    }
    block.innerHTML = currentGameSupportsPredictionTracking()
      ? '<span class="loading-inline">临码派生统计加载中...</span>'
      : "";
    return;
  }
  const ticketItems = items.filter((item) => item.category === "ticket");
  if (els.predictionAdjacentStatsSummary) {
    els.predictionAdjacentStatsSummary.textContent = `来源 ${Number(
      stats.sourceSettledRecords || 0,
    ).toLocaleString("zh-CN")} 条 · 可投注 ${ticketItems.length.toLocaleString("zh-CN")} 项`;
  }
  if (!state.adjacentHits) {
    loadAdjacentHits({ silent: true, panel: state.predictionPanel });
  }
  const renderItem = (item) => {
    const samples = Number(item.samples || 0);
    const hits = Number(item.hits || 0);
    const hitRate = Number(item.hitRate || 0);
    const theory = Number(item.theoreticalHitRate || 0);
    const breakEven = Number(item.breakEvenHitRate || 0);
    const theoryEv = theory * Number(item.odds || 0) - 1;
    const roi = Number(item.roi || 0);
    const profit = Number(item.profitTotal || 0);
    const stake = Number(item.stakeTotal || 0);
    const payout = Number(item.payoutTotal || 0);
    const isTicket = item.category === "ticket";
    const independentSamples = Number(item.independentSamples || samples);
    const sourceHitRecords = Number(item.sourceHitRecords || hits);
    const sourceHitRate = Number(item.sourceHitRate || 0);
    const sourceCi = item.sourceHitRateCi || [0, 0];
    const usesIndependentRate = isTicket && independentSamples !== samples;
    const displayedCi = sourceCi;
    const hitExamples = Array.isArray(item.hitExamples) ? item.hitExamples : [];
    return `<article class="adjacent-stat-card ${isTicket ? "ticket" : "diagnostic"}">
      <div class="adjacent-stat-title">
        <div>
          <strong>${escapeHtml(item.label || "--")}</strong>
          <span>${
            isTicket
              ? `${Number(item.derivedPickCount || 0)}码票 · ${fmtNumber(Number(item.odds || 0), 2)}x`
              : "诊断统计"
          }</span>
        </div>
        <span class="adjacent-evidence">${adjacentEvidenceLabel(independentSamples)}</span>
      </div>
      <div class="adjacent-stat-metrics">
        <div><span>${isTicket ? "中奖" : "命中"}</span><strong>${hits.toLocaleString("zh-CN")}</strong><small>${
          isTicket ? `${samples.toLocaleString("zh-CN")} 注` : `${samples.toLocaleString("zh-CN")} 样本`
        }</small></div>
        <div><span>${usesIndependentRate ? "独立期命中" : "命中率"}</span><strong>${
          usesIndependentRate
            ? independentSamples
              ? fmtPct(sourceHitRate, 2)
              : "--"
            : samples
              ? fmtPct(hitRate, 2)
              : "--"
        }</strong><small>${
          (usesIndependentRate ? independentSamples : samples)
            ? `${fmtPct(Number(displayedCi[0] || 0), 2)} - ${fmtPct(Number(displayedCi[1] || 0), 2)}`
            : "--"
        }</small></div>
        <div><span>${isTicket ? "投入/返还" : "理论基准"}</span><strong>${
          isTicket ? fmtNumber(stake, 0) : "--"
        }</strong><small>${isTicket ? `返还 ${fmtNumber(payout, 0)}` : "诊断项不估算赔率"}</small></div>
        <div><span>ROI</span><strong class="${roi > 0 ? "positive" : roi < 0 ? "negative" : ""}">${
          isTicket && samples ? fmtPct(roi, 2) : "--"
        }</strong><small class="${profit > 0 ? "positive" : profit < 0 ? "negative" : ""}">${
          isTicket && samples ? `利润 ${fmtMoney(profit, 0)}` : "--"
        }</small></div>
      </div>
      ${
        isTicket
          ? `<div class="adjacent-ev-line">理论 EV <strong class="${theoryEv > 0 ? "positive" : theoryEv < 0 ? "negative" : ""}">${fmtPct(
              theoryEv,
              2,
            )}</strong> · 理论命中 ${fmtPct(theory, 3)} · 盈亏线 ${fmtPct(breakEven, 3)}</div>`
          : ""
      }
      ${
        usesIndependentRate
          ? `<div class="adjacent-sample-note">独立 ${independentSamples.toLocaleString("zh-CN")} 期，${sourceHitRecords.toLocaleString("zh-CN")} 期至少中一注。</div>`
          : ""
      }
      <div class="adjacent-hit-strip">${renderAdjacentHitPills(hitExamples)}</div>
    </article>`;
  };
  block.innerHTML = `<div class="adjacent-stat-header">
    <div>
      <h4>临码派生统计</h4>
      <span class="muted">${escapeHtml(stats.note || "")}</span>
    </div>
    <span class="muted">来源 ${Number(stats.sourceSettledRecords || 0).toLocaleString("zh-CN")} 条已结算预测</span>
  </div>
  ${renderAdjacentSchemeSummary(stats.schemeSummary)}
  <div class="adjacent-stat-section">
    <div class="adjacent-section-title">可投注派生票</div>
    <div class="adjacent-stat-grid">${
      ticketItems.length
        ? ticketItems.map(renderItem).join("")
        : '<article class="adjacent-stat-card empty"><span class="muted">暂无可投注派生样本</span></article>'
    }</div>
  </div>
  ${renderAdjacentHitLookup()}
  `;
}

function renderPredictionTracking() {
  const data = state.predictionTracking;
  if (!els.predictionTrackingStats || !els.predictionTrackingRows) return;
  const panelLabel = data?.panelLabel || predictionPanelLabel();
  const summary = data?.summary || {};
  const allSummary = data?.allSummary || summary;
  const settled = Number(summary.settled || 0);
  const cancelled = Number(summary.cancelled || 0);
  const voided = Number(summary.void || 0);
  const ci = summary.hitRateCi || [0, 0];
  const hitRateText = settled ? fmtPct(Number(summary.hitRate || 0), 2) : "--";
  const theoryText = settled ? fmtPct(Number(summary.theoreticalHitRate || 0), 3) : "--";
  const roi = Number(summary.roi || 0);
  const profit = Number(summary.profitTotal || 0);
  const sampleLow = settled > 0 && settled < 30;

  if (els.predictionTrackingMeta) {
    els.predictionTrackingMeta.textContent = data
      ? `${panelLabel} · 当前彩种 ${Number(summary.total || 0).toLocaleString("zh-CN")} 条 · 全部 ${Number(
          allSummary.total || 0,
        ).toLocaleString("zh-CN")} 条 · 当前筛选 ${Number(data.total || 0).toLocaleString("zh-CN")} 条 · ${fmtDate(data.generatedAt)}`
      : "等待生成预测记录";
  }
  if (els.predictionTrackingStatusFilter) {
    els.predictionTrackingStatusFilter.value =
      data?.statusFilter || predictionPanelState().predictionTrackingStatus || "all";
  }
  if (els.predictionTrackingPageInfo) {
    els.predictionTrackingPageInfo.textContent = data
      ? `${Number(data.page || 1).toLocaleString("zh-CN")} / ${Number(data.totalPage || 1).toLocaleString("zh-CN")}`
      : "--";
  }
  if (els.predictionTrackingPrevBtn) {
    els.predictionTrackingPrevBtn.disabled = !data || Number(data.page || 1) <= 1;
  }
  if (els.predictionTrackingNextBtn) {
    els.predictionTrackingNextBtn.disabled = !data || Number(data.page || 1) >= Number(data.totalPage || 1);
  }

  els.predictionTrackingStats.innerHTML = [
    `<article>
      <span>待结算</span>
      <strong>${Number(summary.pending || 0).toLocaleString("zh-CN")}</strong>
      <small>已结算 ${settled.toLocaleString("zh-CN")} · 取消 ${cancelled.toLocaleString("zh-CN")} · 作废 ${voided.toLocaleString("zh-CN")}</small>
    </article>`,
    `<article>
      <span>实际命中</span>
      <strong>${hitRateText}</strong>
      <small>区间 ${settled ? `${fmtPct(Number(ci[0] || 0), 2)} - ${fmtPct(Number(ci[1] || 0), 2)}` : "--"}</small>
    </article>`,
    `<article>
      <span>理论基准</span>
      <strong>${theoryText}</strong>
      <small>盈亏线 ${settled ? fmtPct(Number(summary.breakEvenHitRate || 0), 3) : "--"}</small>
    </article>`,
    `<article class="accent ${sampleLow ? "sample-low" : ""}">
      <span>单位 ROI</span>
      <strong class="${!sampleLow && roi > 0 ? "positive" : !sampleLow && roi < 0 ? "negative" : ""}">${
        settled && !sampleLow ? fmtPct(roi, 2) : "--"
      }</strong>
      <small class="${profit > 0 ? "positive" : profit < 0 ? "negative" : ""}">盈亏 ${
        settled && !sampleLow ? fmtMoney(profit, 2) : "--"
      }${sampleLow ? " · 样本量不足" : ""}</small>
    </article>`,
  ].join("");

  const warnings = [];
  warnings.push("追踪命中率和 ROI 只反映历史记录，不代表未来开奖概率被改变。");
  if (summary.warning) {
    warnings.push(summary.warning);
  } else if (settled > 0 && settled < 30) {
    warnings.push(`当前已结算 ${settled.toLocaleString("zh-CN")} 条，样本仍偏少；至少累计 30 条后再判断是否偏离理论基准。`);
  }
  if (data?.createdNow) {
    warnings.push(`本次新增 ${Number(data.createdNow || 0).toLocaleString("zh-CN")} 条下一期候选票追踪。`);
  }
  if (els.predictionTrackingWarning) {
    els.predictionTrackingWarning.textContent = warnings.join(" ");
    els.predictionTrackingWarning.classList.toggle("hidden", !warnings.length);
  }

  const groups = data?.groups || [];
  renderPredictionStrategyHealth(groups);
  if (els.predictionTrackingGroups) {
    els.predictionTrackingGroups.innerHTML = groups.length
      ? groups
          .slice(0, 6)
          .map((group) => {
            const groupSettled = Number(group.settled || 0);
            const groupRoi = Number(group.roi || 0);
            return `<article class="tracking-group">
              <div>
                <strong>${escapeHtml(group.strategyLabel || "--")}</strong>
                <span>${escapeHtml(group.gameShortName || "")} · ${group.mode === "bonus" ? `${group.pickCount}+1特殊球` : `${group.pickCount}球`}</span>
              </div>
              <div class="tracking-group-metrics">
                <span>${groupSettled ? fmtPct(Number(group.hitRate || 0), 2) : "--"} / 理论 ${
                  groupSettled ? fmtPct(Number(group.theoreticalHitRate || 0), 3) : "--"
                }</span>
                <span class="${groupRoi > 0 ? "positive" : groupRoi < 0 ? "negative" : ""}">${
                  groupSettled ? fmtPct(groupRoi, 2) : "--"
                }</span>
              </div>
            </article>`;
          })
          .join("")
      : '<article class="tracking-group empty"><span class="muted">暂无可分组的追踪记录</span></article>';
  }
  renderPredictionAdjacentStats();

  const items = data?.items || [];
  if (!items.length) {
    els.predictionTrackingRows.innerHTML =
      '<tr><td colspan="7"><span class="muted">生成预测后会自动记录下一期策略候选票。</span></td></tr>';
    return;
  }
  els.predictionTrackingRows.innerHTML = items
    .map((record) => {
      const recordProfit = Number(record.profit || 0);
      const targetRelative = relativeTargetLabel(record.targetDrawTimeUtc, record.status);
      const targetClass = targetRelative.startsWith("!") ? "target-overdue" : "target-relative";
      const coreNumbers = Array.isArray(record.coreNumbers) ? record.coreNumbers : [];
      const companionNumbers = Array.isArray(record.companionNumbers) ? record.companionNumbers : [];
      const recordPanel = normalizePredictionPanel(record.panel || state.predictionPanel);
      const isPanelFRecord = recordPanel === PREDICTION_PANEL_F;
      const isPanelGRecord = recordPanel === PREDICTION_PANEL_G;
      const recallNumbers = Array.isArray(record.recallNumbers) && record.recallNumbers.length
        ? record.recallNumbers
        : Array.isArray(record.reversalNumbers) && record.reversalNumbers.length
          ? record.reversalNumbers
          : companionNumbers;
      const sourcePoolCount = Number(record.sourcePoolCount || record.sourcePoolNumbers?.length || record.excludedNumbers?.length || 0);
      const structureMeta = record.structureType
        ? isPanelFRecord
          ? `<div class="muted tracking-structure">${escapeHtml(record.structureLabel || record.structureType)} · 召回 ${escapeHtml(
              recallNumbers.join("-") || "--",
            )} · 候选池 ${sourcePoolCount ? `${sourcePoolCount.toLocaleString("zh-CN")}个` : "--"}</div>`
          : isPanelGRecord
            ? `<div class="muted tracking-structure">${escapeHtml(record.structureLabel || record.structureType)} · 杀号池 ${
                sourcePoolCount ? `${sourcePoolCount.toLocaleString("zh-CN")}个` : "--"
              } · 剩余池预测</div>`
          : `<div class="muted tracking-structure">${escapeHtml(record.structureLabel || record.structureType)} · 核心 ${escapeHtml(
              coreNumbers.join("-") || "--",
            )} · 派生 ${escapeHtml(companionNumbers.join("-") || "--")}</div>`
        : "";
      const resultCells =
        record.status === "pending"
          ? '<td colspan="2" class="tracking-pending-result"><span class="pending-placeholder">--</span><div class="muted">等待开奖同步</div></td>'
          : `<td>${trackingDrawResult(record)}</td>
        <td class="${recordProfit > 0 ? "profit positive" : recordProfit < 0 ? "profit negative" : "profit"}">${fmtMoney(
            recordProfit,
            2,
          )}</td>`;
      return `<tr>
        <td><strong>${fmtTime(record.targetDrawTimeUtc)}</strong>${
          targetRelative ? ` <span class="${targetClass}">${escapeHtml(targetRelative)}</span>` : ""
        }<div class="muted">${fmtDate(record.createdAt)} 创建</div></td>
        <td>${escapeHtml(record.strategyLabel || "--")}<div class="muted">${escapeHtml(record.methodVersion || "")}</div>${structureMeta}</td>
        <td>${trackingTicketContent(record)}</td>
        <td>${fmtPct(Number(record.theoreticalHitRate || 0), 3)}<div class="muted">近窗 ${fmtPct(
          Number(record.recentHitRate || 0),
          2,
        )}</div></td>
        <td>${statusBadge(record.status)}</td>
        ${resultCells}
      </tr>`;
    })
    .join("");
}

function renderPredictionAutoStatus() {
  const data = state.predictionAuto;
  if (!els.predictionAutoStatus) return;
  const running = Boolean(data?.running);
  const enabled = Boolean(data?.enabled);
  const resultCount = Number(data?.results?.length || 0);
  const errorCount = Number(data?.errors?.length || 0);
  els.predictionAutoStatus.textContent = running
    ? `追踪运行中 · 下次 ${fmtTime(data.nextRunAt)}`
    : enabled
      ? "追踪已启用"
      : "追踪关闭";
  els.predictionAutoStatus.title = data?.message || "";
  if (els.predictionAutoToggleBtn) {
    els.predictionAutoToggleBtn.textContent = running || enabled ? "停止追踪" : "启动追踪";
  }
  if (els.predictionAutoRunBtn) {
    els.predictionAutoRunBtn.textContent = "立即同步一次";
    els.predictionAutoRunBtn.title = resultCount || errorCount ? `上次 ${resultCount} 成功，${errorCount} 错误` : "";
  }
}

function predictionSourceTicketUniqueNumbers(tickets = []) {
  return [
    ...new Set(
      tickets
        .flatMap((ticket) => (Array.isArray(ticket?.numbers) ? ticket.numbers : []))
        .map((number) => Number(number))
        .filter(Number.isFinite),
    ),
  ].sort((a, b) => a - b);
}

function predictionSourceTicketSummaryTitle(tickets = []) {
  return tickets
    .map((ticket, index) => {
      const label = ticket?.ticketLabel || (Array.isArray(ticket?.numbers) ? ticket.numbers.join("-") : "");
      const ticketIndex = Number(ticket?.index || index + 1).toLocaleString("zh-CN");
      return `#${ticketIndex} ${label}`;
    })
    .filter(Boolean)
    .join(" / ");
}

function predictionSourceTicketBalls(numbers = [], limit = 24) {
  const items = [...new Set((numbers || []).map((number) => Number(number)).filter(Number.isFinite))]
    .sort((a, b) => a - b);
  if (!items.length) return '<span class="muted">--</span>';
  const visible = items.slice(0, limit);
  const hiddenCount = Math.max(0, items.length - visible.length);
  return `${visible
    .map((number) => `<span class="prediction-ball compact source"><strong>${number}</strong></span>`)
    .join("")}${hiddenCount ? `<span class="prediction-kill-source-overflow">+${hiddenCount.toLocaleString("zh-CN")}</span>` : ""}`;
}

function renderPredictionKillSources(predictions, showSources) {
  if (!els.predictionKillSources) return;
  const sourceTickets = predictions?.sourceTickets || {};
  const panel = normalizePredictionPanel(predictions?.panel || state.predictionPanel);
  const sourceLabels = {
    [PREDICTION_PANEL_DEFAULT]: "A源票",
    [PREDICTION_PANEL_B]: "B源票",
    [PREDICTION_PANEL_C]: "C源票",
    [PREDICTION_PANEL_D]: "D源票",
    [PREDICTION_PANEL_E]: "E源票",
  };
  const panelOrder =
    panel === PREDICTION_PANEL_G
      ? [PREDICTION_PANEL_C, PREDICTION_PANEL_D, PREDICTION_PANEL_E]
      : panel === PREDICTION_PANEL_F
      ? [PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B, PREDICTION_PANEL_C, PREDICTION_PANEL_D, PREDICTION_PANEL_E]
      : [PREDICTION_PANEL_C, PREDICTION_PANEL_D];
  const groups = panelOrder
    .map((sourcePanel) => [
      sourcePanel,
      sourceLabels[sourcePanel] || `${sourcePanel.toUpperCase()}源票`,
      Array.isArray(sourceTickets[sourcePanel]) ? sourceTickets[sourcePanel] : [],
    ])
    .filter(([, , tickets]) => tickets.length);
  if (!showSources || !groups.length) {
    els.predictionKillSources.classList.add("hidden");
    els.predictionKillSources.innerHTML = "";
    return;
  }
  els.predictionKillSources.innerHTML = groups
    .map(([panel, label, tickets]) => {
      const uniqueNumbers = predictionSourceTicketUniqueNumbers(tickets);
      const title = predictionSourceTicketSummaryTitle(tickets);
      return `<div class="prediction-kill-source-group" data-panel="${escapeHtml(panel)}">
        <div class="prediction-kill-source-title">
          <strong>${escapeHtml(label)}</strong>
          <span>${Number(tickets.length || 0).toLocaleString("zh-CN")}组 · ${Number(uniqueNumbers.length || 0).toLocaleString("zh-CN")}个唯一号</span>
        </div>
        <div class="prediction-kill-source-balls" title="${escapeHtml(title)}">${predictionSourceTicketBalls(uniqueNumbers)}</div>
      </div>`;
    })
    .join("");
  els.predictionKillSources.classList.remove("hidden");
}

function renderPredictionKillPanel(predictions) {
  if (!els.predictionKillPanel) return;
  const panel = normalizePredictionPanel(predictions?.panel || state.predictionPanel);
  const isPanelB = panel === PREDICTION_PANEL_B;
  const isPanelD = panel === PREDICTION_PANEL_D;
  const isPanelE = panel === PREDICTION_PANEL_E;
  const isPanelF = panel === PREDICTION_PANEL_F;
  const isPanelG = panel === PREDICTION_PANEL_G;
  const showKillPanel = isPanelB || isPanelD || isPanelE || isPanelF || isPanelG;
  els.predictionKillPanel.classList.toggle("hidden", !showKillPanel);
  if (!showKillPanel) {
    if (els.predictionKillSummary) els.predictionKillSummary.textContent = "--";
    if (els.predictionKillNumbers) els.predictionKillNumbers.innerHTML = "";
    renderPredictionKillSources(predictions, false);
    return;
  }
  const killLabel =
    isPanelG
      ? "CDE候选杀号池"
      : isPanelF
      ? "ABCDE误杀候选池"
      : isPanelE
        ? "CD杀号"
        : isPanelD && predictions?.sourcePanel === PREDICTION_PANEL_C
          ? "C杀号"
          : isPanelD
            ? "ABC杀号"
            : "面板A杀号";
  if (els.predictionKillLabel) {
    els.predictionKillLabel.textContent = killLabel;
  }
  const numbers = [...new Set((predictions?.excludedNumbers || []).map((number) => Number(number)).filter(Number.isFinite))]
    .sort((a, b) => a - b);
  if (els.predictionKillSummary) {
    els.predictionKillSummary.textContent = numbers.length
      ? isPanelF
        ? `${numbers.length.toLocaleString("zh-CN")} 个主球来自A/B/C/D/E排除链路`
        : isPanelG
          ? `${numbers.length.toLocaleString("zh-CN")} 个主球来自C/D/E候选票，G已从剩余号码生成预测`
          : `${numbers.length.toLocaleString("zh-CN")} 个主球已排除`
      : isPanelF
        ? "暂无候选池"
        : isPanelG
          ? "暂无C/D/E候选杀号池"
          : "暂无排除号";
  }
  if (els.predictionKillNumbers) {
    els.predictionKillNumbers.innerHTML = numbers.length
      ? numbers
          .map((number) => `<span class="prediction-ball compact kill"><strong>${number}</strong></span>`)
          .join("")
      : `<span class="muted">${killLabel}暂未给出可用主球</span>`;
  }
  renderPredictionKillSources(predictions, isPanelE || isPanelF || isPanelG);
}

function renderPredictions(predictions) {
  if (!predictions) return;
  const panelLabel = predictions.panelLabel || predictionPanelLabel(predictions.panel);
  if (els.predictionTitle) {
    els.predictionTitle.textContent = panelLabel;
  }
  const start = fmtTime(predictions.timeWindowUtc?.start);
  const end = fmtTime(predictions.timeWindowUtc?.end);
  const drawCount = Number(state.prediction?.drawCount || 0);
  els.predictionWindow.textContent =
    start !== "--" && end !== "--" ? `预测时间窗 ${start} - ${end}` : "预测时间窗 --";
  els.predictionMethod.textContent = `近${Number(predictions.recentWindow || 0).toLocaleString(
    "zh-CN",
  )}期 · ${predictions.method}`;
  renderPredictionKillPanel(predictions);
  if (els.predictionNotice) {
    const noticeParts = [
      "当前为启发式统计排序，不代表开奖概率被改变；下注前应以理论命中率、赔率盈亏线和资金风险为准。",
    ];
    if (drawCount > 0 && drawCount < 500) {
      noticeParts.unshift(`可用历史仅 ${drawCount.toLocaleString("zh-CN")} 期，样本不足 500 期。`);
    }
    els.predictionNotice.textContent = noticeParts.join(" ");
    els.predictionNotice.classList.toggle("warning-note", drawCount > 0 && drawCount < 500);
  }
  renderPredictionStrategyTickets(predictions.strategyTickets || []);
}

function statusBadge(status) {
  const labels = {
    pending: "待开奖",
    won: "已中奖",
    lost: "未中",
    cancelled: "已取消",
    void: "已作废",
  };
  return `<span class="bet-status ${escapeHtml(status)}">${escapeHtml(
    labels[status] || status || "--",
  )}</span>`;
}

function renderBacktestChart(points) {
  const width = 720;
  const height = 220;
  const padX = 34;
  const padY = 24;
  if (!points?.length) {
    els.backtestChart.innerHTML =
      '<text x="360" y="112" text-anchor="middle" fill="#7f8a84" font-size="13">暂无曲线数据</text>';
    return;
  }
  const minProfit = Math.min(0, ...points.map((point) => Number(point.cumulativeProfit || 0)));
  const maxProfit = Math.max(0, ...points.map((point) => Number(point.cumulativeProfit || 0)));
  const span = maxProfit - minProfit || 1;
  const maxDraw = Math.max(1, ...points.map((point) => Number(point.drawIndex || 0)));
  const xFor = (drawIndex) => padX + (Number(drawIndex || 0) / maxDraw) * (width - padX * 2);
  const yFor = (profit) => height - padY - ((Number(profit || 0) - minProfit) / span) * (height - padY * 2);
  const path = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xFor(point.drawIndex).toFixed(2)} ${yFor(point.cumulativeProfit).toFixed(2)}`)
    .join(" ");
  const zeroY = yFor(0);
  const lastPoint = points[points.length - 1];
  const positive = Number(lastPoint.cumulativeProfit || 0) >= 0;
  els.backtestChart.innerHTML = `
    <line x1="${padX}" y1="${zeroY.toFixed(2)}" x2="${width - padX}" y2="${zeroY.toFixed(
      2,
    )}" class="chart-zero"></line>
    <path d="${path}" class="${positive ? "chart-line positive" : "chart-line negative"}"></path>
    <text x="${padX}" y="16" class="chart-label">${fmtMoney(maxProfit, 2)}</text>
    <text x="${padX}" y="${height - 6}" class="chart-label">${fmtMoney(minProfit, 2)}</text>
    <text x="${width - padX}" y="${height - 6}" text-anchor="end" class="chart-label">${maxDraw}期</text>
  `;
}

function renderBacktestResult(result) {
  if (!result) return;
  els.backtestResultPanel.classList.remove("hidden");
  els.backtestResultTitle.textContent = result.strategyLabel || "回测结果";
  const gapWarning = result.gapWarning;
  const gapText = gapWarning
    ? ` · 时间间隔提示：${Number(gapWarning.missingIntervals || 0).toLocaleString("zh-CN")} 个异常间隔`
    : "";
  const requestedTest =
    Number(result.requestedTestWindow || 0) && Number(result.requestedTestWindow || 0) !== Number(result.testWindow || 0)
      ? ` / 请求 ${Number(result.requestedTestWindow || 0).toLocaleString("zh-CN")}`
      : "";
  const maxSelections = result.maxSelectionsPerDraw
    ? ` · 每期最多 ${Number(result.maxSelectionsPerDraw || 0).toLocaleString("zh-CN")} 注`
    : "";
  const strategyNote = result.strategyNote ? ` · ${result.strategyNote}` : "";
  els.backtestResultMeta.textContent = `训练 ${result.trainWindow} 期 · 验证 ${result.testWindow} 期${requestedTest}${maxSelections} · ${fmtDate(
    result.generatedAt,
  )}${gapText}${strategyNote}`;
  const hitRateCi = result.hitRateCi || [0, 0];
  els.backtestHitRate.textContent = fmtPct(Number(result.hitRate || 0), 3);
  els.backtestTheoryHitRate.textContent = `理论/训练基准 ${fmtPct(Number(result.theoreticalHitRate || 0), 3)}`;
  els.backtestHitRate.title = `95% 置信区间 ${fmtPct(Number(hitRateCi[0] || 0), 2)} - ${fmtPct(Number(hitRateCi[1] || 0), 2)}`;
  els.backtestRoi.textContent = fmtPct(Number(result.roi || 0), 2);
  els.backtestRoi.classList.toggle("positive", Number(result.roi || 0) > 0);
  els.backtestRoi.classList.toggle("negative", Number(result.roi || 0) < 0);
  const backtestExcessRoi = Number(result.excessRoi ?? Number(result.roi || 0) - Number(result.theoreticalRoi || 0));
  els.backtestTheoryRoi.textContent = `理论 ${fmtPct(Number(result.theoreticalRoi || 0), 2)} · 超额 ${fmtPct(backtestExcessRoi, 2)}`;
  els.backtestBetsWon.textContent = `${Number(result.totalBets || 0).toLocaleString("zh-CN")} / ${Number(
    result.won || 0,
  ).toLocaleString("zh-CN")}`;
  els.backtestProfit.textContent = `盈亏 ${fmtMoney(Number(result.profit || 0), 2)} · 投入 ${fmtNumber(
    Number(result.stakeTotal || 0),
    2,
  )}`;
  els.backtestMaxLoss.textContent = Number(result.maxLossStreak || 0).toLocaleString("zh-CN");
  renderBacktestChart(result.roiCurve || []);

  const samples = result.selectionSamples || [];
  if (!samples.length) {
    els.backtestSamples.innerHTML =
      '<tr><td colspan="6"><span class="muted">暂无样本明细</span></td></tr>';
    return;
  }
  els.backtestSamples.innerHTML = samples
    .map((item) => {
      return `<tr>
        <td>${item.drawIndex}</td>
        <td>${fmtTime(item.drawTimeUtc)}</td>
        <td>${escapeHtml(item.label)}</td>
        <td class="strong-cell">${item.currentMiss} / ${item.maxMiss}</td>
        <td>${fmtPct(Number(item.trainHitRate || 0), 2)}</td>
        <td>${item.won ? '<span class="bet-status won">命中</span>' : '<span class="bet-status lost">未中</span>'}</td>
      </tr>`;
    })
    .join("");
}

function renderBacktestScanResult(result) {
  if (!result || !els.backtestScanPanel) return;
  els.backtestScanPanel.classList.remove("hidden");
  const requestedTest =
    Number(result.requestedTestWindow || 0) && Number(result.requestedTestWindow || 0) !== Number(result.testWindow || 0)
      ? ` / 请求 ${Number(result.requestedTestWindow || 0).toLocaleString("zh-CN")}`
      : "";
  els.backtestScanMeta.textContent = `扫描 ${Number(result.candidateCount || 0).toLocaleString(
    "zh-CN",
  )} 项 · 入榜 ${Number(result.eligibleCount || 0).toLocaleString("zh-CN")} · 最小投注 ${Number(
    result.minBets || 0,
  ).toLocaleString("zh-CN")} · 训练 ${Number(result.trainWindow || 0).toLocaleString("zh-CN")} 期 · 验证 ${Number(
    result.testWindow || 0,
  ).toLocaleString("zh-CN")}${requestedTest}`;
  if (els.backtestScanNotice) {
    const skippedCandidates = Number(result.skippedFixedShapeCandidates || 0);
    const deduped = Number(result.dedupedRankResults || 0);
    const notices = [
      "自动扫描是在多组参数中挑选 ROI 靠前结果，存在数据挖掘偏差；请结合理论命中率、投注次数和样本外表现判断。",
    ];
    if (skippedCandidates > 0) {
      notices.push(
        `固定形态组合超出上限，已跳过 ${skippedCandidates.toLocaleString("zh-CN")} 个候选。`,
      );
    }
    if (deduped > 0) {
      notices.push(`已合并 ${deduped.toLocaleString("zh-CN")} 个重复排名结果。`);
    }
    els.backtestScanNotice.textContent = notices.join(" ");
    els.backtestScanNotice.classList.remove("hidden");
  }

  const rows = result.results || [];
  if (!rows.length) {
    els.backtestScanRows.innerHTML = '<tr><td colspan="10"><span class="muted">暂无满足最小投注次数的扫描结果</span></td></tr>';
    return;
  }
  els.backtestScanRows.innerHTML = rows
    .map((item) => {
      const roi = Number(item.roi || 0);
      const theoreticalRoi = Number(item.theoreticalRoi || 0);
      const excessRoi = Number(item.excessRoi ?? roi - theoreticalRoi);
      const profit = Number(item.profit || 0);
      const ci = item.hitRateCi || [0, 0];
      const roiClass = roi > 0 ? "positive" : roi < 0 ? "negative" : "";
      const theoreticalRoiClass = theoreticalRoi > 0 ? "positive" : theoreticalRoi < 0 ? "negative" : "";
      const excessRoiClass = excessRoi > 0 ? "positive" : excessRoi < 0 ? "negative" : "";
      const profitClass = profit > 0 ? "positive" : profit < 0 ? "negative" : "";
      return `<tr>
        <td>${Number(item.rank || 0).toLocaleString("zh-CN")}</td>
        <td>${escapeHtml(scanStrategyText(item))}</td>
        <td>${escapeHtml(scanTypeText(item))}</td>
        <td>${Number(item.totalBets || 0).toLocaleString("zh-CN")} / ${Number(item.won || 0).toLocaleString("zh-CN")}</td>
        <td title="95% 置信区间 ${fmtPct(Number(ci[0] || 0), 2)} - ${fmtPct(Number(ci[1] || 0), 2)}">${fmtPct(Number(item.hitRate || 0), 2)}</td>
        <td class="${roiClass}">${fmtPct(roi, 2)}</td>
        <td class="${theoreticalRoiClass}">${fmtPct(theoreticalRoi, 2)}</td>
        <td class="${excessRoiClass}" title="实测 ROI - 理论 ROI">${fmtPct(excessRoi, 2)}</td>
        <td class="${profitClass}">${fmtMoney(profit, 2)}</td>
        <td>${Number(item.maxLossStreak || 0).toLocaleString("zh-CN")}</td>
      </tr>`;
    })
    .join("");
}

function scanStrategyText(item) {
  const kind = String(item.scanKind || "");
  if (kind.includes("：")) return kind;
  const numbers = item.params?.numbers;
  if (Array.isArray(numbers) && numbers.length) return numbers.join("-");
  if (item.scanCategory === "动态连号遗漏" || item.scanCategory === "形态组合遗漏") {
    const count = Number(item.maxSelectionsPerDraw || 0);
    return count > 0 ? `每期选 ${count} 注` : "动态选择";
  }
  return item.strategyLabel || kind || "--";
}

function scanTypeText(item) {
  const kind = String(item.scanKind || "");
  if (kind.includes("：")) return kind.split("：")[0];
  if (kind) return kind;
  return item.scanCategory || "--";
}

function renderTable(items) {
  els.tripleTable.innerHTML = "";
  const maxMiss = Math.max(1, ...items.map((item) => Number(item.maxMiss || item.currentMiss || 0)));
  for (const item of items) {
    const row = document.createElement("tr");
    const zScore = Number(item.missZScore || 0);
    const zClass =
      zScore > 2 ? "z-score danger" : zScore > 1.5 ? "z-score warn" : zScore < 1 ? "z-score muted" : "z-score";
    const missWidth = Math.max(4, (Number(item.currentMiss || 0) / maxMiss) * 100);
    row.innerHTML = `
      <td>${tripleBadge(item.numbers)}</td>
      <td class="strong-cell miss-cell">
        <span class="miss-mini-track"><span style="width:${missWidth}%"></span></span>
        <strong>${item.currentMiss}</strong>
      </td>
      <td>${item.maxMiss}</td>
      <td>${item.hits}</td>
      <td>${fmtPct(item.hitRate, 2)}</td>
      <td class="${zClass}">${fmtNumber(zScore, 2)}</td>
      <td>${item.lastMiss ?? "--"}</td>
    `;
    els.tripleTable.appendChild(row);
  }
}

function renderAdvanced(advanced) {
  if (!advanced) return;
  renderRunPatternCards(advanced.runPatterns.summary, advanced.runPatterns.windowAverages);
  renderDistribution(els.sumRangeBars, advanced.sumRanges, { limit: 14 });
  renderDistribution(els.sizeRatioBars, advanced.sizeRatios, { skipZero: true, limit: 21 });
  renderDistribution(els.oddEvenBars, advanced.oddEvenRatios, { skipZero: true, limit: 21 });
  renderBonusBallStats(advanced.bonusBall);
  renderCrossAnalysis();
  renderGroupTable({
    table: els.pairTable,
    count: els.pairCount,
    data: advanced.runPatterns.pairs,
    key: "pair",
    className: "pair",
  });
  renderGroupTable({
    table: els.quadTable,
    count: els.quadCount,
    data: advanced.runPatterns.quads,
    key: "quad",
    className: "quad",
  });
}

function renderBonusBallStats(stats) {
  if (!els.bonusBallPanel || !els.bonusBallBars || !els.bonusBallMeta) return;
  if (!stats?.enabled) {
    els.bonusBallPanel.classList.add("hidden");
    els.bonusBallBars.innerHTML = "";
    els.bonusBallMeta.textContent = "--";
    return;
  }
  els.bonusBallPanel.classList.remove("hidden");
  const latest = stats.latest?.number ? ` · 最新 ${stats.latest.number}` : "";
  els.bonusBallMeta.textContent = `${Number(stats.total || 0).toLocaleString("zh-CN")} 期 · 重合 ${fmtPct(
    Number(stats.overlapShare || 0),
    2,
  )}${latest}`;
  const items = [...(stats.items || [])]
    .filter((item) => Number(item.draws || 0) > 0)
    .sort((a, b) => Number(b.draws || 0) - Number(a.draws || 0) || Number(a.number || 0) - Number(b.number || 0));
  renderDistribution(
    els.bonusBallBars,
    items.map((item) => ({ ...item, label: String(item.number) })),
    { limit: 20 },
  );
}

function renderRunPatternCards(items, averages) {
  els.runPatternCards.innerHTML = "";
  for (const item of items) {
    const card = document.createElement("div");
    card.className = "stat-card";
    card.innerHTML = `
      <span>${item.label}</span>
      <strong>${item.draws.toLocaleString("zh-CN")}</strong>
      <small>${fmtPct(item.share, 2)} · 当前遗漏 ${item.currentMiss} · 最大 ${item.maxMiss}</small>
    `;
    els.runPatternCards.appendChild(card);
  }
  const avgCard = document.createElement("div");
  avgCard.className = "stat-card accent";
  avgCard.innerHTML = `
    <span>平均窗口数/期</span>
    <strong>${fmtNumber(averages.pairs, 2)} / ${fmtNumber(averages.triples, 2)} / ${fmtNumber(
      averages.quads,
      2,
    )}</strong>
    <small>两连 / 三连 / 四连</small>
  `;
  els.runPatternCards.appendChild(avgCard);
}

function renderDistribution(container, items, options = {}) {
  const visible = items
    .filter((item) => !options.skipZero || item.draws > 0)
    .slice(0, options.limit || items.length);
  const max = Math.max(1, ...visible.map((item) => item.draws));
  container.innerHTML = "";
  for (const item of visible) {
    const row = document.createElement("div");
    row.className = "dist-row";
    row.innerHTML = `
      <div class="dist-label">${item.label}</div>
      <div class="dist-track"><div class="dist-fill" style="width:${Math.max(
        2,
        (item.draws / max) * 100,
      )}%"></div></div>
      <div class="dist-value">${item.draws.toLocaleString("zh-CN")} <span>${fmtPct(
        item.share,
        2,
      )}</span></div>
    `;
    container.appendChild(row);
  }
}

function renderCrossAnalysis() {
  const advanced = state.analysis?.advanced;
  if (!advanced) return;
  const category = els.crossCategory.value;
  const condition = els.crossCondition.value;
  const rows = advanced.cross.filter(
    (item) => item.category === category && item.condition === condition,
  );
  const max = Math.max(1, ...rows.map((item) => item.draws));
  els.crossBars.innerHTML = "";
  for (const item of rows) {
    const row = document.createElement("div");
    row.className = "dist-row";
    row.innerHTML = `
      <div class="dist-label">${item.label}</div>
      <div class="dist-track"><div class="dist-fill cross" style="width:${Math.max(
        2,
        (item.draws / max) * 100,
      )}%"></div></div>
      <div class="dist-value">${item.draws.toLocaleString("zh-CN")} <span>${fmtPct(
        item.conditionShare,
        2,
      )}</span></div>
    `;
    row.title = `全样本占比 ${fmtPct(item.share, 2)}；当前条件内部占比 ${fmtPct(
      item.conditionShare,
      2,
    )}`;
    els.crossBars.appendChild(row);
  }
}

function renderGroupTable({ table, count, data, key, className }) {
  table.innerHTML = "";
  count.textContent = `${data.items.length}/${data.totalItems}`;
  for (const item of data.items) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${numberBadge(item.numbers, className)}</td>
      <td class="strong-cell">${item.currentMiss}</td>
      <td>${item.maxMiss}</td>
      <td>${item.hits}</td>
      <td>${fmtPct(item.hitRate, 2)}</td>
    `;
    row.title = item[key];
    table.appendChild(row);
  }
}

function runHighlightMap(numbers) {
  const numberSet = new Set(numbers);
  const levels = new Map(numbers.map((number) => [number, 0]));
  for (const length of [4, 3, 2]) {
    for (let start = 1; start <= 80 - length + 1; start += 1) {
      const group = Array.from({ length }, (_, index) => start + index);
      if (!group.every((number) => numberSet.has(number))) continue;
      for (const number of group) {
        levels.set(number, Math.max(levels.get(number) || 0, length));
      }
    }
  }
  return levels;
}

function historyBallClass(level) {
  if (level >= 4) return "ball quad";
  if (level === 3) return "ball triple";
  if (level === 2) return "ball pair";
  return "ball";
}

function renderHistory() {
  const data = state.history;
  if (!data) return;
  state.currentGame = data.game || state.currentGame;
  updateGameUi();
  renderSummary(data);
  els.historyCount.textContent = `${data.total.toLocaleString("zh-CN")} 条 · 第 ${data.page}/${data.totalPage} 页`;
  els.pageInfo.textContent = `第 ${data.page} / ${data.totalPage} 页`;
  els.prevPageBtn.disabled = state.loading || data.page <= 1;
  els.nextPageBtn.disabled = state.loading || data.page >= data.totalPage;
  els.historyTable.innerHTML = "";
  for (const draw of data.items) {
    const row = document.createElement("tr");
    const numbers = Array.isArray(draw.numbers) ? draw.numbers : [];
    const highlights = runHighlightMap(numbers);
    const statusText = String(draw.status || "");
    const isOfficialSupplement = statusText.startsWith("official-");
    const isCancelled =
      Boolean(draw.isCancelled) || (statusText === "60" && numbers.length === 0);
    const badges = `${
      isOfficialSupplement ? '<span class="temp-source">\u5b98\u7f51\u8865\u9f50</span>' : ""
    }${
      isCancelled ? '<span class="cancelled-source">\u5df2\u53d6\u6d88</span>' : ""
    }`;
    const resultHtml = historyResultHtml(draw, numbers, highlights, isCancelled);
    row.innerHTML = `
      <td><strong>${draw.drawEventId}</strong>${badges}</td>
      <td>${fmtDate(draw.drawTimeUtc)}</td>
      <td><div class="history-balls">${resultHtml}</div></td>
    `;
    els.historyTable.appendChild(row);
  }
}

function resetFilters() {
  if (els.drawLimit) els.drawLimit.value = "30";
  if (els.cdeBacktestTrain) els.cdeBacktestTrain.value = "240";
  state.analysis = null;
  state.cdeBacktestPage = 1;
  loadAnalysis({ force: true });
}

async function refreshCurrentView(options = {}) {
  if (state.activeModal === "martingale") {
    await loadCurrentSummary();
    updateMartingaleMeta();
    return;
  }
  if (state.activeModal === "backtest") {
    await loadCurrentSummary();
    await loadBacktestStatus();
    return;
  }
  if (state.activeModal === "analysis") {
    await loadAnalysis({ force: options.force });
    return;
  }
  if (state.activeModal === "history") {
    await loadHistory();
    return;
  }
  if (
    state.activeView === "prediction" ||
    state.activeView === "predictionB" ||
    state.activeView === "predictionC" ||
    state.activeView === "predictionD" ||
    state.activeView === "predictionE" ||
    state.activeView === "predictionF" ||
    state.activeView === "predictionG"
  ) {
    const panel = predictionPanelForView(state.activeView);
    setPredictionPanel(panel);
    await loadPrediction({ preserve: options.preserve, force: options.force, panel });
    return;
  }
  if (state.activeView === "martingale") {
    await loadCurrentSummary();
    updateMartingaleMeta();
    return;
  }
  if (state.activeView === "backtest") {
    await loadCurrentSummary();
    await loadBacktestStatus();
    return;
  }
  if (state.activeView === "analysis") {
    await loadAnalysis({ force: options.force });
    return;
  }
  if (state.activeView === "history") {
    await loadHistory();
  }
}

async function switchView(view) {
  if (!isToolModalView(view)) {
    closeToolModal();
  }
  if (!currentGameSupportsView(view)) {
    const requested = view;
    view = "history";
    showToast(requested === "prediction" ? "该彩种当前只保留开奖同步，不再生成预测" : "该彩种当前不开放该工具");
  }
  state.activeView = view;
  renderTabState();
  document
    .querySelector("#predictionView")
    .classList.toggle(
      "active",
      view === "prediction" ||
        view === "predictionB" ||
        view === "predictionC" ||
        view === "predictionD" ||
        view === "predictionE" ||
        view === "predictionF" ||
        view === "predictionG",
    );
  document.querySelector("#martingaleView").classList.toggle("active", view === "martingale");
  document.querySelector("#backtestView").classList.toggle("active", view === "backtest");
  document.querySelector("#analysisView").classList.toggle("active", view === "analysis");
  document.querySelector("#historyView").classList.toggle("active", view === "history");
  await hydrateView(view);
}

document.querySelectorAll(".tab-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const view = button.dataset.view;
    if (isToolModalView(view)) {
      openToolModal(view);
      return;
    }
    switchView(view);
  });
});

document.querySelectorAll("[data-modal-close]").forEach((element) => {
  element.addEventListener("click", closeToolModal);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.activeModal) {
    closeToolModal();
  }
});

syncBacktestControls();
syncMartingaleModeControls();
setMartingalePickCount(state.martingalePickCount);

els.applyBtn.addEventListener("click", loadAnalysis);
els.resetBtn.addEventListener("click", resetFilters);
els.refreshPageBtn.addEventListener("click", () => refreshCurrentView({ force: true }));
els.syncBtn.addEventListener("click", () => syncData("incremental"));
els.fullSyncBtn.addEventListener("click", () => syncData("full"));
els.gameSelect.addEventListener("change", () => {
  selectGame(els.gameSelect.value);
});
if (els.gamePills) {
  els.gamePills.addEventListener("click", (event) => {
    const button = event.target.closest("[data-game]");
    if (!button) return;
    selectGame(button.dataset.game);
  });
}
if (els.predictionTrackingStatusFilter) {
  els.predictionTrackingStatusFilter.addEventListener("change", () => {
    const slot = predictionPanelState();
    slot.predictionTrackingStatus = els.predictionTrackingStatusFilter.value || "all";
    slot.predictionTrackingPage = 1;
    syncPredictionPanelMirror();
    loadPredictionTracking({ silent: true, panel: state.predictionPanel });
  });
}
if (els.predictionTrackingPrevBtn) {
  els.predictionTrackingPrevBtn.addEventListener("click", () => {
    const slot = predictionPanelState();
    slot.predictionTrackingPage = Math.max(1, Number(slot.predictionTrackingPage || 1) - 1);
    syncPredictionPanelMirror();
    loadPredictionTracking({ silent: true, panel: state.predictionPanel });
  });
}
if (els.predictionTrackingNextBtn) {
  els.predictionTrackingNextBtn.addEventListener("click", () => {
    const slot = predictionPanelState();
    slot.predictionTrackingPage = Number(slot.predictionTrackingPage || 1) + 1;
    syncPredictionPanelMirror();
    loadPredictionTracking({ silent: true, panel: state.predictionPanel });
  });
}
if (els.predictionAutoToggleBtn) {
  els.predictionAutoToggleBtn.addEventListener("click", () => {
    const running = Boolean(state.predictionAuto?.running || state.predictionAuto?.enabled);
    updatePredictionAuto(running ? "stop" : "start");
  });
}
if (els.predictionAutoRunBtn) {
  els.predictionAutoRunBtn.addEventListener("click", () => updatePredictionAuto("runOnce"));
}
if (els.predictionAdjacentStats) {
  els.predictionAdjacentStats.addEventListener("click", (event) => {
    const target = event.target;
    if (target?.id === "adjacentHitSearchBtn") {
      const slot = predictionPanelState();
      slot.adjacentHitQuery = document.querySelector("#adjacentHitQuery")?.value || "";
      slot.adjacentHitPage = 1;
      syncPredictionPanelMirror();
      loadAdjacentHits({ panel: state.predictionPanel });
    }
    if (target?.id === "adjacentHitPrevBtn") {
      const slot = predictionPanelState();
      slot.adjacentHitPage = Math.max(1, Number(slot.adjacentHitPage || 1) - 1);
      syncPredictionPanelMirror();
      loadAdjacentHits({ panel: state.predictionPanel });
    }
    if (target?.id === "adjacentHitNextBtn") {
      const slot = predictionPanelState();
      slot.adjacentHitPage = Number(slot.adjacentHitPage || 1) + 1;
      syncPredictionPanelMirror();
      loadAdjacentHits({ panel: state.predictionPanel });
    }
  });
  els.predictionAdjacentStats.addEventListener("keydown", (event) => {
    if (event.target?.id !== "adjacentHitQuery" || event.key !== "Enter") return;
    const slot = predictionPanelState();
    slot.adjacentHitQuery = event.target.value || "";
    slot.adjacentHitPage = 1;
    syncPredictionPanelMirror();
    loadAdjacentHits({ panel: state.predictionPanel });
  });
}
els.runBacktestBtn.addEventListener("click", runBacktest);
if (els.runBacktestScanBtn) {
  els.runBacktestScanBtn.addEventListener("click", runBacktestScan);
}
els.backtestStrategy.addEventListener("change", () => {
  syncBacktestControls();
});
if (els.martingaleModeGroup) {
  els.martingaleModeGroup.addEventListener("click", (event) => {
    const button = event.target.closest("[data-martingale-mode]");
    if (!button) return;
    setMartingaleMode(button.dataset.martingaleMode);
  });
}
if (els.martingalePlayGroup) {
  els.martingalePlayGroup.addEventListener("click", (event) => {
    const button = event.target.closest("[data-pick-count]");
    if (!button || button.disabled) return;
    setMartingalePickCount(button.dataset.pickCount);
  });
}
if (els.generateMartingaleBtn) {
  els.generateMartingaleBtn.addEventListener("click", () => renderMartingalePlan());
}
els.historySearchBtn.addEventListener("click", () => {
  state.historyPage = 1;
  loadHistory();
});
els.prevPageBtn.addEventListener("click", () => {
  state.historyPage = Math.max(1, state.historyPage - 1);
  loadHistory();
});
els.nextPageBtn.addEventListener("click", () => {
  state.historyPage += 1;
  loadHistory();
});

if (els.cdeBacktestPrevBtn) {
  els.cdeBacktestPrevBtn.addEventListener("click", () => {
    if (!state.analysis) return;
    state.cdeBacktestPage = Math.max(1, Number(state.cdeBacktestPage || 1) - 1);
    renderCdeKillBacktest(state.analysis);
  });
}
if (els.cdeBacktestNextBtn) {
  els.cdeBacktestNextBtn.addEventListener("click", () => {
    if (!state.analysis) return;
    state.cdeBacktestPage = Number(state.cdeBacktestPage || 1) + 1;
    renderCdeKillBacktest(state.analysis);
  });
}

for (const input of [
  els.drawLimit,
  els.cdeBacktestTrain,
].filter(Boolean)) {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadAnalysis();
  });
  input.addEventListener("change", () => {
    state.analysis = null;
    state.cdeBacktestPage = 1;
  });
}

for (const input of [els.historyQuery, els.historySort, els.historyPageSize]) {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      state.historyPage = 1;
      loadHistory();
    }
  });
  input.addEventListener("change", () => {
    if (input !== els.historyQuery) {
      state.historyPage = 1;
      loadHistory();
    }
  });
}

for (const input of [els.crossCategory, els.crossCondition]) {
  input.addEventListener("change", renderCrossAnalysis);
}

for (const input of [
  els.martingaleOdds,
  els.martingaleBankroll,
  els.martingalePeriods,
  els.martingaleTargetProfit,
  els.martingaleUnit,
  els.martingaleMaxStake,
  els.martingaleStopLoss,
  els.riskFlatStake,
  els.riskKellyFraction,
].filter(Boolean)) {
  input.addEventListener("change", () => {
    if (input === els.martingaleOdds) {
      state.martingaleOddsDirty = true;
    }
    updateMartingaleMeta();
    if (state.martingalePlan) renderMartingalePlan({ silent: true });
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") renderMartingalePlan();
  });
}

async function init() {
  try {
    await loadGames();
    await refreshCurrentView();
    await loadPredictionAutoStatus({ silent: true, refreshTracking: false });
    startPredictionAutoPolling();
  } catch (error) {
    showToast(`初始化失败：${error.message}`, true);
  }
}

init();
