# CPGAME Handoff

Updated: 2026-06-12 Asia/Shanghai

This handoff is intentionally ASCII-only. Local PowerShell output can garble
Chinese text, and the next session must be able to read this file reliably.

## Current Production Issue

The previous Poland sync stuck point is resolved.

Current active issue:

```text
Production frontend refresh can wait several minutes before C-plan appears,
especially after supervisor restart. User also reported frontend toast
`HTTP 504` on C-plan prediction load after pulling commit f96386b.
```

User requirement:

```text
Do not change prediction rules.
Only optimize speed, computation scheduling, and diagnostics.
After every code change, commit + push, then tell user to pull on server.
Also update this HANDOFF.md.
```

## Current Code Change

Local change made in:

```text
keno_dashboard_server.py
```

Purpose:

- Make `/api/predictions` faster after production frontend refresh.
- Avoid expensive prediction calculation when the next target draw is not
  usable yet.
- Reduce supervisor restart cold-start pain by prewarming C-plan.
- Reduce background auto-tracking CPU/lock pressure.
- Add timing diagnostics to prove where time is spent.

No prediction algorithm/rules were changed.

## 2026-06-12 Production 504 Follow-up

User screenshot showed production shell successfully pulled:

```text
a998aa1..f96386b main -> origin/main
HEAD = f96386b
```

But the screenshot did not show:

```text
supervisorctl restart cpgame
```

Important: `git pull` updates files on disk but does not reload an already
running Python process. If production still returns 504, first confirm that
supervisor was restarted and that port 8787 is served by the new process.

Later production screenshots confirmed:

```text
1. SSH does not have `supervisorctl`.
2. Production is managed from the aaPanel Super/Supervisor plugin UI.
3. User restarted cpgame from that UI.
4. Backend process changed from old pid/start time to a new pid.
5. Direct backend curl to /api/predictions returned in about 1.1 seconds.
```

Current interpretation:

```text
The original 504/5-minute wait was mainly caused by the old Python process not
being restarted after git pull. After aaPanel Super restart, backend direct
prediction speed is much better. Remaining frontend refresh delay may come from
overlapping frontend requests, tracking refresh, auto sync, or proxy/browser
flow rather than raw prediction compute.
```

The screenshot also showed two diagnostic command problems:

```text
1. `git rev-parse` was prefixed by terminal paste control characters.
2. `grep -E` pattern was split across lines, so grep got no pattern.
3. The final `curl ... |` left the shell in a `>` continuation prompt.
```

If the server shell prompt is still `>`, press Ctrl+C before running more
commands.

Current assessment:

```text
Because local is fast and production returns HTTP 504, this is highly likely
to be production runtime/deployment/proxy contention rather than prediction
rule logic.
```

Top checks:

```text
1. Was supervisor restarted after pull?
2. Is there exactly one backend process on port 8787?
3. Does direct backend curl to 127.0.0.1:8787 return fast?
4. Does the JSON response include the new `performance` object?
5. If backend is fast but browser shows 504, inspect Nginx/aaPanel upstream
   timeout logs.
6. If backend direct curl hangs, inspect CPU, SQLite lock/contention, and
   auto-tracking overlap.
```

Claude audit package was rebuilt locally:

```text
F:\my dev path equivalent\CPGAME\claude
```

Actual Windows path:

```text
F:\我的开发\CPGAME\claude
```

Package contents:

```text
claude/code/
claude/docs/
claude/diagnostics/
claude/README.md
claude/PRODUCTION_504_AUDIT_HANDOFF_ASCII.md
claude/SERVER_PRODUCTION_COMMANDS.md
```

It includes current key code, handoff docs, git diagnostics, the f96386b patch,
local auto config snapshot, and the production 504 screenshot. Runtime CSV data,
SQLite DB files, logs, and cache files were intentionally excluded.

## Implemented Optimizations

1. Prediction API performance diagnostics

`/api/predictions` now includes:

```text
performance.cacheHit
performance.historyIdentityMs
performance.historyLoadMs
performance.historyRows
performance.cacheLookupMs
performance.dataPrepMs
performance.targetContextMs
performance.predictionComputeMs
performance.targetContextAfterComputeMs
performance.cacheStoreMs
performance.trackingTouchMs
performance.totalMs
performance.includeStakingSimulation
```

Use this on production if refresh is still slow.

2. C-plan default no longer runs staking simulation

Default C-plan request:

```text
/api/predictions?game=poland_keno_20_70&panel=m
```

does not compute `stakingSimulation` anymore.

That simulation is auxiliary display/risk playback only. It does not affect
number selection.

Full playback remains available explicitly:

```text
/api/predictions?game=poland_keno_20_70&panel=m&staking=1
```

Cache key now separates light and staking-included C-plan responses.

3. Early target readiness gate

Before running heavy prediction calculation, the API now checks whether the next
operating draw after latest history is a valid target.

If target is not ready, such as:

```text
next_draw_inside_betting_cutoff
history_not_synced_to_previous_draw
target_is_not_next_open_draw_after_latest_history
```

the API returns a lightweight waiting response:

```text
predictionComputeMs = 0
strategyTickets = []
trackingReady = false
```

This prevents the old wasteful path where the server computed C-plan first and
then discarded it because the target was not usable.

4. Startup prewarm

On server startup, enabled prediction games are scheduled for prediction
prewarm. Startup order was changed so prewarm is scheduled before auto tracking
resumes.

The goal is to avoid the first frontend refresh after supervisor restart paying
the full cold computation cost.

5. Auto tracking poll pressure reduced

Old behavior:

```text
single enabled game forced normal poll to 5 seconds
```

New behavior:

```text
normal poll respects config, currently 60 seconds
catch-up / waiting-for-sync poll remains 5 seconds
```

This reduces background CPU/lock pressure while frontend requests are loading.

## 2026-06-12 UI / Deployment Follow-up

User requested two small C-plan display changes:

```text
1. C-plan page already implies C-plan, so ticket names should not repeat
   "C计划".
2. C-plan low-group candidates should clearly show #1/#2/#3/#4.
3. Show current miss count on each plan as betting-cost reference only. This
   must not become an automatic follow recommendation.
```

Implemented display-only changes:

```text
web/app.js
web/styles.css
keno_dashboard_server.py
```

Details:

```text
- C-plan ticket cards now render labels like "#1 2码低组候选".
- Tracking table strategy labels also hide duplicate "C计划" for C-plan rows.
- C-plan ticket cards and tracking rows show "今日未中 N 期" from same-day
  C-plan slot tracking when same-day tracking data exists.
- Text explicitly marks the miss count as staking/reference context, not a
  must-follow instruction.
- New tracking records carry `ticketRank` metadata for stable # display. This
  is display metadata only and does not affect prediction selection, settlement,
  or rules.
```

Follow-up correction:

```text
The previous "currentMiss" display was not the correct same-day staking
reference. It came from the historical/training-window ticket statistics.

Correct staking reference should be same-day miss streak by C-plan slot:
use the configured game-day timezone, start from the first prediction tracking
record of that local game day, track #1/#2/#3/#4 separately, reset to 0 after
that slot wins, and increment after that slot loses. Pending, cancelled, and
void rows do not increment the streak.

Implemented `dailyMissStreak` for prediction tracking rows and C-plan ticket
cards, and changed frontend wording to "今日未中 N 期". Historical max miss is
intentionally not displayed in the C-plan staking-reference UI because it is
not useful for today's stake sizing.

Implementation notes:

- `keno_dashboard_server.py` now enriches prediction tracking responses with
  same-day slot streaks using tracking DB records for the full local game day,
  not just the current page.
- `/api/predictions` enriches C-plan ticket cards with the same field after
  prediction-cache lookup/store, so the dynamic staking reference is not part
  of the prediction algorithm or cache key.
- New records write `ticketRank` from the generated ticket order. Older records
  without `ticketRank` are ranked stably within the same target draw by
  pick-count and ticket label.
- This is display/reference metadata only; no prediction rules, scoring, odds,
  or settlement logic were changed.
```

Second correction after UI/backtest review:

```text
- User-facing C-plan names are now unified as `2码候选#1`, `2码候选#2`,
  `3码候选#3`, and `3码候选#4`.
- The prediction cards, prediction tracking table, and current backtest dropdown
  use the same naming so `3码候选#3` means the same ticket everywhere.
- Current backtest still accepts internal slot keys such as `p3_1`, but the
  visible label is `3码候选#3`.
- Current backtest now maps old tracking rows without `ticketRank` through the
  same display-rank fallback used by the tracking table, instead of re-sorting
  by score. This fixes the Poland 2026-06-12 16:06 Beijing case where
  `5-39-55` should be `3码候选#3` and count under `p3_1`.
- Current miss wording is now `当前第xx期未中`. It is shown directly under the
  strategy name as stake-sizing reference, while won rows do not show a miss
  badge.
- Current backtest policy cells now also show total payout and hit count, making
  it easier to verify that a 3-code hit is paid at the stake level active before
  that draw.
```

Local verification for this correction:

```text
- Beijing 2026-06-12 16:06 / UTC 2026-06-12T08:06:
  `5-39-55` maps to `p3_1`, label `3码候选#3`, status `won`, matched 3/3.
- Before that hit, same-day `3码候选#3` had 53 misses. With default stakes:
  flat stake 1 -> payout 40; conservative stake 2 -> payout 80; standard stake
  3 -> payout 120; aggressive stake 6 -> payout 240.
- 2026-06-12 current backtest for `p3_1` reports selection label
  `3码候选#3` and includes the hit in policy totals.
```

Third correction:

```text
- The old-record fallback rank used string sorting for `ticketLabel`, which put
  `12-28-58` before `2-6-39`. That misassigned the 2026-06-12 16:26 Beijing
  3/3 hit to `3码候选#4` instead of `3码候选#3`.
- Backend and frontend fallback ranking now compare ticket numbers numerically,
  then fall back to label/id. This keeps old rows without `ticketRank` aligned
  between tracking display and current backtest.
- Rechecked `3码候选#3`: 2026-06-12 now includes both 16:06 `5-39-55` and
  16:26 `2-6-39` as wins.
- Current backtest daily totals are moving values while same-day records keep
  settling. Earlier local snapshot for 2026-06-12, `3码候选#3`, reported
  flat +7, conservative +23, standard +39, aggressive +83 with default stakes.
  Do not treat those as fixed expected values after more draws settle.
- Removed the extra current-backtest row text `返奖 xx · 命中 x`; user wanted
  the amount corrected, not extra display text.
```

Fourth correction after staking ledger review:

```text
- Scope is single slot `3码候选#3` / internal `p3_1`. Do not merge `#4` or
  `全部3码候选` when the user is checking #3.
- Current backtest policy simulation can return a non-UI `hitLedger` field per
  policy when the query includes `ledger=1`. This is for auditing the money
  only: each hit includes draw time, slot, ticket, missBefore, stake, odds,
  payout, ticketProfit, and balance after that ticket. Normal UI queries do not
  include this field.
- The current backtest table wording changed from ambiguous `最高` to
  `峰值净利`. This value is `peakProfit`, the highest cumulative net balance in
  the day, not highest stake. Highest stake remains available as `maxStake` in
  the API.
- Frontend `当前第xx期未中` now uses backend `dailyMissStreak` exactly. It no
  longer adds +1 for pending rows, so the displayed count matches the stake
  tier used for the next/current bet.
- Local raw record check: Beijing 17:14 and 17:34 hits were `3码候选#4`, not
  `3码候选#3`; they must not be counted in the #3 single-slot ledger.
- Local latest snapshot while editing (records settled through Beijing 18:02)
  for 2026-06-12 `3码候选#3`:
  - 16:06 `5-39-55`: missBefore 53. flat stake 1/payout 40; conservative
    stake 2/payout 80; standard stake 3/payout 120; aggressive stake 6/payout
    240.
  - 16:26 `2-6-39`: missBefore 4. all ladder profiles were back at stake 1,
    payout 40.
  - 17:58 `5-19-62`: missBefore 22. flat stake 1/payout 40; conservative
    stake 1/payout 40; standard stake 2/payout 80; aggressive stake 3/payout
    120.
  Latest local totals at that snapshot: flat +38, conservative +54, standard
  +107, aggressive +182. These totals will change as later draws settle; use
  `hitLedger` to audit the exact stake sequence for the current server state.
```

Fifth correction for visible current-miss text:

```text
- The backend was already returning `dailyMissStreak` for C-plan tracking rows
  and current prediction tickets, but the frontend hid zero values. That meant
  a freshly reset/current pending ticket could show no `当前第xx期未中` text.
- Frontend display now shows pending/current tickets as `dailyMissStreak + 1`,
  so a newly reset candidate displays `当前第1期未中` instead of disappearing.
  Settled lost rows still display the backend `dailyMissStreak` value.
- This is display-only. Staking backtest money still uses the pre-bet miss
  count (`missBefore`) from the ledger, so bet sizing remains unchanged.
```

Sixth correction for the missing text in the actual tracking table:

```text
- User screenshot still showed no `当前第xx期未中` in the C-plan tracking table.
  Root cause: the running table payload can expose the visible streak as
  `currentMiss`/old fields while the frontend was only checking
  `dailyMissStreak`, and the previous edit also introduced a class name that
  had no styling.
- Backend now emits an explicit `dailyMissDisplayStreak` for C-plan tracking
  rows and prediction tickets. Pending/current tickets use the next/current bet
  display count; settled lost rows use the settled same-day miss streak; won,
  cancelled, and void rows do not display a miss badge.
- Frontend now renders `当前第xx期未中` directly under the strategy name with
  the existing `tracking-miss-note` style, and also appends the same text after
  `strategy-ticket-m-lowgroup-v1` in the visible method line. This is deliberate
  double visibility for the exact strategy column shown in the screenshot.
- `web/index.html` now cache-busts `/app.js` and `/styles.css` with
  `v=20260612-miss-visible`, so production browsers should load the corrected
  frontend after pull/restart instead of reusing stale JavaScript.
```

Deployment docs were updated:

```text
DEPLOYMENT.md now records that production restarts cpgame from aaPanel
Super/Supervisor plugin UI. `supervisorctl` may not exist in SSH on this server.
```

## Local Verification

Syntax checks passed:

```powershell
python -m py_compile .\keno_dashboard_server.py .\fetch_official_supplements.py
node --check .\web\app.js
```

Local backend is running:

```text
http://127.0.0.1:8787
wrapper pid = 39128
port pid = 41072
```

Auto tracking status after clean restart:

```text
pollSeconds = 60
effectivePollSeconds = 60
effectiveCatchupPollSeconds = 5
message = auto tracking completed; normal poll 60 seconds
```

Default C-plan request after restart:

```text
/api/predictions?game=poland_keno_20_70&panel=m&autoSync=0
```

Observed locally:

```text
request wall time ~= 55 ms
cacheHit = true
trackingReady = true
tickets = 4
stakingSimulationIncluded = false
ticketHasStaking = false
performance.totalMs = 2
performance.trackingTouchMs = 2
```

When target is inside betting cutoff:

```text
targetReason = next_draw_inside_betting_cutoff
predictionComputeMs = 0
totalMs ~= 250 ms
tickets = 0
```

This is expected: do not generate a plan for a draw that is too close to closing.

## Files To Commit / Push

Commit only:

```text
keno_dashboard_server.py
web/app.js
web/styles.css
DEPLOYMENT.md
HANDOFF.md
```

Do not commit runtime/local dirty files unless explicitly requested:

```text
data/*.csv
data/prediction_auto_config.json
cpgame_audit_v8_sync.md
claude/
*.bat helper files
```

## Server Pull Steps

After push, user should run on production:

```bash
cd /www/wwwroot/cpgame
git pull origin main
/www/wwwroot/cpgame/.venv/bin/python -m py_compile keno_dashboard_server.py fetch_official_supplements.py
```

Then restart from aaPanel:

```text
Open aaPanel Super/Supervisor plugin, restart cpgame from the UI.
Do not rely on `supervisorctl` on this server; SSH reported command not found.
```

Then verify from SSH:

```bash
ps -ef | grep keno_dashboard_server.py | grep -v grep
ss -ltnp | grep 8787
```

Auto tracking status:

```bash
curl -m 10 -sS http://127.0.0.1:8787/api/prediction-auto > /tmp/cpgame_auto.json
python3 -m json.tool /tmp/cpgame_auto.json | head -120
```

Expected normal state depends on production runtime config:

```text
status/running present
effectivePollSeconds present
effectiveCatchupPollSeconds present
```

Check C-plan performance:

```bash
u=http://127.0.0.1:8787/api/predictions
q='game=poland_keno_20_70&panel=m&autoSync=0'
time curl -m 60 -sS -o /tmp/p.json "$u?$q"
python3 -m json.tool /tmp/p.json | head -120
```

If it is still slow, inspect the `performance` fields first before changing
logic.

## User Context

Respond in Chinese in the next conversation.

Preferred user-facing terms:

```text
gen = follow
bu gen = do not follow
zhi guan cha = observe only
jiang cheng ben = reduce cost
bu gai gui ze = do not change rules
```

The user is sensitive to:

- changing prediction rules just to make UI show a plan,
- production refresh taking minutes,
- repeated fixes not being pushed,
- handoff not being updated.

Always push after code changes when asked/expected, and tell user to pull on
server.

## Session Restart Handoff - 2026-06-12 19:00 CST

Current user state:

```text
User will restart the conversation/session.
First task after restart: read Claude's audit result.
Second task after restart: re-audit/back-calculate 2026-06-08, 2026-06-09,
2026-06-10, and 2026-06-11 current-backtest profit. User believes the all-red
negative result for these days is definitely suspicious/wrong and wants a
proper reverse calculation, not another UI-only explanation.
```

Important correction/root cause from this session:

```text
The repeated "当前第xx期未中" display failure was not only a frontend code issue.
Local port 8787 was still running an old Python process from 2026-06-12 13:46
and had not been restarted after the frontend/backend edits. The user kept
refreshing the browser, but the server was still serving old runtime code.

Old local listener:
PID 41072, python.exe, started 2026-06-12 13:46:52.

It was stopped and local service was restarted from:
F:\我的开发\CPGAME\start_server.ps1

Current verified local listener after restart:
PID 9972 on 127.0.0.1:8787.

After restart, the C-plan tracking table finally shows "当前第xx期未中" and the
current-backtest label changed from old "3码1" to new "3码候选#3".
```

Claude audit package created for the missing current-miss issue:

```text
F:\我的开发\CPGAME\claude\cplan_miss_visible_20260612_1845
```

Package includes:

```text
README_FOR_CLAUDE.md
keno_dashboard_server.py
web/app.js
web/index.html
web/styles.css
HANDOFF.md
DEPLOYMENT.md
latest_commit_diff.patch
git_head.txt
tracking_payload_sample.json
screenshots/missing_current_miss.png
```

Latest pushed code commit before session restart:

```text
77cd53aa19c45e976f072b2c216dfccd907d4797
Make C-plan miss count visible
```

Local verification after restart:

```text
GET /api/current-staking-backtest?game=poland_keno_20_70&source=m&slot=p3_1&timeZone=Asia/Shanghai&baseStake=1&stepStake=1&conservativeStepMisses=30&conservativeMaxStake=5&standardStepMisses=20&standardMaxStake=8&aggressiveStepMisses=10&aggressiveMaxStake=12

selection.label = 3码候选#3
summary.rounds = 903
summary.bets = 903
summary.policies.conservative.netProfit = -586.0
coverage.records = 3612
coverage.startTimeUtc = 2026-06-08T13:38:00+00:00
coverage.endTimeUtc = 2026-06-12T12:06:00+00:00
```

Local day rows after restart for `slot=p3_1` / `3码候选#3`:

```text
date        rounds bets flat    conservative standard aggressive
2026-06-12  114    114   +6.00   +20.00       +63.00   +114.00
2026-06-11  242    242  -122.00 -207.00      -302.00  -554.00
2026-06-10  209    209   -89.00 -121.00      -100.00  -127.00
2026-06-09  223    223   -63.00 -157.00      -180.00  -349.00
```

The user specifically challenged these all-negative historical day results.
Do not assume they are correct. Reconstruct the per-ticket ledger for
2026-06-08 through 2026-06-11 and verify:

```text
- Which records are selected into p3_1 / "3码候选#3" each draw.
- Whether old records without ticketRank are mapped to #3 correctly.
- Whether day boundaries use the expected game day and Beijing display range.
- Whether payout odds/stakes are applied before resetting miss streak.
- Whether all wins for those days are included and assigned to the correct
  candidate slot.
```

Useful next commands:

```powershell
Invoke-RestMethod "http://127.0.0.1:8787/api/current-staking-backtest?game=poland_keno_20_70&source=m&slot=p3_1&timeZone=Asia/Shanghai&baseStake=1&stepStake=1&conservativeStepMisses=30&conservativeMaxStake=5&standardStepMisses=20&standardMaxStake=8&aggressiveStepMisses=10&aggressiveMaxStake=12&ledger=1"

python -c "import keno_dashboard_server as k; p=k.current_staking_backtest_payload({'game':['poland_keno_20_70'],'source':['m'],'slot':['p3_1'],'timeZone':['Asia/Shanghai'],'baseStake':['1'],'stepStake':['1'],'conservativeStepMisses':['30'],'conservativeMaxStake':['5'],'standardStepMisses':['20'],'standardMaxStake':['8'],'aggressiveStepMisses':['10'],'aggressiveMaxStake':['12'],'ledger':['1']}); print(p['selection']['label'], p['summary']['rounds'], p['summary']['policies']['conservative']['netProfit'])"
```

Current uncommitted local files at restart are runtime/local only:

```text
data/bc_italy_win_for_life_10_20_history.csv
data/bc_poland_keno_20_70_history.csv
data/bc_russia_rapido_8_20_history.csv
data/bc_spain_l_express_20_70_history.csv
data/prediction_auto_config.json
cpgame_audit_v8_sync.md
启动Claude.bat
claude/cplan_miss_visible_20260612_1845/
```

Do not commit runtime data or the Claude audit package unless the user
explicitly asks.

## 2026-06-12 Current Backtest Slot-Rank Audit

User corrected the day-boundary requirement:

```text
Do not use Beijing natural day 00:00-00:00.
For Poland Keno, one betting day is the configured operating day: first draw
through the next early-morning close, currently Europe/Warsaw 06:34-23:54
which displays in Beijing as about 12:34 through 05:54 next day.
```

Root cause found for suspicious 2026-06-08 through 2026-06-11 `p3_1` /
`3码候选#3` current-backtest results:

```text
Old tracking rows for those days have no `ticketRank`.
The fallback rank reconstruction used numeric ticket ordering.
But C-plan originally generated candidates by pick count, then score,
recentHitRate, maxMiss, currentMiss, and ticket numbers.
This could swap the old #3/#4 3-code candidates.
```

Fix implemented:

```text
keno_dashboard_server.py
- Added `prediction_tracking_unranked_sort_key`.
- For C-plan rows without `ticketRank`, fallback ranking now mirrors the
  original C-plan candidate ordering as closely as possible from stored fields:
  pickCount, score desc, recentHitRate desc, maxMiss asc, currentMiss asc,
  numeric ticket key, label, id.
- Fixed a temporary indentation mistake in `prediction_tracking_daily_slot_ranks`
  that had accidentally attached `else` to the `for` instead of `if rank > 0`.

web/app.js
- Tracking-table fallback display rank now uses the same C-plan ordering for
  rows without `ticketRank`, keeping visible labels aligned with backend
  current-backtest slot assignment.
```

This is a historical tracking/backtest slot-assignment fix only. It does not
change prediction generation rules, selected numbers for new C-plan payloads,
odds, settlement, or staking formulas.

Local process verification after edit:

```text
Old local backend PID 43596 was stopped.
New local backend PID 18744 started at 2026-06-12 20:53:03.
API verification below was run against that restarted process.
```

Local syntax checks passed:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
python -m py_compile .\tmp\audit_current_backtest_days.py
```

Independent script and API now agree for `slot=p3_1`, Europe/Warsaw
2026-06-08 through 2026-06-11:

```text
date        rounds wins flat    conservative standard aggressive
2026-06-08  115    3    +5.00   +33.00       +32.00   +94.00
2026-06-09  223    8   +97.00  +122.00      +112.00  +159.00
2026-06-10  209    4   -49.00   +23.00       +37.00  +154.00
2026-06-11  242    5   -42.00  -129.00      -179.00  -302.00
```

Main corrected hits now included under `3码候选#3`:

```text
2026-06-08 betting day includes Beijing 2026-06-09 04:10, 33-55-63,
missBefore 70, conservative stake 3, payout 120.

2026-06-09 betting day includes 8 wins, including Beijing 2026-06-10 01:06,
19-28-36, missBefore 32, conservative stake 2, payout 80.
```

Important interpretation:

```text
The previous all-red historical rows were not reliable. They came from old-row
slot reconstruction, not from a prediction-rule change. After the fallback fix,
6/8, 6/9, and 6/10 are not all-red; 6/11 remains negative but less severe.
```

## 2026-06-12 Claude Follow-up Hardening

Claude reviewed commit `7d19367` and concluded the fix is correct and
minimal, but recommended several low-risk hardening changes.

Implemented follow-up hardening:

```text
keno_dashboard_server.py
- Added `prediction_tracking_daily_slot_rank_info(records)` returning both
  rank and rankSource (`stored` or `fallback`).
- Kept `prediction_tracking_daily_slot_ranks(records)` as a compatibility
  wrapper for existing callers.
- Current-backtest selected tickets and `hitLedger` now include `ticketRank`
  and `rankSource`, making old-row fallback visible in diagnostics.
- Prediction tracking API rows enriched by daily-miss logic now include
  `rankSource`.
- In current-backtest policy simulation, default odds fallback now applies only
  when `odds <= 0`, not `odds <= 1`. This avoids incorrectly overwriting a
  legitimate odds value of 1.0 in generic future cases.

web/app.js
- Added `normalizeRecordPredictionPanel(panel)` so record-level fallback matches
  backend behavior: missing panel defaults to A-plan, not the currently selected
  UI panel.
- Tracking fallback rank sorting now uses numeric pickCount fallback from
  `numbers.length`, matching backend behavior.
- Tracking fallback string ties now use plain codepoint comparison instead of
  `localeCompare("zh-CN")`, reducing frontend/backend divergence risk.
```

Not implemented yet:

```text
- Full performance refactor for repeated rank-map calculation on very large
  windows. Current windows are small enough; revisit before expanding to 30+
  days.
- Backfilling old rows with synthetic ticketRank. Runtime fallback is safer
  because it keeps old data auditable and avoids baking current code's
  reconstruction into historical records.
- Reconstructing the original diversity-filter step for old rows. Old records
  do not store enough candidate-pool data for perfect reconstruction. New rows
  already store `ticketRank`, which is the real fix going forward.
```

Local verification after hardening:

```text
python -m py_compile .\keno_dashboard_server.py .\tmp\verify_cplan_slot_rank_fix.py
node --check .\web\app.js
python .\tmp\verify_cplan_slot_rank_fix.py
```

The local backend was restarted again:

```text
Old local PID 18744 stopped.
New local PID 14796 started at 2026-06-12 22:42:25.
```

API verification after restart:

```text
GET /api/current-staking-backtest?...slot=p3_1&timeZone=Europe/Warsaw&
startDateTime=2026-06-08T00:00:00&endDateTime=2026-06-11T23:59:59&ledger=1

date        rounds wins flat    conservative standard aggressive
2026-06-08  115    3    +5.00   +33.00       +32.00   +94.00
2026-06-09  223    8   +97.00  +122.00      +112.00  +159.00
2026-06-10  209    4   -49.00   +23.00       +37.00  +154.00
2026-06-11  242    5   -42.00  -129.00      -179.00  -302.00
```

The first 2026-06-08 hit ledger entries now include diagnostics such as:

```text
slotKey=p3_1
slotLabel=3码候选#3
ticketRank=3
rankSource=fallback
ticketLabel=33-55-63
missBefore=70
stake=3
payout=120
```

Tracking API verification:

```text
/api/prediction-tracking?...panel=m...
Recent new rows include `rankSource: stored`; old reconstructed rows can show
`rankSource: fallback`.
```

## 2026-06-12 Production 504 / Missing C-plan Rows Follow-up

User confirmed production was pulled and restarted from aaPanel Super UI, and
HEAD matched `21d0e92`, but C-plan still waited about 4 minutes and then showed
HTTP 504. A later screenshot showed C-plan tracking finally created new rows at
23:03 for the 23:06 target, while the rows between 22:50 and 23:06 were absent.

Current diagnosis:

```text
1. The page could render existing C-plan tracking rows, so static assets and
   HEAD mismatch were not the root issue.
2. The frontend prediction request used autoSync=0, but the follow-up tracking
   table request did not. That meant ordinary page refreshes could still invoke
   tracking auto-sync/settlement work.
3. The prediction endpoint also touched the tracking DB under
   PREDICTION_TRACKING_LOCK even for no-auto-sync page loads. If the auto worker
   or settlement held that lock, the page request could wait long enough for the
   proxy to return 504.
4. When the auto worker hit a "target not ready / inside betting cutoff" state,
   it could mark the current history marker as handled even though no candidate
   rows were created. After a stall, it then jumped to the next available target
   instead of short-polling until a clean target window was available.
```

Implemented fix:

```text
web/app.js
- All ordinary prediction tracking table reads now send autoSync=0.
- The automatic retry after trackingReady=false no longer enables autoSync.
  Sync remains the job of the backend auto worker or explicit user sync action.

keno_dashboard_server.py
- Added PREDICTION_TRACKING_TOUCH_LOCK_TIMEOUT_SECONDS = 1.5.
- For no-auto-sync /api/predictions calls, lightweight tracking touch now uses a
  short lock timeout. If tracking is busy, the endpoint returns the prediction
  payload with predictionTracking.reason = prediction_tracking_lock_busy instead
  of waiting until Nginx/aaPanel returns 504.
- Auto worker now exposes waitingForTarget.
- If predictions return trackingReady=false and no rows were created, auto
  tracking does not update PREDICTION_AUTO_HISTORY_MARKERS for that game.
- waitingForTarget and refresh errors put auto tracking into the existing
  5-second catch-up poll instead of the normal 60-second poll.
```

Important behavior:

```text
The fix does not backfill target draws that were already past the betting
cutoff. Creating retroactive "pending" candidates would be misleading because
they were not actually available to bet at that time. The fix prevents the
system from continuing to skip future eligible targets after a stall.
```

Local verification after edit and real backend restart:

```text
Old local backend PID 48632 stopped.
New local backend PID 49480 started at 2026-06-12 23:20:40.

python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js

GET /api/predictions?game=poland_keno_20_70&panel=m&autoSync=0
During cutoff window:
  predictionComputeMs = 0
  totalMs ~= 133
  predictions.trackingReady = false
  predictionTracking.reason = prediction_target_not_ready

GET /api/prediction-tracking?...panel=m&autoSync=0
  autoSync.reason = request_disabled

GET /api/prediction-auto
  waitingForDraw = true
  waitingForTarget = true
  pollSeconds = 5
  message includes short polling for draw sync
```

This change is scheduling/locking/frontend request behavior only. It does not
change C-plan number generation, ranking, odds, settlement, or staking formulas.

## 2026-06-13 Session Restart Note

User is restarting the Codex session after the C-plan production 504 / missing
rows fix. Continue from commit:

```text
a75a686 Fix C-plan tracking refresh contention
```

Current local state to remember:

```text
- The code fix has already been committed and pushed.
- Local backend was restarted after the fix and verified on PID 49480, started
  at 2026-06-12 23:20:40.
- Syntax checks passed:
  python -m py_compile .\keno_dashboard_server.py
  node --check .\web\app.js
- Runtime/local files remain dirty and should not be committed unless the user
  explicitly asks:
  data/bc_*_history.csv
  data/prediction_auto_config.json
  cpgame_audit_v8_sync.md
  tmp_current_backtest_full.json
  启动Claude.bat
```

Production follow-up expectations:

```text
- Production must pull to HEAD a75a686 and restart the aaPanel Super/Supervisor
  process. Do not assume a code change is live until the process PID/start time
  is checked.
- If the browser still shows 504, first test the local backend directly on the
  server with curl against 127.0.0.1:8787 and inspect:
  performance.totalMs
  performance.trackingTouchMs
  predictionTracking.reason
  prediction-auto.waitingForTarget
  prediction-auto.pollSeconds
- Already missed target rows should not be inserted as ordinary pending/live
  records after the betting cutoff. Only do audit-only reconstruction if the
  user explicitly asks for it.
```

Important domain rule repeated by the user:

```text
Do not calculate a betting day by natural 00:00-00:00 calendar days.
For Poland Keno, treat one operating day as the first draw of the local game day
through the next Beijing early-morning close, roughly Europe/Warsaw 06:34-23:54
and Beijing 12:34-05:54 next day.
```

Next planned topic after restart:

```text
Discuss automation. Likely areas:
- Make production deploy/restart verification harder to miss.
- Add health checks that detect whether the running backend process actually
  serves the expected git HEAD.
- Add observability for the prediction auto worker: last run, last completed,
  waitingForDraw, waitingForTarget, createdPredictions, lock wait, and current
  poll interval.
- Consider a safe admin/status endpoint or script for "pull, compile, restart,
  verify PID/start time, verify HEAD, smoke-test APIs" without changing C-plan
  prediction rules.
```

## 2026-06-13 Auto Sync Gap Fix

Observed issue:

```text
The auto worker could sleep for 60 seconds even when a pending prediction
target existed for the next 4-minute draw.
If the worker woke up after the official result had already moved past the
betting window, it could skip a whole target period and create the next batch
too late.
```

Implemented scheduling-only fix in:

```text
keno_dashboard_server.py
```

What changed:

```text
- Added prediction_tracking_pending_sync_status(...).
- The auto worker now checks for pending targets before calling the official
  sync path.
- If the next target is not yet due, the worker does not start a refresh for
  that target.
- If the next target is due or overdue, the worker switches to short catch-up
  polling.
- The next sleep is capped by the earliest pending target sync due time, so
  the worker does not keep sleeping past a near-term target.
```

What did not change:

```text
- prediction rules
- candidate ranking
- odds
- settlement
- ticket labeling
```

Local verification:

```text
- Restarted local backend after the edit.
- Verified /api/prediction-auto now exposes pendingSync when a future target is
  pending.
- Verified the 19:42 -> 19:46 sequence on 2026-06-13 created the 19:46 batch
  after the 19:42 draw settled, without skipping the target period in between.
- Verified overdue state flips to waitingForDraw=true and pollSeconds=5.
```

Production follow-up:

```text
Pull latest main, restart the aaPanel Supervisor-managed cpgame process, then
confirm the running PID/start time changed before trusting the fix.
```

## 2026-06-19 Prediction Auto Gap Optimization

User correction:

```text
D-plan is currently performing well. Do not stop or disable the current D-plan.
```

Production symptom:

```text
The server process kept running, but current backtest still showed severe
missing candidate periods. This can happen when the auto worker is delayed and
the official sync advances history by multiple draws in one loop. The worker can
only create true live candidates for the next not-yet-drawn target after the
latest synced draw; intermediate targets that are already in the past must not
be inserted as normal live/pending rows.
```

Implemented in `keno_dashboard_server.py`:

```text
- Kept A/B/C/D auto generation active; D-plan remains in the auto loop.
- Auto sync checks, settlement, and tracking touch now load only pending
  prediction rows instead of scanning the full tracking DB.
- Tracking summaries and grouping now use SQLite aggregate queries instead of
  Python-side full-record scans.
- Candidate creation checks candidate IDs against the DB before inserting, so
  loading only pending rows cannot overwrite settled records back to pending.
- Auto worker no longer schedules redundant prediction prewarm after generating
  candidates; startup prewarm is skipped when auto tracking is enabled.
- `/api/prediction-auto` now reports `skippedTargetAudit` and
  `missedCandidateTargets` when a loop observes that history advanced by
  multiple operating draws.
```

What did not change:

```text
- D-plan was not disabled.
- Prediction rules, ticket ranking, odds, settlement formulas, and staking
  backtest math were not changed.
- Browser-extension / auto-bet work remains local and is not part of this
  production fix.
```

## 2026-06-19 Remove Retired Games

User requested Spain, Russia, and Italy be removed. Production is now limited to
Poland only. The cleanup removes the old game entries from backend/frontend
configuration and removes the three old history CSV files from git tracking.

D-plan remains active and was not disabled.
