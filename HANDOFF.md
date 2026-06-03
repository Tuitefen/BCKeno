# Session Handoff

Updated: 2026-06-03 Asia/Shanghai

## Start Here

For the next conversation, read only this root file first:

1. `HANDOFF.md`

`README_KENO.md` was deleted because it documented the old Slovakia-only tool. Do not use old root audit files as the new-session entry point.

Then inspect current code only as needed:

1. `keno_dashboard_server.py`
2. `web/app.js`
3. `web/index.html`
4. `web/styles.css`
5. `fetch_bc_keno_history.py`
6. `fetch_italy_winforlife_archive.py`

## Current Server

- URL: `http://127.0.0.1:8787`
- Current process: `python PID 46564`
- Workspace: `F:\我的开发\CPGAME`
- Important backup/audit folder: `F:\我的开发\CPGAME\claude`

If backend code changes, restart PID `46564`. Frontend static files are served from disk and usually do not require restart.

## 2026-06-03 Handoff - Prediction Panel F And CDE/F Backtest

User approved implementing prediction panel F and removing the standalone `派生转换` page/tool.

Implemented backend changes in `keno_dashboard_server.py`:

- Added `PREDICTION_PANEL_F = "f"`.
- Added panel label `预测面板F` and tracking method `strategy-ticket-f-v1`.
- Added panel aliases:
  - `f`
  - `panel_f`
  - `prediction_f`
  - `predictionf`
  - `resonance_cd`
  - `overlap_cd`
- Added `prediction_panel_f_overlap_ticket(...)`.
- F logic intentionally does not use post-draw E wrong-kill numbers.
- F uses only pre-draw available data:
  - C source tickets.
  - D source tickets.
  - E kill pool, equal to unique numbers from C source tickets union D source tickets.
- F ticket rule:
  - Prefer `C source numbers ∩ D source numbers`.
  - If fewer than 4 numbers, fill from E kill pool using stable ranking based on source counts, C/D balance, existing score, and low-number tie break.
  - Generate exactly one 4-number ticket.
- F ticket metadata includes:
  - `panel = "f"`
  - `sourcePanel = "cd_overlap"`
  - `sourcePanels = ["c", "d", "e"]`
  - `structureType = "cd_overlap_fill_four"`
  - `structureLabel = "CD重叠补码四码"`
  - `corePoolNumbers`
  - `fillPoolNumbers`
  - source count maps.
- `prediction_payload()` now supports `panel=f`.
- `prediction_context_tickets()` now returns `fTickets` and `fNumbers`.
- Added `cde_prediction_backtest_panel_result(...)` for prediction-hit style result metrics:
  - `hitNumbers`
  - `hitCount`
  - `missNumbers`
  - `missCount`
  - `pickNumbers`
  - `pickCount`
  - compatibility aliases for older CDE rendering fields.
- `cde_kill_backtest_payload()` now includes panel F:
  - `summaries` contains C, D, E, and F.
  - detail rows include `panels.f`.
  - F summary uses `metricType = "prediction_hit"`.
  - C/D/E remain kill-right/kill-wrong metrics.
  - F is not used in `bestPanel` comparison because its metric is prediction hit count, not wrong-kill count.
- Auto tracking now generates A-F and reports `summaryF` / `trackingTotalF`.

Implemented frontend changes:

- `web/index.html`
  - Added top nav button `预测面板F`.
  - Removed standalone `派生转换` nav/page.
  - CDE table now includes `F 命中`.
  - Detail header changed to `错杀/命中号码`.
- `web/app.js`
  - Added F state and routing under the prediction-panel flow.
  - Added `PREDICTION_PANEL_F = "f"`.
  - Added `predictionF` support in view/panel mapping and refresh/hydration logic.
  - F loading text: `读取C/D重叠号并生成F四码票`.
  - F shows the E candidate/kill pool and C/D source ticket groups.
  - CDE/F backtest rendering:
    - C/D/E columns show wrong/right kill counts.
    - F column shows `中 N 未中 M 4码`.
    - last detail column shows C/D/E wrong-killed numbers and `F中` hit numbers.
    - F summary cards show `平均命中`, `平均未中`, `命中率`, and `0中期数`.
  - Removed standalone adjacent-tool functions and event listeners:
    - `parseAdjacentToolNumbers`
    - `adjacentPairCandidates`
    - `adjacentOuterPairCandidates`
    - `adjacentCrossHaloCandidates`
    - `adjacentFourBallCandidates`
    - `selectedAdjacentToolTypes`
    - `buildAdjacentToolRows`
    - `renderAdjacentTool`
    - `copyAdjacentToolResults`
  - Kept prediction tracking's internal `临码派生统计`.
- `web/styles.css`
  - Removed standalone `.adjacent-tool-*` styles.
  - CDE/F backtest table uses no internal vertical scroll.

CDE/F backtest UI behavior:

- It is a normal full-page view, not a modal.
- It shows 25 detail rows per page.
- Previous/next pagination works.
- Spain and Poland are supported.
- Russia remains disabled for CDE/F.

Verification passed:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node --check .\tmp\verify_prediction_f_and_cdef_ui.mjs
node .\tmp\verify_prediction_f_and_cdef_ui.mjs
rg -n "adjacentTool|#adjacentToolView|data-adjacent-type|renderAdjacentTool|copyAdjacentToolResults|adjacent-tool|派生转换" .\web\app.js .\web\index.html .\web\styles.css
```

The final `rg` returned no matches.

Browser verification summary from `tmp/verify_prediction_f_and_cdef_ui.mjs`:

- Spain F:
  - one 4-number ticket.
  - current sample ticket: `13,32,45,48`.
  - C source tickets: 8.
  - D source tickets: 8.
  - E kill pool visible.
- Poland F:
  - one 4-number ticket.
  - current sample ticket: `1,10,12,53`.
  - C source tickets: 8.
  - D source tickets: 8.
  - E kill pool visible.
- Spain and Poland CDE/F backtest:
  - 4 panel cards.
  - `F 命中` column present.
  - `错杀/命中号码` column present.
  - first page has 25 rows.
  - next page works.
  - table has no internal scroll.
  - no horizontal overflow.
  - no console errors.
- Russia CDE/F tab stays disabled.

Claude audit package for this change:

- Folder: `F:\我的开发\CPGAME\claude\prediction_f_cde_audit_2026-06-03`
- Entry file: `AUDIT_BRIEF.md`
- Important files copied there:
  - `keno_dashboard_server.py`
  - `web\app.js`
  - `web\index.html`
  - `web\styles.css`
  - `tmp\verify_prediction_f_and_cdef_ui.mjs`
  - `git_diff_prediction_f_cde.patch`

Suggested next-session first action:

- Read Claude's audit suggestions.
- Focus on correctness bugs and speed optimizations around F generation, CDE/F backtest payload calculation, caching, and frontend rendering.

## 2026-06-03 Handoff - Prediction Panel D/E Rule Change

User requested:

- Spain and Poland: use C and D predictions, each currently 8 groups of 4-number tickets. Collect unique numbers from those C/D 4-number tickets, kill those unique numbers, then output new 4-number tickets.
- Russia and Italy: change D because killing A+B+C leaves too few numbers. D should only kill C, then output 4-number tickets.

Implemented.

Backend changes in `keno_dashboard_server.py`:

- Added prediction panel E:
  - `PREDICTION_PANEL_E = "e"`.
  - Label: `预测面板E`.
  - Tracking method version: `strategy-ticket-e-v1`.
  - Aliases include `e`, `panel_e`, `prediction_e`, `predictione`, `kill_cd`, `clean_cd`.
- E is enabled only for:
  - `spain_l_express_20_70`
  - `poland_keno_20_70`
- E rule:
  - Generate A/B/C first.
  - Generate D-source tickets using the normal Spain/Poland D rule.
  - Collect unique main numbers from C 4-number tickets and D 4-number tickets.
  - Use that C+D unique set as `excludedNumbers`.
  - Generate 8 clean 4-number tickets from the remaining pool.
  - Ticket label: `E CD杀号四码`.
  - `sourcePanel = "cd"`, `sourcePanels = ["c", "d"]`, `structureType = "kill_cd_four"`.
- E on Russia/Italy returns no tickets and an explanatory method string:
  - Current intent is to avoid over-killing 20-number games.
  - Russia/Italy should use D's new only-kill-C rule instead.
- Changed D rule for:
  - `russia_rapido_8_20`
  - `italy_win_for_life_10_20`
- Russia/Italy D now:
  - Kills only unique main numbers from C 4-number tickets.
  - Generates 8 clean 4-number tickets.
  - Ticket label: `D C杀号四码`.
  - `sourcePanel = "c"`, `sourcePanels = ["c"]`, `structureType = "kill_c_four"`.
- Spain/Poland D stays as the prior A+B+C kill rule:
  - Ticket label remains `D ABC杀号四码`.
- D tracking method version was intentionally bumped:
  - Old: `strategy-ticket-d-v1`.
  - New: `strategy-ticket-d-v2`.
  - Reason: D behavior changed for Russia/Italy, so new D tracking records must not be deduped or grouped with older ABC-kill D records.
- Auto tracking now also generates E and reports:
  - `summaryE`
  - `trackingTotalE`

Frontend changes:

- `web/index.html`:
  - Added top nav button `预测面板E`.
  - First five top tabs are now A/B/C/D/E.
  - A/B/C/D remain the first four tabs as user requested earlier.
- `web/app.js`:
  - Added E state slot under `predictionPanels`.
  - Added `PREDICTION_PANEL_E = "e"`.
  - Added `predictionE` routing/mapping/support in:
    - `normalizePredictionPanel`
    - `predictionPanelLabel`
    - `predictionPanelForView`
    - `predictionPanelForOptions`
    - `currentGameSupportsView`
    - `hydrateView`
    - `isPredictionMainViewActive`
    - `refreshCurrentView`
    - `switchView`
  - Loading text:
    - E: `读取C/D四码票并生成CD杀号4码票`
  - Kill panel labels:
    - B: `面板A杀号`
    - D on Russia/Italy: `C杀号`
    - D on Spain/Poland: `ABC杀号`
    - E: `CD杀号`
  - Empty ticket area now displays the method/explanation instead of blank content, useful for Russia/Italy E where no tickets are generated.

Verification script added:

- `tmp/verify_prediction_e_rules_ui.mjs`
  - Real Playwright browser check.
  - Verifies top tabs A/B/C/D/E.
  - Verifies Spain E renders as `CD杀号`, 8 ticket cards, no overlap with kill pool.
  - Verifies Russia D renders as `C杀号`, 8 ticket cards, no overlap with kill pool.
  - Checks no horizontal page overflow and no console errors.

Verification commands passed:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node --check .\tmp\verify_prediction_e_rules_ui.mjs
node .\tmp\verify_prediction_e_rules_ui.mjs
```

Runtime verification snapshot after backend restart:

- Current server: `http://127.0.0.1:8787`
- Current backend process: `python PID 43156`

API verification summary:

```text
Spain E:
  game=spain_l_express_20_70
  panel=e
  sourcePanel=cd
  killCount=22
  tickets=8
  firstTicket=5-15-29-33
  label=E CD杀号四码
  overlapWithKilledNumbers=0
  trackingTotal=24

Poland E:
  game=poland_keno_20_70
  panel=e
  sourcePanel=cd
  killCount=16
  tickets=8
  firstTicket=33-35-48-61
  label=E CD杀号四码
  overlapWithKilledNumbers=0
  trackingTotal=24

Russia D:
  game=russia_rapido_8_20
  panel=d
  sourcePanel=c
  killCount=9
  tickets=8
  firstTicket=2-5-6-13
  label=D C杀号四码
  overlapWithKilledNumbers=0
  trackingTotal=12

Italy D:
  game=italy_win_for_life_10_20
  panel=d
  sourcePanel=c
  killCount=11
  tickets=8
  firstTicket=14-15-17-18
  label=D C杀号四码
  overlapWithKilledNumbers=0
  trackingTotal=16
```

Tracking verification:

- Russia D latest records include:
  - `methodVersion = strategy-ticket-d-v2`
  - `strategyLabel = D C杀号四码`
  - `structureLabel = C杀号四码`
- Spain E latest records include:
  - `methodVersion = strategy-ticket-e-v1`
  - `strategyLabel = E CD杀号四码`
  - `structureLabel = CD杀号四码`

Browser verification summary:

```text
Top tabs: 预测面板A / 预测面板B / 预测面板C / 预测面板D / 预测面板E
Backtest tab: not present in top navigation
Spain E: CD杀号, killCount=22, ticketCards=8, firstTicket=5-15-29-33, overlap=[]
Russia D: C杀号, killCount=9, ticketCards=8, firstTicket=2-5-6-13, overlap=[]
pageOverflow=0
console errors=[]
```

Important notes for next session:

- Do not downgrade D back to `strategy-ticket-d-v1`; the version bump is intentional because the D rule changed.
- Existing older D records with `strategy-ticket-d-v1` can still appear in tracking history. New D records should use `strategy-ticket-d-v2`.
- Running prediction API checks creates/touches prediction tracking records. The tracking totals above already include records created during verification.
- The working tree already had many unrelated modified/deleted runtime files and data files. Do not revert unrelated changes unless explicitly requested.

## 2026-06-02 Late Handoff - Spain Settlement Lag

User reported: `西班牙的结算总慢一期`.

Diagnosis:

- Settlement logic itself was working. When Spain history caught up from `2026-06-02T15:34:00+00:00` to `2026-06-02T15:46:00+00:00`, auto tracking immediately settled `20` prediction records.
- The visible lag came from upstream Spain draw data arriving late into local history.
- Verification snapshot around `2026-06-02T15:52:00+00:00`:
  - Local newest Spain draw: `2026-06-02T15:46:00+00:00`.
  - Oldest overdue target draw: `2026-06-02T15:50:00+00:00`.
  - Pending overdue records across A/B/C for that target: `20`.
  - LotoDate official supplement latest: `2026-06-02T15:46:00+00:00`.
  - BC incremental fetch still did not provide `15:50`; refresh response showed source/history still behind the target.
- So Spain can look "one draw late" because the target draw is over, but neither BC nor LotoDate has provided that draw to the local history yet.

Backend changes in `keno_dashboard_server.py`:

- Added `PREDICTION_TRACKING_OVERDUE_AUTO_SYNC_COOLDOWN_SECONDS = 20`.
- Added `prediction_tracking_auto_sync_status(records, rows, config)`:
  - Detects pending records whose `targetDrawTimeMs + grace <= now` while local latest history is still earlier than the target.
  - Returns diagnostic fields such as `reason=history_behind_target`, latest local draw time, oldest/newest overdue target time, overdue pending record count, and grace seconds.
- Kept `prediction_tracking_needs_auto_sync()` as a bool wrapper over the new status helper.
- Updated `maybe_auto_sync_prediction_tracking()`:
  - Uses the new overdue status.
  - For overdue history-behind-target cases, retry cooldown is now `20` seconds instead of the old Spain-effective `120` seconds (`max(45, drawIntervalMinutes * 30)`).
  - `autoSync` API response now includes `cooldownSeconds`, `trigger`, and `history_behind_target` diagnostics.
- Updated `run_prediction_auto_once()`:
  - After refresh, it loads current rows and tracking records and computes `tracking_wait`.
  - If `waitingForDraw=True`, auto tracking updates summaries only and does not generate new A/B/C prediction tracking batches.
  - Result payload now includes `waitingForDraw` and `trackingWait`.

Verification run:

```powershell
python -m py_compile .\keno_dashboard_server.py
```

Runtime verification:

- Restarted backend. Current server is `http://127.0.0.1:8787`, Python PID `11312`.
- `/api/prediction-auto` for Spain returned `waitingForDraw=True` when local latest draw was `15:46` and overdue target was `15:50`.
- `/api/prediction-tracking?game=spain_l_express_20_70&panel=a&status=pending&page=1&pageSize=200` returned `autoSync.reason=history_behind_target`.
- Pending A-panel groups at the verification moment:
  - `2026-06-02T15:50:00+00:00`: `6`
  - `2026-06-02T15:54:00+00:00`: `6`

Important next-session note:

- Do not treat Spain pending-at-current-draw as a settlement bug until checking `autoSync.reason`.
- If `reason=history_behind_target`, the system is waiting for source data. It should retry sync every ~20 seconds for overdue pending records and should not keep creating new future tracking batches while waiting.
- If source data has arrived but records remain pending, then inspect `settle_prediction_tracking()` and `rows_by_time[target_ms]`.

## 2026-06-02 Final Note Before Session Restart

User is restarting the conversation. Continue from this state, do not redo the Slovakia removal from scratch.

Final state:

- Slovakia / `sk_keno_20_80` is fully removed from active app code/config/data.
- `/api/games` has 4 games and defaults to `spain_l_express_20_70`.
- `data/bc_keno_history.csv` is deleted and did not reappear after backend restart and browser verification.
- `README_KENO.md`, `fetch_etipos_archive.py`, `data/bc_triples_report.csv`, and `data/triples_report.csv` were deleted as old Slovakia-only artifacts.
- `keno_triple_omission.py` remains because the backend imports it, but it is now Keno 20/70/default-Spain oriented rather than Slovakia 20/80 oriented.
- `tmp/verify_slovakia_removed_ui.mjs` intentionally contains `sk_keno_20_80` only as a negative assertion that API/UI must not expose it.
- Audit package is refreshed under `F:\我的开发\CPGAME\claude`.
- `claude/prediction_panel_spain_layout.png` is a PC desktop screenshot. Do not use mobile screenshots as the primary audit artifact.

Final verification passed:

```powershell
python -m py_compile .\keno_dashboard_server.py .\fetch_bc_keno_history.py .\fetch_official_supplements.py .\keno_triple_omission.py
node --check .\web\app.js
node .\tmp\verify_slovakia_removed_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
node .\tmp\verify_modal_views_ui.mjs
node .\tmp\verify_adjacent_tool_ui.mjs
node .\tmp\verify_martingale_ui.mjs
```

The earlier self-check hang was caused by repeated history modal hydration:

```text
openToolModal("history") -> hydrateView("history") -> loadHistory() -> renderHistory() -> updateGameUi() -> openToolModal("history")
```

`openToolModal()` now returns early when the same modal is already open, so the browser no longer enters that loop.

## 2026-06-02 Continuation - Slovakia Fully Removed

User decided Slovakia should not remain as history-only. Current intended state:

- `sk_keno_20_80` / Slovakia is removed entirely from the app.
- No Slovakia game should be offered by `/api/games`, frontend selectors, pills, prediction tools, tracking, or auto config.
- `data/bc_keno_history.csv` was intentionally deleted and should not be recreated.
- Older HANDOFF sections below still mention Slovakia as previous project history only; this top section supersedes them.
- Audit screenshots/files should prioritize PC desktop. Mobile checks can remain only as basic overflow safety; do not use mobile screenshots as primary audit evidence.

Implemented:

- Stopped old backend `python PID 39492`, because it had already recreated `data/bc_keno_history.csv` once while old Slovakia sync code was still running.
- Updated `keno_dashboard_server.py`:
  - Default game switched to Spain: `spain_l_express_20_70`.
  - Default lottery ID switched to `115889`.
  - Default history file switched to `data/bc_spain_l_express_20_70_history.csv`.
  - Removed `LOTTERY_GAMES["sk_keno_20_80"]`.
  - Removed Slovakia odds config from `DEFAULT_MAIN_ODDS_BY_GAME`.
  - Removed eTIPOS / Slovakia supplement import and helper path.
- Updated frontend defaults:
  - `web/index.html` initial subtitle now points to BC.Game `115889` / Spain.
  - `web/app.js` no longer has Slovakia martingale default odds.
- Removed Slovakia from local runtime state:
  - `data/prediction_auto_config.json` now has only Spain, Poland, Russia, and Italy enabled.
  - `data/prediction_tracking.json`: removed 9 Slovakia records.
  - `data/prediction_tracking.sqlite3`: removed 132 Slovakia records.
  - `data/bc_keno_history.csv`: deleted.
- Updated helper/diagnostic files:
  - `fetch_bc_keno_history.py` remains because the server imports its generic BC parsing/fetch helpers, but standalone defaults now target Spain `115889` and output `data/bc_spain_l_express_20_70_history.csv`.
  - `keno_triple_omission.py` remains because the server imports its probability table and combinatorics helpers, but it was changed from Slovakia 20/80 wording/defaults to Keno 20/70 wording/defaults.
  - Deleted unused old Slovakia-only files:
    - `fetch_etipos_archive.py`
    - `README_KENO.md`
    - `data/bc_triples_report.csv`
    - `data/triples_report.csv`
  - Removed Slovakia from `tmp/check_bc_totals.py`, `tmp/audit_history_gaps.py`, and `tmp/infer_operating_hours.py`.
  - Deleted old Slovakia-only task doc `tmp/docs/keno_codex_tasks.txt`.
  - Replaced the old Slovakia-disabled UI verifier with `tmp/verify_slovakia_removed_ui.mjs`.
  - Changed `tmp/verify_prediction_layout_order.mjs` so `claude/prediction_panel_spain_layout.png` is written from the PC viewport only, not overwritten by the mobile pass.
  - Updated `tmp/verify_modal_views_ui.mjs` sync-toast fixture from `5/5` to `4/4`.
- Updated `DEPLOYMENT.md` so `data/bc_keno_history.csv` is no longer listed as an important runtime data file.

Verification on the new backend:

```powershell
python -m py_compile .\keno_dashboard_server.py .\fetch_bc_keno_history.py
node --check .\web\app.js
node --check .\tmp\verify_slovakia_removed_ui.mjs
node --check .\tmp\verify_martingale_ui.mjs
node --check .\tmp\verify_prediction_layout_order.mjs
node --check .\tmp\verify_adjacent_tool_ui.mjs
node --check .\tmp\verify_modal_views_ui.mjs
Invoke-RestMethod http://127.0.0.1:8787/api/games
node .\tmp\verify_slovakia_removed_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
node .\tmp\verify_adjacent_tool_ui.mjs
node .\tmp\verify_martingale_ui.mjs
node .\tmp\verify_modal_views_ui.mjs
```

Observed:

- `/api/games` returns exactly 4 games:
  - `spain_l_express_20_70`
  - `poland_keno_20_70`
  - `russia_rapido_8_20`
  - `italy_win_for_life_10_20`
- `/api/games.defaultGame` is `spain_l_express_20_70`.
- PC UI game select and game pills contain only those 4 games.
- `data/bc_keno_history.csv` did not reappear after restarting the backend and running browser checks.
- After the final code cleanup, the backend was restarted again and now listens as `python PID 6096`.
- Prediction page PC layout still renders 6 ticket cards, 50 tracking rows, and adjacent stats below tracking.
- Tool modals, adjacent conversion, martingale calculator, and history modal all open/close without the previous repeated-hydration hang.
- Crash/hang root cause from the previous section remains the modal rehydration loop; Slovakia removal also removes the unsupported Slovakia fallback path that used to trigger it most easily.

## 2026-06-02 Continuation - Tool Modals And Crash Fix

User asked to inspect the already-applied screenshot changes, finish self-checking, document locally, and copy the current files to `claude` for Claude audit.

Implemented / confirmed:

- `web/index.html`
  - Converted tool-style tabs into modal-capable views:
    - `派生转换`
    - `倍投计算`
    - `模拟投注`
    - `策略回测`
    - `分析面板`
    - `历史开奖`
  - Added modal backdrops and close buttons for those views.
- `web/styles.css`
  - Added shared modal overlay, modal panel, close button, scroll containment, and mobile sizing styles.
- `web/app.js`
  - Added modal state:
    - `state.activeModal`
    - `TOOL_MODAL_VIEWS`
    - `openToolModal()`
    - `closeToolModal()`
    - `hydrateView()`
    - `renderTabState()`
  - Tool tabs now open as overlays instead of replacing the prediction page.
  - `Escape` and backdrop/close buttons close the active tool modal.
  - `refreshCurrentView()` now respects the active modal.
  - Unsupported tool requests fall back to the history modal.
  - Improved all-game sync toast text to list only games with new rows, or explicitly say no new draw rows.

Important crash / hang root cause found:

- Slovakia is intentionally prediction-disabled.
- With the new history modal fallback, `updateGameUi()` opened `history` when the active view was unsupported.
- `history` hydration called `loadHistory()`, then `renderHistory()`, then `updateGameUi()`.
- Because the history modal was already open but `openToolModal("history")` rehydrated it again, this created a loop:
  - `openToolModal("history") -> loadHistory() -> renderHistory() -> updateGameUi() -> openToolModal("history")`
- Symptom:
  - Browser page became unresponsive for Slovakia / unsupported-view fallback.
  - Playwright `page.evaluate()` and `waitForFunction()` appeared to hang.
  - Earlier self-checks looked like "flash crash" or silent timeout.
- Fix:
  - `openToolModal()` now returns early when the requested modal is already open:
    - if `state.activeModal === view` and the element has `modal-open`, only tab state is refreshed and hydration is not repeated.

Verification after fix:

```powershell
node --check .\web\app.js
python -m py_compile .\keno_dashboard_server.py
node .\tmp\verify_slovakia_predictions_removed_ui.mjs
node .\tmp\verify_adjacent_tool_ui.mjs
node .\tmp\verify_martingale_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
```

Observed:

- Slovakia opens history as a modal, prediction/analysis are disabled, and history renders 100 rows.
- Switching Spain -> prediction and back to Slovakia works.
- Prediction layout still has tracking records above adjacent stats on desktop and mobile.
- Adjacent conversion modal renders desktop/mobile with `pageOverflow=0`.
- Martingale modal renders desktop/mobile with 12-row plan and `pageOverflow=0`.
- No console errors were reported by the verification scripts.

Verification script maintenance:

- `tmp/verify_martingale_ui.mjs`
  - Reworked repeated game/default-odds checks to use fresh pages per case.
  - Replaced fragile `waitForFunction()` waits with explicit `page.evaluate()` polling.
  - Added stage logs and hard-timeout cleanup.
- `tmp/verify_prediction_layout_order.mjs`
  - Replaced fragile `waitForFunction()` waits with explicit `page.evaluate()` polling.
  - Added hard-timeout cleanup.

Current caveats:

- Runtime data files remain modified by live sync/tracking:
  - `data/*.csv`
  - `data/prediction_tracking.sqlite3`
- User screenshot file remains untracked:
  - `wechat_longscreenshot_2026-06-02_143150_432.png`

## 2026-06-02 Handoff - Auto Tracking Health Check

User asked to check whether automatic tracking is normal, then record the current state locally before restarting the conversation.

Current repo state:

- Git repository is active on branch `main`.
- Remote:
  - `origin=https://github.com/Tuitefen/BCKeno.git`
- Latest pushed code commit before this handoff:
  - `802ce58 Add Italy and Russia two-ball adjacent support`
- Code was clean before the latest runtime sync changes.
- Current modified files are normal runtime data produced by sync/tracking:
  - `data/bc_italy_win_for_life_10_20_history.csv`
  - `data/bc_keno_history.csv`
  - `data/bc_poland_keno_20_70_history.csv`
  - `data/bc_russia_rapido_8_20_history.csv`
  - `data/bc_spain_l_express_20_70_history.csv`
  - `data/prediction_tracking.sqlite3`

Automatic prediction tracking status:

- `GET /api/prediction-auto` returned healthy.
- `enabled=true`
- `running=true`
- `status=running`
- `pollSeconds=60`
- `errors=[]`
- Message:
  - `自动追踪完成：4 个彩种，0 个错误`
- Last run:
  - `2026-06-01T15:07:20+00:00`
- Next run:
  - `2026-06-01T15:08:24+00:00`

Enabled games in automatic tracking:

- Spain: enabled
- Poland: enabled
- Russia: enabled
- Italy: enabled
- Slovakia: disabled intentionally because Slovakia predictions were removed; Slovakia remains history-sync only.

Important interpretation:

- `skippedPrediction=true` in a cycle is normal when there are no new rows or when the target batch already exists. It prevents duplicate tracking records.
- Italy now has pending main `2球` records plus `3球` records.
- Russia now has pending main `2球` records plus existing `2+1` special-ball records.
- Adjacent-derived stats only use main tickets with `mode == "main"`, so Russia `2+1` does not enter adjacent-derived stats.

Observed pending examples after the Italy/Russia change:

- Russia main `2球`:
  - `3-15`
  - `4-7`
  - `7-8`
- Russia `2+1特殊球`:
  - `7-11 + 1`
  - `7-14 + 1`
  - `7-15 + 1`
- Italy main `2球`:
  - `6-19`
  - `6-13`
  - `6-9`
- Italy `3球`:
  - `6-8-13`
  - `6-8-9`
  - `2-8-13`

Next-session recommendation:

1. Read this `HANDOFF.md` first.
2. Check whether server PID `75624` is still alive.
3. If code changed or server died, restart with:

```powershell
.\start_server.ps1
```

4. Re-check auto tracking with:

```powershell
Invoke-RestMethod "http://127.0.0.1:8787/api/prediction-auto"
```

## 2026-06-01 Continuation - Italy/Russia Two-Ball Prediction And Adjacent Stats

User approved:

- Italy currently had `3球` and `1+1`; recent `1+1` had not hit, so replace `1+1` with `2球`.
- Russia currently had only `2+1`; keep it and add a main `2球`.
- Enable adjacent-derived stats for those main `2球` tickets.

Implemented:

- `keno_dashboard_server.py`
  - `PREDICTION_TICKET_STRATEGIES`:
    - Italy now generates:
      - main `3球`
      - main `2球`
    - Italy no longer generates bonus `1+1`.
    - Russia now generates:
      - main `2球`
      - bonus `2+1`
  - `ADJACENT_DERIVED_STATS_GAME_KEYS` now includes:
    - `italy_win_for_life_10_20`
    - `russia_rapido_8_20`
  - Existing adjacent stats logic already filters:
    - same `gameKey`
    - settled `won/lost`
    - `mode == "main"`
    - `pickCount in {1,2}`
    - result draw exists
  - Therefore Russia `2+1` special-ball tickets are not included in adjacent-derived stats.
- Added `tmp/verify_italy_russia_two_ball.mjs`.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_prediction_layout_order.mjs
node .\tmp\verify_italy_russia_two_ball.mjs
```

Observed:

- Italy `/api/predictions` now returns:
  - three main `3球` tickets
  - three main `2球` tickets at `3.8x`
  - no bonus tickets
- Russia `/api/predictions` now returns:
  - three main `2球` tickets at `6x`
  - three bonus `2+1` tickets at `25x`
- Italy and Russia `/api/adjacent-derived-stats` return `enabled=true`.
- Current source settled records for Italy/Russia adjacent stats may be `0` until newly created main `2球` prediction records settle.

Current local server:

```text
http://127.0.0.1:8787
python PID 75624
```

## 2026-06-01 Continuation - Basic Runtime Path Cleanup

User asked whether a startup command already exists and requested basic cleanup of configuration/data paths before any server deployment work.

Answer:

- Existing startup command was already:
  - `python .\keno_dashboard_server.py`
- `启动命令.txt` also existed, but its encoding/display was messy.

Implemented:

- Added runtime directories:
  - `data/`
  - `logs/`
  - `backups/`
- Migrated current runtime data into `data/`:
  - `bc_keno_history.csv`
  - `bc_spain_l_express_20_70_history.csv`
  - `bc_poland_keno_20_70_history.csv`
  - `bc_russia_rapido_8_20_history.csv`
  - `bc_italy_win_for_life_10_20_history.csv`
  - `bc_triples_report.csv`
  - `triples_report.csv`
  - `prediction_tracking.sqlite3`
  - `prediction_tracking.json`
  - `prediction_auto_config.json`
  - `simulated_bets.jsonl`
  - `sample_history.csv`
- Updated `keno_dashboard_server.py`:
  - Added `DATA_ROOT`, `LOG_ROOT`, `BACKUP_ROOT`.
  - Defaults:
    - `DATA_ROOT = ROOT / "data"`
    - `LOG_ROOT = ROOT / "logs"`
    - `BACKUP_ROOT = ROOT / "backups"`
  - Environment overrides:
    - `BCKENO_DATA_DIR`
    - `BCKENO_LOG_DIR`
    - `BCKENO_BACKUP_DIR`
  - All game history paths now point to `DATA_ROOT`.
  - Runtime files now point to `DATA_ROOT`:
    - bets JSONL
    - prediction tracking JSON
    - prediction tracking SQLite
    - prediction auto config JSON
  - Server startup creates `data/`, `logs/`, and `backups/` if missing and prints their paths.
- Updated `fetch_bc_keno_history.py`:
  - Default output is now `data/bc_keno_history.csv`.
  - Default report output is now `data/bc_triples_report.csv`.
  - Supports `BCKENO_DATA_DIR`.
- Added `start_server.ps1`:
  - Sets default runtime env vars if not already set.
  - Creates runtime directories.
  - Starts `python .\keno_dashboard_server.py`.
- Rewrote `启动命令.txt` with clear startup commands:
  - `.\start_server.ps1`
  - fallback `python .\keno_dashboard_server.py`
- Added `DEPLOYMENT.md` with startup and directory notes.
- Updated `.gitignore`:
  - ignores `logs/`
  - ignores `backups/`
  - existing WAL/SHM ignores remain.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py .\fetch_bc_keno_history.py
node .\tmp\verify_prediction_layout_order.mjs
node .\tmp\verify_adjacent_tool_ui.mjs
```

Observed:

- Prediction panel still loads Spain data from the migrated `data/` files.
- Adjacent conversion page still works.
- Root directory no longer contains the moved runtime data files.
- Current local server:

```text
http://127.0.0.1:8787
python PID 77196
```

## 2026-06-01 Continuation - Adjacent Conversion Tool

User requested a standalone page named `派生转换`: input numbers, select derived types, and immediately output derived tickets without prediction settlement/statistics.

Implemented:

- `web/index.html`
  - Added top tab `派生转换`.
  - Added standalone `#adjacentToolView`.
  - Inputs:
    - original numbers text box
    - derived-type checkboxes
    - generate button
    - copy total-list button
- `web/app.js`
  - Added current-game independent view support for `adjacentTool`.
  - Added frontend conversion logic matching the current adjacent-derived stats rules:
    - 1 input number:
      - `1球左右邻二码`
    - 2 input numbers:
      - `2球锚点邻二码`
      - `2球外侧邻二码`
      - `2球交叉临码二码`
      - `2球局部四码`
  - Supports whitespace/comma/dash/slash separators.
  - Filters numbers by current game range.
  - Shows grouped results and a de-duplicated total ticket list.
  - Copy button copies the de-duplicated total list, one ticket per line.
- `web/styles.css`
  - Added responsive layout and pill/card styles for the conversion page.
- `tmp/verify_adjacent_tool_ui.mjs`
  - Verifies `20 35` on Spain generates 21 de-duplicated tickets.
  - Verifies anchor, outer, cross, and four-ball groups render.
  - Verifies desktop/mobile `pageOverflow=0`.

Verification:

```powershell
node --check .\web\app.js
node --check .\tmp\verify_adjacent_tool_ui.mjs
node .\tmp\verify_adjacent_tool_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
node .\tmp\verify_martingale_ui.mjs
```

Observed example for Spain input `20 35`:

- Summary: `原号 20-35 · 21 条 · 去重 21 注`
- Total list includes:
  - `19-20`
  - `20-21`
  - `34-35`
  - `35-36`
  - `19-20-34-35`
  - `20-21-35-36`

Current local server:

```text
http://127.0.0.1:8787
python PID 79484
```

## 2026-06-01 Continuation - Adjacent Hit Lookup Full Derived Display

User noticed that a grouped adjacent-hit lookup row could show `8` hits while only listing four derived winning number groups, which was misleading.

Implemented:

- `keno_dashboard_server.py`
  - Grouped adjacent-hit rows now keep `stakeTotal` as the total derived tickets generated from the source prediction record.
  - Grouped `profitTotal` now uses whole-scheme accounting:
    - `profitTotal = payoutTotal - stakeTotal`
  - Preserved the previous hit-only profit as `hitOnlyProfitTotal` for diagnostics/backward compatibility.
- `web/app.js`
  - Removed the four-item display cap from grouped adjacent-hit lookup rows.
  - Lookup rows now show every winning derived ticket for that source prediction record.
  - Column labels now use the clearer accounting language:
    - `中奖派生号码`
    - `命中/总注`
    - `整套利润`
  - `命中/总注` displays `hitTickets / stakeTotal`, so the row shows both winning ticket count and total derived tickets bought for that source prediction.
- `web/styles.css`
  - Added wrapping pill styles for full derived-ticket display.
- `tmp/verify_adjacent_hit_lookup_ui.mjs`
  - Verifies that visible derived-ticket pills equal the API `derivedTickets.length`.
  - Verifies grouped `profitTotal = payoutTotal - stakeTotal`.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node --check .\tmp\verify_adjacent_hit_lookup_ui.mjs
node .\tmp\verify_adjacent_hit_lookup_ui.mjs
node .\tmp\verify_adjacent_stats_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
```

Observed:

- Adjacent hit lookup renders all winning derived tickets for the grouped row.
- First API row in verification:
  - `derivedTickets=1`
  - `visibleDerivedPills=1`
  - `hitTickets=1`
  - `stakeTotal=2`
  - `payoutTotal=11`
  - `profitTotal=9`
- Adjacent stats and prediction layout regressions passed.

Current local server:

```text
http://127.0.0.1:8787
python PID 67556
```

## 2026-06-01 Continuation - Martingale Max Stake Kept

User asked whether `单注上限` should become a group-count field. I briefly prototyped a multi-group conservative formula, but the user correctly pointed out that this confuses the hit-return assumption because a draw could hit one group or multiple groups.

Final decision:

- Reverted the prototype.
- Keep the original `单注上限` field and original single-ticket martingale formula.
- `单注上限` means the maximum allowed stake for one calculated martingale period; it is a risk warning/cutoff, not the number of groups bought.
- Multi-group martingale needs a separate design later because the UI must define whether returns assume one group hit, all groups hit, or a distribution over possible hit counts.

Code state:

- `web/index.html` restored:
  - `#martingaleMaxStake`
  - `单注上限`
  - `单期理论命中`
  - `最大单注`
  - `命中返还`
  - `命中净利`
- `web/app.js` restored:
  - `martingaleMaxStake`
  - `stake = ceil_to_unit((previousLoss + targetProfit) / (odds - 1))`
  - risk issue `超单注`
- `tmp/verify_martingale_ui.mjs`
  - Uses `#martingaleMaxStake`.
  - Slovakia expectation remains updated: Slovakia is history-only, so martingale tools should be disabled.

## 2026-06-01 Continuation - v4 Audit Follow-up

User asked to read `keno_audit_report_v4.md` and then approved the actionable follow-up. User also noted the audit report's `web/` vs `web/web/` P0 was likely caused by the audit input file.

Audit clarification:

- Checked `web/`.
- Current `web/` contains only:
  - `app.js`
  - `index.html`
  - `styles.css`
- `Test-Path .\web\web` returned `False`.
- Current served `web/app.js` already contains the latest adjacent stats / grouped hit lookup / capability matrix code.
- Therefore the v4 audit P0 about the server serving an old frontend is stale / incorrect for the current workspace.

Implemented:

- `keno_dashboard_server.py`
  - Moved `all_total = prediction_tracking_count()` out of `PREDICTION_TRACKING_LOCK` in `prediction_tracking_payload()`.
  - The scoped `total_items` count remains inside the lock with the page query; the all-game total is now computed after releasing the lock.
- `web/app.js`
  - Added direct theoretical EV display to each actionable adjacent-derived ticket card:
    - `理论 EV`
    - `理论命中`
    - `盈亏线`
  - Formula:
    - `theoryEv = theoreticalHitRate * odds - 1`
- `web/styles.css`
  - Added `.adjacent-ev-line` styling.
  - Added `@media (max-width: 440px)` so `.adjacent-stat-metrics` and scheme-card metrics render as 2x2 instead of 4 columns on narrow mobile.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_adjacent_stats_ui.mjs
node .\tmp\verify_adjacent_hit_lookup_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
```

Observed:

- Adjacent cards now show e.g.:
  - `理论 EV -13.46% · 理论命中 7.867% · 盈亏线 9.091%`
- Adjacent card count remains 8; diagnostic cards remain removed.
- `prediction-tracking` layout still has tracking above adjacent stats.
- Desktop/mobile `pageOverflow=0`.

Current local server:

```text
http://127.0.0.1:8787
python PID 68340
```

## 2026-06-01 Continuation - Split Adjacent Stats API And Grouped Hit Lookup

User asked to implement items 1 and 3 from the must-fix list, skip item 2, and remove diagnostic stats entirely because the diagnostic cards duplicated the useful content above.

Implemented:

- `keno_dashboard_server.py`
  - Added independent adjacent stats endpoint:
    - `GET /api/adjacent-derived-stats?game=...`
  - `/api/prediction-tracking` no longer computes or returns adjacent-derived stats by default.
    - This prevents every tracking page/filter request from recalculating adjacent stats.
  - `adjacent_derived_stats()` now returns only actionable ticket items.
    - Diagnostic category items are filtered out before response.
    - Note changed to remove diagnostic wording.
  - `GET /api/adjacent-derived-hits` now supports:
    - `groupBy=record` default
    - `groupBy=ticket` for raw per-ticket rows if needed later
  - Default grouped hit rows aggregate by source prediction record:
    - one row per source prediction record / draw time
    - source numbers
    - hit ticket count
    - payout total
    - profit total
    - derived ticket list
    - draw numbers
- `web/app.js`
  - Added `state.adjacentStats`.
  - Added `loadAdjacentStats()` and loads it separately from prediction tracking.
  - Adjacent hit lookup calls `/api/adjacent-derived-hits` with `groupBy=record`.
  - Lookup table now defaults to grouped rows:
    - time
    - source numbers
    - derived winning numbers summary
    - hit ticket count
    - draw numbers
    - total payout
    - total profit
  - Diagnostic stats UI removed completely.
- `web/styles.css`
  - Removed diagnostic-details styles.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_adjacent_hit_lookup_ui.mjs
node .\tmp\verify_adjacent_stats_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
```

API verification:

- `/api/prediction-tracking?game=spain_l_express_20_70&status=all&page=1&pageSize=5`
  - `hasAdjacent=false`
- `/api/adjacent-derived-stats?game=spain_l_express_20_70`
  - `ok=True`
  - `adjacentStats.enabled=True`
  - `items` contains only ticket items
- `/api/adjacent-derived-hits?game=spain_l_express_20_70&page=1&pageSize=5`
  - `groupBy=record`
  - `total=87`
  - rows aggregate multiple hit tickets under one source record

UI verification:

- Adjacent stat card count is now 8 instead of 13, confirming diagnostic cards are removed.
- Lookup still renders 50 grouped rows.
- ROI remains visible; no `样本不足`.
- Tracking table remains above adjacent stats.
- Desktop/mobile `pageOverflow=0`.

Current local server:

```text
http://127.0.0.1:8787
python PID 72900
```

## 2026-06-01 Continuation - Adjacent Scheme ROI And Paged Hit API

User approved the next must-fix items:

1. Add real "whole derived scheme" ROI because actual betting buys a set of derived tickets together, not just one rule in isolation.
2. Move adjacent hit lookup to an independent backend paged API.
3. Make diagnostic stats lower priority / folded so they do not distract from actionable derived tickets.

Implemented:

- `keno_dashboard_server.py`
  - Added `adjacent_ticket_candidates_for_numbers()` so single-rule stats and whole-scheme stats use the same candidate generation.
  - Added `adjacent_scheme_summary()`:
    - Groups by source pick count, e.g. `1球整套派生方案`, `2球整套派生方案`.
    - Tracks:
      - source records
      - winning records
      - ticket total
      - hit tickets
      - total stake
      - total payout
      - total profit
      - ROI
      - per-record hit rate
      - average tickets per source record
  - `adjacent_derived_stats()` now returns `schemeSummary`.
  - Added `adjacent_derived_hit_rows()` and `adjacent_derived_hits_payload()`.
  - New GET endpoint:
    - `/api/adjacent-derived-hits?game=...&q=...&strategy=...&page=...&pageSize=...`
  - Full adjacent hit lookup now uses this endpoint instead of relying on `adjacentStats.items[].hitExamples`.
  - `hitExamples` inside adjacent stats is reduced back to card-preview scale only.
- `web/app.js`
  - Added whole-scheme ROI cards above individual derived ticket cards.
  - Added backend-driven adjacent hit lookup pagination:
    - query input
    - search button
    - previous/next page
  - Diagnostic stats are now inside a collapsed `<details>` section under the actionable stats and lookup.
- `web/styles.css`
  - Added scheme card styles.
  - Added paged lookup controls.
  - Styled collapsed diagnostic details.
- `tmp/verify_adjacent_hit_lookup_ui.mjs`
  - Still verifies lookup input, rows, hit pills, visible ROI, and no `样本不足`.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node --check .\tmp\verify_adjacent_hit_lookup_ui.mjs
node .\tmp\verify_adjacent_hit_lookup_ui.mjs
node .\tmp\verify_adjacent_stats_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
```

API verification:

- `/api/adjacent-derived-hits?game=spain_l_express_20_70&page=1&pageSize=5`
  - `ok=True`
  - `total=172`
  - `totalPage=18`
- `/api/adjacent-derived-hits?game=spain_l_express_20_70&q=3-4&page=1&pageSize=10`
  - `ok=True`
  - `total=55`
  - `totalPage=6`

Observed scheme summary for Spain:

- `1球整套派生方案`
  - `records=111`
  - `winningRecords=15`
  - `stakeTotal=221`
  - `payoutTotal=187`
  - `profitTotal=-34`
  - `roi=-15.38%`
- `2球整套派生方案`
  - `records=111`
  - `winningRecords=72`
  - `stakeTotal=2255`
  - `payoutTotal=1844`
  - `profitTotal=-411`
  - `roi=-18.23%`

Current local server:

```text
http://127.0.0.1:8787
python PID 55716
```

## 2026-06-01 Continuation - Adjacent Derived ROI And Hit Lookup

User disliked the adjacent-derived ticket cards hiding ROI as "sample insufficient" and said ROI increases confidence rather than causing misunderstanding. User also said the current example line in the cards was not useful because it was too small, did not make the actual numbers clear, and they mainly care whether the derived ticket won; detailed records can be queried separately.

Implemented:

- `keno_dashboard_server.py`
  - Added `ADJACENT_DERIVED_HIT_DETAIL_LIMIT = 80`.
  - Adjacent-derived stats now return `hitExamples` per group.
  - Each hit example includes:
    - `recordId`
    - `targetDrawTimeUtc`
    - `sourceNumbers`
    - `derivedNumbers`
    - `drawNumbers`
    - `payout`
    - `profit`
- `web/app.js`
  - Removed the adjacent-derived ticket ROI suppression for small samples.
  - Ticket cards now show:
    - `中奖`
    - `命中率`
    - `投入/返还`
    - `ROI`
    - `利润`
  - Replaced the old cramped example line with readable hit pills, e.g. `17:46 15-16`.
  - Added a bottom `派生中奖查询` section under adjacent stats.
  - The lookup has a search box and table columns:
    - time
    - strategy
    - derived numbers
    - source numbers
    - draw numbers
    - payout
    - profit
- `web/styles.css`
  - Added styles for hit pills and the hit lookup table.
- `tmp/verify_adjacent_hit_lookup_ui.mjs`
  - New Playwright check for:
    - lookup input exists
    - hit pills render
    - hit table rows render
    - card no longer contains `样本不足`
    - ROI value is displayed

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node --check .\tmp\verify_adjacent_hit_lookup_ui.mjs
node .\tmp\verify_adjacent_hit_lookup_ui.mjs
node .\tmp\verify_adjacent_stats_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
```

Observed examples:

- Spain first adjacent ticket card:
  - `中奖 7`
  - `105 注`
  - `命中率 6.67%`
  - `投入 105`
  - `返还 77`
  - `ROI -26.67%`
  - `利润 -28`
  - hit pills include `17:46 15-16`, `17:14 45-46`, `16:54 16-17`, `16:34 60-61`
- Poland first adjacent ticket card:
  - `中奖 7`
  - `93 注`
  - `ROI -17.20%`
- Layout still passes:
  - tracking remains above adjacent stats.
  - desktop/mobile `pageOverflow=0`.

Current local server:

```text
http://127.0.0.1:8787
python PID 55756
```

## 2026-06-01 Continuation - Capability Flags And Tracking Explanation

User accepted the next-step recommendation to split game capability switches, localize the missing-target void reason, and add a concise prediction tracking caveat.

Implemented:

- `keno_dashboard_server.py`
  - Added explicit capability outputs in `game_public_config()`:
    - `supportsHistory`
    - `supportsAnalysis`
    - `supportsPredictions`
    - `supportsPredictionTracking`
    - `supportsSimBets`
    - `supportsBacktest`
    - `supportsMartingale`
  - Slovakia is explicitly history-only:
    - `supportsAnalysis=False`
    - `supportsPredictions=False`
    - `supportsPredictionTracking=False`
    - `supportsSimBets=False`
    - `supportsBacktest=False`
    - `supportsMartingale=False`
  - Spain, Poland, Russia, and Italy continue to expose all existing tools.
  - Added independent backend guards:
    - `ensure_prediction_tracking_supported()`
    - `ensure_sim_bets_supported()`
    - `ensure_backtest_supported()`
  - Sim bet endpoints now use `ensure_sim_bets_supported()`.
  - Backtest normalization paths now use `ensure_backtest_supported()`.
  - Prediction tracking endpoint now uses `ensure_prediction_tracking_supported()`.
  - Missing-target void reason is now Chinese:
    - `目标期开奖缺失，且后续期次已到达，追踪作废`
  - Existing SQLite records with the previous English reason are normalized to the Chinese text when read.
- `web/app.js`
  - Added per-view capability checks:
    - prediction
    - analysis
    - bets
    - backtest
    - martingale
  - Tab disabling now uses the capability matrix instead of one broad `supportsAnalysis` switch.
  - Prediction tracking loading checks `supportsPredictionTracking`.
  - Tracking warning area always includes:
    - `追踪命中率和 ROI 只反映历史记录，不代表未来开奖概率被改变。`
  - Old English missing-target void reason is also normalized on the frontend as a compatibility fallback.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_prediction_tracking_ui.mjs
node .\tmp\verify_slovakia_predictions_removed_ui.mjs
```

Observed:

- `/api/games` returns Slovakia as history-only and all other four games with all current tools enabled.
- Russia missing-target void rows now return Chinese reason text through the API.
- Spain tracking UI shows the caveat text and still renders 50 rows without overflow.
- Slovakia UI verification still starts and returns to history view, with prediction/analysis disabled.

Current local server:

```text
http://127.0.0.1:8787
python PID 77036
```

## 2026-06-01 Continuation - Russia Missing Target Void And V5 Audit Fixes

User reported Russia tracking still had stale pending records after the 16:37 draw and the following 17:07 cancelled draw. The stale batch was for `2026-06-01T08:52:30+00:00` UTC, which is 16:52:30 Asia/Shanghai. Local history had already advanced to `2026-06-01T09:07:30+00:00` UTC as a cancelled draw, but there was no exact 16:52:30 draw/cancel row, so those predictions should not remain pending.

Implemented:

- `keno_dashboard_server.py`
  - Added `PREDICTION_VOID_REASON_MISSING_TARGET`.
  - `settle_prediction_tracking()` now voids a pending record when:
    - the exact target draw is missing from local history, and
    - the local timeline has advanced at least one draw interval beyond that target.
  - This covers skipped/missing target draws such as Russia 16:52:30 after a later 17:07:30 cancellation arrives.
  - Updated top module docstring from Slovakia-only wording to multi-market wording.
  - Auto-sync cooldown is now dynamic: `max(45 seconds, drawIntervalMinutes * 30 seconds)`.
  - `prediction_tracking_response()` accepts precomputed `groups` and `adjacent_stats`.
  - `/api/prediction-tracking` now computes grouped summaries and adjacent-derived stats after releasing `PREDICTION_TRACKING_LOCK`, reducing lock-held CPU work.
  - Removed the duplicate in-function computation of `groups` / `allGroups`; response still returns both fields for compatibility, backed by the same computed result.
- `web/app.js`
  - Adjacent derived ticket ROI now requires at least 100 independent source samples instead of 50.
  - Tracking summary ROI shows `--` while settled sample size is below 30.
  - Pending target time now shows a compact relative marker:
    - `+Nm` for future target draws.
    - `!Nm` for overdue pending rows.
- `web/styles.css`
  - Added styles for target relative / overdue markers.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_prediction_tracking_ui.mjs
node .\tmp\verify_prediction_layout_order.mjs
```

Observed:

- Russia stale 16:52:30 Asia/Shanghai batch became `void`:
  - `pt_9b55703b7ab68d52c990`
  - `pt_82ad07aefe9e846744db`
  - `pt_18ca86b9ce016d524918`
- Void reason: `Target draw was skipped after later draws arrived; tracking voided`.
- Russia summary after settlement:
  - `total=60`
  - `pending=0`
  - `won=3`
  - `lost=48`
  - `cancelled=3`
  - `void=6`
  - `settled=51`
  - `closed=60`
- Tracking UI verification showed the new relative target marker, e.g. first Spain row included `17:46 +4m`.
- Layout verification still passes:
  - desktop/mobile `trackingBeforeAdjacent=true`
  - desktop/mobile `visualTrackingBeforeAdjacent=true`
  - desktop/mobile `pageOverflow=0`

Audit v5 notes:

- `keno_audit_v5.md` was read.
- Its `void` filter recommendation is stale: current `web/index.html` already has `<option value="void">已作废</option>`.
- Slovakia remains prediction-disabled per user decision; do not re-enable Slovakia prediction panels.

Claude audit folder was refreshed again after this change.

Current local server:

```text
http://127.0.0.1:8787
python PID 25172
```

## 2026-06-01 Continuation - Prediction Tracking Auto Sync And Layout Move

User reported the prediction tracking table still showing `等待开奖同步` for Spain/Italy and asked to move the tracking table above the adjacent-number derived stats block.

Implemented:

- `keno_dashboard_server.py`
  - Added a lightweight prediction-tracking auto-sync path.
  - When pending prediction records are due and local history has not reached their target draw time, `/api/prediction-tracking` and prediction touch/update now run a current-game incremental sync before settlement.
  - Auto-sync uses a per-game cooldown to avoid repeatedly fetching on every page refresh.
  - `autoSync` metadata is returned in prediction tracking responses for debugging.
- `web/index.html`
  - Moved the prediction tracking table above `#predictionAdjacentStats`, so the visible order is now:
    - tracking summary/groups
    - tracking records table
    - adjacent-number derived stats
- `tmp/verify_prediction_layout_order.mjs`
  - Added a Playwright layout verification script.
  - It checks tracking table DOM order and visual top position are above adjacent stats in desktop and mobile.
  - It writes `claude/prediction_panel_spain_layout.png`.
- `claude/AUDIT_BRIEF.md`
  - Updated for the next Claude audit round and explicitly references the layout screenshot.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node --check .\tmp\verify_prediction_layout_order.mjs
node .\tmp\verify_prediction_layout_order.mjs
node .\tmp\verify_prediction_tracking_ui.mjs
node .\tmp\verify_adjacent_stats_ui.mjs
```

Observed:

- Spain auto-sync advanced local newest draw from `2026-06-01T08:42:00+00:00` to `2026-06-01T08:46:00+00:00`, then later to `2026-06-01T08:50:00+00:00`.
- Spain pending records whose target time was already covered by local newest draw: `0`.
- Italy pending records whose target time was already covered by local newest draw: `0`; current Italy target was still later than local newest draw during verification, so pending was expected.
- Layout verification:
  - desktop: `trackingBeforeAdjacent=true`, `visualTrackingBeforeAdjacent=true`, `trackingRows=50`, `adjacentCards=13`, `pageOverflow=0`
  - mobile: `trackingBeforeAdjacent=true`, `visualTrackingBeforeAdjacent=true`, `trackingRows=50`, `adjacentCards=13`, `pageOverflow=0`

Claude audit folder refreshed:

- `claude/keno_dashboard_server.py`
- `claude/web/`
- `claude/tmp/`
- `claude/HANDOFF.md`
- `claude/AUDIT_BRIEF.md`
- `claude/prediction_panel_spain_layout.png`
- `claude/prediction_tracking.sqlite3`
- `claude/prediction_tracking.sqlite3-wal`
- `claude/prediction_tracking.sqlite3-shm`
- `claude/prediction_tracking.json`
- `claude/bc_*_history.csv`
- `claude/README_KENO.md`

Current local server:

```text
http://127.0.0.1:8787
python PID 69972
```

## 2026-06-01 Continuation - Slovakia Prediction Removed And V3 Audit Fixes

User decided to remove Slovakia from prediction entirely:

- Keep Slovakia draw sync/history only.
- Do not show Slovakia prediction panel.
- Do not generate Slovakia prediction tracking records.
- Do not include Slovakia in automatic prediction tracking.

Implemented:

- `keno_dashboard_server.py`
  - `sk_keno_20_80` now has:
    - `supportsAnalysis=False`
    - `supportsPredictions=False`
  - Removed Slovakia from `PREDICTION_TICKET_STRATEGIES`.
  - Added `supports_predictions()` / `ensure_predictions_supported()`.
  - `/api/predictions?game=sk_keno_20_80` now returns an error: `斯洛伐克 20/80 当前只保留开奖同步，不再生成预测`.
  - `prediction_auto_enabled_games()` and default auto config now use `supports_predictions()`.
  - Stored `prediction_auto_config.json` now has Slovakia disabled.
  - Simulated-bet endpoints now also require `supportsAnalysis`, so Slovakia betting/analysis tooling is blocked along with prediction.

V3 audit fixes implemented:

- `void` is now included in backend tracking status filters.
- Frontend tracking rows no longer use `.slice(0, 20)`; the backend page size of 50 now renders fully.
- Prediction tracking DB reads now support scoped SQL:
  - `load_prediction_tracking_for_game(game_key, status_filter, limit, offset)`
  - `prediction_tracking_count(game_key, status_filter)`
  - `/api/prediction-tracking` now loads only the selected game's records plus the requested page, instead of JSON-decoding the full SQLite table for every response.
- Spain/Poland adjacent-number derived stats now expose independent source counts:
  - `independentSamples`
  - `sourceHitRecords`
  - `sourceHitRate`
  - `sourceHitRateCi`
- Frontend adjacent stats:
  - Shows ticket sample count separately from independent draw count when multiple derived tickets come from one source prediction.
  - Hides ROI/profit for ticket stats with fewer than 50 independent samples and shows `样本不足`.
  - Uses independent-source CI for multi-ticket derived groups.
- GET API parameter/capability errors now return HTTP 400 instead of being reported as generic HTTP 500.
- Frontend async responses now check `payload.game.key` against the currently selected game before rendering. This prevents an older history/prediction request from overwriting the UI after a quick game switch.
- If a game switch is attempted while the app is loading, the dropdown is reset to the actual current game instead of leaving DOM state and app state out of sync.

Frontend behavior:

- If current game does not support predictions, the app switches to `历史开奖`.
- Slovakia prediction and analysis tabs are disabled.
- Switching back from Spain/Poland/Italy/Russia to Slovakia returns to history.
- Spain/Poland/Russia/Italy prediction behavior remains enabled.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node --check .\tmp\verify_slovakia_predictions_removed_ui.mjs
node --check .\tmp\verify_prediction_forecasts_removed_ui.mjs
node --check .\tmp\verify_adjacent_stats_ui.mjs
node --check .\tmp\verify_prediction_tracking_ui.mjs
node .\tmp\verify_slovakia_predictions_removed_ui.mjs
node .\tmp\verify_prediction_forecasts_removed_ui.mjs
node .\tmp\verify_adjacent_stats_ui.mjs
node .\tmp\verify_prediction_tracking_ui.mjs
```

API verification after restart:

- `/api/games`:
  - Slovakia `supportsAnalysis=false`
  - Slovakia `supportsPredictions=false`
  - Spain prediction remains enabled
- `/api/predictions?game=sk_keno_20_80` returns HTTP 400 with the expected no-prediction message.
- `/api/predictions?game=spain_l_express_20_70` still returns 6 strategy tickets.
- `/api/prediction-tracking?game=spain_l_express_20_70&status=void&page=1&pageSize=50` returns:
  - `statusFilter=void`
  - `itemCount=6`
  - `adjacentStats.enabled=true`
  - `p2_cross_halo_pair.samples=518`
  - `p2_cross_halo_pair.independentSamples=60`

Playwright verification:

- Slovakia initial page:
  - active view: `history`
  - prediction tab disabled
  - analysis tab disabled
  - history rows: 100
  - prediction cards: 0
  - page overflow: 0
- Spain prediction page:
  - active view: `prediction`
  - ticket cards: 6
  - tracking rows: 50
  - adjacent cards: 13
  - page overflow: 0
  - no console errors
- Italy prediction page:
  - ticket cards: 6
  - adjacent stats hidden
  - no console errors

Current local server:

```text
http://127.0.0.1:8787
python PID 23764
```

## 2026-06-01 Continuation - Removed Forecast Cards Before Claude Audit

User said the future-period forecast card block was no longer useful and asked to remove it, record the change, then back up files to `F:\我的开发\CPGAME\claude` for Claude audit.

Removed frontend-only forecast card UI:

- Removed `#predictionForecasts` from `web/index.html`.
- Removed `predictionForecasts` DOM reference from `web/app.js`.
- Removed loading placeholders for future-period forecast cards.
- Removed the `renderPredictions()` loop that rendered future cards showing:
  - big/small numbers
  - pairs/triples/quads
  - shape chips
  - omission pressure
- Removed unused forecast-card CSS:
  - `.prediction-forecast-grid`
  - `.prediction-card.near`
  - `.prediction-card.far`
  - `.prediction-row`
  - `.prediction-chip`
  - `.pressure-chip`
  - related mobile carousel rules

Important behavior retained:

- Backend `predictions.forecasts` is still returned and still used by:
  - prediction tracking target time
  - bet target time dropdown
  - auto tracking
- Strategy ticket cards, prediction tracking, and Spain/Poland adjacent-number derived stats remain visible.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node --check .\tmp\verify_prediction_forecasts_removed_ui.mjs
node .\tmp\verify_prediction_forecasts_removed_ui.mjs
```

Playwright results:

- Spain desktop:
  - `forecastContainer=false`
  - `forecastCards=0`
  - `ticketCards=6`
  - `adjacentVisible=true`
  - `adjacentCards=13`
  - `trackingRows=20`
  - `pageOverflow=0`
  - no console errors
- Spain mobile:
  - `forecastContainer=false`
  - `forecastCards=0`
  - `ticketCards=6`
  - `adjacentVisible=true`
  - `adjacentCards=13`
  - `trackingRows=20`
  - `pageOverflow=0`
  - no console errors
- Italy desktop:
  - `forecastContainer=false`
  - `forecastCards=0`
  - `ticketCards=6`
  - `adjacentVisible=false`
  - `trackingRows=20`
  - `pageOverflow=0`
  - no console errors

Stale verification scripts:

- `tmp\verify_ui_changes.mjs` and `tmp\verify_special_delete_ui.mjs` still expect `.prediction-card.near` forecast cards, so they are now stale unless updated for the removed forecast-card UI.

Current local server:

```text
http://127.0.0.1:8787
python PID 71644
```

## 2026-06-01 Continuation - Prediction Tracking Duplicate Batch Fix

User reported Poland, Spain, Russia, and Italy creating too many prediction tracking rows.

Root causes:

- Every `/api/predictions` call automatically writes next-draw strategy tickets into tracking.
- Some games intentionally create multiple candidate tickets per target draw:
  - Spain/Poland: 3 `1球` + 3 `2球` = 6 rows per target draw.
  - Italy: 3 normal `3球` + 3 `1+1特殊球` = 6 rows per target draw.
  - Russia: 3 `2+1特殊球` rows per target draw.
- Deduplication previously included `basedOnDrawTimeMs`, so if the same target draw was generated again after local history caught up, the same target draw could get another full batch.

Backend fix in `keno_dashboard_server.py`:

- Added `prediction_tracking_batch_key()` using:
  - game
  - method version
  - target draw time
- `add_prediction_tracking_snapshot()` now refuses to add a new pending batch if that same game/method/target draw already has pending records.
- Added superseded-batch cleanup:
  - `PREDICTION_VOID_REASON_SUPERSEDED`
  - `void_superseded_prediction_batches()`
  - `settle_prediction_tracking()` now marks older pending batches for the same game/method/target draw as `void`, keeping only the newest base draw batch.

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
```

After triggering `/api/prediction-tracking` reads:

- Russia duplicate pending cleanup: `settledNow=3`, pending reduced to 3 for the current target.
- Italy duplicate pending cleanup: `settledNow=6`, pending reduced to 6 for the current target.
- Current pending batch check:
  - Slovakia: one target, 6 rows, `base_count=1`
  - Spain: two target times pending, each `base_count=1`; older target is waiting for history sync, not a duplicate batch.
  - Poland: no pending rows after settlement.
  - Russia: one target, 3 rows, `base_count=1`
  - Italy: one target, 6 rows, `base_count=1`

## 2026-06-01 Plan - Spain/Poland Adjacent-Number Derived Stats

User proposed tracking adjacent-number usefulness after prediction settlement, especially for Spain and Poland.

Agreed product/statistics direction:

- Treat adjacent-number analysis as derived/shadow statistics, not as a primary prediction strategy yet.
- Derived tickets/rules must be deterministic from the original prediction record and frozen by rule before judging results; do not hand-pick combinations after seeing the draw.
- Separate diagnostic hit-rate questions from purchasable ticket ROI:
  - Diagnostic examples for a 1-ball prediction `15`:
    - original number hit: `15`
    - left adjacent hit: `14`
    - right adjacent hit: `16`
    - adjacent either hit: `14 or 16`
    - local 3-number zone hit: `14/15/16`
  - Purchasable examples:
    - left pair ticket: `14,15`
    - right pair ticket: `15,16`
- For 2-ball predictions such as `20,35`, start with:
  - adjacent pair tickets around each anchor:
    - `19,20`, `20,21`, `34,35`, `35,36`
  - cross-halo 2-ball tickets:
    - every combination from `{19,20,21} x {34,35,36}`
  - outer adjacent pair tickets as a control:
    - `18,19`, `21,22`, `33,34`, `36,37`
  - optional 4-ball tickets should be tracked as low-priority/statistical-only because hits are sparse.
- Boundary rule:
  - No wraparound. For 1 and 70, missing neighbors are omitted; `70` and `1` are not adjacent.
- Initial scope:
  - Spain `spain_l_express_20_70`
  - Poland `poland_keno_20_70`
  - Normal main-number strategy tickets only (`mode=main`), especially `1球` and `2球`.
- Stats to show:
  - sample count
  - hit count
  - hit rate
  - theoretical hit rate
  - difference vs theory
  - break-even hit rate
  - unit stake total
  - payout/profit
  - ROI
  - Wilson 95% confidence interval
- Interpretation:
  - Fewer than 300 derived ticket samples: display only, no judgment.
  - 300-1000: trend only.
  - 1000-2000: preliminary comparison.
  - 2000+: stronger evidence, still account for related samples within the same draw.

Implementation suggestion:

- Prefer computing derived stats from existing settled prediction tracking records rather than creating a second persistent tracking table immediately.
- Add derived stats to `/api/prediction-tracking` responses for Spain/Poland.
- Frontend should display a compact `临码派生统计` section below grouped strategy stats.

Implemented in this session:

- Backend:
  - Added `ADJACENT_DERIVED_STATS_GAME_KEYS`.
  - Added adjacent/outer/cross-halo/four-ball candidate helpers.
  - Added `adjacent_derived_stats()` and related aggregation helpers.
  - `GET /api/prediction-tracking` now includes `adjacentStats`.
  - Scope is Spain/Poland main-number settled tracking records with `pickCount` 1 or 2.
  - No new DB table yet; stats are computed from settled tracking records and `result.draw`.
- Frontend:
  - Added `#predictionAdjacentStats` below tracking group cards.
  - Added `renderPredictionAdjacentStats()`.
  - Shows `临码派生统计` with:
    - 可投注派生票
    - 诊断统计
    - sample count, hit count/rate, Wilson CI, theoretical/break-even for ticket items, ROI/profit, examples
  - Evidence label:
    - `<300`: `仅展示`
    - `<1000`: `趋势观察`
    - `<2000`: `初步比较`
    - otherwise `样本较足`
- Added validation script:
  - `tmp\verify_adjacent_stats_ui.mjs`

Verification:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node --check .\tmp\verify_adjacent_stats_ui.mjs
node .\tmp\verify_adjacent_stats_ui.mjs
```

API check:

- Spain adjacent stats:
  - `enabled=True`
  - `sourceSettledRecords=72`
  - `items=13`
- Poland adjacent stats:
  - `enabled=True`
  - `sourceSettledRecords=72`
  - `items=13`
- Italy adjacent stats:
  - `enabled=False`

Playwright check:

- Spain desktop:
  - `cardCount=13`
  - `ticketCardCount=8`
  - `pageOverflow=0`
  - no console errors
- Poland desktop:
  - `cardCount=13`
  - `ticketCardCount=8`
  - `pageOverflow=0`
  - no console errors
- Spain mobile:
  - `cardCount=13`
  - `ticketCardCount=8`
  - `pageOverflow=0`
  - no console errors

Current local server:

```text
http://127.0.0.1:8787
python PID 61848
```

### Prediction Tracking V2 Continuation

After discussing tracking usefulness, implemented the next iteration:

- Spain and Poland strategy tickets changed from `1球` to `2球`.
- Follow-up changed Spain and Poland to include both `1球` and `2球` candidate tickets for comparison.
- Italy strategy tickets now include both:
  - normal `3球`
  - bonus `1+1特殊球`
- Italy can now produce 6 strategy ticket cards: 3 normal + 3 special-ball.
- Prediction tracking settlement now handles cancelled draws:
  - target draw found but cancelled -> record status `cancelled`
  - cancelled records are excluded from hit-rate/ROI denominator
  - UI status label shows `已取消`
- Prediction scheduling now uses `newestTimelineDraw` when the latest local row is cancelled, so Russia can continue targeting the draw after a cancellation instead of being stuck on the cancelled time.

Storage update:

- Added SQLite tracking storage:
  - `prediction_tracking.sqlite3`
- Existing `prediction_tracking.json` remains as migration source / legacy file.
- On first DB initialization, JSON records are imported if the DB is empty.
- API responses now include `trackingDb`.

Tracking API pagination/filtering:

- `GET /api/prediction-tracking?game=...&status=all&page=1&pageSize=50`
- Supported status filters:
  - `all`
  - `pending`
  - `won`
  - `lost`
  - `cancelled`
- Response includes:
  - `page`
  - `pageSize`
  - `total`
  - `totalPage`
  - paginated `items`

Automatic tracking:

- Added config file path (created on save/start/stop):
  - `prediction_auto_config.json`
- Added endpoints:
  - `GET /api/prediction-auto`
  - `POST /api/prediction-auto`
- Supported POST actions:
  - `start`
  - `stop`
  - `runOnce`
  - `save`
- Default auto config:
  - disabled by default
  - `pollSeconds=60`
  - `sync=True`
  - `maxPages=2`
  - `pageSize=100`
  - `skipSupplement=True`
  - all prediction-supported games enabled
- Auto worker loop:
  1. optionally runs incremental sync per enabled game
  2. settles pending tracking
  3. calls prediction generation for each enabled game
  4. writes deduped next-draw strategy tickets
  5. updates status/results/errors
- UI controls added in Prediction Tracking:
  - status filter
  - previous/next page
  - auto tracking status
  - `启动追踪` / `停止追踪`
  - `检查一次`

Verification after V2:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_prediction_tracking_ui.mjs
```

Additional API checks:

- Spain prediction tickets returned `西班牙 2球候选票`, `pickCount=2`, odds `11`.
- Poland prediction tickets returned `波兰 2球候选票`, `pickCount=2`, odds `11`.
- Follow-up verification:
  - Spain returns 3 `西班牙 1球候选票` and 3 `西班牙 2球候选票`.
  - Poland returns 3 `波兰 1球候选票` and 3 `波兰 2球候选票`.
- Italy prediction tickets returned both:
  - `意大利 3球候选票`, `pickCount=3`, odds `9`
  - `意大利 1+1特殊球候选票`, `pickCount=1`, `mode=bonus`, odds `35`
- `GET /api/prediction-auto` returned `enabled=False`, `running=False`.
- `POST /api/prediction-auto` with `runOnce` and `sync=false` completed 5 games with 0 errors.
- `GET /api/prediction-tracking?game=italy_win_for_life_10_20&page=1&pageSize=10&status=all` returned:
  - `items=9`
  - `summaryTotal=9`
  - `groups=2`
  - `trackingDb.exists=True`
- Playwright desktop and mobile checks:
  - no console errors
  - `pageOverflow=0`

## Latest Continuation: Prediction Tracking Phase 1

Implemented the first phase discussed after the Claude audit: automatic prediction tracking with passive settlement, without adding background auto-sync.

New storage:

- `prediction_tracking.json`
- Records are deterministic/deduped by:
  - game
  - method version
  - latest draw used as prediction base
  - target draw time
  - strategy ticket numbers / bonus number
- Current method version: `strategy-ticket-v1`
- Current behavior records the next-draw strategy tickets generated by `/api/predictions`.

New backend behavior:

- `GET /api/predictions?game=...`
  - generates prediction strategy tickets as before
  - automatically writes deduped tracking snapshots for next-draw strategy tickets
  - attempts passive settlement for that game
  - returns a compact `predictionTracking` summary
- `GET /api/prediction-tracking?game=...`
  - attempts passive settlement for the current game
  - returns current-game summary, all-game summary, grouped stats, and recent records
- `POST /api/prediction-tracking/settle`
  - manually attempts settlement for the selected/default game
- `DELETE /api/prediction-tracking/:id?game=...`
  - deletes one tracking record scoped to the current game
- `refresh_history()` now settles prediction tracking records after syncing rows.
- `refresh_all_games()` totals now include `settledPredictions`.

New frontend behavior:

- Prediction page now shows a `预测追踪` section:
  - pending / settled counts
  - actual hit rate with Wilson CI
  - theoretical hit-rate baseline
  - break-even hit rate
  - unit ROI and profit
  - grouped strategy stats
  - recent tracking records with status/result/profit
- Sync log now shows `结算预测`.
- Opening Prediction or Bets views triggers a tracking-settlement read.

Verification after this phase:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_prediction_tracking_ui.mjs
```

API checks:

- First Italy prediction call created 3 tracking records.
- Repeating the same Italy prediction call returned `createdNow=0`, confirming dedupe.
- Slovakia prediction UI check created 3 tracking records during browser verification.
- `GET /api/prediction-tracking?game=sk_keno_20_80` returned `items=3`, `groups=1`, `allTotal=6`.
- `POST /api/prediction-tracking/settle` returned `ok=True`; current records remain pending because target draws were not yet in local history.
- Desktop and mobile Playwright checks had no console errors and `pageOverflow=0`.

Current tracking file state after verification:

- `prediction_tracking.json` exists.
- It contains 6 pending records:
  - 3 Italy `意大利 3球候选票`
  - 3 Slovakia `斯洛伐克 2球候选票`

Important data note:

- `simulated_bets.jsonl` is currently 0 bytes.
- Recursive search found no `simulated_bets*` backup or temp file in the workspace.
- Do not invent or recreate the prior 3 simulated bet records without the original record details.

## Current Data State

Italy Win for Life Classico 10/20 was deep-backfilled once.

- File: `bc_italy_win_for_life_10_20_history.csv`
- Oldest local draw at previous deep check: `2024-10-03T18:00:00Z`
- Added deep-history rows have status `official-wflcloud`.
- Daily/latest sync logic is unchanged:
  1. BC.Game fetch.
  2. LotoDate recent supplement.

Special-number mapping was checked:

- Archive source special field: `Numerone`
- Local field: `bonus_ball`
- 300 archive rows sampled, 298 overlapped local/BC rows.
- Main-number mismatches: `0`
- `Numerone`/`bonus_ball` mismatches: `0`

## Latest Feature Changes

### Claude Audit Fixes

Implemented the concrete correctness and low-risk audit fixes from `keno_audit_report.md`:

- Added `HISTORY_CACHE_LOCK` around history-cache reads, writes, and clears.
- Removed the hard-coded `80` default from `find_run_windows`; callers now pass the active game's `totalNumbers`.
- Changed backend odds validation from `odds > 0` to `odds > 1` for simulated bets and backtests; frontend odds inputs now use `min="1.01"`.
- Fixed `evProfitOnly` to use the same full-payout odds semantics as the rest of the app: `P * odds - 1`.
- Removed the stale backend `evAt60x` field and frontend fallback.
- Added a 1 MB JSON request-body limit.
- Made simulated-bet defaults for numbers/pair/triple/quad use `DEFAULT_MAIN_ODDS_BY_GAME` for the selected game.
- Removed the unused `runs` variable from `run_length_distribution`.
- Made backtest scan `minBets=0` expansion explicit.
- Backtest scan responses now include skipped fixed-shape scan counts:
  - `skippedFixedShapeScans`
  - `skippedFixedShapeGroups`
  - `skippedFixedShapeCandidates`
- Backtest scan UI now warns about ROI data-mining bias, skipped fixed-shape candidates, and deduped rank results.
- Prediction UI now states that the current panel is heuristic only and shows a stronger sample-size warning when available history is below 500 valid draws.
- Prediction UI now includes concrete strategy candidate tickets for the priority games:
  - Italy normal `3球`
  - Russia `2+1特殊球`
  - Spain normal `1球`
  - Poland normal `1球`
  - Slovakia normal `2球`
- Each strategy ticket shows:
  - concrete purchasable numbers
  - configured odds
  - theoretical hit rate
  - break-even hit rate
  - recent-window hit rate
  - Wilson confidence interval
  - current/max omission
  - EV at configured odds
  - 10-period all-miss probability

Verification run after fixes:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_martingale_ui.mjs
node .\tmp\verify_backtest_scan_ui.mjs
node .\tmp\verify_backtest_dedupe_ui.mjs
node .\tmp\verify_ui_changes.mjs
node .\tmp\verify_prediction_tickets_ui.mjs
```

Additional API checks:

- `GET /api/games` returned `ok=True`.
- Italy analysis `threePick` returns `defaultOdds=9` and `evAtDefaultOdds=-0.052631578947368474`.
- Italy sim-bet defaults now return `pair=3.8`, `triple=9`, `quad=20`.
- All five priority prediction games returned 3 strategy tickets.
- Strategy-ticket UI rendered 3 cards with no console errors and `pageOverflow=0`.
- Bets-tab scope check passed:
  - Slovakia shows `0 条` and the cross-game notice
  - Poland shows `3 条`
  - Both current and all-games tables render on the same page
- Single backtest and scan results now include:
  - `hitRateCi`
  - `hitRateVsTheory`
- Backtest scan hit-rate cells expose the 95% confidence interval as a hover title.
- Oversized JSON request bodies now return HTTP `413`.
- Martingale special-ball mode now explains the probability estimate as `main hit probability * 1 / bonus-ball pool`.
- Simulated bets are filtered by current game in the Bets tab. The three existing records are all for `poland_keno_20_70`, so the Bets table will look empty on other games unless you switch to Poland. The UI now says this explicitly and also shows the total count across all games.
- API `sim-bets?game=...` now returns `allSummary` alongside the current-game `summary`, so the frontend can distinguish "no bets for this game" from "no bets at all".
- Bets tab now shows two tables on one page:
  - current game records
  - all games records
  The current-game table shows the empty-state notice only when that game really has no bets.
- Added validation scripts:
  - `tmp\verify_prediction_tickets_ui.mjs`
  - `tmp\verify_bets_scope_ui.mjs`

One old script, `tmp\verify_backtest_strategy_ui.mjs`, currently fails because it expects legacy `condition_top_n` UI options that were already removed by the prior strategy-menu cleanup. This is a stale test expectation, not a failure from the latest audit fixes.

### Backtest Scan Cleanup

Problem:

- Auto scan results showed redundant rows, such as the same concrete two-number run appearing as both `18-19 / 二连` and `任意两连：18-19 / 任意两连`.

Fix:

- Removed bare shape-event scan output from auto scan ranking.
- Simple shape events already covered by concrete run strategies are skipped:
  - `hasPair`
  - `hasTriple`
  - `hasQuad`
- Ranking results are deduped by actual strategy/selection and keep the better ROI/profit/hit-rate result.
- Scan response now includes `dedupedRankResults`.

Important behavior:

- Shape events such as `三双两连` are useful only when decomposed into concrete purchasable combinations, such as `3-4 + 14-15 + 17-18`.
- Do not reintroduce plain event-based ranking unless clearly separated as analysis-only, not purchase strategy.

### Strategy Menu Cleanup

The strategy dropdown no longer displays duplicated `含xxx遗漏` labels.

Current labels include:

- `两连号遗漏 Top N`
- `三连号遗漏 Top N`
- `四连号遗漏 Top N`
- `双两连遗漏 Top N`
- `三双两连遗漏 Top N`
- `两连+三连遗漏 Top N`
- `三连+双两连遗漏 Top N`

### Martingale Calculator

Added a new top tab: `倍投计算`.

Inputs:

- Mode:
  - `普通主号`
  - `含特殊球`
- Pick count: `1球` to `8球`, or `1+1特殊球` style in special-ball mode.
- Odds.
- Initial bankroll.
- Chase periods.
- Target net profit.
- Stake unit.
- Per-bet max stake.
- Stop-loss line.

Formula:

```text
stake = ceil_to_unit((previous_loss + target_profit) / (odds - 1))
```

Probability:

```text
normal main numbers: C(drawnNumbers, k) / C(totalNumbers, k)
special-ball mode: main_number_probability * (1 / bonusBallTotalNumbers)
```

EV:

```text
EV = probability * odds - 1
```

Default normal odds:

```text
Slovakia 20/80:
1=3.6, 2=15, 3=60, 4=250, 5=1000, 6=3800, 7=12500, 8=35000

Spain 20/70:
1=3.2, 2=11, 3=40, 4=150, 5=500, 6=2000, 7=6500, 8=18000

Poland 20/70:
1=3.2, 2=11, 3=40, 4=150, 5=500, 6=2000, 7=6500, 8=18000

Russia 8/20:
1=2.2, 2=6, 3=18, 4=60, 5=220, 6=1000, 7=5000
Russia 8-ball has no configured normal default odds and clears the odds input.

Italy 10/20:
1=1.8, 2=3.8, 3=9, 4=20, 5=50, 6=150, 7=500, 8=1650
```

Special-ball odds:

```text
Russia 8/20 + special ball:
1+1=9, 2+1=25, 3+1=70, 4+1=200, 5+1=700, 6+1=2000, 7+1=8000

Italy 10/20 + special ball:
1+1=35, 2+1=75, 3+1=150, 4+1=300, 5+1=600, 6+1=1500, 7+1=3000, 8+1=10000
```

Special-ball EV quick check:

- Russia `2+1` special ball: `P=3.6842%`, fair odds `27.1429`, odds `25`, EV `-7.8947%`.
- Italy normal `3球`: `P=10.5263%`, fair odds `9.5`, odds `9`, EV `-5.2632%`.

### Analysis Panel EV Fix

Problem:

- Analysis panel used fixed `60x 理论期望` for 3-pick EV, which was wrong for games where default 3-ball odds are not 60.

Fix:

- Backend `probability_summary()` returns:
  - `threePick.defaultOdds`
  - `threePick.evAtDefaultOdds`
- Frontend label now displays current game's 3-ball default odds, for example:
  - `3球 9.00x 期望` for Italy.

### Prediction Feature Concern

The user believes the current prediction panel has low practical value and may be too close to omission/random-style ranking.

Current prediction method string:

```text
当前遗漏 + 近240期动量偏差 + 全样本偏差 + 连号遗漏 z-score 的启发式排序
```

Need future discussion/work:

- Rework prediction around concrete purchasable target strategies, not generic top-number display.
- Priority candidates from current EV discussion:
  1. Italy normal `3球`.
  2. Russia `2+1特殊球`.
  3. Spain/Poland normal `1球`.
  4. Slovakia normal `2球`.
- Prediction UI should likely show strategy-specific candidate tickets, break-even hit rate, historical backtest hit rate, sample-size warning, and bankroll/chase risk.

## Verification Already Run

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_backtest_dedupe_ui.mjs
node .\tmp\verify_backtest_scan_ui.mjs
node .\tmp\verify_martingale_ui.mjs
```

Browser verification:

- Backtest strategy menu has no `含xxx` duplicates.
- Auto scan result table has no duplicate displayed strategy/type rows in tested sample.
- Martingale normal odds default correctly across configured games.
- Martingale special-ball odds default correctly for Russia and Italy.
- Slovakia special-ball mode disables unavailable special-ball buttons.
- Analysis panel Italy 3-ball EV label uses `9.00x`, not `60x`, and EV is `-5.26%`.
- Desktop and mobile martingale plan generation works.
- Console errors: none.

## Files Copied To Claude Audit Folder

Audit folder:

`F:\我的开发\CPGAME\claude`

Contains:

- `AUDIT_BRIEF.md`
- `keno_dashboard_server.py`
- `fetch_italy_winforlife_archive.py`
- `fetch_official_supplements.py`
- `fetch_bc_keno_history.py`
- `web/index.html`
- `web/app.js`
- `web/styles.css`
- current game CSV files
- verification scripts under `tmp/`

Claude audit should focus especially on prediction feature usefulness, practical prediction-rule improvements, strategy-specific UI, martingale/special-ball EV correctness, and possible useful feature extensions.

## Notes

- This workspace is now a git repository on branch `main`.
- Use root `HANDOFF.md` as the current reliable handoff.
- Claude audit backups are under `claude\`.

## 2026-06-01 Handoff - Prediction Tracking Time Fix

User reported screenshots where prediction tracking target draw time was earlier than the creation time, for example:

- Slovakia target `11:12`, created `11:12` after the draw had already passed.
- Spain target `03:02`, created `03:04`.
- Poland target `02:46`, created `02:57`.

The user also reported Spain, Poland, and Italy did not settle after syncing.

Root cause:

- Tracking target draw was generated as `local newest draw time + draw interval`.
- If local history was behind real current time, this generated a target draw that had already passed.
- Prediction payloads were also cached without a time bucket, so an old target draw could be reused even when the file had not changed.
- Spain, Poland, and Italy had pending records created hours after their target draw times, so they were invalid tracking records rather than meaningful pending bets.

Backend fixes in `keno_dashboard_server.py`:

- Added `PREDICTION_TRACKING_LEAD_SECONDS = 45`.
- Added `future_prediction_draw_times()`:
  - Chooses the first forecast draw strictly after current time plus the lead buffer.
  - Skips closed operating hours for games with `operatingHours`.
  - Produces up to `PREDICTION_HORIZONS` future forecast slots.
- Updated `prediction_payload()`:
  - Forecast cards now use `future_prediction_draw_times()` instead of blindly using `newest_ms + horizon * interval`.
  - `drawOffset` can now be larger than 1 when local history is behind, which is intentional.
- Added `prediction_schedule_cache_bucket()` and included it in the prediction cache key:
  - Prevents stale prediction payloads from reusing expired target draw times.
- Added `parse_datetime_ms()`.
- Added invalid-tracking status:
  - Status: `void`
  - Reason: `预测创建晚于目标期开奖，追踪作废`
- Updated `settle_prediction_tracking()`:
  - Pending records where `createdAt >= targetDrawTimeMs` are marked `void`.
  - `void` records are treated like cancelled/invalid records, not wins/losses.
- Updated `prediction_tracking_summary()`:
  - Adds `void`.
  - `closed = settled + cancelled + void`.
  - `void` records are excluded from hit-rate / ROI denominators.

Frontend fixes:

- `web/app.js`
  - `statusBadge()` supports `void` as `已作废`.
  - `trackingDrawResult()` displays the void reason instead of trying to show a missing draw result.
  - Tracking stat card now shows `作废` count beside settled/cancelled.
- `web/index.html`
  - Tracking status filter includes `已作废`.
- `web/styles.css`
  - `void` uses the same muted badge style as cancelled.

Verification run after restart:

```powershell
python -m py_compile .\keno_dashboard_server.py
node --check .\web\app.js
node .\tmp\verify_prediction_tracking_ui.mjs
node .\tmp\verify_prediction_tickets_ui.mjs
node .\tmp\capture_claude_ui.mjs
```

Manual API verification:

```text
now 2026-06-01T05:02:32+00:00
sk_keno_20_80 target 2026-06-01T05:04:00+00:00, generated 2026-06-01T05:02:39+00:00
spain_l_express_20_70 target 2026-06-01T05:06:00+00:00, generated 2026-06-01T05:02:45+00:00
poland_keno_20_70 target 2026-06-01T05:06:00+00:00, generated 2026-06-01T05:02:49+00:00
italy_win_for_life_10_20 target 2026-06-01T06:00:00+00:00, generated 2026-06-01T05:02:51+00:00
russia_rapido_8_20 target 2026-06-01T05:07:30+00:00, generated 2026-06-01T05:02:52+00:00
```

SQLite verification after fix:

```text
spain_l_express_20_70      {'lost': 43, 'won': 5, 'void': 6, 'pending': 6}
poland_keno_20_70          {'lost': 36, 'won': 6, 'void': 6, 'pending': 6}
italy_win_for_life_10_20   {'lost': 13, 'won': 2, 'void': 6, 'pending': 6}
sk_keno_20_80              {'lost': 63, 'won': 9, 'pending': 6}
russia_rapido_8_20         {'lost': 23, 'cancelled': 3, 'won': 1, 'pending': 3}
bad_pending_count          0
```

Current local server:

```text
http://127.0.0.1:8787
python PID 46944
```

If backend code changes next session, restart PID `46944`.

Important product note:

- User agrees Slovakia 2-minute draw interval is too short for manual operation because analysis may finish after betting has stopped.
- Keep Slovakia as a test/diagnostic game for now.
- Next practical work is to choose a replacement game with a longer betting window and then wire it into the same prediction/tracking pipeline.
