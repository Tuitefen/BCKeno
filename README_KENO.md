# 斯洛伐克 E-Klub 基诺 20/80 分析面板

本项目用于本地抓取、保存和分析 BC.Game 的 `Slovakia E-Klub Keno 20/80`
开奖数据，重点观察连续三连号的历史命中、当前遗漏和历史最大遗漏。

游戏页面：

```text
https://bcgame.nz/zh-CN/lottery/detail/74214?tab=1
```

本地面板：

```text
http://127.0.0.1:8787
```

官方开奖归档：

```text
https://eklubkeno.etipos.sk/Archive.aspx
```

## 当前状态

最近一次增量同步时间：`2026-05-30 02:35 Asia/Shanghai`。

本地有效唯一开奖数据：

```text
63,053 条
```

本地数据范围：

```text
最新：4655712320 / 2026-05-29T18:34:00+00:00 / eTIPOS 官网临时补数
最早：4481158504 / 2026-02-28T00:00:00+00:00
```

BC 接口全量抓取时报告总数约 `64,131` 到 `64,137` 条，实际写入数量更少，
原因是接口里存在 `normalBall` 为空的未完成/无效记录。脚本现在会跳过这些
记录，并跳过全量抓取期间分页漂移造成的重复期号。

最近一次完整抓取记录：

```text
pageSize=100
sleep=0.25s
API totalPage=642
写入有效行=62,990
跳过空号/无效行=1,141
增量同步后唯一有效行=62,996
```

接口测试过 `pageSize=500`，BC 返回 `页面大小无效`，所以当前默认使用
`pageSize=100`。每页间隔 `0.25s`，属于比较稳妥的同步频率。

BC.Game 的开奖记录会比 eTIPOS 官方归档慢约 14 分钟，通常缺少最新 7 期。
现在每次点 `同步开奖结果` 或 `全量同步` 时，服务端都会：

- 先从 BC.Game 拉取并合并已有正式期号数据；
- 再从 eTIPOS 官方归档抓取当前小时和上一小时开奖；
- 用开奖 UTC 时间去重，把 BC 尚未出现的新期开奖补入本地；
- 官网没有期号，所以临时按最近 BC 期号和 2 分钟间隔推算 `drawEventId`；
- 下次 BC 同步到同一开奖时间时，会自动用 BC 正式记录覆盖官网临时记录。

## 文件说明

- `fetch_bc_keno_history.py`：从 BC.Game 抓取开奖历史，写入 CSV。
- `fetch_etipos_archive.py`：从 eTIPOS 官方归档抓取最新开奖，用于补齐 BC 延迟。
- `keno_triple_omission.py`：命令行概率和三连号遗漏分析。
- `keno_dashboard_server.py`：本地 HTTP 服务和 JSON API。
- `web/index.html`：前端页面结构。
- `web/styles.css`：前端布局和热度图样式。
- `web/app.js`：前端交互、筛选、同步和历史分页逻辑。
- `bc_keno_history.csv`：本地完整开奖数据。
- `bc_triples_report.csv`：三连号遗漏报告。
- `HANDOFF.md`：会话交接文件。关闭会话前更新这里。
- `output/dashboard/dashboard-full-data.png`：分析页验证截图。
- `output/dashboard/history-page.png`：历史开奖页验证截图。
- `output/dashboard/advanced-analysis.png`：新增高级分析验证截图。
- `output/dashboard/history-highlighted.png`：历史开奖连号高亮验证截图。
- `output/dashboard/history-etipos-large.png`：官网临时补数和放大历史页验证截图。

## 启动面板

启动本地服务：

```powershell
python .\keno_dashboard_server.py
```

打开浏览器：

```text
http://127.0.0.1:8787
```

当前面板功能：

- 顶部显示本地数据状态、开奖总数、最新/最早数据范围。
- `同步开奖结果`：增量同步。抓取最新页，遇到本地已有期号就停止。
- `全量同步`：重新抓取全部历史，逐页写入临时 CSV，完成后替换正式文件。
- `分析面板`：概率摘要、遗漏排行榜、号码热度图、三连号明细。
- `分析面板`：概率摘要、三连号明细、高级连号统计、和值/大小/奇偶分布、交叉分析。
- `历史开奖`：本地完整开奖数据分页查询，不再每次查 BC。
- 三连号明细表已放大，当前默认显示 78 个连续三连号组。
- `遗漏排名` 和 `号码热度` 已删除，避免与三连号明细重复或占用空间。
- 三连号明细现在占满内容宽度。
- `连号组合统计` 和 `最长连号长度` 放在同一排。
- `两连号遗漏明细`、`四连号遗漏明细` 放在 `交叉分析` 上方。
- 新增高级分析：
  - 两连号；
  - 双两连；
  - 三双两连、四双两连、五双两连；
  - 两连号 + 三连号；
  - 双三连；
  - 三连配双两连；
  - 四连号；
  - 和值 14 档；
  - 大小比例、奇偶比例；
  - 和值/大小/奇偶与连号条件的交叉分析。
- 历史开奖页号码已放大，并用颜色标注两连、三连、四连。
- 官网补入的临时记录会显示 `官网临时` 标签。

## 数据抓取

BC.Game 页面实际调用：

```text
POST https://bcgame.nz/api/platform-lottery/lottery-detail/history
```

请求体：

```json
{"lotteryId":"74214","pageSize":100,"page":1,"sortBy":"DRAW_DATE","sort":"DESC"}
```

请求需要浏览器类似 headers，尤其是：

```text
Origin: https://bcgame.nz
Referer: https://bcgame.nz/zh-CN/lottery/detail/74214?tab=1
User-Agent: browser user agent
Accept: application/json, text/plain, */*
```

脚本已经内置这些 header。

eTIPOS 官方归档是 ASP.NET 表单页，按斯洛伐克当地日期和小时段查询。
脚本 `fetch_etipos_archive.py` 会自动按 `Europe/Bratislava` 时区取当前小时和上一小时：

```powershell
python .\fetch_etipos_archive.py --hours 2 --limit 10
```

抓最新 1000 条：

```powershell
python .\fetch_bc_keno_history.py
```

抓指定数量：

```powershell
python .\fetch_bc_keno_history.py --limit 5000 --out .\bc_keno_history_5000.csv
```

抓全部历史到本地正式 CSV：

```powershell
python .\fetch_bc_keno_history.py --all --page-size 100 --sleep 0.25 --out .\bc_keno_history.csv
```

全量抓取现在是流式写入：

- 每页抓到后立即写入 `bc_keno_history.csv.tmp`；
- 过滤空 `normalBall`、号码数量不等于 20、重复号码、越界号码；
- 过滤重复 `draw_event_id`；
- 全部完成后再替换 `bc_keno_history.csv`。

## 分析命令

BC CSV 是新到旧排序。命令行分析时必须加 `--newest-first`：

```powershell
python .\keno_triple_omission.py --history .\bc_keno_history.csv --newest-first --top 78 --out .\bc_triples_report.csv
```

前端服务端内部会按开奖时间排序，不需要手动传排序参数。

## 本地 API

服务端监听：

```text
127.0.0.1:8787
```

接口：

- `GET /api/status`：本地文件状态。
- `GET /api/analysis`：分析数据。
- `GET /api/draws`：历史开奖分页查询。
- `POST /api/refresh`：同步开奖。

`/api/analysis` 常用参数：

- `drawLimit`：只分析最近 N 条；`0` 表示全部本地数据。
- `minCurrentMiss`：当前遗漏下限。
- `minHits`：历史命中次数下限。
- `maxTail`：遗漏尾部概率上限。
- `q`：三连号搜索。
- `sort`：排序字段，如 `currentMiss`、`maxMiss`、`hits`、`hitRate`、`tail`。
- `order`：`desc` 或 `asc`。
- `limit`：返回三连号数量。

`/api/draws` 常用参数：

- `page`：页码。
- `pageSize`：每页数量，前端可选 50、100、200、500。
- `sort`：`desc` 新到旧，`asc` 旧到新。
- `q`：搜索期号、日期，或输入多个号码查询同时出现的开奖。

增量同步请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8787/api/refresh" -Method Post -ContentType "application/json" -Body '{"mode":"incremental","pageSize":100,"sleep":0.25}'
```

增量同步返回里有：

- `newRows`：本次最终新增总数；
- `bcNewRows`：BC.Game 新增数；
- `etiposNewRows`：eTIPOS 官网补齐数；
- `etiposMeta`：官网补数检查结果。

最近一次验证：

```text
newRows=45
bcNewRows=38
etiposNewRows=7
writtenRows=63053
eTIPOS newestOfficialUtc=2026-05-29T18:34:00+00:00
```

全量同步请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8787/api/refresh" -Method Post -ContentType "application/json" -Body '{"mode":"full","pageSize":100,"sleep":0.25}'
```

## 概率说明

固定 3 个号码全部命中的概率：

```text
C(77,17) / C(80,20)
= 20/80 * 19/79 * 18/78
= 约 1.3875%
```

平均等待：

```text
约 72.07 期
约 144.1 分钟，按 2 分钟一期计算
```

如果 `60x` 是总返还赔率，理论期望：

```text
1.3875% * 60 - 1 = 约 -16.75%
```

连续三连号本身不会比任意固定 3 个号码更容易中。例如 `15-16-17` 和
`4-29-73` 的单次命中概率一样。遗漏统计适合做历史观察、筛选和波动分析，
不代表下一期概率变大。

## 三连号定义

当前分析的三连号组：

```text
1-2-3
2-3-4
...
78-79-80
```

共 78 组。某一期开奖号码里同时出现一组三连号的 3 个号码，就记为该组命中；
否则该组遗漏加 1。

字段含义：

- `currentMiss` / `current_miss`：当前连续遗漏多少期。
- `maxMiss` / `max_miss`：历史最大连续遗漏。
- `hits`：样本内命中次数。
- `hitRate`：样本内命中率。
- `missTailProbability`：按理论概率计算，至少遗漏这么久的尾部概率。

最近一次报告中当前遗漏最高：

```text
21-22-23：当前遗漏 290 期，历史最大遗漏 443 期
44-45-46：当前遗漏 253 期，历史最大遗漏 462 期
57-58-59：当前遗漏 210 期，历史最大遗漏 472 期
```

## 高级分析定义

连号窗口：

- 两连：例如 `7-8`。
- 三连：例如 `33-34-35`。
- 四连：例如 `32-33-34-35`。

多组连号默认要求互不重叠：

- 双两连：至少 2 组不重叠两连，例如 `5-6` 与 `23-24`。
- 三双两连：至少 3 组不重叠两连。
- 四双两连：至少 4 组不重叠两连。
- 五双两连：至少 5 组不重叠两连。
- 双三连：至少 2 组不重叠三连。
- 三连配双两连：至少 1 组三连 + 2 组两连，三组互不重叠。

和值范围 14 档：

```text
210-600
601-634
635-700
701-730
731-760
761-790
791-809
810-829
830-859
860-889
890-919
920-985
986-1019
1020-1410
```

大小比例：

```text
小号=1-40
大号=41-80
```

奇偶比例按开奖号码中的奇数个数和偶数个数统计。

## 验证记录

已执行：

```powershell
python -m py_compile .\fetch_etipos_archive.py .\fetch_bc_keno_history.py .\keno_dashboard_server.py .\keno_triple_omission.py
node --check .\web\app.js
python .\keno_triple_omission.py --history .\bc_keno_history.csv --newest-first --top 78 --out .\bc_triples_report.csv
```

浏览器验证结果：

```text
分析页标题：基诺分析面板
本地开奖数：63,053
三连号表：78 行
号码热度图：80 格
遗漏图：15 条
高级统计卡片：10 个
和值范围：14 档
两连遗漏表：20 行
四连遗漏表：20 行
历史开奖页：第 1 页 100 行
每期开奖：20 个号码
官网临时标签：7 条
历史页号码球：32px
console errors：0
```

当前后台服务进程：

```text
python PID 57348
```

## 后续开发计划

数据层：

- 增加自动定时同步，例如每 2 分钟或每 5 分钟增量同步一次。
- 保存同步日志，包括新增期数、跳过空号数、错误原因。
- 加配置文件，集中设置 lottery id、pageSize、sleep、默认样本窗口。

分析条件：

- 自定义号码组遗漏，例如任意 2 个、3 个、4 个号码。
- 非连续组合，例如热号组、冷号组、分区组。
- 和值、奇偶比、高低比、区间分布、尾数分布。
- 查询某组号码最近 N 期出现/未出现情况。
- 对比不同窗口，例如最近 300、1000、5000、全部数据。

可视化：

- 点击三连号查看该组命中/遗漏时间线。
- 可点击的 1-80 号码矩阵，用来构建自定义组合。
- 历史开奖详情侧栏。
- 导出当前筛选结果 CSV。

工程：

- 把分析逻辑拆成更稳定的模块，方便以后增加条件。
- 增加小型 fixture 测试，防止排序和遗漏计算再次出错。
- 保持零第三方依赖，除非后续前端复杂度明显提高。
