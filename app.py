import streamlit as st
import pandas as pd
import bcrypt
import hashlib
import io
import logging
from supabase import create_client
from datetime import date, datetime
import plotly.express as px
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from typing import Optional, List, Dict, Any

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO INICIAL & LOGGING
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Prates Compras",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Moderno, Leve e Otimizado
st.markdown("""
<style>
    /* Base */
    .stApp {background: #0f1419; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif}
    
    /* Login */
    .login-box {max-width: 420px; margin: 60px auto; padding: 40px; background: #161b22; border-radius: 16px; border: 1px solid #30363d; box-shadow: 0 8px 32px rgba(0,0,0,0.4)}
    .login-header {text-align: center; margin-bottom: 30px}
    .login-logo {width: 70px; height: 70px; border-radius: 50%; background: linear-gradient(135deg, #238636, #2ea043); display: flex; align-items: center; justify-content: center; font-size: 28px; margin: 0 auto 15px; color: #fff}
    .login-title {font-size: 22px; font-weight: 700; color: #f0f6fc; margin: 5px 0}
    .login-sub {font-size: 13px; color: #8b949e}
    
    /* Inputs & Buttons */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div {background: #0d1117 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; border-radius: 8px !important; padding: 10px 12px !important; font-size: 14px !important}
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {border-color: #58a6ff !important; box-shadow: 0 0 0 3px rgba(88,166,255,0.15) !important}
    .stButton>button {background: #238636 !important; color: #fff !important; border: none !important; border-radius: 8px !important; padding: 10px 20px !important; font-weight: 600 !important; transition: all 0.2s ease !important}
    .stButton>button:hover {background: #2ea043 !important; transform: translateY(-1px)}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {background: #0d1117 !important; border-right: 1px solid #21262d !important; padding: 20px 12px !important}
    .sidebar-user {font-weight: 600; color: #f0f6fc; font-size: 14px; margin-bottom: 4px}
    .sidebar-role {display: inline-block; background: #238636; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 12px; font-weight: 600}
    .nav-btn {width: 100%; text-align: left; padding: 10px 12px; margin: 4px 0; border-radius: 8px; background: transparent !important; border: 1px solid transparent !important; color: #8b949e !important; font-size: 13px !important}
    .nav-btn.active {background: #161b22 !important; border-color: #30363d !important; color: #f0f6fc !important; font-weight: 600}
    .nav-btn:hover:not(.active) {background: #161b22 !important; color: #e6edf3 !important}
    
    /* Cards & KPIs */
    .kpi-card {background: #161b22; border: 1px solid #21262d; border-radius: 12px; padding: 16px; text-align: center; transition: transform 0.2s}
    .kpi-card:hover {transform: translateY(-2px); border-color: #30363d}
    .kpi-val {font-size: 24px; font-weight: 700; color: #f0f6fc; margin: 6px 0}
    .kpi-lbl {font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600}
    
    /* Sections & Badges */
    .sec-hdr {background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center}
    .sec-body {background: #0d1117; border: 1px solid #21262d; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px}
    .badge {display: inline-block; padding: 3px 8px; border-radius: 20px; font-size: 11px; font-weight: 600}
    .b-Pendente{background:rgba(210,153,34,.15);color:#D2991E;border:1px solid rgba(210,153,34,.3)}
    .b-Aprovado{background:rgba(88,166,255,.15);color:#58A6FF;border:1px solid rgba(88,166,255,.3)}
    .b-Comprado{background:rgba(163,113,247,.15);color:#A371F7;border:1px solid rgba(163,113,247,.3)}
    .b-Entregue{background:rgba(63,185,80,.15);color:#3FB950;border:1px solid rgba(63,185,80,.3)}
    .b-Cancelado{background:rgba(248,81,73,.15);color:#F85149;border:1px solid rgba(248,81,73,.3)}
    .b-Alta{background:rgba(248,81,73,.15);color:#F85149;border:1px solid rgba(248,81,73,.3)}
    .b-Media{background:rgba(210,153,34,.15);color:#D2991E;border:1px solid rgba(210,153,34,.3)}
    .b-Baixa{background:rgba(63,185,80,.15);color:#3FB950;border:1px solid rgba(63,185,80,.3)}
    
    /* Utils */
    .divider {height: 1px; background: #21262d; margin: 20px 0}
    .text-muted {color: #8b949e}
    .total-bar {background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 12px 20px; margin-top: 12px; text-align: right}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & CONFIG
# ─────────────────────────────────────────────────────────────────────────────
LOJAS = {"distribuidora": {"nome": "Prates Distribuidora", "cor": "#58A6FF", "icone": "📦"}, "sublimacao": {"nome": "Prates Sublimação", "cor": "#3FB950", "icone": "🎨"}}
STATUS_ALL = ["Pendente", "Aprovado", "Comprado", "Entregue", "Cancelado"]
STATUS_AT = ["Pendente", "Aprovado"]
STATUS_HI = ["Comprado", "Entregue", "Cancelado"]
PRIO = ["Alta", "Media", "Baixa"]
UNID = ["UN", "CX", "PCT", "KG", "MT", "LT", "RL", "PAR"]
CACHE_TTL = {"fornecedores": 300, "secoes": 120, "itens": 60, "usuarios": 300}

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE & SECURITY
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_sb():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        logger.critical(f"DB Connection Failed: {e}")
        st.error("Erro de conexão com o banco. Verifique as credenciais.")
        st.stop()

sb = get_sb()

def hash_pwd(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

def verify_pwd(p: str, h: str) -> bool:
    try: return bcrypt.checkpw(p.encode(), h.encode())
    except: return False

# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS LOGIC & CRUD (Validated, Typed, Error-Handled)
# ─────────────────────────────────────────────────────────────────────────────
def _validate_item(data: dict) -> Optional[str]:
    if not data.get("produto") or len(data["produto"]) > 150: return "Nome do produto inválido."
    if data.get("qtd", 0) < 0: return "Quantidade não pode ser negativa."
    if data.get("preco_unit", 0) < 0: return "Preço não pode ser negativo."
    return None

@st.cache_data(ttl=CACHE_TTL["fornecedores"])
def get_fornecedores() -> List[dict]:
    try: return sb.table("pc_fornecedores").select("*").eq("ativo", True).order("nome").execute().data or []
    except Exception as e: logger.error(f"Erro ao buscar fornecedores: {e}"); return []

def create_fornecedor(d: dict) -> bool:
    try: sb.table("pc_fornecedores").insert(d).execute(); st.cache_data.clear(); return True
    except Exception as e: logger.error(f"Erro ao criar fornecedor: {e}"); return False

def update_fornecedor(fid: int, d: dict) -> bool:
    try: sb.table("pc_fornecedores").update(d).eq("id", fid).execute(); st.cache_data.clear(); return True
    except Exception as e: logger.error(f"Erro ao atualizar fornecedor: {e}"); return False

def delete_fornecedor(fid: int) -> bool:
    try: sb.table("pc_fornecedores").update({"ativo": False}).eq("id", fid).execute(); st.cache_data.clear(); return True
    except Exception as e: logger.error(f"Erro ao desativar fornecedor: {e}"); return False

@st.cache_data(ttl=CACHE_TTL["secoes"])
def get_secoes(loja: str) -> List[dict]:
    try: return sb.table("pc_secoes").select("*").eq("loja", loja).eq("ativa", True).order("ordem").execute().data or []
    except Exception as e: logger.error(f"Erro ao buscar seções: {e}"); return []

def create_secao(loja: str, nome: str) -> bool:
    try:
        ss = get_secoes(loja)
        ordem = (max(s["ordem"] for s in ss) + 1) if ss else 1
        sb.table("pc_secoes").insert({"loja": loja, "nome": nome, "ordem": ordem, "ativa": True}).execute()
        st.cache_data.clear(); return True
    except Exception as e: logger.error(f"Erro ao criar seção: {e}"); return False

def update_secao(sid: int, nome: str) -> bool:
    try: sb.table("pc_secoes").update({"nome": nome}).eq("id", sid).execute(); st.cache_data.clear(); return True
    except Exception as e: logger.error(f"Erro ao atualizar seção: {e}"); return False

def delete_secao(sid: int) -> bool:
    try: sb.table("pc_secoes").update({"ativa": False}).eq("id", sid).execute(); st.cache_data.clear(); return True
    except Exception as e: logger.error(f"Erro ao desativar seção: {e}"); return False

@st.cache_data(ttl=CACHE_TTL["itens"])
def get_itens_secao(sid: int, status_filter: Optional[List[str]] = None) -> List[dict]:
    try:
        q = sb.table("pc_itens").select("*").eq("secao_id", sid)
        if status_filter: q = q.in_("status", status_filter)
        return q.order("criado_em").execute().data or []
    except Exception as e: logger.error(f"Erro ao buscar itens: {e}"); return []

def create_item(sid: int, d: dict, user: str) -> Optional[str]:
    err = _validate_item(d)
    if err: return err
    try:
        d.update({"secao_id": sid, "criado_por": user, "criado_em": datetime.now().isoformat(), "atualizado_em": datetime.now().isoformat()})
        sb.table("pc_itens").insert(d).execute(); st.cache_data.clear()
        return None
    except Exception as e: logger.error(f"Erro ao criar item: {e}"); return "Erro ao salvar no banco."

def update_item(iid: int, d: dict) -> Optional[str]:
    err = _validate_item(d)
    if err: return err
    try:
        d["atualizado_em"] = datetime.now().isoformat()
        sb.table("pc_itens").update(d).eq("id", iid).execute(); st.cache_data.clear()
        return None
    except Exception as e: logger.error(f"Erro ao atualizar item: {e}"); return "Erro ao atualizar."

def delete_item(iid: int) -> bool:
    try: sb.table("pc_itens").delete().eq("id", iid).execute(); st.cache_data.clear(); return True
    except Exception as e: logger.error(f"Erro ao deletar item: {e}"); return False

def batch_update_status(ids: List[int], new_status: str) -> bool:
    if not ids: return False
    try:
        for iid in ids:
            sb.table("pc_itens").update({"status": new_status, "atualizado_em": datetime.now().isoformat()}).eq("id", iid).execute()
        st.cache_data.clear(); return True
    except Exception as e: logger.error(f"Erro na atualização em lote: {e}"); return False

@st.cache_data(ttl=CACHE_TTL["usuarios"])
def get_usuarios() -> List[dict]:
    try: return sb.table("pc_usuarios").select("id,nome,email,acesso,ativo").order("nome").execute().data or []
    except Exception as e: logger.error(f"Erro ao buscar usuários: {e}"); return []

def create_usuario(nome: str, email: str, senha: str, acesso: str) -> Optional[str]:
    try:
        sb.table("pc_usuarios").insert({"nome": nome, "email": email.lower(), "senha_hash": hash_pwd(senha), "acesso": acesso, "ativo": True}).execute()
        st.cache_data.clear(); return None
    except Exception as e: logger.error(f"Erro ao criar usuário: {e}"); return "Erro ao criar usuário."

def update_usuario(uid: int, d: dict) -> Optional[str]:
    try:
        sb.table("pc_usuarios").update(d).eq("id", uid).execute(); st.cache_data.clear()
        return None
    except Exception as e: logger.error(f"Erro ao atualizar usuário: {e}"); return "Erro ao atualizar."

# ─────────────────────────────────────────────────────────────────────────────
# UTILS & HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt_brl(v: Any) -> str:
    try: return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

def parse_date_safe(dt_str: Any) -> Optional[date]:
    if not dt_str: return None
    try: return date.fromisoformat(str(dt_str))
    except:
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
            try: return datetime.strptime(str(dt_str), fmt).date()
            except: continue
    return None

def days_until(dt_str: Any) -> Optional[int]:
    d = parse_date_safe(dt_str)
    return (d - date.today()).days if d else None

def badge(txt: str) -> str:
    c = {"Media": "Media", "Média": "Media"}.get(txt, txt)
    return f"<span class='badge b-{c}'>{txt}</span>"

def check_perm(loja: str) -> bool:
    u = st.session_state.get("usuario")
    if not u: return False
    a = u["acesso"]
    if a in ("admin", "ambas"): return True
    if loja == "distribuidora": return a in ("distribuidora", "op_dist", "op_ambas", "operador")
    if loja == "sublimacao": return a in ("sublimacao", "op_sub", "op_ambas", "operador")
    return False

def is_op() -> bool:
    u = st.session_state.get("usuario")
    return bool(u and u["acesso"] in ("op_dist", "op_sub", "op_ambas", "operador"))

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
for k, v in [("usuario", None), ("pagina", "dashboard")]:
    if k not in st.session_state: st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN & AUTH
# ─────────────────────────────────────────────────────────────────────────────
def do_login(email: str, senha: str) -> bool:
    email = email.strip().lower()
    if not email or not senha:
        st.warning("Preencha email e senha.", icon="⚠️")
        return False
    
    try:
        with st.spinner("Verificando credenciais..."):
            r = sb.table("pc_usuarios").select("*").eq("email", email).eq("ativo", True).execute()
        if not r.data:
            logger.warning(f"Login falho: email não encontrado ({email})")
            st.error("Email ou senha incorretos.", icon="🔒")
            return False
            
        u = r.data[0]
        # Suporte a upgrade de SHA256 para bcrypt
        if u["senha_hash"].startswith("$2b$"):
            if not verify_pwd(senha, u["senha_hash"]):
                st.error("Email ou senha incorretos.", icon="🔒"); return False
        else:
            if hashlib.sha256(senha.encode()).hexdigest() != u["senha_hash"]:
                st.error("Email ou senha incorretos.", icon="🔒"); return False
            # Upgrade automático para bcrypt
            u["senha_hash"] = hash_pwd(senha)
            sb.table("pc_usuarios").update({"senha_hash": u["senha_hash"]}).eq("id", u["id"]).execute()
            
        st.session_state.usuario = u
        logger.info(f"Login bem-sucedido: {email}")
        return True
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        st.error("Erro interno. Tente novamente.", icon="❌")
        return False

if not st.session_state.usuario:
    _, c, _ = st.columns([1, 0.9, 1])
    with c:
        st.markdown("""
        <div class="login-box">
            <div class="login-header">
                <div class="login-logo">🛒</div>
                <div class="login-title">Prates Compras</div>
                <div class="login-sub">Sistema de Gestão de Compras</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            em = st.text_input("Email", placeholder="seu@email.com", label_visibility="collapsed")
            se = st.text_input("Senha", type="password", placeholder="Digite sua senha", label_visibility="collapsed")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.form_submit_button("Entrar", use_container_width=True, type="primary"):
                    if do_login(em, se): st.rerun()
        st.markdown("<div style='text-align:center;margin-top:25px;color:#8b949e;font-size:12px'>© 2026 Prates - Todos os direitos reservados</div>", unsafe_allow_html=True)
    st.stop()

u = st.session_state.usuario

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center;margin-bottom:20px;padding-bottom:15px;border-bottom:1px solid #21262d'>
        <div class='sidebar-user'>👤 {u['nome']}</div>
        <div class='sidebar-role'>{u['acesso'].upper()}</div>
    </div>
    """, unsafe_allow_html=True)
    
    nav = [("📊 Dashboard", "dashboard"), ("📅 Histórico", "historico"), ("📥 Exportar", "exportar"), ("🏭 Fornecedores", "fornecedores")]
    if check_perm("distribuidora"): nav.insert(1, ("📦 Distribuidora", "distribuidora"))
    if check_perm("sublimacao"): nav.insert(2, ("🎨 Sublimação", "sublimacao"))
    if u["acesso"] == "admin": nav.append(("⚙️ Administração", "admin"))
    
    for label, page in nav:
        active = st.session_state.pagina == page
        if st.button(label, use_container_width=True, type="primary" if active else "secondary", key=f"nav_{page}"):
            st.session_state.pagina = page; st.rerun()
            
    st.divider()
    if st.button("🚪 Sair", use_container_width=True): st.session_state.usuario = None; st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────

def pagina_dashboard():
    st.markdown("<h2 style='font-size:22px;font-weight:700;color:#f0f6fc;margin-bottom:20px'>📊 Dashboard</h2>", unsafe_allow_html=True)
    
    @st.cache_data(ttl=CACHE_TTL["itens"])
    def load_all():
        try: return sb.table("pc_itens").select("*, pc_secoes(nome,loja)").execute().data or []
        except: return []
    
    with st.spinner("Carregando dados..."):
        todos = load_all()
        
    if not todos:
        st.markdown("<div style='text-align:center;padding:50px 20px;background:#161b22;border-radius:12px;border:1px dashed #30363d'><div style='font-size:40px'>📦</div><div class='text-muted' style='margin-top:10px'>Nenhum produto lançado.</div></div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(todos)
    df["loja"] = df["pc_secoes"].apply(lambda x: x["loja"] if x else "")
    df["secao"] = df["pc_secoes"].apply(lambda x: x["nome"] if x else "")
    df["total"] = pd.to_numeric(df.get("total", 0), errors="coerce").fillna(0)

    # KPIs
    cols = st.columns(4)
    metrics = [
        ("💰 Total Geral", fmt_brl(df["total"].sum()), "#f0f6fc"),
        ("📦 Distribuidora", fmt_brl(df[df["loja"]=="distribuidora"]["total"].sum()), "#58A6FF"),
        ("🎨 Sublimação", fmt_brl(df[df["loja"]=="sublimacao"]["total"].sum()), "#3FB950"),
        ("📋 Total Itens", str(len(df)), "#8b949e")
    ]
    for i, (lbl, val, cor) in enumerate(metrics):
        cols[i].markdown(f"<div class='kpi-card' style='border-top:3px solid {cor}'><div class='kpi-lbl'>{lbl}</div><div class='kpi-val' style='color:{cor}'>{val}</div></div>", unsafe_allow_html=True)

    st.divider()

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='text-muted' style='font-size:13px;margin-bottom:10px'>ITENS POR STATUS</div>", unsafe_allow_html=True)
        s = df.groupby("status").size().reset_index(name="qtd")
        fig = px.bar(s, x="status", y="qtd", color="status", color_discrete_map={"Pendente":"#D2991E","Aprovado":"#58A6FF","Comprado":"#A371F7","Entregue":"#3FB950","Cancelado":"#F85149"}, template="plotly_dark")
        fig.update_layout(showlegend=False, height=220, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor="#161b22", plot_bgcolor="#0d1117", font=dict(color="#8b949e"))
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.markdown("<div class='text-muted' style='font-size:13px;margin-bottom:10px'>DISTRIBUIÇÃO POR LOJA</div>", unsafe_allow_html=True)
        l = df.groupby("loja").size().reset_index(name="qtd")
        l["nome"] = l["loja"].map({"distribuidora":"Distribuidora","sublimacao":"Sublimação"})
        fig2 = px.pie(l, names="nome", values="qtd", color_discrete_sequence=["#58A6FF","#3FB950"], hole=0.5, template="plotly_dark")
        fig2.update_layout(height=220, margin=dict(t=10,b=10), paper_bgcolor="#161b22", font=dict(color="#8b949e"), legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig2, use_container_width=True)

def pagina_loja(loja: str):
    info = LOJAS[loja]
    st.markdown(f"<h2 style='font-size:20px;font-weight:700;color:#f0f6fc;margin-bottom:15px'>{info['icone']} {info['nome']}</h2>", unsafe_allow_html=True)

    # Search & Actions
    c1, c2, c3 = st.columns([3, 1, 1])
    busca = c1.text_input("", placeholder="Buscar produto, marca, SKU...", label_visibility="collapsed", key=f"busc_{loja}")
    if c2.button("+ Produto", use_container_width=True, key=f"btnp_{loja}"): st.session_state[f"cp_{loja}"] = not st.session_state.get(f"cp_{loja}", False)
    if c3.button("Seções", use_container_width=True, key=f"btns_{loja}"): st.session_state[f"gs_{loja}"] = not st.session_state.get(f"gs_{loja}", False)

    # Filters
    f1, f2 = st.columns(2)
    fst = f1.radio("", ["Todos"]+STATUS_AT, horizontal=True, key=f"fst_{loja}", label_visibility="collapsed")
    fpr = f2.radio("", ["Todas"]+PRIO, horizontal=True, key=f"fpr_{loja}", label_visibility="collapsed")

    # Section Manager
    if st.session_state.get(f"gs_{loja}"):
        st.markdown("<div class='sec-hdr'><span style='font-weight:600;color:#58A6FF'>Gerenciar Seções</span></div>", unsafe_allow_html=True)
        with st.form(f"fns_{loja}"):
            n1, n2 = st.columns([4, 1])
            nn = n1.text_input("", placeholder="Nome da nova seção", label_visibility="collapsed")
            if n2.form_submit_button("+ Criar", type="primary", use_container_width=True):
                if nn.strip(): create_secao(loja, nn.strip()); st.rerun()
        for sec in get_secoes(loja):
            with st.form(f"fsec_{sec['id']}"):
                e1, e2, e3 = st.columns([4, 1, 1])
                v = e1.text_input("", value=sec["nome"], label_visibility="collapsed")
                if e2.form_submit_button("Salvar", type="primary", use_container_width=True): update_secao(sec["id"], v.strip()); st.rerun()
                if e3.form_submit_button("Excluir", use_container_width=True): delete_secao(sec["id"]); st.rerun()
        if st.button("Fechar", key=f"fgs_{loja}"): st.session_state[f"gs_{loja}"] = False; st.rerun()
        st.divider()

    # Create Product Form
    if st.session_state.get(f"cp_{loja}"):
        secs = get_secoes(loja)
        if not secs: st.warning("Crie uma seção primeiro."); st.stop()
        
        st.markdown("<div class='sec-hdr' style='border-top:2px solid #238636'><span style='font-weight:600;color:#3FB950'>Novo Produto</span></div>", unsafe_allow_html=True)
        fmc = {f["nome"]:f["id"] for f in get_fornecedores()}
        with st.form(f"fcp_{loja}"):
            r1 = st.columns([2,2.5,2,1.5,1.5,2])
            sec_sel = r1[0].selectbox("Seção", [s["nome"] for s in secs])
            prod = r1[1].text_input("Produto *")
            marca = r1[2].text_input("Marca")
            sku = r1[3].text_input("SKU")
            ean = r1[4].text_input("EAN")
            forn = r1[5].selectbox("Fornecedor", ["(Nenhum)"]+list(fmc.keys()))
            
            r2 = st.columns([1.2,1.5,1.5,1.5,1.5,1.5,1.5,1])
            qtd = r2[0].number_input("Qtd", min_value=0.0, step=1.0)
            un = r2[1].selectbox("Unid", UNID)
            prec = r2[2].number_input("Preço", min_value=0.0, step=0.01, format="%.2f")
            prio = r2[3].selectbox("Prioridade", PRIO, index=1)
            dt = r2[4].date_input("Necessidade", value=None)
            img = r2[5].text_input("URL Img", placeholder="https://...")
            obs = r2[6].text_input("Obs")
            r2[7].markdown("<br>", unsafe_allow_html=True)
            
            if r2[7].form_submit_button("Salvar", type="primary", use_container_width=True):
                if prod.strip():
                    sid = next(s["id"] for s in secs if s["nome"]==sec_sel)
                    fid = fmc.get(forn) if forn != "(Nenhum)" else None
                    err = create_item(sid, {"produto":prod.strip(),"marca":marca.strip(),"sku":sku.strip(),"ean":ean.strip(),"fornecedor_id":fid,"imagem_url":img.strip() or None,"qtd":qtd,"unidade":un,"preco_unit":prec,"total":round(qtd*prec,2),"prioridade":prio,"dt_necessidade":str(dt) if dt else None,"obs":obs.strip(),"status":"Pendente"}, u["nome"])
                    if err: st.error(err)
                    else: st.success("Salvo!"); st.session_state[f"cp_{loja}"]=False; st.rerun()
                else: st.warning("Informe o nome do produto.")
        st.divider()

    # Sections & Items
    secoes = get_secoes(loja)
    total_loja = 0.0
    fmc = {f["id"]:f["nome"] for f in get_fornecedores()}
    
    # Batch Selection
    sel_key = f"sel_{loja}"
    if sel_key not in st.session_state: st.session_state[sel_key] = []
    marcados = st.session_state[sel_key]
    
    if marcados and not is_op():
        st.markdown(f"<div style='background:#1C2128;border:1px solid #30363d;border-radius:8px;padding:8px 12px;margin-bottom:12px'><b style='color:#58A6FF'>{len(marcados)} selecionado(s)</b></div>", unsafe_allow_html=True)
        ba = st.columns(5)
        ops = [("Aprovar","Aprovado","primary"),("Comprado","Comprado","secondary"),("Entregue","Entregue","secondary"),("Cancelar","Cancelado","secondary"),("Limpar","",None)]
        for i,(lbl,sv,tp) in enumerate(ops):
            if tp and ba[i].button(lbl, key=f"lote_{sv}_{loja}", use_container_width=True, type=tp):
                if lbl=="Limpar": st.session_state[sel_key]=[]
                else: batch_update_status(marcados, sv); st.session_state[sel_key]=[]
                st.rerun()
        st.divider()

    for sec in secoes:
        with st.expander(f"📁 {sec['nome']} ({len(get_itens_secao(sec['id'], tuple(STATUS_AT)))} itens)", expanded=False):
            itens_all = get_itens_secao(sec['id'], tuple(STATUS_AT))
            itens = itens_all[:]
            if fst != "Todos": itens = [i for i in itens if i.get("status")==fst]
            if fpr != "Todas": itens = [i for i in itens if i.get("prioridade")==fpr]
            if busca:
                b = busca.lower()
                itens = [i for i in itens if b in " ".join([i.get("produto",""),i.get("marca",""),i.get("sku",""),i.get("ean","")]).lower()]
                
            tsec = sum(float(i.get("total") or 0) for i in itens_all)
            total_loja += tsec
            
            if itens:
                for item in itens:
                    iid = item["id"]
                    cols = st.columns([0.3, 3.5, 1.2, 0.8, 0.8, 1.2, 1, 1, 0.8])
                    
                    # Checkbox selection
                    sel = cols[0].checkbox("", value=iid in marcados, key=f"chk_{iid}", label_visibility="collapsed")
                    if sel and iid not in marcados: st.session_state.setdefault(sel_key, []).append(iid)
                    elif not sel and iid in marcados: st.session_state[sel_key].remove(iid)
                    
                    # Info
                    img = item.get("imagem_url","")
                    img_html = f'<img src="{img}" style="width:32px;height:32px;object-fit:cover;border-radius:6px;border:1px solid #30363d">' if img else '📦'
                    meta = " · ".join(filter(None, [f"Marca: {item.get('marca','')}", f"SKU: {item.get('sku','')}", f"Fornecedor: {fmc.get(item.get('fornecedor_id'),'')}"]))
                    cols[1].markdown(f"{img_html} <span style='font-weight:600'>{item.get('produto','')}</span><br><span class='text-muted' style='font-size:12px'>{meta}</span>", unsafe_allow_html=True)
                    
                    cols[2].markdown(f"<span class='text-muted' style='font-size:12px'>{sec['nome']}</span>", unsafe_allow_html=True)
                    cols[3].markdown(f"{item.get('qtd','')} {item.get('unidade','')}", unsafe_allow_html=True)
                    cols[4].markdown(f"<span class='text-muted'>{fmt_brl(item.get('preco_unit',0))}</span>", unsafe_allow_html=True)
                    cols[5].markdown(f"<b style='color:{info['cor']}'>{fmt_brl(item.get('total',0))}</b>", unsafe_allow_html=True)
                    
                    # Badges & Actions
                    d = days_until(item.get("dt_necessidade"))
                    urg_html = f"<span class='badge b-Pendente' style='background:rgba(248,81,73,.25);color:#F85149'>Atraso {abs(d)}d</span>" if d and d<0 else ""
                    cols[6].markdown(f"{badge(item.get('status',''))} {urg_html}", unsafe_allow_html=True)
                    cols[7].markdown(badge(item.get("prioridade","")), unsafe_allow_html=True)
                    
                    with cols[8]:
                        with st.popover("⚙️"):
                            if is_op(): st.caption("Acesso restrito para edição.")
                            else:
                                cur = item.get("status","Pendente")
                                for sv in STATUS_ALL:
                                    if st.button(f"{'✓' if sv==cur else ''} {sv}", key=f"st_{sv}_{iid}", use_container_width=True, type="primary" if sv==cur else "secondary"):
                                        update_item(iid, {"status": sv}); st.rerun()
                                st.divider()
                                if st.button("Editar", key=f"ed_{iid}", use_container_width=True): st.session_state[f"ed_{iid}"]=True
                                # Confirmação de exclusão
                                if st.session_state.get(f"conf_del_{iid}"):
                                    if st.button("Confirmar Exclusão", key=f"conf_yes_{iid}", use_container_width=True, type="primary"): delete_item(iid); st.rerun()
                                    if st.button("Cancelar", key=f"conf_no_{iid}", use_container_width=True): st.session_state[f"conf_del_{iid}"]=False; st.rerun()
                                else:
                                    if st.button("Excluir", key=f"del_{iid}", use_container_width=True): st.session_state[f"conf_del_{iid}"]=True; st.rerun()
                                    
            else:
                st.markdown("<span class='text-muted' style='font-size:13px'>Nenhum item corresponde aos filtros.</span>", unsafe_allow_html=True)
                
    st.markdown(f"<div class='total-bar'><span class='text-muted'>{info['nome']} — Total em aberto:</span> <span style='color:{info['cor']};font-size:18px;font-weight:700;margin-left:8px'>{fmt_brl(total_loja)}</span></div>", unsafe_allow_html=True)

def pagina_historico():
    st.markdown("<h2 style='font-size:22px;font-weight:700;color:#f0f6fc;margin-bottom:15px'>📅 Histórico</h2>", unsafe_allow_html=True)
    f1,f2,f3,f4 = st.columns(4)
    fl = f1.selectbox("Loja", ["Todas","Distribuidora","Sublimação"], key="hfl", label_visibility="collapsed")
    fs = f2.selectbox("Status", ["Todos"]+STATUS_HI, key="hfs", label_visibility="collapsed")
    fp = f3.selectbox("Prioridade", ["Todas"]+PRIO, key="hfp", label_visibility="collapsed")
    fb = f4.text_input("","", placeholder="Buscar...", key="hfb", label_visibility="collapsed")
    
    with st.spinner("Carregando histórico..."):
        todos = sb.table("pc_itens").select("*, pc_secoes(nome,loja)").in_("status", STATUS_HI).execute().data or []
        
    if not todos: st.info("Nenhum item no histórico."); return
    
    df = pd.DataFrame(todos)
    df["loja"] = df["pc_secoes"].apply(lambda x: x["loja"] if x else "")
    df["secao"] = df["pc_secoes"].apply(lambda x: x["nome"] if x else "")
    df["total"] = pd.to_numeric(df.get("total",0), errors="coerce").fillna(0)
    df["fornecedor"] = df["fornecedor_id"].map({f["id"]:f["nome"] for f in get_fornecedores()}).fillna("")
    
    if fl!="Todas": df=df[df["loja"]==("distribuidora" if fl=="Distribuidora" else "sublimacao")]
    if fs!="Todos": df=df[df["status"]==fs]
    if fp!="Todas": df=df[df["prioridade"]==fp]
    if fb: df=df[df["produto"].str.lower().str.contains(fb.lower(), na=False)]
    
    st.markdown(f"<div class='text-muted' style='font-size:13px;margin:8px 0'>{len(df)} itens · Total: <b style='color:#58A6FF'>{fmt_brl(df['total'].sum())}</b></div>", unsafe_allow_html=True)
    st.dataframe(df[["produto","marca","sku","secao","loja","fornecedor","qtd","unidade","total","prioridade","status","dt_necessidade"]].rename(columns={"produto":"Produto","marca":"Marca","sku":"SKU","secao":"Seção","loja":"Loja","fornecedor":"Fornecedor","qtd":"Qtd","unidade":"Unid","total":"Total","prioridade":"Prioridade","status":"Status","dt_necessidade":"Data"}), use_container_width=True, hide_index=True, height=450)

def pagina_exportar():
    st.markdown("<h2 style='font-size:22px;font-weight:700;color:#f0f6fc;margin-bottom:15px'>📥 Exportar</h2>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    le = c1.selectbox("Loja", ["Ambas","Distribuidora","Sublimação"])
    inc = c2.checkbox("Incluir Histórico")
    lk = {"Ambas":"ambas","Distribuidora":"distribuidora","Sublimacao":"sublimacao"}[le]
    
    if st.button("Gerar Excel", use_container_width=True, type="primary"):
        with st.spinner("Gerando arquivo..."):
            sf = None if inc else STATUS_AT
            lojas_ = ["distribuidora","sublimacao"] if lk=="ambas" else [lk]
            wb = Workbook(); ws = wb.active; ws.title = "Compras"
            row = 1
            ws.merge_cells(f"A{row}:L{row}")
            c = ws.cell(row=row, column=1, value="GRUPO PRATES - GUIA DE COMPRAS")
            c.font = Font(bold=True, size=14, color="FFFFFF"); c.fill = PatternFill("solid", start_color="0D1117")
            c.alignment = Alignment(horizontal="center"); ws.row_dimensions[row].height = 28; row += 1
            
            hdrs = ["Seção","Produto","Marca","SKU","EAN","Fornecedor","Qtd","Unid","Preço","Total","Prioridade","Status"]
            for i,h in enumerate(hdrs,1):
                ws.column_dimensions[get_column_letter(i)].width = [20,28,16,14,14,18,7,6,12,12,12,12][i-1]
                c = ws.cell(row=row, column=i, value=h); c.font = Font(bold=True, color="FFFFFF", size=9)
                c.fill = PatternFill("solid", start_color="21262D"); c.alignment = Alignment(horizontal="center")
            row += 1
            
            fme = {f["id"]:f["nome"] for f in get_fornecedores()}
            for loja in lojas_:
                info = LOJAS[loja]
                ws.merge_cells(f"A{row}:L{row}")
                c = ws.cell(row=row, column=1, value=f"  {info['nome'].upper()}")
                c.font = Font(bold=True, size=11, color="FFFFFF"); c.fill = PatternFill("solid", start_color="161B22")
                c.alignment = Alignment(horizontal="left"); ws.row_dimensions[row].height = 20; row += 1; tl = 0
                
                for sec in get_secoes(loja):
                    for ri, item in enumerate(get_itens_secao(sec["id"], tuple(sf) if sf else None)):
                        zb = "0D1117" if ri%2==0 else "161B22"
                        vals = [sec["nome"],item.get("produto",""),item.get("marca",""),item.get("sku",""),item.get("ean",""),fme.get(item.get("fornecedor_id"),""),item.get("qtd",""),item.get("unidade",""),item.get("preco_unit",""),item.get("total",""),item.get("prioridade",""),item.get("status","")]
                        for ci,v in enumerate(vals,1):
                            c = ws.cell(row=row, column=ci, value=v); c.font = Font(size=9, color="E6EDF3")
                            c.fill = PatternFill("solid", start_color=zb); c.alignment = Alignment(horizontal="center" if ci>5 else "left")
                            if ci in (9,10) and v: c.number_format = '"R$" #,##0.00'
                        ws.row_dimensions[row].height = 16; tl += float(item.get("total") or 0); row += 1
                        
                ws.merge_cells(f"A{row}:I{row}")
                c = ws.cell(row=row, column=1, value=f"TOTAL {info['nome'].upper()}")
                c.font = Font(bold=True, size=10, color="FFFFFF"); c.fill = PatternFill("solid", start_color="0D1117"); c.alignment = Alignment(horizontal="right")
                c = ws.cell(row=row, column=10, value=tl); c.font = Font(bold=True, size=10, color="58A6FF"); c.fill = PatternFill("solid", start_color="0D1117"); c.number_format = '"R$" #,##0.00'
                ws.row_dimensions[row].height = 22; row += 2
                
            buf = io.BytesIO(); wb.save(buf); buf.seek(0)
            st.download_button("Baixar Excel", buf, file_name=f"Compras_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

def pagina_fornecedores():
    st.markdown("<h2 style='font-size:22px;font-weight:700;color:#f0f6fc;margin-bottom:15px'>🏭 Fornecedores</h2>", unsafe_allow_html=True)
    tab_l, tab_n = st.tabs(["Lista", "Novo Fornecedor"])
    with tab_n:
        with st.form("fnovoforn"):
            na,nb,nc,nd,ne,nf = st.columns([2.5,2,1.8,2,1.8,1])
            fn = na.text_input("Nome *"); fc = nb.text_input("Contato"); ft = nc.text_input("Telefone")
            fe = nd.text_input("Email"); fcnpj = ne.text_input("CNPJ"); nf.markdown("<br>", unsafe_allow_html=True)
            if nf.form_submit_button("+ Adicionar", type="primary", use_container_width=True):
                if fn.strip(): create_fornecedor({"nome":fn.strip(),"contato":fc,"telefone":ft,"email":fe,"cnpj":fcnpj,"observacoes":"","ativo":True}); st.success("Cadastrado!"); st.rerun()
                else: st.warning("Informe o nome.")
    with tab_l:
        bf = st.text_input("","", placeholder="Buscar...", key="bff", label_visibility="collapsed")
        forns = [f for f in get_fornecedores() if not bf or bf.lower() in f["nome"].lower()]
        for forn in forns:
            with st.form(f"ef_{forn['id']}"):
                fa,fb,fc,fd,fe,fg,fh = st.columns([2.5,1.8,1.8,2,1.8,.7,.7])
                en = fa.text_input("Nome", value=forn.get("nome","")); ec = fb.text_input("Contato", value=forn.get("contato",""))
                et = fc.text_input("Telefone", value=forn.get("telefone","")); ee = fd.text_input("Email", value=forn.get("email",""))
                ecnpj = fe.text_input("CNPJ", value=forn.get("cnpj",""))
                fg.markdown("<br>", unsafe_allow_html=True)
                eobs = st.text_input("Obs", value=forn.get("observacoes",""), label_visibility="collapsed", placeholder="Obs...")
                if fg.form_submit_button("💾", use_container_width=True, type="primary"): update_fornecedor(forn["id"], {"nome":en,"contato":ec,"telefone":et,"email":ee,"cnpj":ecnpj,"observacoes":eobs}); st.rerun()
                fh.markdown("<br>", unsafe_allow_html=True)
                if fh.form_submit_button("🗑", use_container_width=True): delete_fornecedor(forn["id"]); st.rerun()

def pagina_admin():
    if u["acesso"] != "admin": st.error("Acesso restrito."); return
    st.markdown("<h2 style='font-size:22px;font-weight:700;color:#f0f6fc;margin-bottom:15px'>⚙️ Administração</h2>", unsafe_allow_html=True)
    tab_u, tab_s = st.tabs(["Usuários", "Seções"])
    with tab_u:
        st.markdown("#### Novo Usuário")
        with st.form("fnu"):
            c1,c2,c3,c4 = st.columns(4)
            nome = c1.text_input("Nome"); email = c2.text_input("Email"); senha = c3.text_input("Senha", type="password")
            acesso = c4.selectbox("Acesso", ["op_dist","op_sub","op_ambas","distribuidora","sublimacao","ambas","admin"], format_func=lambda x: {"op_dist":"Op. Dist","op_sub":"Op. Sub","op_ambas":"Op. Ambas","distribuidora":"Gestor Dist","sublimacao":"Gestor Sub","ambas":"Gestor Ambas","admin":"Admin"}[x])
            if st.form_submit_button("Criar", type="primary"):
                if nome and email and senha: err = create_usuario(nome, email, senha, acesso); st.success("Criado!") if not err else st.error(err); st.rerun()
        st.markdown("#### Usuários")
        for usu in get_usuarios():
            st.markdown(f"<div style='background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 12px;margin-bottom:6px'><b style='color:#f0f6fc'>{usu['nome']}</b> · {usu['email']} · <span class='text-muted'>{usu['acesso']}</span> · {'✅' if usu['ativo'] else '❌'}</div>", unsafe_allow_html=True)
            with st.form(f"eu_{usu['id']}"):
                e1,e2 = st.columns(2); en=e1.text_input("Nome", value=usu["nome"]); ee=e2.text_input("Email", value=usu["email"])
                e3,e4 = st.columns(2)
                _opts = ["op_dist","op_sub","op_ambas","distribuidora","sublimacao","ambas","admin"]
                ea = e3.selectbox("Acesso", _opts, index=_opts.index(usu["acesso"]) if usu["acesso"] in _opts else 0, format_func=lambda x: {"op_dist":"Op. Dist","op_sub":"Op. Sub","op_ambas":"Op. Ambas","distribuidora":"Gestor Dist","sublimacao":"Gestor Sub","ambas":"Gestor Ambas","admin":"Admin"}[x])
                ep = e4.text_input("Nova Senha", type="password")
                s1,s2 = st.columns(2)
                if s1.form_submit_button("Salvar", type="primary"):
                    d = {"nome":en,"email":ee,"acesso":ea}
                    if ep: d["senha_hash"] = hash_pwd(ep)
                    err = update_usuario(usu["id"], d); st.success("Salvo!") if not err else st.error(err); st.rerun()
                if s2.form_submit_button("Desativar" if usu["ativo"] else "Ativar"): update_usuario(usu["id"], {"ativo":not usu["ativo"]}); st.rerun()
    with tab_s:
        for loja, info in LOJAS.items():
            st.markdown(f"#### {info['icone']} {info['nome']}")
            for sec in get_secoes(loja):
                with st.form(f"as_{sec['id']}"):
                    s1,s2,s3 = st.columns([4,1.5,1]); nn = s1.text_input("", value=sec["nome"], label_visibility="collapsed")
                    if s2.form_submit_button("Salvar"): update_secao(sec["id"], nn); st.rerun()
                    if s3.form_submit_button("Excluir"): delete_secao(sec["id"]); st.rerun()
            st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
pg = st.session_state.pagina
if   pg == "dashboard":    pagina_dashboard()
elif pg == "distribuidora":
    if check_perm("distribuidora"): pagina_loja("distribuidora")
    else: st.error("Acesso negado.")
elif pg == "sublimacao":
    if check_perm("sublimacao"): pagina_loja("sublimacao")
    else: st.error("Acesso negado.")
elif pg == "historico":    pagina_historico()
elif pg == "exportar":     pagina_exportar()
elif pg == "fornecedores": pagina_fornecedores()
elif pg == "admin":
    if u["acesso"] == "admin": pagina_admin()
    else: st.error("Acesso restrito.")
