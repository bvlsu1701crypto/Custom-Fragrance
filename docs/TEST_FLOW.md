# 前后端联调测试文档

从零启动到完整跑通一次香水推荐的操作手册。适合第一次 clone 下来的人照着做。

---

## 0. 前置依赖

| 组件 | 版本要求 |
|---|---|
| Python | 3.10+（项目 venv 已带） |
| Node.js | 18+（推荐 20） |
| npm / pnpm | 任意 |
| DeepSeek API Key | `.env` 里 `DEEPSEEK_API_KEY=...` |
| 网络 | 能访问 `api.deepseek.com` 和 `api.open-meteo.com` |

检查 key：
```bash
cat /Users/coy/Desktop/CodeX/Custom-Fragrance/backend/.env | grep DEEPSEEK
```

---

## 1. 启动后端

开 **终端 A**：
```bash
cd /Users/coy/Desktop/CodeX/Custom-Fragrance/backend
./venv/bin/python main.py
```

成功标志（日志）：
```
[DB] 加载 原料: 80+ 条
[DB] 加载 香基: 30+ 条
[DB] 加载 配方明细: 300+ 条
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete.
```

**常见坑**
- `command not found: python` → 用 `./venv/bin/python`，不要直接 `python`
- `ModuleNotFoundError` → `./venv/bin/pip install -r requirements.txt`
- 端口被占 → `lsof -ti:8000 | xargs kill -9`

---

## 2. 启动前端

开 **终端 B**（另开一个，不要覆盖终端 A）：
```bash
cd /Users/coy/Desktop/CodeX/Custom-Fragrance/frontend
npm install    # 第一次需要
npm run dev
```

成功标志：
```
▲ Next.js 16.x.x
- Local:   http://localhost:3000
✓ Ready in ...s
```

浏览器打开 http://localhost:3000，首页应有 hero 图 + 哲学段落。

**前端读后端地址的位置**：[frontend/lib/api/client.ts](frontend/lib/api/client.ts)，默认 `http://localhost:8000`。

---

## 3. 后端独立测试（不经前端）

在 **终端 C** 跑 3 个 curl，验证后端自己能工作。

### 3.1 健康检查
```bash
curl -s http://localhost:8000/api/health
```
期望：`{"status":"ok"}` 之类。

### 3.2 原料列表（之前曾 500，现已修）
```bash
curl -s http://localhost:8000/api/ingredients | head -c 300
```
期望：JSON，以 `{"ingredients":[` 开头。**不能**是 `Internal Server Error`。

### 3.3 完整生成
```bash
curl -s -X POST http://localhost:8000/api/generate-perfume \
  -H "Content-Type: application/json" \
  -d '{
    "preferences":{
      "occasion":"日常",
      "scent_preference":["清新","柑橘"],
      "sillage":"中等",
      "concentration":"香水",
      "avoided_notes":[],
      "time_of_day":"下午",
      "free_description":""
    },
    "biometrics":{"body_temperature":36.5,"heart_rate":72,"activity_level":"resting"},
    "environment":{"city":"Shanghai","latitude":31.23,"longitude":121.47}
  }' | python3 -m json.tool > /tmp/perfume.json

cat /tmp/perfume.json | head -80
```

逐项检查 `/tmp/perfume.json`：
- [ ] `weather_snapshot` 不为 null（后端自动查了 Open-Meteo）
- [ ] `formula.top_notes` 长度 ≥ 1
- [ ] `formula.middle_notes` 长度 ≥ 1
- [ ] `formula.base_notes` 长度 ≥ 1
- [ ] 三层 `percentage` 相加 ≈ 100（整瓶占比）
- [ ] `selection_rationale` 和 `scent_description` 都是中文完整句子

终端 A 应有相应日志：
```
[Weather] fetching Open-Meteo lat=31.23 lng=121.47
[Agent1] analyzing ...
[Agent2] 动态配比 | concentration=香水 层比=(40/35/25) ...
```

---

## 4. 前端向导走查（手工）

浏览器里按 4 步一路点到底，每步检查项如下。

### Step 0 · 偏好
- 场合、气味偏好、扩散、**浓度**（EDT/EDP/浓香/香精可选）、时段、避免、补充描述
- ❌ 没有 "持续时间"、"预算" 字段
- Next 按钮在 occasion 为空或 scent_preference=[] 时灰掉

### Step 1 · 生理
- 体温（滑杆）、心率（滑杆，能拉到 110+）、活动三选一

### Step 2 · 环境
- **只有城市下拉**（Shanghai / Beijing / ...）
- 提示文案："天气将由系统自动获取"
- ❌ 不再有手填温度/湿度/天气/季节

### Step 3 · 结果
加载动画（`t.analyzing`）之后出现结果页：
- Analysis 段落有中文描述
- **Fragrance Notes Structure** 三列（前/中/后）每列 ≥1 个标签
- 下方 Parameters 卡：Occasion / Projection / Concentration / Time of Day（❌ 没有 Longevity / Budget）
- Context 卡里 Temp / Humidity / Weather / Season 都是具体值（自动拉的）
- 底部按钮 **"查看完整配方详情 · View Full Detail"**，点开跳 `/detail`

如果任何一步报 toast 错误：复制错误内容，回终端 A 查 traceback。

---

## 5. `/detail` 详情页验证

从 Step 3 点按钮进入：
- 顶部返回按钮 + 标题
- 3 张卡（前/中/后调），每张 header 显示 "合计 X%"
  - EDT 测试时应是约 `50% / 30% / 20%`
  - EDP 测试时应是约 `40% / 35% / 25%`
  - 香精测试时应是约 `30% / 30% / 40%`
  - 三张卡 "合计" 相加 ≈ **100%**，**不是** 100/100/100
- 每条原料行：名字（中/英）+ `XX%` Badge + 扩散距离 + 强度 + 谨慎等级 + Function/Description/Scent 说明
- 底部三宫格：建议总量 ml / 香精浓度 % / 预估留香 h
- 最下：选配理由 + 气味描述

**反向用例**：直接新开无痕窗口访问 `http://localhost:3000/detail` → 应立即跳回 `/`（因为 Context 里没有结果）。

---

## 6. 关键行为验证（每项一次性测完）

固定 Shanghai + 香水浓度，只改下表变量。

### 6.1 avoided_notes 硬约束
- 选 `scent_preference=["清新","木质"]`, `avoided_notes=["柑橘"]`
- 结果页 + `/detail` 里所有原料名里 **不能** 有 柠檬/佛手柑/橙/柚/橘/青柠/香柠檬

### 6.2 前调永不为空（跨层兜底）
- `scent_preference=["花香","木质"]`
- `avoided_notes=["柑橘","海洋","青草","清新"]`
- 终端 A 出现 `[Agent2] 前调候选被 avoid 全部排除，启动跨层兜底`
- `/detail` 前调卡仍然 ≥1 条，且该原料不在中调卡里

### 6.3 浓度动态层比
依次把 concentration 切到 4 档，各生成一次：
- 终端 A 日志里 `层比=(X/Y/Z)` 四次数值不同
- `/detail` 三卡 "合计" 随之变化

### 6.4 定香不出现在三层
任意请求下，`/detail` 三卡里 **都不应** 有 "苯甲酸苄酯" 或带 "定香" 二字的原料。

### 6.5 天气降级
关闭网络 → 重新生成一次：
- 终端 A 出现 `[Weather] fallback to default`
- 请求不 500，结果页依然展示（温湿度是默认值）

---

## 7. 一页纸冒烟清单（发版前过一遍）

```
[ ] 后端 ./venv/bin/python main.py 起来，无 ERROR
[ ] 前端 npm run dev 起来，首页能打开
[ ] curl /api/health 返回 ok
[ ] curl /api/ingredients 不 500
[ ] curl /api/generate-perfume 返回三层非空 + weather_snapshot
[ ] 浏览器走完 4 步向导，结果页正常
[ ] /detail 三卡合计加总 ≈ 100%
[ ] avoided=柑橘 场景下结果无柑橘原料
[ ] 切换 EDT / 香精，日志层比不同
[ ] 终端 A 无未处理异常
```

---

## 8. 调试小抄

| 现象 | 先查 |
|---|---|
| 前端 toast "Failed to fetch" | 终端 A 还在跑吗？`curl localhost:8000/api/health` |
| 500 Internal Server Error | 终端 A 的 traceback |
| 结果页前调为空 | 终端 A 有没有 "跨层兜底" 日志；`avoided_notes` 是不是太苛刻 |
| /detail 三层都 100% | percentage 语义回退了，看 `agent2_executor.py::_build_notes` 是否保留 `layer_ratio * 100 * w / total_w` |
| 浓度切换层比不变 | `execute()` 是否把 `profile.concentration` 传给了 `_calculate_proportions` |
| 天气一直是默认值 | Open-Meteo 是否可达；`_weather_service` 是否 init |

---

## 9. 停止服务

```bash
# 终端 A / B 各自 Ctrl+C
# 若残留进程
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```
