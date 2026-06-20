const state = {
  games: [],
  currentGame: null,
  analysis: null,
  prediction: null,
  predictionTracking: null,
  predictionTrackingPage: 1,
  predictionTrackingStatus: "all",
  predictionTrackingSlot: "all",
  predictionTrackingDay: "",
  adjacentStats: null,
  adjacentHitPage: 1,
  adjacentHitQuery: "",
  adjacentHits: null,
  predictionAuto: null,
  predictionAutoPollTimer: null,
  predictionSyncRetryTimer: null,
  predictionAutoLastCompletedAt: "",
  telegram: null,
  predictionTrackingRefreshInFlight: false,
  predictionPanel: "a",
  predictionPanels: {
    a: {
      prediction: null,
      predictionTracking: null,
      predictionTrackingPage: 1,
      predictionTrackingStatus: "all",
      predictionTrackingSlot: "all",
      predictionTrackingDay: "",
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
      predictionTrackingSlot: "all",
      predictionTrackingDay: "",
      adjacentStats: null,
      adjacentHitPage: 1,
      adjacentHitQuery: "",
      adjacentHits: null,
    },
    m: {
      prediction: null,
      predictionTracking: null,
      predictionTrackingPage: 1,
      predictionTrackingStatus: "all",
      predictionTrackingSlot: "all",
      predictionTrackingDay: "",
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
      predictionTrackingSlot: "all",
      predictionTrackingDay: "",
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
      predictionTrackingSlot: "all",
      predictionTrackingDay: "",
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
      predictionTrackingSlot: "all",
      predictionTrackingDay: "",
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
      predictionTrackingSlot: "all",
      predictionTrackingDay: "",
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
      predictionTrackingSlot: "all",
      predictionTrackingDay: "",
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
  stakingBacktest: null,
  currentBacktest: null,
  fixedTripleObservation: null,
  fixedTripleOmission: null,
  martingaleMode: "main",
  martingalePickCount: 3,
  martingalePlan: null,
  martingaleOddsDirty: false,
  martingaleDefaultKey: "",
  historyPage: 1,
  history: null,
  cdeBacktestPage: 1,
  strategyAudit: null,
  strategyAuditStability: null,
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
  cdeBacktestBucketMeta: document.querySelector("#cdeBacktestBucketMeta"),
  cdeBacktestBucketRows: document.querySelector("#cdeBacktestBucketRows"),
  cdeBacktestNotes: document.querySelector("#cdeBacktestNotes"),
  cdeBacktestRows: document.querySelector("#cdeBacktestRows"),
  cdeBacktestPrevBtn: document.querySelector("#cdeBacktestPrevBtn"),
  cdeBacktestNextBtn: document.querySelector("#cdeBacktestNextBtn"),
  cdeBacktestPageInfo: document.querySelector("#cdeBacktestPageInfo"),
  strategyAuditMeta: document.querySelector("#strategyAuditMeta"),
  strategyAuditRunBtn: document.querySelector("#strategyAuditRunBtn"),
  strategyAuditWindow: document.querySelector("#strategyAuditWindow"),
  strategyAuditTrain: document.querySelector("#strategyAuditTrain"),
  strategyAuditStats: document.querySelector("#strategyAuditStats"),
  strategyAuditNotes: document.querySelector("#strategyAuditNotes"),
  strategyAuditVerdicts: document.querySelector("#strategyAuditVerdicts"),
  strategyAuditMatrixMeta: document.querySelector("#strategyAuditMatrixMeta"),
  strategyAuditScoreRows: document.querySelector("#strategyAuditScoreRows"),
  strategyAuditExperimentMeta: document.querySelector("#strategyAuditExperimentMeta"),
  strategyAuditExperimentRows: document.querySelector("#strategyAuditExperimentRows"),
  strategyAuditMixedMeta: document.querySelector("#strategyAuditMixedMeta"),
  strategyAuditMixedRows: document.querySelector("#strategyAuditMixedRows"),
  strategyAuditStabilityMeta: document.querySelector("#strategyAuditStabilityMeta"),
  strategyAuditStabilityRows: document.querySelector("#strategyAuditStabilityRows"),
  strategyAuditKillRows: document.querySelector("#strategyAuditKillRows"),
  strategyAuditTicketRows: document.querySelector("#strategyAuditTicketRows"),
  strategyAuditETopRows: document.querySelector("#strategyAuditETopRows"),
  strategyAuditRepeatRows: document.querySelector("#strategyAuditRepeatRows"),
  strategyAuditTrackingRows: document.querySelector("#strategyAuditTrackingRows"),
  strategyAuditDetailRows: document.querySelector("#strategyAuditDetailRows"),
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
  predictionTrackingSlotFilter: document.querySelector("#predictionTrackingSlotFilter"),
  predictionTrackingDayFilter: document.querySelector("#predictionTrackingDayFilter"),
  predictionTrackingPrevBtn: document.querySelector("#predictionTrackingPrevBtn"),
  predictionTrackingNextBtn: document.querySelector("#predictionTrackingNextBtn"),
  predictionTrackingPageInfo: document.querySelector("#predictionTrackingPageInfo"),
  predictionAutoStatus: document.querySelector("#predictionAutoStatus"),
  predictionAutoToggleBtn: document.querySelector("#predictionAutoToggleBtn"),
  predictionAutoRunBtn: document.querySelector("#predictionAutoRunBtn"),
  predictionAutoGameToggles: document.querySelector("#predictionAutoGameToggles"),
  telegramStatus: document.querySelector("#telegramStatus"),
  telegramEnabled: document.querySelector("#telegramEnabled"),
  telegramAllGames: document.querySelector("#telegramAllGames"),
  telegramChannel: document.querySelector("#telegramChannel"),
  telegramInviteLink: document.querySelector("#telegramInviteLink"),
  telegramDrawLink: document.querySelector("#telegramDrawLink"),
  telegramGameToggles: document.querySelector("#telegramGameToggles"),
  telegramSaveBtn: document.querySelector("#telegramSaveBtn"),
  telegramTestBtn: document.querySelector("#telegramTestBtn"),
  telegramNotifyNowBtn: document.querySelector("#telegramNotifyNowBtn"),
  telegramHint: document.querySelector("#telegramHint"),
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
  stakingBacktestView: document.querySelector("#stakingBacktestView"),
  stakingBacktestMeta: document.querySelector("#stakingBacktestMeta"),
  stakingBacktestSource: document.querySelector("#stakingBacktestSource"),
  stakingBacktestWindow: document.querySelector("#stakingBacktestWindow"),
  stakingBacktestCustomWindow: document.querySelector("#stakingBacktestCustomWindow"),
  stakingBacktestStartDateTime: document.querySelector("#stakingBacktestStartDateTime"),
  stakingBacktestEndDateTime: document.querySelector("#stakingBacktestEndDateTime"),
  stakingBacktestDailyStart: document.querySelector("#stakingBacktestDailyStart"),
  stakingBacktestDailyEnd: document.querySelector("#stakingBacktestDailyEnd"),
  stakingBacktestTimeZone: document.querySelector("#stakingBacktestTimeZone"),
  stakingBacktestSliceHours: document.querySelector("#stakingBacktestSliceHours"),
  stakingBacktestBaseStake: document.querySelector("#stakingBacktestBaseStake"),
  stakingBacktestStepStake: document.querySelector("#stakingBacktestStepStake"),
  stakingBacktestConservativeStep: document.querySelector("#stakingBacktestConservativeStep"),
  stakingBacktestConservativeMax: document.querySelector("#stakingBacktestConservativeMax"),
  stakingBacktestStandardStep: document.querySelector("#stakingBacktestStandardStep"),
  stakingBacktestStandardMax: document.querySelector("#stakingBacktestStandardMax"),
  stakingBacktestAggressiveStep: document.querySelector("#stakingBacktestAggressiveStep"),
  stakingBacktestAggressiveMax: document.querySelector("#stakingBacktestAggressiveMax"),
  stakingBacktestCustomStep: document.querySelector("#stakingBacktestCustomStep"),
  stakingBacktestCustomMax: document.querySelector("#stakingBacktestCustomMax"),
  stakingBacktestManualField: document.querySelector("#stakingBacktestManualField"),
  stakingBacktestNumbers: document.querySelector("#stakingBacktestNumbers"),
  runStakingBacktestBtn: document.querySelector("#runStakingBacktestBtn"),
  stakingBacktestHint: document.querySelector("#stakingBacktestHint"),
  stakingBacktestStats: document.querySelector("#stakingBacktestStats"),
  stakingBacktestResultMeta: document.querySelector("#stakingBacktestResultMeta"),
  stakingBacktestRows: document.querySelector("#stakingBacktestRows"),
  stakingBacktestSegmentMeta: document.querySelector("#stakingBacktestSegmentMeta"),
  stakingBacktestSegmentRows: document.querySelector("#stakingBacktestSegmentRows"),
  currentBacktestView: document.querySelector("#currentBacktestView"),
  currentBacktestMeta: document.querySelector("#currentBacktestMeta"),
  currentBacktestSource: document.querySelector("#currentBacktestSource"),
  currentBacktestSlot: document.querySelector("#currentBacktestSlot"),
  currentBacktestStartDateTime: document.querySelector("#currentBacktestStartDateTime"),
  currentBacktestEndDateTime: document.querySelector("#currentBacktestEndDateTime"),
  currentBacktestDailyStart: document.querySelector("#currentBacktestDailyStart"),
  currentBacktestDailyEnd: document.querySelector("#currentBacktestDailyEnd"),
  currentBacktestTimeZone: document.querySelector("#currentBacktestTimeZone"),
  currentBacktestBaseStake: document.querySelector("#currentBacktestBaseStake"),
  currentBacktestStepStake: document.querySelector("#currentBacktestStepStake"),
  currentBacktestConservativeStep: document.querySelector("#currentBacktestConservativeStep"),
  currentBacktestConservativeMax: document.querySelector("#currentBacktestConservativeMax"),
  currentBacktestStandardStep: document.querySelector("#currentBacktestStandardStep"),
  currentBacktestStandardMax: document.querySelector("#currentBacktestStandardMax"),
  currentBacktestAggressiveStep: document.querySelector("#currentBacktestAggressiveStep"),
  currentBacktestAggressiveMax: document.querySelector("#currentBacktestAggressiveMax"),
  runCurrentBacktestBtn: document.querySelector("#runCurrentBacktestBtn"),
  currentBacktestHint: document.querySelector("#currentBacktestHint"),
  currentBacktestStats: document.querySelector("#currentBacktestStats"),
  currentBacktestWarnings: document.querySelector("#currentBacktestWarnings"),
  currentBacktestResultMeta: document.querySelector("#currentBacktestResultMeta"),
  currentBacktestRows: document.querySelector("#currentBacktestRows"),
  fixedTripleObservationView: document.querySelector("#fixedTripleObservationView"),
  fixedTripleObservationMeta: document.querySelector("#fixedTripleObservationMeta"),
  fixedTripleObservationPickCount: document.querySelector("#fixedTripleObservationPickCount"),
  fixedTripleObservationDays: document.querySelector("#fixedTripleObservationDays"),
  fixedTripleObservationTop: document.querySelector("#fixedTripleObservationTop"),
  fixedTripleObservationMinDailyHits: document.querySelector("#fixedTripleObservationMinDailyHits"),
  fixedTripleObservationForwardDays: document.querySelector("#fixedTripleObservationForwardDays"),
  fixedTripleObservationStartDateTime: document.querySelector("#fixedTripleObservationStartDateTime"),
  fixedTripleObservationEndDateTime: document.querySelector("#fixedTripleObservationEndDateTime"),
  fixedTripleObservationTimeZone: document.querySelector("#fixedTripleObservationTimeZone"),
  fixedTripleObservationBaseStake: document.querySelector("#fixedTripleObservationBaseStake"),
  fixedTripleObservationStepStake: document.querySelector("#fixedTripleObservationStepStake"),
  fixedTripleObservationConservativeStep: document.querySelector("#fixedTripleObservationConservativeStep"),
  fixedTripleObservationConservativeMax: document.querySelector("#fixedTripleObservationConservativeMax"),
  runFixedTripleObservationBtn: document.querySelector("#runFixedTripleObservationBtn"),
  fixedTripleObservationStats: document.querySelector("#fixedTripleObservationStats"),
  fixedTripleObservationResultMeta: document.querySelector("#fixedTripleObservationResultMeta"),
  fixedTripleObservationRows: document.querySelector("#fixedTripleObservationRows"),
  fixedTripleOmissionMeta: document.querySelector("#fixedTripleOmissionMeta"),
  fixedTripleOmissionNumbers: document.querySelector("#fixedTripleOmissionNumbers"),
  fixedTripleOmissionDate: document.querySelector("#fixedTripleOmissionDate"),
  runFixedTripleOmissionBtn: document.querySelector("#runFixedTripleOmissionBtn"),
  fixedTripleOmissionStats: document.querySelector("#fixedTripleOmissionStats"),
  fixedTripleOmissionRows: document.querySelector("#fixedTripleOmissionRows"),
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
  strategyAuditView: document.querySelector("#strategyAuditView"),
  pairCount: document.querySelector("#pairCount"),
  pairTable: document.querySelector("#pairTable"),
  quadCount: document.querySelector("#quadCount"),
  quadTable: document.querySelector("#quadTable"),
  historyQuery: document.querySelector("#historyQuery"),
  historySort: document.querySelector("#historySort"),
  historyPageSize: document.querySelector("#historyPageSize"),
  historySearchBtn: document.querySelector("#historySearchBtn"),
  historyCount: document.querySelector("#historyCount"),
  historyRunMeta: document.querySelector("#historyRunMeta"),
  historyRunStats: document.querySelector("#historyRunStats"),
  historyTable: document.querySelector("#historyTable"),
  historyView: document.querySelector("#historyView"),
  prevPageBtn: document.querySelector("#prevPageBtn"),
  nextPageBtn: document.querySelector("#nextPageBtn"),
  pageInfo: document.querySelector("#pageInfo"),
  toast: document.querySelector("#toast"),
};

const TOOL_MODAL_VIEWS = new Set(["martingale", "backtest"]);
const PREDICTION_PANEL_DEFAULT = "a";
const PREDICTION_PANEL_B = "b";
const PREDICTION_PANEL_C = "c";
const PREDICTION_PANEL_D = "d";
const PREDICTION_PANEL_E = "e";
const PREDICTION_PANEL_M = "m";
const PREDICTION_PANEL_F = "f";
const PREDICTION_PANEL_G = "g";
const CDE_KILL_BACKTEST_GAMES = new Set(["poland_keno_20_70"]);
const STRATEGY_AUDIT_STABILITY_GAMES = ["poland_keno_20_70"];
const STRATEGY_AUDIT_STABILITY_WINDOW = 360;
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

function fmtSignedPct(value, digits = 2) {
  if (!Number.isFinite(value)) return "--";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${(value * 100).toFixed(digits)}%`;
}

function fmtNumber(value, digits = 2) {
  if (!Number.isFinite(value)) return "--";
  return value.toFixed(digits);
}

function fmtInt(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString("zh-CN") : "--";
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

function buildStrategyAuditQuery() {
  const params = new URLSearchParams();
  params.set("game", state.currentGame?.key || els.gameSelect.value || "");
  params.set("window", els.strategyAuditWindow?.value || "180");
  params.set("trainWindow", els.strategyAuditTrain?.value || "360");
  return params;
}

function buildStrategyAuditQueryForGame(gameKey, options = {}) {
  const params = new URLSearchParams();
  params.set("game", gameKey);
  params.set("window", String(options.window || STRATEGY_AUDIT_STABILITY_WINDOW));
  params.set("trainWindow", String(options.trainWindow || els.strategyAuditTrain?.value || "360"));
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
  if (panel === PREDICTION_PANEL_M) return PREDICTION_PANEL_M;
  return panel === PREDICTION_PANEL_B ? PREDICTION_PANEL_B : PREDICTION_PANEL_DEFAULT;
}

function normalizeRecordPredictionPanel(panel) {
  return normalizePredictionPanel(panel || PREDICTION_PANEL_DEFAULT);
}

function predictionPanelState(panel = state.predictionPanel) {
  return state.predictionPanels[normalizePredictionPanel(panel)] || state.predictionPanels[PREDICTION_PANEL_DEFAULT];
}

function predictionPanelLabel(panel = state.predictionPanel) {
  const panelKey = normalizePredictionPanel(panel);
  if (panelKey === PREDICTION_PANEL_G) return "旧G计划";
  if (panelKey === PREDICTION_PANEL_F) return "旧F计划";
  if (panelKey === PREDICTION_PANEL_E) return "E计划";
  if (panelKey === PREDICTION_PANEL_D) return "D计划";
  if (panelKey === PREDICTION_PANEL_C) return "旧C计划";
  if (panelKey === PREDICTION_PANEL_M) return "C计划";
  return panelKey === PREDICTION_PANEL_B ? "B计划" : "A计划";
}

function predictionPanelForView(view) {
  if (view === "predictionE") return PREDICTION_PANEL_E;
  if (view === "predictionD") return PREDICTION_PANEL_D;
  if (view === "predictionM") return PREDICTION_PANEL_M;
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
  state.predictionTrackingSlot = slot.predictionTrackingSlot || "all";
  state.predictionTrackingDay = slot.predictionTrackingDay || "";
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
  const panelKey = normalizePredictionPanel(panel);
  const slot = predictionPanelState(panelKey);
  const values = new Set(predictionTrackingSlotOptions(panelKey).map(([value]) => value));
  if (!values.has(slot.predictionTrackingSlot || "all")) {
    slot.predictionTrackingSlot = "all";
    slot.predictionTrackingPage = 1;
  }
  syncPredictionPanelMirror(panelKey);
}

function predictionPanelForOptions(options = {}) {
  if (options.panel) return normalizePredictionPanel(options.panel);
  if (state.activeView === "predictionE") return PREDICTION_PANEL_E;
  if (state.activeView === "predictionM") return PREDICTION_PANEL_M;
  if (state.activeView === "predictionD") return PREDICTION_PANEL_D;
  if (state.activeView === "predictionB") return PREDICTION_PANEL_B;
  if (state.activeView === "prediction") return PREDICTION_PANEL_DEFAULT;
  return normalizePredictionPanel(state.predictionPanel);
}

function currentGameSupportsAnalysis() {
  return false;
}

function currentGameSupportsStrategyAudit() {
  return currentGameSupportsPredictions();
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
    view === "predictionM" ||
    view === "predictionD" ||
    view === "predictionE" ||
    view === "stakingBacktest" ||
    view === "currentBacktest" ||
    view === "fixedTripleObservation"
  ) {
    return currentGameSupportsPredictions();
  }
  if (view === "analysis") return currentGameSupportsAnalysis();
  if (view === "strategyAudit") return currentGameSupportsStrategyAudit();
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
  return null;
}

function renderTabState() {
  const activeView = state.activeModal || state.activeView;
  for (const button of document.querySelectorAll(".tab-btn")) {
    button.classList.toggle("active", button.dataset.view === activeView);
  }
}

function showHistoryView() {
  closeToolModal();
  state.activeView = "history";
  renderTabState();
  document.querySelector("#predictionView")?.classList.remove("active");
  document.querySelector("#martingaleView")?.classList.remove("active");
  document.querySelector("#backtestView")?.classList.remove("active");
  document.querySelector("#stakingBacktestView")?.classList.remove("active");
  document.querySelector("#currentBacktestView")?.classList.remove("active");
  document.querySelector("#fixedTripleObservationView")?.classList.remove("active");
  document.querySelector("#analysisView")?.classList.remove("active");
  document.querySelector("#strategyAuditView")?.classList.remove("active");
  document.querySelector("#historyView")?.classList.add("active");
  if (!state.history) loadHistory();
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
    view === "predictionM" ||
    view === "predictionD" ||
    view === "predictionE"
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
  if (view === "strategyAudit" && !state.strategyAudit) loadStrategyAudit();
  if (view === "stakingBacktest") {
    syncStakingBacktestControls();
    if (!state.stakingBacktest) loadStakingBacktest();
  }
  if (view === "currentBacktest" && !state.currentBacktest) loadCurrentBacktest();
  if (view === "fixedTripleObservation" && !state.fixedTripleObservation) loadFixedTripleObservation();
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

function stopPredictionSyncRetry() {
  if (state.predictionSyncRetryTimer) {
    window.clearTimeout(state.predictionSyncRetryTimer);
    state.predictionSyncRetryTimer = null;
  }
}

function schedulePredictionSyncRetry(panel) {
  stopPredictionSyncRetry();
  state.predictionSyncRetryTimer = window.setTimeout(() => {
    state.predictionSyncRetryTimer = null;
    if (state.activeView.startsWith("prediction") && state.predictionPanel === panel) {
      loadPrediction({ force: true, preserve: true, panel });
    }
  }, 5000);
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
  const parts = ["最近一次同步未命中本地已有记录，建议到服务器确认历史连续性。"];
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
  state.strategyAudit = null;
  state.strategyAuditStability = null;
  state.cdeBacktestPage = 1;
  for (const slot of Object.values(state.predictionPanels)) {
    slot.prediction = null;
    slot.predictionTracking = null;
    slot.predictionTrackingPage = 1;
    slot.predictionTrackingStatus = "all";
    slot.predictionTrackingSlot = "all";
    slot.predictionTrackingDay = "";
    slot.adjacentStats = null;
    slot.adjacentHitPage = 1;
    slot.adjacentHitQuery = "";
    slot.adjacentHits = null;
  }
  syncPredictionPanelMirror();
  state.backtest = null;
  state.backtestScan = null;
  state.stakingBacktest = null;
  state.currentBacktest = null;
  state.fixedTripleObservation = null;
  state.fixedTripleOmission = null;
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
    showHistoryView();
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
    els.strategyAuditRunBtn,
    els.runBacktestBtn,
    els.runBacktestScanBtn,
    els.runStakingBacktestBtn,
    els.runCurrentBacktestBtn,
    els.runFixedTripleObservationBtn,
    els.runFixedTripleOmissionBtn,
    els.generateMartingaleBtn,
    els.predictionAutoToggleBtn,
    els.predictionAutoRunBtn,
    els.telegramSaveBtn,
    els.telegramTestBtn,
    els.telegramNotifyNowBtn,
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
  if (!isLoading && state.strategyAudit && els.strategyAuditKillRows) {
    renderStrategyAudit();
  }
}

function renderAllGamesSyncLog(payload) {
  state.lastSync = payload;
  updateSyncGapWarnings(payload);
  const modeLabel = payload.mode === "full" ? "同步" : "同步";
  const current = payload.currentResult;
  const currentLabel = current?.game?.shortName || payload.game?.shortName || "";
  const currentRows = Number(current?.newRows || 0);
  const newRows = Number(payload.newRows || 0);
  const bcRows = Number(payload.bcNewRows || 0);
  const etiposRows = Number(payload.etiposNewRows || 0);
  const settledPredictions = Number(payload.settledPredictions || 0);
  els.lastSyncSummary.textContent = `${modeLabel} · 当前 ${currentLabel} +${currentRows} 期 · 总新增 ${newRows} 期 · ${payload.successCount}/${payload.totalCount} 成功`;
  els.lastSyncTime.textContent = fmtDate(payload.generatedAt);
  els.lastBcRows.textContent = bcRows.toLocaleString("zh-CN");
  els.lastEtiposRows.textContent = etiposRows.toLocaleString("zh-CN");
  if (els.lastSettledPredictions) {
    els.lastSettledPredictions.textContent = settledPredictions.toLocaleString("zh-CN");
  }

  const warnings = [];
  if (payload.possibleGapGames?.length) {
    warnings.push(`这些彩种本次同步未命中已有记录，请确认历史连续性：${payload.possibleGapGames.join("、")}。`);
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
    els.lastSyncError.textContent = "同步完成，当前彩种已刷新。";
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
    return `同步完成：无新增开奖号，${successText}`;
  }
  const detailText = changedGames
    .map((item) => `${item.label}新增${item.newRows.toLocaleString("zh-CN")}期开奖号`)
    .join("；");
  return `同步完成：${detailText}，${successText}`;
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
  const modeLabel = "同步";
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
      `本次同步未命中本地已有记录：抓取 ${syncMeta.pagesFetched || "--"} 页，最旧抓取 ${oldestFetched}，本地原最新 ${newestExisting}。请确认历史连续性。`,
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
  renderPredictionTrackingSlotFilter({ panel });
  els.predictionWindow.textContent = "预测计算中";
  els.predictionMethod.textContent =
    panel === PREDICTION_PANEL_D
      ? "生成共识、拆解、逆向、形态四类2码/3码观察候选"
      : panel === PREDICTION_PANEL_E
      ? "生成E4/E5/E6/E7连号结构观察候选"
      : panel === PREDICTION_PANEL_M
      ? "审计低组数2码/3码候选，最多保留4组"
      : panel === PREDICTION_PANEL_B
        ? "读取A计划规则并排除A候选号"
        : "读取最新开奖并生成策略候选";
  const showKillPanel = panel === PREDICTION_PANEL_B;
  if (els.predictionKillPanel) {
    els.predictionKillPanel.classList.toggle("hidden", !showKillPanel);
  }
  if (els.predictionKillLabel) {
    els.predictionKillLabel.textContent = "A计划杀号";
  }
  if (els.predictionKillSummary) {
    els.predictionKillSummary.textContent = showKillPanel ? "计算排除号..." : "--";
  }
  if (els.predictionKillNumbers) {
    els.predictionKillNumbers.innerHTML = showKillPanel
      ? '<span class="muted">等待A计划杀号</span>'
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
    showHistoryView();
    return;
  }
  setLoading(true, "预测中");
  if (!options.preserve || !slot.prediction) {
    renderPredictionLoading();
  }
  try {
    const params = new URLSearchParams({
      game: currentGameKey(),
      panel,
      autoSync: options.retrySync ? "1" : "0",
    });
    const url = `/api/predictions?${params.toString()}`;
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
    if (data?.predictions?.trackingReady === false) {
      schedulePredictionSyncRetry(panel);
    } else if (state.predictionPanel === panel) {
      stopPredictionSyncRetry();
    }
    if (state.predictionPanel === panel) {
      renderPredictionPage();
    }
    loadPredictionTracking({ silent: true, panel });
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
      slot: slot.predictionTrackingSlot || "all",
      day: slot.predictionTrackingDay || "",
      page: String(slot.predictionTrackingPage || 1),
      pageSize: "20",
    });
    params.set("autoSync", options.autoSync === true ? "1" : "0");
    const response = await fetch(`/api/prediction-tracking?${params.toString()}`);
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    if (!payloadMatchesCurrentGame(data)) return null;
    const updates = {
      predictionTracking: data,
      predictionTrackingPage: Number(data.page || 1),
      predictionTrackingSlot: data.slotFilter || slot.predictionTrackingSlot || "all",
      predictionTrackingDay: data.dayFilter || slot.predictionTrackingDay || "",
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
  return null;
}

async function loadAdjacentHits(options = {}) {
  return null;
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
          refreshAdjacent: false,
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
  return !state.activeModal && ["prediction", "predictionB", "predictionM", "predictionD"].includes(state.activeView);
}

function startPredictionAutoPolling(delayMs = 5000) {
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
      clearResponseCache();
      for (const slot of Object.values(state.predictionPanels)) {
        slot.prediction = null;
      }
      await loadPrediction({ force: true, preserve: false, panel: state.predictionPanel, retrySync: true });
      await loadPredictionTracking({ silent: true, panel: state.predictionPanel });
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

async function savePredictionAutoGames() {
  if (!els.predictionAutoGameToggles) return;
  const inputs = [...els.predictionAutoGameToggles.querySelectorAll("[data-auto-game]")];
  const selected = inputs.filter((input) => input.checked);
  if (!selected.length) {
    showToast("至少保留一个自动追踪彩种", true);
    renderPredictionAutoGameToggles();
    return;
  }
  const games = {};
  for (const input of inputs) {
    games[input.dataset.autoGame] = { enabled: Boolean(input.checked) };
  }
  setLoading(true, "保存追踪彩种");
  try {
    const response = await fetch("/api/prediction-auto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "save", config: { games } }),
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
    state.predictionAuto = data;
    renderPredictionAutoStatus();
    showToast("已保存自动追踪彩种");
  } catch (error) {
    showToast(`保存追踪彩种失败：${error.message}`, true);
    renderPredictionAutoGameToggles();
  } finally {
    setLoading(false);
  }
}

function renderTelegramStatus() {
  if (!els.telegramStatus) return;
  const data = state.telegram || {};
  const config = data.config || {};
  const stateInfo = data.state || {};
  const enabled = Boolean(config.enabled);
  const tokenConfigured = Boolean(config.tokenConfigured);
  els.telegramStatus.textContent = enabled
    ? tokenConfigured
      ? "已启用"
      : "已启用，缺少token"
    : "已关闭";
  els.telegramStatus.title = tokenConfigured ? "Telegram token 已配置" : "需要在本地环境或 local 配置中设置 token";
  if (els.telegramEnabled) els.telegramEnabled.checked = enabled;
  if (els.telegramAllGames) els.telegramAllGames.checked = Boolean(config.allGames);
  if (els.telegramChannel) els.telegramChannel.value = config.channelChatId || "@Keno100x";
  if (els.telegramInviteLink) els.telegramInviteLink.value = config.inviteLink || "";
  if (els.telegramDrawLink) els.telegramDrawLink.value = config.drawLink || "";
  if (els.telegramHint) {
    const errors = Array.isArray(stateInfo.lastErrors) ? stateInfo.lastErrors : [];
    els.telegramHint.textContent = errors.length
      ? `最近错误：${errors[errors.length - 1].stage || "--"} ${errors[errors.length - 1].error || ""}`
      : tokenConfigured
        ? `已记录计划 ${stateInfo.sentPlanBatches || 0} 批，结算 ${stateInfo.sentResultBatches || 0} 批`
        : "token 从本地环境或 local 配置读取，不显示在页面。";
  }
  if (els.telegramGameToggles) {
    const games = config.games || {};
    els.telegramGameToggles.innerHTML = (state.games || [])
      .map((game) => {
        const checked = Boolean(games[game.key]?.enabled);
        return `<label class="telegram-game-toggle">
          <input type="checkbox" data-telegram-game="${escapeHtml(game.key)}" ${checked ? "checked" : ""} />
          <span>${escapeHtml(game.shortName)}</span>
        </label>`;
      })
      .join("");
  }
}

async function loadTelegramStatus(options = {}) {
  if (!els.telegramStatus) return null;
  try {
    const response = await fetch("/api/telegram");
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
    state.telegram = data;
    renderTelegramStatus();
    return data;
  } catch (error) {
    if (!options.silent) showToast(`读取 Telegram 状态失败：${error.message}`, true);
    return null;
  }
}

function buildTelegramConfigPayload() {
  const games = {};
  for (const input of document.querySelectorAll("[data-telegram-game]")) {
    games[input.dataset.telegramGame] = { enabled: Boolean(input.checked) };
  }
  return {
    enabled: Boolean(els.telegramEnabled?.checked),
    allGames: Boolean(els.telegramAllGames?.checked),
    channelChatId: els.telegramChannel?.value || "@Keno100x",
    inviteLink: els.telegramInviteLink?.value || "",
    drawLink: els.telegramDrawLink?.value || "",
    games,
  };
}

async function updateTelegram(action) {
  setLoading(true, action === "test" ? "测试 Telegram" : "Telegram 处理中");
  try {
    const body = action === "save"
      ? { action, config: buildTelegramConfigPayload() }
      : { action };
    const response = await fetch("/api/telegram", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
    state.telegram = data.status || data;
    renderTelegramStatus();
    showToast(action === "test" ? "Telegram 测试消息已发送" : action === "notifynow" ? "Telegram 已立即检查" : "Telegram 配置已保存");
  } catch (error) {
    showToast(`Telegram 操作失败：${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

async function loadAnalysis(options = {}) {
  state.analysis = null;
  showToast("C回测已停用；当前只保留 A/B/C计划 和策略审计。", true);
  return;
  if (!currentGameSupportsAnalysis()) {
    showToast("C 杀号回测当前只支持波兰", true);
    return;
  }
  if (!options.keepPage) {
    state.cdeBacktestPage = 1;
  }
  setLoading(true, "C回测中");
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
    showToast(`加载C回测失败：${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

async function loadStrategyAudit(options = {}) {
  if (!currentGameSupportsStrategyAudit()) {
    showToast("该彩种当前不支持策略审计", true);
    return;
    showToast("策略信号审计当前只支持波兰", true);
    return;
  }
  setLoading(true, "策略审计中");
  state.strategyAuditStability = null;
  renderStrategyAuditLoading();
  try {
    const url = `/api/strategy-signal-audit?${buildStrategyAuditQuery().toString()}`;
    const cached = options.force ? null : cacheGet(url);
    if (cached) {
      if (!payloadMatchesCurrentGame(cached)) return;
      state.strategyAudit = cached;
      renderStrategyAudit();
      return;
    }
    const response = await fetch(url);
    const data = await response.json().catch(() => null);
    if (!response.ok || data?.ok === false) {
      throw new Error(data?.error || `HTTP ${response.status}`);
    }
    if (!payloadMatchesCurrentGame(data)) return;
    state.strategyAudit = data;
    cacheSet(url, data);
    renderStrategyAudit();
  } catch (error) {
    showToast(`加载策略审计失败：${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

async function loadStrategyAuditStability(options = {}) {
  if (!els.strategyAuditStabilityRows) return;
  const selectedGame = currentGameKey();
  const trainWindow = String(els.strategyAuditTrain?.value || "360");
  if (els.strategyAuditStabilityMeta) {
    els.strategyAuditStabilityMeta.textContent = "波兰 60/180/360 稳定性计算中";
  }
  if (els.strategyAuditStabilityRows) {
    els.strategyAuditStabilityRows.innerHTML = '<tr><td colspan="8"><span class="muted">多窗口稳定性对照计算中</span></td></tr>';
  }
  try {
    const results = await Promise.allSettled(
      STRATEGY_AUDIT_STABILITY_GAMES.map(async (gameKey) => {
        const url = `/api/strategy-signal-audit?${buildStrategyAuditQueryForGame(gameKey, {
          window: STRATEGY_AUDIT_STABILITY_WINDOW,
          trainWindow,
        }).toString()}`;
        const cached = options.force ? null : cacheGet(url);
        if (cached) return cached;
        const response = await fetch(url);
        const data = await response.json().catch(() => null);
        if (!response.ok || data?.ok === false) {
          throw new Error(`${gameKey}: ${data?.error || `HTTP ${response.status}`}`);
        }
        cacheSet(url, data);
        return data;
      }),
    );
    if (currentGameKey() !== selectedGame || String(els.strategyAuditTrain?.value || "360") !== trainWindow) return;
    const items = [];
    const errors = [];
    results.forEach((result, index) => {
      if (result.status === "fulfilled") {
        items.push(result.value);
      } else {
        errors.push({
          game: STRATEGY_AUDIT_STABILITY_GAMES[index],
          message: result.reason?.message || String(result.reason || "加载失败"),
        });
      }
    });
    state.strategyAuditStability = {
      generatedAt: new Date().toISOString(),
      sourceGame: selectedGame,
      trainWindow,
      window: STRATEGY_AUDIT_STABILITY_WINDOW,
      items,
      errors,
    };
    renderStrategyAuditStability();
  } catch (error) {
    state.strategyAuditStability = {
      generatedAt: new Date().toISOString(),
      sourceGame: selectedGame,
      trainWindow,
      window: STRATEGY_AUDIT_STABILITY_WINDOW,
      items: [],
      errors: [{ game: "all", message: error.message || String(error) }],
    };
    renderStrategyAuditStability();
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
    showHistoryView();
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

function syncStakingBacktestControls() {
  if (!els.stakingBacktestSource || !els.stakingBacktestManualField) return;
  const manual = els.stakingBacktestSource.value === "manual";
  els.stakingBacktestManualField.classList.toggle("hidden", !manual);
  if (els.stakingBacktestMeta) {
    els.stakingBacktestMeta.textContent = manual ? "手动号码按固定票回放" : "默认读取当前 C计划 4 张候选票";
  }
}

function buildStakingBacktestQuery() {
  const customWindow = Number(els.stakingBacktestCustomWindow?.value || 0);
  const windowValue = Number.isFinite(customWindow) && customWindow > 0
    ? String(Math.max(30, Math.min(50000, Math.floor(customWindow))))
    : els.stakingBacktestWindow?.value || "1000";
  const params = new URLSearchParams({
    game: currentGameKey(),
    source: els.stakingBacktestSource?.value || "c_plan",
    window: windowValue,
    timeZone: els.stakingBacktestTimeZone?.value || "Asia/Shanghai",
    sliceHours: els.stakingBacktestSliceHours?.value || "2",
    baseStake: String(parseNumberInput(els.stakingBacktestBaseStake, 1)),
    stepStake: String(parseNumberInput(els.stakingBacktestStepStake, 1)),
    conservativeStepMisses: String(parseNumberInput(els.stakingBacktestConservativeStep, 30)),
    conservativeMaxStake: String(parseNumberInput(els.stakingBacktestConservativeMax, 5)),
    standardStepMisses: String(parseNumberInput(els.stakingBacktestStandardStep, 20)),
    standardMaxStake: String(parseNumberInput(els.stakingBacktestStandardMax, 8)),
    aggressiveStepMisses: String(parseNumberInput(els.stakingBacktestAggressiveStep, 10)),
    aggressiveMaxStake: String(parseNumberInput(els.stakingBacktestAggressiveMax, 12)),
    customStepMisses: String(parseNumberInput(els.stakingBacktestCustomStep, 20)),
    customStepStake: String(parseNumberInput(els.stakingBacktestStepStake, 1)),
    customMaxStake: String(parseNumberInput(els.stakingBacktestCustomMax, 8)),
  });
  if (params.get("source") === "manual") {
    params.set("numbers", els.stakingBacktestNumbers?.value || "");
  }
  if (els.stakingBacktestStartDateTime?.value) {
    params.set("startDateTime", els.stakingBacktestStartDateTime.value);
  }
  if (els.stakingBacktestEndDateTime?.value) {
    params.set("endDateTime", els.stakingBacktestEndDateTime.value);
  }
  if (els.stakingBacktestDailyStart?.value) {
    params.set("dailyStart", els.stakingBacktestDailyStart.value);
  }
  if (els.stakingBacktestDailyEnd?.value) {
    params.set("dailyEnd", els.stakingBacktestDailyEnd.value);
  }
  return params;
}

async function loadStakingBacktest() {
  if (!currentGameSupportsPredictions()) {
    showHistoryView();
    return;
  }
  syncStakingBacktestControls();
  setLoading(true, "固定回测中");
  if (els.stakingBacktestResultMeta) {
    els.stakingBacktestResultMeta.textContent = "回测中...";
  }
  try {
    const response = await fetch(`/api/staking-backtest?${buildStakingBacktestQuery().toString()}`);
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    if (!payloadMatchesCurrentGame(data)) return;
    state.stakingBacktest = data;
    renderStakingBacktest(data);
  } catch (error) {
    showToast(`固定回测失败：${error.message}`, true);
    if (els.stakingBacktestResultMeta) {
      els.stakingBacktestResultMeta.textContent = "回测失败";
    }
  } finally {
    setLoading(false);
  }
}

function stakingPolicyCell(policy) {
  if (!policy || typeof policy !== "object") return '<span class="muted">--</span>';
  const net = Number(policy.netProfit || 0);
  const roi = Number(policy.roi || 0);
  const className = net > 0 ? "positive" : net < 0 ? "negative" : "";
  const ladder = policy.kind === "flat" ? "不加档" : `每${fmtInt(policy.stepMisses)}期 +${fmtYuan(Number(policy.stepStake || 0), 2)}`;
  return `<div class="staking-policy-cell">
    <strong class="${className}">${fmtYuan(net, 2, true)}</strong>
    <span>ROI ${fmtPct(roi, 2)}</span>
    <span>投入 ${fmtYuan(Number(policy.totalStake || 0), 2)}</span>
    <span>回撤 ${fmtYuan(Number(policy.maxDrawdown || 0), 2)}</span>
    <span>下一注 ${fmtYuan(Number(policy.nextStake || 0), 2)}</span>
    <small>${escapeHtml(ladder)}</small>
  </div>`;
}

function stakingSegmentPolicyCell(policy) {
  if (!policy || typeof policy !== "object") return '<span class="muted">--</span>';
  const net = Number(policy.netProfit || 0);
  const roi = Number(policy.roi || 0);
  const peak = Number(policy.peakProfit);
  const peakTime = policy.peakTimeUtc ? fmtTime(policy.peakTimeUtc) : "";
  const className = net > 0 ? "positive" : net < 0 ? "negative" : "";
  const peakLine = Number.isFinite(peak)
    ? `<small>峰值净利 ${fmtYuan(peak, 2, true)}${peakTime ? ` · ${escapeHtml(peakTime)}` : ""}</small>`
    : "";
  return `<div class="staking-segment-policy-cell">
    <strong class="${className}">${fmtYuan(net, 2, true)}</strong>
    <span>ROI ${fmtPct(roi, 2)}</span>
    ${peakLine}
    <small>投入 ${fmtYuan(Number(policy.totalStake || 0), 2)}</small>
  </div>`;
}

function stakingVerdictClass(verdict) {
  const tone = String(verdict?.tone || "");
  if (tone === "good") return "good";
  if (tone === "bad") return "bad";
  return "watch";
}

function stakingTimeFilterText(data) {
  const filter = data?.timeFilter || {};
  const parts = [];
  if (filter.startDateTime || filter.endDateTime) {
    parts.push(`日期 ${filter.startDateTime || "不限"} - ${filter.endDateTime || "不限"}`);
  }
  if (filter.dailyStart || filter.dailyEnd) {
    parts.push(`每日 ${filter.dailyStart || "00:00"} - ${filter.dailyEnd || "23:59"}`);
  }
  if (filter.gameDayTimeZone) {
    parts.push(`开奖日 ${filter.gameDayTimeZone}`);
  }
  parts.push(filter.timeZone === "UTC" ? "UTC" : "北京时间");
  return parts.join(" · ");
}

function renderStakingBacktestSegments(data) {
  const segments = Array.isArray(data?.timeSegments) ? data.timeSegments : [];
  const filter = data?.timeFilter || {};
  if (els.stakingBacktestSegmentMeta) {
    els.stakingBacktestSegmentMeta.textContent = `${fmtInt(filter.sliceHours || 2)}小时切片 · ${stakingTimeFilterText(data)} · 标准档排序`;
  }
  if (!els.stakingBacktestSegmentRows) return;
  if (!segments.length) {
    els.stakingBacktestSegmentRows.innerHTML = '<tr><td colspan="9"><span class="muted">暂无时段统计</span></td></tr>';
    return;
  }
  els.stakingBacktestSegmentRows.innerHTML = segments
    .map((segment) => {
      const verdict = segment.verdict || {};
      const verdictClass = stakingVerdictClass(verdict);
      const reasons = Array.isArray(verdict.reasons) ? verdict.reasons : [];
      const policies = segment.policies || {};
      return `<tr class="staking-backtest-row ${verdictClass}">
        <td>${fmtInt(segment.rank || 0)}</td>
        <td><strong>${escapeHtml(segment.label || "--")}</strong></td>
        <td>
          <div class="staking-miss-cell">
            <strong>${fmtInt(segment.rows || 0)}</strong>
            <span>${Number(segment.rows || 0) < 300 ? "样本慎用" : "样本可看"}</span>
          </div>
        </td>
        <td>${stakingSegmentPolicyCell(policies.flat)}</td>
        <td>${stakingSegmentPolicyCell(policies.conservative)}</td>
        <td>${stakingSegmentPolicyCell(policies.standard)}</td>
        <td>${stakingSegmentPolicyCell(policies.aggressive)}</td>
        <td>${stakingSegmentPolicyCell(policies.custom)}</td>
        <td>
          <div class="staking-verdict ${verdictClass}">
            <strong>${escapeHtml(verdict.label || "--")}</strong>
            <span>${escapeHtml(reasons.join("；") || "固定切片统计")}</span>
          </div>
        </td>
      </tr>`;
    })
    .join("");
}

function renderStakingBacktest(data) {
  if (!data) return;
  const tickets = Array.isArray(data.tickets) ? data.tickets : [];
  const summary = data.summary || {};
  const window = data.window || {};
  if (els.stakingBacktestMeta) {
    els.stakingBacktestMeta.textContent = `${data.sourceLabel || "--"} · ${fmtInt(window.rows)}期 · ${fmtDate(data.generatedAt)}`;
  }
  if (els.stakingBacktestResultMeta) {
    els.stakingBacktestResultMeta.textContent = `${data.sourceLabel || "--"} · 回放 ${fmtInt(window.rows)} 期 · ${fmtTime(
      window.startDrawTimeUtc,
    )} - ${fmtTime(window.endDrawTimeUtc)} · ${stakingTimeFilterText(data)}`;
  }
  if (els.stakingBacktestStats) {
    els.stakingBacktestStats.innerHTML = `
      <article class="stat-card">
        <span>候选票</span>
        <strong>${fmtInt(summary.ticketCount || tickets.length)}</strong>
        <small>${escapeHtml(data.sourceLabel || "--")}</small>
      </article>
      <article class="stat-card accent">
        <span>重点观察</span>
        <strong>${fmtInt(summary.focusCount || 0)}</strong>
        <small>平买/保守/标准更稳</small>
      </article>
      <article class="stat-card">
        <span>只观察</span>
        <strong>${fmtInt(summary.watchCount || 0)}</strong>
        <small>有档位优势但证据不足</small>
      </article>
      <article class="stat-card">
        <span>不跟</span>
        <strong>${fmtInt(summary.noFollowCount || 0)}</strong>
        <small>回撤或高档位风险过高</small>
      </article>`;
  }
  if (!els.stakingBacktestRows) return;
  if (!tickets.length) {
    els.stakingBacktestRows.innerHTML = '<tr><td colspan="9"><span class="muted">当前没有可回放的候选票</span></td></tr>';
    return;
  }
  els.stakingBacktestRows.innerHTML = tickets
    .map((ticket) => {
      const verdict = ticket.verdict || {};
      const verdictClass = stakingVerdictClass(verdict);
      const reasons = Array.isArray(verdict.reasons) ? verdict.reasons : [];
      const policies = ticket.policies || {};
      const ci = ticket.recentHitRateCi || [0, 0];
      return `<tr class="staking-backtest-row ${verdictClass}">
        <td>
          <div class="staking-ticket">
            <strong>${escapeHtml(ticket.label || `候选 #${ticket.index || ""}`)}</strong>
            <div class="ticket-balls">${ticketNumberBalls(ticket)}</div>
            <span>${escapeHtml(ticket.auditSourceLabel || ticket.ticketLabel || "--")}</span>
          </div>
        </td>
        <td>
          <div class="staking-odds-cell">
            <strong>${fmtNumber(Number(ticket.odds || 0), 2)}x</strong>
            <span>历史 ${fmtPct(Number(ticket.hitRate || 0), 2)}</span>
            <span>近${fmtInt(ticket.recentWindow || 0)}期 ${fmtPct(Number(ticket.recentHitRate || 0), 2)}</span>
            <small>理论 ${fmtPct(Number(ticket.theoreticalHitRate || 0), 3)} · 区间 ${fmtPct(Number(ci[0] || 0), 2)}-${fmtPct(Number(ci[1] || 0), 2)}</small>
          </div>
        </td>
        <td>${stakingPolicyCell(policies.flat)}</td>
        <td>${stakingPolicyCell(policies.conservative)}</td>
        <td>${stakingPolicyCell(policies.standard)}</td>
        <td>${stakingPolicyCell(policies.aggressive)}</td>
        <td>${stakingPolicyCell(policies.custom)}</td>
        <td>
          <div class="staking-miss-cell">
            <strong>${fmtInt(ticket.currentMiss || 0)} / ${fmtInt(ticket.maxMiss || 0)}</strong>
            <span>当前 / 最长</span>
            <small>最佳 ${escapeHtml(ticket.bestPolicy?.label || "--")}</small>
          </div>
        </td>
        <td>
          <div class="staking-verdict ${verdictClass}">
            <strong>${escapeHtml(verdict.label || "--")}</strong>
            <span>${escapeHtml(reasons.join("；") || "等待更多结算")}</span>
          </div>
        </td>
      </tr>`;
    })
    .join("");
  renderStakingBacktestSegments(data);
}

function buildCurrentBacktestQuery() {
  syncCurrentBacktestSlotOptions();
  const params = new URLSearchParams({
    game: currentGameKey(),
    source: els.currentBacktestSource?.value || "m",
    slot: els.currentBacktestSlot?.value || "p3_1",
    timeZone: els.currentBacktestTimeZone?.value || "Asia/Shanghai",
    baseStake: String(parseNumberInput(els.currentBacktestBaseStake, 1)),
    stepStake: String(parseNumberInput(els.currentBacktestStepStake, 1)),
    conservativeStepMisses: String(parseNumberInput(els.currentBacktestConservativeStep, 30)),
    conservativeMaxStake: String(parseNumberInput(els.currentBacktestConservativeMax, 5)),
    standardStepMisses: String(parseNumberInput(els.currentBacktestStandardStep, 20)),
    standardMaxStake: String(parseNumberInput(els.currentBacktestStandardMax, 8)),
    aggressiveStepMisses: String(parseNumberInput(els.currentBacktestAggressiveStep, 10)),
    aggressiveMaxStake: String(parseNumberInput(els.currentBacktestAggressiveMax, 12)),
    customStepMisses: String(parseNumberInput(els.currentBacktestStandardStep, 20)),
    customStepStake: String(parseNumberInput(els.currentBacktestStepStake, 1)),
    customMaxStake: String(parseNumberInput(els.currentBacktestStandardMax, 8)),
  });
  if (els.currentBacktestStartDateTime?.value) {
    params.set("startDateTime", els.currentBacktestStartDateTime.value);
  }
  if (els.currentBacktestEndDateTime?.value) {
    params.set("endDateTime", els.currentBacktestEndDateTime.value);
  }
  if (els.currentBacktestDailyStart?.value) {
    params.set("dailyStart", els.currentBacktestDailyStart.value);
  }
  if (els.currentBacktestDailyEnd?.value) {
    params.set("dailyEnd", els.currentBacktestDailyEnd.value);
  }
  return params;
}

const CURRENT_BACKTEST_SLOT_OPTIONS = {
  m: [
    ["p3_1", "3码候选#3"],
    ["p3_2", "3码候选#4"],
    ["p3_all", "全部3码候选"],
    ["p2_1", "2码候选#1"],
    ["p2_2", "2码候选#2"],
    ["p2_all", "全部2码候选"],
    ["all", "全部候选"],
  ],
  d: [
    ["p2_2", "2码候选#2"],
    ["p3_4", "3码候选#8"],
    ["all", "全部D2+D8"],
  ],
  e: [
    ["p4_all", "全部E4"],
    ["p5_all", "全部E5"],
    ["p6_all", "全部E6"],
    ["p7_all", "全部E7"],
    ["all", "全部E计划"],
    ...Array.from({ length: 6 }, (_, index) => [`p4_${index + 1}`, `E4候选#${index + 1}`]),
    ...Array.from({ length: 8 }, (_, index) => [`p5_${index + 1}`, `E5候选#${index + 1}`]),
    ...Array.from({ length: 10 }, (_, index) => [`p6_${index + 1}`, `E6候选#${index + 1}`]),
    ...Array.from({ length: 8 }, (_, index) => [`p7_${index + 1}`, `E7候选#${index + 1}`]),
  ],
};

function syncCurrentBacktestSlotOptions() {
  if (!els.currentBacktestSource || !els.currentBacktestSlot) return;
  const source = els.currentBacktestSource.value === "e" ? "e" : els.currentBacktestSource.value === "d" ? "d" : "m";
  const options = CURRENT_BACKTEST_SLOT_OPTIONS[source] || CURRENT_BACKTEST_SLOT_OPTIONS.m;
  const previous = els.currentBacktestSlot.value;
  const allowed = new Set(options.map(([value]) => value));
  if (els.currentBacktestSlot.dataset.source === source && allowed.has(previous)) {
    return;
  }
  els.currentBacktestSlot.innerHTML = "";
  for (const [value, label] of options) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    els.currentBacktestSlot.appendChild(option);
  }
  els.currentBacktestSlot.value = allowed.has(previous) ? previous : source === "d" ? "p3_4" : source === "e" ? "p4_all" : "p3_1";
  els.currentBacktestSlot.dataset.source = source;
}

async function loadCurrentBacktest() {
  if (!currentGameSupportsPredictions()) {
    showHistoryView();
    return;
  }
  setLoading(true, "当前回测中");
  if (els.currentBacktestResultMeta) {
    els.currentBacktestResultMeta.textContent = "回测中...";
  }
  try {
    const response = await fetch(`/api/current-staking-backtest?${buildCurrentBacktestQuery().toString()}`);
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    if (!payloadMatchesCurrentGame(data)) return;
    state.currentBacktest = data;
    renderCurrentBacktest(data);
  } catch (error) {
    showToast(`当前回测失败：${error.message}`, true);
    if (els.currentBacktestResultMeta) {
      els.currentBacktestResultMeta.textContent = "回测失败";
    }
  } finally {
    setLoading(false);
  }
}

function renderCurrentBacktest(data) {
  if (!data) return;
  const days = Array.isArray(data.days) ? data.days : [];
  const summary = data.summary || {};
  const coverage = data.coverage || {};
  const missingTracking = Number(coverage.missingTrackingDraws || 0);
  const historyDraws = Number(coverage.historyDraws || 0);
  const policies = summary.policies || {};
  const conservative = policies.conservative || {};
  const selectionText = `${data.selection?.sourceLabel || "C计划"} · ${data.selection?.label || "--"}`;
  if (els.currentBacktestMeta) {
    els.currentBacktestMeta.textContent = `${selectionText} · ${fmtInt(coverage.selectedDraws || 0)}期 · ${fmtDate(data.generatedAt)}`;
  }
  if (els.currentBacktestResultMeta) {
    const coverageText = historyDraws ? ` · 追踪覆盖 ${fmtInt(summary.rounds || 0)}/${fmtInt(historyDraws)}期` : "";
    els.currentBacktestResultMeta.textContent = `${selectionText} · ${fmtInt(summary.rounds || 0)}期 / ${fmtInt(
      summary.bets || 0,
    )}票${coverageText} · ${fmtTime(coverage.startTimeUtc)} - ${fmtTime(coverage.endTimeUtc)} · ${stakingTimeFilterText(data)}`;
  }
  const warnings = Array.isArray(data.warnings) ? data.warnings : [];
  if (els.currentBacktestWarnings) {
    els.currentBacktestWarnings.classList.toggle("hidden", !warnings.length);
    els.currentBacktestWarnings.textContent = warnings.join(" ");
  }
  if (els.currentBacktestStats) {
    els.currentBacktestStats.innerHTML = `
      <article class="stat-card">
        <span>覆盖天数</span>
        <strong>${fmtInt(summary.days || days.length)}</strong>
        <small>${escapeHtml(selectionText)}</small>
      </article>
      <article class="stat-card ${missingTracking > 0 ? "warn" : ""}">
        <span>追踪覆盖</span>
        <strong>${historyDraws ? `${fmtInt(summary.rounds || 0)}/${fmtInt(historyDraws)}` : fmtInt(summary.rounds || 0)}</strong>
        <small>${missingTracking > 0 ? `缺 ${fmtInt(missingTracking)} 期候选` : "追踪库已结算"}</small>
      </article>
      <article class="stat-card accent">
        <span>保守净利</span>
        <strong class="${Number(conservative.netProfit || 0) >= 0 ? "positive" : "negative"}">${fmtYuan(
          Number(conservative.netProfit || 0),
          2,
          true,
        )}</strong>
        <small>ROI ${fmtPct(Number(conservative.roi || 0), 2)}</small>
      </article>`;
  }
  if (!els.currentBacktestRows) return;
  if (!days.length) {
    els.currentBacktestRows.innerHTML = '<tr><td colspan="7"><span class="muted">没有可回放的真实逐期候选</span></td></tr>';
    return;
  }
  els.currentBacktestRows.innerHTML = days
    .map((day) => {
      const dayPolicies = day.policies || {};
      const verdict = day.verdict || {};
      const verdictClass = stakingVerdictClass(verdict);
      const reasons = Array.isArray(verdict.reasons) ? verdict.reasons : [];
      return `<tr class="staking-backtest-row ${verdictClass}">
        <td>
          <div class="staking-miss-cell">
            <strong>${escapeHtml(day.date || "--")}</strong>
            <span>${fmtTime(day.startTimeUtc)} - ${fmtTime(day.endTimeUtc)}</span>
          </div>
        </td>
        <td>
          <div class="staking-miss-cell">
            <strong>${fmtInt(day.rounds || 0)}期</strong>
            <span>${fmtInt(day.bets || 0)}张票</span>
            <small>${
              day.historyDraws
                ? `开奖 ${fmtInt(day.historyDraws)}期 · 缺 ${fmtInt(day.missingTrackingDraws || 0)}期候选`
                : "未取到开奖覆盖"
            }</small>
          </div>
        </td>
        <td>${stakingSegmentPolicyCell(dayPolicies.flat)}</td>
        <td>${stakingSegmentPolicyCell(dayPolicies.conservative)}</td>
        <td>${stakingSegmentPolicyCell(dayPolicies.standard)}</td>
        <td>${stakingSegmentPolicyCell(dayPolicies.aggressive)}</td>
        <td>
          <div class="staking-verdict ${verdictClass}">
            <strong>${escapeHtml(verdict.label || "--")}</strong>
            <span>${escapeHtml(reasons.join("；") || "真实逐期回放")}</span>
          </div>
        </td>
      </tr>`;
    })
    .join("");
}

function buildFixedTripleObservationQuery() {
  const params = new URLSearchParams({
    game: currentGameKey(),
    pickCount: els.fixedTripleObservationPickCount?.value || "3",
    days: String(parseNumberInput(els.fixedTripleObservationDays, 31)),
    top: String(parseNumberInput(els.fixedTripleObservationTop, 3)),
    minDailyHits: String(parseNumberInput(els.fixedTripleObservationMinDailyHits, 3)),
    forwardDays: String(parseNumberInput(els.fixedTripleObservationForwardDays, 3)),
    timeZone: els.fixedTripleObservationTimeZone?.value || "Asia/Shanghai",
    baseStake: String(parseNumberInput(els.fixedTripleObservationBaseStake, 1)),
    stepStake: String(parseNumberInput(els.fixedTripleObservationStepStake, 1)),
    conservativeStepMisses: String(parseNumberInput(els.fixedTripleObservationConservativeStep, 30)),
    conservativeMaxStake: String(parseNumberInput(els.fixedTripleObservationConservativeMax, 5)),
  });
  if (els.fixedTripleObservationStartDateTime?.value) {
    params.set("startDateTime", els.fixedTripleObservationStartDateTime.value);
  }
  if (els.fixedTripleObservationEndDateTime?.value) {
    params.set("endDateTime", els.fixedTripleObservationEndDateTime.value);
  }
  return params;
}

async function loadFixedTripleObservation() {
  if (!currentGameSupportsPredictions()) {
    showHistoryView();
    return;
  }
  setLoading(true, "频码观察统计中");
  if (els.fixedTripleObservationResultMeta) {
    els.fixedTripleObservationResultMeta.textContent = "统计中...";
  }
  try {
    const response = await fetch(`/api/frequency-observation?${buildFixedTripleObservationQuery().toString()}`);
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    if (!payloadMatchesCurrentGame(data)) return;
    state.fixedTripleObservation = data;
    renderFixedTripleObservation(data);
  } catch (error) {
    showToast(`频码观察失败：${error.message}`, true);
    if (els.fixedTripleObservationResultMeta) {
      els.fixedTripleObservationResultMeta.textContent = "统计失败";
    }
  } finally {
    setLoading(false);
  }
}

function renderFixedTripleObservation(data) {
  if (!data) return;
  const items = Array.isArray(data.items) ? data.items : [];
  const summary = data.summary || {};
  const settings = data.settings || {};
  const pickCount = Number(settings.pickCount || data.items?.[0]?.pickCount || 3);
  if (els.fixedTripleObservationMeta) {
    els.fixedTripleObservationMeta.textContent = `${fmtInt(pickCount)}码 · 近${fmtInt(settings.actualDays || settings.days || 0)}天 · 稳定Top ${fmtInt(
      settings.top || 0,
    )} · 每天≥${fmtInt(settings.minDailyHits || 3)}次 · 后续${fmtInt(settings.forwardDays || 0)}天`;
  }
  if (els.fixedTripleObservationResultMeta) {
    els.fixedTripleObservationResultMeta.textContent = `${escapeHtml(summary.sourceStartDay || "--")} - ${escapeHtml(
      summary.sourceEndDay || "--",
    )} · ${fmtInt(
      summary.items || 0,
    )}组固定${fmtInt(pickCount)}码 · 合格池 ${fmtInt(summary.filteredCombos || 0)} / ${fmtInt(summary.allCombos || 0)} · ${stakingTimeFilterText(data)}`;
  }
  if (els.fixedTripleObservationStats) {
    els.fixedTripleObservationStats.innerHTML = `
      <article class="stat-card">
        <span>统计天数</span>
        <strong>${fmtInt(summary.days || 0)}</strong>
        <small>${escapeHtml(summary.sourceStartDay || "--")} - ${escapeHtml(summary.sourceEndDay || "--")}</small>
      </article>
      <article class="stat-card">
        <span>合格固定${fmtInt(pickCount)}码</span>
        <strong>${fmtInt(summary.filteredCombos || 0)}</strong>
        <small>每天≥${fmtInt(settings.minDailyHits || 3)}次</small>
      </article>
      <article class="stat-card accent">
        <span>历史保守盈利</span>
        <strong>${fmtInt(summary.profitableHistoryConservative || 0)}</strong>
        <small>输出 ${fmtInt(summary.items || items.length)} 组</small>
      </article>
      <article class="stat-card">
        <span>后续观察</span>
        <strong>${fmtInt(summary.forwardDays || 0)}</strong>
        <small>${summary.forwardStartDay ? `${escapeHtml(summary.forwardStartDay)} - ${escapeHtml(summary.forwardEndDay || "--")}` : "待未来开奖"}</small>
      </article>`;
  }
  if (!els.fixedTripleObservationRows) return;
  if (!items.length) {
    els.fixedTripleObservationRows.innerHTML = `<tr><td colspan="8"><span class="muted">没有满足跨天过滤条件的固定${fmtInt(pickCount)}码；可以降低“最低每日出现”。</span></td></tr>`;
    return;
  }
  if (els.fixedTripleOmissionNumbers && !els.fixedTripleOmissionNumbers.value && items[0]?.numbers) {
    els.fixedTripleOmissionNumbers.value = (items[0].numbers || []).join("-");
  }
  els.fixedTripleObservationRows.innerHTML = items
    .map((item) => {
      const verdict = item.verdict || {};
      const verdictClass = stakingVerdictClass(verdict);
      const reasons = Array.isArray(verdict.reasons) ? verdict.reasons : [];
      return `<tr class="staking-backtest-row ${verdictClass}">
        <td>
          <div class="staking-miss-cell">
            <strong>#${fmtInt(item.rank || 0)}</strong>
            <span>${fmtInt(item.sourceDays || 0)}天全勤</span>
          </div>
        </td>
        <td><div class="staking-ticket"><div class="ticket-balls">${numberBadge(item.numbers || [], "ticket-main")}</div><span>${fmtNumber(Number(item.odds || 0), 2)}x</span></div></td>
        <td>
          <div class="staking-miss-cell">
            <strong>日均 ${fmtNumber(Number(item.averageDailyHits || 0), 2)}</strong>
            <span>最低/最高 ${fmtInt(item.minDailyHits || 0)} / ${fmtInt(item.maxDailyHits || 0)}</span>
            <small>合计 ${fmtInt(item.totalHits || 0)}次 · ${fmtInt(item.sourceDraws || 0)}期</small>
          </div>
        </td>
        <td>${stakingSegmentPolicyCell(item.historyFlat)}</td>
        <td>${stakingSegmentPolicyCell(item.historyConservative)}</td>
        <td>
          <div class="staking-miss-cell">
            <strong>${fmtInt(item.forwardHits || 0)} / ${fmtInt(item.forwardDraws || 0)}</strong>
            <span>${fmtPct(Number(item.forwardHitRate || 0), 2)}</span>
            <small>${item.forwardStartDay ? `${escapeHtml(item.forwardStartDay)} - ${escapeHtml(item.forwardEndDay || "--")}` : "等待后续开奖"}</small>
          </div>
        </td>
        <td>${stakingSegmentPolicyCell(item.forwardConservative)}</td>
        <td>
          <div class="staking-verdict ${verdictClass}">
            <strong>${escapeHtml(verdict.label || "--")}</strong>
            <span>${escapeHtml(reasons.join("；") || "等待后续样本")}</span>
          </div>
        </td>
      </tr>`;
    })
    .join("");
}

function buildFixedTripleOmissionQuery() {
  const numbers = (els.fixedTripleOmissionNumbers?.value || "").trim();
  const params = new URLSearchParams({
    game: currentGameKey(),
    numbers,
    pickCount: els.fixedTripleObservationPickCount?.value || "",
    timeZone: els.fixedTripleObservationTimeZone?.value || "Asia/Shanghai",
    baseStake: String(parseNumberInput(els.fixedTripleObservationBaseStake, 1)),
    stepStake: String(parseNumberInput(els.fixedTripleObservationStepStake, 1)),
    conservativeStepMisses: String(parseNumberInput(els.fixedTripleObservationConservativeStep, 30)),
    conservativeMaxStake: String(parseNumberInput(els.fixedTripleObservationConservativeMax, 5)),
  });
  if (els.fixedTripleOmissionDate?.value) {
    params.set("date", els.fixedTripleOmissionDate.value);
  }
  return params;
}

async function loadFixedTripleOmission() {
  const numbers = (els.fixedTripleOmissionNumbers?.value || "").trim();
  if (!numbers) {
    showToast("请先输入固定频码，例如 3-51-61", true);
    return;
  }
  setLoading(true, "固定3码遗漏查询中");
  if (els.fixedTripleOmissionMeta) {
    els.fixedTripleOmissionMeta.textContent = "查询中...";
  }
  try {
    const response = await fetch(`/api/fixed-triple-omission?${buildFixedTripleOmissionQuery().toString()}`);
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    if (!payloadMatchesCurrentGame(data)) return;
    state.fixedTripleOmission = data;
    renderFixedTripleOmission(data);
  } catch (error) {
    showToast(`遗漏查询失败：${error.message}`, true);
    if (els.fixedTripleOmissionMeta) {
      els.fixedTripleOmissionMeta.textContent = "查询失败";
    }
  } finally {
    setLoading(false);
  }
}

function renderFixedTripleOmission(data) {
  if (!data) return;
  const conservative = data.conservative || {};
  const verdict = data.verdict || {};
  const verdictClass = stakingVerdictClass(verdict);
  const reasons = Array.isArray(verdict.reasons) ? verdict.reasons : [];
  if (els.fixedTripleOmissionMeta) {
    els.fixedTripleOmissionMeta.textContent = `${escapeHtml(data.ticketLabel || "--")} · ${escapeHtml(
      data.date || "--",
    )} · ${fmtTime(data.firstDrawTimeUtc)} - ${fmtTime(data.latestDrawTimeUtc)}`;
  }
  if (els.fixedTripleOmissionStats) {
    els.fixedTripleOmissionStats.innerHTML = `
      <article class="stat-card">
        <span>今日命中</span>
        <strong>${fmtInt(data.hits || 0)} / ${fmtInt(data.draws || 0)}</strong>
        <small>${fmtPct(Number(data.hitRate || 0), 2)}</small>
      </article>
      <article class="stat-card">
        <span>当前遗漏</span>
        <strong>${fmtInt(data.currentMiss || 0)}</strong>
        <small>最长 ${fmtInt(data.maxMiss || 0)} · 上次 ${data.lastHitTimeUtc ? fmtTime(data.lastHitTimeUtc) : "未中"}</small>
      </article>
      <article class="stat-card accent">
        <span>今日保守</span>
        <strong class="${Number(conservative.netProfit || 0) >= 0 ? "positive" : "negative"}">${fmtYuan(
          Number(conservative.netProfit || 0),
          2,
          true,
        )}</strong>
        <small>投入 ${fmtYuan(Number(conservative.totalStake || 0), 2)} · 下一注 ${fmtYuan(Number(conservative.nextStake || 0), 2)}</small>
      </article>
      <article class="stat-card">
        <span>判断</span>
        <strong class="${verdictClass === "good" ? "positive" : verdictClass === "bad" ? "negative" : ""}">${escapeHtml(
          verdict.label || "--",
        )}</strong>
        <small>${escapeHtml(reasons.join("；") || "等待更多开奖")}</small>
      </article>`;
  }
  const rows = Array.isArray(data.recentHitTimes) ? data.recentHitTimes : [];
  if (!els.fixedTripleOmissionRows) return;
  if (!rows.length) {
    els.fixedTripleOmissionRows.innerHTML = '<tr><td colspan="3"><span class="muted">今天暂时没有命中记录</span></td></tr>';
    return;
  }
  els.fixedTripleOmissionRows.innerHTML = rows
    .map(
      (item) => `<tr>
        <td><strong>${fmtInt(item.drawIndex || 0)}</strong></td>
        <td>${fmtDate(item.drawTimeUtc || "")}</td>
        <td>${escapeHtml(item.drawEventId || "--")}</td>
      </tr>`,
    )
    .join("");
}

async function syncData(mode = "incremental") {
  const isFull = false;
  mode = "incremental";

  setLoading(true, "同步中");
  try {
    const endpoint = "/api/refresh";
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
      slot.predictionTrackingSlot = "all";
      slot.predictionTrackingDay = "";
      slot.adjacentStats = null;
      slot.adjacentHitPage = 1;
      slot.adjacentHitQuery = "";
      slot.adjacentHits = null;
    }
    syncPredictionPanelMirror();
    state.analysis = null;
    state.strategyAudit = null;
    state.strategyAuditStability = null;
    state.history = null;
    state.backtest = null;
    state.stakingBacktest = null;
    state.currentBacktest = null;
    state.fixedTripleObservation = null;
    state.fixedTripleOmission = null;
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

function renderStrategyAuditLoading() {
  if (els.strategyAuditMeta) {
    els.strategyAuditMeta.textContent = "策略审计计算中，只读读取历史和追踪库";
  }
  if (els.strategyAuditStats) {
    els.strategyAuditStats.innerHTML = `
      <article class="accent"><span>状态</span><strong>审计中</strong><small>不创建追踪记录</small></article>
      <article><span>窗口</span><strong>${escapeHtml(els.strategyAuditWindow?.value || "--")}</strong><small>最近期数</small></article>
      <article><span>训练</span><strong>${escapeHtml(els.strategyAuditTrain?.value || "--")}</strong><small>每期开奖前历史</small></article>
      <article><span>规则</span><strong>只读</strong><small>不改预测权重</small></article>
    `;
  }
  if (els.strategyAuditVerdicts) {
    els.strategyAuditVerdicts.innerHTML = `
      <article class="strategy-verdict-card observe">
        <div class="strategy-verdict-head">
          <strong>自动判读</strong>
          <span>计算中</span>
        </div>
        <p>正在读取 C 杀号池和重复号分桶。</p>
      </article>
    `;
  }
  if (els.strategyAuditMatrixMeta) {
    els.strategyAuditMatrixMeta.textContent = "按跟随、主杀、成本、样本可信度综合排序";
  }
  if (els.strategyAuditScoreRows) {
    els.strategyAuditScoreRows.innerHTML = '<tr><td colspan="7"><span class="muted">策略评分矩阵计算中</span></td></tr>';
  }
  if (els.strategyAuditExperimentMeta) {
    els.strategyAuditExperimentMeta.textContent = "只读沙盒，对照原规则，不影响正式预测";
  }
  if (els.strategyAuditExperimentRows) {
    els.strategyAuditExperimentRows.innerHTML = '<tr><td colspan="8"><span class="muted">实验规则对照计算中</span></td></tr>';
  }
  if (els.strategyAuditMixedMeta) {
    els.strategyAuditMixedMeta.textContent = "逐期开奖模拟规则组合，不影响正式预测";
  }
  if (els.strategyAuditMixedRows) {
    els.strategyAuditMixedRows.innerHTML = '<tr><td colspan="8"><span class="muted">逐期混合回测计算中</span></td></tr>';
  }
  if (els.strategyAuditStabilityMeta) {
    els.strategyAuditStabilityMeta.textContent = "波兰 60/180/360 稳定性计算中";
  }
  if (els.strategyAuditStabilityRows) {
    els.strategyAuditStabilityRows.innerHTML = '<tr><td colspan="8"><span class="muted">多窗口稳定性对照计算中</span></td></tr>';
  }
  if (els.strategyAuditTicketRows) {
    els.strategyAuditTicketRows.innerHTML = '<tr><td colspan="8"><span class="muted">A/B 前向票审计计算中</span></td></tr>';
  }
  if (els.strategyAuditVerdicts) {
    els.strategyAuditVerdicts.innerHTML = `
      <article class="strategy-verdict-card observe">
        <div class="strategy-verdict-head">
          <strong>自动判读</strong>
          <span>计算中</span>
        </div>
        <p>正在读取 A/B/C计划 前向票、真实追踪和重复号特征。</p>
      </article>
    `;
  }
  if (els.strategyAuditTicketRows) {
    els.strategyAuditTicketRows.innerHTML = '<tr><td colspan="8"><span class="muted">A/B/C计划 前向票审计计算中</span></td></tr>';
  }
  if (els.strategyAuditKillRows) {
    els.strategyAuditKillRows.closest(".panel")?.classList.add("hidden");
    els.strategyAuditKillRows.innerHTML = "";
  }
}

function strategyAuditWindowLabel(windowItem) {
  return `${Number(windowItem?.window || 0).toLocaleString("zh-CN")}期`;
}

function strategyAuditLiftClass(value, goodWhenLow = false, threshold = 0.001) {
  if (!Number.isFinite(value) || Math.abs(value) < threshold) return "";
  const good = goodWhenLow ? value < 0 : value > 0;
  return good ? "positive" : "negative";
}

function strategyAuditDistribution(items, labelKey, options = {}) {
  const values = Array.isArray(items) ? items : [];
  if (!values.length) return '<span class="muted">--</span>';
  const countKey = options.countKey || "tickets";
  const shareKey = options.shareKey || "share";
  const suffix = options.suffix || "";
  return `<div class="strategy-audit-distribution">${values
    .map((item) => {
      const label = item[labelKey];
      const count = Number(item[countKey] ?? item.rounds ?? 0);
      const share = Number(item[shareKey] || 0);
      const title = Number.isFinite(share) ? ` title="${fmtPct(share, 2)}"` : "";
      return `<span class="strategy-audit-chip"${title}>${escapeHtml(label)}${suffix} ${count.toLocaleString("zh-CN")}</span>`;
    })
    .join("")}</div>`;
}

function strategyAuditHitDistribution(items) {
  return strategyAuditDistribution(items, "hitCount", { suffix: "中" });
}

function strategyAuditOverlapDistribution(items) {
  return strategyAuditDistribution(items, "overlap", { countKey: "rounds", suffix: "重" });
}

function strategyAuditTicketOverlapSummary(items) {
  const values = Array.isArray(items) ? items : [];
  if (!values.length) return '<span class="muted">--</span>';
  return `<div class="strategy-audit-distribution">${values
    .map((item) => {
      const overlap = Number(item.previousOverlap || 0);
      const tickets = Number(item.tickets || 0);
      return `<span class="strategy-audit-chip" title="票数 ${tickets.toLocaleString("zh-CN")}">${overlap}重 ${fmtPct(
        Number(item.twoPlusRate || 0),
        1,
      )}/${fmtPct(Number(item.threePlusRate || 0), 1)}</span>`;
    })
    .join("")}</div>`;
}

function strategyAuditStatusCounts(statusCounts) {
  const labels = {
    pending: "待",
    won: "中",
    lost: "失",
    cancelled: "取消",
    void: "作废",
  };
  const entries = Object.entries(statusCounts || {}).filter(([, count]) => Number(count || 0) > 0);
  if (!entries.length) return '<span class="muted">--</span>';
  return `<div class="strategy-audit-distribution">${entries
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
    .map(([status, count]) => `<span class="strategy-audit-chip">${escapeHtml(labels[status] || status)} ${fmtInt(count)}</span>`)
    .join("")}</div>`;
}

function strategyAuditCounts(values, suffix = "") {
  const items = Array.isArray(values) ? values : [];
  if (!items.length) return '<span class="muted">--</span>';
  return `<div class="strategy-audit-distribution">${items
    .map((value, index) => `<span class="strategy-audit-chip">${index + 1}:${fmtInt(value)}${suffix}</span>`)
    .join("")}</div>`;
}

function strategyAuditBestKill(windowItem) {
  const panels = Array.isArray(windowItem?.killPanels) ? windowItem.killPanels : [];
  return panels
    .filter((item) => Number.isFinite(Number(item.wrongRateLift)))
    .sort((a, b) => Number(a.wrongRateLift || 0) - Number(b.wrongRateLift || 0))[0];
}

function strategyAuditBestETop(windowItem) {
  const items = Array.isArray(windowItem?.eTopTickets) ? windowItem.eTopTickets : [];
  return items
    .filter((item) => Number(item.tickets || 0) > 0)
    .sort((a, b) => Number(b.roi || 0) - Number(a.roi || 0) || Number(a.topCount || 0) - Number(b.topCount || 0))[0];
}

function strategyAuditWeightedMean(items, key, weightKey = "rounds") {
  let total = 0;
  let weightTotal = 0;
  for (const item of items || []) {
    const value = Number(item?.[key]);
    const weight = Math.max(0, Number(item?.[weightKey] || item?.rounds || item?.tickets || 0));
    if (!Number.isFinite(value) || weight <= 0) continue;
    total += value * weight;
    weightTotal += weight;
  }
  return weightTotal ? total / weightTotal : 0;
}

function strategyAuditWindowConsistency(items, predicate) {
  const values = (items || []).filter(Boolean);
  if (!values.length) return { total: 0, matched: 0, share: 0 };
  const matched = values.filter(predicate).length;
  return { total: values.length, matched, share: matched / values.length };
}

function strategyAuditPanelItems(windows, listKey, panel) {
  return (windows || [])
    .map((windowItem) => {
      const list = Array.isArray(windowItem?.[listKey]) ? windowItem[listKey] : [];
      const found = list.find((item) => item.panel === panel);
      return found ? { ...found, auditWindow: Number(windowItem.window || 0), windowRounds: Number(windowItem.rounds || 0) } : null;
    })
    .filter(Boolean);
}

function strategyAuditTicketItems(windows, panel, pickCount, mode = "main") {
  return (windows || [])
    .map((windowItem) => {
      const list = Array.isArray(windowItem?.ticketPanels) ? windowItem.ticketPanels : [];
      const found = list.find(
        (item) =>
          item.panel === panel &&
          Number(item.pickCount || 0) === Number(pickCount) &&
          String(item.mode || "main") === mode,
      );
      return found ? { ...found, auditWindow: Number(windowItem.window || 0), windowRounds: Number(windowItem.rounds || 0) } : null;
    })
    .filter(Boolean);
}

function strategyAuditPlanLabel(panel) {
  if (panel === PREDICTION_PANEL_DEFAULT) return "A计划";
  if (panel === PREDICTION_PANEL_B) return "B计划";
  if (panel === PREDICTION_PANEL_M) return "C计划";
  if (panel === PREDICTION_PANEL_C) return "旧C计划";
  return cdePanelLabel(panel);
}

function strategyAuditETopItems(windows, topCount) {
  return (windows || [])
    .map((windowItem) => {
      const list = Array.isArray(windowItem?.eTopTickets) ? windowItem.eTopTickets : [];
      const found = list.find((item) => Number(item.topCount || 0) === Number(topCount));
      return found ? { ...found, auditWindow: Number(windowItem.window || 0), windowRounds: Number(windowItem.rounds || 0) } : null;
    })
    .filter(Boolean);
}

function strategyAuditAtLeastHitProbability(game, pickCount, minHits) {
  const totalNumbers = Number(game?.totalNumbers || state.currentGame?.totalNumbers || 0);
  const drawnNumbers = Number(game?.drawnNumbers || state.currentGame?.drawnNumbers || 0);
  if (!totalNumbers || !drawnNumbers || pickCount <= 0) return 0;
  const denominator = combination(totalNumbers, pickCount);
  if (!denominator) return 0;
  let probability = 0;
  for (let hits = minHits; hits <= pickCount; hits += 1) {
    if (hits > drawnNumbers || pickCount - hits > totalNumbers - drawnNumbers) continue;
    probability += (combination(drawnNumbers, hits) * combination(totalNumbers - drawnNumbers, pickCount - hits)) / denominator;
  }
  return probability;
}

function strategyAuditVerdictTone(status) {
  if (status === "strong") return "strong";
  if (status === "weak") return "weak";
  if (status === "warn") return "warn";
  return "observe";
}

function strategyAuditVerdictCard({ title, status, label, summary, details }) {
  const detailList = (details || []).filter(Boolean);
  return `<article class="strategy-verdict-card ${strategyAuditVerdictTone(status)}">
    <div class="strategy-verdict-head">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(label)}</span>
    </div>
    <p>${escapeHtml(summary || "--")}</p>
    ${
      detailList.length
        ? `<div class="strategy-verdict-details">${detailList
            .map((detail) => `<span>${escapeHtml(detail)}</span>`)
            .join("")}</div>`
        : ""
    }
  </article>`;
}

function strategyAuditKillVerdict(windows) {
  const panels = [PREDICTION_PANEL_C];
  const results = panels
    .map((panel) => {
      const items = strategyAuditPanelItems(windows, "killPanels", panel);
      const latest = items.at(-1) || null;
      const avgLift = strategyAuditWeightedMean(items, "wrongRateLift", "rounds");
      const consistency = strategyAuditWindowConsistency(items, (item) => Number(item.wrongRateLift || 0) < 0);
      const avgPool = strategyAuditWeightedMean(items, "averagePoolSize", "rounds");
      let status = "observe";
      let label = "观察";
      if (items.length && avgLift <= -0.012 && Number(latest?.wrongRateLift || 0) <= -0.008 && consistency.share >= 0.67) {
        status = "strong";
        label = "主杀候选";
      } else if (items.length && avgLift >= 0.006 && Number(latest?.wrongRateLift || 0) >= 0) {
        status = "weak";
        label = "不适合主杀";
      } else if (items.length && (avgLift <= -0.005 || Number(latest?.wrongRateLift || 0) <= -0.008)) {
        status = "warn";
        label = "偏强观察";
      }
      return {
        panel,
        items,
        latest,
        avgLift,
        avgPool,
        consistency,
        status,
        label,
      };
    })
    .filter((item) => item.items.length);
  const best = [...results].sort((a, b) => a.avgLift - b.avgLift)[0];
  if (!best) {
    return strategyAuditVerdictCard({
      title: "C 主杀",
      status: "observe",
      label: "无数据",
      summary: "当前窗口没有足够的 C 杀号池审计数据。",
    });
  }
  const weakPanels = results.filter((item) => item.status === "weak").map((item) => cdePanelLabel(item.panel));
  return strategyAuditVerdictCard({
    title: "C 主杀",
    status: best.status,
    label: `${cdePanelLabel(best.panel)} ${best.label}`,
    summary:
      best.status === "strong"
        ? `${cdePanelLabel(best.panel)} 的错杀率多窗口低于随机基准，可先作为主杀候选观察。`
        : best.status === "weak"
          ? `${cdePanelLabel(best.panel)} 目前是三者里相对最好，但整体没有形成主杀优势。`
          : `${cdePanelLabel(best.panel)} 暂时只是相对占优，先观察，不直接提高权重。`,
    details: [
      `平均偏离 ${fmtSignedPct(best.avgLift, 2)}`,
      `最近偏离 ${fmtSignedPct(Number(best.latest?.wrongRateLift || 0), 2)}`,
      `低于随机 ${best.consistency.matched}/${best.consistency.total} 窗口`,
      `平均池 ${fmtNumber(best.avgPool, 1)} 码`,
      weakPanels.length ? `不适合主杀：${weakPanels.join("/")}` : "",
    ],
  });
}

function strategyAuditBTwoVerdict(windows) {
  const item = strategyAuditTicketItems(windows, PREDICTION_PANEL_B, 2).at(-1);
  if (!item) {
    return strategyAuditVerdictCard({
      title: "B 2码",
      status: "observe",
      label: "无数据",
      summary: "当前窗口没有 B 官方2码前向审计数据。",
    });
  }
  const tickets = Number(item.tickets || 0);
  const won = Number(item.won || 0);
  const hitRate = Number(item.hitRate || 0);
  const theoretical = Number(item.theoreticalHitRate || 0);
  const ci = Array.isArray(item.hitRateCi) ? item.hitRateCi : [0, 0];
  const ciLow = Number(ci[0] || 0);
  const ciHigh = Number(ci[1] || 0);
  let status = "observe";
  let label = "只观察";
  let summary = "B 官方2码当前还没有统计上站稳，继续低成本观察。";
  if (tickets >= 100 && ciHigh < theoretical) {
    status = "weak";
    label = "不跟";
    summary = "B 官方2码 Wilson 上沿低于理论基线，不支持继续加注或做四码派生。";
  } else if (tickets >= 300 && ciLow > theoretical) {
    status = "strong";
    label = "跟";
    summary = "B 官方2码 Wilson 下沿高于理论基线，才具备推进低票数派生的前提。";
  } else if (tickets >= 100 && hitRate > theoretical) {
    status = "warn";
    label = "只观察";
    summary = "B 官方2码表面高于理论基线，但置信区间仍跨过基线，先不扩票。";
  }
  return strategyAuditVerdictCard({
    title: "B 2码",
    status,
    label,
    summary,
    details: [
      `命中 ${fmtInt(won)}/${fmtInt(tickets)} · ${fmtPct(hitRate, 2)}`,
      `理论 ${fmtPct(theoretical, 2)}`,
      `Wilson ${fmtPct(ciLow, 2)}-${fmtPct(ciHigh, 2)}`,
      `偏离 ${fmtSignedPct(Number(item.hitRateVsTheory || 0), 2)}`,
    ],
  });
}

function strategyAuditETopVerdict(windows) {
  const topCounts = [1, 2, 3, 5, 8];
  const results = topCounts
    .map((topCount) => {
      const items = strategyAuditETopItems(windows, topCount);
      let covered = 0;
      let top8Hits = 0;
      let missed = 0;
      for (const item of items) {
        const coverage = item.roundCoverage || {};
        covered += Number(coverage.coveredFourHitRounds || 0);
        top8Hits += Number(coverage.top8FourHitRounds || 0);
        missed += Number(coverage.missedFourHitRounds || 0);
      }
      const missRate = top8Hits ? missed / top8Hits : 1;
      const coverageRate = top8Hits ? covered / top8Hits : 0;
      const roi = strategyAuditWeightedMean(items, "roi", "stake");
      const threePlus = strategyAuditWeightedMean(items, "threePlusRate", "tickets");
      const costSave = 1 - topCount / 8;
      let status = "observe";
      let label = "观察";
      if (top8Hits >= 2 && topCount < 8 && missRate <= 0.25) {
        status = "strong";
        label = "压缩候选";
      } else if (top8Hits >= 2 && topCount < 8 && missRate <= 0.5) {
        status = "warn";
        label = "谨慎压缩";
      } else if (top8Hits >= 2 && topCount < 8 && missRate > 0.5) {
        status = "weak";
        label = "漏中偏高";
      }
      return {
        topCount,
        items,
        top8Hits,
        missed,
        missRate,
        coverageRate,
        roi,
        threePlus,
        costSave,
        status,
        label,
      };
    })
    .filter((item) => item.items.length);
  const candidates = results.filter((item) => item.topCount < 8 && (item.status === "strong" || item.status === "warn"));
  const compressionItems = results.filter((item) => item.topCount < 8);
  const best = (candidates.length ? candidates : compressionItems.length ? compressionItems : results).sort(
    (a, b) =>
      a.missRate - b.missRate ||
      b.costSave - a.costSave ||
      b.roi - a.roi ||
      Number(a.topCount || 0) - Number(b.topCount || 0),
  )[0];
  if (!best) {
    return strategyAuditVerdictCard({
      title: "E 成本压缩",
      status: "observe",
      label: "无数据",
      summary: "当前窗口没有足够的 E TopN 数据。",
    });
  }
  return strategyAuditVerdictCard({
    title: "E 成本压缩",
    status: best.status,
    label: `Top${best.topCount} ${best.label}`,
    summary:
      best.status === "strong"
        ? `Top${best.topCount} 在 Top8 有四码命中时漏中较少，可作为降低 E 成本的第一候选。`
        : best.status === "weak"
          ? `Top${best.topCount} 省成本明显，但漏中偏高，不适合直接压缩到这个层级。`
          : `Top${best.topCount} 可继续观察，暂不建议把 E 从 8 组一次性压得太低。`,
    details: [
      `省票 ${fmtPct(best.costSave, 1)}`,
      `Top8命中 ${fmtInt(best.top8Hits)} 次`,
      `漏中 ${fmtInt(best.missed)} 次，漏率 ${fmtPct(best.missRate, 1)}`,
      `3码+ ${fmtPct(best.threePlus, 1)}`,
      `ROI ${fmtPct(best.roi, 2)}`,
    ],
  });
}

function strategyAuditRepeatVerdict(windows) {
  const repeats = (windows || []).map((windowItem) => windowItem.repeat).filter(Boolean);
  const latest = repeats.at(-1) || null;
  const avgLift = strategyAuditWeightedMean(
    repeats.map((item) => ({
      ...item,
      lift: Number(item.previousNumberHitRate || 0) - Number(item.baselinePreviousNumberHitRate || 0),
    })),
    "lift",
    "pairs",
  );
  const latestLift = Number(latest?.previousNumberHitRate || 0) - Number(latest?.baselinePreviousNumberHitRate || 0);
  const latestZ = Number(latest?.meanZ || 0);
  const consistency = strategyAuditWindowConsistency(
    repeats,
    (item) => Number(item.previousNumberHitRate || 0) >= Number(item.baselinePreviousNumberHitRate || 0),
  );
  let status = "observe";
  let label = "不加权";
  if (avgLift >= 0.012 && latestLift >= 0.008 && latestZ >= 1.5 && consistency.share >= 0.67) {
    status = "warn";
    label = "轻权观察";
  } else if (Math.abs(avgLift) <= 0.006 && Math.abs(latestZ) < 1.5) {
    status = "observe";
    label = "接近随机";
  } else if (avgLift < -0.006) {
    status = "weak";
    label = "不加权";
  }
  return strategyAuditVerdictCard({
    title: "重复号",
    status,
    label,
    summary:
      status === "warn"
        ? "重复号整体略强，但还只适合做轻权或过滤观察，暂不进入核心预测。"
        : "重复号暂时没有强到可以直接加权，继续只作为观察特征。",
    details: [
      `平均偏离 ${fmtSignedPct(avgLift, 2)}`,
      `最近偏离 ${fmtSignedPct(latestLift, 2)}`,
      `最近Z ${fmtNumber(latestZ, 2)}`,
      `高于基准 ${consistency.matched}/${consistency.total} 窗口`,
    ],
  });
}

function strategyAuditTrackingVerdict(tracking) {
  const panels = Array.isArray(tracking?.panels) ? tracking.panels : [];
  const settledPanels = panels.filter((item) => Number(item.tickets || 0) > 0);
  if (!tracking?.available || !settledPanels.length) {
    return strategyAuditVerdictCard({
      title: "追踪库复核",
      status: "observe",
      label: "样本不足",
      summary: "真实追踪库当前不足以复核自动审计结论。",
    });
  }
  const best = [...settledPanels].sort((a, b) => Number(b.roi || 0) - Number(a.roi || 0))[0];
  const worst = [...settledPanels].sort((a, b) => Number(a.roi || 0) - Number(b.roi || 0))[0];
  const totalSettled = settledPanels.reduce((sum, item) => sum + Number(item.tickets || 0), 0);
  let status = "observe";
  let label = "样本偏少";
  if (Number(best.tickets || 0) >= 30 && Number(best.roi || 0) > 0) {
    status = "warn";
    label = `${cdePanelLabel(best.panel)} 偏强`;
  }
  if (Number(worst.tickets || 0) >= 30 && Number(worst.roi || 0) < -0.35) {
    status = "weak";
    label = `${cdePanelLabel(worst.panel)} 偏弱`;
  }
  return strategyAuditVerdictCard({
    title: "追踪库复核",
    status,
    label,
    summary: "追踪库只作为真实落单记录复核；样本小的面板不单独定性。",
    details: [
      `已结算 ${fmtInt(totalSettled)} 注`,
      `最佳 ${cdePanelLabel(best.panel)} ROI ${fmtPct(Number(best.roi || 0), 2)} / ${fmtInt(best.tickets)} 注`,
      `最弱 ${cdePanelLabel(worst.panel)} ROI ${fmtPct(Number(worst.roi || 0), 2)} / ${fmtInt(worst.tickets)} 注`,
    ],
  });
}

function renderStrategyAuditVerdicts(data, windows) {
  if (!els.strategyAuditVerdicts) return;
  els.strategyAuditVerdicts.innerHTML = [
    strategyAuditBTwoVerdict(windows),
    strategyAuditRepeatVerdict(windows),
    strategyAuditTrackingVerdict(data.tracking),
  ].join("");
}

function strategyAuditScoreClamp(value) {
  return Math.round(clampNumber(Number(value) || 0, 0, 100));
}

function strategyAuditWindowSampleCount(items, key = "rounds") {
  const largest = [...(items || [])].sort((a, b) => Number(b.auditWindow || 0) - Number(a.auditWindow || 0))[0];
  if (!largest) return 0;
  return Number(largest[key] || largest.tickets || largest.rounds || largest.pairs || largest.windowRounds || 0);
}

function strategyAuditConfidenceScore(items, sampleKey = "rounds", sampleTarget = 180) {
  const values = (items || []).filter(Boolean);
  if (!values.length) return 0;
  const largestWindow = Math.max(...values.map((item) => Number(item.auditWindow || item.window || 0)), 0);
  const samples = strategyAuditWindowSampleCount(values, sampleKey);
  const sampleScore = Math.min(1, Math.sqrt(Math.max(0, samples) / sampleTarget));
  const windowScore = Math.min(1, largestWindow / 360);
  const multiWindowScore = Math.min(1, values.length / 3);
  return strategyAuditScoreClamp(18 + sampleScore * 45 + windowScore * 24 + multiWindowScore * 13);
}

function strategyAuditTrackingPanel(tracking, panel) {
  const panels = Array.isArray(tracking?.panels) ? tracking.panels : [];
  return panels.find((item) => item.panel === panel) || null;
}

function strategyAuditScoreTone(row) {
  if (row.tone && ["etop", "officialTicket"].includes(row.mode)) return row.tone;
  const follow = Number(row.followScore || 0);
  const kill = Number(row.killScore || 0);
  if (follow >= 70 || kill >= 70) return "strong";
  if (follow >= 58 || kill >= 58) return "warn";
  if ((follow > 0 && follow <= 35) || (kill > 0 && kill <= 35)) return "weak";
  return "observe";
}

function strategyAuditConclusion(row) {
  if (row.conclusion) return row.conclusion;
  const follow = Number(row.followScore || 0);
  const kill = Number(row.killScore || 0);
  const confidence = Number(row.confidence || 0);
  if (confidence < 38) return "样本观察";
  if (follow >= 70 && follow >= kill + 10) return "值得跟";
  if (kill >= 70 && kill >= follow + 10) return "主杀候选";
  if (follow >= 58 && follow >= kill) return "跟随观察";
  if (kill >= 58) return "反杀观察";
  return "随机附近";
}

function strategyAuditConfidenceScoreCap(confidence) {
  const value = Number(confidence || 0);
  if (value < 38) return 52;
  if (value < 55) return 62;
  if (value < 70) return 78;
  if (value < 82) return 88;
  return 100;
}

function strategyAuditApplyScoreCap(score, confidence) {
  if (score === null || score === undefined || !Number.isFinite(Number(score))) return score;
  return Math.min(strategyAuditScoreClamp(score), strategyAuditConfidenceScoreCap(confidence));
}

function strategyAuditFinalizeScoreRow(row) {
  const next = {
    ...row,
    evidence: [...(row.evidence || [])],
  };
  const rawFollow = next.followScore;
  const rawKill = next.killScore;
  next.followScore = strategyAuditApplyScoreCap(next.followScore, next.confidence);
  next.killScore = strategyAuditApplyScoreCap(next.killScore, next.confidence);
  const capped =
    (Number.isFinite(Number(rawFollow)) && Number(rawFollow) !== Number(next.followScore)) ||
    (Number.isFinite(Number(rawKill)) && Number(rawKill) !== Number(next.killScore));
  if (capped) {
    next.evidence.push(`可信度封顶 ${strategyAuditConfidenceScoreCap(next.confidence)}`);
  }
  if (next.mode === "kill") {
    const kill = Number(next.killScore || 0);
    const confidence = Number(next.confidence || 0);
    next.conclusion =
      confidence < 38
        ? "样本观察"
        : kill >= 70
          ? "主杀候选"
          : kill >= 58
            ? "主杀观察"
            : kill <= 40
              ? "不适合主杀"
              : "随机附近";
    next.tone = kill >= 70 ? "strong" : kill >= 58 ? "warn" : kill <= 40 ? "weak" : "observe";
  } else if (next.mode === "ticket") {
    const follow = Number(next.followScore || 0);
    const kill = Number(next.killScore || 0);
    const confidence = Number(next.confidence || 0);
    if (confidence < 38) next.conclusion = "样本观察";
    else if (kill >= 65 && kill >= follow + 8) next.conclusion = "反向主杀候选";
    else if (follow >= 70 && follow >= kill + 10) next.conclusion = "值得跟";
    else if (follow >= 58 && follow >= kill) next.conclusion = "跟随观察";
    else if (kill >= 58) next.conclusion = "反杀观察";
    else next.conclusion = "随机附近";
    next.tone = follow >= 70 && follow >= kill ? "strong" : kill >= 65 && kill > follow ? "weak" : follow >= 58 || kill >= 58 ? "warn" : "observe";
  } else if (next.mode === "bucket") {
    const follow = Number(next.followScore || 0);
    const kill = Number(next.killScore || 0);
    const confidence = Number(next.confidence || 0);
    next.conclusion =
      confidence < 38
        ? "样本观察"
        : follow >= 66 && follow > kill
          ? "重复桶偏强"
          : kill >= 64 && kill > follow
            ? "重复桶反杀"
            : "分桶观察";
    next.tone = follow >= 66 && follow > kill ? "warn" : kill >= 64 && kill > follow ? "weak" : "observe";
  }
  return next;
}

function strategyAuditScoreCell(score, kind = "action") {
  if (score === null || score === undefined || !Number.isFinite(Number(score))) return '<span class="muted">--</span>';
  const value = strategyAuditScoreClamp(score);
  let level = "mid";
  if (kind === "risk") {
    level = value >= 70 ? "risk" : value <= 35 ? "safe" : "mid";
  } else if (kind === "confidence") {
    level = value >= 70 ? "high" : value < 45 ? "low" : "mid";
  } else {
    level = value >= 70 ? "high" : value < 40 ? "low" : "mid";
  }
  return `<span class="strategy-score ${level}">${value}</span>`;
}

function strategyAuditRiskLabel(score) {
  const value = Number(score || 0);
  if (value >= 70) return "高";
  if (value >= 45) return "中";
  return "低";
}

function strategyAuditConfidenceLabel(score) {
  const value = Number(score || 0);
  if (value >= 72) return "较高";
  if (value >= 52) return "中";
  if (value >= 35) return "低";
  return "很低";
}

function strategyAuditBuildKillScoreRows(windows) {
  return [PREDICTION_PANEL_C]
    .map((panel) => {
      const items = strategyAuditPanelItems(windows, "killPanels", panel);
      if (!items.length) return null;
      const latest = items.at(-1);
      const avgLift = strategyAuditWeightedMean(items, "wrongRateLift", "rounds");
      const consistency = strategyAuditWindowConsistency(items, (item) => Number(item.wrongRateLift || 0) < 0);
      const confidence = strategyAuditConfidenceScore(items, "rounds", 180);
      const killScore = strategyAuditScoreClamp(50 + -avgLift * 1400 + (consistency.share - 0.5) * 20);
      const conclusion =
        confidence < 38
          ? "样本观察"
          : killScore >= 70
            ? "主杀候选"
            : killScore >= 58
              ? "主杀观察"
              : killScore <= 40
                ? "不适合主杀"
                : "随机附近";
      return {
        key: `kill-${panel}`,
        mode: "kill",
        strategy: `${cdePanelLabel(panel)} 杀号池`,
        followScore: null,
        killScore,
        costRisk: 18,
        confidence,
        conclusion,
        tone: killScore >= 70 ? "strong" : killScore >= 58 ? "warn" : killScore <= 40 ? "weak" : "observe",
        evidence: [
          `错杀偏离 ${fmtSignedPct(avgLift, 2)}`,
          `最近 ${fmtSignedPct(Number(latest?.wrongRateLift || 0), 2)}`,
          `低于随机 ${consistency.matched}/${consistency.total} 窗口`,
          `平均池 ${fmtNumber(strategyAuditWeightedMean(items, "averagePoolSize", "rounds"), 1)}码`,
        ],
      };
    })
    .filter(Boolean);
}

function strategyAuditBuildTicketScoreRows(data, windows) {
  const rows = [];
  for (const panel of [PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B, PREDICTION_PANEL_M]) {
    for (const pickCount of [1, 2, 3]) {
      const items = strategyAuditTicketItems(windows, panel, pickCount);
      if (!items.length) continue;
      const latest = items.at(-1);
      const avgLift = strategyAuditWeightedMean(items, "hitRateVsTheory", "tickets");
      const consistency = strategyAuditWindowConsistency(items, (item) => Number(item.hitRate || 0) >= Number(item.theoreticalHitRate || 0));
      const ci = Array.isArray(latest?.hitRateCi) ? latest.hitRateCi : [0, 0];
      const ciLow = Number(ci[0] || 0);
      const ciHigh = Number(ci[1] || 0);
      const theoretical = Number(latest?.theoreticalHitRate || 0);
      const tickets = Number(latest?.tickets || 0);
      const confidence = strategyAuditConfidenceScore(items, "tickets", pickCount === 2 ? 300 : 180);
      let followScore = strategyAuditScoreClamp(48 + avgLift * (pickCount === 2 ? 420 : 260) + (consistency.share - 0.5) * 18);
      let conclusion = "只观察";
      let tone = "observe";
      if (tickets >= 100 && ciHigh < theoretical) {
        followScore = Math.min(followScore, 35);
        conclusion = "不跟";
        tone = "weak";
      } else if (tickets >= 300 && ciLow > theoretical) {
        followScore = Math.max(followScore, 72);
        conclusion = "跟";
        tone = "strong";
      } else if (tickets >= 100 && Number(latest?.hitRate || 0) > theoretical) {
        followScore = Math.max(followScore, 58);
        conclusion = "只观察";
        tone = "warn";
      }
      rows.push({
        key: `ticket-${panel}-${pickCount}`,
        mode: "officialTicket",
        strategy: `${strategyAuditPlanLabel(panel)} ${pickCount}码`,
        followScore,
        killScore: null,
        costRisk: pickCount === 2 ? 28 : 16,
        confidence,
        conclusion,
        tone,
        evidence: [
          `命中 ${fmtPct(Number(latest?.hitRate || 0), 2)}`,
          `理论 ${fmtPct(theoretical, 2)}`,
          `Wilson ${fmtPct(ciLow, 2)}-${fmtPct(ciHigh, 2)}`,
          `高于基线 ${consistency.matched}/${consistency.total} 窗口`,
        ],
      });
    }
  }
  return rows;
}

function strategyAuditBucketRate(items, bucketKey) {
  let tickets = 0;
  let twoPlus = 0;
  let threePlus = 0;
  let windows = 0;
  let strongWindows = 0;
  for (const item of items || []) {
    let bucketTickets = 0;
    let bucketTwoPlus = 0;
    let bucketThreePlus = 0;
    for (const bucket of item.previousOverlapDistribution || []) {
      const overlap = Number(bucket.previousOverlap || 0);
      const key = overlap >= 2 ? "2+" : String(overlap);
      if (key !== bucketKey) continue;
      bucketTickets += Number(bucket.tickets || 0);
      bucketTwoPlus += Number(bucket.twoPlus || 0);
      bucketThreePlus += Number(bucket.threePlus || 0);
    }
    if (bucketTickets > 0) {
      windows += 1;
      tickets += bucketTickets;
      twoPlus += bucketTwoPlus;
      threePlus += bucketThreePlus;
      if (bucketThreePlus / bucketTickets > 0) strongWindows += 1;
    }
  }
  return {
    bucketKey,
    tickets,
    twoPlus,
    threePlus,
    twoPlusRate: tickets ? twoPlus / tickets : 0,
    threePlusRate: tickets ? threePlus / tickets : 0,
    windows,
    strongWindows,
  };
}

function strategyAuditBuildBucketScoreRows(data, windows) {
  const baselineTwoPlus = strategyAuditAtLeastHitProbability(data.game, 4, 2);
  const baselineThreePlus = strategyAuditAtLeastHitProbability(data.game, 4, 3);
  const rows = [];
  for (const panel of [PREDICTION_PANEL_F, PREDICTION_PANEL_G]) {
    const items = strategyAuditPanelItems(windows, "ticketPanels", panel);
    if (!items.length) continue;
    for (const bucketKey of ["0", "1", "2+"]) {
      const bucket = strategyAuditBucketRate(items, bucketKey);
      if (bucket.tickets < 20) continue;
      const twoLift = bucket.twoPlusRate - baselineTwoPlus;
      const threeLift = bucket.threePlusRate - baselineThreePlus;
      const confidence = strategyAuditScoreClamp(
        18 + Math.min(1, Math.sqrt(bucket.tickets / 120)) * 48 + Math.min(1, bucket.windows / 3) * 20,
      );
      const followScore = strategyAuditScoreClamp(48 + threeLift * 950 + twoLift * 320 + (bucket.strongWindows / bucket.windows - 0.5) * 10);
      const killScore = strategyAuditScoreClamp(48 + -threeLift * 850 + -twoLift * 260);
      rows.push({
        key: `bucket-${panel}-${bucketKey}`,
        mode: "bucket",
        strategy: `${cdePanelLabel(panel)} 重复${bucketKey}`,
        followScore,
        killScore,
        costRisk: 18,
        confidence,
        conclusion:
          confidence < 38
            ? "样本观察"
            : followScore >= 66 && followScore > killScore
              ? "重复桶偏强"
              : killScore >= 64 && killScore > followScore
                ? "重复桶反杀"
                : "分桶观察",
        tone: followScore >= 66 && followScore > killScore ? "warn" : killScore >= 64 && killScore > followScore ? "weak" : "observe",
        evidence: [
          `样本 ${fmtInt(bucket.tickets)}注`,
          `2码+ ${fmtSignedPct(twoLift, 1)}`,
          `3码+ ${fmtSignedPct(threeLift, 1)}`,
          `${bucket.strongWindows}/${bucket.windows} 窗口有3码+`,
        ],
      });
    }
  }
  return rows;
}

function strategyAuditBuildETopScoreRows(windows) {
  return [1, 2, 3, 5, 8]
    .map((topCount) => {
      const items = strategyAuditETopItems(windows, topCount);
      if (!items.length) return null;
      let top8Hits = 0;
      let missed = 0;
      for (const item of items) {
        const coverage = item.roundCoverage || {};
        top8Hits += Number(coverage.top8FourHitRounds || 0);
        missed += Number(coverage.missedFourHitRounds || 0);
      }
      const missRate = top8Hits ? missed / top8Hits : topCount < 8 ? 1 : 0;
      const roi = strategyAuditWeightedMean(items, "roi", "stake");
      const threePlus = strategyAuditWeightedMean(items, "threePlusRate", "tickets");
      const confidence = strategyAuditConfidenceScore(items, "tickets", 240);
      const costSave = 1 - topCount / 8;
      const costRisk = strategyAuditScoreClamp(15 + (topCount / 8) * 55 + missRate * 35);
      const followScore = strategyAuditScoreClamp(48 + clampNumber(roi, -1, 1) * 10 + threePlus * 120 - missRate * 14);
      let conclusion = "观察";
      let tone = "observe";
      if (topCount < 8 && top8Hits >= 2 && missRate <= 0.25) {
        conclusion = "压缩候选";
        tone = "strong";
      } else if (topCount < 8 && missRate > 0.5) {
        conclusion = "漏中偏高";
        tone = "weak";
      } else if (topCount === 8) {
        conclusion = "全买基准";
      }
      return {
        key: `etop-${topCount}`,
        mode: "etop",
        strategy: `E Top${topCount}`,
        followScore,
        killScore: null,
        costRisk,
        confidence,
        conclusion,
        tone,
        evidence: [
          `省票 ${fmtPct(costSave, 1)}`,
          `Top8命中 ${fmtInt(top8Hits)}次`,
          `漏中 ${fmtInt(missed)} / ${fmtPct(missRate, 1)}`,
          `3码+ ${fmtPct(threePlus, 1)}`,
          `ROI ${fmtPct(roi, 1)}`,
        ],
      };
    })
    .filter(Boolean);
}

function strategyAuditBuildRepeatScoreRow(windows) {
  const repeats = (windows || [])
    .map((windowItem) =>
      windowItem.repeat
        ? {
            ...windowItem.repeat,
            auditWindow: Number(windowItem.window || 0),
            lift: Number(windowItem.repeat.previousNumberHitRate || 0) - Number(windowItem.repeat.baselinePreviousNumberHitRate || 0),
          }
        : null,
    )
    .filter(Boolean);
  if (!repeats.length) return [];
  const latest = repeats.at(-1);
  const avgLift = strategyAuditWeightedMean(repeats, "lift", "pairs");
  const consistency = strategyAuditWindowConsistency(repeats, (item) => Number(item.lift || 0) > 0);
  const confidence = strategyAuditConfidenceScore(repeats, "pairs", 180);
  const followScore = strategyAuditScoreClamp(46 + avgLift * 800 + Number(latest.meanZ || 0) * 4 + (consistency.share - 0.5) * 12);
  return [
    {
      key: "repeat-overall",
      mode: "repeat",
      strategy: "重复号整体",
      followScore,
      killScore: null,
      costRisk: 10,
      confidence,
      conclusion: followScore >= 62 && confidence >= 45 ? "轻权观察" : "只观察",
      tone: followScore >= 62 && confidence >= 45 ? "warn" : "observe",
      evidence: [
        `平均偏离 ${fmtSignedPct(avgLift, 2)}`,
        `最近Z ${fmtNumber(Number(latest.meanZ || 0), 2)}`,
        `高于基准 ${consistency.matched}/${consistency.total} 窗口`,
      ],
    },
  ];
}

function strategyAuditBuildScoreRows(data, windows) {
  const rows = [
    ...strategyAuditBuildTicketScoreRows(data, windows),
    ...strategyAuditBuildRepeatScoreRow(windows),
  ].map(strategyAuditFinalizeScoreRow);
  return rows.sort((a, b) => {
    const aAction = Math.max(Number(a.followScore || 0), Number(a.killScore || 0));
    const bAction = Math.max(Number(b.followScore || 0), Number(b.killScore || 0));
    return (
      bAction - aAction ||
      Number(b.confidence || 0) - Number(a.confidence || 0) ||
      Number(a.costRisk || 0) - Number(b.costRisk || 0)
    );
  });
}

function renderStrategyAuditScoreMatrix(data, windows) {
  if (!els.strategyAuditScoreRows) return;
  const rows = strategyAuditBuildScoreRows(data, windows);
  if (els.strategyAuditMatrixMeta) {
    const highFollow = rows.filter((row) => Number(row.followScore || 0) >= 65).length;
    const highKill = rows.filter((row) => Number(row.killScore || 0) >= 65).length;
    els.strategyAuditMatrixMeta.textContent = `${fmtInt(rows.length)} 项 · 跟随候选 ${fmtInt(highFollow)} · 主杀/反杀候选 ${fmtInt(
      highKill,
    )} · 分数只用于排序，不等于开奖概率`;
  }
  els.strategyAuditScoreRows.innerHTML = rows.length
    ? rows
        .map((row) => {
          const tone = strategyAuditScoreTone(row);
          const evidence = (row.evidence || []).filter(Boolean);
          return `<tr class="strategy-score-row ${tone}">
            <td><strong>${escapeHtml(row.strategy || "--")}</strong></td>
            <td>${strategyAuditScoreCell(row.followScore)}</td>
            <td>${strategyAuditScoreCell(row.killScore)}</td>
            <td>${strategyAuditScoreCell(row.costRisk, "risk")}<div class="strategy-audit-inline-note">${strategyAuditRiskLabel(
              row.costRisk,
            )}</div></td>
            <td>${strategyAuditScoreCell(row.confidence, "confidence")}<div class="strategy-audit-inline-note">${strategyAuditConfidenceLabel(
              row.confidence,
            )}</div></td>
            <td><span class="strategy-score-badge ${tone}">${escapeHtml(strategyAuditConclusion(row))}</span></td>
            <td><div class="strategy-score-evidence">${evidence
              .map((item) => `<span>${escapeHtml(item)}</span>`)
              .join("")}</div></td>
          </tr>`;
        })
        .join("")
    : '<tr><td colspan="7"><span class="muted">暂无可评分策略</span></td></tr>';
}

function strategyAuditExperimentTone(row) {
  return row.tone || "observe";
}

function strategyAuditExperimentBadge(label, tone) {
  return `<span class="strategy-score-badge ${strategyAuditExperimentTone({ tone })}">${escapeHtml(label || "--")}</span>`;
}

function strategyAuditExperimentDelta(value, digits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return fmtSignedPct(number, digits);
}

function strategyAuditAggregateETop(items) {
  let top8Hits = 0;
  let missed = 0;
  let covered = 0;
  for (const item of items || []) {
    const coverage = item.roundCoverage || {};
    top8Hits += Number(coverage.top8FourHitRounds || 0);
    missed += Number(coverage.missedFourHitRounds || 0);
    covered += Number(coverage.coveredFourHitRounds || 0);
  }
  return {
    tickets: (items || []).reduce((sum, item) => sum + Number(item.tickets || 0), 0),
    won: (items || []).reduce((sum, item) => sum + Number(item.won || 0), 0),
    roi: strategyAuditWeightedMean(items, "roi", "stake"),
    twoPlusRate: strategyAuditWeightedMean(items, "twoPlusRate", "tickets"),
    threePlusRate: strategyAuditWeightedMean(items, "threePlusRate", "tickets"),
    top8Hits,
    missed,
    covered,
    missRate: top8Hits ? missed / top8Hits : 0,
    coverageRate: top8Hits ? covered / top8Hits : 0,
  };
}

function strategyAuditExperimentETopRows(windows) {
  const top8 = strategyAuditAggregateETop(strategyAuditETopItems(windows, 8));
  return [5, 3, 2, 1].map((topCount) => {
    const summary = strategyAuditAggregateETop(strategyAuditETopItems(windows, topCount));
    const costChange = topCount / 8 - 1;
    let tone = "observe";
    let conclusion = "观察";
    if (summary.top8Hits >= 2 && summary.missRate <= 0.25) {
      tone = "strong";
      conclusion = "可执行候选";
    } else if (summary.top8Hits >= 2 && summary.missRate <= 0.5) {
      tone = "warn";
      conclusion = "谨慎观察";
    } else if (summary.top8Hits >= 2 && summary.missRate > 0.5) {
      tone = "weak";
      conclusion = "不建议压缩";
    }
    return {
      name: `E Top${topCount} 替代 Top8`,
      target: "E 成本压缩",
      trigger: `Top8命中 ${fmtInt(summary.top8Hits)} 次`,
      cost: strategyAuditExperimentDelta(costChange, 1),
      metric: `漏 ${fmtInt(summary.missed)} / ${fmtPct(summary.missRate, 1)} · 3码+ ${fmtPct(summary.threePlusRate, 1)}`,
      relative: `ROI ${fmtPct(summary.roi, 1)} · Top8 ROI ${fmtPct(top8.roi, 1)}`,
      risk:
        summary.top8Hits < 2
          ? "四码样本少"
          : summary.missRate > 0.5
            ? "漏中高"
            : topCount <= 2
              ? "执行省但漏中敏感"
              : "成本/覆盖平衡",
      conclusion,
      tone,
    };
  });
}

function strategyAuditExperimentDowngradeRows(data, windows) {
  return [PREDICTION_PANEL_F, PREDICTION_PANEL_G].map((panel) => {
    const items = strategyAuditPanelItems(windows, "ticketPanels", panel);
    const latest = items.at(-1) || {};
    const tracking = strategyAuditTrackingPanel(data.tracking, panel);
    const trackingTickets = Number(tracking?.tickets || 0);
    const trackingRoi = Number(tracking?.roi || 0);
    const twoPlus = strategyAuditWeightedMean(items, "twoPlusRate", "tickets");
    const threePlus = strategyAuditWeightedMean(items, "threePlusRate", "tickets");
    const triggered = trackingTickets >= 60 && trackingRoi <= -0.5;
    return {
      name: `${cdePanelLabel(panel)} 追踪负面降级`,
      target: `${cdePanelLabel(panel)} 原始跟随`,
      trigger: trackingTickets ? `追踪 ${fmtInt(trackingTickets)} 注 · ROI ${fmtPct(trackingRoi, 1)}` : "追踪样本不足",
      cost: triggered ? "-100.0%" : "0.0%",
      metric: `审计2/3码 ${fmtPct(twoPlus, 1)} / ${fmtPct(threePlus, 1)}`,
      relative: `最近四码全中 ${fmtInt(latest.won || 0)} / ${fmtInt(latest.tickets || 0)}`,
      risk: triggered ? "会错过短窗口回暖" : "未触发",
      conclusion: triggered ? "可降级观察" : "暂不触发",
      tone: triggered ? "warn" : "observe",
    };
  });
}

function strategyAuditExperimentReverseKillRows(data, windows) {
  const singleBaseline = Number(data.game?.drawnNumbers || 0) / Number(data.game?.totalNumbers || 1);
  return [PREDICTION_PANEL_F, PREDICTION_PANEL_G].map((panel) => {
    const items = strategyAuditPanelItems(windows, "ticketPanels", panel);
    const latest = items.at(-1) || {};
    const numberHitRate = strategyAuditWeightedMean(items, "numberHitRate", "numberPicks");
    const wrongLift = numberHitRate - singleBaseline;
    const twoPlus = strategyAuditWeightedMean(items, "twoPlusRate", "tickets");
    const threePlus = strategyAuditWeightedMean(items, "threePlusRate", "tickets");
    const baselineTwo = strategyAuditAtLeastHitProbability(data.game, 4, 2);
    const baselineThree = strategyAuditAtLeastHitProbability(data.game, 4, 3);
    const weakDensity = twoPlus < baselineTwo && threePlus < baselineThree;
    let tone = "observe";
    let conclusion = "不满足";
    if (wrongLift <= -0.015 && weakDensity) {
      tone = "strong";
      conclusion = "反杀候选";
    } else if (wrongLift <= -0.008 || weakDensity) {
      tone = "warn";
      conclusion = "反杀观察";
    } else {
      tone = "weak";
      conclusion = "不建议反杀";
    }
    return {
      name: `${cdePanelLabel(panel)} 弱信号反杀`,
      target: `${cdePanelLabel(panel)} 四码号码`,
      trigger: `样本 ${fmtInt(latest.tickets || 0)} 注`,
      cost: "不下注",
      metric: `号码错杀率 ${fmtPct(numberHitRate, 2)}`,
      relative: `随机 ${fmtPct(singleBaseline, 2)} · 偏离 ${strategyAuditExperimentDelta(wrongLift, 2)}`,
      risk: weakDensity ? "2/3码弱" : "2/3码未同步弱",
      conclusion,
      tone,
    };
  });
}

function strategyAuditExperimentRepeatRows(data, windows) {
  const rows = [];
  const baselineThree = strategyAuditAtLeastHitProbability(data.game, 4, 3);
  for (const panel of [PREDICTION_PANEL_F, PREDICTION_PANEL_G]) {
    const items = strategyAuditPanelItems(windows, "ticketPanels", panel);
    const overallThree = strategyAuditWeightedMean(items, "threePlusRate", "tickets");
    const totalTickets = items.reduce((sum, item) => sum + Number(item.tickets || 0), 0);
    for (const bucketKey of ["0", "1", "2+"]) {
      const bucket = strategyAuditBucketRate(items, bucketKey);
      if (bucket.tickets < 20) continue;
      const keepShare = bucket.tickets / Math.max(1, totalTickets);
      const liftVsOverall = bucket.threePlusRate - overallThree;
      const liftVsRandom = bucket.threePlusRate - baselineThree;
      let tone = "observe";
      let conclusion = "分桶观察";
      if (bucket.tickets >= 30 && liftVsOverall >= 0.015 && liftVsRandom >= 0.01) {
        tone = "warn";
        conclusion = "过滤候选";
      } else if (bucket.tickets >= 30 && liftVsOverall <= -0.015 && liftVsRandom <= 0) {
        tone = "weak";
        conclusion = "不保留候选";
      }
      rows.push({
        name: `${cdePanelLabel(panel)} 只保留重复${bucketKey}`,
        target: `${cdePanelLabel(panel)} 重复号分桶`,
        trigger: `桶样本 ${fmtInt(bucket.tickets)} 注`,
        cost: strategyAuditExperimentDelta(keepShare - 1, 1),
        metric: `3码+ ${fmtPct(bucket.threePlusRate, 1)} · 2码+ ${fmtPct(bucket.twoPlusRate, 1)}`,
        relative: `比整体 ${strategyAuditExperimentDelta(liftVsOverall, 1)} · 比随机 ${strategyAuditExperimentDelta(liftVsRandom, 1)}`,
        risk: bucket.tickets < 60 ? "分桶样本小" : "可能少买漏强期",
        conclusion,
        tone,
      });
    }
  }
  return rows;
}

function strategyAuditExperimentKillRows(data, windows) {
  const singleBaseline = Number(data.game?.drawnNumbers || 0) / Number(data.game?.totalNumbers || 1);
  return [PREDICTION_PANEL_C].map((panel) => {
    const items = strategyAuditPanelItems(windows, "killPanels", panel);
    const latest = items.at(-1) || {};
    const wrongRate = strategyAuditWeightedMean(items, "wrongRate", "poolTotal");
    const wrongLift = wrongRate - singleBaseline;
    let tone = "observe";
    let conclusion = "主杀观察";
    if (wrongLift <= -0.012) {
      tone = "strong";
      conclusion = "主杀候选";
    } else if (wrongLift >= 0) {
      tone = "weak";
      conclusion = "不建议主杀";
    }
    return {
      name: `${cdePanelLabel(panel)} 单池主杀`,
      target: "C 杀号池",
      trigger: `平均池 ${fmtNumber(Number(latest.averagePoolSize || 0), 1)} 码`,
      cost: "不下注",
      metric: `错杀率 ${fmtPct(wrongRate, 2)}`,
      relative: `随机 ${fmtPct(singleBaseline, 2)} · 偏离 ${strategyAuditExperimentDelta(wrongLift, 2)}`,
      risk: Number(latest.averagePoolSize || 0) > 20 ? "杀池偏大" : "单池风险",
      conclusion,
      tone,
    };
  });
}

function strategyAuditBuildExperimentRows(data, windows) {
  return [];
}

function renderStrategyAuditExperiments(data, windows) {
  if (!els.strategyAuditExperimentRows) return;
  const rows = strategyAuditBuildExperimentRows(data, windows);
  if (els.strategyAuditExperimentMeta) {
    const executable = rows.filter((row) => row.conclusion.includes("候选") || row.conclusion.includes("降级")).length;
    els.strategyAuditExperimentMeta.textContent = `${fmtInt(rows.length)} 个只读实验 · 候选 ${fmtInt(
      executable,
    )} · 第一版复用审计聚合，不改正式预测`;
  }
  els.strategyAuditExperimentRows.innerHTML = rows.length
    ? rows
        .map((row) => `<tr class="strategy-experiment-row ${strategyAuditExperimentTone(row)}">
          <td><strong>${escapeHtml(row.name)}</strong></td>
          <td>${escapeHtml(row.target)}</td>
          <td>${escapeHtml(row.trigger)}</td>
          <td>${escapeHtml(row.cost)}</td>
          <td>${escapeHtml(row.metric)}</td>
          <td>${escapeHtml(row.relative)}</td>
          <td>${escapeHtml(row.risk)}</td>
          <td>${strategyAuditExperimentBadge(row.conclusion, row.tone)}</td>
        </tr>`)
        .join("")
    : '<tr><td colspan="8"><span class="muted">暂无实验对照数据</span></td></tr>';
}

function strategyAuditMixedBuyConclusion(item) {
  const reference = item.reference || {};
  const sameReference = item.key === reference.key;
  const costChange = Number(reference.stakeChangeRate || reference.ticketChangeRate || 0);
  const roiDelta = Number(reference.roiDelta || 0);
  const missFourRate = Number(reference.missRateWhenReferenceFourHit || 0);
  const playedRate = Number(item.playedRoundRate || 0);
  const avgTickets = Number(item.averageTicketsPerRound || 0);
  if (sameReference) return { tone: "observe", label: "基准" };
  if (playedRate > 0 && playedRate < 0.18) return { tone: "weak", label: "触发太少" };
  if (missFourRate >= 0.35) return { tone: "weak", label: "漏中偏高" };
  if (costChange <= -0.25 && missFourRate <= 0.12 && roiDelta >= -0.1) return { tone: "strong", label: "降成本候选" };
  if (roiDelta >= 0.05 && missFourRate <= 0.2) return { tone: "warn", label: "改善观察" };
  if (avgTickets > 6 && roiDelta <= 0) return { tone: "weak", label: "成本偏重" };
  return { tone: "observe", label: "只读观察" };
}

function strategyAuditMixedKillConclusion(item) {
  const wrongLift = Number(item.wrongRateLift || 0);
  const avgPool = Number(item.averagePoolSize || 0);
  const poolTotal = Number(item.poolTotal || 0);
  const triggered = Number(item.triggeredRounds || 0);
  const category = item.category || "";
  if (!triggered || poolTotal < 30 || avgPool < 0.5) return { tone: "weak", label: "样本太少" };
  if (avgPool > 30) return { tone: "weak", label: "杀池过大" };
  if (wrongLift >= 0) return { tone: "weak", label: category === "fg_reverse" ? "不建议反杀" : "不建议主杀" };
  if (category === "fg_reverse") {
    if (wrongLift <= -0.018 && avgPool <= 8) return { tone: "warn", label: "反杀观察" };
    return { tone: "observe", label: "反杀证据弱" };
  }
  if (wrongLift <= -0.015 && avgPool <= 18) return { tone: "strong", label: "主杀候选" };
  if (wrongLift <= -0.008 && avgPool <= 24) return { tone: "warn", label: "主杀观察" };
  return { tone: "observe", label: "边际观察" };
}

function strategyAuditMixedTypeLabel(item) {
  if (item.mode === "buy") {
    if (item.category === "e_cost") return "跟随压缩";
    if (item.category === "fg_repeat") return "F/G过滤";
    return "混合买票";
  }
  if (item.category === "fg_reverse") return "F/G反杀";
  if (item.category === "cde_intersection") return "共识主杀";
  if (item.category === "cde_union") return "合并主杀";
  return "杀号池";
}

function strategyAuditMixedBuyRow(windowItem, item) {
  const verdict = strategyAuditMixedBuyConclusion(item);
  const reference = item.reference || {};
  const missFour = Number(reference.missRateWhenReferenceFourHit || 0);
  const missThree = Number(reference.missRateWhenReferenceThreePlus || 0);
  return {
    tone: verdict.tone,
    window: strategyAuditWindowLabel(windowItem),
    name: item.label || item.key || "--",
    description: item.description || "",
    type: strategyAuditMixedTypeLabel(item),
    sample: `${fmtInt(item.rounds)}期 · ${fmtInt(item.tickets)}票 · 均 ${fmtNumber(Number(item.averageTicketsPerRound || 0), 1)}组`,
    metric: `ROI ${fmtPct(Number(item.roi || 0), 1)} · 4码期 ${fmtPct(Number(item.roundFourHitRate || 0), 1)} · 3码+期 ${fmtPct(
      Number(item.roundThreePlusRate || 0),
      1,
    )}`,
    relative:
      item.key === reference.key
        ? "自身基准"
        : `${reference.label || "基准"} · 成本 ${strategyAuditExperimentDelta(
            Number(reference.stakeChangeRate || reference.ticketChangeRate || 0),
            1,
          )} · ROI ${strategyAuditExperimentDelta(Number(reference.roiDelta || 0), 1)}`,
    risk:
      item.key === reference.key
        ? `跳过 ${fmtInt(item.skippedRounds || 0)}期`
        : `漏4码 ${fmtInt(reference.missedFourHitRounds || 0)}期/${fmtPct(missFour, 1)} · 漏3码+ ${fmtPct(missThree, 1)}`,
    conclusion: verdict.label,
  };
}

function strategyAuditMixedKillRow(windowItem, item) {
  const verdict = strategyAuditMixedKillConclusion(item);
  const wrongLift = Number(item.wrongRateLift || 0);
  return {
    tone: verdict.tone,
    window: strategyAuditWindowLabel(windowItem),
    name: item.label || item.key || "--",
    description: item.description || "",
    type: strategyAuditMixedTypeLabel(item),
    sample: `${fmtInt(item.rounds)}期 · 触发 ${fmtInt(item.triggeredRounds)}期 · 均池 ${fmtNumber(Number(item.averagePoolSize || 0), 1)}码`,
    metric: `错杀率 ${fmtPct(Number(item.wrongRate || 0), 2)} · 平均错 ${fmtNumber(Number(item.averageWrong || 0), 2)}`,
    relative: `随机 ${fmtPct(Number(item.baselineWrongRate || 0), 2)} · 偏离 ${strategyAuditExperimentDelta(wrongLift, 2)} · 多错 ${fmtNumber(
      Number(item.wrongTotalLift || 0),
      1,
    )}`,
    risk: `0/1/2错 ${fmtPct(Number(item.zeroWrongRate || 0), 1)} / ${fmtPct(Number(item.oneOrLessWrongRate || 0), 1)} / ${fmtPct(
      Number(item.twoOrLessWrongRate || 0),
      1,
    )}`,
    conclusion: verdict.label,
  };
}

function strategyAuditBuildMixedRows(windows) {
  const rows = [];
  const orderedWindows = [...(windows || [])].sort((a, b) => Number(b.window || 0) - Number(a.window || 0));
  for (const windowItem of orderedWindows) {
    for (const item of windowItem.mixedBuyExperiments || []) {
      rows.push(strategyAuditMixedBuyRow(windowItem, item));
    }
    for (const item of windowItem.mixedKillExperiments || []) {
      rows.push(strategyAuditMixedKillRow(windowItem, item));
    }
  }
  return rows;
}

function renderStrategyAuditMixedExperiments(windows) {
  if (!els.strategyAuditMixedRows) return;
  const rows = strategyAuditBuildMixedRows(windows);
  if (els.strategyAuditMixedMeta) {
    const candidates = rows.filter((row) => row.conclusion.includes("候选") || row.conclusion.includes("改善")).length;
    els.strategyAuditMixedMeta.textContent = `${fmtInt(rows.length)} 条逐期模拟 · 候选 ${fmtInt(
      candidates,
    )} · 按每期开奖前历史生成，不改正式预测`;
  }
  els.strategyAuditMixedRows.innerHTML = rows.length
    ? rows
        .map((row) => `<tr class="strategy-mixed-row ${strategyAuditExperimentTone(row)}">
          <td>${escapeHtml(row.window)}</td>
          <td><strong>${escapeHtml(row.name)}</strong><div class="strategy-audit-inline-note">${escapeHtml(row.description)}</div></td>
          <td>${escapeHtml(row.type)}</td>
          <td>${escapeHtml(row.sample)}</td>
          <td>${escapeHtml(row.metric)}</td>
          <td>${escapeHtml(row.relative)}</td>
          <td>${escapeHtml(row.risk)}</td>
          <td>${strategyAuditExperimentBadge(row.conclusion, row.tone)}</td>
        </tr>`)
        .join("")
    : '<tr><td colspan="8"><span class="muted">暂无逐期混合回测数据</span></td></tr>';
}

function strategyAuditStabilityGameName(payload) {
  return payload?.game?.shortName || payload?.game?.name || payload?.game?.key || "--";
}

function strategyAuditStabilityGroupKey(item) {
  return `${item?.mode || "unknown"}:${item?.key || item?.label || "--"}`;
}

function strategyAuditStabilityWeight(item, keys) {
  for (const key of keys) {
    const value = Number(item?.[key]);
    if (Number.isFinite(value) && value > 0) return value;
  }
  return 0;
}

function strategyAuditStabilityWeightedMean(items, valueFn, weightFn) {
  let total = 0;
  let weightTotal = 0;
  for (const item of items || []) {
    const value = Number(valueFn(item));
    const weight = Math.max(0, Number(weightFn(item) || 0));
    if (!Number.isFinite(value) || weight <= 0) continue;
    total += value * weight;
    weightTotal += weight;
  }
  return weightTotal > 0 ? total / weightTotal : Number.NaN;
}

function strategyAuditStabilityMean(items, valueFn) {
  let total = 0;
  let count = 0;
  for (const item of items || []) {
    const value = Number(valueFn(item));
    if (!Number.isFinite(value)) continue;
    total += value;
    count += 1;
  }
  return count ? total / count : Number.NaN;
}

function strategyAuditStabilityMax(items, valueFn) {
  const values = (items || [])
    .map((item) => Number(valueFn(item)))
    .filter((value) => Number.isFinite(value));
  return values.length ? Math.max(...values) : Number.NaN;
}

function strategyAuditStabilityCount(items, predicate) {
  return (items || []).filter((item) => {
    try {
      return Boolean(predicate(item));
    } catch (_) {
      return false;
    }
  }).length;
}

function strategyAuditStabilityCostChange(item) {
  const reference = item?.reference || {};
  const stakeChange = Number(reference.stakeChangeRate);
  if (Number.isFinite(stakeChange)) return stakeChange;
  const ticketChange = Number(reference.ticketChangeRate);
  return Number.isFinite(ticketChange) ? ticketChange : 0;
}

function strategyAuditStabilityMissFour(item) {
  const reference = item?.reference || {};
  if (item?.key && item.key === reference.key) return Number.NaN;
  const value = Number(reference.missRateWhenReferenceFourHit);
  return Number.isFinite(value) ? value : Number.NaN;
}

function strategyAuditStabilityToneRank(tone) {
  if (tone === "strong") return 0;
  if (tone === "warn") return 1;
  if (tone === "observe") return 2;
  if (tone === "weak") return 3;
  return 4;
}

function strategyAuditStabilityCoverage(items) {
  const games = new Map();
  const windows = new Set();
  for (const item of items || []) {
    const gameName = item.gameName || item.gameKey || "--";
    const windowValue = Number(item.auditWindow || 0);
    if (!games.has(gameName)) games.set(gameName, new Set());
    if (windowValue) {
      games.get(gameName).add(windowValue);
      windows.add(windowValue);
    }
  }
  const gameCount = games.size;
  const windowCount = windows.size;
  const crossGame = [...games.entries()]
    .map(([game, gameWindows]) => {
      const label = [...gameWindows].sort((a, b) => a - b).join("/");
      return `${game} ${label || "--"}`;
    })
    .join(" · ");
  return {
    gameCount,
    windowCount,
    samples: (items || []).length,
    crossGame,
    text: `${fmtInt((items || []).length)}样本 · ${fmtInt(gameCount)}彩种 · ${fmtInt(windowCount)}窗口`,
  };
}

function strategyAuditStabilityBuyConclusion(summary) {
  if (summary.samples < 3) return { tone: "weak", label: "样本不足" };
  if (summary.sameReference) return { tone: "observe", label: "基准对照" };
  if (Number.isFinite(summary.missFourMax) && summary.missFourMax >= 0.35) return { tone: "weak", label: "漏中偏高" };
  if (Number.isFinite(summary.missFourAvg) && summary.missFourAvg >= 0.25) return { tone: "weak", label: "漏中偏高" };
  if (summary.avgTickets > 6 && summary.roi <= 0 && summary.costChange >= -0.05) return { tone: "weak", label: "成本偏重" };
  if (
    summary.costChange <= -0.2 &&
    (!Number.isFinite(summary.missFourMax) || summary.missFourMax <= 0.18) &&
    summary.improvedShare >= 0.67 &&
    summary.gameCount >= 2
  ) {
    return { tone: "strong", label: "降成本候选" };
  }
  if (summary.costChange <= -0.15 && (!Number.isFinite(summary.missFourMax) || summary.missFourMax <= 0.25) && summary.improvedShare >= 0.5) {
    return { tone: "warn", label: "压缩观察" };
  }
  if (summary.roiImprovedShare >= 0.67 && (!Number.isFinite(summary.missFourAvg) || summary.missFourAvg <= 0.2)) {
    return { tone: "warn", label: "改善观察" };
  }
  return { tone: "observe", label: "只读观察" };
}

function strategyAuditStabilityKillConclusion(summary) {
  if (summary.samples < 3 || summary.poolTotal < 100) return { tone: "weak", label: "样本不足" };
  if (summary.avgPool > 30) return { tone: "weak", label: "杀池过大" };
  if (summary.wrongLift >= 0 || summary.negativeShare < 0.5) {
    return { tone: "weak", label: summary.category === "fg_reverse" ? "不建议反杀" : "不建议主杀" };
  }
  if (summary.category === "fg_reverse") {
    if (summary.wrongLift <= -0.01 && summary.negativeShare >= 0.67 && summary.avgPool <= 12) {
      return { tone: "warn", label: "反杀观察" };
    }
    return { tone: "observe", label: "反杀证据弱" };
  }
  if (summary.wrongLift <= -0.01 && summary.negativeShare >= 0.67 && summary.avgPool <= 20 && summary.gameCount >= 2) {
    return { tone: "strong", label: "主杀候选" };
  }
  if (summary.wrongLift < 0 && summary.negativeShare >= 0.5 && summary.avgPool <= 24) {
    return { tone: "warn", label: "主杀观察" };
  }
  return { tone: "observe", label: "边际观察" };
}

function strategyAuditStabilityBuyRow(group) {
  const items = group.items;
  const coverage = strategyAuditStabilityCoverage(items);
  const sameReference = items.every((item) => item.key && item.key === item.reference?.key);
  const roi = strategyAuditStabilityWeightedMean(items, (item) => item.roi, (item) =>
    strategyAuditStabilityWeight(item, ["stake", "tickets", "rounds"]),
  );
  const costChange = strategyAuditStabilityWeightedMean(items, strategyAuditStabilityCostChange, (item) =>
    strategyAuditStabilityWeight(item, ["stake", "tickets", "rounds"]),
  );
  const roiDelta = strategyAuditStabilityWeightedMean(
    items,
    (item) => Number(item.reference?.roiDelta),
    (item) => strategyAuditStabilityWeight(item, ["stake", "tickets", "rounds"]),
  );
  const roundFourHitRate = strategyAuditStabilityWeightedMean(items, (item) => item.roundFourHitRate, (item) =>
    strategyAuditStabilityWeight(item, ["rounds", "tickets"]),
  );
  const roundThreePlusRate = strategyAuditStabilityWeightedMean(items, (item) => item.roundThreePlusRate, (item) =>
    strategyAuditStabilityWeight(item, ["rounds", "tickets"]),
  );
  const playedRate = strategyAuditStabilityWeightedMean(items, (item) => item.playedRoundRate, (item) =>
    strategyAuditStabilityWeight(item, ["rounds", "tickets"]),
  );
  const avgTickets = strategyAuditStabilityWeightedMean(items, (item) => item.averageTicketsPerRound, (item) =>
    strategyAuditStabilityWeight(item, ["rounds", "tickets"]),
  );
  const missFourAvg = strategyAuditStabilityMean(items, strategyAuditStabilityMissFour);
  const missFourMax = strategyAuditStabilityMax(items, strategyAuditStabilityMissFour);
  const roiPositiveCount = strategyAuditStabilityCount(items, (item) => Number(item.roi || 0) > 0);
  const roiImprovedCount = strategyAuditStabilityCount(items, (item) => Number(item.reference?.roiDelta || 0) > 0);
  const improvedCount = strategyAuditStabilityCount(
    items,
    (item) =>
      Number(item.roi || 0) > 0 ||
      Number(item.reference?.roiDelta || 0) >= 0 ||
      (strategyAuditStabilityCostChange(item) <= -0.2 && (Number.isNaN(strategyAuditStabilityMissFour(item)) || strategyAuditStabilityMissFour(item) <= 0.18)),
  );
  const summary = {
    samples: coverage.samples,
    gameCount: coverage.gameCount,
    sameReference,
    roi: Number.isFinite(roi) ? roi : 0,
    costChange: Number.isFinite(costChange) ? costChange : 0,
    roiImprovedShare: coverage.samples ? roiImprovedCount / coverage.samples : 0,
    improvedShare: coverage.samples ? improvedCount / coverage.samples : 0,
    missFourAvg,
    missFourMax,
    avgTickets: Number.isFinite(avgTickets) ? avgTickets : 0,
  };
  const verdict = strategyAuditStabilityBuyConclusion(summary);
  return {
    key: group.key,
    mode: "buy",
    tone: verdict.tone,
    name: group.label,
    description: group.description,
    type: strategyAuditMixedTypeLabel(group.prototype),
    coverage: coverage.text,
    windowPerformance: `ROI>0 ${fmtInt(roiPositiveCount)}/${fmtInt(coverage.samples)} · ROI改善 ${fmtInt(roiImprovedCount)}/${fmtInt(
      coverage.samples,
    )} · 成本降 ${fmtInt(strategyAuditStabilityCount(items, (item) => strategyAuditStabilityCostChange(item) <= -0.2))}/${fmtInt(coverage.samples)}`,
    metric: `ROI ${fmtPct(roi, 1)} · ROI差 ${strategyAuditExperimentDelta(roiDelta, 1)} · 成本 ${strategyAuditExperimentDelta(
      costChange,
      1,
    )} · 均 ${fmtNumber(avgTickets, 1)}组`,
    crossGame: coverage.crossGame || "--",
    risk: `4码期 ${fmtPct(roundFourHitRate, 1)} · 3码+期 ${fmtPct(roundThreePlusRate, 1)} · 触发 ${fmtPct(playedRate, 1)} · 漏4均/峰 ${
      Number.isFinite(missFourAvg) ? fmtPct(missFourAvg, 1) : "--"
    }/${Number.isFinite(missFourMax) ? fmtPct(missFourMax, 1) : "--"}`,
    conclusion: verdict.label,
  };
}

function strategyAuditStabilityKillRow(group) {
  const items = group.items;
  const coverage = strategyAuditStabilityCoverage(items);
  const wrongRate = strategyAuditStabilityWeightedMean(items, (item) => item.wrongRate, (item) =>
    strategyAuditStabilityWeight(item, ["poolTotal", "triggeredRounds", "rounds"]),
  );
  const baselineWrongRate = strategyAuditStabilityWeightedMean(items, (item) => item.baselineWrongRate, (item) =>
    strategyAuditStabilityWeight(item, ["poolTotal", "triggeredRounds", "rounds"]),
  );
  const wrongLift = strategyAuditStabilityWeightedMean(items, (item) => item.wrongRateLift, (item) =>
    strategyAuditStabilityWeight(item, ["poolTotal", "triggeredRounds", "rounds"]),
  );
  const avgPool = strategyAuditStabilityWeightedMean(items, (item) => item.averagePoolSize, (item) =>
    strategyAuditStabilityWeight(item, ["triggeredRounds", "rounds"]),
  );
  const avgWrong = strategyAuditStabilityWeightedMean(items, (item) => item.averageWrong, (item) =>
    strategyAuditStabilityWeight(item, ["triggeredRounds", "rounds"]),
  );
  const triggeredRounds = items.reduce((total, item) => total + Math.max(0, Number(item.triggeredRounds || 0)), 0);
  const rounds = items.reduce((total, item) => total + Math.max(0, Number(item.rounds || 0)), 0);
  const poolTotal = items.reduce((total, item) => total + Math.max(0, Number(item.poolTotal || 0)), 0);
  const negativeCount = strategyAuditStabilityCount(items, (item) => Number(item.wrongRateLift || 0) < 0);
  const twoOrLessCount = strategyAuditStabilityCount(items, (item) => Number(item.twoOrLessWrongRate || 0) >= 0.2);
  const summary = {
    samples: coverage.samples,
    gameCount: coverage.gameCount,
    poolTotal,
    avgPool: Number.isFinite(avgPool) ? avgPool : 0,
    wrongLift: Number.isFinite(wrongLift) ? wrongLift : 0,
    negativeShare: coverage.samples ? negativeCount / coverage.samples : 0,
    category: group.prototype?.category || "",
  };
  const verdict = strategyAuditStabilityKillConclusion(summary);
  return {
    key: group.key,
    mode: "kill",
    tone: verdict.tone,
    name: group.label,
    description: group.description,
    type: strategyAuditMixedTypeLabel(group.prototype),
    coverage: coverage.text,
    windowPerformance: `低随机 ${fmtInt(negativeCount)}/${fmtInt(coverage.samples)} · 触发 ${fmtInt(triggeredRounds)}/${fmtInt(
      rounds,
    )}期 · 2错内 ${fmtInt(twoOrLessCount)}/${fmtInt(coverage.samples)}`,
    metric: `错杀 ${fmtPct(wrongRate, 2)} · 随机 ${fmtPct(baselineWrongRate, 2)} · 偏离 ${strategyAuditExperimentDelta(
      wrongLift,
      2,
    )} · 均池 ${fmtNumber(avgPool, 1)}码`,
    crossGame: coverage.crossGame || "--",
    risk: `平均错 ${fmtNumber(avgWrong, 2)} · 杀池总 ${fmtInt(poolTotal)}码 · 高于随机 ${fmtInt(
      coverage.samples - negativeCount,
    )}/${fmtInt(coverage.samples)}样本`,
    conclusion: verdict.label,
  };
}

function strategyAuditBuildStabilityRows(stability) {
  const payloads = Array.isArray(stability?.items) ? stability.items : [];
  const groups = new Map();
  for (const payload of payloads) {
    const gameName = strategyAuditStabilityGameName(payload);
    const gameKey = payload?.game?.key || gameName;
    for (const windowItem of payload?.windows || []) {
      const auditWindow = Number(windowItem?.window || 0);
      for (const item of windowItem?.mixedBuyExperiments || []) {
        const sample = { ...item, mode: "buy", gameName, gameKey, auditWindow };
        const key = strategyAuditStabilityGroupKey(sample);
        if (!groups.has(key)) {
          groups.set(key, {
            key,
            label: item.label || item.key || "--",
            description: item.description || "",
            prototype: sample,
            items: [],
          });
        }
        groups.get(key).items.push(sample);
      }
      for (const item of windowItem?.mixedKillExperiments || []) {
        const sample = { ...item, mode: "kill", gameName, gameKey, auditWindow };
        const key = strategyAuditStabilityGroupKey(sample);
        if (!groups.has(key)) {
          groups.set(key, {
            key,
            label: item.label || item.key || "--",
            description: item.description || "",
            prototype: sample,
            items: [],
          });
        }
        groups.get(key).items.push(sample);
      }
    }
  }
  return [...groups.values()]
    .map((group) => (group.prototype?.mode === "buy" ? strategyAuditStabilityBuyRow(group) : strategyAuditStabilityKillRow(group)))
    .sort((a, b) => {
      const toneDiff = strategyAuditStabilityToneRank(a.tone) - strategyAuditStabilityToneRank(b.tone);
      if (toneDiff) return toneDiff;
      if (a.mode !== b.mode) return a.mode === "buy" ? -1 : 1;
      return a.name.localeCompare(b.name, "zh-CN");
    });
}

function renderStrategyAuditStability() {
  if (!els.strategyAuditStabilityRows) return;
  const stability = state.strategyAuditStability;
  const rows = strategyAuditBuildStabilityRows(stability);
  if (els.strategyAuditStabilityMeta) {
    const errors = Array.isArray(stability?.errors) ? stability.errors : [];
    const games = new Set((stability?.items || []).map((item) => item?.game?.key || item?.game?.shortName).filter(Boolean));
    const candidates = rows.filter((row) => row.conclusion.includes("候选") || row.conclusion.includes("观察")).length;
    const errorText = errors.length ? ` · ${fmtInt(errors.length)}个彩种读取失败` : "";
    els.strategyAuditStabilityMeta.textContent = `${fmtInt(rows.length)} 个规则 · ${fmtInt(
      games.size,
    )} 个彩种 · 60/180/360 稳定性 · 候选/观察 ${fmtInt(candidates)}${errorText}`;
  }
  if (!rows.length) {
    const errors = (stability?.errors || []).map((item) => item.message).filter(Boolean);
    els.strategyAuditStabilityRows.innerHTML = `<tr><td colspan="8"><span class="muted">${
      errors.length ? escapeHtml(errors.join(" · ")) : "暂无多窗口稳定性数据"
    }</span></td></tr>`;
    return;
  }
  els.strategyAuditStabilityRows.innerHTML = rows
    .map((row) => `<tr class="strategy-stability-row ${strategyAuditExperimentTone(row)}">
      <td><strong>${escapeHtml(row.name)}</strong><div class="strategy-audit-inline-note">${escapeHtml(row.description)}</div></td>
      <td>${escapeHtml(row.type)}</td>
      <td>${escapeHtml(row.coverage)}</td>
      <td>${escapeHtml(row.windowPerformance)}</td>
      <td>${escapeHtml(row.metric)}</td>
      <td>${escapeHtml(row.crossGame)}</td>
      <td>${escapeHtml(row.risk)}</td>
      <td>${strategyAuditExperimentBadge(row.conclusion, row.tone)}</td>
    </tr>`)
    .join("");
}

function renderStrategyAudit() {
  const data = state.strategyAudit;
  if (!data) return;
  state.currentGame = data.game || state.currentGame;
  updateGameUi();
  renderSummary(data);
  els.strategyAuditKillRows?.closest(".panel")?.classList.add("hidden");

  const windows = Array.isArray(data.windows) ? data.windows : [];
  const latestWindow = windows.at(-1) || null;
  const bestKill = strategyAuditBestKill(latestWindow);
  const repeat = latestWindow?.repeat || null;

  if (els.strategyAuditMeta) {
    const cacheText = data.cacheHit ? " · 前端/后端缓存" : "";
    els.strategyAuditMeta.textContent = `${data.game?.shortName || "--"} · 最近 ${fmtInt(data.actualRounds)}期 · 训练 ${fmtInt(
      data.trainWindow,
    )}期 · 四码赔率 ${fmtNumber(Number(data.odds || 0), 2)}x · ${fmtInt(data.elapsedMs)}ms${cacheText} · ${fmtDate(data.generatedAt)}`;
  }

  if (els.strategyAuditStats) {
    const killLift = Number(bestKill?.wrongRateLift || 0);
    const bTwo = strategyAuditTicketItems(windows, PREDICTION_PANEL_B, 2).at(-1);
    const mTwo = strategyAuditTicketItems(windows, PREDICTION_PANEL_M, 2).at(-1);
    const mThree = strategyAuditTicketItems(windows, PREDICTION_PANEL_M, 3).at(-1);
    const bTwoLift = Number(bTwo?.hitRateVsTheory || 0);
    els.strategyAuditStats.innerHTML = `
      <article class="accent">
        <span>审计期数</span>
        <strong>${fmtInt(data.actualRounds)}</strong>
        <small>请求 ${fmtInt(data.window)} · 跳过 ${fmtInt(data.skippedRounds || 0)}</small>
      </article>
      <article>
        <span>最稳杀号池</span>
        <strong class="${strategyAuditLiftClass(killLift, true)}">${
          bestKill ? `${cdePanelLabel(bestKill.panel)} ${fmtSignedPct(killLift, 2)}` : "--"
        }</strong>
        <small>相对随机错杀率，负数才有价值</small>
      </article>
      <article>
        <span>C错杀</span>
        <strong>${bestKill ? fmtNumber(Number(bestKill.averageWrong || 0), 2) : "--"}</strong>
        <small>${bestKill ? `C 平均池 ${fmtNumber(Number(bestKill.averagePoolSize || 0), 1)}码` : "只评估 C 杀号"}</small>
      </article>
      <article>
        <span>B2前向</span>
        <strong class="${strategyAuditLiftClass(bTwoLift)}">${bTwo ? fmtPct(Number(bTwo.hitRate || 0), 2) : "--"}</strong>
        <small>${bTwo ? `理论 ${fmtPct(Number(bTwo.theoreticalHitRate || 0), 2)} · ${fmtSignedPct(bTwoLift, 2)}` : "等待 B 2码样本"}</small>
      </article>
      <article>
        <span>重复号均值</span>
        <strong>${repeat ? fmtNumber(Number(repeat.averageOverlap || 0), 2) : "--"}</strong>
        <small>理论 ${repeat ? fmtNumber(Number(repeat.expectedOverlap || 0), 2) : "--"} · Z ${
      repeat ? fmtNumber(Number(repeat.meanZ || 0), 2) : "--"
    }</small>
      </article>
    `;
    els.strategyAuditStats.innerHTML = `
      <article class="accent">
        <span>审计期数</span>
        <strong>${fmtInt(data.actualRounds)}</strong>
        <small>请求 ${fmtInt(data.window)} · 跳过 ${fmtInt(data.skippedRounds || 0)}</small>
      </article>
      <article>
        <span>B 2码前向</span>
        <strong class="${strategyAuditLiftClass(bTwoLift)}">${bTwo ? fmtPct(Number(bTwo.hitRate || 0), 2) : "--"}</strong>
        <small>${bTwo ? `理论 ${fmtPct(Number(bTwo.theoreticalHitRate || 0), 2)} · ${fmtSignedPct(bTwoLift, 2)}` : "等待 B 2码样本"}</small>
      </article>
      <article>
        <span>C计划 2码前向</span>
        <strong class="${strategyAuditLiftClass(Number(mTwo?.hitRateVsTheory || 0))}">${mTwo ? fmtPct(Number(mTwo.hitRate || 0), 2) : "--"}</strong>
        <small>${mTwo ? `理论 ${fmtPct(Number(mTwo.theoreticalHitRate || 0), 2)} · ${fmtSignedPct(Number(mTwo.hitRateVsTheory || 0), 2)}` : "等待 C计划 2码样本"}</small>
      </article>
      <article>
        <span>C计划 3码前向</span>
        <strong class="${strategyAuditLiftClass(Number(mThree?.hitRateVsTheory || 0))}">${mThree ? fmtPct(Number(mThree.hitRate || 0), 2) : "--"}</strong>
        <small>${mThree ? `理论 ${fmtPct(Number(mThree.theoreticalHitRate || 0), 2)} · ${fmtSignedPct(Number(mThree.hitRateVsTheory || 0), 2)}` : "等待 C计划 3码样本"}</small>
      </article>
      <article>
        <span>重复号均值</span>
        <strong>${repeat ? fmtNumber(Number(repeat.averageOverlap || 0), 2) : "--"}</strong>
        <small>理论 ${repeat ? fmtNumber(Number(repeat.expectedOverlap || 0), 2) : "--"} · Z ${
      repeat ? fmtNumber(Number(repeat.meanZ || 0), 2) : "--"
    }</small>
      </article>
    `;
  }

  if (els.strategyAuditNotes) {
    els.strategyAuditNotes.textContent = (data.notes || []).join(" ");
  }

  renderStrategyAuditVerdicts(data, windows);
  renderStrategyAuditScoreMatrix(data, windows);
  renderStrategyAuditExperiments(data, windows);
  renderStrategyAuditKillRows(windows);
  renderStrategyAuditTicketRows(windows);
  renderStrategyAuditRepeatRows(windows);
  renderStrategyAuditTrackingRows(data.tracking);
  renderStrategyAuditDetailRows(data.items || []);
}

function renderStrategyAuditKillRows(windows) {
  if (!els.strategyAuditKillRows) return;
  els.strategyAuditKillRows.closest(".panel")?.classList.add("hidden");
  els.strategyAuditKillRows.innerHTML = "";
  return;
  const rows = [];
  for (const windowItem of windows) {
    for (const item of windowItem.killPanels || []) {
      const lift = Number(item.wrongRateLift || 0);
      rows.push(`<tr>
        <td>${strategyAuditWindowLabel(windowItem)}</td>
        <td><strong>${cdePanelLabel(item.panel)}</strong><div class="muted">${escapeHtml(item.label || "")}</div></td>
        <td>${fmtNumber(Number(item.averagePoolSize || 0), 1)}</td>
        <td>${fmtNumber(Number(item.averageWrong || 0), 2)}</td>
        <td class="${strategyAuditLiftClass(lift, true)}">${fmtPct(Number(item.wrongRate || 0), 2)}<div class="strategy-audit-inline-note">${fmtSignedPct(
        lift,
        2,
      )}</div></td>
        <td>${fmtPct(Number(item.baselineWrongRate || 0), 2)}</td>
        <td>${fmtPct(Number(item.zeroWrongRate || 0), 1)} / ${fmtPct(Number(item.oneOrLessWrongRate || 0), 1)} / ${fmtPct(
        Number(item.twoOrLessWrongRate || 0),
        1,
      )}</td>
      </tr>`);
    }
  }
  els.strategyAuditKillRows.innerHTML = rows.length
    ? rows.join("")
    : '<tr><td colspan="7"><span class="muted">暂无杀号池审计数据</span></td></tr>';
}

function renderStrategyAuditETopRows(windows) {
  if (!els.strategyAuditETopRows) return;
  const rows = [];
  for (const windowItem of windows) {
    for (const item of windowItem.eTopTickets || []) {
      const coverage = item.roundCoverage || {};
      const roi = Number(item.roi || 0);
      rows.push(`<tr>
        <td>${strategyAuditWindowLabel(windowItem)}</td>
        <td><strong>Top${fmtInt(item.topCount)}</strong></td>
        <td>${fmtInt(item.tickets)}</td>
        <td>${fmtInt(item.won)}<div class="strategy-audit-inline-note">${fmtPct(Number(item.hitRate || 0), 2)}</div></td>
        <td class="${strategyAuditLiftClass(roi)}">${fmtPct(roi, 2)}</td>
        <td>${fmtPct(Number(item.twoPlusRate || 0), 1)} / ${fmtPct(Number(item.threePlusRate || 0), 1)}</td>
        <td>${fmtInt(coverage.missedFourHitRounds || 0)} / ${fmtInt(coverage.top8FourHitRounds || 0)}<div class="strategy-audit-inline-note">漏率 ${fmtPct(
        Number(coverage.missRateWhenTop8Hit || 0),
        1,
      )}</div></td>
      </tr>`);
    }
  }
  els.strategyAuditETopRows.innerHTML = rows.length
    ? rows.join("")
    : '<tr><td colspan="7"><span class="muted">暂无 E TopN 审计数据</span></td></tr>';
}

function renderStrategyAuditTicketRows(windows) {
  if (!els.strategyAuditTicketRows) return;
  const rows = [];
  for (const windowItem of windows) {
    for (const item of windowItem.ticketPanels || []) {
      if (![PREDICTION_PANEL_DEFAULT, PREDICTION_PANEL_B, PREDICTION_PANEL_M].includes(item.panel)) continue;
      if (String(item.mode || "main") !== "main") continue;
      const lift = Number(item.hitRateVsTheory || 0);
      const ci = Array.isArray(item.hitRateCi) ? item.hitRateCi : [0, 0];
      rows.push(`<tr>
        <td>${strategyAuditWindowLabel(windowItem)}</td>
        <td><strong>${strategyAuditPlanLabel(item.panel)}</strong><div class="muted">${escapeHtml(item.label || "")}</div></td>
        <td>${fmtInt(item.pickCount)}码<div class="strategy-audit-inline-note">${escapeHtml(item.mode || "main")}</div></td>
        <td>${fmtInt(item.tickets)}</td>
        <td class="${strategyAuditLiftClass(lift)}">${fmtInt(item.won)}<div class="strategy-audit-inline-note">${fmtPct(
        Number(item.hitRate || 0),
        2,
      )} · ${fmtSignedPct(lift, 2)}</div></td>
        <td>${fmtPct(Number(item.theoreticalHitRate || 0), 2)}<div class="strategy-audit-inline-note">期望 ${fmtNumber(
        Number(item.expectedWins || 0),
        1,
      )}</div></td>
        <td>${fmtPct(Number(ci[0] || 0), 2)} - ${fmtPct(Number(ci[1] || 0), 2)}</td>
        <td class="${strategyAuditLiftClass(Number(item.roi || 0))}">${fmtPct(Number(item.roi || 0), 2)}<div class="strategy-audit-inline-note">理论 ${fmtPct(
        Number(item.theoreticalRoi || 0),
        2,
      )}</div></td>
      </tr>`);
    }
  }
  els.strategyAuditTicketRows.innerHTML = rows.length
    ? rows.join("")
    : '<tr><td colspan="8"><span class="muted">暂无 A/B 前向票审计数据</span></td></tr>';
}

function renderStrategyAuditRepeatRows(windows) {
  if (!els.strategyAuditRepeatRows) return;
  const rows = [];
  for (const windowItem of windows) {
    const item = windowItem.repeat || {};
    const z = Number(item.meanZ || 0);
    const repeatLift = Number(item.previousNumberHitRate || 0) - Number(item.baselinePreviousNumberHitRate || 0);
    rows.push(`<tr>
      <td>${strategyAuditWindowLabel(windowItem)}</td>
      <td>${fmtNumber(Number(item.averageOverlap || 0), 2)}</td>
      <td>${fmtNumber(Number(item.expectedOverlap || 0), 2)}</td>
      <td class="${strategyAuditLiftClass(z, false, 1.5)}">${fmtNumber(z, 2)}</td>
      <td>${fmtPct(Number(item.previousNumberHitRate || 0), 2)}<div class="strategy-audit-inline-note ${strategyAuditLiftClass(
      repeatLift,
    )}">${fmtSignedPct(repeatLift, 2)}</div></td>
      <td>${strategyAuditOverlapDistribution(item.overlapDistribution)}</td>
    </tr>`);
  }
  els.strategyAuditRepeatRows.innerHTML = rows.length
    ? rows.join("")
    : '<tr><td colspan="6"><span class="muted">暂无重复号统计</span></td></tr>';
}

function renderStrategyAuditTrackingRows(tracking) {
  if (!els.strategyAuditTrackingRows) return;
  if (!tracking?.available) {
    els.strategyAuditTrackingRows.innerHTML = `<tr><td colspan="7"><span class="muted">${
      tracking?.error ? `追踪库不可读：${escapeHtml(tracking.error)}` : "暂无可读追踪库"
    }</span></td></tr>`;
    return;
  }
  const panels = Array.isArray(tracking.panels) ? tracking.panels : [];
  els.strategyAuditTrackingRows.innerHTML = panels.length
    ? panels
        .map((item) => {
          const roi = Number(item.roi || 0);
          return `<tr>
            <td><strong>${strategyAuditPlanLabel(item.panel)}</strong><div class="strategy-audit-inline-note">${fmtInt(item.pickCount || 0)}码</div></td>
            <td>${fmtInt(item.tickets)}</td>
            <td>${fmtInt(item.won)}<div class="strategy-audit-inline-note">${fmtPct(Number(item.hitRate || 0), 2)}</div></td>
            <td class="${strategyAuditLiftClass(roi)}">${item.tickets ? fmtPct(roi, 2) : "--"}</td>
            <td>${item.tickets ? fmtPct(Number(item.twoPlusRate || 0), 2) : "--"}</td>
            <td>${item.tickets ? fmtPct(Number(item.threePlusRate || 0), 2) : "--"}</td>
            <td>${strategyAuditStatusCounts(item.statusCounts)}</td>
          </tr>`;
        })
        .join("")
    : '<tr><td colspan="7"><span class="muted">暂无追踪统计</span></td></tr>';
}

function renderStrategyAuditDetailRows(items) {
  if (!els.strategyAuditDetailRows) return;
  const headerCells = els.strategyAuditDetailRows.closest("table")?.querySelectorAll("th") || [];
  if (headerCells[3]) headerCells[3].textContent = "A/B/C命中";
  const rows = Array.isArray(items) ? items : [];
  els.strategyAuditDetailRows.innerHTML = rows.length
    ? rows
        .map((item) => `<tr>
          <td><strong>${escapeHtml(item.drawEventId || "--")}</strong></td>
          <td>${fmtDate(item.drawTimeUtc)}</td>
          <td>${fmtInt(item.previousOverlap)}</td>
          <td>A2 ${fmtInt(item.aTwoWon)} · B2 ${fmtInt(item.bTwoWon)} · M2 ${fmtInt(item.mTwoWon)} · M3 ${fmtInt(item.mThreeWon)}</td>
        </tr>`)
        .join("")
    : '<tr><td colspan="4"><span class="muted">暂无最近明细</span></td></tr>';
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
  const parts = [PREDICTION_PANEL_C].map((panel) => {
    const result = panels?.[panel];
    const numbers = result?.wrongKilledNumbers || [];
    return `<div class="cde-wrong-group">
      <span>${cdePanelLabel(panel)}</span>
      <div>${cdeNumberBalls(numbers, numbers.length ? "kill wrong" : "safe")}</div>
    </div>`;
  });
  return `<div class="cde-wrong-stack">${parts.join("")}</div>`;
}

function cdeBucketTone(item) {
  const lift = Number(item?.wrongRateLift || 0);
  if (lift >= 0.02) return "rescue";
  if (lift <= -0.02) return "kill";
  return "neutral";
}

function cdeBucketVerdict(item) {
  const lift = Number(item?.wrongRateLift || 0);
  if (lift >= 0.02) return "可救观察";
  if (lift <= -0.02) return "可杀观察";
  return "接近随机";
}

function renderCdeKillBucketAudit(bucketAudit) {
  if (!els.cdeBacktestBucketRows) return;
  const buckets = Array.isArray(bucketAudit?.buckets) ? bucketAudit.buckets : [];
  const baseline = Number(bucketAudit?.baselineWrongRate || 0);
  if (els.cdeBacktestBucketMeta) {
    els.cdeBacktestBucketMeta.textContent = bucketAudit
      ? `${fmtInt(bucketAudit.sampleTotal || 0)} 个被杀单号样本 · 错杀 ${fmtInt(bucketAudit.wrongTotal || 0)} · 随机基准 ${fmtPct(
          baseline,
          2,
        )} · 只读不改规则`
      : "只读观察：错杀率高于随机的桶先考虑救出";
  }
  els.cdeBacktestBucketRows.innerHTML = buckets.length
    ? buckets
        .map((item) => {
          const tone = cdeBucketTone(item);
          const lift = Number(item.wrongRateLift || 0);
          return `<tr class="cde-bucket-row ${tone}">
            <td>${escapeHtml(item.dimension || "--")}</td>
            <td><strong>${escapeHtml(item.label || "--")}</strong></td>
            <td>${fmtInt(item.killTotal || 0)}杀<div class="cde-inline-note">错 ${fmtInt(item.wrongTotal || 0)} · 对 ${fmtInt(
              item.rightTotal || 0,
            )}</div></td>
            <td class="${strategyAuditLiftClass(lift, true)}">${fmtPct(Number(item.wrongRate || 0), 2)}<div class="cde-inline-note">随机 ${fmtPct(
              baseline,
              2,
            )}</div></td>
            <td class="${strategyAuditLiftClass(lift, true)}">${fmtSignedPct(lift, 2)}<div class="cde-inline-note">多错 ${fmtNumber(
              Number(item.wrongTotalLift || 0),
              1,
            )}</div></td>
            <td>少错 ${fmtInt(item.rescueWrongSaved || 0)}<div class="cde-inline-note">代价：少杀对 ${fmtInt(
              item.rescueRightLost || 0,
            )}</div></td>
            <td><span class="cde-bucket-badge ${tone}">${escapeHtml(item.verdict || cdeBucketVerdict(item))}</span></td>
          </tr>`;
        })
        .join("")
    : '<tr><td colspan="7"><span class="muted">暂无足够样本的错杀分桶</span></td></tr>';
}

function renderCdeKillBacktest(data) {
  const cdePanels = [PREDICTION_PANEL_C];
  const summaries = (Array.isArray(data.summaries) ? data.summaries : []).filter((summary) => cdePanels.includes(summary?.panel));
  const rawBestPanel = data.bestPanel || summaries[0] || null;
  const bestPanel = cdePanels.includes(rawBestPanel?.panel) ? rawBestPanel : summaries[0] || null;
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
    const bestMetric = bestPanel?.averageWrongKillCount;
    const bestLabel = bestPanel ? `${cdePanelLabel(bestPanel.panel)} · ${fmtNumber(Number(bestMetric || 0), 2)}错/期` : "--";
    const detailLabel = totalRows ? `${Number(visibleStart).toLocaleString("zh-CN")}-${Number(visibleEnd).toLocaleString("zh-CN")}` : "0";
    els.cdeBacktestStats.innerHTML = `
      <article class="accent"><span>回测期数</span><strong>${Number(data.actualRounds || 0).toLocaleString("zh-CN")}</strong><small>请求 ${Number(
        data.window || 0,
      ).toLocaleString("zh-CN")} 期</small></article>
      <article><span>C面板</span><strong>${escapeHtml(bestLabel)}</strong><small>只看 C 错杀</small></article>
      <article><span>训练窗口</span><strong>${Number(data.trainWindow || 0).toLocaleString("zh-CN")}</strong><small>每期只用开奖前历史</small></article>
      <article><span>明细</span><strong>${detailLabel}</strong><small>共 ${Number(totalRows).toLocaleString("zh-CN")} 行 · 每页 ${CDE_BACKTEST_PAGE_SIZE}</small></article>
    `;
  }
  if (els.cdeBacktestPanelCards) {
    els.cdeBacktestPanelCards.innerHTML = summaries.length
      ? summaries
          .map((summary) => {
            const wrong = Number(summary.averageWrongKillCount || 0);
            const right = Number(summary.averageRightKillCount || 0);
            const zeroWrong = Number(summary.zeroWrongRate || 0);
            const distributionItems = summary.wrongDistribution || [];
            const dist = distributionItems
              .map(
                (item) =>
                  `<span>${Number(item.wrongKillCount || 0)}错: ${Number(item.rounds || 0).toLocaleString("zh-CN")}期</span>`,
              )
              .join("");
            return `<article class="cde-panel-card">
              <div class="cde-panel-card-title">
                <strong>${cdePanelLabel(summary.panel)} 面板</strong>
                <span>${escapeHtml(summary.label || "")}</span>
              </div>
              <div class="cde-panel-metrics">
                <div><span>平均错杀</span><strong class="${wrong > 2 ? "negative" : "positive"}">${fmtNumber(wrong, 2)}</strong></div>
                <div><span>平均杀对</span><strong>${fmtNumber(right, 2)}</strong></div>
                <div><span>错杀率</span><strong>${fmtPct(Number(summary.wrongKillRate || 0), 2)}</strong></div>
                <div><span>0错期数</span><strong>${fmtPct(zeroWrong, 2)}</strong></div>
              </div>
              <div class="cde-distribution">${dist || '<span class="muted">暂无分布</span>'}</div>
            </article>`;
          })
          .join("")
      : '<article class="cde-panel-card"><span class="muted">暂无回测结果</span></article>';
  }
  renderCdeKillBucketAudit(data.killBucketAudit);
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
              <td>${cdeWrongNumbersCell(panels)}</td>
            </tr>`;
          })
          .join("")
      : '<tr><td colspan="4"><span class="muted">暂无回测明细</span></td></tr>';
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

function compactStrategyLabel(label, panel = state.predictionPanel) {
  let text = String(label || "").trim();
  if (normalizePredictionPanel(panel) === PREDICTION_PANEL_M) {
    text = text.replace(/^C计划\s*/, "");
  }
  return text || "策略候选票";
}

function ticketDisplayRank(item, fallbackIndex = 0) {
  const rank = Number(item?.ticketRank || item?.displayRank || 0);
  return Number.isFinite(rank) && rank > 0 ? rank : fallbackIndex + 1;
}

function rankedStrategyLabel(item, fallbackIndex = 0, panel = state.predictionPanel) {
  const rank = ticketDisplayRank(item, fallbackIndex);
  const pickCount = Number(item?.pickCount || (Array.isArray(item?.numbers) ? item.numbers.length : 0));
  if (normalizePredictionPanel(panel) === PREDICTION_PANEL_M && Number.isFinite(pickCount) && pickCount > 0) {
    return `${fmtInt(pickCount)}码候选#${fmtInt(rank)}`;
  }
  return `#${rank} ${compactStrategyLabel(item?.label || item?.strategyLabel, panel)}`;
}

function predictionTrackingSlotOptions(panel = state.predictionPanel) {
  const panelKey = normalizePredictionPanel(panel);
  if (panelKey === PREDICTION_PANEL_D) {
    return [
      ["all", "全部候选"],
      ["rank:2", "#2"],
      ["rank:8", "#8"],
    ];
  }
  if (panelKey === PREDICTION_PANEL_E) {
    return [
      ["all", "全部E计划"],
      ["pick:4", "全部E4"],
      ["pick:5", "全部E5"],
      ["pick:6", "全部E6"],
      ["pick:7", "全部E7"],
      ...Array.from({ length: 32 }, (_, index) => [`rank:${index + 1}`, `#${index + 1}`]),
    ];
  }
  if (panelKey === PREDICTION_PANEL_M) {
    return [
      ["all", "全部候选"],
      ["rank:1", "2码 #1"],
      ["rank:2", "2码 #2"],
      ["rank:3", "3码 #3"],
      ["rank:4", "3码 #4"],
    ];
  }
  return [
    ["all", "全部候选"],
    ["rank:1", "#1"],
    ["rank:2", "#2"],
    ["rank:3", "#3"],
  ];
}

function renderPredictionTrackingSlotFilter(data) {
  if (!els.predictionTrackingSlotFilter) return;
  const panel = normalizePredictionPanel(data?.panel || state.predictionPanel);
  const options = predictionTrackingSlotOptions(panel);
  const selected = data?.slotFilter || predictionPanelState(panel).predictionTrackingSlot || "all";
  const validValues = new Set(options.map(([value]) => value));
  const value = validValues.has(selected) ? selected : "all";
  els.predictionTrackingSlotFilter.innerHTML = options
    .map(
      ([optionValue, label]) =>
        `<option value="${escapeHtml(optionValue)}"${optionValue === value ? " selected" : ""}>${escapeHtml(label)}</option>`,
    )
    .join("");
  els.predictionTrackingSlotFilter.value = value;
}

function predictionMissCount(item) {
  if (!item) return null;
  const status = String(item.status || "").toLowerCase();
  if (status === "won" || status === "cancelled" || status === "void") return null;
  if (item.dailyMissDisplayStreak !== undefined && item.dailyMissDisplayStreak !== null) {
    const displayMiss = Number(item.dailyMissDisplayStreak);
    return Number.isFinite(displayMiss) && displayMiss > 0 ? displayMiss : null;
  }
  if (item.dailyMissStreak === undefined || item.dailyMissStreak === null) return null;
  const miss = Number(item.dailyMissStreak || 0);
  if (!Number.isFinite(miss)) return null;
  const displayMiss = status === "lost" ? miss : miss + 1;
  return displayMiss > 0 ? displayMiss : null;
}

function predictionMissText(item) {
  const displayMiss = predictionMissCount(item);
  return displayMiss ? `当前第${fmtInt(displayMiss)}期未中` : "";
}

function predictionTrackingCurrentMissText(item) {
  if (!item) return "";
  const status = String(item.status || "").toLowerCase();
  if (status === "won" || status === "cancelled" || status === "void") return "";
  const raw = item.currentMissDisplayStreak ?? item.currentMissStreak;
  const miss = Number(raw);
  if (!Number.isFinite(miss) || miss <= 0) return "";
  const displayMiss =
    item.currentMissDisplayStreak !== undefined && item.currentMissDisplayStreak !== null
      ? miss
      : status === "pending"
        ? miss + 1
        : miss;
  return displayMiss > 0 ? `跨天当前第${fmtInt(displayMiss)}期未中` : "";
}

function predictionMissLine(item, className) {
  const missText = predictionMissText(item);
  return missText ? `<div class="${className}">${escapeHtml(missText)}</div>` : "";
}

function predictionCurrentMissLine(item, className) {
  const missText = predictionTrackingCurrentMissText(item);
  return missText ? `<div class="${className} current">${escapeHtml(missText)}</div>` : "";
}

function trackingTicketNumberKey(record) {
  const source = Array.isArray(record?.numbers) && record.numbers.length
    ? record.numbers
    : String(record?.ticketLabel || "").match(/\d+/g) || [];
  return source.map((number) => Number(number || 0)).filter((number) => Number.isFinite(number) && number > 0);
}

function compareNumberKeys(left, right) {
  const length = Math.max(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    const leftValue = left[index] ?? 0;
    const rightValue = right[index] ?? 0;
    if (leftValue !== rightValue) return leftValue - rightValue;
  }
  return 0;
}

function compareCodepoint(left, right) {
  const leftText = String(left || "");
  const rightText = String(right || "");
  if (leftText < rightText) return -1;
  if (leftText > rightText) return 1;
  return 0;
}

function trackingPickCount(record) {
  const explicit = Number(record?.pickCount || 0);
  if (Number.isFinite(explicit) && explicit > 0) return explicit;
  const numbers = trackingTicketNumberKey(record);
  return numbers.length;
}

function compareTrackingUnrankedRecords(left, right) {
  const leftPanel = normalizeRecordPredictionPanel(left?.panel);
  const rightPanel = normalizeRecordPredictionPanel(right?.panel);
  const leftPickCount = trackingPickCount(left);
  const rightPickCount = trackingPickCount(right);
  const pickDiff = leftPickCount - rightPickCount;
  if (pickDiff) return pickDiff;
  if (leftPanel === PREDICTION_PANEL_M && rightPanel === PREDICTION_PANEL_M) {
    const scoreDiff = Number(right?.score || 0) - Number(left?.score || 0);
    if (scoreDiff) return scoreDiff;
    const recentDiff = Number(right?.recentHitRate || 0) - Number(left?.recentHitRate || 0);
    if (recentDiff) return recentDiff;
    const maxMissDiff = Number(left?.maxMiss || 0) - Number(right?.maxMiss || 0);
    if (maxMissDiff) return maxMissDiff;
    const currentMissDiff = Number(left?.currentMiss || 0) - Number(right?.currentMiss || 0);
    if (currentMissDiff) return currentMissDiff;
  }
  return (
    compareNumberKeys(trackingTicketNumberKey(left), trackingTicketNumberKey(right)) ||
    compareCodepoint(left?.ticketLabel, right?.ticketLabel) ||
    compareCodepoint(left?.id, right?.id)
  );
}

function fmtYuan(value, digits = 2, signed = false) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  const prefix = signed && number > 0 ? "+" : "";
  return `${prefix}${number.toFixed(digits)}元`;
}

function stakingPolicyText(policy) {
  if (!policy || typeof policy !== "object") return "--";
  if (policy.kind === "flat") return "不加倍，1元平买";
  return `连挂 ${fmtInt(policy.missBeforeDouble)} 期后加倍`;
}

function renderTicketStakingSimulation(ticket) {
  const sim = ticket.stakingSimulation;
  if (!sim || typeof sim !== "object") return "";
  if (!sim.enabled) {
    return `<div class="ticket-staking-sim disabled"><span>${escapeHtml(sim.reason || "当前候选暂无法做倍投回放。")}</span></div>`;
  }
  const best = sim.best || {};
  const flat = sim.flat || {};
  const bestDouble = sim.bestDouble || {};
  const bestNet = Number(best.netProfit || 0);
  const flatNet = Number(flat.netProfit || 0);
  const bestDoubleNet = Number(bestDouble.netProfit || 0);
  const bestClass = bestNet > 0 ? "positive" : bestNet < 0 ? "negative" : "";
  const flatClass = flatNet > 0 ? "positive" : flatNet < 0 ? "negative" : "";
  const actionText = best.kind === "flat" ? "历史最优：不加倍" : `历史最优：${stakingPolicyText(best)}`;
  const compareText =
    best.kind === "flat" && bestDouble.kind
      ? `最佳翻倍 ${stakingPolicyText(bestDouble)}，净 ${fmtYuan(bestDoubleNet, 2, true)}`
      : `平买净 ${fmtYuan(flatNet, 2, true)}`;
  const firstDoubleText =
    best.kind === "flat"
      ? "平买未触发加倍"
      : best.firstDoubleRound
        ? `第 ${fmtInt(best.firstDoubleRound)} 期首次加倍`
        : "历史窗口内未触发加倍";
  return `<div class="ticket-staking-sim">
    <div class="ticket-staking-head">
      <strong>倍投模拟</strong>
      <span>1元起步 · 上限 ${fmtInt(sim.maxMultiplier)} 倍 · 回放 ${fmtInt(sim.lookback)} 期</span>
    </div>
    <div class="ticket-staking-verdict ${bestClass}">
      <strong>${escapeHtml(actionText)}</strong>
      <span>${escapeHtml(firstDoubleText)} · 当前连挂 ${fmtInt(best.currentMissStreak)}，下一注 ${fmtYuan(best.nextStake, 2)}</span>
    </div>
    <div class="ticket-staking-grid">
      <div><span>总投入</span><strong>${fmtYuan(best.totalStake, 2)}</strong></div>
      <div><span>总返奖</span><strong>${fmtYuan(best.totalPayout, 2)}</strong></div>
      <div><span>净收益</span><strong class="${bestClass}">${fmtYuan(bestNet, 2, true)}</strong></div>
      <div><span>ROI</span><strong class="${bestClass}">${fmtPct(Number(best.roi || 0), 2)}</strong></div>
      <div><span>最大单注</span><strong>${fmtYuan(best.maxStake, 2)}</strong></div>
      <div><span>最大回撤</span><strong>${fmtYuan(best.maxDrawdown, 2)}</strong></div>
    </div>
    <div class="ticket-staking-note">
      <span class="${flatClass}">${escapeHtml(compareText)}</span>
      <span>命中 ${fmtInt(best.wins)} / ${fmtInt(best.rounds)}，最长连挂 ${fmtInt(best.longestMissStreak)}</span>
    </div>
  </div>`;
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
      const isPanelMTicket = panelKey === PREDICTION_PANEL_M;
      const recallNumbers = Array.isArray(ticket.recallNumbers) && ticket.recallNumbers.length
        ? ticket.recallNumbers
        : Array.isArray(ticket.reversalNumbers) && ticket.reversalNumbers.length
          ? ticket.reversalNumbers
          : companionNumbers;
      const sourcePoolCount = Number(ticket.sourcePoolCount || ticket.sourcePoolNumbers?.length || ticket.excludedNumbers?.length || 0);
      const sourceLabels = Array.isArray(ticket.sourceCoreTicketLabels) ? ticket.sourceCoreTicketLabels.filter(Boolean) : [];
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
                : isPanelMTicket
                  ? `<span>来源 ${escapeHtml(ticket.auditSourceLabel || sourceLabels.join(" / ") || "--")}</span>
                     <span>${escapeHtml(ticket.followDecision || "只观察")}</span>`
                : `<span>核心 ${escapeHtml(coreNumbers.join("-") || "--")}</span>
                   <span>派生 ${escapeHtml(companionNumbers.join("-") || "--")}</span>`
            }
          </div>`
        : "";
      return `<article class="prediction-ticket-card">
        <div class="prediction-card-title">
          <strong>${escapeHtml(rankedStrategyLabel(ticket, index, panelKey))}</strong>
          <span>${escapeHtml(ticket.mode === "bonus" ? `${ticket.pickCount}+1特殊` : `${ticket.pickCount}球`)} · ${fmtNumber(Number(ticket.odds || 0), 2)}x</span>
        </div>
        ${predictionMissLine(ticket, "ticket-miss-badge")}
        ${panelKey === PREDICTION_PANEL_E ? predictionCurrentMissLine(ticket, "ticket-miss-badge") : ""}
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
          <span>${Number(ticket.chasePeriods || 0)} 期全挂 ${fmtPct(Number(ticket.missAllProbability || 0), 2)}</span>
        </div>
        ${renderTicketStakingSimulation(ticket)}
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

function renderPredictionAdjacentStats() {
  return;
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
  renderPredictionTrackingSlotFilter(data);
  if (els.predictionTrackingDayFilter) {
    els.predictionTrackingDayFilter.value = data?.dayFilter || predictionPanelState().predictionTrackingDay || "";
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
  const displayRankByRecord = new Map();
  const rankGroups = new Map();
  for (const record of items) {
    const groupKey = [
      record.targetDrawTimeMs || record.targetDrawTimeUtc || "",
      record.methodVersion || "",
      normalizeRecordPredictionPanel(record.panel),
    ].join("|");
    if (!rankGroups.has(groupKey)) rankGroups.set(groupKey, []);
    rankGroups.get(groupKey).push(record);
  }
  for (const records of rankGroups.values()) {
    const usedRanks = new Set();
    const unranked = [];
    for (const record of records) {
      const rank = Number(record.ticketRank || 0);
      if (Number.isFinite(rank) && rank > 0) {
        displayRankByRecord.set(record, rank);
        usedRanks.add(rank);
      } else {
        unranked.push(record);
      }
    }
    let nextRank = 1;
    unranked
      .sort(compareTrackingUnrankedRecords)
      .forEach((record) => {
        while (usedRanks.has(nextRank)) nextRank += 1;
        displayRankByRecord.set(record, nextRank);
        usedRanks.add(nextRank);
        nextRank += 1;
      });
  }
  els.predictionTrackingRows.innerHTML = items
    .map((record, index) => {
      const recordProfit = Number(record.profit || 0);
      const targetRelative = relativeTargetLabel(record.targetDrawTimeUtc, record.status);
      const targetClass = targetRelative.startsWith("!") ? "target-overdue" : "target-relative";
      const coreNumbers = Array.isArray(record.coreNumbers) ? record.coreNumbers : [];
      const companionNumbers = Array.isArray(record.companionNumbers) ? record.companionNumbers : [];
      const recordPanel = normalizeRecordPredictionPanel(record.panel);
      const isPanelFRecord = recordPanel === PREDICTION_PANEL_F;
      const isPanelGRecord = recordPanel === PREDICTION_PANEL_G;
      const isPanelMRecord = recordPanel === PREDICTION_PANEL_M;
      const recallNumbers = Array.isArray(record.recallNumbers) && record.recallNumbers.length
        ? record.recallNumbers
        : Array.isArray(record.reversalNumbers) && record.reversalNumbers.length
          ? record.reversalNumbers
          : companionNumbers;
      const sourcePoolCount = Number(record.sourcePoolCount || record.sourcePoolNumbers?.length || record.excludedNumbers?.length || 0);
      const sourceLabels = Array.isArray(record.sourceCoreTicketLabels) ? record.sourceCoreTicketLabels.filter(Boolean) : [];
      const structureMeta = record.structureType
        ? isPanelFRecord
          ? `<div class="muted tracking-structure">${escapeHtml(record.structureLabel || record.structureType)} · 召回 ${escapeHtml(
              recallNumbers.join("-") || "--",
            )} · 候选池 ${sourcePoolCount ? `${sourcePoolCount.toLocaleString("zh-CN")}个` : "--"}</div>`
          : isPanelGRecord
            ? `<div class="muted tracking-structure">${escapeHtml(record.structureLabel || record.structureType)} · 杀号池 ${
                sourcePoolCount ? `${sourcePoolCount.toLocaleString("zh-CN")}个` : "--"
              } · 剩余池预测</div>`
          : isPanelMRecord
            ? `<div class="muted tracking-structure">${escapeHtml(record.structureLabel || record.structureType)} · 来源 ${escapeHtml(
                record.auditSourceLabel || sourceLabels.join(" / ") || "--",
              )} · ${escapeHtml(record.followDecision || "只观察")}</div>`
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
      const fallbackRank = displayRankByRecord.get(record) || index + 1;
      const missText = predictionMissText(record);
      const currentMissText = recordPanel === PREDICTION_PANEL_E ? predictionTrackingCurrentMissText(record) : "";
      const missLine = [missText, currentMissText]
        .filter(Boolean)
        .map((text) => `<div class="tracking-miss-note">${escapeHtml(text)}</div>`)
        .join("");
      const missMetaText = [missText, currentMissText].filter(Boolean).join(" · ");
      return `<tr>
        <td><strong>${fmtTime(record.targetDrawTimeUtc)}</strong>${
          targetRelative ? ` <span class="${targetClass}">${escapeHtml(targetRelative)}</span>` : ""
        }<div class="muted">${fmtDate(record.createdAt)} 创建</div></td>
        <td>
          <strong>${escapeHtml(rankedStrategyLabel(record, fallbackRank - 1, recordPanel))}</strong>
          ${missLine}
          <div class="muted">${escapeHtml(record.methodVersion || "")}${missMetaText ? ` · ${escapeHtml(missMetaText)}` : ""}</div>
          ${structureMeta}
        </td>
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
  renderPredictionAutoGameToggles();
}

function renderPredictionAutoGameToggles() {
  if (!els.predictionAutoGameToggles) return;
  const games = state.predictionAuto?.config?.games || {};
  els.predictionAutoGameToggles.innerHTML = (state.games || [])
    .filter((game) => game.supportsPredictions)
    .map((game) => {
      const checked = Boolean(games[game.key]?.enabled);
      return `<label class="auto-game-toggle">
        <input type="checkbox" data-auto-game="${escapeHtml(game.key)}" ${checked ? "checked" : ""} />
        <span>${escapeHtml(game.shortName || game.name || game.key)}</span>
      </label>`;
    })
    .join("");
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
  const isPanelF = panel === PREDICTION_PANEL_F;
  const isPanelG = panel === PREDICTION_PANEL_G;
  const showKillPanel = isPanelB || isPanelF || isPanelG;
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
      : "A计划杀号";
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
  renderPredictionKillSources(predictions, isPanelF || isPanelG);
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
  const totalNumbers = Number(state.currentGame?.totalNumbers || Math.max(0, ...numbers));
  for (const length of [7, 6, 5, 4, 3, 2]) {
    for (let start = 1; start <= totalNumbers - length + 1; start += 1) {
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
  if (level >= 7) return "ball seven-run";
  if (level === 6) return "ball six-run";
  if (level === 5) return "ball five-run";
  if (level === 4) return "ball quad";
  if (level === 3) return "ball triple";
  if (level === 2) return "ball pair";
  return "ball";
}

function renderHistoryRunStats(data) {
  if (!els.historyRunStats) return;
  const stats = data?.runStats || {};
  const drawCount = Number(stats.drawCount || 0);
  const items = Array.isArray(stats.items) ? stats.items : [];
  if (els.historyRunMeta) {
    els.historyRunMeta.textContent = drawCount
      ? `${drawCount.toLocaleString("zh-CN")} 期有效开奖`
      : "--";
  }
  if (!items.length) {
    els.historyRunStats.innerHTML = '<tr><td colspan="5"><span class="muted">暂无连号统计</span></td></tr>';
    return;
  }
  els.historyRunStats.innerHTML = items
    .map((item) => {
      const length = Number(item.length || 0);
      const isShape = item.kind === "shape" || Boolean(item.shape);
      const label = String(item.label || item.shape || `${length}连`);
      const marker = isShape
        ? `<span class="history-run-shape-badge">${escapeHtml(label)}</span>`
        : `<span class="${historyBallClass(length)}">${length}</span>`;
      const draws = Number(item.draws || 0);
      const occurrences = Number(item.occurrences || 0);
      const share = Number(item.drawShare || 0);
      const latestTime = fmtDate(item.latestDrawTimeUtc || "");
      const latestId = item.latestDrawEventId || "";
      const latest = latestId ? `${latestTime} · ${escapeHtml(latestId)}` : "--";
      return `<tr>
        <td>${marker}<strong>${escapeHtml(isShape ? "组合形态" : label)}</strong></td>
        <td>${draws.toLocaleString("zh-CN")}</td>
        <td>${occurrences.toLocaleString("zh-CN")}<div class="history-run-note">单期最多 ${Number(
          item.maxOccurrencesInDraw || 0,
        ).toLocaleString("zh-CN")} 组</div></td>
        <td>${fmtPct(share, 2)}<div class="history-run-note">均值 ${fmtNumber(Number(item.avgOccurrencesPerDraw || 0), 3)} 组/期</div></td>
        <td>${latest}</td>
      </tr>`;
    })
    .join("");
}

function renderHistory() {
  const data = state.history;
  if (!data) return;
  state.currentGame = data.game || state.currentGame;
  updateGameUi();
  renderSummary(data);
  renderHistoryRunStats(data);
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
    state.activeView === "predictionM" ||
    state.activeView === "predictionD" ||
    state.activeView === "predictionE"
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
  if (state.activeView === "strategyAudit") {
    await loadStrategyAudit({ force: options.force });
    return;
  }
  if (state.activeView === "stakingBacktest") {
    await loadStakingBacktest();
    return;
  }
  if (state.activeView === "currentBacktest") {
    await loadCurrentBacktest();
    return;
  }
  if (state.activeView === "fixedTripleObservation") {
    await loadFixedTripleObservation();
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
      view === "predictionM" ||
      view === "predictionD" ||
      view === "predictionE",
    );
  document.querySelector("#martingaleView").classList.toggle("active", view === "martingale");
  document.querySelector("#backtestView").classList.toggle("active", view === "backtest");
  document.querySelector("#stakingBacktestView")?.classList.toggle("active", view === "stakingBacktest");
  document.querySelector("#currentBacktestView")?.classList.toggle("active", view === "currentBacktest");
  document
    .querySelector("#fixedTripleObservationView")
    ?.classList.toggle("active", view === "fixedTripleObservation");
  document.querySelector("#analysisView")?.classList.toggle("active", view === "analysis");
  document.querySelector("#strategyAuditView").classList.toggle("active", view === "strategyAudit");
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
syncStakingBacktestControls();
syncMartingaleModeControls();
setMartingalePickCount(state.martingalePickCount);

if (els.applyBtn) els.applyBtn.addEventListener("click", loadAnalysis);
if (els.resetBtn) els.resetBtn.addEventListener("click", resetFilters);
if (els.strategyAuditRunBtn) {
  els.strategyAuditRunBtn.addEventListener("click", () => loadStrategyAudit({ force: true }));
}
els.refreshPageBtn.addEventListener("click", () => refreshCurrentView({ force: true }));
els.syncBtn?.addEventListener("click", () => syncData("incremental"));
els.fullSyncBtn?.classList.add("hidden");
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
if (els.predictionTrackingSlotFilter) {
  els.predictionTrackingSlotFilter.addEventListener("change", () => {
    const slot = predictionPanelState();
    slot.predictionTrackingSlot = els.predictionTrackingSlotFilter.value || "all";
    slot.predictionTrackingPage = 1;
    syncPredictionPanelMirror();
    loadPredictionTracking({ silent: true, panel: state.predictionPanel });
  });
}
if (els.predictionTrackingDayFilter) {
  els.predictionTrackingDayFilter.addEventListener("change", () => {
    const slot = predictionPanelState();
    slot.predictionTrackingDay = els.predictionTrackingDayFilter.value || "";
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
if (els.predictionAutoGameToggles) {
  els.predictionAutoGameToggles.addEventListener("change", (event) => {
    if (event.target?.matches?.("[data-auto-game]")) {
      savePredictionAutoGames();
    }
  });
}
if (els.telegramSaveBtn) {
  els.telegramSaveBtn.addEventListener("click", () => updateTelegram("save"));
}
if (els.telegramTestBtn) {
  els.telegramTestBtn.addEventListener("click", () => updateTelegram("test"));
}
if (els.telegramNotifyNowBtn) {
  els.telegramNotifyNowBtn.addEventListener("click", () => updateTelegram("notifynow"));
}
if (els.telegramAllGames) {
  els.telegramAllGames.addEventListener("change", () => {
    for (const input of document.querySelectorAll("[data-telegram-game]")) {
      input.checked = Boolean(els.telegramAllGames.checked);
    }
  });
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
if (els.runStakingBacktestBtn) {
  els.runStakingBacktestBtn.addEventListener("click", loadStakingBacktest);
}
if (els.runCurrentBacktestBtn) {
  els.runCurrentBacktestBtn.addEventListener("click", loadCurrentBacktest);
}
if (els.runFixedTripleObservationBtn) {
  els.runFixedTripleObservationBtn.addEventListener("click", loadFixedTripleObservation);
}
if (els.runFixedTripleOmissionBtn) {
  els.runFixedTripleOmissionBtn.addEventListener("click", loadFixedTripleOmission);
}
if (els.stakingBacktestSource) {
  els.stakingBacktestSource.addEventListener("change", () => {
    syncStakingBacktestControls();
    state.stakingBacktest = null;
  });
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

for (const input of [
  els.strategyAuditWindow,
  els.strategyAuditTrain,
].filter(Boolean)) {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadStrategyAudit({ force: true });
  });
  input.addEventListener("change", () => {
    state.strategyAudit = null;
    state.strategyAuditStability = null;
  });
}

for (const input of [
  els.stakingBacktestWindow,
  els.stakingBacktestCustomWindow,
  els.stakingBacktestStartDateTime,
  els.stakingBacktestEndDateTime,
  els.stakingBacktestDailyStart,
  els.stakingBacktestDailyEnd,
  els.stakingBacktestTimeZone,
  els.stakingBacktestSliceHours,
  els.stakingBacktestBaseStake,
  els.stakingBacktestStepStake,
  els.stakingBacktestConservativeStep,
  els.stakingBacktestConservativeMax,
  els.stakingBacktestStandardStep,
  els.stakingBacktestStandardMax,
  els.stakingBacktestAggressiveStep,
  els.stakingBacktestAggressiveMax,
  els.stakingBacktestCustomStep,
  els.stakingBacktestCustomMax,
  els.stakingBacktestNumbers,
].filter(Boolean)) {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && input !== els.stakingBacktestNumbers) loadStakingBacktest();
  });
  input.addEventListener("change", () => {
    state.stakingBacktest = null;
  });
}

for (const input of [
  els.currentBacktestSlot,
  els.currentBacktestSource,
  els.currentBacktestStartDateTime,
  els.currentBacktestEndDateTime,
  els.currentBacktestDailyStart,
  els.currentBacktestDailyEnd,
  els.currentBacktestTimeZone,
  els.currentBacktestBaseStake,
  els.currentBacktestStepStake,
  els.currentBacktestConservativeStep,
  els.currentBacktestConservativeMax,
  els.currentBacktestStandardStep,
  els.currentBacktestStandardMax,
  els.currentBacktestAggressiveStep,
  els.currentBacktestAggressiveMax,
].filter(Boolean)) {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadCurrentBacktest();
  });
  input.addEventListener("change", () => {
    state.currentBacktest = null;
  });
}

if (els.currentBacktestSource) {
  els.currentBacktestSource.addEventListener("change", syncCurrentBacktestSlotOptions);
}

for (const input of [
  els.fixedTripleObservationPickCount,
  els.fixedTripleObservationDays,
  els.fixedTripleObservationTop,
  els.fixedTripleObservationMinDailyHits,
  els.fixedTripleObservationForwardDays,
  els.fixedTripleObservationStartDateTime,
  els.fixedTripleObservationEndDateTime,
  els.fixedTripleObservationTimeZone,
  els.fixedTripleObservationBaseStake,
  els.fixedTripleObservationStepStake,
  els.fixedTripleObservationConservativeStep,
  els.fixedTripleObservationConservativeMax,
].filter(Boolean)) {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadFixedTripleObservation();
  });
  input.addEventListener("change", () => {
    state.fixedTripleObservation = null;
    state.fixedTripleOmission = null;
  });
}

for (const input of [
  els.fixedTripleOmissionNumbers,
  els.fixedTripleOmissionDate,
].filter(Boolean)) {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadFixedTripleOmission();
  });
  input.addEventListener("change", () => {
    state.fixedTripleOmission = null;
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
    syncCurrentBacktestSlotOptions();
    await loadGames();
    await refreshCurrentView();
    await loadPredictionAutoStatus({ silent: true, refreshTracking: false });
    await loadTelegramStatus({ silent: true });
    startPredictionAutoPolling();
  } catch (error) {
    showToast(`初始化失败：${error.message}`, true);
  }
}

init();
