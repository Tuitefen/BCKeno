# Session Handoff

Updated: 2026-06-10 Asia/Shanghai

## Start Here

Read this file first, then inspect code only as needed:

1. `keno_dashboard_server.py`
2. `web/app.js`
3. `web/index.html`
4. `web/styles.css`

Do not use old audit notes as the entry point. The current work should stay focused on the active A/B/C prediction chain; user-facing `C计划` is implemented by backend `panel=m`, formerly named `倍投候选`.

## Current Runtime

- Workspace: `F:\我的开发\CPGAME`
- Backend URL: `http://127.0.0.1:8787`
- Current backend process last observed: `python PID 92852`
- Frontend static files are served by the backend.

If backend code changes, restart the active Python backend process. Frontend-only edits usually do not require a backend restart.

## Latest Telegram / C Plan Push Fix

On 2026-06-10, Telegram C计划 push cumulative stats were corrected.

Follow-up on 2026-06-10 night:

- The former dashboard `倍投回测` view was renamed to `固定回测`.
  - This view still calls `/api/staking-backtest`.
  - Its meaning is now explicit: current C计划 tickets or manual tickets are fixed, then replayed against historical draws.
  - It does not represent the true historical C计划 recommendations for each draw.
- Added `当前回测` view and `/api/current-staking-backtest`.
  - This uses settled `prediction_tracking` records for the real C计划 (`panel=m`) recommendations saved before each target draw.
  - Candidate slots reuse Telegram ordering: `p3_1` = `3码1`, `p3_2` = `3码2`, with combined slot options available.
  - Daily simulations now reset at the lottery operating-day boundary, not at UTC+8 midnight. For Poland this uses `Europe/Warsaw`, so the displayed UTC+8 window starts around `12:34` and ends after midnight.
  - It shows flat / conservative / standard / aggressive results, with each staking profile cell showing its own intraday peak profit and peak time.
  - The separate `保守最高摸到` table column and summary card were removed on 2026-06-10 because the same peak information is already visible inside each staking profile cell.
  - Important limitation: it can only replay dates that exist in the tracking database; it does not fabricate older historical recommendations.
- Added `3码观察` view and `/api/fixed-triple-observation`.
  - It now finds stable fixed 3-number combinations across the whole historical window, not separate Top 3 triples for each day.
  - Default settings: last 31 local days, output Top 3, require each candidate to appear at least 3 times on every selected day.
  - The statistics window now accepts up to 120 local days; actual days are limited by available local history.
  - Stable triple observation also uses the lottery operating-day boundary instead of natural UTC+8 days.
  - Ranking uses average daily hits, worst-day hits, and total hits, then checks flat/conservative daily-reset fixed staking over the historical window.
  - Forward observation starts after the selected historical window; when no later draws exist, candidates show `待观察`.
- Added fixed 3-number omission lookup to the same `3码观察` page and `/api/fixed-triple-omission`.
  - Input a fixed triple such as `3-51-61`; default date is today in the selected timezone.
  - Omission lookup also uses the lottery operating-day date; the page labels this as `开奖日日期`.
  - It returns today's draws, hits, hit rate, current miss, max miss, last hit time, recent hit rows, and flat/conservative same-day fixed staking results.
- Verification performed:
  - `python -m py_compile .\keno_dashboard_server.py` passed.
  - `node --check .\web\app.js` passed.
  - Backend restarted: current PID `24228`.
  - `/api/current-staking-backtest?game=poland_keno_20_70&slot=p3_1` returned 3 days / 436 real C计划 draws.
  - After correcting the day boundary, Poland `p3_1` current backtest for `2026-06-10` starts at `2026-06-10T04:34:00Z` (`12:34 UTC+8`), no longer at UTC+8 midnight.
  - `/api/fixed-triple-observation?game=poland_keno_20_70` uses default 31 operating days / Top 3 / min daily hits 3 and returned stable fixed-triple candidates under the corrected day boundary.
  - `/api/fixed-triple-omission?game=poland_keno_20_70&numbers=3-51-61` now counts today's Poland operating day from first draw; latest test returned 167 draws, 5 hits, current miss 19, max miss 65, conservative profit +71.

Follow-up on 2026-06-11:

- Reintroduced `D计划` as an active observation plan, replacing the old four-code derived D implementation in the live prediction path.
  - D method version is now `strategy-ticket-d-observe-23-v1`, so old D records do not mix with new D tracking.
  - D is now in active tracking with A/B/C(M); E/F/G remain retired.
  - Each D generation outputs exactly 8 tickets: 4 two-code tickets and 4 three-code tickets.
  - The four D rule families are `共识`, `拆解`, `逆向`, and `形态`; each family contributes one 2码 ticket and one 3码 ticket.
  - D uses the active A/B/C chain, where user-facing C is backend panel `m`; it does not use the retired old C four-code derived chain.
  - Prediction auto now generates D alongside A/B/C(M), so D can accumulate real forward tracking samples.
- Added a `D计划` tab to the dashboard prediction navigation.
- Updated `当前回测`:
  - Added `计划来源` selector with `C计划` and `D计划`.
  - Slot options now support up to `2码1-4` and `3码1-4`, plus `全部2码`, `全部3码`, and `全部候选`.
  - Default remains C计划, so existing C observation is unchanged.
- Renamed `3码观察` to `频码观察`.
  - Added `码数` selector for 3-8码.
  - `/api/frequency-observation` was added as the new endpoint; `/api/fixed-triple-observation` remains as a compatibility alias.
  - 3码 is counted exhaustively.
  - 4-8码 uses a global high-frequency number pool for the selected historical window to keep runtime bounded. The response includes `poolSize`, `poolNumbers`, and `cappedDays` so this pruning is visible.
  - The fixed omission lookup now accepts 3-8 numbers, matching the selected frequency-code size.
- Removed the user-facing adjacent derived statistics and derived hit lookup:
  - The dashboard no longer renders the `临码派生统计` block.
  - Frontend adjacent-derived fetch functions now no-op.
  - `/api/adjacent-derived-stats` and `/api/adjacent-derived-hits` return HTTP 410 and do not run the old calculations.
- Verification performed:
  - `python -m py_compile .\keno_dashboard_server.py` passed.
  - `node --check .\web\app.js` passed.
  - Backend restarted: current PID `92852`.
  - `/api/predictions?game=poland_keno_20_70&panel=d` returned 8 D tickets: 4 two-code and 4 three-code.
  - `/api/frequency-observation?game=poland_keno_20_70&pickCount=4&days=3&top=3&minDailyHits=1` returned 3 fixed 4-code candidates quickly.
  - `/api/current-staking-backtest?game=poland_keno_20_70&source=d&slot=p3_all` returned selection `D计划 / 全部3码`.
  - Both adjacent-derived endpoints returned HTTP 410.
  - Playwright UI smoke passed: D tab rendered 8 cards, current backtest switched to D, 4-code frequency observation rendered, and page overflow was 0.

Current Telegram staking and cumulative rules:

- Push staking profile now defaults to `conservative` / `保守`.
- Local ignored config `data/telegram_bot_config.local.json` was updated from `standard` to `conservative`; the bot token remains local only and must not be printed or committed.
- Conservative fixed ladder is shared with the website 投倍回测 rules: base `1`, every `30` misses add `1`, max stake `5`.
- Telegram no longer uses bot `enabledAt` as the cumulative start for result stats.
- For each game/result, the cumulative window starts at that lottery's first valid draw of the current lottery-local day, then displays that start time in UTC+8.
- Result message now shows:
  - `开奖时间`: today's first draw time converted to UTC+8.
  - `当前开奖`: the current settled draw time converted to UTC+8.
  - `投注档位`: current staking profile and fixed ladder parameters.
- `候选独立累计` is calculated per current candidate slot (`2码1`, `2码2`, `3码1`, `3码2`) over actual history rows from the first daily draw through the current draw.
- Each candidate is simulated independently with the same fixed ladder logic as `/api/staking-backtest`; stake/profit no longer uses the record's full-history `currentMiss`.
- Plan messages also use the daily window to compute the next stake and show UTC+8 target draw time.

Verification performed:

- `python -m py_compile .\keno_dashboard_server.py` passed.
- Local preview for enabled game `poland_keno_20_70` showed window `2026-06-10 12:34 UTC+8 -> 2026-06-10 18:34 UTC+8`, profile `conservative`, and independent candidate totals.
- Internal `/api/staking-backtest` payload was checked on the same time window; matching candidate/ticket math used the same `rounds`, `totalStake`, `totalPayout`, and `netProfit` fields.
- Backend restarted after the fix: current PID `73104`.
- `/api/telegram` reports `stakingProfile=conservative`, `tokenConfigured=true`, and `lastErrors=[]`.

Follow-up on 2026-06-10:

- Telegram plan/result message layout was cleaned up from long `|`-joined rows into per-candidate blocks.
- Result message `开奖号码` now includes the UTC+8 draw time in the same line, for example `18:54 开奖号码：...`.
- `本期结算` now shows each candidate as:
  - candidate + slot + numbers
  - result/stake/profit
  - matched numbers
- `候选独立累计` now shows each candidate as:
  - candidate + slot + numbers
  - periods/wins/stake/payout
  - profit/ROI
- Plan message uses the same block layout for candidate, odds, stake, current daily miss streak, and decision.
- `python -m py_compile .\keno_dashboard_server.py` passed after the layout change.
- Local preview confirmed the result line format: `18:54 开奖号码：9 15 16 ...`.
- Backend restarted again after the layout change: current PID `9340`.
- `/api/telegram` still reports `stakingProfile=conservative`, `tokenConfigured=true`, and `lastErrors=[]`.

Follow-up on 2026-06-10 evening:

- User compared Telegram Poland result with the website 投倍回测 panel and saw different profit values.
- Diagnosis:
  - Website screenshot window was `12:34-18:57`, actual replay rows ended at `18:54`, total `96` periods.
  - Telegram result message was for `当前开奖 18:58`, total `97` periods, and explicitly includes the current draw.
  - Same-ticket differences matched exactly one extra losing stake:
    - `13-42`: website conservative `投入108 / 中奖88 / 利润-20`; Telegram `累投109 / 中奖88 / 利润-21`.
    - `29-33-63`: website conservative `投入119 / 中奖160 / 利润+41`; Telegram `累投120 / 中奖160 / 利润+40`.
  - Some rows also differed because the website source is `当前C计划` after refresh, while Telegram result is the candidate batch that was pushed for that settled draw.
- Result message now states `范围：含当前开奖` and `候选：当期推送` to make this comparison boundary visible.
- Telegram push messages were changed from Markdown code blocks to HTML inline code:
  - Copyable fields are wrapped with `<code>...</code>`.
  - No large grey Markdown code blocks for plan/result messages.
  - Betting and draw URLs are removed from the body and sent as inline buttons: `投注地址` and `开奖地址`.
- Bot menu wording was updated:
  - Main menu now has `编辑按钮链接`.
  - Message settings now exposes `修改投注按钮` and `修改开奖按钮`.
- `python -m py_compile .\keno_dashboard_server.py` passed after stopping the old backend process.
- Backend restarted after the HTML/button format change: current PID `9636`.
- `/api/telegram` reports `stakingProfile=conservative`, `tokenConfigured=true`, and `lastErrors=[]`.

## Latest Sync Incident

On 2026-06-09 afternoon, the PC had been off for the morning and draw history stopped near `2026-06-08T21:00Z`.

Diagnosis:

- Local backend was running, but `/api/prediction-auto` reported all 4 games failing with `[WinError 10054]`.
- Direct local network checks showed normal internet access and normal access to `lotodate.ro`.
- BC.Game domains (`bcgame.nz`, `bc.game`, mirrors tested) could not be reached from this machine.

Fix applied:

- `refresh_history()` now continues to official supplements if BC.Game fetch fails.
- If both BC.Game and the official supplement fail, the game still reports an error.
- Auto sync now uses short BC failure settings by default: `timeout=6`, `retries=0`, `retrySleep=0.5`, so it quickly falls back to official supplements instead of waiting minutes.
- User found an accessible BC mirror: `https://playglobal5.com`.
- `fetch_bc_keno_history.py` now uses configurable BC API base URLs via `BCGAME_API_BASE_URLS`; default order is `https://playglobal5.com`, then `https://bcgame.nz`.

Current verification:

- Current backend after latest restart: `python PID 88180`.
- `playglobal5.com` was verified against all 4 lottery IDs and returned `code=0` history rows.
- A manual `/api/refresh-all` completed successfully: 4 games, 0 errors.
- `/api/prediction-auto` is running and completed a 4-game cycle with `0` errors.
- Latest synced valid draw times after the mirror update:
  - Spain: `2026-06-09T09:06:00Z`
  - Poland: `2026-06-09T09:10:00Z`
  - Russia: `2026-06-09T08:52:30Z` as latest valid draw; newer BC rows may include cancelled periods.
  - Italy: `2026-06-09T09:00:00Z`

## User Priorities

The user needs practical betting decisions quickly. The available decision window can be about 120 seconds.

Communication style:

- Use Chinese.
- Be direct and practical.
- Give operational conclusions first.
- Avoid long audit explanations unless the user asks.
- Do not ask the user to interpret complex tables.
- Do not expand dashboard/report UI unless it directly improves prediction output, speed, or decision clarity.
- Do not discuss retired branches unless the user explicitly asks.

Preferred decision words:

```text
跟
不跟
只观察
降成本
不改规则
```

## Active Prediction State

Only these user-facing prediction plans are active:

- `A计划`
- `B计划`
- `C计划` (`panel=m`, former `倍投候选`)

Current stance:

- `A计划` and `B计划` remain active as source/base references.
- `旧C/D/E/F/G` are retired from active prediction and auto tracking.
- `C计划` (`panel=m`) is the current practical low-group martingale observation direction.
- The user wants low input: no more than 5 groups, preferably exactly 2 groups of 2-number tickets plus 2 groups of 3-number tickets.
- `C回测` has also been removed from the active UI/API path. The top navigation no longer exposes it, and `/api/cde-kill-backtest` returns HTTP 410. Do not use it for current decisions unless the user explicitly asks to resurrect it.
- `策略审计` now audits only the active A/B/C chain. Its backend payload no longer exposes old C kill panels, old C wrong-kill detail, or C/D tracking summaries; it reports A/B/M implementation-key forward tickets and tracking only. Strategy audit is available for all four active games.

## A Plan

Current A method is the base heuristic:

```text
当前遗漏 + 近240期动量偏差 + 全样本偏差 + 连号遗漏 z-score 的启发式排序
```

Relevant constant:

```text
PREDICTION_RECENT_WINDOW = 240
```

The user asked whether 240 periods is too few. Current conclusion:

```text
240 is not obviously the main problem.
A's weakness is more likely signal quality than window size.
Do not try to rescue A merely by changing 240 to a larger number.
If windows are tested, compare 120/240/480/720/1000 only by downstream B performance.
```

## B Plan

Important current-code finding:

```text
B is not a separate predictive model.
B first generates A tickets, collects A main numbers, excludes those numbers,
then reruns the same heuristic ticket generation over the remaining pool.
```

So B is not pure random, but its distinct signal is mainly:

```text
exclude A candidate numbers
```

After that exclusion, B appears to reuse the same scoring family as A rather than applying a fundamentally independent probability model.

Primary question to keep investigating:

```text
Is B useful because excluding weak A candidates creates a real edge,
or is B's recent success just short-term noise?
```

## B Adjacent-Derived Opportunity

The strongest observed opportunity is:

```text
B official 2-number ticket
-> local adjacent 4-number expansion
-> "2球局部四码全中"
```

This is currently derived from settled tracking records. It is not yet a clean formal low-ticket prediction plan.

Key distinction:

```text
Do not expand all loose B numbers into arbitrary pairs.
That creates too many candidates and does not match the observed signal.
```

Candidate future direction:

```text
Use only B official 2-number main tickets as anchors.
Generate local adjacent 4-number tickets from those anchors.
Rank/filter them.
Output only 2-4 tickets per draw.
Track source-anchor hit and derived-ticket hit separately.
```

Important risk:

```text
The source 2-number anchor must hit first.
Then the local 4-number expansion must also hit.
These two layers must be measured separately.
```

## C Plan

C can remain as supporting observation. Do not make C the main line unless current live tracking clearly improves.

## Tracking

Tracking should focus on active A/B/C records and any future B-derived formal plan.

For judging follow/buy tracking:

```text
<100 tickets: too little
100-300: observe only
300+: initial judgment
600+: more trustworthy
```

Rule-change thresholds:

```text
30 periods: abnormal signal only
60 periods: observe only
180 periods: eligible for small adjustment if stable
360 periods: eligible for formal rule change if stable
```

## External Audit Package

The user is asking an external reviewer to audit code and strategy direction.

Prepared folder:

```text
F:\我的开发\CPGAME\claude
```

Files prepared there:

- `EXTERNAL_AUDIT_REQUEST.md`
- `CURRENT_CONTEXT.md`
- `keno_dashboard_server.py`
- `web_app.js`
- `web_index.html`
- `web_styles.css`

The external audit question:

```text
A is weak.
B excludes A and then reruns similar scoring.
Does B have any real probability-improving mechanism beyond excluding A?
Can B's 2-number tickets be used as anchors for a low-ticket adjacent 4-number plan?
What filters can reduce derived tickets to 2-4 without destroying the signal?
```

## Current Engineering Notes

Recent completed work:

- User-facing prediction navigation exposes A/B/C/D.
- Auto prediction/tracking flow generates active A/B/C/D records.
- Tracking DB work optimized active tracking paths with SQLite columns/indexes and aggregation.
- Prediction generation has shared ticket stats indexing via bitmasks.

## 2026-06-06 D Plan Update

User decision:

```text
Do not continue with 1-number experiments.
Create D as a direct 4-number experimental rule pool.
Different rules can output multiple groups.
Track by rule, observe, then keep the best rules and remove bad rules.
```

Implemented D plan:

```text
D plan = A/B 2-number anchors + C 4-number structures -> derived 4-number tickets.
No 1-number output.
Panel D is active again.
Old retired D semantics are not reused.
```

Backend changes:

- `PREDICTION_PANEL_D` label is now `D计划`.
- D tracking method version is now `strategy-ticket-d-derived-four-v1`.
- D was removed from `PREDICTION_RETIRED_PANELS`.
- D was added to `PREDICTION_ACTIVE_TRACKING_PANELS`.
- D output cap is `48` tickets per generation.
- Per-rule cap is `8` tickets to avoid one rule dominating the pool.
- Old D records stay separated because the new method version is different.
- Tracking DB queries default to current D method only, so old D cancelled/history records do not mix into new D totals.
- Strategy audit context no longer computes old D by default; D is included in tracking summary only, not high-cost per-round D backplay.

D rule families currently generated:

```text
AB pair rules:
- AB ±1..±9 outer expansion
- AB +1..+9 / -1..-9 shift expansion
- AB same-tail +10 / -10 / +20 / -20
- AB mirror
- AB midpoint / interval split

C structure rules:
- C original 4-number structure
- C whole-ticket +1 / -1 / +10 / -10
- C mirror
```

Important fields saved for later pruning:

```text
structureType
structureLabel
derivedRule
sourcePanel
sourcePanels
sourceCoreTicketLabels
coreNumbers
companionNumbers
```

Frontend changes:

- D tab restored as `D计划`.
- D routes through the normal prediction view.
- D does not show the old kill-number panel because it is no longer a kill plan.
- D tickets show rule label, core numbers, and derived numbers in the existing ticket cards/tracking rows.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
```

Runtime/API checks completed:

```text
GET /api/predictions?game=spain_l_express_20_70&panel=d
-> panel d, label D计划, 48 tickets, pickCounts = 4
-> sample structureType d_c_original_cohit_free

GET /api/predictions?game=poland_keno_20_70&panel=d
-> panel d, label D计划, 48 tickets, pickCounts = 4

GET /api/prediction-tracking?game=spain_l_express_20_70&panel=d&status=all&page=1&pageSize=10&autoSync=0
-> total 48, methodVersion strategy-ticket-d-derived-four-v1, groupCount 20

GET /api/strategy-signal-audit?game=spain_l_express_20_70&window=30&trainWindow=120
-> ok, tracking panels c,d
```

Current local backend:

```text
http://127.0.0.1:8787
python PID observed after restart: 71468
```

Decision status:

```text
D is observation only.
Do not mark D as follow/buy yet.
Use it to accumulate rule-level evidence.
```

Suggested D pruning thresholds:

```text
<30 settled per rule: sample too small
30-100 settled per rule: observe direction only
100+ settled per rule: weak rules can be removed if clearly below theory/ROI
300+ settled per rule: candidate rules can be kept/promoted if they beat theory and ROI is not poor
```

## 2026-06-08 D Rule Pruning

User asked:

```text
Review D and kick out the derived garbage rules that do not hit.
```

Review basis:

```text
Source: data/prediction_tracking.sqlite3
Panel: d
Method: strategy-ticket-d-derived-four-v1
Grouping: game_key + structureType + structureLabel
```

Pruning rule used:

```text
settled >= 300 and won = 0 -> remove
settled >= 300 and ROI < -15% and hitRate < theory -> remove
settled >= 100 and ROI < -35% and hitRate < theory -> remove
```

Important finding:

```text
D overall was not garbage.
Spain D had 13,824 settled / 97 won / hitRate about 0.702% / ROI about +5.25%.
The problem was specific bad derived rules inside D.
Do not delete all D.
```

Implemented:

- Added `PREDICTION_PANEL_D_DISABLED_STRUCTURE_TYPES_BY_GAME`.
- D now filters disabled `structureType` values during candidate generation.
- Pruning is per game, not global, because the same derived rule can be bad in one game and useful in another.
- Kept D tracking method version as `strategy-ticket-d-derived-four-v1` so existing pending records continue to settle.
- D method text now reports how many low-hit rules were removed for the current game.

Disabled counts:

```text
Spain: 15 D structure types removed
Poland: 24 D structure types removed
Russia: 6 D structure types removed
Italy: 1 D structure type removed
```

Examples of removed rules:

```text
Spain:
- d_ab_pm_1
- d_ab_pm_3
- d_ab_shift_plus_1
- d_ab_shift_plus_3
- d_ab_shift_minus_8
- d_ab_mirror
- d_c_original_offset_d

Poland:
- d_ab_shift_minus_8
- d_ab_shift_plus_4
- d_ab_shift_plus_5
- d_c_original_band_5_10
- d_c_original_cohit_free
- d_c_shift_plus_10_cohit_free

Russia:
- d_ab_shift_minus_1
- d_ab_shift_minus_3
- d_ab_shift_plus_3
- d_c_shift_minus_1_cohit_free
- d_c_shift_plus_1_cohit_free

Italy:
- d_c_shift_minus_1_cohit_free
```

Rules that should not be globally deleted yet:

```text
Some AB +/- and C mirror/cohit rules are bad in one game but strong in another.
Keep the pruning list per game unless a rule becomes consistently bad across all games.
```

Post-prune API verification:

```text
GET /api/predictions?game=spain_l_express_20_70&panel=d
-> 48 tickets, pickCounts = 4, disabledCount = 15, no disabled structure leaked

GET /api/predictions?game=poland_keno_20_70&panel=d
-> 48 tickets, pickCounts = 4, disabledCount = 24, no disabled structure leaked

GET /api/predictions?game=russia_rapido_8_20&panel=d
-> 48 tickets, pickCounts = 4, disabledCount = 6, no disabled structure leaked

GET /api/predictions?game=italy_win_for_life_10_20&panel=d
-> 48 tickets, pickCounts = 4, disabledCount = 1, no disabled structure leaked
```

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
```

Current local backend after restart:

```text
http://127.0.0.1:8787
python PID observed after restart: 71468
```

Verification from the latest completed code work:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
```

## E Plan Added: D-Profit Five-Number Observation Pool

Implemented E as a new active plan:

```text
E plan = currently profitable D rules -> D-to-D five-number combinations
methodVersion = strategy-ticket-e-dprofit-five-v1
panelLabel = E计划
```

Important behavior:

- E is active again; F/G remain retired.
- E uses D plan tickets only. The base 4-number ticket comes from a profitable D `structureType`.
- The fifth number also comes from another profitable D ticket, not from a standalone hot-number or adjacent-number rule.
- Pairing priority is D ticket overlap:
  - overlap 3: strongest source, one different D number becomes the fifth number.
  - overlap 2: allowed as a lower-priority fallback when it scores well.
- E records exact source metadata for later pruning:
  - `sourceStructureType`
  - `extensionStructureType`
  - `overlapNumbers`
  - `extensionNumbers`
  - `derivedRule`
- E groups are intentionally granular by source rule pair:
  - `structureType = e_d_overlap{2|3}_{baseDRule}__{extensionDRule}`
  - This makes it possible to delete bad E source pairs later instead of deleting the whole plan.

Current caps:

```text
PREDICTION_PANEL_E_TOP_COUNT = 32
PREDICTION_PANEL_E_D_SOURCE_LIMIT = 48
PREDICTION_PANEL_E_DERIVED_PREFILTER_LIMIT = 240
PREDICTION_PANEL_E_RULE_LIMIT = 4
PREDICTION_PANEL_E_SOURCE_MIN_SETTLED = 30
```

Current profitable D rule source selection:

- First choice: read current D tracking DB summaries and include D `structureType` where:
  - settled >= 30
  - profit > 0
  - hit rate >= theoretical hit rate
- Fallback: use the latest manually reviewed profitable D source snapshot if the DB read fails or has no qualifying rules.
- E still subtracts the per-game disabled D rules, so pruned D garbage rules cannot leak into E.

Backend/API verification:

```text
GET /api/predictions?game=spain_l_express_20_70&panel=e&autoSync=0
-> 32 tickets, pickCounts = 5, sourceRules = 26

GET /api/predictions?game=poland_keno_20_70&panel=e&autoSync=0
-> 32 tickets, pickCounts = 5, sourceRules = 20

GET /api/predictions?game=russia_rapido_8_20&panel=e&autoSync=0
-> 32 tickets, pickCounts = 5, sourceRules = 18

GET /api/predictions?game=italy_win_for_life_10_20&panel=e&autoSync=0
-> 21 tickets, pickCounts = 5, sourceRules = 5
```

Disabled D rule leak check:

```text
Spain:  32 E tickets, disabledLeaks = 0, allFive = True
Poland: 32 E tickets, disabledLeaks = 0, allFive = True
Russia: 32 E tickets, disabledLeaks = 0, allFive = True
Italy:  21 E tickets, disabledLeaks = 0, allFive = True
```

Tracking verification:

```text
GET /api/prediction-tracking?game=spain_l_express_20_70&panel=e&status=all&page=1&pageSize=5&autoSync=0
-> panel = e
-> total = 32
-> pending = 32
-> methodVersion = strategy-ticket-e-dprofit-five-v1
```

Frontend changes:

- Added `predictionE` tab labeled `E计划`.
- `predictionE` routes to `panel=e`.
- E loading text says it is reading D profitable rules and generating five-number observation tickets.
- E no longer shows the old CD kill panel.

Important operating decision:

```text
E is observation only for now.
Do not treat E as followable until its own 5-number tracking ROI and hit rate are reviewed.
If E performs poorly, the conclusion is that D four-number signals cannot be naively upgraded to five-number tickets.
Then prune by E source pair, not by emotion.
```

Runtime data files may be dirty from tracking and history refresh. Do not revert generated/runtime data unless the user explicitly asks.

Likely dirty runtime files:

- `data/*.csv`
- `data/prediction_tracking.sqlite3`
- `data/prediction_auto_config.json`

## Next Practical Steps

1. Let D accumulate rule-level tracking records.
2. Review D tracking groups by `structureType` / `structureLabel`.
3. Prune rules that are below theory and negative ROI after enough settled samples.
4. Keep rules that remain above theory with acceptable ROI and stable Wilson interval.
5. Only after pruning, consider making a smaller followable D subset.
6. Keep first-screen output practical: target time, remaining seconds, ticket list, follow/not-follow conclusion.

## 2026-06-08 Direction Shift: Retire C/D/E, Add M Low-Group Candidates

User decision:

- Stop the C/D/E direction for active prediction work.
- E has no practical value in the new direction and is retired.
- Do not allow prediction output to exceed 5 groups.
- Preferred output is only:
  - 2 groups of 2-number tickets
  - 2 groups of 3-number tickets
- The intent is to move away from 4/5-number low-hit-rate tickets and observe lower-group martingale candidates.

Implementation:

- Added `PREDICTION_PANEL_M = "m"` with method version `strategy-ticket-m-lowgroup-v1`; user-facing label is now `C计划`.
- Active tracking panels are now only:
  - `A计划`
  - `B计划`
  - `C计划` (`panel=m`)
- Retired panels are now:
  - `旧C计划`
  - `D计划`
  - `E计划`
  - `旧F计划`
  - `旧G计划`
- Retired panels no longer generate new predictions and no longer run in automatic tracking.
- Historical C/D/E/F/G tracking evidence is not deleted; pending retired records are cancelled as retired-plan records.

M plan generation:

- Main-ball tickets only.
- Generates at most 4 tickets per draw:
  - max 2 tickets with `pickCount = 2`
  - max 2 tickets with `pickCount = 3`
- Candidate sources:
  - A/B source tickets
  - A/B merged source pool
  - composite score pool
  - recent-hot pool
  - current-miss pool
  - consecutive-run shape pool
- Selection score uses:
  - recent hit rate vs break-even line
  - full-sample hit rate vs theory
  - recent Wilson lower-bound edge
  - lower historical max-miss risk
  - lower current-miss risk
  - source/heuristic score
- C计划 ticket cards expose `auditSourceLabel`, `auditScore`, `followDecision`, and `stakingSimulation`.
- `stakingSimulation` replays the current fixed candidate ticket over the latest 1000 valid draws, starts from 1 yuan, scans "double after 1-30 consecutive misses", caps the multiplier at 64x, and returns flat-buy baseline, best double policy, total stake, total payout, net profit, ROI, max stake, max drawdown, current miss streak, and next stake.

Frontend:

- Removed C/D/E prediction tabs.
- Added `predictionM` tab labeled `C计划`.
- A/B/C are the only active prediction views; C still uses backend `panel=m`.
- C backtest and strategy-audit pages remain as read-only historical audit tools.

Verification already run:

```text
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
```

Verified after server restart:

```text
GET /api/predictions?game=spain_l_express_20_70&panel=m&autoSync=0
-> panel = m
-> ticket count = 4
-> pickCounts = 2:2, 3:2
-> tickets = 4-37 | 17-58 | 11-37-43 | 4-37-58

GET /api/predictions?game=spain_l_express_20_70&panel=e&autoSync=0
-> 400 retired-plan response
```

All four games were checked after restart:

```text
Spain M:  4 tickets, pickCounts 2:2 / 3:2
Poland M: 4 tickets, pickCounts 2:2 / 3:2
Russia M: 4 tickets, pickCounts 2:2 / 3:2
Italy M:  4 tickets, pickCounts 2:2 / 3:2
```

C/D/E generation was checked and all now return retired-plan errors:

```text
panel=c -> 400
panel=d -> 400
panel=e -> 400
```

Frontend verification:

- Top prediction tabs are now `A计划`, `B计划`, `C计划`.
- No C/D/E prediction tabs remain.
- `C计划` page renders 4 tickets.
- Tracking groups show `C计划 2码低组候选` and `C计划 3码低组候选` for new records; older records may still show the old M labels.
- Only browser console error was `/favicon.ico` 404, unrelated.

## 2026-06-08 Window Restart Note

User is restarting the conversation window and wants to observe C计划 (`panel=m`) for one night.

Important next-window stance:

- Do not revive old C/D/E unless explicitly requested.
- Do not expand C计划 above 4 tickets.
- Observe C计划 by settled tracking groups:
  - `C计划 2码低组候选`
  - `C计划 3码低组候选`
- First decision after overnight data:
  - keep the group whose hit rate/ROI is less bad and whose miss streak is manageable;
  - mark the weaker group as `只观察` or retire it;
  - do not add more groups to compensate for losses.

Current server:

```text
http://127.0.0.1:8787
python PID 88180
```

## 2026-06-09 C Plan Rename And Staking Simulation

User request:

- Rename user-facing `倍投候选` to `C计划`.
- Keep backend implementation key as `panel=m` to avoid migrating tracking/history data.
- Add a staking simulation for any current C计划 candidate ticket.

Implemented:

- Backend `PREDICTION_PANEL_M` label is now `C计划`; old `PREDICTION_PANEL_C` label is now `旧C计划`.
- Top nav `predictionM` tab now displays `C计划`.
- Current C计划 tickets are labeled `C计划 2码低组候选` / `C计划 3码低组候选`.
- Strategy audit user-facing text now says A/B/C计划, while still using implementation key `m` internally.
- Each current C计划 ticket now includes `stakingSimulation`.

Staking simulation rules:

- Uses the current fixed candidate ticket, not forward-regenerated historical tickets.
- Replays the latest 1000 valid draws from old to new.
- Base stake is 1 yuan.
- Flat-buy baseline is always computed.
- Double policies scan `连挂1期后加倍` through `连挂30期后加倍`.
- Winning resets the next stake to 1 yuan.
- Multiplier is capped at 64x.
- Best policy ranks by net profit first, then ROI, lower max drawdown, lower total stake, lower max stake.
- Returned fields include best policy, best double policy, flat baseline, total stake, total payout, net profit, ROI, max stake, max drawdown, current miss streak, next stake, and first double round.

Verification after restart:

```text
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js

GET /api/predictions?game=spain_l_express_20_70&panel=m
panelLabel = C计划
ticket count = 4
all 4 tickets have stakingSimulation.enabled = true
backend PID = 88180
```

Most recent Spain M sample at verification time:

```text
2码: 4-37
2码: 17-58
3码: 11-37-43
3码: 4-37-58
```

Verification commands run:

```text
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
Playwright page check for M tab and ticket rendering
```

## 2026-06-09 Fixed Ladder Staking Backtest Page

User decision:

- Do not put flexible staking/backtest controls inside C计划 cards.
- Keep the split clear:
  - C计划 only outputs candidate tickets.
  - A separate `倍投回测` page validates fixed staking rules.

Implemented:

- Added standalone frontend tab/page:
  - view key: `stakingBacktest`
  - nav label: `倍投回测`
  - normal flat page, not a modal/tool overlay.
- Default source is `当前C计划`, which reads backend `panel=m` and keeps the existing C计划 cap of 4 tickets.
- Added optional `手动号码` source for fixed ticket replay.
- Added adjustable fixed profiles:
  - 平买
  - 保守
  - 标准
  - 激进
  - 自定义
- Conservative/standard/aggressive/custom controls include fixed miss-step interval and max single stake. All profiles share base stake and per-step stake unless custom step stake is sent separately.

Backend:

- New endpoint:

```text
GET /api/staking-backtest
```

Important query params:

```text
game=spain_l_express_20_70
source=c_plan|manual
window=300|500|1000|all
numbers=4-37,11-37-43
baseStake=1
stepStake=1
conservativeStepMisses=30
conservativeMaxStake=5
standardStepMisses=20
standardMaxStake=8
aggressiveStepMisses=10
aggressiveMaxStake=12
customStepMisses=20
customMaxStake=8
```

Fixed ladder rule:

- Ticket numbers stay fixed through the replay window.
- Each historical draw is replayed from old to new.
- If the ticket hits, next stake resets to base stake.
- If the ticket misses, current miss streak increases.
- Stake for the next draw is:
  - `baseStake + floor(currentMissStreak / stepMisses) * stepStake`
  - capped at `maxStake`
- Flat profile always stays at base stake.

Returned per ticket:

- odds, theoretical hit rate, recent/full historical hit rates
- current miss and historical max miss
- policy results for flat/conservative/standard/aggressive/custom
- total stake, payout, net profit, ROI, max drawdown, max stake used, next stake
- verdict:
  - `重点观察`
  - `只观察`
  - `不跟`

Verification:

```text
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
```

API checks after backend restart:

```text
GET /api/staking-backtest?game=spain_l_express_20_70&source=c_plan&window=1000
-> ok=true, source=c_plan, tickets=4, rows=1000, focus=3, watch=0, noFollow=1

GET /api/staking-backtest?game=poland_keno_20_70&source=c_plan&window=1000
-> ok=true, source=c_plan, tickets=4, rows=1000, focus=2, watch=0, noFollow=2

GET /api/staking-backtest?game=russia_rapido_8_20&source=c_plan&window=1000
-> ok=true, source=c_plan, tickets=4, rows=1000, focus=2, watch=0, noFollow=2

GET /api/staking-backtest?game=italy_win_for_life_10_20&source=c_plan&window=1000
-> ok=true, source=c_plan, tickets=4, rows=1000, focus=3, watch=0, noFollow=1

GET /api/staking-backtest?game=spain_l_express_20_70&source=manual&numbers=4-37,11-37-43&window=300
-> ok=true, source=manual, tickets=2, rows=300
```

Frontend smoke:

```text
node .\tmp\verify_staking_backtest_ui.mjs
-> ok=true, C计划 rows=4, manual rows=2
```

Current backend:

```text
http://127.0.0.1:8787
python PID 94760
```

## 2026-06-10 Staking Backtest Time Segment Audit

User request:

- Add time-range statistics to `倍投回测`.
- Allow selecting start/end time so the user can compare which time period performs better.
- Add a manual backtest period input, for example input `100` to replay exactly the latest 100 draws.

Implemented:

- Extended `GET /api/staking-backtest` with time filters:
  - `startDateTime`
  - `endDateTime`
  - `dailyStart`
  - `dailyEnd`
  - `timeZone`
  - `sliceHours`
- Added frontend controls on `倍投回测`:
  - 回测窗口 select: 300 / 500 / 1000 / 全部
  - 自定义期数 input: overrides the select when filled, supports values like `100`
  - 开始日期时间 / 结束日期时间
  - 每日开始 / 每日结束
  - 时区: 北京时间 / UTC
  - 切片粒度: 1小时 / 2小时 / 4小时 / 6小时
- Added `时段表现排行` table under the main result table.

Time-filter behavior:

- Absolute date range is applied first.
- Then the latest N rows are selected from that date-filtered set.
- The main ticket replay optionally applies the daily time window.
- Fixed time-segment ranking uses the same date/window base and splits it into fixed daily slices.
- Daily time window supports normal ranges and cross-midnight ranges.

Segment ranking:

- Uses the same fixed-ladder policy simulator as the main table.
- Aggregates all visible tickets by policy:
  - 平买
  - 保守
  - 标准
  - 激进
  - 自定义
- Default sort is by standard-policy net profit, with 300+ sample slices prioritized.
- Segment verdict safeguards:
  - fewer than 100 rows: `样本不足`
  - 100-299 rows: `只观察`
  - 300+ rows can become `重点观察` only if flat is not losing and a fixed profile is positive.

Verification:

```text
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
```

API checks:

```text
GET /api/staking-backtest?game=spain_l_express_20_70&source=c_plan&window=100&sliceHours=2
-> ok=true, tickets=4, rows=100, requested=100, segments=12

GET /api/staking-backtest?game=spain_l_express_20_70&source=c_plan&window=1000&dailyStart=20:00&dailyEnd=23:59&sliceHours=4
-> ok=true, tickets=4, rows=240, segmentSourceRows=1000, segments=6

GET /api/staking-backtest?game=spain_l_express_20_70&source=manual&numbers=4-37,11-37-43&window=500&startDateTime=2026-06-09T00:00&endDateTime=2026-06-10T23:59&sliceHours=6
-> ok=true, source=manual, tickets=2, rows=262, dateFilteredRows=262, segments=4
```

Frontend smoke:

```text
node .\tmp\verify_staking_backtest_ui.mjs
-> ok=true, C计划 rows=4, default segment rows=12, manual rows=2, manual segment rows=4
```

Current backend:

```text
http://127.0.0.1:8787
python PID 90720
```

## 2026-06-10 Telegram Bot / Channel Notification

User request:

- Connect CPGAME to Telegram bot/channel notifications.
- First support Spain, with switches for one game or all games.
- Send C计划 plans and suggested staking multiple.
- After settlement, send won/lost result, draw numbers, profit/loss, betting invite link, and realtime draw link.
- Pin profit milestone messages at every +50 profit step.
- Send and pin the daily profit summary near the end of the day.
- Correct channel username is `@Keno100x`.

Implemented:

- Added local Telegram config/state files:
  - `data/telegram_bot_config.local.json`
  - `data/telegram_bot_state.local.json`
- Added both files to `.gitignore`.
- Added `GET /api/telegram`:
  - returns public Telegram config/status
  - never returns `botToken`
  - reports `tokenConfigured`
- Added `POST /api/telegram` actions:
  - `save`: save switches/channel/invite/draw/game selection
  - `test`: send a test message to the configured channel
  - `notifynow`: immediately check enabled games and send pending plan/result notifications
- Added Telegram notification hook inside `run_prediction_auto_once()`.
- Telegram currently sends only the active user-facing `C计划` records, which are backend `panel=m`.
- Added Telegram bot polling worker using `getUpdates`, because the local service has no public webhook URL.
- Added bot commands:
  - `/menu`: open control menu
  - `/status`: view current push status
- Added inline keyboard controls:
  - private bot chat: channel total switch, game result switches, message settings, test send, notify now
  - channel `/menu`: game result switches and total push switch
- Inline callback changes are restricted to `adminIds`.
- Channel message settings support editing channel id, invite link, and per-game draw links from the private bot menu.
- Default config:
  - `enabled=false`
  - `channelChatId=@Keno100x`
  - `adminIds=["988670752"]`
  - `inviteLink=https://playglobal4.com/i-23u4bw0u7-n/`
  - `drawLink=""`
  - `drawLinksByGame`:
    - Spain L'Express: `https://lotodate.ro/Extrageri/5-l-express-spania-20-70`
    - Poland Keno: `https://lotodate.ro/Extrageri/4-keno-polonia-20-70`
    - Italy Win for Life Classico: `https://lotodate.ro/Extrageri/11-win-for-life-classico-italia-10-20`
    - Russia Rapido has no matching page on `lotodate.ro/Loterii`; messages do not attach a wrong fallback URL
  - Telegram messages disable web page previews by default
  - `allGames=false`
  - Spain enabled; Poland/Russia/Italy disabled
  - standard staking ladder: base 1, +1 every 20 misses, cap 8
- Token loading:
  - preferred: `TELEGRAM_BOT_TOKEN` environment variable
  - fallback: ignored local config key `botToken`
  - token is not committed and must not be copied into this handoff file
  - current ignored local config has a token configured; do not print or commit the file content

Frontend:

- Added Telegram panel under the sync log.
- Controls:
  - total enable switch
  - all-games switch
  - channel input
  - betting/invite link
  - realtime draw link
  - per-game checkboxes
  - Save / Test / Notify Now buttons
- The page shows token status only as configured/missing, never the token value.

Verification:

```text
python -m py_compile .\keno_dashboard_server.py
-> ok

node --check .\web\app.js
-> ok

GET /api/telegram
-> ok=true, channelChatId=@Keno100x, enabled=false, tokenConfigured=true,
   drawLink empty, per-game drawLinksByGame present, Spain enabled by default,
   other games disabled, no botToken in response

POST /api/telegram action=save with enabled=false and Spain only
-> ok=true, config file written locally, no botToken in response

POST /api/telegram action=test
-> ok=true, messageId=122, message uses Spain-specific LotoDate draw page and no link preview

POST /api/telegram action=setupmenu
-> ok=true, result=true

POST /api/telegram action=sendmenu
-> ok=true, messageId=88 sent to admin private chat

POST /api/telegram action=poll
-> ok=true, updates=0, handled=0, errors=[]

node .\tmp\verify_telegram_ui.mjs
-> ok=true, channel=@Keno100x, game toggles=4
```

Current backend:

```text
http://127.0.0.1:8787
python PID 91432
```

### 2026-06-10 Telegram Message Throttle / Markdown Format Fix

User correction:

- Do not send many Telegram messages at once.
- Normal push should be one C计划 message and one开奖结果 message.
- Message format should be Markdown and easy to copy.
- 投入金额 and 利润 must be cumulative from the Telegram start time, not isolated per draw.

Implemented:

- `telegram_send_recent_results()` now sends only the latest settled target batch.
  - It no longer loops over every settled draw from the last 6 hours.
  - Deduplication key remains `game:targetDrawTimeMs`.
- Plan/result channel messages now use Telegram Markdown.
  - Numbers and links are wrapped in code blocks for copy-friendly display.
  - Link previews remain disabled.
- Result messages now show:
  - current draw numbers
  - current draw settlement details
  - current draw total stake/profit
  - candidate-level cumulative stake/profit/ROI from `enabledAt`
- Candidate cumulative stats are split independently:
  - `候选1 / 2码1`
  - `候选2 / 2码2`
  - `候选3 / 3码1`
  - `候选4 / 3码2`
  - each slot rolls its own periods, stake, profit, and ROI
- Cumulative stake uses the same standard ladder policy as the plan recommendation:
  - base stake
  - step misses
  - step stake
  - max stake
- Cumulative profit is recalculated from each record's computed stake and odds:
  - won: `stake * odds - stake`
  - lost: `-stake`
- Bot menu total switch now writes `enabledAt` when turning push on, matching the frontend save behavior.
- If a local config was already enabled before this fix and lacked `enabledAt`, the loader falls back to the local config file modified time; the current local config has persisted:
  - `enabledAt=2026-06-10T09:53:29.257149+00:00`
- Telegram long-poll read timeouts are ignored instead of being recorded as user-visible errors.

Verification:

```text
python -m py_compile .\keno_dashboard_server.py
-> ok

node --check .\web\app.js
-> ok

POST /api/telegram action=test
-> ok=true, messageId=257, Markdown accepted

GET /api/telegram
-> ok=true, enabled=true, enabledAt present, lastErrors=[]

Local preview of latest Spain result message:
-> candidate cumulative block shows separate lines for 候选1/2/3/4,
   each with independent 期数 / 累投 / 累利 / ROI
```

Current backend:

```text
http://127.0.0.1:8787
python PID 38588
```
