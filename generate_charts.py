import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

os.makedirs("team/results/figures", exist_ok=True)

# ── 数据来源：论文 Table I & II ──────────────────────────
services = ["Features", "LangTool", "NCS", "REST\nCountries",
            "SCS", "Genome\nNexus", "Person\nCtrl", "User\nMgmt",
            "Market", "Project\nTracking"]

# Table I: 各工具生成的请求数 (2xx+500)
requests = {
    "ARAT-RL":    [95479, 77221, 62618, 36297, 115328, 15819, 101083, 44121, 29393, 23958],
    "Morest":     [103475, 1273, 18389, 8431, 110147, 32598, 104226, 1111, 1399, 14906],
    "EvoMaster":  [113136, 22006, 61282, 9842, 66313, 8374, 91316, 29064, 10697, 15073],
    "RESTler":    [4671, 32796, 140, 259, 5858, 182, 167, 79, 1278, 72],
}

# Table I: 覆盖的 operations 数
operations = {
    "ARAT-RL":   [18, 2, 6, 22, 11, 23, 12, 21, 12, 53],
    "Morest":    [18, 1, 5, 22, 11, 23, 11, 17, 6, 42],
    "EvoMaster": [18, 2, 2, 16, 10, 19, 12, 18, 5, 43],
    "RESTler":   [17, 1, 2, 6, 10, 1, 1, 4, 2, 3],
}

# Table II: 各工具发现的 faults 总数（10次运行累计）
faults_total = {
    "ARAT-RL":   [10, 122, 0, 10, 0, 10, 943, 10, 10, 10],
    "Morest":    [10, 0,   0, 10, 0, 5,  274, 8,  10, 10],
    "EvoMaster": [10, 48,  0, 10, 0, 0,  221, 10, 10, 10],
    "RESTler":   [10, 0,   0, 9,  3, 0,  58,  10, 10, 10],
}

# 论文 Table III: Ablation study
ablation_labels = ["ARAT-RL\n(Full)", "No\nPrioritization", "No\nFeedback", "No\nSampling"]
ablation_branch = [36.25, 28.70, 32.69, 34.10]
ablation_line   = [58.47, 53.27, 54.80, 56.39]
ablation_method = [59.42, 55.51, 56.09, 57.20]
ablation_faults = [112.10, 100.10, 110.80, 112.50]

COLORS = {
    "ARAT-RL":   "#2563EB",
    "Morest":    "#16A34A",
    "EvoMaster": "#D97706",
    "RESTler":   "#DC2626",
}

tools = ["ARAT-RL", "Morest", "EvoMaster", "RESTler"]
x = np.arange(len(services))
width = 0.2

# ── 图1: 请求数对比 ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 6))
for i, tool in enumerate(tools):
    vals = [v / 1000 for v in requests[tool]]
    ax.bar(x + i * width, vals, width, label=tool, color=COLORS[tool], alpha=0.85)
ax.set_xlabel("Service", fontsize=12)
ax.set_ylabel("Requests Generated (×1000)", fontsize=12)
ax.set_title("Figure 1: Valid & Fault-Inducing Requests Generated (Table I)", fontsize=13, fontweight='bold')
ax.set_xticks(x + width * 1.5)
ax.set_xticklabels(services, fontsize=9)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig("team/results/figures/fig1_requests.png", dpi=150)
plt.close()
print("Saved fig1_requests.png")

# ── 图2: Operations 覆盖对比 ─────────────────────────────
fig, ax = plt.subplots(figsize=(16, 6))
for i, tool in enumerate(tools):
    ax.bar(x + i * width, operations[tool], width, label=tool, color=COLORS[tool], alpha=0.85)
ax.set_xlabel("Service", fontsize=12)
ax.set_ylabel("Operations Covered", fontsize=12)
ax.set_title("Figure 2: Operations Covered Within 1-Hour Budget (Table I)", fontsize=13, fontweight='bold')
ax.set_xticks(x + width * 1.5)
ax.set_xticklabels(services, fontsize=9)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig("team/results/figures/fig2_operations.png", dpi=150)
plt.close()
print("Saved fig2_operations.png")

# ── 图3: Faults 检测对比 ─────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 6))
for i, tool in enumerate(tools):
    ax.bar(x + i * width, faults_total[tool], width, label=tool, color=COLORS[tool], alpha=0.85)
ax.set_xlabel("Service", fontsize=12)
ax.set_ylabel("Total Faults Detected (10 runs)", fontsize=12)
ax.set_title("Figure 3: Fault Detection Capability (Table II)", fontsize=13, fontweight='bold')
ax.set_xticks(x + width * 1.5)
ax.set_xticklabels(services, fontsize=9)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig("team/results/figures/fig3_faults.png", dpi=150)
plt.close()
print("Saved fig3_faults.png")

# ── 图4: Ablation Study ──────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
bar_x = np.arange(len(ablation_labels))
bar_w = 0.25
ablation_colors = ["#2563EB", "#9333EA", "#EA580C"]

# Coverage
ax = axes[0]
ax.bar(bar_x - bar_w, ablation_branch, bar_w, label="Branch", color=ablation_colors[0], alpha=0.85)
ax.bar(bar_x,         ablation_line,   bar_w, label="Line",   color=ablation_colors[1], alpha=0.85)
ax.bar(bar_x + bar_w, ablation_method, bar_w, label="Method", color=ablation_colors[2], alpha=0.85)
ax.set_ylabel("Coverage (%)", fontsize=12)
ax.set_title("Code Coverage — Ablation Study (Table III)", fontsize=11, fontweight='bold')
ax.set_xticks(bar_x)
ax.set_xticklabels(ablation_labels, fontsize=10)
ax.set_ylim(0, 75)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)

# Faults
ax = axes[1]
bars = ax.bar(bar_x, ablation_faults, 0.5,
              color=["#2563EB", "#94A3B8", "#94A3B8", "#94A3B8"], alpha=0.85)
ax.set_ylabel("Avg Faults Detected", fontsize=12)
ax.set_title("Fault Detection — Ablation Study (Table III)", fontsize=11, fontweight='bold')
ax.set_xticks(bar_x)
ax.set_xticklabels(ablation_labels, fontsize=10)
ax.set_ylim(90, 120)
ax.grid(axis='y', alpha=0.3)
for bar, val in zip(bars, ablation_faults):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{val}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig("team/results/figures/fig4_ablation.png", dpi=150)
plt.close()
print("Saved fig4_ablation.png")

# ── 图5: 平均性能汇总 (雷达图风格 → 用水平条形图替代) ────
fig, ax = plt.subplots(figsize=(10, 5))
avg_metrics = {
    "Avg Requests (×1000)": [60.1, 39.6, 42.7, 4.6],
    "Avg Operations":        [18.0, 15.6, 14.5, 4.7],
    "Avg Faults/run":        [112.5, 32.7, 31.9, 11.0],
}
metric_names = list(avg_metrics.keys())
bar_x = np.arange(len(tools))
offsets = [-0.25, 0, 0.25]
metric_colors = ["#2563EB", "#16A34A", "#DC2626"]

for i, (metric, vals) in enumerate(avg_metrics.items()):
    norm = [v / max(vals) * 100 for v in vals]
    ax.bar(bar_x + offsets[i], norm, 0.22, label=metric, color=metric_colors[i], alpha=0.85)

ax.set_ylabel("Normalized Score (%)", fontsize=12)
ax.set_title("Figure 5: Overall Average Performance (Normalized)", fontsize=13, fontweight='bold')
ax.set_xticks(bar_x)
ax.set_xticklabels(tools, fontsize=12)
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig("team/results/figures/fig5_summary.png", dpi=150)
plt.close()
print("Saved fig5_summary.png")

print("\nAll charts saved to team/results/figures/")
