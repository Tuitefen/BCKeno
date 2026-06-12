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
