"""
ARAT-RL Demo Dashboard  （最终版）
====================================
普通模式：python demo_dashboard.py
回放模式：python demo_dashboard.py --replay
浏览器打开：http://localhost:5001

【演讲建议】
1. 提前在课室用"普通模式"跑一次，录下真实数据（自动保存）
2. 演讲时切换到"回放模式"，3倍速60秒内播完，无需等待
"""

import subprocess, threading, time, sys, os, re, json
from flask import Flask, Response, render_template_string

# ── 配置 ─────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MOCK_SERVER   = os.path.join(BASE_DIR, "team", "mock-server", "app.py")
ARAT_RL       = os.path.join(BASE_DIR, "arat-rl.py")
SPEC_FILE     = os.path.join(BASE_DIR, "spec", "features.yaml")
TARGET_URL    = "http://localhost:8080/"
DEMO_DURATION = 600    # 实际运行秒数（600s≈130次迭代，Q值分叉更明显）
REPLAY_SPEED  = 10     # 回放倍速：600s ÷ 10 = 60s 播完，演讲 Demo 黄金时长
RECORD_FILE   = os.path.join(BASE_DIR, "team", "results", "raw", "demo_recording.json")
IS_REPLAY     = "--replay" in sys.argv

# ── 全局状态 ─────────────────────────────────────────────
state = {
    "status": "ready", "iter":0, "ok":0, "err":0, "s500":0, "elapsed":0,
    "logs":[], "status_codes":{"201":0,"200":0,"404":0,"409":0,"500":0},
    "chain":[False,False,False,False], "q_history":[], "mode": "replay" if IS_REPLAY else "live",
    "error_msg": "",   # ← 修复：必须初始化，否则 SSE 生成器报 KeyError 导致页面无数据
}
state_lock = threading.Lock()
mock_proc = arat_proc = None

# ── Mock Server ───────────────────────────────────────────
def start_mock_server():
    global mock_proc
    print("[Dashboard] 启动 Mock Server...")
    env = os.environ.copy(); env["PYTHONIOENCODING"] = "utf-8"
    mock_proc = subprocess.Popen([sys.executable, MOCK_SERVER],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    time.sleep(2)
    print("[Dashboard] Mock Server 就绪 → http://localhost:8080")

# ── 核心解析逻辑（供实时和录制共用） ─────────────────────
def apply_event(ev, qv):
    """把一条事件写入 state，返回更新后的 qv"""
    code   = ev["code"]
    path   = ev["path"]
    method = ev["method"]
    is_ok  = 200 <= code < 300
    is_500 = code == 500

    mark = "✓" if is_ok else ("💥 500!" if is_500 else "✗")

    # Q 值
    if is_ok:
        qv["post"] = round(max(-2.0, qv["post"] - 0.2), 2)
        qv["get"]  = round(min(3.0,  qv["get"]  + 0.1), 2)
    else:
        qv["post"] = round(min(3.0,  qv["post"] + 0.3), 2)
    if "configurations" in path and "features" not in path and is_ok:
        qv["cfg"]  = round(min(3.0,  qv["cfg"]  + 0.4), 2)
    if "features" in path and method == "POST" and is_ok:
        qv["feat"] = round(min(3.0,  qv["feat"] + 0.5), 2)
    if is_500:
        qv["feat"] = round(min(3.0,  qv["feat"] + 0.8), 2)

    with state_lock:
        chain = state["chain"][:]
        if method == "POST" and "configurations" not in path and "features" not in path and is_ok:
            chain[0] = True
        if method == "POST" and "configurations" in path and "features" not in path and is_ok:
            chain[1] = True
        if method == "POST" and "features" in path and is_ok:
            chain[2] = True
        if method == "GET" and "features" in path and is_ok:
            chain[3] = True

        if is_ok: state["ok"]   += 1
        else:     state["err"]  += 1
        if is_500: state["s500"] += 1
        state["iter"] = ev["iter"] + 1
        state["elapsed"] = ev["elapsed"]

        ck = str(code)
        if ck in state["status_codes"]: state["status_codes"][ck] += 1

        state["logs"].append({"iter":ev["iter"],"method":method,"path":path,"code":code,"mark":mark})
        if len(state["logs"]) > 300: state["logs"] = state["logs"][-300:]
        state["chain"] = chain
        state["q_history"].append({"iter":ev["iter"],**qv})
        if len(state["q_history"]) > 80: state["q_history"] = state["q_history"][-80:]

    return qv

# ── 实时模式：运行 ARAT-RL 并录制 ────────────────────────
def parse_and_run():
    global arat_proc
    with state_lock:
        state.update({"status":"running","iter":0,"ok":0,"err":0,"s500":0,
                      "elapsed":0,"logs":[],"chain":[False,False,False,False],
                      "q_history":[],"status_codes":{"201":0,"200":0,"404":0,"409":0,"500":0}})

    env = os.environ.copy(); env["PYTHONIOENCODING"] = "utf-8"
    arat_proc = subprocess.Popen(
        [sys.executable, ARAT_RL, SPEC_FILE, TARGET_URL, str(DEMO_DURATION)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace", bufsize=1, env=env)

    current_iter = current_method = None
    start_ts = time.time()
    qv = {"post":0.5,"get":0.2,"cfg":0.1,"feat":0.1}
    recording = []   # 用于录制

    for raw in arat_proc.stdout:
        line = raw.rstrip()
        elapsed = round(time.time() - start_ts, 1)

        m = re.match(r'\[Iter\s+(\d+)\]\s+OP:\s+(\w+)\s+(.+)', line)
        if m:
            current_iter   = int(m.group(1))
            current_method = m.group(2).upper()
            continue

        if current_iter is not None and '|' in line and 'path:' in line:
            cm = re.search(r'\b(\d{3})\b', line)
            pm = re.search(r'path:\s*(\S+)', line)
            if cm and pm:
                ev = {"iter":current_iter,"method":current_method,
                      "path":pm.group(1),"code":int(cm.group(1)),"elapsed":elapsed}
                recording.append(ev)
                qv = apply_event(ev, qv)
                current_iter = None

    arat_proc.wait()

    # 保存录制文件
    try:
        os.makedirs(os.path.dirname(RECORD_FILE), exist_ok=True)
        with open(RECORD_FILE, "w", encoding="utf-8") as f:
            json.dump({"duration":DEMO_DURATION,"events":recording}, f, ensure_ascii=False, indent=2)
        print(f"[Dashboard] 录制已保存 → {RECORD_FILE}")
    except Exception as e:
        print(f"[Dashboard] 保存录制失败: {e}")

    with state_lock:
        state["status"] = "done"
    print("[Dashboard] ARAT-RL 完成。")

# ── 回放模式：读取录制文件快速播放 ───────────────────────
def replay_recording():
    if not os.path.exists(RECORD_FILE):
        with state_lock:
            state["status"] = "error"
            state["error_msg"] = f"找不到录制文件：{RECORD_FILE}\n请先用普通模式跑一次。"
        print("[Dashboard] 错误：找不到录制文件，请先普通模式运行一次。")
        return

    with open(RECORD_FILE, encoding="utf-8") as f:
        rec = json.load(f)

    events   = rec["events"]
    duration = rec.get("duration", DEMO_DURATION)

    with state_lock:
        state.update({"status":"running","iter":0,"ok":0,"err":0,"s500":0,
                      "elapsed":0,"logs":[],"chain":[False,False,False,False],
                      "q_history":[],"status_codes":{"201":0,"200":0,"404":0,"409":0,"500":0}})

    qv = {"post":0.5,"get":0.2,"cfg":0.1,"feat":0.1}
    prev_ts = 0.0

    print(f"[Dashboard] 回放模式，共 {len(events)} 条事件，{REPLAY_SPEED}x 倍速...")

    for ev in events:
        gap = (ev["elapsed"] - prev_ts) / REPLAY_SPEED
        if gap > 0:
            time.sleep(gap)
        prev_ts = ev["elapsed"]
        qv = apply_event(ev, qv)

    with state_lock:
        state["status"] = "done"
    print("[Dashboard] 回放完成。")

# ── Flask ─────────────────────────────────────────────────
app = Flask(__name__)


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>ARAT-RL Demo Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:#060F1E;color:#C8DCF0;padding:18px 22px;font-size:16px}

/* ── 顶栏 ── */
.top-title{font-size:26px;font-weight:800;color:#FFFFFF;letter-spacing:-.5px}
.top-bar{display:flex;align-items:center;gap:14px;margin-bottom:4px}
.top-sub{font-size:17px;font-weight:600;color:#A8C8E8;margin-bottom:14px;letter-spacing:.2px}
.badge{font-size:13px;font-weight:800;padding:5px 18px;border-radius:20px;
       display:inline-block;letter-spacing:.2px}
.badge.ready  {background:#0D2035;color:#5A8CAA}
.badge.running{background:#053322;color:#3DCCA0}
.badge.done   {background:#0B3006;color:#78D44E}
.badge.error  {background:#3A0A12;color:#F07088}
.mode-tag{font-size:13px;font-weight:800;padding:5px 16px;border-radius:20px}
.mode-tag     {background:#2A1A00;color:#F5BC45}
.mode-tag.live{background:#0A2040;color:#5BB0F0}

/* ── 控制 ── */
.ctrl-row{display:flex;align-items:center;gap:12px;margin:12px 0}
.btn{padding:11px 30px;border-radius:10px;border:none;cursor:pointer;
     font-size:16px;font-weight:800;transition:all .18s}
.btn-start{background:#1568BE;color:#FFFFFF}
.btn-start:hover{background:#0E4F99}
.btn-start:disabled{background:#0D2035;color:#3A6080;cursor:not-allowed}
.btn-reset{background:#0D2035;color:#7AAAC8}
.btn-reset:hover{background:#122840}
.btn-reset:disabled{opacity:.35;cursor:not-allowed}
.timer{font-size:16px;font-weight:700;color:#5A8CAA;margin-left:auto;
       font-variant-numeric:tabular-nums;letter-spacing:.3px}

/* ── 进度条 ── */
.pbar-wrap{height:8px;background:#0D2035;border-radius:4px;margin-bottom:18px;overflow:hidden}
.pbar{height:100%;background:#1568BE;border-radius:4px;transition:width .6s linear;width:0%}

/* ── 指标卡 ── */
.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px}
.metric{background:#0C1E33;border-radius:12px;padding:16px 20px;
        border:1.5px solid #142840}
.metric-label{font-size:13px;color:#5A8CAA;margin-bottom:10px;font-weight:700;
              text-transform:uppercase;letter-spacing:.8px}
.metric-value{font-size:38px;font-weight:900;line-height:1}
.c-white{color:#FFFFFF}
.c-green{color:#3DCCA0}
.c-red  {color:#F07088}
.c-amber{color:#F5BC45}
.c-blue {color:#5BB0F0}

/* ── 面판 ── */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.panel{background:#0C1E33;border-radius:14px;padding:18px 20px;border:1.5px solid #142840}
.panel-title{font-size:15px;font-weight:800;color:#CADDEE;
             text-transform:uppercase;letter-spacing:.6px;
             margin-bottom:14px;padding-bottom:10px;
             border-bottom:2px solid #1A3550}

/* ── 日志框 ── */
.log-box{height:290px;overflow-y:auto;font-family:'Courier New',monospace;
         font-size:14px;line-height:1;background:#060F1E;
         border-radius:10px;padding:10px 12px;
         scrollbar-width:thin;scrollbar-color:#1A3550 transparent}
.log-box::-webkit-scrollbar{width:6px}
.log-box::-webkit-scrollbar-track{background:transparent}
.log-box::-webkit-scrollbar-thumb{background:#1A3550;border-radius:3px}

.log-line{padding:5px 0;border-bottom:1px solid #0E2235;
          display:flex;align-items:baseline;gap:8px;min-height:28px}
.log-line:last-child{border:none}
.log-iter{font-size:12px;color:#3A6080;flex-shrink:0;font-weight:700;
          width:38px;text-align:right}
.log-tag{display:inline-block;font-size:11px;padding:2px 7px;border-radius:4px;
         font-weight:800;flex-shrink:0}
.tag-POST  {background:#0E3A6A;color:#70C0FF}
.tag-GET   {background:#073A20;color:#5FDD9A}
.tag-DELETE{background:#3A1008;color:#FFB090}
.tag-PUT   {background:#3A2A00;color:#FFD070}
.log-path{font-size:13px;color:#A8C8E8;white-space:nowrap;
          overflow:hidden;text-overflow:ellipsis;flex:1;min-width:0}
.log-code{font-size:13px;font-weight:800;flex-shrink:0;margin-left:auto;padding-left:8px}
.c-ok {color:#3DCCA0}
.c-err{color:#F07088}
.c-500{color:#F5BC45}

/* ── 依赖链 ── */
.chain-step{display:flex;align-items:center;gap:12px;padding:11px 14px;
            border-radius:10px;margin-bottom:8px;border:1.5px solid #142840;
            background:#060F1E;transition:all .5s}
.chain-step.done  {background:#053322;border-color:#1D9060}
.chain-step.active{background:#0A1E3A;border-color:#1568BE}
.chain-num{width:28px;height:28px;border-radius:50%;display:flex;
           align-items:center;justify-content:center;font-size:13px;
           font-weight:900;flex-shrink:0}
.chain-num.pending{background:#0D2035;color:#3A6080}
.chain-num.done   {background:#1D9060;color:#FFFFFF}
.chain-num.active {background:#1568BE;color:#FFFFFF}
.chain-label{font-size:15px;font-weight:800;color:#DDEEFF}
.chain-sub  {font-size:13px;color:#5A8CAA;margin-top:2px}

/* ── 图例 ── */
.legend{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:10px;
        font-size:13px;color:#7AAAC8;font-weight:600}
.legend-dot{width:12px;height:12px;border-radius:3px;display:inline-block;
            margin-right:5px;vertical-align:middle}
.chart-wrap{position:relative;height:145px}
.schart-wrap{position:relative;height:115px}

/* ── 错误框 ── */
.error-box{background:#200810;border:1.5px solid #6D2E46;border-radius:10px;
           padding:18px;color:#F4C0D1;font-size:15px;line-height:1.8;
           white-space:pre-wrap;margin-bottom:14px}
</style>
</head>
<body>
<div class="top-bar">
  <span class="top-title">ARAT-RL Demo Dashboard</span>
  <span class="badge ready" id="badge">待机</span>
  <span class="mode-tag {{mode_cls}}">{{mode_label}}</span>
</div>
<p class="top-sub">ASE 2023 &nbsp;·&nbsp; Adaptive REST API Testing with Reinforcement Learning &nbsp;·&nbsp; CS112 课程演示</p>

<div id="error-area"></div>

<div class="ctrl-row">
  <button class="btn btn-start" id="btn-start" onclick="startDemo()">▶&nbsp; {{btn_label}}</button>
  <button class="btn btn-reset" id="btn-reset" onclick="resetDemo()" disabled>↺&nbsp; 重置</button>
  <span class="timer" id="timer">0 / {{duration}}s</span>
</div>
<div class="pbar-wrap"><div class="pbar" id="pbar"></div></div>

<div class="metrics">
  <div class="metric">
    <div class="metric-label">总迭代数</div>
    <div class="metric-value c-white" id="m-iter">0</div>
  </div>
  <div class="metric">
    <div class="metric-label">成功 &nbsp;2xx</div>
    <div class="metric-value c-green" id="m-ok">0</div>
  </div>
  <div class="metric">
    <div class="metric-label">失败 &nbsp;4xx</div>
    <div class="metric-value c-red" id="m-err">0</div>
  </div>
  <div class="metric">
    <div class="metric-label">发现 500</div>
    <div class="metric-value c-amber" id="m-500">0</div>
  </div>
  <div class="metric">
    <div class="metric-label">已耗时</div>
    <div class="metric-value c-blue" id="m-time">0s</div>
  </div>
</div>

<div class="two-col">
  <div class="panel">
    <div class="panel-title">实时请求日志</div>
    <div class="log-box" id="log-box"></div>
  </div>
  <div class="panel">
    <div class="panel-title">Producer-Consumer 依赖链（RL 自动发现）</div>
    <div id="chain-wrap">
      <div class="chain-step" id="cs-0">
        <div class="chain-num pending" id="ci-0">1</div>
        <div>
          <div class="chain-label">POST &nbsp;/products/{name}</div>
          <div class="chain-sub">创建产品 &mdash; Producer</div>
        </div>
      </div>
      <div class="chain-step" id="cs-1">
        <div class="chain-num pending" id="ci-1">2</div>
        <div>
          <div class="chain-label">POST &nbsp;/products/{name}/configurations/{cfg}</div>
          <div class="chain-sub">创建配置 &mdash; Consumer of Step 1</div>
        </div>
      </div>
      <div class="chain-step" id="cs-2">
        <div class="chain-num pending" id="ci-2">3</div>
        <div>
          <div class="chain-label">POST &nbsp;.../features/{featureName}</div>
          <div class="chain-sub">添加特性 &mdash; Consumer of Step 2</div>
        </div>
      </div>
      <div class="chain-step" id="cs-3">
        <div class="chain-num pending" id="ci-3">4</div>
        <div>
          <div class="chain-label">GET &nbsp;.../features</div>
          <div class="chain-sub">查询结果 &mdash; RL 学习完成 ✓</div>
        </div>
      </div>
    </div>
    <div style="margin-top:16px">
      <div class="panel-title">Q 值变化（操作优先级动态调整）</div>
      <div class="legend">
        <span><span class="legend-dot" style="background:#5BB0F0"></span>POST /products</span>
        <span><span class="legend-dot" style="background:#3DCCA0"></span>GET /features</span>
        <span><span class="legend-dot" style="background:#F5BC45"></span>POST /configs</span>
        <span><span class="legend-dot" style="background:#F07088"></span>POST /features</span>
      </div>
      <div class="chart-wrap">
        <canvas id="qchart" role="img" aria-label="Q值变化折线图，显示各操作优先级随迭代动态变化"></canvas>
      </div>
    </div>
  </div>
</div>

<div class="panel">
  <div class="panel-title">HTTP 状态码分布（实时统计）</div>
  <div class="schart-wrap">
    <canvas id="schart" role="img" aria-label="HTTP状态码分布柱状图"></canvas>
  </div>
</div>

<script>
const DURATION = {{duration}};
let evtSource = null, lastLogs = 0;

const qChart = new Chart(document.getElementById('qchart').getContext('2d'), {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      {data:[], borderColor:'#5BB0F0', backgroundColor:'transparent', tension:.4, pointRadius:0, borderWidth:3},
      {data:[], borderColor:'#3DCCA0', backgroundColor:'transparent', tension:.4, pointRadius:0, borderWidth:3},
      {data:[], borderColor:'#F5BC45', backgroundColor:'transparent', tension:.4, pointRadius:0, borderWidth:3},
      {data:[], borderColor:'#F07088', backgroundColor:'transparent', tension:.4, pointRadius:0, borderWidth:3},
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: {legend: {display: false}},
    scales: {
      x: {display: false},
      y: {
        min: -2, max: 3.5,
        ticks: {color:'#5A8CAA', font:{size:12}, stepSize:1},
        grid:  {color:'rgba(255,255,255,.05)'}
      }
    },
    animation: {duration: 200}
  }
});

const scChart = new Chart(document.getElementById('schart').getContext('2d'), {
  type: 'bar',
  data: {
    labels: ['201 Created','200 OK','404 Not Found','409 Conflict','500 Error'],
    datasets: [{
      data: [0,0,0,0,0],
      backgroundColor: ['#1568BE','#1D9060','#8A5010','#3A3A3A','#8A1030'],
      borderRadius: 6,
      barThickness: 38,
    }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: {legend: {display: false}},
    scales: {
      x: {ticks: {color:'#A8C8E8', font:{size:13}}, grid: {display:false}},
      y: {ticks: {color:'#5A8CAA', font:{size:12}, stepSize:1}, grid: {color:'rgba(255,255,255,.05)'}}
    },
    animation: {duration: 150}
  }
});

function makeTag(m) {
  return `<span class="log-tag tag-${m}">${m}</span>`;
}

function truncPath(p, max) {
  return p.length > max ? '...' + p.slice(-(max-3)) : p;
}

function update(d) {
  document.getElementById('m-iter').textContent = d.iter;
  document.getElementById('m-ok').textContent   = d.ok;
  document.getElementById('m-err').textContent  = d.err;
  document.getElementById('m-500').textContent  = d.s500;
  document.getElementById('m-time').textContent = d.elapsed + 's';
  document.getElementById('timer').textContent  = d.elapsed + ' / ' + DURATION + 's';
  document.getElementById('pbar').style.width   = Math.min(100, d.elapsed / DURATION * 100) + '%';

  const b = document.getElementById('badge');
  b.textContent = {ready:'待机', running:'运行中', done:'完成', error:'错误'}[d.status] || d.status;
  b.className   = 'badge ' + d.status;

  if (d.status === 'error') {
    document.getElementById('error-area').innerHTML =
      '<div class="error-box">' + d.error_msg + '</div>';
    document.getElementById('btn-start').disabled = false;
    document.getElementById('btn-reset').disabled = false;
    if (evtSource) { evtSource.close(); evtSource = null; }
    return;
  }

  // ── 追加日志（单行，路径截断不换行）
  const box = document.getElementById('log-box');
  d.logs.slice(lastLogs).forEach(l => {
    lastLogs++;
    const div = document.createElement('div');
    div.className = 'log-line';
    const cls  = l.code >= 200 && l.code < 300 ? 'c-ok' : l.code === 500 ? 'c-500' : 'c-err';
    const mark = l.code >= 200 && l.code < 300 ? '✓' : l.code === 500 ? '500!' : '✗';
    div.innerHTML =
      `<span class="log-iter">[${String(l.iter).padStart(3,'0')}]</span>` +
      makeTag(l.method) +
      `<span class="log-path" title="${l.path}">${truncPath(l.path, 48)}</span>` +
      `<span class="log-code ${cls}">${l.code} ${mark}</span>`;
    box.appendChild(div);
  });
  box.scrollTop = box.scrollHeight;

  // ── 依赖链
  d.chain.forEach((done, i) => {
    const cs = document.getElementById(`cs-${i}`);
    const ci = document.getElementById(`ci-${i}`);
    if (done) {
      cs.className = 'chain-step done';
      ci.className = 'chain-num done';
      ci.textContent = '✓';
    } else if (d.status === 'running' && i === d.chain.findIndex(x => !x)) {
      cs.className = 'chain-step active';
      ci.className = 'chain-num active';
    }
  });

  // ── Q 值折线图
  if (d.q_history.length > 0) {
    qChart.data.labels = d.q_history.map(q => q.iter);
    ['post','get','cfg','feat'].forEach((k, i) => {
      qChart.data.datasets[i].data = d.q_history.map(q => q[k]);
    });
    qChart.update('none');
  }

  // ── 状态码柱状图
  const sc = d.status_codes;
  scChart.data.datasets[0].data = [sc['201'], sc['200'], sc['404'], sc['409'], sc['500']];
  scChart.update('none');

  if (d.status === 'done') {
    document.getElementById('btn-start').disabled = true;
    document.getElementById('btn-reset').disabled = false;
    document.getElementById('pbar').style.width      = '100%';
    document.getElementById('pbar').style.background = '#1D9060';
    [0,1,2,3].forEach(i => {
      document.getElementById(`cs-${i}`).className = 'chain-step done';
      const ci = document.getElementById(`ci-${i}`);
      ci.className = 'chain-num done';
      ci.textContent = '✓';
    });
    if (evtSource) { evtSource.close(); evtSource = null; }
  }
}

function startDemo() {
  document.getElementById('btn-start').disabled = true;
  document.getElementById('btn-reset').disabled = false;
  document.getElementById('error-area').innerHTML = '';
  lastLogs = 0;
  fetch('/api/start').then(r => r.json()).then(d => {
    if (d.status !== 'ok') {
      alert('启动失败：' + d.msg);
      document.getElementById('btn-start').disabled = false;
      return;
    }
    evtSource = new EventSource('/api/stream');
    evtSource.onmessage = e => { try { update(JSON.parse(e.data)); } catch(ex) {} };
    evtSource.onerror   = () => {
      setTimeout(() => { if (evtSource) { evtSource.close(); evtSource = null; } }, 1000);
    };
  });
}

function resetDemo() {
  if (evtSource) { evtSource.close(); evtSource = null; }
  fetch('/api/reset').then(() => location.reload());
}
</script>
</body>
</html>"""


@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML,
        duration   = DEMO_DURATION,
        mode_cls   = "live" if not IS_REPLAY else "",
        mode_label = f"实时模式（录制中）" if not IS_REPLAY else f"回放模式 {REPLAY_SPEED}x",
        btn_label  = "开始录制运行" if not IS_REPLAY else f"开始回放（{REPLAY_SPEED}x 倍速）",
    )

@app.route('/api/start')
def api_start():
    global mock_proc
    try:
        if IS_REPLAY:
            t = threading.Thread(target=replay_recording, daemon=True)
        else:
            if mock_proc is None or mock_proc.poll() is not None:
                start_mock_server()
            t = threading.Thread(target=parse_and_run, daemon=True)
        t.start()
        return json.dumps({"status":"ok"})
    except Exception as e:
        return json.dumps({"status":"error","msg":str(e)})

@app.route('/api/stream')
def api_stream():
    def gen():
        while True:
            with state_lock:
                payload = json.dumps({k: state[k] for k in
                    ["status","iter","ok","err","s500","elapsed",
                     "logs","chain","q_history","status_codes","error_msg"]})
            yield f"data: {payload}\n\n"
            if state["status"] in ("done","error"): break
            time.sleep(0.4)
    return Response(gen(), mimetype='text/event-stream',
                    headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@app.route('/api/reset')
def api_reset():
    global mock_proc, arat_proc
    try:
        if arat_proc and arat_proc.poll() is None: arat_proc.terminate()
        if mock_proc  and mock_proc.poll()  is None: mock_proc.terminate()
    except: pass
    mock_proc = arat_proc = None
    with state_lock:
        state.update({"status":"ready","iter":0,"ok":0,"err":0,"s500":0,
                      "elapsed":0,"logs":[],"chain":[False,False,False,False],
                      "q_history":[],"status_codes":{"201":0,"200":0,"404":0,"409":0,"500":0},"error_msg":""})
    return json.dumps({"status":"ok"})

if __name__ == '__main__':
    mode = "回放模式" if IS_REPLAY else "实时模式（录制）"
    print("=" * 52)
    print(f"  ARAT-RL Demo Dashboard  [{mode}]")
    print("=" * 52)
    if IS_REPLAY:
        print(f"  录制文件 : {RECORD_FILE}")
        print(f"  回放倍速 : {REPLAY_SPEED}x（约 {DEMO_DURATION//REPLAY_SPEED}s 播完）")
    else:
        print(f"  运行时长 : {DEMO_DURATION}s")
        print(f"  录制保存 : {RECORD_FILE}")
    print("=" * 52)
    print("  浏览器打开 → http://localhost:5001")
    print("=" * 52)
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
