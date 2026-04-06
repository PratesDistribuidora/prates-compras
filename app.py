import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib
from datetime import date, datetime, timedelta
import io
import plotly.express as px
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Prates — Guia de Compras", page_icon="🛒",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

[data-testid="stAppViewContainer"],[data-testid="stMain"] { background:#0D1117 !important; }
section[data-testid="stSidebar"] { background:#010409 !important; border-right:1px solid #21262D !important; }
section[data-testid="stSidebar"] * { color:#E6EDF3 !important; }
section[data-testid="stSidebar"] hr { border-color:#21262D !important; }

p,li,span,label,div { color:#E6EDF3; }
h1,h2,h3 { color:#F0F6FC !important; }

[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input {
    background:#161B22 !important; color:#E6EDF3 !important;
    border:1px solid #30363D !important; border-radius:6px !important;
}
[data-testid="stSelectbox"]>div>div {
    background:#161B22 !important; color:#E6EDF3 !important; border:1px solid #30363D !important;
}
[data-testid="stTextArea"] textarea {
    background:#161B22 !important; color:#E6EDF3 !important; border:1px solid #30363D !important;
}
[data-testid="stButton"]>button {
    background:#21262D !important; color:#E6EDF3 !important;
    border:1px solid #30363D !important; border-radius:8px !important;
    font-weight:500 !important; transition:all .2s !important;
}
[data-testid="stButton"]>button:hover { background:#30363D !important; border-color:#58A6FF !important; }
[data-testid="stButton"]>button[kind="primary"] {
    background:#238636 !important; color:#fff !important; border-color:#2EA043 !important;
}
[data-testid="stButton"]>button[kind="primary"]:hover { background:#2EA043 !important; }
[data-testid="stExpander"] {
    background:#161B22 !important; border:1px solid #21262D !important; border-radius:10px !important;
}
[data-testid="stForm"] {
    background:#161B22 !important; border:1px solid #30363D !important; border-radius:10px !important; padding:1rem !important;
}
[data-testid="stTabs"] [role="tab"] { color:#8B949E !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:#58A6FF !important; border-bottom:2px solid #58A6FF !important; }
[data-testid="stDataFrame"] { background:#161B22 !important; }
hr { border-color:#21262D !important; }
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#0D1117; }
::-webkit-scrollbar-thumb { background:#30363D; border-radius:3px; }

.pg-title { font-size:1.6rem; font-weight:800; color:#F0F6FC; margin-bottom:.2rem; }
.pg-sub   { font-size:.85rem; color:#8B949E; margin-bottom:1.2rem; }

.card { background:#161B22; border:1px solid #21262D; border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:.8rem; }
.kpi-card {
    background:#161B22; border:1px solid #21262D; border-radius:12px;
    padding:1.2rem; text-align:center; position:relative; overflow:hidden;
}
.kpi-card::before { content:''; position:absolute; top:0;left:0;right:0; height:3px; background:var(--acc,#238636); }
.kpi-val  { font-size:1.6rem; font-weight:700; color:var(--acc,#F0F6FC); margin:.3rem 0; }
.kpi-lbl  { font-size:.72rem; color:#8B949E; text-transform:uppercase; letter-spacing:.06em; font-weight:600; }

.badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:.72rem; font-weight:600; }
.b-pendente  { background:rgba(210,153,34,.15);  color:#D2991E; border:1px solid #D2991E44; }
.b-aprovado  { background:rgba(88,166,255,.15);  color:#58A6FF; border:1px solid #58A6FF44; }
.b-comprado  { background:rgba(163,113,247,.15); color:#A371F7; border:1px solid #A371F744; }
.b-entregue  { background:rgba(35,134,54,.15);   color:#3FB950; border:1px solid #3FB95044; }
.b-cancelado { background:rgba(248,81,73,.15);   color:#F85149; border:1px solid #F8514944; }
.b-alta  { background:rgba(248,81,73,.15);  color:#F85149; border:1px solid #F8514944; }
.b-media { background:rgba(210,153,34,.15); color:#D2991E; border:1px solid #D2991E44; }
.b-baixa { background:rgba(35,134,54,.15);  color:#3FB950; border:1px solid #3FB95044; }
.b-urgente { background:rgba(248,81,73,.25); color:#F85149; border:1px solid #F85149; }

.item-card {
    background:#0D1117; border:1px solid #21262D; border-radius:8px;
    padding:.7rem 1rem; margin-bottom:.4rem; transition:border-color .2s;
}
.item-card:hover { border-color:#30363D; }
.item-nome { font-weight:600; color:#F0F6FC; font-size:.95rem; }
.item-meta { font-size:.78rem; color:#8B949E; margin-top:2px; }

.nav-sec { font-size:.68rem; color:#6E7681; text-transform:uppercase;
           letter-spacing:.1em; font-weight:600; margin:1rem 0 .4rem .3rem; }
.user-card { background:#0D1117; border:1px solid #21262D; border-radius:8px; padding:.7rem 1rem; margin:.5rem 0; }
.user-role { display:inline-block; background:#238636; color:#fff;
             font-size:.65rem; font-weight:700; padding:1px 8px; border-radius:20px; margin-top:3px; }

.flow-bar {
    display:flex; align-items:center; gap:.5rem; padding:.6rem 1rem;
    background:#161B22; border:1px solid #21262D; border-radius:8px; margin-bottom:1rem;
}
.flow-step { font-size:.8rem; font-weight:600; padding:.3rem .8rem; border-radius:6px; }
.flow-arrow { color:#30363D; font-size:.9rem; }
.forn-card { background:#161B22; border:1px solid #21262D; border-radius:10px; padding:1rem; margin-bottom:.6rem; }
</style>
""", unsafe_allow_html=True)

# ── Supabase ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_sb():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
sb = get_sb()

# ── Constantes ────────────────────────────────────────────────────────────────
LOJAS = {
    "distribuidora": {"nome":"Prates Distribuidora","cor":"#58A6FF","icone":"📦"},
    "sublimacao":    {"nome":"Prates Sublimação",   "cor":"#3FB950","icone":"🎨"},
}
UNIDADES    = ["UN","CX","PCT","KG","MT","LT","RL","PAR"]
PRIORIDADES = ["Alta","Média","Baixa"]
STATUS_FLUXO = ["Pendente","Aprovado","Comprado","Entregue","Cancelado"]
STATUS_ATIVOS    = ["Pendente","Aprovado"]          # aparecem na lista de compras
STATUS_HISTORICO = ["Comprado","Entregue","Cancelado"]  # aparecem só no histórico

STATUS_CLS = {"Pendente":"pendente","Aprovado":"aprovado","Comprado":"comprado",
              "Entregue":"entregue","Cancelado":"cancelado"}
PRIO_CLS   = {"Alta":"alta","Média":"media","Baixa":"baixa"}

# ── DB helpers ────────────────────────────────────────────────────────────────
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def login_user(email, senha):
    r = sb.table("pc_usuarios").select("*").eq("email",email.strip().lower()).eq("ativo",True).execute()
    if not r.data: return None
    u = r.data[0]
    return u if u["senha_hash"] == hash_pw(senha) else None

# Fornecedores
def get_fornecedores():
    r = sb.table("pc_fornecedores").select("*").eq("ativo",True).order("nome").execute()
    return r.data or []

def criar_fornecedor(dados):
    sb.table("pc_fornecedores").insert(dados).execute()

def editar_fornecedor(fid, dados):
    sb.table("pc_fornecedores").update(dados).eq("id",fid).execute()

def deletar_fornecedor(fid):
    sb.table("pc_fornecedores").update({"ativo":False}).eq("id",fid).execute()

# Seções
def get_secoes(loja):
    r = sb.table("pc_secoes").select("*").eq("loja",loja).eq("ativa",True).order("ordem").execute()
    return r.data or []

def criar_secao(loja, nome):
    secs = get_secoes(loja)
    ordem = (max(s["ordem"] for s in secs)+1) if secs else 1
    sb.table("pc_secoes").insert({"loja":loja,"nome":nome,"ordem":ordem,"ativa":True}).execute()

def editar_secao(sid, nome):
    sb.table("pc_secoes").update({"nome":nome}).eq("id",sid).execute()

def arquivar_secao(sid):
    sb.table("pc_secoes").update({"ativa":False}).eq("id",sid).execute()

# Itens
def get_itens(secao_id, status_filter=None):
    q = sb.table("pc_itens").select("*").eq("secao_id",secao_id)
    if status_filter:
        q = q.in_("status", status_filter)
    return (q.order("criado_em").execute().data or [])

def get_todos_itens(status_filter=None):
    q = sb.table("pc_itens").select("*, pc_secoes(nome,loja)")
    if status_filter:
        q = q.in_("status", status_filter)
    return (q.execute().data or [])

def inserir_item(secao_id, dados, user):
    dados.update({"secao_id":secao_id,"criado_por":user,
                  "criado_em":datetime.now().isoformat(),
                  "atualizado_em":datetime.now().isoformat()})
    sb.table("pc_itens").insert(dados).execute()

def atualizar_item(iid, dados):
    dados["atualizado_em"] = datetime.now().isoformat()
    sb.table("pc_itens").update(dados).eq("id",iid).execute()

def deletar_item(iid):
    sb.table("pc_itens").delete().eq("id",iid).execute()

def atualizar_status_lote(ids, status):
    for iid in ids:
        sb.table("pc_itens").update({"status":status,
            "atualizado_em":datetime.now().isoformat()}).eq("id",iid).execute()

# Usuários
def get_usuarios():
    r = sb.table("pc_usuarios").select("id,nome,email,acesso,ativo").order("nome").execute()
    return r.data or []

def criar_usuario(nome, email, senha, acesso):
    sb.table("pc_usuarios").insert({"nome":nome,"email":email.lower(),
        "senha_hash":hash_pw(senha),"acesso":acesso,"ativo":True}).execute()

def editar_usuario(uid, dados):
    sb.table("pc_usuarios").update(dados).eq("id",uid).execute()

def pode_ver(loja):
    u = st.session_state.get("usuario")
    return u and u["acesso"] in ("admin","ambas",loja)

# ── Session ───────────────────────────────────────────────────────────────────
for k,v in [("usuario",None),("pagina","dashboard"),("sel",{})]:
    if k not in st.session_state: st.session_state[k] = v

# ── Login ─────────────────────────────────────────────────────────────────────
def pagina_login():
    c1,c2,c3 = st.columns([1,1.1,1])
    with c2:
        st.markdown("""
        <div style='text-align:center;padding:80px 0 30px'>
            <div style='font-size:3.5rem'>🛒</div>
            <div style='font-size:2rem;font-weight:800;color:#F0F6FC;margin:8px 0 4px'>Prates</div>
            <div style='font-size:.95rem;color:#8B949E'>Guia de Compras — Grupo Prates</div>
        </div>""", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("E-mail", placeholder="seu@email.com")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar →", use_container_width=True, type="primary"):
                u = login_user(email, senha)
                if u: st.session_state.usuario = u; st.rerun()
                else: st.error("E-mail ou senha incorretos.")

if not st.session_state.usuario:
    pagina_login(); st.stop()

u = st.session_state.usuario

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:1.5rem 0 1rem'>
        <div style='font-size:2.5rem'>🛒</div>
        <div style='font-size:1.1rem;font-weight:700;color:#F0F6FC'>Guia de Compras</div>
        <div style='font-size:.75rem;color:#8B949E'>Grupo Prates</div>
    </div>""", unsafe_allow_html=True)

    roles = {"admin":"Administrador","ambas":"Ambas as Lojas",
             "distribuidora":"Distribuidora","sublimacao":"Sublimação"}
    st.markdown(f"""
    <div class='user-card'>
        <div style='font-weight:600;color:#F0F6FC'>👤 {u['nome']}</div>
        <div style='font-size:.75rem;color:#8B949E'>{u['email']}</div>
        <div class='user-role'>{roles.get(u['acesso'],'')}</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    def nav(label, pagina, icone=""):
        ativo = st.session_state.pagina == pagina
        if st.button(f"{icone}  {label}", use_container_width=True,
                     type="primary" if ativo else "secondary", key=f"nav_{pagina}"):
            st.session_state.pagina = pagina; st.rerun()

    st.markdown("<div class='nav-sec'>Principal</div>", unsafe_allow_html=True)
    nav("Dashboard","dashboard","📊")

    st.markdown("<div class='nav-sec'>Lançamento</div>", unsafe_allow_html=True)
    if pode_ver("distribuidora"): nav("Prates Distribuidora","distribuidora","📦")
    if pode_ver("sublimacao"):    nav("Prates Sublimação","sublimacao","🎨")

    st.markdown("<div class='nav-sec'>Consultas</div>", unsafe_allow_html=True)
    nav("Histórico","historico","📅")
    nav("Exportar","exportar","📥")

    st.markdown("<div class='nav-sec'>Cadastros</div>", unsafe_allow_html=True)
    nav("Fornecedores","fornecedores","🏭")
    if u["acesso"]=="admin":
        nav("Administração","admin","⚙️")

    st.divider()
    if st.button("⏻  Sair", use_container_width=True):
        st.session_state.usuario = None; st.rerun()

# ── Utils ─────────────────────────────────────────────────────────────────────
def badge(txt, tipo="status"):
    cls = STATUS_CLS.get(txt, PRIO_CLS.get(txt,"pendente"))
    return f"<span class='badge b-{cls}'>{txt}</span>"

def dias_badge(dt_str):
    if not dt_str: return ""
    try:
        d = (date.fromisoformat(str(dt_str)) - date.today()).days
        if d<0:  return f"<span class='badge b-urgente'>⚠ {abs(d)}d atrasado</span>"
        if d==0: return f"<span class='badge b-urgente'>⚠ Hoje!</span>"
        if d<=3: return f"<span class='badge b-alta'>🔴 {d}d</span>"
        if d<=7: return f"<span class='badge b-media'>🟡 {d}d</span>"
        return f"<span class='badge b-baixa'>🟢 {d}d</span>"
    except: return ""

def fmt(v):
    try: return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except: return "R$ 0,00"

def forn_map():
    return {f["id"]: f["nome"] for f in get_fornecedores()}

# ── Dashboard ─────────────────────────────────────────────────────────────────
def pagina_dashboard():
    st.markdown("<div class='pg-title'>📊 Dashboard</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='pg-sub'>{datetime.now().strftime('%d/%m/%Y %H:%M')} — Visão geral do Grupo Prates</div>", unsafe_allow_html=True)

    todos = get_todos_itens()
    if not todos: st.info("Nenhum item lançado ainda."); return

    df = pd.DataFrame(todos)
    df["loja"]       = df["pc_secoes"].apply(lambda x: x["loja"] if x else "")
    df["secao_nome"] = df["pc_secoes"].apply(lambda x: x["nome"] if x else "")
    df["total"]      = pd.to_numeric(df.get("total",0), errors="coerce").fillna(0)
    df["qtd"]        = pd.to_numeric(df.get("qtd",0), errors="coerce").fillna(0)

    # Barra de fluxo
    st.markdown("""
    <div class='flow-bar'>
        <span class='flow-step' style='background:rgba(210,153,34,.15);color:#D2991E'>Pendente</span>
        <span class='flow-arrow'>→</span>
        <span class='flow-step' style='background:rgba(88,166,255,.15);color:#58A6FF'>Aprovado</span>
        <span class='flow-arrow'>→</span>
        <span class='flow-step' style='background:rgba(163,113,247,.15);color:#A371F7'>Comprado</span>
        <span class='flow-arrow'>→</span>
        <span class='flow-step' style='background:rgba(35,134,54,.15);color:#3FB950'>Entregue</span>
    </div>""", unsafe_allow_html=True)

    # KPIs
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    kpis = [
        (c1,"Total Geral",fmt(df["total"].sum()),"#58A6FF"),
        (c2,"Distribuidora",fmt(df[df["loja"]=="distribuidora"]["total"].sum()),"#58A6FF"),
        (c3,"Sublimação",fmt(df[df["loja"]=="sublimacao"]["total"].sum()),"#3FB950"),
        (c4,"Pendentes",str((df["status"]=="Pendente").sum()),"#D2991E"),
        (c5,"Aprovados",str((df["status"]=="Aprovado").sum()),"#58A6FF"),
        (c6,"Entregues",str((df["status"]=="Entregue").sum()),"#3FB950"),
    ]
    for col,lbl,val,cor in kpis:
        col.markdown(f"""
        <div class='kpi-card' style='--acc:{cor}'>
            <div class='kpi-lbl'>{lbl}</div>
            <div class='kpi-val'>{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Alertas urgência
    if "dt_necessidade" in df.columns:
        urg = df[df["dt_necessidade"].notna() & df["status"].isin(STATUS_ATIVOS)].copy()
        urg["dias"] = urg["dt_necessidade"].apply(lambda x: (date.fromisoformat(str(x))-date.today()).days if x else 999)
        urg = urg[urg["dias"]<=3].sort_values("dias")
        if not urg.empty:
            st.markdown(f"### ⚠️ {len(urg)} item(ns) com prazo crítico")
            for _,row in urg.iterrows():
                st.markdown(f"<div class='item-card'><span class='item-nome'>{row['produto']}</span> &nbsp;·&nbsp; {row['secao_nome']} &nbsp; {dias_badge(row['dt_necessidade'])}</div>",
                            unsafe_allow_html=True)
            st.divider()

    g1,g2 = st.columns(2)
    with g1:
        st.markdown("#### Por Status")
        s = df.groupby("status")["total"].sum().reset_index()
        cor_map = {"Pendente":"#D2991E","Aprovado":"#58A6FF","Comprado":"#A371F7","Entregue":"#3FB950","Cancelado":"#F85149"}
        fig = px.bar(s, x="status", y="total", color="status", color_discrete_map=cor_map, template="plotly_dark")
        fig.update_layout(showlegend=False, paper_bgcolor="#161B22", plot_bgcolor="#0D1117",
                          margin=dict(t=10,b=10), height=250, font=dict(color="#E6EDF3"),
                          xaxis=dict(gridcolor="#21262D"), yaxis=dict(gridcolor="#21262D"))
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.markdown("#### Por Loja")
        l = df.groupby("loja")["total"].sum().reset_index()
        l["nome"] = l["loja"].map({"distribuidora":"Distribuidora","sublimacao":"Sublimação"})
        fig2 = px.pie(l, names="nome", values="total",
                      color_discrete_sequence=["#58A6FF","#3FB950"], hole=.5, template="plotly_dark")
        fig2.update_layout(paper_bgcolor="#161B22", margin=dict(t=10,b=10), height=250,
                           font=dict(color="#E6EDF3"), legend=dict(bgcolor="#161B22"))
        st.plotly_chart(fig2, use_container_width=True)

    g3,g4 = st.columns(2)
    with g3:
        st.markdown("#### Top 5 Produtos Comprados")
        top = df[df["status"].isin(["Comprado","Entregue"])].groupby("produto")["qtd"].sum().sort_values(ascending=False).head(5).reset_index()
        if not top.empty:
            fig3 = px.bar(top, x="qtd", y="produto", orientation="h",
                          template="plotly_dark", color_discrete_sequence=["#58A6FF"])
            fig3.update_layout(paper_bgcolor="#161B22", plot_bgcolor="#0D1117",
                               margin=dict(t=10,b=10), height=250, font=dict(color="#E6EDF3"),
                               xaxis=dict(gridcolor="#21262D"), yaxis=dict(gridcolor="#21262D"))
            st.plotly_chart(fig3, use_container_width=True)
        else: st.caption("Nenhum comprado ainda.")

    with g4:
        st.markdown("#### Por Seção")
        sec = df.groupby(["secao_nome","loja"])["total"].sum().reset_index().sort_values("total",ascending=True)
        fig4 = px.bar(sec, x="total", y="secao_nome", orientation="h", color="loja",
                      color_discrete_map={"distribuidora":"#58A6FF","sublimacao":"#3FB950"},
                      template="plotly_dark", labels={"total":"Total","secao_nome":"","loja":"Loja"})
        fig4.update_layout(paper_bgcolor="#161B22", plot_bgcolor="#0D1117",
                           margin=dict(t=10,b=10), height=250, font=dict(color="#E6EDF3"),
                           xaxis=dict(gridcolor="#21262D"), yaxis=dict(gridcolor="#21262D"),
                           legend=dict(bgcolor="#161B22"))
        st.plotly_chart(fig4, use_container_width=True)

# ── Form de Item (add/edit) ───────────────────────────────────────────────────
def form_item(key, secao_id=None, item=None, user=""):
    """Retorna dados do item se form foi submetido, senão None."""
    forns = get_fornecedores()
    forn_opts = {f["nome"]: f["id"] for f in forns}
    forn_nomes = ["(Nenhum)"] + list(forn_opts.keys())

    with st.form(key):
        st.markdown("**Dados do Produto**")
        c1,c2,c3 = st.columns(3)
        a_prod  = c1.text_input("Produto *", value=item.get("produto","") if item else "")
        a_marca = c2.text_input("Marca / Fabricante", value=item.get("marca","") if item else "")
        a_sku   = c3.text_input("Código Interno / SKU", value=item.get("sku","") if item else "")

        c4,c5,c6 = st.columns(3)
        a_ean   = c4.text_input("Código de Barras (EAN)", value=item.get("ean","") if item else "")

        # Fornecedor
        forn_atual = "(Nenhum)"
        if item and item.get("fornecedor_id"):
            for f in forns:
                if f["id"] == item.get("fornecedor_id"):
                    forn_atual = f["nome"]; break
        forn_idx = forn_nomes.index(forn_atual) if forn_atual in forn_nomes else 0
        a_forn_nome = c5.selectbox("Fornecedor", forn_nomes, index=forn_idx)
        a_forn_id = forn_opts.get(a_forn_nome) if a_forn_nome != "(Nenhum)" else None

        a_img = c6.text_input("URL da Imagem", value=item.get("imagem_url","") if item else "",
                               placeholder="https://...")

        st.markdown("**Quantidade e Preço**")
        q1,q2,q3,q4,q5 = st.columns(5)
        a_qtd   = q1.number_input("Qtd *", min_value=0.0, value=float(item.get("qtd",0) if item else 0), step=1.0)
        a_un    = q2.selectbox("Unidade", UNIDADES,
                               index=UNIDADES.index(item.get("unidade","UN")) if item and item.get("unidade","UN") in UNIDADES else 0)
        a_preco = q3.number_input("Preço Unit. (R$)", min_value=0.0,
                                   value=float(item.get("preco_unit",0) if item else 0),
                                   step=0.01, format="%.2f")
        a_prio  = q4.selectbox("Prioridade", PRIORIDADES,
                                index=PRIORIDADES.index(item.get("prioridade","Média")) if item and item.get("prioridade") in PRIORIDADES else 1)
        a_dt    = q5.date_input("Dt. Necessidade", value=None)

        a_obs = st.text_area("Observações", value=item.get("obs","") if item else "", height=68)

        sub = st.form_submit_button("💾 Salvar" if item else "➕ Adicionar", type="primary")
        if sub:
            if not a_prod.strip(): st.warning("Informe o nome do produto."); return None
            return {
                "produto": a_prod.strip(), "marca": a_marca.strip(), "sku": a_sku.strip(),
                "ean": a_ean.strip(), "fornecedor_id": a_forn_id,
                "imagem_url": a_img.strip() or None,
                "qtd": a_qtd, "unidade": a_un, "preco_unit": a_preco,
                "total": round(a_qtd*a_preco,2), "prioridade": a_prio,
                "dt_necessidade": str(a_dt) if a_dt else None,
                "obs": a_obs.strip(), "status": item.get("status","Pendente") if item else "Pendente",
            }
    return None

# ── Página de Loja ────────────────────────────────────────────────────────────
def pagina_loja(loja):
    info = LOJAS[loja]
    cor  = info["cor"]
    fm   = forn_map()

    st.markdown(f"<div class='pg-title'>{info['icone']} {info['nome']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='pg-sub'>Lista de compras — Pendente e Aprovado | Comprado/Entregue vão para o Histórico</div>", unsafe_allow_html=True)

    # Fluxo visual
    st.markdown(f"""
    <div class='flow-bar'>
        <span class='flow-step' style='background:rgba(210,153,34,.15);color:#D2991E'>1. Pendente</span>
        <span class='flow-arrow'>→</span>
        <span class='flow-step' style='background:rgba(88,166,255,.15);color:#58A6FF'>2. Aprovado</span>
        <span class='flow-arrow'>→</span>
        <span class='flow-step' style='background:rgba(163,113,247,.2);color:#A371F7'>3. Comprado ✓ Histórico</span>
        <span class='flow-arrow'>→</span>
        <span class='flow-step' style='background:rgba(35,134,54,.2);color:#3FB950'>4. Entregue ✓ Histórico</span>
    </div>""", unsafe_allow_html=True)

    # Controles
    ca,cb,cc,cd = st.columns([3,1,1,1])
    busca = ca.text_input("🔍 Buscar", placeholder="Produto, marca, SKU, EAN...",
                          label_visibility="collapsed", key=f"bsc_{loja}")
    f_st  = cb.selectbox("Status", ["Todos"]+STATUS_ATIVOS, key=f"fst_{loja}", label_visibility="collapsed")
    f_pr  = cc.selectbox("Prioridade", ["Todas"]+PRIORIDADES, key=f"fpr_{loja}", label_visibility="collapsed")
    if cd.button("➕ Nova Seção", use_container_width=True, key=f"bns_{loja}"):
        st.session_state[f"ns_{loja}"] = True

    if st.session_state.get(f"ns_{loja}"):
        with st.form(f"fns_{loja}"):
            st.markdown("**Nova Seção**")
            nome_sec = st.text_input("Nome")
            x1,x2 = st.columns(2)
            if x1.form_submit_button("✅ Criar", type="primary"):
                if nome_sec.strip():
                    criar_secao(loja, nome_sec.strip())
                    st.session_state[f"ns_{loja}"] = False; st.rerun()
            if x2.form_submit_button("Cancelar"):
                st.session_state[f"ns_{loja}"] = False; st.rerun()

    # Seleção em lote
    sel_key = f"sel_{loja}"
    if sel_key not in st.session_state: st.session_state[sel_key] = []
    marcados = st.session_state[sel_key]
    if marcados:
        st.markdown(f"<div style='background:#1C2128;border:1px solid #30363D;border-radius:8px;padding:.8rem 1rem;margin-bottom:.8rem'><span style='color:#58A6FF;font-weight:600'>✅ {len(marcados)} item(ns) selecionado(s)</span></div>",
                    unsafe_allow_html=True)
        la,lb,lc,ld,le = st.columns(5)
        for col,lbl,st_val,tp in [(la,"✅ Aprovar","Aprovado","primary"),(lb,"🛒 Comprado","Comprado","secondary"),
                                    (lc,"📦 Entregue","Entregue","secondary"),(ld,"❌ Cancelar","Cancelado","secondary")]:
            if col.button(lbl, key=f"lote_{st_val}_{loja}", use_container_width=True, type=tp):
                atualizar_status_lote(marcados, st_val)
                st.session_state[sel_key] = []; st.rerun()
        if le.button("Limpar", key=f"clr_{loja}", use_container_width=True):
            st.session_state[sel_key] = []; st.rerun()

    secoes = get_secoes(loja)
    if not secoes:
        st.markdown("<div style='text-align:center;padding:3rem;background:#161B22;border:1px dashed #30363D;border-radius:12px;color:#8B949E'>Nenhuma seção. Clique em <b>+ Nova Seção</b>.</div>", unsafe_allow_html=True)
        return

    total_loja = 0
    for sec in secoes:
        itens = get_itens(sec["id"], status_filter=STATUS_ATIVOS)
        # filtros
        if f_st != "Todos":   itens = [i for i in itens if i.get("status")==f_st]
        if f_pr != "Todas":   itens = [i for i in itens if i.get("prioridade")==f_pr]
        if busca:
            b = busca.lower()
            itens = [i for i in itens if b in " ".join([
                i.get("produto",""), i.get("marca",""), i.get("sku",""), i.get("ean","")
            ]).lower()]

        total_sec = sum(float(i.get("total") or 0) for i in get_itens(sec["id"], STATUS_ATIVOS))
        total_loja += total_sec
        n_pend = sum(1 for i in get_itens(sec["id"], STATUS_ATIVOS) if i.get("status")=="Pendente")

        with st.expander(f"**{sec['nome']}** · {len(get_itens(sec['id'], STATUS_ATIVOS))} itens · {fmt(total_sec)}"
                         + (f" · 🟡 {n_pend} pendentes" if n_pend else ""), expanded=True):

            # Editar seção
            sc1,sc2,sc3 = st.columns([4,1.5,1])
            novo_nome = sc1.text_input("", value=sec["nome"], key=f"rn_{sec['id']}",
                                       label_visibility="collapsed")
            if sc2.button("💾 Salvar nome", key=f"svn_{sec['id']}", use_container_width=True):
                if novo_nome.strip() and novo_nome != sec["nome"]:
                    editar_secao(sec["id"], novo_nome.strip()); st.rerun()
            if sc3.button("🗑 Arquivar", key=f"arc_{sec['id']}", use_container_width=True):
                arquivar_secao(sec["id"]); st.rerun()

            st.divider()

            if itens:
                for item in itens:
                    iid = item["id"]
                    dias = None
                    if item.get("dt_necessidade"):
                        try: dias = (date.fromisoformat(str(item["dt_necessidade"])) - date.today()).days
                        except: pass

                    selecionado = iid in st.session_state.get(sel_key,[])
                    c0,c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([.4,3.5,1.5,.8,.8,1.5,1.2,1.2,.8])

                    sel = c0.checkbox("", value=selecionado, key=f"chk_{iid}", label_visibility="collapsed")
                    if sel and iid not in st.session_state.get(sel_key,[]):
                        st.session_state.setdefault(sel_key,[]).append(iid)
                    elif not sel and iid in st.session_state.get(sel_key,[]):
                        st.session_state[sel_key].remove(iid)

                    # Imagem + nome
                    img_url = item.get("imagem_url","")
                    meta = " · ".join(filter(None,[item.get("marca",""), item.get("sku",""), item.get("ean","")]))
                    forn_nome = fm.get(item.get("fornecedor_id"),"")
                    c1.markdown(f"""
                    <div style='display:flex;align-items:center;gap:.6rem'>
                        {'<img src="'+img_url+'" style="width:36px;height:36px;object-fit:cover;border-radius:6px;border:1px solid #30363D">' if img_url else '<div style="width:36px;height:36px;background:#21262D;border-radius:6px;border:1px solid #30363D;display:flex;align-items:center;justify-content:center;font-size:.8rem">📦</div>'}
                        <div>
                            <div class='item-nome'>{item.get('produto','')}</div>
                            <div class='item-meta'>{meta}{' · '+forn_nome if forn_nome else ''}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    c2.markdown(f"<div style='font-size:.8rem;color:#8B949E;margin-top:.3rem'>{sec['nome']}</div>", unsafe_allow_html=True)
                    c3.markdown(f"<div style='text-align:center;font-size:.9rem;margin-top:.3rem'>{item.get('qtd','')} {item.get('unidade','')}</div>", unsafe_allow_html=True)
                    c4.markdown(f"<div style='text-align:right;font-size:.82rem;color:#8B949E;margin-top:.3rem'>{fmt(item.get('preco_unit',0))}</div>", unsafe_allow_html=True)
                    c5.markdown(f"<div style='text-align:right;font-weight:700;color:{cor};margin-top:.3rem'>{fmt(item.get('total',0))}</div>", unsafe_allow_html=True)
                    c6.markdown(badge(item.get("status",""))+" "+dias_badge(item.get("dt_necessidade")), unsafe_allow_html=True)
                    c7.markdown(badge(item.get("prioridade","")), unsafe_allow_html=True)

                    with c8:
                        with st.popover("···"):
                            st.markdown(f"**{item.get('produto','')}**")
                            if img_url:
                                st.image(img_url, width=120)
                            novo_st = st.selectbox("Status", STATUS_FLUXO,
                                                   index=STATUS_FLUXO.index(item.get("status","Pendente")),
                                                   key=f"pst_{iid}")
                            if st.button("Salvar status", key=f"svst_{iid}", type="primary"):
                                atualizar_item(iid, {"status":novo_st}); st.rerun()
                            st.divider()
                            if st.button("✏️ Editar item", key=f"edbtn_{iid}"):
                                st.session_state[f"ed_{iid}"] = True
                            if st.button("🗑 Deletar", key=f"del_{iid}"):
                                deletar_item(iid); st.rerun()

                    if st.session_state.get(f"ed_{iid}"):
                        st.markdown("---")
                        result = form_item(f"fedit_{iid}", item=item, user=u["nome"])
                        if result is not None:
                            atualizar_item(iid, result)
                            st.session_state[f"ed_{iid}"] = False; st.rerun()
                        if st.button("Cancelar edição", key=f"cedit_{iid}"):
                            st.session_state[f"ed_{iid}"] = False; st.rerun()
            else:
                st.markdown("<div style='color:#8B949E;padding:.5rem 0'>Nenhum item com os filtros selecionados.</div>", unsafe_allow_html=True)

            # Adicionar
            st.markdown("---")
            with st.expander("➕ Adicionar item nesta seção"):
                result = form_item(f"fadd_{sec['id']}", secao_id=sec["id"], user=u["nome"])
                if result is not None:
                    inserir_item(sec["id"], result, u["nome"]); st.rerun()

    st.markdown(f"""
    <div style='background:#161B22;border:1px solid #21262D;border-radius:10px;
                padding:1rem 1.5rem;margin-top:1rem;text-align:right'>
        <span style='color:#8B949E'>{info['nome']} — Total em aberto:</span>
        <span style='color:{cor};font-size:1.3rem;font-weight:700;margin-left:1rem'>{fmt(total_loja)}</span>
    </div>""", unsafe_allow_html=True)

# ── Histórico ─────────────────────────────────────────────────────────────────
def pagina_historico():
    st.markdown("<div class='pg-title'>📅 Histórico</div>", unsafe_allow_html=True)
    st.markdown("<div class='pg-sub'>Itens com status Comprado, Entregue ou Cancelado</div>", unsafe_allow_html=True)

    todos = get_todos_itens(status_filter=STATUS_HISTORICO)
    if not todos: st.info("Nenhum item no histórico ainda."); return

    df = pd.DataFrame(todos)
    df["loja"]       = df["pc_secoes"].apply(lambda x: x["loja"] if x else "")
    df["secao_nome"] = df["pc_secoes"].apply(lambda x: x["nome"] if x else "")
    df["total"]      = pd.to_numeric(df.get("total",0), errors="coerce").fillna(0)
    df["loja_nome"]  = df["loja"].map({"distribuidora":"Distribuidora","sublimacao":"Sublimação"})

    # Filtros
    f1,f2,f3,f4,f5 = st.columns(5)
    fl = f1.selectbox("Loja",["Todas","Distribuidora","Sublimação"], label_visibility="collapsed")
    fs = f2.selectbox("Status",["Todos"]+STATUS_HISTORICO, label_visibility="collapsed")
    fp = f3.selectbox("Prioridade",["Todas"]+PRIORIDADES, label_visibility="collapsed")
    fb = f4.text_input("Buscar","", placeholder="Produto...", label_visibility="collapsed")
    fsec = f5.selectbox("Seção",["Todas"]+sorted(df["secao_nome"].unique().tolist()), label_visibility="collapsed")

    dff = df.copy()
    if fl!="Todas": dff=dff[dff["loja"]==("distribuidora" if fl=="Distribuidora" else "sublimacao")]
    if fs!="Todos": dff=dff[dff["status"]==fs]
    if fp!="Todas": dff=dff[dff["prioridade"]==fp]
    if fb: dff=dff[dff["produto"].str.lower().str.contains(fb.lower(),na=False)]
    if fsec!="Todas": dff=dff[dff["secao_nome"]==fsec]

    st.markdown(f"<div style='color:#8B949E;font-size:.85rem;margin:.5rem 0'>{len(dff)} itens · Total: <b style='color:#58A6FF'>{fmt(dff['total'].sum())}</b></div>", unsafe_allow_html=True)

    cols = ["produto","marca","sku","ean","secao_nome","loja_nome","fornecedor_id",
            "qtd","unidade","total","prioridade","status","dt_necessidade","obs","criado_por","criado_em"]
    cols_ex = [c for c in cols if c in dff.columns]

    fm = forn_map()
    if "fornecedor_id" in dff.columns:
        dff["fornecedor"] = dff["fornecedor_id"].map(fm).fillna("")

    rename = {"produto":"Produto","marca":"Marca","sku":"SKU","ean":"EAN",
               "secao_nome":"Seção","loja_nome":"Loja","fornecedor":"Fornecedor",
               "qtd":"Qtd","unidade":"Unid","total":"Total (R$)","prioridade":"Prioridade",
               "status":"Status","dt_necessidade":"Dt. Necessidade","obs":"Obs",
               "criado_por":"Criado por","criado_em":"Criado em"}
    st.dataframe(dff[[c for c in cols_ex if c in dff.columns]].rename(columns=rename),
                 use_container_width=True, hide_index=True, height=500)

# ── Fornecedores ──────────────────────────────────────────────────────────────
def pagina_fornecedores():
    st.markdown("<div class='pg-title'>🏭 Fornecedores</div>", unsafe_allow_html=True)
    st.markdown("<div class='pg-sub'>Cadastro completo de fornecedores</div>", unsafe_allow_html=True)

    tab_lista, tab_novo = st.tabs(["📋 Lista de Fornecedores", "➕ Novo Fornecedor"])

    with tab_novo:
        with st.form("f_novo_forn"):
            st.markdown("**Dados do Fornecedor**")
            n1,n2 = st.columns(2)
            f_nome    = n1.text_input("Nome *")
            f_contato = n2.text_input("Nome do Contato")
            n3,n4,n5 = st.columns(3)
            f_tel  = n3.text_input("Telefone / WhatsApp")
            f_email= n4.text_input("E-mail")
            f_cnpj = n5.text_input("CNPJ")
            f_obs  = st.text_area("Observações", height=80)
            if st.form_submit_button("✅ Cadastrar Fornecedor", type="primary"):
                if f_nome.strip():
                    criar_fornecedor({"nome":f_nome.strip(),"contato":f_contato,"telefone":f_tel,
                                      "email":f_email,"cnpj":f_cnpj,"observacoes":f_obs,"ativo":True})
                    st.success(f"✅ Fornecedor '{f_nome}' cadastrado!")
                    st.rerun()
                else:
                    st.warning("Informe o nome do fornecedor.")

    with tab_lista:
        forns = get_fornecedores()
        if not forns:
            st.info("Nenhum fornecedor cadastrado.")
            return

        busca_f = st.text_input("🔍 Buscar fornecedor", placeholder="Nome, CNPJ...",
                                label_visibility="collapsed")
        if busca_f:
            forns = [f for f in forns if busca_f.lower() in (f["nome"]+f.get("cnpj","")).lower()]

        for forn in forns:
            with st.expander(f"🏭 **{forn['nome']}**" +
                             (f" · {forn.get('telefone','')}" if forn.get("telefone") else "") +
                             (f" · {forn.get('cnpj','')}" if forn.get("cnpj") else "")):
                with st.form(f"edit_forn_{forn['id']}"):
                    st.markdown("**Editar Fornecedor**")
                    e1,e2 = st.columns(2)
                    e_nome    = e1.text_input("Nome *", value=forn.get("nome",""))
                    e_contato = e2.text_input("Contato", value=forn.get("contato",""))
                    e3,e4,e5 = st.columns(3)
                    e_tel  = e3.text_input("Telefone", value=forn.get("telefone",""))
                    e_email= e4.text_input("E-mail", value=forn.get("email",""))
                    e_cnpj = e5.text_input("CNPJ", value=forn.get("cnpj",""))
                    e_obs  = st.text_area("Observações", value=forn.get("observacoes",""), height=68)
                    s1,s2,s3 = st.columns(3)
                    if s1.form_submit_button("💾 Salvar", type="primary"):
                        editar_fornecedor(forn["id"], {"nome":e_nome,"contato":e_contato,
                            "telefone":e_tel,"email":e_email,"cnpj":e_cnpj,"observacoes":e_obs})
                        st.success("✅ Salvo!"); st.rerun()
                    if s3.form_submit_button("🗑 Remover"):
                        deletar_fornecedor(forn["id"]); st.rerun()

# ── Exportar ──────────────────────────────────────────────────────────────────
def gerar_excel(loja_filtro="ambas", include_historico=False):
    wb = Workbook(); ws = wb.active; ws.title = "Compras"
    def thin():
        s = Side(style="thin",color="2D3748")
        return Border(left=s,right=s,top=s,bottom=s)

    lojas = ["distribuidora","sublimacao"] if loja_filtro=="ambas" else [loja_filtro]
    row = 1
    ws.merge_cells(f"A{row}:L{row}")
    c=ws.cell(row=row,column=1,value="GRUPO PRATES — GUIA DE COMPRAS")
    c.font=Font(name="Calibri",bold=True,size=14,color="FFFFFF")
    c.fill=PatternFill("solid",start_color="0D1117")
    c.alignment=Alignment(horizontal="center",vertical="center")
    ws.row_dimensions[row].height=28; row+=1

    ws.merge_cells(f"A{row}:L{row}")
    c=ws.cell(row=row,column=1,value=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.font=Font(name="Calibri",italic=True,size=9,color="8B949E")
    c.fill=PatternFill("solid",start_color="161B22")
    c.alignment=Alignment(horizontal="right",vertical="center")
    ws.row_dimensions[row].height=16; row+=1

    headers=["Seção","Produto","Marca","SKU","EAN","Fornecedor","Qtd","Unid","Preço","Total","Prioridade","Status"]
    widths=[20,28,16,14,14,18,7,6,12,12,12,12]
    for i,(h,w) in enumerate(zip(headers,widths),1):
        ws.column_dimensions[get_column_letter(i)].width=w
        c=ws.cell(row=row,column=i,value=h)
        c.font=Font(name="Calibri",bold=True,color="E6EDF3",size=9)
        c.fill=PatternFill("solid",start_color="21262D")
        c.alignment=Alignment(horizontal="center",vertical="center"); c.border=thin()
    ws.row_dimensions[row].height=18; row+=1

    fm = forn_map()
    sf = None if include_historico else STATUS_ATIVOS
    for loja in lojas:
        info=LOJAS[loja]; secoes=get_secoes(loja)
        ws.merge_cells(f"A{row}:L{row}")
        c=ws.cell(row=row,column=1,value=f"  {info['icone']}  {info['nome'].upper()}")
        c.font=Font(name="Calibri",bold=True,size=11,color="FFFFFF")
        c.fill=PatternFill("solid",start_color="161B22")
        c.alignment=Alignment(horizontal="left",vertical="center"); c.border=thin()
        ws.row_dimensions[row].height=20; row+=1; tl=0
        for sec in secoes:
            itens=get_itens(sec["id"],status_filter=sf)
            if not itens: continue
            ts=0
            for ri,item in enumerate(itens):
                zb="0D1117" if ri%2==0 else "161B22"
                vals=[sec["nome"],item.get("produto",""),item.get("marca",""),
                      item.get("sku",""),item.get("ean",""),
                      fm.get(item.get("fornecedor_id"),""),
                      item.get("qtd",""),item.get("unidade",""),
                      item.get("preco_unit",""),item.get("total",""),
                      item.get("prioridade",""),item.get("status","")]
                for ci,v in enumerate(vals,1):
                    c=ws.cell(row=row,column=ci,value=v)
                    c.font=Font(name="Calibri",size=9,color="E6EDF3")
                    c.fill=PatternFill("solid",start_color=zb)
                    c.alignment=Alignment(horizontal="center" if ci>5 else "left",vertical="center"); c.border=thin()
                    if ci in (9,10) and v: c.number_format='"R$" #,##0.00'
                ws.row_dimensions[row].height=16; ts+=float(item.get("total") or 0); row+=1
            tl+=ts
        ws.merge_cells(f"A{row}:I{row}")
        c=ws.cell(row=row,column=1,value=f"TOTAL {info['nome'].upper()}")
        c.font=Font(name="Calibri",bold=True,size=10,color="FFFFFF")
        c.fill=PatternFill("solid",start_color="0D1117")
        c.alignment=Alignment(horizontal="right",vertical="center"); c.border=thin()
        c=ws.cell(row=row,column=10,value=tl)
        c.font=Font(name="Calibri",bold=True,size=10,color="58A6FF")
        c.fill=PatternFill("solid",start_color="0D1117")
        c.alignment=Alignment(horizontal="right",vertical="center")
        c.number_format='"R$" #,##0.00'; c.border=thin()
        for ci in [9,11,12]:
            ws.cell(row=row,column=ci).fill=PatternFill("solid",start_color="0D1117")
            ws.cell(row=row,column=ci).border=thin()
        ws.row_dimensions[row].height=22; row+=2

    buf=io.BytesIO(); wb.save(buf); buf.seek(0); return buf

def pagina_exportar():
    st.markdown("<div class='pg-title'>📥 Exportar</div>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        loja_exp = st.selectbox("Loja",["Ambas","Prates Distribuidora","Prates Sublimação"])
        lk = {"Ambas":"ambas","Prates Distribuidora":"distribuidora","Prates Sublimação":"sublimacao"}[loja_exp]
        inc_hist = st.checkbox("Incluir Histórico (Comprado/Entregue)")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 Gerar Excel", use_container_width=True, type="primary"):
            buf = gerar_excel(lk, inc_hist)
            st.download_button("⬇️ Baixar Excel", buf,
                file_name=f"Compras_Prates_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)

# ── Admin ─────────────────────────────────────────────────────────────────────
def pagina_admin():
    st.markdown("<div class='pg-title'>⚙️ Administração</div>", unsafe_allow_html=True)
    tab_u,tab_s = st.tabs(["👤 Usuários","📂 Seções"])

    with tab_u:
        st.markdown("#### Novo Usuário")
        with st.form("f_usr"):
            c1,c2=st.columns(2)
            nome=c1.text_input("Nome"); email=c2.text_input("E-mail")
            c3,c4=st.columns(2)
            senha=c3.text_input("Senha",type="password")
            acesso=c4.selectbox("Acesso",["distribuidora","sublimacao","ambas","admin"],
                format_func=lambda x:{"distribuidora":"Só Distribuidora","sublimacao":"Só Sublimação",
                                       "ambas":"Ambas","admin":"Administrador"}[x])
            if st.form_submit_button("✅ Criar",type="primary"):
                if nome and email and senha: criar_usuario(nome,email,senha,acesso); st.success("✅ Criado!"); st.rerun()
                else: st.warning("Preencha todos os campos.")

        st.markdown("#### Usuários")
        for uu in get_usuarios():
            with st.expander(f"👤 **{uu['nome']}** · {uu['email']} · {uu['acesso']}"):
                with st.form(f"eu_{uu['id']}"):
                    eu1,eu2=st.columns(2)
                    e_nome=eu1.text_input("Nome",value=uu["nome"])
                    e_email=eu2.text_input("E-mail",value=uu["email"])
                    eu3,eu4=st.columns(2)
                    e_acesso=eu3.selectbox("Acesso",["distribuidora","sublimacao","ambas","admin"],
                        index=["distribuidora","sublimacao","ambas","admin"].index(uu["acesso"]),
                        format_func=lambda x:{"distribuidora":"Só Distribuidora","sublimacao":"Só Sublimação",
                                               "ambas":"Ambas","admin":"Administrador"}[x])
                    e_nova_senha=eu4.text_input("Nova Senha (deixe em branco para manter)",type="password")
                    s1,s2=st.columns(2)
                    if s1.form_submit_button("💾 Salvar",type="primary"):
                        dados={"nome":e_nome,"email":e_email,"acesso":e_acesso}
                        if e_nova_senha: dados["senha_hash"]=hash_pw(e_nova_senha)
                        editar_usuario(uu["id"],dados); st.success("✅ Salvo!"); st.rerun()
                    lbl="❌ Desativar" if uu["ativo"] else "✅ Ativar"
                    if s2.form_submit_button(lbl):
                        editar_usuario(uu["id"],{"ativo":not uu["ativo"]}); st.rerun()

    with tab_s:
        for loja,info in LOJAS.items():
            st.markdown(f"#### {info['icone']} {info['nome']}")
            for sec in get_secoes(loja):
                with st.form(f"as_{sec['id']}"):
                    s1,s2,s3=st.columns([4,1.5,1])
                    nn=s1.text_input("",value=sec["nome"],label_visibility="collapsed")
                    if s2.form_submit_button("💾 Salvar"):
                        editar_secao(sec["id"],nn); st.rerun()
                    if s3.form_submit_button("🗑"):
                        arquivar_secao(sec["id"]); st.rerun()
            st.divider()

# ── Roteador ──────────────────────────────────────────────────────────────────
pg = st.session_state.pagina
if   pg=="dashboard":     pagina_dashboard()
elif pg=="distribuidora":
    if pode_ver("distribuidora"): pagina_loja("distribuidora")
    else: st.error("Acesso negado.")
elif pg=="sublimacao":
    if pode_ver("sublimacao"): pagina_loja("sublimacao")
    else: st.error("Acesso negado.")
elif pg=="historico":     pagina_historico()
elif pg=="exportar":      pagina_exportar()
elif pg=="fornecedores":  pagina_fornecedores()
elif pg=="admin":
    if u["acesso"]=="admin": pagina_admin()
    else: st.error("Acesso restrito.")
