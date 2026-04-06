import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib
from datetime import date, datetime
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

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Prates — Guia de Compras",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

LOJAS = {
    "distribuidora": {"nome": "Prates Distribuidora", "cor": "#1F3864", "icone": "📦"},
    "sublimacao":    {"nome": "Prates Sublimação",    "cor": "#1E4620", "icone": "🎨"},
}

UNIDADES   = ["UN","CX","PCT","KG","MT","LT","RL","PAR"]
PRIORIDADES = ["Alta","Média","Baixa"]
STATUS_OPS  = ["Pendente","Aprovado","Comprado","Entregue","Cancelado"]
STATUS_COR  = {
    "Pendente":  "#FFA500",
    "Aprovado":  "#2196F3",
    "Comprado":  "#9C27B0",
    "Entregue":  "#4CAF50",
    "Cancelado": "#F44336",
}

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #F5F7FA; }
[data-testid="stSidebar"] { background: #1F3864 !important; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2) !important; }
.bloco-secao {
    background: white; border-radius: 12px; padding: 1.2rem 1.5rem;
    margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    border-left: 5px solid #2E75B6;
}
.bloco-secao-sub { border-left-color: #2E7D32 !important; }
.card-kpi {
    background: white; border-radius: 12px; padding: 1.2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center;
}
.titulo-pagina {
    font-size: 1.6rem; font-weight: 700; margin-bottom: 0.3rem;
}
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; color: white;
}
div[data-testid="stForm"] { background: white; border-radius: 12px; padding: 1rem; }
</style>
""", unsafe_allow_html=True)

# ─── SUPABASE ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_sb() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

sb = get_sb()

# ─── HELPERS DB ───────────────────────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def login_user(email: str, senha: str):
    r = sb.table("pc_usuarios").select("*").eq("email", email.strip().lower()).eq("ativo", True).execute()
    if not r.data:
        return None
    u = r.data[0]
    return u if u["senha_hash"] == hash_pw(senha) else None

def get_secoes(loja: str):
    r = sb.table("pc_secoes").select("*").eq("loja", loja).eq("ativa", True).order("ordem").execute()
    return r.data or []

def get_itens(secao_id: int):
    r = sb.table("pc_itens").select("*").eq("secao_id", secao_id).order("criado_em", desc=False).execute()
    return r.data or []

def get_itens_loja(loja: str):
    secoes = get_secoes(loja)
    ids = [s["id"] for s in secoes]
    if not ids:
        return []
    r = sb.table("pc_itens").select("*, pc_secoes(nome)").in_("secao_id", ids).execute()
    return r.data or []

def get_todos_itens():
    r = sb.table("pc_itens").select("*, pc_secoes(nome, loja)").execute()
    return r.data or []

def inserir_item(secao_id, dados, usuario_nome):
    dados["secao_id"] = secao_id
    dados["criado_por"] = usuario_nome
    dados["criado_em"] = datetime.now().isoformat()
    dados["atualizado_em"] = datetime.now().isoformat()
    sb.table("pc_itens").insert(dados).execute()

def atualizar_item(item_id, dados):
    dados["atualizado_em"] = datetime.now().isoformat()
    sb.table("pc_itens").update(dados).eq("id", item_id).execute()

def deletar_item(item_id):
    sb.table("pc_itens").delete().eq("id", item_id).execute()

def atualizar_status(item_id, status):
    sb.table("pc_itens").update({"status": status, "atualizado_em": datetime.now().isoformat()}).eq("id", item_id).execute()

def criar_secao(loja, nome):
    secoes = get_secoes(loja)
    ordem = (max([s["ordem"] for s in secoes]) + 1) if secoes else 1
    sb.table("pc_secoes").insert({"loja": loja, "nome": nome, "ordem": ordem, "ativa": True}).execute()

def renomear_secao(secao_id, novo_nome):
    sb.table("pc_secoes").update({"nome": novo_nome}).eq("id", secao_id).execute()

def arquivar_secao(secao_id):
    sb.table("pc_secoes").update({"ativa": False}).eq("id", secao_id).execute()

def get_usuarios():
    r = sb.table("pc_usuarios").select("id, nome, email, acesso, ativo").order("nome").execute()
    return r.data or []

def criar_usuario(nome, email, senha, acesso):
    sb.table("pc_usuarios").insert({
        "nome": nome, "email": email.lower(),
        "senha_hash": hash_pw(senha), "acesso": acesso, "ativo": True
    }).execute()

def toggle_usuario(uid, ativo):
    sb.table("pc_usuarios").update({"ativo": ativo}).eq("id", uid).execute()

def pode_ver(loja: str) -> bool:
    u = st.session_state.get("usuario")
    if not u:
        return False
    return u["acesso"] in ("admin", "ambas", loja)

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in [("usuario", None), ("pagina", "dashboard"), ("loja_ativa", "distribuidora")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── LOGIN ────────────────────────────────────────────────────────────────────
def pagina_login():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("""
        <div style='text-align:center;padding:60px 0 30px'>
            <div style='font-size:3rem'>🛒</div>
            <h1 style='color:#1F3864;margin:0'>Prates</h1>
            <p style='color:#888;font-size:1.1rem'>Guia de Compras</p>
        </div>""", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("E-mail", placeholder="seuemail@prates.com")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar →", use_container_width=True, type="primary"):
                u = login_user(email, senha)
                if u:
                    st.session_state.usuario = u
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")

if not st.session_state.usuario:
    pagina_login()
    st.stop()

u = st.session_state.usuario

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='padding:16px 0 8px;text-align:center'>
        <div style='font-size:2rem'>🛒</div>
        <div style='font-size:1.1rem;font-weight:700'>Guia de Compras</div>
        <div style='font-size:0.8rem;opacity:0.7'>Grupo Prates</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    st.markdown(f"👤 **{u['nome']}**")
    st.markdown(f"<small style='opacity:.6'>{u['email']}</small>", unsafe_allow_html=True)
    st.divider()

    def nav_btn(label, pagina, icone=""):
        ativo = st.session_state.pagina == pagina
        if st.button(f"{icone} {label}", use_container_width=True,
                     type="primary" if ativo else "secondary"):
            st.session_state.pagina = pagina
            st.rerun()

    nav_btn("Dashboard", "dashboard", "📊")
    st.markdown("**Lançamento**")
    if pode_ver("distribuidora"):
        nav_btn("Prates Distribuidora", "distribuidora", "📦")
    if pode_ver("sublimacao"):
        nav_btn("Prates Sublimação",    "sublimacao",    "🎨")
    nav_btn("Exportar",   "exportar",   "📥")
    if u["acesso"] == "admin":
        st.divider()
        nav_btn("Administração", "admin", "⚙️")
    st.divider()
    if st.button("Sair", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def pagina_dashboard():
    st.markdown("<div class='titulo-pagina'>📊 Dashboard Geral</div>", unsafe_allow_html=True)
    st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    todos = get_todos_itens()
    if not todos:
        st.info("Nenhum item lançado ainda. Use as abas de cada loja para começar.")
        return

    df = pd.DataFrame(todos)
    df["loja"]      = df["pc_secoes"].apply(lambda x: x["loja"] if x else "")
    df["secao_nome"]= df["pc_secoes"].apply(lambda x: x["nome"] if x else "")
    df["total"]     = pd.to_numeric(df.get("total", 0), errors="coerce").fillna(0)
    df["qtd"]       = pd.to_numeric(df.get("qtd", 0), errors="coerce").fillna(0)

    # KPIs
    total_geral   = df["total"].sum()
    total_dist    = df[df["loja"]=="distribuidora"]["total"].sum()
    total_sub     = df[df["loja"]=="sublimacao"]["total"].sum()
    n_pendentes   = (df["status"]=="Pendente").sum()
    n_aprovados   = (df["status"]=="Aprovado").sum()
    n_comprados   = (df["status"]=="Comprado").sum()

    c1,c2,c3,c4,c5 = st.columns(5)
    def kpi(col, label, valor, sub=None, cor="#1F3864"):
        col.markdown(f"""
        <div class='card-kpi'>
            <div style='color:#888;font-size:.8rem'>{label}</div>
            <div style='font-size:1.5rem;font-weight:700;color:{cor}'>{valor}</div>
            {"<div style='color:#aaa;font-size:.75rem'>"+sub+"</div>" if sub else ""}
        </div>""", unsafe_allow_html=True)

    kpi(c1, "Total Geral", f"R$ {total_geral:,.2f}".replace(",","X").replace(".",",").replace("X","."))
    kpi(c2, "Distribuidora", f"R$ {total_dist:,.2f}".replace(",","X").replace(".",",").replace("X","."), cor="#1F3864")
    kpi(c3, "Sublimação", f"R$ {total_sub:,.2f}".replace(",","X").replace(".",",").replace("X","."), cor="#1E4620")
    kpi(c4, "Pendentes / Aprovados", f"{n_pendentes} / {n_aprovados}", cor="#FFA500")
    kpi(c5, "Comprados", str(n_comprados), cor="#9C27B0")

    st.markdown("<br>", unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("#### Total por Status")
        status_df = df.groupby("status")["total"].sum().reset_index()
        status_df.columns = ["Status","Total"]
        cmap = {s: c for s,c in STATUS_COR.items()}
        colors_list = [cmap.get(s, "#999") for s in status_df["Status"]]
        fig = px.bar(status_df, x="Status", y="Total",
                     color="Status", color_discrete_map=STATUS_COR,
                     text_auto=True)
        fig.update_layout(showlegend=False, margin=dict(t=10,b=10), height=280,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_traces(texttemplate="R$ %{y:,.0f}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_g2:
        st.markdown("#### Distribuição por Loja")
        loja_df = df.groupby("loja")["total"].sum().reset_index()
        loja_df["loja_nome"] = loja_df["loja"].map({"distribuidora":"Distribuidora","sublimacao":"Sublimação"})
        fig2 = px.pie(loja_df, names="loja_nome", values="total",
                      color_discrete_sequence=["#2E75B6","#2E7D32"],
                      hole=0.4)
        fig2.update_layout(margin=dict(t=10,b=10), height=280,
                           paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    col_g3, col_g4 = st.columns(2)
    with col_g3:
        st.markdown("#### Total por Seção")
        sec_df = df.groupby(["secao_nome","loja"])["total"].sum().reset_index().sort_values("total", ascending=True)
        sec_df["cor"] = sec_df["loja"].map({"distribuidora":"#2E75B6","sublimacao":"#2E7D32"})
        fig3 = px.bar(sec_df, x="total", y="secao_nome", orientation="h",
                      color="loja", color_discrete_map={"distribuidora":"#2E75B6","sublimacao":"#2E7D32"},
                      labels={"total":"Total (R$)","secao_nome":"Seção","loja":"Loja"})
        fig3.update_layout(showlegend=True, margin=dict(t=10,b=10), height=320,
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)

    with col_g4:
        st.markdown("#### Itens por Prioridade")
        prio_df = df.groupby("prioridade").size().reset_index(name="count")
        fig4 = px.pie(prio_df, names="prioridade", values="count",
                      color_discrete_map={"Alta":"#F44336","Média":"#FF9800","Baixa":"#4CAF50"},
                      hole=0.35)
        fig4.update_layout(margin=dict(t=10,b=10), height=320,
                           paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Todos os Itens")
    cols_show = ["produto","secao_nome","loja","fornecedor","qtd","unidade","total","prioridade","status","dt_necessidade"]
    cols_exist = [c for c in cols_show if c in df.columns]
    st.dataframe(
        df[cols_exist].rename(columns={
            "produto":"Produto","secao_nome":"Seção","loja":"Loja",
            "fornecedor":"Fornecedor","qtd":"Qtd","unidade":"Unid",
            "total":"Total (R$)","prioridade":"Prioridade","status":"Status",
            "dt_necessidade":"Dt. Necessidade"
        }),
        use_container_width=True, hide_index=True
    )

# ─── PÁGINA DE LOJA ───────────────────────────────────────────────────────────
def pagina_loja(loja: str):
    info = LOJAS[loja]
    cls  = "bloco-secao" + (" bloco-secao-sub" if loja=="sublimacao" else "")
    cor  = info["cor"]

    st.markdown(f"<div class='titulo-pagina' style='color:{cor}'>{info['icone']} {info['nome']}</div>",
                unsafe_allow_html=True)

    # Barra de ações rápidas
    ca, cb, cc = st.columns([3,1,1])
    with ca:
        st.markdown(f"**{len(get_secoes(loja))} seções ativas**")
    with cb:
        if u["acesso"] in ("admin","ambas", loja):
            if st.button("➕ Nova Seção", use_container_width=True, key=f"btn_nova_{loja}"):
                st.session_state[f"show_nova_secao_{loja}"] = True
    with cc:
        filtro_status = st.selectbox("Filtrar status", ["Todos"]+STATUS_OPS,
                                     key=f"filtro_{loja}", label_visibility="collapsed")

    # Form nova seção
    if st.session_state.get(f"show_nova_secao_{loja}"):
        with st.form(f"form_nova_secao_{loja}"):
            nome_sec = st.text_input("Nome da nova seção")
            c1,c2 = st.columns(2)
            if c1.form_submit_button("Criar", type="primary"):
                if nome_sec.strip():
                    criar_secao(loja, nome_sec.strip())
                    st.session_state[f"show_nova_secao_{loja}"] = False
                    st.rerun()
            if c2.form_submit_button("Cancelar"):
                st.session_state[f"show_nova_secao_{loja}"] = False
                st.rerun()

    secoes = get_secoes(loja)
    if not secoes:
        st.info("Nenhuma seção cadastrada. Clique em '➕ Nova Seção' para começar.")
        return

    for sec in secoes:
        itens = get_itens(sec["id"])
        # filtro de status
        itens_filt = itens if filtro_status == "Todos" else [i for i in itens if i.get("status")==filtro_status]
        total_sec = sum(float(i.get("total") or 0) for i in itens)
        n = len(itens)

        with st.expander(f"**{sec['nome']}** — {n} item{'ns' if n!=1 else ''} | R$ {total_sec:,.2f}".replace(",","X").replace(".",",").replace("X","."), expanded=True):

            # Renomear / arquivar seção
            col_r, col_a, _ = st.columns([2,1,4])
            with col_r:
                novo_nome = st.text_input("Renomear", value=sec["nome"],
                                          key=f"rename_{sec['id']}", label_visibility="collapsed")
                if novo_nome != sec["nome"]:
                    if st.button("Salvar nome", key=f"save_rename_{sec['id']}"):
                        renomear_secao(sec["id"], novo_nome)
                        st.rerun()
            with col_a:
                if st.button("🗑 Arquivar seção", key=f"arch_{sec['id']}"):
                    arquivar_secao(sec["id"])
                    st.rerun()

            st.divider()

            # Tabela de itens
            if itens_filt:
                for item in itens_filt:
                    total_item = float(item.get("total") or 0)
                    scor = STATUS_COR.get(item.get("status",""), "#999")
                    ci1,ci2,ci3,ci4,ci5,ci6,ci7 = st.columns([3,2,1,1,1.5,1.5,1.5])
                    ci1.markdown(f"**{item['produto']}**")
                    ci2.markdown(f"<small>{item.get('fornecedor','—')}</small>", unsafe_allow_html=True)
                    ci3.markdown(f"{item.get('qtd','')} {item.get('unidade','')}")
                    ci4.markdown(f"R$ {float(item.get('preco_unit') or 0):,.2f}".replace(",","X").replace(".",",").replace("X","."))
                    ci5.markdown(f"**R$ {total_item:,.2f}**".replace(",","X").replace(".",",").replace("X","."))
                    ci6.markdown(f"<span class='badge' style='background:{scor}'>{item.get('status','')}</span>",
                                 unsafe_allow_html=True)
                    with ci7:
                        with st.popover("•••"):
                            st.markdown(f"**{item['produto']}**")
                            novo_st = st.selectbox("Status", STATUS_OPS,
                                                   index=STATUS_OPS.index(item.get("status","Pendente")),
                                                   key=f"st_{item['id']}")
                            if st.button("Salvar status", key=f"svst_{item['id']}"):
                                atualizar_status(item["id"], novo_st)
                                st.rerun()
                            st.divider()
                            if st.button("✏️ Editar item", key=f"edit_btn_{item['id']}"):
                                st.session_state[f"edit_{item['id']}"] = True
                            if st.button("🗑 Deletar", key=f"del_{item['id']}"):
                                deletar_item(item["id"])
                                st.rerun()

                    # Form de edição inline
                    if st.session_state.get(f"edit_{item['id']}"):
                        with st.form(f"form_edit_{item['id']}"):
                            ep1,ep2 = st.columns(2)
                            e_prod = ep1.text_input("Produto", value=item.get("produto",""))
                            e_forn = ep2.text_input("Fornecedor", value=item.get("fornecedor",""))
                            eq1,eq2,eq3,eq4 = st.columns(4)
                            e_qtd   = eq1.number_input("Qtd", min_value=0.0, value=float(item.get("qtd") or 0), step=1.0)
                            e_un    = eq2.selectbox("Unid", UNIDADES, index=UNIDADES.index(item.get("unidade","UN")) if item.get("unidade","UN") in UNIDADES else 0)
                            e_preco = eq3.number_input("Preço Unit.", min_value=0.0, value=float(item.get("preco_unit") or 0), step=0.01, format="%.2f")
                            e_prio  = eq4.selectbox("Prioridade", PRIORIDADES, index=PRIORIDADES.index(item.get("prioridade","Média")) if item.get("prioridade") in PRIORIDADES else 1)
                            e_obs   = st.text_input("Observações", value=item.get("obs",""))
                            e_dt    = st.date_input("Data de Necessidade", value=None)
                            es1,es2 = st.columns(2)
                            if es1.form_submit_button("Salvar", type="primary"):
                                atualizar_item(item["id"], {
                                    "produto": e_prod, "fornecedor": e_forn,
                                    "qtd": e_qtd, "unidade": e_un,
                                    "preco_unit": e_preco, "total": round(e_qtd*e_preco,2),
                                    "prioridade": e_prio, "obs": e_obs,
                                    "dt_necessidade": str(e_dt) if e_dt else None,
                                })
                                st.session_state[f"edit_{item['id']}"] = False
                                st.rerun()
                            if es2.form_submit_button("Cancelar"):
                                st.session_state[f"edit_{item['id']}"] = False
                                st.rerun()
            else:
                st.caption("Nenhum item nesta seção." if filtro_status=="Todos" else f"Nenhum item com status '{filtro_status}'.")

            # Adicionar item
            st.markdown("---")
            with st.expander("➕ Adicionar item nesta seção"):
                with st.form(f"form_add_{sec['id']}"):
                    ap1,ap2 = st.columns(2)
                    a_prod = ap1.text_input("Produto *")
                    a_forn = ap2.text_input("Fornecedor")
                    aq1,aq2,aq3,aq4,aq5 = st.columns(5)
                    a_qtd   = aq1.number_input("Qtd *", min_value=0.0, step=1.0)
                    a_un    = aq2.selectbox("Unid", UNIDADES)
                    a_preco = aq3.number_input("Preço Unit. *", min_value=0.0, step=0.01, format="%.2f")
                    a_prio  = aq4.selectbox("Prioridade", PRIORIDADES, index=1)
                    a_dt    = aq5.date_input("Dt. Necessidade", value=None)
                    a_obs   = st.text_input("Observações")
                    if st.form_submit_button("Adicionar item", type="primary"):
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

# ─── EXPORTAR ─────────────────────────────────────────────────────────────────
def gerar_excel(loja_filtro="ambas"):
    wb = Workbook()
    ws = wb.active

    def thin():
        s = Side(style="thin", color="BFBFBF")
        return Border(left=s,right=s,top=s,bottom=s)

    lojas_proc = ["distribuidora","sublimacao"] if loja_filtro=="ambas" else [loja_filtro]
    ws.title = "Compras"

    row = 1
    ws.merge_cells(f"A{row}:J{row}")
    c = ws.cell(row=row,column=1,value="GRUPO PRATES — GUIA DE COMPRAS")
    c.font = Font(name="Arial",bold=True,size=14,color="FFFFFF")
    c.fill = PatternFill("solid",start_color="1A1A2E")
    c.alignment = Alignment(horizontal="center",vertical="center")
    ws.row_dimensions[row].height = 28
    row += 1

    ws.merge_cells(f"A{row}:J{row}")
    c = ws.cell(row=row,column=1,value=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.font = Font(name="Arial",italic=True,size=9,color="595959")
    c.fill = PatternFill("solid",start_color="F2F2F2")
    c.alignment = Alignment(horizontal="right",vertical="center")
    ws.row_dimensions[row].height = 16
    row += 1

    headers = ["Seção","Produto","Fornecedor","Qtd","Unid","Preço Unit.","Total","Prioridade","Status","Dt. Necessidade"]
    widths   = [22,30,20,8,7,14,14,12,12,16]
    for i,(h,w) in enumerate(zip(headers,widths),1):
        ws.column_dimensions[get_column_letter(i)].width = w
        c = ws.cell(row=row,column=i,value=h)
        c.font = Font(name="Arial",bold=True,color="FFFFFF",size=10)
        c.fill = PatternFill("solid",start_color="405D72")
        c.alignment = Alignment(horizontal="center",vertical="center")
        c.border = thin()
    ws.row_dimensions[row].height = 18
    row += 1

    for loja in lojas_proc:
        info = LOJAS[loja]
        secoes = get_secoes(loja)
        ws.merge_cells(f"A{row}:J{row}")
        c = ws.cell(row=row,column=1,value=f"  {info['icone']}  {info['nome'].upper()}")
        c.font = Font(name="Arial",bold=True,size=11,color="FFFFFF")
        c.fill = PatternFill("solid",start_color=info["cor"].replace("#",""))
        c.alignment = Alignment(horizontal="left",vertical="center")
        c.border = thin()
        ws.row_dimensions[row].height = 22
        row += 1

        total_loja = 0
        for sec in secoes:
            itens = get_itens(sec["id"])
            if not itens:
                continue
            total_sec = 0
            for ri, item in enumerate(itens):
                zb = "EEF4FB" if ri%2==0 else "FFFFFF"
                vals = [
                    sec["nome"], item.get("produto",""),
                    item.get("fornecedor",""),
                    item.get("qtd",""), item.get("unidade",""),
                    item.get("preco_unit",""), item.get("total",""),
                    item.get("prioridade",""), item.get("status",""),
                    item.get("dt_necessidade","")
                ]
                for ci,v in enumerate(vals,1):
                    c = ws.cell(row=row,column=ci,value=v)
                    c.font = Font(name="Arial",size=9)
                    c.fill = PatternFill("solid",start_color=zb)
                    c.alignment = Alignment(horizontal="center" if ci>3 else "left",vertical="center")
                    c.border = thin()
                    if ci in (6,7) and v:
                        c.number_format = '"R$" #,##0.00'
                ws.row_dimensions[row].height = 16
                total_sec += float(item.get("total") or 0)
                row += 1
            total_loja += total_sec

            # subtotal seção
            ws.merge_cells(f"A{row}:F{row}")
            c = ws.cell(row=row,column=1,value=f"Subtotal {sec['nome']}")
            c.font = Font(name="Arial",bold=True,size=9,color="FFFFFF")
            c.fill = PatternFill("solid",start_color="6D9EC1" if loja=="distribuidora" else "6AAA64")
            c.alignment = Alignment(horizontal="right",vertical="center"); c.border = thin()
            c = ws.cell(row=row,column=7,value=total_sec)
            c.font = Font(name="Arial",bold=True,size=9,color="FFFFFF")
            c.fill = PatternFill("solid",start_color="6D9EC1" if loja=="distribuidora" else "6AAA64")
            c.alignment = Alignment(horizontal="right",vertical="center")
            c.number_format = '"R$" #,##0.00'; c.border = thin()
            for ci in range(8,11):
                cc = ws.cell(row=row,column=ci)
                cc.fill = PatternFill("solid",start_color="6D9EC1" if loja=="distribuidora" else "6AAA64")
                cc.border = thin()
            ws.row_dimensions[row].height = 18
            row += 1

        # total loja
        ws.merge_cells(f"A{row}:F{row}")
        c = ws.cell(row=row,column=1,value=f"TOTAL {info['nome'].upper()}")
        c.font = Font(name="Arial",bold=True,size=10,color="FFFFFF")
        c.fill = PatternFill("solid",start_color=info["cor"].replace("#",""))
        c.alignment = Alignment(horizontal="right",vertical="center"); c.border = thin()
        c = ws.cell(row=row,column=7,value=total_loja)
        c.font = Font(name="Arial",bold=True,size=10,color="FFFFFF")
        c.fill = PatternFill("solid",start_color=info["cor"].replace("#",""))
        c.alignment = Alignment(horizontal="right",vertical="center")
        c.number_format = '"R$" #,##0.00'; c.border = thin()
        for ci in range(8,11):
            cc = ws.cell(row=row,column=ci)
            cc.fill = PatternFill("solid",start_color=info["cor"].replace("#",""))
            cc.border = thin()
        ws.row_dimensions[row].height = 22
        row += 2

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def gerar_pdf(loja_filtro="ambas"):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story  = []

    titulo_style = ParagraphStyle("titulo", parent=styles["Title"],
                                  fontSize=16, textColor=rl_colors.HexColor("#1A1A2E"), spaceAfter=4)
    sub_style    = ParagraphStyle("sub", parent=styles["Normal"],
                                  fontSize=9, textColor=rl_colors.gray, spaceAfter=12)
    loja_style   = ParagraphStyle("loja", parent=styles["Heading2"],
                                  fontSize=12, textColor=rl_colors.white, spaceAfter=4)
    sec_style    = ParagraphStyle("sec", parent=styles["Normal"],
                                  fontSize=10, fontName="Helvetica-Bold", spaceAfter=2)

    story.append(Paragraph("GRUPO PRATES — GUIA DE COMPRAS", titulo_style))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub_style))

    lojas_proc = ["distribuidora","sublimacao"] if loja_filtro=="ambas" else [loja_filtro]

    col_widths = [4.5*cm,4*cm,3*cm,1.5*cm,1.5*cm,3*cm,3*cm,2.5*cm,2.5*cm]
    headers_pdf = ["Produto","Fornecedor","Seção","Qtd","Unid","Preço Unit.","Total","Prioridade","Status"]

    for loja in lojas_proc:
        info = LOJAS[loja]
        cor  = rl_colors.HexColor(info["cor"])
        story.append(Spacer(1,0.3*cm))
        story.append(HRFlowable(width="100%", thickness=2, color=cor))
        story.append(Paragraph(f"{info['icone']} {info['nome'].upper()}", loja_style))

        secoes = get_secoes(loja)
        total_loja = 0
        all_rows = [headers_pdf]
        for sec in secoes:
            itens = get_itens(sec["id"])
            if not itens: continue
            for item in itens:
                all_rows.append([
                    item.get("produto",""),
                    item.get("fornecedor",""),
                    sec["nome"],
                    str(item.get("qtd","")),
                    item.get("unidade",""),
                    f"R$ {float(item.get('preco_unit') or 0):,.2f}".replace(",","X").replace(".",",").replace("X","."),
                    f"R$ {float(item.get('total') or 0):,.2f}".replace(",","X").replace(".",",").replace("X","."),
                    item.get("prioridade",""),
                    item.get("status",""),
                ])
                total_loja += float(item.get("total") or 0)

        if len(all_rows) > 1:
            t = Table(all_rows, colWidths=col_widths, repeatRows=1)
            ts = TableStyle([
                ("BACKGROUND",   (0,0), (-1,0),  cor),
                ("TEXTCOLOR",    (0,0), (-1,0),  rl_colors.white),
                ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",     (0,0), (-1,-1), 8),
                ("ALIGN",        (3,0), (-1,-1), "CENTER"),
                ("ALIGN",        (0,0), (2,-1),  "LEFT"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [rl_colors.white, rl_colors.HexColor("#EEF4FB")]),
                ("GRID",         (0,0), (-1,-1), 0.5, rl_colors.HexColor("#CCCCCC")),
                ("TOPPADDING",   (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0), (-1,-1), 4),
            ])
            t.setStyle(ts)
            story.append(t)

        story.append(Paragraph(
            f"Total {info['nome']}: R$ {total_loja:,.2f}".replace(",","X").replace(".",",").replace("X","."),
            ParagraphStyle("tot", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold", spaceAfter=4)
        ))

    doc.build(story)
    buf.seek(0)
    return buf

def pagina_exportar():
    st.markdown("<div class='titulo-pagina'>📥 Exportar Pedido</div>", unsafe_allow_html=True)

    col_op, _ = st.columns([1,2])
    with col_op:
        loja_exp = st.selectbox("Loja", ["Ambas as lojas","Prates Distribuidora","Prates Sublimação"])
        loja_key = {"Ambas as lojas":"ambas","Prates Distribuidora":"distribuidora","Prates Sublimação":"sublimacao"}[loja_exp]

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📊 Excel (.xlsx)")
        st.caption("Planilha completa com todas as seções, subtotais e total geral.")
        if st.button("Gerar Excel", use_container_width=True, type="primary"):
            buf = gerar_excel(loja_key)
            st.download_button(
                "⬇️ Baixar Excel", buf,
                file_name=f"Compras_Prates_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    with c2:
        st.markdown("### 📄 PDF")
        st.caption("Relatório formatado para impressão ou envio.")
        if st.button("Gerar PDF", use_container_width=True):
            buf = gerar_pdf(loja_key)
            st.download_button(
                "⬇️ Baixar PDF", buf,
                file_name=f"Compras_Prates_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# ─── ADMIN ────────────────────────────────────────────────────────────────────
def pagina_admin():
    st.markdown("<div class='titulo-pagina'>⚙️ Administração</div>", unsafe_allow_html=True)

    tab_u, tab_s = st.tabs(["👤 Usuários", "📂 Seções"])

    with tab_u:
        st.markdown("#### Criar novo usuário")
        with st.form("form_criar_user"):
            cu1,cu2 = st.columns(2)
            n_nome  = cu1.text_input("Nome completo")
            n_email = cu2.text_input("E-mail")
            cu3,cu4 = st.columns(2)
            n_senha = cu3.text_input("Senha inicial", type="password")
            n_acesso= cu4.selectbox("Acesso", ["distribuidora","sublimacao","ambas","admin"],
                                    format_func=lambda x: {"distribuidora":"Só Distribuidora",
                                                            "sublimacao":"Só Sublimação",
                                                            "ambas":"Ambas as lojas",
                                                            "admin":"Administrador"}[x])
            if st.form_submit_button("Criar usuário", type="primary"):
                if n_nome and n_email and n_senha:
                    criar_usuario(n_nome, n_email, n_senha, n_acesso)
                    st.success(f"Usuário '{n_nome}' criado!")
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos.")

        st.markdown("#### Usuários cadastrados")
        usuarios = get_usuarios()
        for uu in usuarios:
            cu1,cu2,cu3,cu4 = st.columns([3,3,2,1])
            cu1.markdown(f"**{uu['nome']}**")
            cu2.markdown(f"<small>{uu['email']}</small>", unsafe_allow_html=True)
            cu3.markdown(uu["acesso"])
            status_u = "✅ Ativo" if uu["ativo"] else "❌ Inativo"
            if cu4.button(status_u, key=f"tog_{uu['id']}"):
                toggle_usuario(uu["id"], not uu["ativo"])
                st.rerun()

    with tab_s:
        for loja, info in LOJAS.items():
            st.markdown(f"#### {info['icone']} {info['nome']}")
            secoes = get_secoes(loja)
            for sec in secoes:
                cs1,cs2,cs3 = st.columns([4,2,1])
                cs1.markdown(f"**{sec['nome']}** — ordem {sec['ordem']}")
                novo_n = cs2.text_input("", value=sec["nome"], key=f"adm_sec_{sec['id']}",
                                         label_visibility="collapsed")
                if cs3.button("Renomear", key=f"adm_ren_{sec['id']}"):
                    renomear_secao(sec["id"], novo_n)
                    st.rerun()
            st.markdown("---")

# ─── ROTEADOR ─────────────────────────────────────────────────────────────────
pagina = st.session_state.pagina

if pagina == "dashboard":
    pagina_dashboard()
elif pagina == "distribuidora":
    if pode_ver("distribuidora"):
        pagina_loja("distribuidora")
    else:
        st.error("Você não tem acesso à Prates Distribuidora.")
elif pagina == "sublimacao":
    if pode_ver("sublimacao"):
        pagina_loja("sublimacao")
    else:
        st.error("Você não tem acesso à Prates Sublimação.")
elif pagina == "exportar":
    pagina_exportar()
elif pagina == "admin":
    if u["acesso"] == "admin":
        pagina_admin()
    else:
        st.error("Acesso restrito.")
