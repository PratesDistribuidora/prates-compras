import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib
from datetime import date, datetime, timedelta
import io
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib import colors as rl_colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

st.set_page_config(
    page_title="Prates — Guia de Compras",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── TEMA DARK ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* FUNDO GERAL */
[data-testid="stAppViewContainer"] {
    background: #0D1117 !important;
}
[data-testid="stMain"] {
    background: #0D1117 !important;
}
section[data-testid="stSidebar"] {
    background: #161B22 !important;
    border-right: 1px solid #30363D !important;
}
section[data-testid="stSidebar"] * { color: #E6EDF3 !important; }
section[data-testid="stSidebar"] hr { border-color: #30363D !important; }

/* TEXTO GERAL */
p, li, span, label, div { color: #E6EDF3; }
h1, h2, h3 { color: #F0F6FC !important; }

/* INPUTS */
input, textarea, select {
    background: #21262D !important;
    color: #E6EDF3 !important;
    border: 1px solid #30363D !important;
    border-radius: 6px !important;
}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: #21262D !important;
    color: #E6EDF3 !important;
    border: 1px solid #30363D !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #21262D !important;
    color: #E6EDF3 !important;
    border: 1px solid #30363D !important;
}

/* BOTÕES */
[data-testid="stButton"] > button {
    background: #21262D !important;
    color: #E6EDF3 !important;
    border: 1px solid #30363D !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] > button:hover {
    background: #30363D !important;
    border-color: #58A6FF !important;
    color: #58A6FF !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: #238636 !important;
    color: white !important;
    border-color: #2EA043 !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #2EA043 !important;
}

/* CARDS */
.card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
}
.card-kpi {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1.3rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.card-kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #238636);
}
.kpi-value {
    font-size: 1.7rem;
    font-weight: 700;
    color: #F0F6FC;
    margin: 0.3rem 0;
}
.kpi-label {
    font-size: 0.75rem;
    color: #8B949E;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 500;
}
.kpi-sub {
    font-size: 0.78rem;
    color: #58A6FF;
    margin-top: 0.2rem;
}

/* SEÇÕES */
.sec-header {
    background: #161B22;
    border: 1px solid #30363D;
    border-left: 4px solid var(--sec-color, #238636);
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.sec-title {
    font-size: 1rem;
    font-weight: 600;
    color: #F0F6FC;
}
.sec-meta {
    font-size: 0.8rem;
    color: #8B949E;
}

/* BADGES */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.badge-pendente  { background: rgba(210,153,34,0.15);  color: #D2991E; border: 1px solid #D2991E44; }
.badge-aprovado  { background: rgba(88,166,255,0.15);  color: #58A6FF; border: 1px solid #58A6FF44; }
.badge-comprado  { background: rgba(163,113,247,0.15); color: #A371F7; border: 1px solid #A371F744; }
.badge-entregue  { background: rgba(35,134,54,0.15);   color: #3FB950; border: 1px solid #3FB95044; }
.badge-cancelado { background: rgba(248,81,73,0.15);   color: #F85149; border: 1px solid #F8514944; }

.badge-alta  { background: rgba(248,81,73,0.15);   color: #F85149; border: 1px solid #F8514944; }
.badge-media { background: rgba(210,153,34,0.15);  color: #D2991E; border: 1px solid #D2991E44; }
.badge-baixa { background: rgba(35,134,54,0.15);   color: #3FB950; border: 1px solid #3FB95044; }

/* URGENTE */
.badge-urgente { background: rgba(248,81,73,0.2); color: #F85149;
                 border: 1px solid #F85149; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.6; } }

/* ITEM ROW */
.item-row {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.4rem;
    transition: border-color 0.2s;
}
.item-row:hover { border-color: #58A6FF44; }
.item-nome { font-weight: 600; color: #F0F6FC; font-size: 0.95rem; }
.item-meta { font-size: 0.78rem; color: #8B949E; }

/* SIDEBAR NAV */
.nav-section { font-size: 0.7rem; color: #8B949E; text-transform: uppercase;
               letter-spacing: 0.08em; font-weight: 600; margin: 1rem 0 0.4rem; }

/* EXPANDER */
[data-testid="stExpander"] {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    color: #E6EDF3 !important;
}

/* DATAFRAME */
[data-testid="stDataFrame"] {
    background: #161B22 !important;
}

/* FORM */
[data-testid="stForm"] {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

/* TABS */
[data-testid="stTabs"] [role="tab"] {
    color: #8B949E !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #58A6FF !important;
    border-bottom: 2px solid #58A6FF !important;
}

/* DIVIDER */
hr { border-color: #21262D !important; }

/* ALERT / INFO */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* METRIC */
[data-testid="stMetric"] { background: #161B22; border-radius: 8px; padding: 0.8rem; }

/* SCROLLBAR */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0D1117; }
::-webkit-scrollbar-thumb { background: #30363D; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #58A6FF; }

/* LOGO SIDEBAR */
.sidebar-logo {
    text-align: center;
    padding: 1.5rem 0 1rem;
}
.sidebar-logo .icon { font-size: 2.5rem; }
.sidebar-logo .title { font-size: 1.1rem; font-weight: 700; color: #F0F6FC; margin-top: 0.3rem; }
.sidebar-logo .sub { font-size: 0.75rem; color: #8B949E; }

.user-card {
    background: #0D1117;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0;
}
.user-name { font-weight: 600; font-size: 0.9rem; color: #F0F6FC; }
.user-email { font-size: 0.75rem; color: #8B949E; }
.user-role {
    display: inline-block;
    background: #238636;
    color: white;
    font-size: 0.65rem;
    font-weight: 600;
    padding: 1px 7px;
    border-radius: 20px;
    margin-top: 3px;
}

.titulo-pagina {
    font-size: 1.5rem;
    font-weight: 700;
    color: #F0F6FC;
    margin-bottom: 0.2rem;
}
.subtitulo {
    font-size: 0.85rem;
    color: #8B949E;
    margin-bottom: 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# ─── SUPABASE ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_sb() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
sb = get_sb()

# ─── CONSTANTES ───────────────────────────────────────────────────────────────
LOJAS = {
    "distribuidora": {"nome": "Prates Distribuidora", "cor": "#58A6FF", "icone": "📦"},
    "sublimacao":    {"nome": "Prates Sublimação",    "cor": "#3FB950", "icone": "🎨"},
}
UNIDADES    = ["UN","CX","PCT","KG","MT","LT","RL","PAR"]
PRIORIDADES = ["Alta","Média","Baixa"]
STATUS_OPS  = ["Pendente","Aprovado","Comprado","Entregue","Cancelado"]
STATUS_CLS  = {
    "Pendente": "pendente","Aprovado": "aprovado","Comprado": "comprado",
    "Entregue": "entregue","Cancelado": "cancelado"
}
PRIO_CLS = {"Alta":"alta","Média":"media","Baixa":"baixa"}

# ─── DB ───────────────────────────────────────────────────────────────────────
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def login_user(email, senha):
    r = sb.table("pc_usuarios").select("*").eq("email", email.strip().lower()).eq("ativo", True).execute()
    if not r.data: return None
    u = r.data[0]
    return u if u["senha_hash"] == hash_pw(senha) else None

def get_secoes(loja):
    r = sb.table("pc_secoes").select("*").eq("loja", loja).eq("ativa", True).order("ordem").execute()
    return r.data or []

def get_itens(secao_id):
    r = sb.table("pc_itens").select("*").eq("secao_id", secao_id).order("criado_em").execute()
    return r.data or []

def get_todos_itens():
    r = sb.table("pc_itens").select("*, pc_secoes(nome, loja)").execute()
    return r.data or []

def inserir_item(secao_id, dados, user):
    dados.update({"secao_id": secao_id, "criado_por": user,
                  "criado_em": datetime.now().isoformat(),
                  "atualizado_em": datetime.now().isoformat()})
    sb.table("pc_itens").insert(dados).execute()

def atualizar_item(iid, dados):
    dados["atualizado_em"] = datetime.now().isoformat()
    sb.table("pc_itens").update(dados).eq("id", iid).execute()

def deletar_item(iid):
    sb.table("pc_itens").delete().eq("id", iid).execute()

def atualizar_status_lote(ids, status):
    for iid in ids:
        sb.table("pc_itens").update({"status": status,
            "atualizado_em": datetime.now().isoformat()}).eq("id", iid).execute()

def criar_secao(loja, nome):
    secs = get_secoes(loja)
    ordem = (max(s["ordem"] for s in secs) + 1) if secs else 1
    sb.table("pc_secoes").insert({"loja": loja, "nome": nome, "ordem": ordem, "ativa": True}).execute()

def renomear_secao(sid, nome):
    sb.table("pc_secoes").update({"nome": nome}).eq("id", sid).execute()

def arquivar_secao(sid):
    sb.table("pc_secoes").update({"ativa": False}).eq("id", sid).execute()

def get_usuarios():
    r = sb.table("pc_usuarios").select("id,nome,email,acesso,ativo").order("nome").execute()
    return r.data or []

def criar_usuario(nome, email, senha, acesso):
    sb.table("pc_usuarios").insert({"nome": nome, "email": email.lower(),
        "senha_hash": hash_pw(senha), "acesso": acesso, "ativo": True}).execute()

def toggle_usuario(uid, ativo):
    sb.table("pc_usuarios").update({"ativo": ativo}).eq("id", uid).execute()

def pode_ver(loja):
    u = st.session_state.get("usuario")
    return u and u["acesso"] in ("admin","ambas", loja)

# ─── SESSION ──────────────────────────────────────────────────────────────────
for k,v in [("usuario",None),("pagina","dashboard"),("sel_itens",{})]:
    if k not in st.session_state: st.session_state[k] = v

# ─── LOGIN ────────────────────────────────────────────────────────────────────
def pagina_login():
    c1,c2,c3 = st.columns([1,1.1,1])
    with c2:
        st.markdown("""
        <div style='text-align:center;padding:80px 0 30px'>
            <div style='font-size:3.5rem'>🛒</div>
            <div style='font-size:2rem;font-weight:800;color:#F0F6FC;margin:8px 0 4px'>Prates</div>
            <div style='font-size:0.95rem;color:#8B949E'>Guia de Compras — Grupo Prates</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style='background:#161B22;border:1px solid #30363D;border-radius:12px;padding:2rem;'>
        """, unsafe_allow_html=True)

        with st.form("login", clear_on_submit=False):
            st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#F0F6FC;margin-bottom:1rem'>Entrar na conta</div>", unsafe_allow_html=True)
            email = st.text_input("E-mail", placeholder="seu@email.com")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            if st.form_submit_button("→  Entrar", use_container_width=True, type="primary"):
                u = login_user(email, senha)
                if u:
                    st.session_state.usuario = u
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
        st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.usuario:
    pagina_login()
    st.stop()

u = st.session_state.usuario

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class='sidebar-logo'>
        <div class='icon'>🛒</div>
        <div class='title'>Guia de Compras</div>
        <div class='sub'>Grupo Prates</div>
    </div>""", unsafe_allow_html=True)

    acesso_label = {"admin":"Administrador","ambas":"Ambas as Lojas",
                    "distribuidora":"Distribuidora","sublimacao":"Sublimação"}.get(u["acesso"],"")
    st.markdown(f"""
    <div class='user-card'>
        <div class='user-name'>👤 {u['nome']}</div>
        <div class='user-email'>{u['email']}</div>
        <div class='user-role'>{acesso_label}</div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    def nav(label, pagina, icone=""):
        ativo = st.session_state.pagina == pagina
        style = "primary" if ativo else "secondary"
        if st.button(f"{icone}  {label}", use_container_width=True, type=style, key=f"nav_{pagina}"):
            st.session_state.pagina = pagina
            st.rerun()

    st.markdown("<div class='nav-section'>Principal</div>", unsafe_allow_html=True)
    nav("Dashboard", "dashboard", "📊")

    st.markdown("<div class='nav-section'>Lançamento</div>", unsafe_allow_html=True)
    if pode_ver("distribuidora"):
        nav("Prates Distribuidora", "distribuidora", "📦")
    if pode_ver("sublimacao"):
        nav("Prates Sublimação", "sublimacao", "🎨")

    st.markdown("<div class='nav-section'>Relatórios</div>", unsafe_allow_html=True)
    nav("Histórico", "historico", "📅")
    nav("Exportar",  "exportar",  "📥")

    if u["acesso"] == "admin":
        st.markdown("<div class='nav-section'>Sistema</div>", unsafe_allow_html=True)
        nav("Administração", "admin", "⚙️")

    st.divider()
    if st.button("⏻  Sair", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

# ─── UTILS UI ─────────────────────────────────────────────────────────────────
def badge(texto, tipo):
    cls = STATUS_CLS.get(texto, PRIO_CLS.get(texto, "pendente"))
    return f"<span class='badge badge-{cls}'>{texto}</span>"

def dias_restantes(dt_str):
    if not dt_str: return None
    try:
        dt = date.fromisoformat(str(dt_str))
        diff = (dt - date.today()).days
        return diff
    except: return None

def badge_dias(dias):
    if dias is None: return ""
    if dias < 0:   return f"<span class='badge badge-urgente'>⚠ {abs(dias)}d atrasado</span>"
    if dias == 0:  return f"<span class='badge badge-urgente'>⚠ Hoje!</span>"
    if dias <= 3:  return f"<span class='badge badge-alta'>🔴 {dias}d</span>"
    if dias <= 7:  return f"<span class='badge badge-media'>🟡 {dias}d</span>"
    return f"<span class='badge badge-entregue'>🟢 {dias}d</span>"

def fmt_brl(v):
    try: return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except: return "R$ 0,00"

# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def pagina_dashboard():
    st.markdown("<div class='titulo-pagina'>📊 Dashboard</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitulo'>Visão geral do Grupo Prates — {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>", unsafe_allow_html=True)

    todos = get_todos_itens()
    if not todos:
        st.info("Nenhum item lançado ainda. Use as abas de cada loja para começar.")
        return

    df = pd.DataFrame(todos)
    df["loja"]       = df["pc_secoes"].apply(lambda x: x["loja"] if x else "")
    df["secao_nome"] = df["pc_secoes"].apply(lambda x: x["nome"] if x else "")
    df["total"]      = pd.to_numeric(df.get("total",0), errors="coerce").fillna(0)
    df["qtd"]        = pd.to_numeric(df.get("qtd",0), errors="coerce").fillna(0)

    total_geral  = df["total"].sum()
    total_dist   = df[df["loja"]=="distribuidora"]["total"].sum()
    total_sub    = df[df["loja"]=="sublimacao"]["total"].sum()
    n_pendentes  = (df["status"]=="Pendente").sum()
    n_aprovados  = (df["status"]=="Aprovado").sum()
    n_comprados  = (df["status"]=="Comprado").sum()
    n_entregues  = (df["status"]=="Entregue").sum()

    # KPIs
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    kpis = [
        (c1, "Total Geral",       fmt_brl(total_geral),  "",              "#58A6FF"),
        (c2, "Distribuidora",     fmt_brl(total_dist),   "📦",            "#58A6FF"),
        (c3, "Sublimação",        fmt_brl(total_sub),    "🎨",            "#3FB950"),
        (c4, "Pendentes",         str(n_pendentes),      "aguardando",    "#D2991E"),
        (c5, "Aprovados/Compra",  f"{n_aprovados}",      "em andamento",  "#A371F7"),
        (c6, "Entregues",         str(n_entregues),      "concluídos",    "#3FB950"),
    ]
    for col, label, val, sub, cor in kpis:
        col.markdown(f"""
        <div class='card-kpi' style='--accent:{cor}'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value' style='color:{cor}'>{val}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Alertas de urgência
    if "dt_necessidade" in df.columns:
        urgentes = []
        for _, row in df.iterrows():
            d = dias_restantes(row.get("dt_necessidade"))
            if d is not None and d <= 3 and row.get("status") not in ("Entregue","Cancelado"):
                urgentes.append(row)
        if urgentes:
            st.markdown(f"### ⚠️ {len(urgentes)} item(ns) urgente(s) — necessidade em até 3 dias")
            for item in urgentes[:5]:
                d = dias_restantes(item.get("dt_necessidade"))
                txt = f"**{item['produto']}** — {item['secao_nome']} — {badge_dias(d)}"
                st.markdown(f"<div class='item-row'>{txt}</div>", unsafe_allow_html=True)
            st.divider()

    # Gráficos
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("#### Total por Status")
        s_df = df.groupby("status")["total"].sum().reset_index()
        cor_map = {"Pendente":"#D2991E","Aprovado":"#58A6FF","Comprado":"#A371F7","Entregue":"#3FB950","Cancelado":"#F85149"}
        fig = px.bar(s_df, x="status", y="total", color="status",
                     color_discrete_map=cor_map, template="plotly_dark")
        fig.update_layout(showlegend=False, paper_bgcolor="#161B22", plot_bgcolor="#0D1117",
                          margin=dict(t=10,b=10), height=260,
                          font=dict(color="#E6EDF3"), xaxis=dict(gridcolor="#21262D"),
                          yaxis=dict(gridcolor="#21262D"))
        fig.update_traces(texttemplate="%{y:,.0f}", textposition="outside", textfont_color="#E6EDF3")
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.markdown("#### Distribuição por Loja")
        l_df = df.groupby("loja")["total"].sum().reset_index()
        l_df["nome"] = l_df["loja"].map({"distribuidora":"Distribuidora","sublimacao":"Sublimação"})
        fig2 = px.pie(l_df, names="nome", values="total",
                      color_discrete_sequence=["#58A6FF","#3FB950"],
                      hole=0.5, template="plotly_dark")
        fig2.update_layout(paper_bgcolor="#161B22", margin=dict(t=10,b=10), height=260,
                           font=dict(color="#E6EDF3"),
                           legend=dict(bgcolor="#161B22"))
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        st.markdown("#### Top 5 Produtos mais comprados")
        top5 = (df[df["status"].isin(["Comprado","Entregue"])]
                .groupby("produto")["qtd"].sum()
                .sort_values(ascending=False).head(5).reset_index())
        if not top5.empty:
            fig3 = px.bar(top5, x="qtd", y="produto", orientation="h",
                          template="plotly_dark", color_discrete_sequence=["#58A6FF"])
            fig3.update_layout(paper_bgcolor="#161B22", plot_bgcolor="#0D1117",
                               margin=dict(t=10,b=10), height=260,
                               font=dict(color="#E6EDF3"),
                               xaxis=dict(gridcolor="#21262D"), yaxis=dict(gridcolor="#21262D"))
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.caption("Nenhum item comprado/entregue ainda.")

    with g4:
        st.markdown("#### Total por Seção")
        sec_df = (df.groupby(["secao_nome","loja"])["total"].sum()
                  .reset_index().sort_values("total", ascending=True))
        fig4 = px.bar(sec_df, x="total", y="secao_nome", orientation="h",
                      color="loja", color_discrete_map={"distribuidora":"#58A6FF","sublimacao":"#3FB950"},
                      template="plotly_dark",
                      labels={"total":"Total (R$)","secao_nome":"","loja":"Loja"})
        fig4.update_layout(paper_bgcolor="#161B22", plot_bgcolor="#0D1117",
                           margin=dict(t=10,b=10), height=260,
                           font=dict(color="#E6EDF3"),
                           xaxis=dict(gridcolor="#21262D"), yaxis=dict(gridcolor="#21262D"),
                           legend=dict(bgcolor="#161B22"))
        st.plotly_chart(fig4, use_container_width=True)

# ─── PÁGINA DE LOJA ───────────────────────────────────────────────────────────
def pagina_loja(loja):
    info = LOJAS[loja]
    cor  = info["cor"]

    st.markdown(f"<div class='titulo-pagina'>{info['icone']} {info['nome']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Gerencie seções e itens para compra</div>", unsafe_allow_html=True)

    # Barra de controle
    ca, cb, cc, cd = st.columns([2,1,1,1])
    with ca:
        busca = st.text_input("🔍 Buscar produto ou fornecedor", placeholder="Digite para filtrar...",
                              label_visibility="collapsed", key=f"busca_{loja}")
    with cb:
        filtro_status = st.selectbox("Status", ["Todos"]+STATUS_OPS,
                                     key=f"fst_{loja}", label_visibility="collapsed")
    with cc:
        filtro_prio = st.selectbox("Prioridade", ["Todas"]+PRIORIDADES,
                                   key=f"fpr_{loja}", label_visibility="collapsed")
    with cd:
        if st.button("➕ Nova Seção", use_container_width=True, key=f"btn_ns_{loja}"):
            st.session_state[f"show_ns_{loja}"] = True

    # Form nova seção
    if st.session_state.get(f"show_ns_{loja}"):
        with st.form(f"form_ns_{loja}"):
            st.markdown("**Nova Seção**")
            nome_sec = st.text_input("Nome da seção", placeholder="Ex: Carregadores Tipo-C")
            c1,c2 = st.columns(2)
            if c1.form_submit_button("✅ Criar", type="primary"):
                if nome_sec.strip():
                    criar_secao(loja, nome_sec.strip())
                    st.session_state[f"show_ns_{loja}"] = False
                    st.rerun()
            if c2.form_submit_button("Cancelar"):
                st.session_state[f"show_ns_{loja}"] = False
                st.rerun()

    # Aprovar em lote
    sel_key = f"sel_{loja}"
    if sel_key not in st.session_state: st.session_state[sel_key] = []

    secoes = get_secoes(loja)
    if not secoes:
        st.markdown("""
        <div style='text-align:center;padding:3rem;background:#161B22;border:1px dashed #30363D;border-radius:12px;'>
            <div style='font-size:2rem'>📂</div>
            <div style='color:#8B949E;margin-top:0.5rem'>Nenhuma seção ainda.<br>Clique em <b>+ Nova Seção</b> para começar.</div>
        </div>""", unsafe_allow_html=True)
        return

    # Ação em lote
    itens_marcados = st.session_state.get(sel_key, [])
    if itens_marcados:
        st.markdown(f"""
        <div style='background:#1C2128;border:1px solid #30363D;border-radius:8px;
                    padding:0.8rem 1rem;margin-bottom:1rem;display:flex;align-items:center;gap:1rem'>
            <span style='color:#58A6FF;font-weight:600'>{len(itens_marcados)} item(ns) selecionado(s)</span>
        </div>""", unsafe_allow_html=True)
        bc1,bc2,bc3,bc4,bc5,bc6 = st.columns(6)
        acoes = [
            (bc1,"✅ Aprovar","Aprovado","primary"),
            (bc2,"🛒 Comprado","Comprado","secondary"),
            (bc3,"📦 Entregue","Entregue","secondary"),
            (bc4,"❌ Cancelar","Cancelado","secondary"),
        ]
        for col,label,status,tipo in acoes:
            if col.button(label, key=f"lote_{status}_{loja}", use_container_width=True, type=tipo):
                atualizar_status_lote(itens_marcados, status)
                st.session_state[sel_key] = []
                st.rerun()
        if bc6.button("Limpar seleção", key=f"clr_{loja}", use_container_width=True):
            st.session_state[sel_key] = []
            st.rerun()

    total_loja = 0
    for sec in secoes:
        itens = get_itens(sec["id"])

        # aplicar filtros
        itens_f = itens
        if filtro_status != "Todos":
            itens_f = [i for i in itens_f if i.get("status")==filtro_status]
        if filtro_prio != "Todas":
            itens_f = [i for i in itens_f if i.get("prioridade")==filtro_prio]
        if busca:
            b = busca.lower()
            itens_f = [i for i in itens_f if b in (i.get("produto","")+""+i.get("fornecedor","")).lower()]

        total_sec  = sum(float(i.get("total") or 0) for i in itens)
        total_loja += total_sec
        n_pend = sum(1 for i in itens if i.get("status")=="Pendente")

        with st.expander(
            f"**{sec['nome']}** &nbsp;·&nbsp; {len(itens)} itens &nbsp;·&nbsp; {fmt_brl(total_sec)}"
            + (f" &nbsp;·&nbsp; 🟡 {n_pend} pendentes" if n_pend else ""),
            expanded=True
        ):
            # Controles da seção
            sc1,sc2,sc3 = st.columns([3,1,1])
            with sc1:
                novo_nome = st.text_input("", value=sec["nome"], key=f"rn_{sec['id']}",
                                          label_visibility="collapsed",
                                          placeholder="Renomear seção...")
            with sc2:
                if st.button("💾 Renomear", key=f"sv_rn_{sec['id']}", use_container_width=True):
                    if novo_nome.strip() and novo_nome != sec["nome"]:
                        renomear_secao(sec["id"], novo_nome.strip())
                        st.rerun()
            with sc3:
                if st.button("🗑 Arquivar", key=f"arch_{sec['id']}", use_container_width=True):
                    arquivar_secao(sec["id"])
                    st.rerun()

            st.divider()

            # Lista de itens
            if itens_f:
                for item in itens_f:
                    total_item = float(item.get("total") or 0)
                    dias = dias_restantes(item.get("dt_necessidade"))
                    iid  = item["id"]
                    selecionado = iid in st.session_state.get(sel_key, [])

                    ci0,ci1,ci2,ci3,ci4,ci5,ci6,ci7,ci8 = st.columns([0.4,3,2,1,1,1.5,1.5,1.5,1])
                    # checkbox seleção
                    sel = ci0.checkbox("", value=selecionado, key=f"chk_{iid}", label_visibility="collapsed")
                    if sel and iid not in st.session_state.get(sel_key,[]):
                        st.session_state.setdefault(sel_key,[]).append(iid)
                    elif not sel and iid in st.session_state.get(sel_key,[]):
                        st.session_state[sel_key].remove(iid)

                    ci1.markdown(f"<div class='item-nome'>{item.get('produto','')}</div>"
                                 f"<div class='item-meta'>{item.get('fornecedor','—')}</div>",
                                 unsafe_allow_html=True)
                    ci2.markdown(f"<div style='font-size:.85rem;color:#8B949E'>{sec['nome']}</div>",
                                 unsafe_allow_html=True)
                    ci3.markdown(f"<div style='text-align:center;font-size:.9rem'>{item.get('qtd','')} {item.get('unidade','')}</div>",
                                 unsafe_allow_html=True)
                    ci4.markdown(f"<div style='text-align:right;font-size:.85rem;color:#8B949E'>{fmt_brl(item.get('preco_unit',0))}</div>",
                                 unsafe_allow_html=True)
                    ci5.markdown(f"<div style='text-align:right;font-weight:600;color:{cor}'>{fmt_brl(total_item)}</div>",
                                 unsafe_allow_html=True)
                    ci6.markdown(badge(item.get("status",""), "status")
                                 + " " + badge_dias(dias), unsafe_allow_html=True)
                    ci7.markdown(badge(item.get("prioridade",""), "prio"), unsafe_allow_html=True)

                    with ci8:
                        with st.popover("···"):
                            st.markdown(f"**{item.get('produto','')}**")
                            novo_st = st.selectbox("Status", STATUS_OPS,
                                                   index=STATUS_OPS.index(item.get("status","Pendente")),
                                                   key=f"pop_st_{iid}")
                            if st.button("Salvar status", key=f"sv_st_{iid}", type="primary"):
                                atualizar_item(iid, {"status": novo_st})
                                st.rerun()
                            st.divider()
                            obs = item.get("obs","")
                            if obs:
                                st.caption(f"📝 {obs}")
                            if st.button("✏️ Editar", key=f"edit_btn_{iid}"):
                                st.session_state[f"edit_{iid}"] = True
                            if st.button("🗑 Deletar", key=f"del_{iid}"):
                                deletar_item(iid)
                                st.rerun()

                    # Form edição inline
                    if st.session_state.get(f"edit_{iid}"):
                        with st.form(f"fe_{iid}"):
                            st.markdown("**✏️ Editar item**")
                            ep1,ep2 = st.columns(2)
                            e_prod = ep1.text_input("Produto", value=item.get("produto",""))
                            e_forn = ep2.text_input("Fornecedor", value=item.get("fornecedor",""))
                            eq1,eq2,eq3,eq4 = st.columns(4)
                            e_qtd   = eq1.number_input("Qtd", min_value=0.0, value=float(item.get("qtd") or 0), step=1.0)
                            e_un    = eq2.selectbox("Unid", UNIDADES,
                                                    index=UNIDADES.index(item.get("unidade","UN"))
                                                    if item.get("unidade","UN") in UNIDADES else 0)
                            e_preco = eq3.number_input("Preço Unit.", min_value=0.0,
                                                       value=float(item.get("preco_unit") or 0),
                                                       step=0.01, format="%.2f")
                            e_prio  = eq4.selectbox("Prioridade", PRIORIDADES,
                                                    index=PRIORIDADES.index(item.get("prioridade","Média"))
                                                    if item.get("prioridade") in PRIORIDADES else 1)
                            e_dt    = st.date_input("Data de Necessidade", value=None)
                            e_obs   = st.text_input("Observações", value=item.get("obs",""))
                            es1,es2 = st.columns(2)
                            if es1.form_submit_button("💾 Salvar", type="primary"):
                                atualizar_item(iid, {
                                    "produto": e_prod, "fornecedor": e_forn,
                                    "qtd": e_qtd, "unidade": e_un,
                                    "preco_unit": e_preco, "total": round(e_qtd*e_preco,2),
                                    "prioridade": e_prio, "obs": e_obs,
                                    "dt_necessidade": str(e_dt) if e_dt else None,
                                })
                                st.session_state[f"edit_{iid}"] = False
                                st.rerun()
                            if es2.form_submit_button("Cancelar"):
                                st.session_state[f"edit_{iid}"] = False
                                st.rerun()
            else:
                st.markdown("<div style='color:#8B949E;padding:1rem 0;font-size:.9rem'>Nenhum item encontrado com os filtros selecionados.</div>",
                            unsafe_allow_html=True)

            # Adicionar item
            st.markdown("---")
            with st.expander("➕ Adicionar item nesta seção"):
                with st.form(f"fa_{sec['id']}"):
                    ap1,ap2 = st.columns(2)
                    a_prod = ap1.text_input("Produto *")
                    a_forn = ap2.text_input("Fornecedor")
                    aq1,aq2,aq3,aq4,aq5 = st.columns(5)
                    a_qtd   = aq1.number_input("Qtd *", min_value=0.0, step=1.0)
                    a_un    = aq2.selectbox("Unid", UNIDADES)
                    a_preco = aq3.number_input("Preço Unit.", min_value=0.0, step=0.01, format="%.2f")
                    a_prio  = aq4.selectbox("Prioridade", PRIORIDADES, index=1)
                    a_dt    = aq5.date_input("Dt. Necessidade", value=None)
                    a_obs   = st.text_input("Observações")
                    if st.form_submit_button("➕ Adicionar", type="primary"):
                        if a_prod.strip():
                            inserir_item(sec["id"], {
                                "produto": a_prod.strip(), "fornecedor": a_forn.strip(),
                                "qtd": a_qtd, "unidade": a_un,
                                "preco_unit": a_preco, "total": round(a_qtd*a_preco,2),
                                "prioridade": a_prio, "status": "Pendente",
                                "dt_necessidade": str(a_dt) if a_dt else None,
                                "obs": a_obs.strip(),
                            }, u["nome"])
                            st.rerun()
                        else:
                            st.warning("Informe o nome do produto.")

    # Total da loja
    st.markdown(f"""
    <div style='background:#161B22;border:1px solid #30363D;border-radius:10px;
                padding:1rem 1.5rem;margin-top:1rem;text-align:right'>
        <span style='color:#8B949E;font-size:.9rem'>Total {info['nome']}:</span>
        <span style='color:{cor};font-size:1.3rem;font-weight:700;margin-left:1rem'>{fmt_brl(total_loja)}</span>
    </div>""", unsafe_allow_html=True)

# ─── HISTÓRICO ────────────────────────────────────────────────────────────────
def pagina_historico():
    st.markdown("<div class='titulo-pagina'>📅 Histórico de Pedidos</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Todos os itens lançados com filtros avançados</div>", unsafe_allow_html=True)

    todos = get_todos_itens()
    if not todos:
        st.info("Nenhum item lançado ainda.")
        return

    df = pd.DataFrame(todos)
    df["loja"]       = df["pc_secoes"].apply(lambda x: x["loja"] if x else "")
    df["secao_nome"] = df["pc_secoes"].apply(lambda x: x["nome"] if x else "")
    df["total"]      = pd.to_numeric(df.get("total",0), errors="coerce").fillna(0)
    df["loja_nome"]  = df["loja"].map({"distribuidora":"Distribuidora","sublimacao":"Sublimação"})

    # Filtros
    f1,f2,f3,f4,f5 = st.columns(5)
    f_loja   = f1.selectbox("Loja", ["Todas","Distribuidora","Sublimação"], label_visibility="collapsed")
    f_status = f2.selectbox("Status", ["Todos"]+STATUS_OPS, label_visibility="collapsed")
    f_prio   = f3.selectbox("Prioridade", ["Todas"]+PRIORIDADES, label_visibility="collapsed")
    f_busca  = f4.text_input("Buscar", placeholder="Produto ou fornecedor...", label_visibility="collapsed")
    f_seção  = f5.selectbox("Seção", ["Todas"]+sorted(df["secao_nome"].unique().tolist()), label_visibility="collapsed")

    df_f = df.copy()
    if f_loja != "Todas":
        lk = "distribuidora" if f_loja=="Distribuidora" else "sublimacao"
        df_f = df_f[df_f["loja"]==lk]
    if f_status != "Todos":
        df_f = df_f[df_f["status"]==f_status]
    if f_prio != "Todas":
        df_f = df_f[df_f["prioridade"]==f_prio]
    if f_busca:
        b = f_busca.lower()
        df_f = df_f[df_f["produto"].str.lower().str.contains(b, na=False) |
                    df_f["fornecedor"].str.lower().str.contains(b, na=False)]
    if f_seção != "Todas":
        df_f = df_f[df_f["secao_nome"]==f_seção]

    st.markdown(f"<div style='color:#8B949E;font-size:.85rem;margin:0.5rem 0'>{len(df_f)} itens encontrados — Total: <b style='color:#58A6FF'>{fmt_brl(df_f['total'].sum())}</b></div>",
                unsafe_allow_html=True)

    cols_show = ["produto","secao_nome","loja_nome","fornecedor","qtd","unidade","total","prioridade","status","dt_necessidade","obs","criado_por","criado_em"]
    cols_exist = [c for c in cols_show if c in df_f.columns]
    st.dataframe(
        df_f[cols_exist].rename(columns={
            "produto":"Produto","secao_nome":"Seção","loja_nome":"Loja",
            "fornecedor":"Fornecedor","qtd":"Qtd","unidade":"Unid",
            "total":"Total (R$)","prioridade":"Prioridade","status":"Status",
            "dt_necessidade":"Dt. Necessidade","obs":"Obs",
            "criado_por":"Criado por","criado_em":"Criado em"
        }),
        use_container_width=True, hide_index=True, height=500
    )

# ─── EXPORTAR ─────────────────────────────────────────────────────────────────
def gerar_excel(loja_filtro="ambas"):
    wb = Workbook()
    ws = wb.active
    ws.title = "Compras"

    def thin():
        s = Side(style="thin", color="2D3748")
        return Border(left=s,right=s,top=s,bottom=s)

    lojas_proc = ["distribuidora","sublimacao"] if loja_filtro=="ambas" else [loja_filtro]

    row = 1
    ws.merge_cells(f"A{row}:J{row}")
    c = ws.cell(row=row,column=1,value="GRUPO PRATES — GUIA DE COMPRAS")
    c.font = Font(name="Calibri",bold=True,size=14,color="FFFFFF")
    c.fill = PatternFill("solid",start_color="0D1117")
    c.alignment = Alignment(horizontal="center",vertical="center")
    ws.row_dimensions[row].height = 30
    row += 1

    ws.merge_cells(f"A{row}:J{row}")
    c = ws.cell(row=row,column=1,value=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.font = Font(name="Calibri",italic=True,size=9,color="8B949E")
    c.fill = PatternFill("solid",start_color="161B22")
    c.alignment = Alignment(horizontal="right",vertical="center")
    ws.row_dimensions[row].height = 16
    row += 1

    headers = ["Seção","Produto","Fornecedor","Qtd","Unid","Preço Unit.","Total","Prioridade","Status","Dt. Necessidade"]
    widths   = [22,30,20,8,7,14,14,12,12,16]
    for i,(h,w) in enumerate(zip(headers,widths),1):
        ws.column_dimensions[get_column_letter(i)].width = w
        c = ws.cell(row=row,column=i,value=h)
        c.font = Font(name="Calibri",bold=True,color="E6EDF3",size=10)
        c.fill = PatternFill("solid",start_color="21262D")
        c.alignment = Alignment(horizontal="center",vertical="center")
        c.border = thin()
    ws.row_dimensions[row].height = 18
    row += 1

    for loja in lojas_proc:
        info = LOJAS[loja]
        cor_hex = info["cor"].replace("#","")
        secoes = get_secoes(loja)

        ws.merge_cells(f"A{row}:J{row}")
        c = ws.cell(row=row,column=1,value=f"  {info['icone']}  {info['nome'].upper()}")
        c.font = Font(name="Calibri",bold=True,size=11,color="FFFFFF")
        c.fill = PatternFill("solid",start_color="161B22")
        c.alignment = Alignment(horizontal="left",vertical="center")
        c.border = thin()
        ws.row_dimensions[row].height = 22
        row += 1

        total_loja = 0
        for sec in secoes:
            itens = get_itens(sec["id"])
            if not itens: continue
            total_sec = 0
            for ri,item in enumerate(itens):
                zb = "0D1117" if ri%2==0 else "161B22"
                vals = [sec["nome"],item.get("produto",""),item.get("fornecedor",""),
                        item.get("qtd",""),item.get("unidade",""),
                        item.get("preco_unit",""),item.get("total",""),
                        item.get("prioridade",""),item.get("status",""),
                        item.get("dt_necessidade","")]
                for ci,v in enumerate(vals,1):
                    c = ws.cell(row=row,column=ci,value=v)
                    c.font = Font(name="Calibri",size=9,color="E6EDF3")
                    c.fill = PatternFill("solid",start_color=zb)
                    c.alignment = Alignment(horizontal="center" if ci>3 else "left",vertical="center")
                    c.border = thin()
                    if ci in (6,7) and v: c.number_format = '"R$" #,##0.00'
                ws.row_dimensions[row].height = 16
                total_sec += float(item.get("total") or 0)
                row += 1
            total_loja += total_sec
            ws.merge_cells(f"A{row}:F{row}")
            c = ws.cell(row=row,column=1,value=f"Subtotal {sec['nome']}")
            c.font = Font(name="Calibri",bold=True,size=9,color="FFFFFF")
            c.fill = PatternFill("solid",start_color="21262D")
            c.alignment = Alignment(horizontal="right",vertical="center"); c.border = thin()
            c = ws.cell(row=row,column=7,value=total_sec)
            c.font = Font(name="Calibri",bold=True,size=9,color="58A6FF")
            c.fill = PatternFill("solid",start_color="21262D")
            c.alignment = Alignment(horizontal="right",vertical="center")
            c.number_format = '"R$" #,##0.00'; c.border = thin()
            for ci in range(8,11):
                cc = ws.cell(row=row,column=ci)
                cc.fill = PatternFill("solid",start_color="21262D"); cc.border = thin()
            ws.row_dimensions[row].height = 18; row += 1

        ws.merge_cells(f"A{row}:F{row}")
        c = ws.cell(row=row,column=1,value=f"TOTAL {info['nome'].upper()}")
        c.font = Font(name="Calibri",bold=True,size=10,color="FFFFFF")
        c.fill = PatternFill("solid",start_color="0D1117")
        c.alignment = Alignment(horizontal="right",vertical="center"); c.border = thin()
        c = ws.cell(row=row,column=7,value=total_loja)
        c.font = Font(name="Calibri",bold=True,size=10,color=cor_hex)
        c.fill = PatternFill("solid",start_color="0D1117")
        c.alignment = Alignment(horizontal="right",vertical="center")
        c.number_format = '"R$" #,##0.00'; c.border = thin()
        for ci in range(8,11):
            cc = ws.cell(row=row,column=ci)
            cc.fill = PatternFill("solid",start_color="0D1117"); cc.border = thin()
        ws.row_dimensions[row].height = 22; row += 2

    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return buf

def pagina_exportar():
    st.markdown("<div class='titulo-pagina'>📥 Exportar</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Baixe os pedidos em Excel ou PDF</div>", unsafe_allow_html=True)

    col_op,_ = st.columns([1,2])
    with col_op:
        loja_exp = st.selectbox("Loja", ["Ambas as lojas","Prates Distribuidora","Prates Sublimação"])
        loja_key = {"Ambas as lojas":"ambas","Prates Distribuidora":"distribuidora","Prates Sublimação":"sublimacao"}[loja_exp]

    st.divider()
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='card' style='text-align:center'>
            <div style='font-size:2.5rem'>📊</div>
            <div style='font-weight:600;font-size:1.1rem;margin:0.5rem 0'>Excel (.xlsx)</div>
            <div style='color:#8B949E;font-size:.85rem'>Planilha dark com subtotais e formatação</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Gerar Excel", use_container_width=True, type="primary", key="gen_xl"):
            buf = gerar_excel(loja_key)
            st.download_button("⬇️ Baixar Excel", buf,
                file_name=f"Compras_Prates_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
    with c2:
        st.markdown("""
        <div class='card' style='text-align:center'>
            <div style='font-size:2.5rem'>📄</div>
            <div style='font-weight:600;font-size:1.1rem;margin:0.5rem 0'>PDF</div>
            <div style='color:#8B949E;font-size:.85rem'>Relatório formatado para impressão</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Gerar PDF", use_container_width=True, key="gen_pdf"):
            st.info("Em breve! Use o Excel por enquanto.")

# ─── ADMIN ────────────────────────────────────────────────────────────────────
def pagina_admin():
    st.markdown("<div class='titulo-pagina'>⚙️ Administração</div>", unsafe_allow_html=True)
    tab_u, tab_s = st.tabs(["👤 Usuários", "📂 Seções"])

    with tab_u:
        st.markdown("#### Criar novo usuário")
        with st.form("form_usr"):
            c1,c2 = st.columns(2)
            nome  = c1.text_input("Nome completo")
            email = c2.text_input("E-mail")
            c3,c4 = st.columns(2)
            senha = c3.text_input("Senha inicial", type="password")
            acesso= c4.selectbox("Acesso", ["distribuidora","sublimacao","ambas","admin"],
                                 format_func=lambda x: {"distribuidora":"Só Distribuidora",
                                     "sublimacao":"Só Sublimação","ambas":"Ambas","admin":"Admin"}[x])
            if st.form_submit_button("➕ Criar usuário", type="primary"):
                if nome and email and senha:
                    criar_usuario(nome,email,senha,acesso)
                    st.success(f"✅ Usuário '{nome}' criado!")
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos.")

        st.markdown("#### Usuários cadastrados")
        for uu in get_usuarios():
            cu1,cu2,cu3,cu4 = st.columns([3,3,2,1])
            cu1.markdown(f"**{uu['nome']}**")
            cu2.markdown(f"<small style='color:#8B949E'>{uu['email']}</small>", unsafe_allow_html=True)
            cu3.markdown(uu["acesso"])
            lbl = "✅ Ativo" if uu["ativo"] else "❌ Inativo"
            if cu4.button(lbl, key=f"tog_{uu['id']}"):
                toggle_usuario(uu["id"], not uu["ativo"]); st.rerun()

    with tab_s:
        for loja, info in LOJAS.items():
            st.markdown(f"#### {info['icone']} {info['nome']}")
            for sec in get_secoes(loja):
                cs1,cs2,cs3 = st.columns([4,2,1])
                cs1.markdown(f"**{sec['nome']}**")
                nn = cs2.text_input("", value=sec["nome"], key=f"a_sec_{sec['id']}",
                                    label_visibility="collapsed")
                if cs3.button("Salvar", key=f"a_ren_{sec['id']}"):
                    renomear_secao(sec["id"], nn); st.rerun()
            st.divider()

# ─── ROTEADOR ─────────────────────────────────────────────────────────────────
pg = st.session_state.pagina
if   pg == "dashboard":    pagina_dashboard()
elif pg == "distribuidora":
    if pode_ver("distribuidora"): pagina_loja("distribuidora")
    else: st.error("Acesso negado.")
elif pg == "sublimacao":
    if pode_ver("sublimacao"): pagina_loja("sublimacao")
    else: st.error("Acesso negado.")
elif pg == "historico":    pagina_historico()
elif pg == "exportar":     pagina_exportar()
elif pg == "admin":
    if u["acesso"] == "admin": pagina_admin()
    else: st.error("Acesso restrito.")
