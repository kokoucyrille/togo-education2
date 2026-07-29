"""
utils/graph_utils.py
=====================
Théorie des graphes appliquée au système Formation ↔ Territoire ↔ Emploi (§10 du
notebook). Quatre graphes : bipartite Région↔Catégorie, hiérarchique territorial
Région→Préfecture, Établissements↔Villes (PageRank + Louvain), et le graphe global
multi-niveaux interactif (pyvis).
"""
from typing import Dict

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import REGIONS, REGION_COLORS
from utils.preprocessing import clean_etablissements, clean_repartition_sup

try:
    from community import community_louvain
except ImportError:  # pragma: no cover
    community_louvain = None


@st.cache_resource(show_spinner=False)
def build_graph_region_categorie():
    """Graphe bipartite Région ↔ Catégorie de formation, pondéré par le nombre
    d'établissements. Retourne (G1, centralities)."""
    df_etab = clean_etablissements()
    G1 = nx.Graph()
    for r in REGIONS:
        G1.add_node(r, bipartite=0, kind="region")
    categories = df_etab["etablissement_categorie"].dropna().unique()
    for c in categories:
        G1.add_node(c, bipartite=1, kind="categorie")

    edge_weights = df_etab.dropna(subset=["etablissement_categorie"]).groupby(
        ["region_nom_bdd", "etablissement_categorie"]).size()
    for (r, c), w in edge_weights.items():
        G1.add_edge(r, c, weight=int(w))

    centralities = pd.DataFrame({
        "degree": nx.degree_centrality(G1),
        "betweenness": nx.betweenness_centrality(G1, weight="weight"),
        "closeness": nx.closeness_centrality(G1),
        "eigenvector": nx.eigenvector_centrality(G1, weight="weight", max_iter=1000),
    }).sort_values("degree", ascending=False)
    centralities["type"] = ["Région" if n in REGIONS else "Catégorie" for n in centralities.index]
    return G1, centralities


def plotly_graph_region_categorie(G1: nx.Graph, centralities: pd.DataFrame) -> go.Figure:
    """Rendu Plotly (interactif) du graphe Région ↔ Catégorie."""
    pos = nx.spring_layout(G1, seed=42, weight="weight", k=0.9)
    edge_x, edge_y = [], []
    for u, v in G1.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_x += [x0, x1, None]; edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color="#adb5bd"), hoverinfo="none")

    node_x, node_y, node_color, node_size, node_text = [], [], [], [], []
    for n in G1.nodes():
        x, y = pos[n]
        node_x.append(x); node_y.append(y)
        node_color.append(REGION_COLORS.get(n, "#495057"))
        node_size.append(30 * centralities.loc[n, "eigenvector"] + 12)
        node_text.append(f"{n}<br>degré: {centralities.loc[n,'degree']:.2f} | betweenness: {centralities.loc[n,'betweenness']:.2f}")

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text", text=list(G1.nodes()), textposition="top center",
        hovertext=node_text, hoverinfo="text",
        marker=dict(color=node_color, size=node_size, line=dict(width=1, color="white")),
    )
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(title="Graphe Région ↔ Catégorie de formation (taille = centralité de vecteur propre)",
                       showlegend=False, height=560, margin=dict(t=60, b=10),
                       xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


@st.cache_resource(show_spinner=False)
def build_graph_territorial():
    """Graphe hiérarchique Togo → Région → Préfecture (§10.2). Retourne (G2, top_prefectures)."""
    df_etab = clean_etablissements()
    G2 = nx.Graph()
    G2.add_node("Togo", level=0)
    for r in REGIONS:
        G2.add_node(r, level=1)
        G2.add_edge("Togo", r)

    for _, row in df_etab.dropna(subset=["prefecture_nom_bdd"]).drop_duplicates(
            subset=["region_nom_bdd", "prefecture_nom_bdd"]).iterrows():
        G2.add_node(row["prefecture_nom_bdd"], level=2)
        G2.add_edge(row["region_nom_bdd"], row["prefecture_nom_bdd"])

    prefecture_deg = df_etab.groupby("prefecture_nom_bdd").size()
    for pref, n_etab in prefecture_deg.items():
        G2.nodes[pref]["nb_etablissements"] = int(n_etab)

    top_prefectures = prefecture_deg.sort_values(ascending=False).head(10)
    return G2, top_prefectures


def plotly_graph_territorial(G2: nx.Graph) -> go.Figure:
    pos = nx.kamada_kawai_layout(G2)
    edge_x, edge_y = [], []
    for u, v in G2.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_x += [x0, x1, None]; edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=0.6, color="#ced4da"), hoverinfo="none")

    node_x, node_y, colors, sizes, texts, labels = [], [], [], [], [], []
    for n in G2.nodes():
        x, y = pos[n]
        node_x.append(x); node_y.append(y)
        lvl = G2.nodes[n].get("level")
        if lvl == 0:
            colors.append("#212529"); sizes.append(28); labels.append(n)
        elif lvl == 1:
            colors.append("#F2C744"); sizes.append(20); labels.append(n)
        else:
            parent_region = next((r for r in REGIONS if r in G2.neighbors(n)), None)
            colors.append(REGION_COLORS.get(parent_region, "#B0A8B9"))
            sizes.append(6 + G2.nodes[n].get("nb_etablissements", 0) * 1.2)
            labels.append("")
        texts.append(f"{n} ({G2.nodes[n].get('nb_etablissements', '')} étab.)" if lvl == 2 else n)

    node_trace = go.Scatter(x=node_x, y=node_y, mode="markers+text", text=labels, textposition="top center",
                             hovertext=texts, hoverinfo="text",
                             marker=dict(color=colors, size=sizes, line=dict(width=1, color="white")))
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(title="Arborescence territoriale Togo → Régions → Préfectures (taille = nb établissements)",
                       showlegend=False, height=620, margin=dict(t=60, b=10),
                       xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


@st.cache_resource(show_spinner=False)
def build_graph_etab_villes():
    """Graphe Établissements ↔ Villes (2018), PageRank + communautés de Louvain (§10.3)."""
    df_repart = clean_repartition_sup()
    G3 = nx.Graph()
    combo = df_repart.copy()
    combo["type_statut"] = combo["type"] + " " + combo["statut"]

    for v in combo["villes"].unique():
        G3.add_node(v, kind="ville")
    for ts in combo["type_statut"].unique():
        G3.add_node(ts, kind="type_statut")

    grouped = combo.groupby(["villes", "type_statut"])["Value"].sum()
    for (v, ts), w in grouped.items():
        if w > 0:
            G3.add_edge(v, ts, weight=float(w))
    G3.remove_nodes_from(list(nx.isolates(G3)))

    pagerank = nx.pagerank(G3, weight="weight")
    if community_louvain is not None:
        partition = community_louvain.best_partition(G3, weight="weight", random_state=42)
    else:
        partition = {n: 0 for n in G3.nodes()}

    result3 = pd.DataFrame({
        "pagerank": pd.Series(pagerank),
        "communaute_louvain": pd.Series(partition),
        "type": ["Ville" if G3.nodes[n]["kind"] == "ville" else "Type×Statut" for n in G3.nodes()],
    }).sort_values("pagerank", ascending=False)
    return G3, pagerank, partition, result3


def plotly_graph_etab_villes(G3: nx.Graph, pagerank: dict, partition: dict) -> go.Figure:
    pos = nx.spring_layout(G3, seed=7, weight="weight", k=1.1)
    edge_x, edge_y = [], []
    for u, v in G3.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_x += [x0, x1, None]; edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=0.8, color="#ced4da"), hoverinfo="none")

    import plotly.colors as pc
    palette = pc.qualitative.Set2 + pc.qualitative.Set3
    node_x, node_y, colors, sizes, texts, symbols = [], [], [], [], [], []
    for n in G3.nodes():
        x, y = pos[n]
        node_x.append(x); node_y.append(y)
        colors.append(palette[partition[n] % len(palette)])
        sizes.append(4000 * pagerank[n] / 2 + 10)
        symbols.append("circle" if G3.nodes[n]["kind"] == "ville" else "square")
        texts.append(f"{n} — PageRank {pagerank[n]:.3f}, communauté {partition[n]}")

    node_trace = go.Scatter(x=node_x, y=node_y, mode="markers+text", text=list(G3.nodes()), textposition="top center",
                             hovertext=texts, hoverinfo="text",
                             marker=dict(color=colors, size=sizes, symbol=symbols, line=dict(width=1, color="black")))
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(title="Graphe Établissements ↔ Villes (2018) — ○ ville, ▢ type×statut, couleur = communauté Louvain, taille = PageRank",
                       showlegend=False, height=600, margin=dict(t=60, b=10),
                       xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


@st.cache_resource(show_spinner=False)
def build_global_pyvis_html() -> str:
    """Construit le grand graphe multi-niveaux interactif (Région → Préfecture →
    Établissement → Catégorie / Secteur estimé) et retourne le HTML pyvis prêt à
    intégrer dans un composant Streamlit."""
    from pyvis.network import Network
    import plotly.express as px

    df_etab = clean_etablissements()
    net = Network(height="720px", width="100%", bgcolor="#ffffff", font_color="#212121",
                  notebook=False, cdn_resources="in_line")
    net.barnes_hut(gravity=-4000, central_gravity=0.3, spring_length=110, spring_strength=0.02, damping=0.9)

    net.add_node("TOGO", label="TOGO", color="#212529", size=40, shape="star", level=0)
    for r in REGIONS:
        net.add_node(r, label=r, color=REGION_COLORS[r], size=32, level=1, title=f"Région : {r}")
        net.add_edge("TOGO", r)

    prefectures_df = df_etab.dropna(subset=["prefecture_nom_bdd"]).drop_duplicates(subset=["prefecture_nom_bdd"])
    for _, row in prefectures_df.iterrows():
        pid = f"PREF::{row['prefecture_nom_bdd']}"
        net.add_node(pid, label=row["prefecture_nom_bdd"], color=REGION_COLORS[row["region_nom_bdd"]],
                     size=16, level=2, title=f"Préfecture : {row['prefecture_nom_bdd']}")
        net.add_edge(row["region_nom_bdd"], pid)

    categories = df_etab["etablissement_categorie"].dropna().unique()
    for c in categories:
        net.add_node(f"CAT::{c}", label=c, color="#495057", size=22, shape="diamond", level=4,
                     title=f"Catégorie de formation : {c}")

    sectors = df_etab["secteur_estime"].unique()
    for s in sectors:
        net.add_node(f"SECT::{s}", label=s, color="#adb5bd", size=18, shape="triangle", level=5,
                     title=f"⚠️ Secteur estimé : {s}")

    for _, row in df_etab.iterrows():
        eid = f"ETAB::{row.name}"
        pid = f"PREF::{row['prefecture_nom_bdd']}" if pd.notna(row["prefecture_nom_bdd"]) else None
        net.add_node(eid, label="", color="#F2C744", size=6, level=3,
                     title=f"{row['etab_nom']} ({row['region_nom_bdd']}, {row['prefecture_nom_bdd']})")
        if pid:
            net.add_edge(pid, eid)
        if pd.notna(row["etablissement_categorie"]):
            net.add_edge(eid, f"CAT::{row['etablissement_categorie']}")
        net.add_edge(eid, f"SECT::{row['secteur_estime']}")

    net.set_options('''
    {
      "layout": {"hierarchical": {"enabled": false}},
      "physics": {"stabilization": {"iterations": 150}},
      "interaction": {"hover": true, "tooltipDelay": 100}
    }
    ''')
    return net.generate_html(notebook=False)
