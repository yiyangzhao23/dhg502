# -*- coding: utf-8 -*-
"""从《明史》文本构建明代重要将领共现网络。

规则：同一行（段落）中出现的将领两两之间建立一条边。
输出：nodes.csv, edges.csv, ming_generals_network.png, ming_generals_network.html
"""
import os
import itertools
import pandas as pd
import networkx as nx
from networkx.algorithms.community import louvain_communities
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from qhchina import load_fonts

TXT = "/Users/cici/Downloads/明史.txt"
OUT = os.path.dirname(os.path.abspath(__file__))

# 明初開國將領（同一時段，共現緊密）
GENERALS = [
    "徐達", "傅友德", "李文忠", "常遇春", "湯和", "藍玉", "馮勝", "鄧愈", "沐英",
    "耿炳文", "胡大海", "周德興", "俞通海", "唐勝宗", "吳良", "顧時", "趙庸",
    "陳德", "陸仲亨", "費聚",
]

# 加载中文字体（由 qhchina 提供并设置 matplotlib rcParams）
load_fonts()

# ---------- 1. 统计 ----------
lines = open(TXT, encoding="utf-8").read().splitlines()

node_freq = {g: 0 for g in GENERALS}
edge_weight = {}

for line in lines:
    present = [g for g in GENERALS if g in line]
    for g in present:
        node_freq[g] += 1
    for a, b in itertools.combinations(present, 2):
        key = tuple(sorted((a, b)))
        edge_weight[key] = edge_weight.get(key, 0) + 1

# ---------- 2. 节点表 / 边表 ----------
G = nx.Graph()
for g in GENERALS:
    G.add_node(g)

edges = []
for (a, b), w in edge_weight.items():
    G.add_edge(a, b, weight=w)
    edges.append({"Source": a, "Target": b, "Weight": w})
edges.sort(key=lambda r: r["Weight"], reverse=True)

# Louvain 社区发现
communities = louvain_communities(G, weight="weight", seed=42)
node_comm = {n: i for i, c in enumerate(communities) for n in c}
print(f"\n=== Louvain 社区（{len(communities)} 个）===")
for i, c in enumerate(communities):
    print(f"  社区 {i}: {sorted(c, key=lambda n: -node_freq[n])}")

# 特征向量中心性（迭代至收敛）
eig = nx.eigenvector_centrality(G, weight="weight", max_iter=1000, tol=1e-9)
e_min, e_max = min(eig.values()), max(eig.values())

nodes = []
for g in GENERALS:
    nodes.append({
        "Id": GENERALS.index(g) + 1,
        "Label": g,
        "Freq": node_freq[g],
        "Degree": G.degree(g),
        "WeightedDegree": sum(d["weight"] for _, _, d in G.edges(g, data=True)),
        "Community": node_comm[g],
        "EigenvectorCentrality": round(eig[g], 4),
    })
nodes_df = pd.DataFrame(nodes)
edges_df = pd.DataFrame(edges)

nodes_df.to_csv(f"{OUT}/nodes.csv", index=False, encoding="utf-8-sig")
edges_df.to_csv(f"{OUT}/edges.csv", index=False, encoding="utf-8-sig")

print("=== 20 位将领（按特征向量中心性）===")
for g in sorted(GENERALS, key=lambda n: -eig[n]):
    print(f"  {g}  特征向量中心性={eig[g]:.4f}  度={G.degree(g):>2}"
          f"  加权度={nodes_df.set_index('Label').loc[g, 'WeightedDegree']:>4}")
print(f"\n节点数={G.number_of_nodes()}  边数={G.number_of_edges()}"
      f"  连通分量={nx.number_connected_components(G)}")
print("\n=== 权重最高的 10 条边 ===")
print(edges_df.head(10).to_string(index=False))
print(f"\n已写出: {OUT}/nodes.csv, {OUT}/edges.csv")

# ---------- 3. 可视化（深色高级风）----------
BG = "#0F141A"          # 深色背景
INK = "#EAF0F6"         # 主文字（浅色）
MUTED = "#9BA6B4"       # 次要文字
PANEL = "#1A212B"       # 面板底色
BORDER = "#2B3542"      # 面板描边
COMMUNITY_COLORS = ["#5B9DF9", "#F2994A", "#4CD4A0", "#B58CF0", "#E6C34A"]
node_colors = [COMMUNITY_COLORS[node_comm[n] % len(COMMUNITY_COLORS)] for n in G.nodes()]

# 节点大小与特征向量中心性成正比（归一化后映射到 [1200, 4200]）
size = [1200 + 3000 * (eig[n] - e_min) / (e_max - e_min or 1) for n in G.nodes()]
width = [0.6 + 2.0 * (G[u][v]["weight"] ** 0.5) for u, v in G.edges()]


def draw_graph(pos, title, subtitle, filename, figsize):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    nx.draw_networkx_edges(G, pos, ax=ax, width=width, alpha=0.42,
                           edge_color="#C7D2DE")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=size, node_color=node_colors,
                           edgecolors=BG, linewidths=2.8)
    for n in G.nodes():
        ax.text(pos[n][0], pos[n][1], n, fontsize=23, fontweight="bold",
                color=INK, ha="center", va="center", zorder=5,
                path_effects=[pe.withStroke(linewidth=2.6, foreground=BG)])

    ax.text(0.5, 1.075, title, transform=ax.transAxes, ha="center",
            va="bottom", fontsize=26, color=INK, fontweight="bold")
    ax.text(0.5, 1.025, subtitle, transform=ax.transAxes, ha="center",
            va="bottom", fontsize=14.5, color=MUTED)

    handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=14,
                          markerfacecolor=COMMUNITY_COLORS[i % len(COMMUNITY_COLORS)],
                          markeredgecolor=BG, markeredgewidth=1.6,
                          label=f"社区 {i}")
               for i in range(len(communities))]
    leg = ax.legend(handles=handles, loc="lower right", fontsize=13, frameon=True,
                    framealpha=0.95, facecolor=PANEL, edgecolor=BORDER,
                    labelcolor=INK, title="Louvain 社區")
    leg.get_title().set_color(INK)
    leg.get_title().set_fontsize(13)

    ax.axis("off")
    ax.margins(0.06)
    fig.tight_layout()
    fig.savefig(f"{OUT}/{filename}", dpi=220, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"已写出: {OUT}/{filename}")


pos = nx.spring_layout(G, k=0.9, seed=42, weight="weight")
draw_graph(pos, "《明史》明初開國將領共現網絡",
           "力導向布局 · 節點大小 = 特徵向量中心性 · 顏色 = Louvain 社區 · 線寬 = 共現次數",
           "ming_generals_network.png", (16, 13))

pos_c = nx.circular_layout(G)
draw_graph(pos_c, "《明史》明初開國將領共現網絡（圓形布局）",
           "節點大小 = 特徵向量中心性 · 顏色 = Louvain 社區 · 線寬 = 共現次數",
           "ming_generals_network_circular.png", (16, 16))

# ---------- 4. 交互式 HTML（节点/边均带说明与属性）----------
DESCRIPTIONS = {
    "徐達": "明初第一名將。濠州人，從朱元璋起兵，官至太傅、中書右丞相，封魏國公。主持北伐滅元，用兵持重，為開國功臣之首。",
    "常遇春": "明朝開國名將，勇猛無敵，自稱能將十萬眾橫行天下，人稱「常十萬」。從徐達北伐，拔采石、克大都，封鄂國公。",
    "李文忠": "朱元璋外甥，明初名將，封曹國公。屢敗張士誠、北征蒙古，戰功卓著，位列開國功臣。",
    "湯和": "明初開國名將，朱元璋同鄉，封信國公。沉敏多智，先後鎮守東南沿海抗倭，為明初長壽宿將。",
    "鄧愈": "明初名將，封衛國公。少年起兵，驍勇善戰，從征陳友諒、北伐中原，屢立戰功。",
    "沐英": "朱元璋養子，明初名將，封西平侯，追封黔寧王。平定雲南、鎮守滇黔，沐氏世鎮雲南。",
    "馮勝": "明初名將，封宋國公。從徐達北伐，征討遼東、甘肅，功勳卓著，後因故賜死。",
    "傅友德": "明初名將，封潁國公。北征大漠、南平雲貴，七戰七勝，勇略兼備，為開國宿將。",
    "藍玉": "明初名將，常遇春妻弟，封涼國公。捕魚兒海大破北元，功高震主，後以謀反被誅（藍玉案）。",
    "胡大海": "明初開國名將，封越國公。長身鐵面，智力過人，善用兵，鎮守浙東，後被叛將所殺。",
    "耿炳文": "明初名將，封長興侯。以堅守長興、屢敗張士誠著稱，長於防守，靖難之役統軍北上。",
    "周德興": "明初開國名將，封江夏侯。從朱元璋起兵，平定湖南、廣西，後鎮守福建。",
    "俞通海": "明初水師名將，統巢湖水軍歸附，善水戰，鄱陽湖之戰有功，追封虢國公。",
    "唐勝宗": "明初開國名將，封延安侯。從征陳友諒、北元，屢立戰功，後坐胡惟庸案被誅。",
    "吳良": "明初開國名將，封江陰侯。與弟吳禎鎮守江陰十年，屢挫張士誠，朱元璋贊其「保障一方」。",
    "顧時": "明初開國名將，封濟寧侯。從朱元璋渡江，征陳友諒、張士誠及北伐，勇冠諸軍。",
    "趙庸": "明初開國名將，封南雄侯。從征陳友諒、北伐中原，後平廣東、廣西。",
    "陳德": "明初開國名將，封臨江侯。從朱元璋起兵，征陳友諒、北伐，後戰死於征討。",
    "陸仲亨": "明初開國名將，封吉安侯。從朱元璋起兵，戰功卓著，後因胡惟庸案被誅。",
    "費聚": "明初開國名將，封平涼侯。早年隨朱元璋定遠起兵，後鎮守雲南。",
}

try:
    from pyvis.network import Network

    # 每条边取一个示例段落（两将共同出现）
    edge_example = {}
    for line in lines:
        present = [g for g in GENERALS if g in line]
        for a, b in itertools.combinations(present, 2):
            k = tuple(sorted((a, b)))
            edge_example.setdefault(k, line.strip())

    net = Network(height="900px", width="100%", bgcolor=BG,
                  font_color=INK, directed=False)

    # 采用与 PNG 一致的 networkx 力导向（spring）布局坐标
    SPREAD = 700
    spring_pos = nx.spring_layout(G, k=0.9, seed=42, weight="weight")

    for _, r in nodes_df.iterrows():
        n = r["Label"]
        c = COMMUNITY_COLORS[int(r["Community"]) % len(COMMUNITY_COLORS)]
        tip = (
            f"<div style='max-width:320px;font-family:PingFang SC,Microsoft YaHei,sans-serif;"
            f"background:{PANEL};border:1px solid {BORDER};border-radius:10px;"
            f"padding:10px 13px;color:{INK}'>"
            f"<div style='font-size:16px;font-weight:700;color:{INK};margin-bottom:6px'>{n}</div>"
            f"<div style='color:#C7D2DE;line-height:1.55'>{DESCRIPTIONS.get(n, '')}</div>"
            f"<hr style='border:none;border-top:1px solid {BORDER};margin:8px 0'>"
            f"<div style='color:#C7D2DE;line-height:1.6'>"
            f"出現行數：<b>{int(r['Freq'])}</b><br>"
            f"度（相連將領數）：<b>{int(r['Degree'])}</b><br>"
            f"加權度（共現總次數）：<b>{int(r['WeightedDegree'])}</b><br>"
            f"特徵向量中心性：<b>{r['EigenvectorCentrality']}</b><br>"
            f"Louvain 社區：<b>{int(r['Community'])}</b></div></div>"
        )
        net.add_node(n, label=n, title=tip, value=float(r["EigenvectorCentrality"]) * 100,
                     color={"background": c, "border": BG}, borderWidth=2.5,
                     x=spring_pos[n][0] * SPREAD, y=-spring_pos[n][1] * SPREAD,
                     font={"size": 22, "face": "PingFang SC", "color": INK})

    for _, r in edges_df.iterrows():
        k = tuple(sorted((r["Source"], r["Target"])))
        ex = edge_example.get(k, "")
        if len(ex) > 80:
            ex = ex[:80] + "…"
        tip = (
            f"<div style='max-width:340px;font-family:PingFang SC,Microsoft YaHei,sans-serif;"
            f"background:{PANEL};border:1px solid {BORDER};border-radius:10px;"
            f"padding:10px 13px;color:{INK}'>"
            f"<div style='font-size:15px;font-weight:700;color:{INK}'>"
            f"{r['Source']} — {r['Target']}</div>"
            f"<hr style='border:none;border-top:1px solid {BORDER};margin:8px 0'>"
            f"<div style='color:#C7D2DE;line-height:1.6'>"
            f"共現權重：<b>{int(r['Weight'])}</b> 個段落<br>"
            f"說明：兩將領在《明史》同一段落中共同出現 {int(r['Weight'])} 次。</div>"
            f"<div style='color:#9BA6B4;margin-top:6px;line-height:1.5'>示例：{ex}</div></div>"
        )
        net.add_edge(r["Source"], r["Target"], value=int(r["Weight"]),
                     title=tip, color="rgba(199,210,222,0.55)", width=0.8)

    net.set_options("""{
      "nodes": {"shape": "dot", "scaling": {"min": 12, "max": 55}},
      "edges": {"smooth": {"enabled": true, "type": "dynamic"}},
      "physics": {"enabled": false},
      "interaction": {"hover": true, "tooltipDelay": 60,
                      "navigationButtons": true, "dragNodes": true}
    }""")

    legend = "".join(
        f"<div style='display:flex;align-items:center;gap:8px;margin:4px 0'>"
        f"<span style='width:13px;height:13px;border-radius:50%;background:"
        f"{COMMUNITY_COLORS[i % len(COMMUNITY_COLORS)]};display:inline-block'></span>"
        f"<span>社區 {i}</span></div>"
        for i in range(len(communities))
    )
    overlay = (
        "<style>.vis-tooltip{background:transparent!important;border:none!important;"
        "box-shadow:none!important;padding:0!important;}</style>"
        f"<div style='position:absolute;top:16px;left:16px;z-index:9;"
        f"font-family:PingFang SC,Microsoft YaHei,sans-serif;color:{INK}'>"
        f"<div style='font-size:20px;font-weight:700'>《明史》明初開國將領共現網絡</div>"
        f"<div style='font-size:12.5px;color:{MUTED};margin-top:2px'>"
        f"力導向（spring）布局 · 節點大小＝特徵向量中心性 · 顏色＝Louvain 社區 · 連線粗細＝共現次數</div></div>"
        f"<div style='position:absolute;top:16px;right:16px;z-index:9;"
        f"background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:10px 14px;"
        f"font-family:PingFang SC,Microsoft YaHei,sans-serif;font-size:13px;color:{INK};"
        f"box-shadow:0 6px 18px rgba(0,0,0,0.45)'>"
        f"<div style='font-weight:700;margin-bottom:6px'>Louvain 社區</div>{legend}</div>"
        f"<div style='position:absolute;bottom:14px;left:16px;z-index:9;"
        f"font-family:PingFang SC,Microsoft YaHei,sans-serif;font-size:12.5px;color:{MUTED}'>"
        f"提示：滑鼠移到節點／連線可查看簡介、屬性與共現權重；節點可拖動。</div>"
    )
    html = net.generate_html(notebook=False).replace("<body>", "<body>" + overlay, 1)
    with open(f"{OUT}/ming_generals_network.html", "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"已写出: {OUT}/ming_generals_network.html")
except ImportError:
    print("（未安装 pyvis，跳过交互式 HTML）")
