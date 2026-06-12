# CPGAME Handoff

Updated: 2026-06-12 Asia/Shanghai

This handoff is intentionally ASCII-only. Local PowerShell output can garble
Chinese text, and the next session must be able to read this file reliably.

## Current Production Issue

The previous Poland sync stuck point is resolved.

Current active issue:

```text
Production frontend refresh can wait several minutes before C-plan appears,
especially after supervisor restart.
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
supervisorctl restart cpgame
```

Then verify:

```bash
curl -s 'http://127.0.0.1:8787/api/prediction-auto' | python3 -m json.tool | grep -E 'pollSeconds|effectivePollSeconds|effectiveCatchupPollSeconds|message'
```

Expected normal state:

```text
pollSeconds: 60
effectivePollSeconds: 60
effectiveCatchupPollSeconds: 5
```

Check C-plan performance:

```bash
curl -s 'http://127.0.0.1:8787/api/predictions?game=poland_keno_20_70&panel=m&autoSync=0' | python3 -m json.tool | grep -E 'cacheHit|stakingSimulationIncluded|performance|predictionComputeMs|trackingTouchMs|totalMs|reason'
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
