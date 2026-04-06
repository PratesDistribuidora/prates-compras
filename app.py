import streamlit as st, pandas as pd, hashlib, io
from supabase import create_client
from datetime import date, datetime
import plotly.express as px
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Prates Compras", page_icon="🛒", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#0D1117!important}
section[data-testid="stSidebar"]{background:#010409!important;border-right:1px solid #21262D!important}
section[data-testid="stSidebar"] *{color:#E6EDF3!important}
section[data-testid="stSidebar"] hr{border-color:#21262D!important}
p,label,div,span{color:#E6EDF3}h1,h2,h3{color:#F0F6FC!important}
[data-testid="stTextInput"] input{background:#161B22!important;color:#E6EDF3!important;border:1px solid #30363D!important;border-radius:8px!important}
[data-testid="stNumberInput"] input{background:#161B22!important;color:#E6EDF3!important;border:1px solid #30363D!important;border-radius:8px!important}
[data-testid="stSelectbox"]>div>div{background:#161B22!important;color:#E6EDF3!important;border:1px solid #30363D!important;border-radius:8px!important}
[data-testid="stTextArea"] textarea{background:#161B22!important;color:#E6EDF3!important;border:1px solid #30363D!important}
[data-testid="stButton"]>button{background:#21262D!important;color:#E6EDF3!important;border:1px solid #30363D!important;border-radius:6px!important;font-weight:500!important}
[data-testid="stButton"]>button:hover{background:#30363D!important;border-color:#58A6FF!important;color:#58A6FF!important}
[data-testid="stButton"]>button[kind="primary"]{background:#238636!important;color:#fff!important;border-color:#2EA043!important}
[data-testid="stButton"]>button[kind="primary"]:hover{background:#2EA043!important}
[data-testid="stPopover"]>div>button{background:#1C2128!important;border:1px solid #30363D!important;border-radius:6px!important;color:#E6EDF3!important}
[data-testid="stPopoverBody"]{padding:.25rem .4rem!important;max-width:180px!important;min-width:140px!important}
[data-testid="stPopoverBody"] [data-testid="stButton"]>button{font-size:.8rem!important;padding:.1rem .5rem!important;min-height:0!important;line-height:1.3!important}
[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"]>div{gap:.1rem!important}
.pg-title{font-size:1.5rem;font-weight:800;color:#F0F6FC;margin-bottom:.2rem}
.pg-sub{font-size:.82rem;color:#8B949E;margin-bottom:1.2rem}
.kpi-box{background:#161B22;border:1px solid #21262D;border-radius:12px;padding:1rem;text-align:center;border-top:3px solid var(--c,#238636)}
.kpi-v{font-size:1.5rem;font-weight:800;color:var(--c,#F0F6FC);margin:.2rem 0}
.kpi-l{font-size:.7rem;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.bdg{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.72rem;font-weight:600;white-space:nowrap}
.b-Pendente{background:rgba(210,153,34,.15);color:#D2991E;border:1px solid rgba(210,153,34,.3)}
.b-Aprovado{background:rgba(88,166,255,.15);color:#58A6FF;border:1px solid rgba(88,166,255,.3)}
.b-Comprado{background:rgba(163,113,247,.15);color:#A371F7;border:1px solid rgba(163,113,247,.3)}
.b-Entregue{background:rgba(63,185,80,.15);color:#3FB950;border:1px solid rgba(63,185,80,.3)}
.b-Cancelado{background:rgba(248,81,73,.15);color:#F85149;border:1px solid rgba(248,81,73,.3)}
.b-Alta{background:rgba(248,81,73,.15);color:#F85149;border:1px solid rgba(248,81,73,.3)}
.b-Media{background:rgba(210,153,34,.15);color:#D2991E;border:1px solid rgba(210,153,34,.3)}
.b-Baixa{background:rgba(63,185,80,.15);color:#3FB950;border:1px solid rgba(63,185,80,.3)}
.b-urg{background:rgba(248,81,73,.25);color:#F85149;border:1px solid #F85149}
.i-nome{font-weight:600;color:#F0F6FC;font-size:.92rem}
.i-meta{font-size:.75rem;color:#8B949E;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:min(500px,55vw)}
.nav-lbl{font-size:.68rem;color:#6E7681;text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin:.6rem 0 .2rem .2rem}
.usr-box{background:#0D1117;border:1px solid #21262D;border-radius:8px;padding:.65rem 1rem;margin:.4rem 0}
.role-tag{display:inline-block;background:#238636;color:#fff;font-size:.62rem;font-weight:700;padding:1px 8px;border-radius:20px;margin-top:3px}

.total-bar{background:#161B22;border:1px solid #21262D;border-radius:10px;padding:.9rem 1.4rem;margin-top:1rem;text-align:right}
.sec-hdr{background:#161B22;border:1px solid #30363D;border-radius:10px;padding:.85rem 1.1rem;margin-bottom:4px}
.sec-body{background:#0D1117;border:1px solid #21262D;border-radius:10px;padding:1rem;margin-bottom:1rem}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def get_sb(): return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
sb = get_sb()

LOJAS = {"distribuidora":{"nome":"Prates Distribuidora","cor":"#58A6FF","icone":"📦"},"sublimacao":{"nome":"Prates Sublimacao","cor":"#3FB950","icone":"🎨"}}
UNID=["UN","CX","PCT","KG","MT","LT","RL","PAR"]
PRIO=["Alta","Media","Baixa"]
ST_ALL=["Pendente","Aprovado","Comprado","Entregue","Cancelado"]
ST_AT=["Pendente","Aprovado"]
ST_HI=["Comprado","Entregue","Cancelado"]

def hp(p): return hashlib.sha256(p.encode()).hexdigest()
def login(email,senha):
    r=sb.table("pc_usuarios").select("*").eq("email",email.strip().lower()).eq("ativo",True).execute()
    if not r.data: return None
    u=r.data[0]; return u if u["senha_hash"]==hp(senha) else None
@st.cache_data(ttl=60)
def gf(): return sb.table("pc_fornecedores").select("*").eq("ativo",True).order("nome").execute().data or []
def cf(d): sb.table("pc_fornecedores").insert(d).execute(); st.cache_data.clear()
def ef(fid,d): sb.table("pc_fornecedores").update(d).eq("id",fid).execute(); st.cache_data.clear()
def df2(fid): sb.table("pc_fornecedores").update({"ativo":False}).eq("id",fid).execute(); st.cache_data.clear()
@st.cache_data(ttl=20)
def gs(loja): return sb.table("pc_secoes").select("*").eq("loja",loja).eq("ativa",True).order("ordem").execute().data or []
def cs(loja,nome):
    ss=gs(loja); o=(max(s["ordem"] for s in ss)+1) if ss else 1
    sb.table("pc_secoes").insert({"loja":loja,"nome":nome,"ordem":o,"ativa":True}).execute(); st.cache_data.clear()
def es(sid,nome): sb.table("pc_secoes").update({"nome":nome}).eq("id",sid).execute(); st.cache_data.clear()
def as2(sid): sb.table("pc_secoes").update({"ativa":False}).eq("id",sid).execute(); st.cache_data.clear()
@st.cache_data(ttl=20)
def gi(sid,sf_key=None):
    sf=list(sf_key) if sf_key else None
    q=sb.table("pc_itens").select("*").eq("secao_id",sid)
    if sf: q=q.in_("status",sf)
    return q.order("criado_em").execute().data or []
@st.cache_data(ttl=20)
def ga(sf_key=None):
    sf=list(sf_key) if sf_key else None
    q=sb.table("pc_itens").select("*, pc_secoes(nome,loja)")
    if sf: q=q.in_("status",sf)
    return q.execute().data or []
def ai(sid,d,user):
    d.update({"secao_id":sid,"criado_por":user,"criado_em":datetime.now().isoformat(),"atualizado_em":datetime.now().isoformat()})
    sb.table("pc_itens").insert(d).execute(); st.cache_data.clear()
def ui(iid,d): d["atualizado_em"]=datetime.now().isoformat(); sb.table("pc_itens").update(d).eq("id",iid).execute(); st.cache_data.clear()
def di(iid): sb.table("pc_itens").delete().eq("id",iid).execute(); st.cache_data.clear()
def ls(ids,sv):
    for iid in ids: sb.table("pc_itens").update({"status":sv,"atualizado_em":datetime.now().isoformat()}).eq("id",iid).execute()
def gu(): return sb.table("pc_usuarios").select("id,nome,email,acesso,ativo").order("nome").execute().data or []
def cu(nome,email,senha,acesso): sb.table("pc_usuarios").insert({"nome":nome,"email":email.lower(),"senha_hash":hp(senha),"acesso":acesso,"ativo":True}).execute()
def uu2(uid,d): sb.table("pc_usuarios").update(d).eq("id",uid).execute()
def pv(loja):
    u=st.session_state.get("usuario")
    if not u: return False
    a=u["acesso"]
    if a in ("admin","ambas"): return True
    if loja=="distribuidora": return a in ("distribuidora","op_dist","op_ambas","operador")
    if loja=="sublimacao":    return a in ("sublimacao","op_sub","op_ambas","operador")
    return False
def is_op():
    u=st.session_state.get("usuario")
    return u and u["acesso"] in ("op_dist","op_sub","op_ambas","operador")
def fm(): return {f["id"]:f["nome"] for f in gf()}
def brl(v):
    try: return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except: return "R$ 0,00"
def bdg(txt):
    c={"Media":"Media","Média":"Media"}.get(txt,txt)
    return f"<span class='bdg b-{c}'>{txt}</span>"
def dbd(dt_str):
    if not dt_str: return ""
    try:
        d=(date.fromisoformat(str(dt_str))-date.today()).days
        if d<0: return f"<span class='bdg b-urg'>Atraso {abs(d)}d</span>"
        if d==0: return f"<span class='bdg b-urg'>Hoje</span>"
        if d<=3: return f"<span class='bdg b-Alta'>{d}d</span>"
        if d<=7: return f"<span class='bdg b-Media'>{d}d</span>"
        return f"<span class='bdg b-Baixa'>{d}d</span>"
    except: return ""

for k,v in [("usuario",None),("pagina","dashboard")]:
    if k not in st.session_state: st.session_state[k]=v

def pagina_login():
    _,c2,_=st.columns([1,1.2,1])
    with c2:
        st.markdown("<div style='text-align:center;padding:50px 0 20px'><img src='data:image/jpeg;base64,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' style='width:90px;height:90px;border-radius:50%'><div style='font-size:1.4rem;font-weight:800;color:#F0F6FC;margin-top:.5rem'>Prates</div><div style='font-size:.85rem;color:#8B949E'>Guia de Compras</div></div>",unsafe_allow_html=True)
        st.markdown("<div style='background:#161B22;border:1px solid #30363D;border-radius:12px;padding:1.8rem'>",unsafe_allow_html=True)
        with st.form("login"):
            email=st.text_input("Email",placeholder="seu@email.com")
            senha=st.text_input("Senha",type="password")
            if st.form_submit_button("Entrar",use_container_width=True,type="primary"):
                u=login(email,senha)
                if u: st.session_state.usuario=u; st.rerun()
                else: st.error("Email ou senha incorretos.")
        st.markdown("</div>",unsafe_allow_html=True)

if not st.session_state.usuario: pagina_login(); st.stop()
u=st.session_state.usuario

with st.sidebar:
    st.markdown("<div style='text-align:center;padding:.2rem 0 0'><img src='data:image/jpeg;base64,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' style='width:66px;height:66px;border-radius:50%;margin-bottom:.1rem'></div>",unsafe_allow_html=True)
    roles={"admin":"Admin","ambas":"Gestor","distribuidora":"Gestor Dist.","sublimacao":"Gestor Sub.",
         "op_dist":"Operador Dist.","op_sub":"Operador Sub.","op_ambas":"Operador","operador":"Operador"}
    st.markdown(f"<div style='background:#0D1117;border:1px solid #21262D;border-radius:6px;padding:.3rem .6rem;margin:.2rem 0'><span style='font-weight:600;font-size:.82rem;color:#F0F6FC'>{u['nome']}</span> <span class='role-tag'>{roles.get(u['acesso'],' ')}</span></div>",unsafe_allow_html=True)
    def nav(label,pg,ico=""):
        if st.button(f"{ico} {label}",use_container_width=True,type="primary" if st.session_state.pagina==pg else "secondary",key=f"nav_{pg}"):
            st.session_state.pagina=pg; st.rerun()
    st.markdown("<div class='nav-lbl'>Principal</div>",unsafe_allow_html=True); nav("Dashboard","dashboard","📊")
    st.markdown("<div class='nav-lbl'>Lancamento</div>",unsafe_allow_html=True)
    if pv("distribuidora"): nav("Distribuidora","distribuidora","📦")
    if pv("sublimacao"): nav("Sublimacao","sublimacao","🎨")
    st.markdown("<div class='nav-lbl'>Consultas</div>",unsafe_allow_html=True)
    nav("Historico","historico","📅"); nav("Exportar","exportar","📥")
    st.markdown("<div class='nav-lbl'>Cadastros</div>",unsafe_allow_html=True); nav("Fornecedores","fornecedores","🏭")
    if u["acesso"]=="admin": st.markdown("<div class='nav-lbl'>Sistema</div>",unsafe_allow_html=True); nav("Administracao","admin","⚙️")
    st.divider()
    if st.button("Sair",use_container_width=True): st.session_state.usuario=None; st.rerun()

def pagina_dashboard():
    # Header
    now = datetime.now()
    st.markdown(f"""
    <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem'>
        <div>
            <div style='font-size:1.3rem;font-weight:800;color:#F0F6FC'>Dashboard</div>
            <div style='font-size:.75rem;color:#8B949E'>{now.strftime("%A, %d de %B de %Y  %H:%M")}</div>
        </div>
    </div>""",unsafe_allow_html=True)

    todos=ga(sf_key=None)
    if not todos:
        st.markdown("""<div style='text-align:center;padding:4rem 2rem;background:#161B22;border:1px dashed #30363D;border-radius:12px'>
            <div style='font-size:2rem'>📦</div>
            <div style='color:#8B949E;margin-top:.5rem'>Nenhum produto lançado ainda.</div>
        </div>""",unsafe_allow_html=True); return

    df=pd.DataFrame(todos)
    df["loja"]=df["pc_secoes"].apply(lambda x:x["loja"] if x else "")
    df["secao_nome"]=df["pc_secoes"].apply(lambda x:x["nome"] if x else "")
    df["total"]=pd.to_numeric(df.get("total",0),errors="coerce").fillna(0)
    df["qtd"]=pd.to_numeric(df.get("qtd",0),errors="coerce").fillna(0)

    total_geral = df["total"].sum()
    total_dist  = df[df["loja"]=="distribuidora"]["total"].sum()
    total_sub   = df[df["loja"]=="sublimacao"]["total"].sum()
    n_pend  = (df["status"]=="Pendente").sum()
    n_aprov = (df["status"]=="Aprovado").sum()
    n_comp  = (df["status"]=="Comprado").sum()
    n_entr  = (df["status"]=="Entregue").sum()
    n_total = len(df)

    # KPI row 1 — valores financeiros
    st.markdown("<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin-bottom:.6rem'>",unsafe_allow_html=True)
    kpis_fin = [
        ("💰 Total em Aberto", brl(total_geral), "#58A6FF", "soma de todos os itens ativos"),
        ("📦 Distribuidora",   brl(total_dist),  "#58A6FF", f"{len(df[df['loja']=='distribuidora'])} itens"),
        ("🎨 Sublimação",      brl(total_sub),   "#3FB950", f"{len(df[df['loja']=='sublimacao'])} itens"),
    ]
    cols_fin = st.columns(3)
    for i,(lbl,val,cor,sub) in enumerate(kpis_fin):
        cols_fin[i].markdown(f"""<div class='kpi-box' style='--c:{cor}'>
            <div class='kpi-l'>{lbl}</div>
            <div class='kpi-v'>{val}</div>
            <div style='font-size:.7rem;color:#8B949E;margin-top:.1rem'>{sub}</div>
        </div>""",unsafe_allow_html=True)

    st.markdown("<br style='margin:.3rem'>",unsafe_allow_html=True)

    # KPI row 2 — contadores de status
    status_kpis = [
        ("🟡 Pendente",  n_pend,  "#D2991E"),
        ("🔵 Aprovado",  n_aprov, "#58A6FF"),
        ("🟣 Comprado",  n_comp,  "#A371F7"),
        ("🟢 Entregue",  n_entr,  "#3FB950"),
        ("📋 Total Itens", n_total, "#8B949E"),
    ]
    cols_st = st.columns(5)
    for i,(lbl,val,cor) in enumerate(status_kpis):
        cols_st[i].markdown(f"""<div style='background:#161B22;border:1px solid #21262D;border-radius:10px;
            padding:.7rem;text-align:center;border-top:2px solid {cor}'>
            <div style='font-size:.68rem;color:#8B949E;text-transform:uppercase;letter-spacing:.05em;font-weight:600'>{lbl}</div>
            <div style='font-size:1.4rem;font-weight:700;color:{cor}'>{val}</div>
        </div>""",unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    # Alertas urgência
    if "dt_necessidade" in df.columns:
        urg=[]
        for _,r in df.iterrows():
            if not r.get("dt_necessidade") or r.get("status") not in ST_AT: continue
            try:
                d=(date.fromisoformat(str(r["dt_necessidade"]))-date.today()).days
                if d<=3: urg.append((d,r))
            except: pass
        if urg:
            st.markdown(f"""<div style='background:rgba(248,81,73,.08);border:1px solid rgba(248,81,73,.3);
                border-radius:10px;padding:.8rem 1rem;margin-bottom:1rem'>
                <div style='font-size:.85rem;font-weight:700;color:#F85149;margin-bottom:.4rem'>
                    ⚠️ {len(urg)} item(ns) com prazo crítico (próximos 3 dias)
                </div>""",unsafe_allow_html=True)
            for d,r in sorted(urg):
                st.markdown(f"<div style='font-size:.8rem;color:#E6EDF3;padding:.2rem 0'>"
                            f"• <b>{r['produto']}</b> — {r['secao_nome']} {dbd(r['dt_necessidade'])}</div>",
                            unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

    # Gráficos
    cm={"Pendente":"#D2991E","Aprovado":"#58A6FF","Comprado":"#A371F7","Entregue":"#3FB950","Cancelado":"#F85149"}
    chart_layout = dict(paper_bgcolor="#161B22",plot_bgcolor="#0D1117",
                        margin=dict(t=30,b=10,l=10,r=10),height=220,
                        font=dict(color="#E6EDF3",size=11),
                        xaxis=dict(gridcolor="#21262D",showline=False),
                        yaxis=dict(gridcolor="#21262D",showline=False))

    g1,g2=st.columns(2)
    with g1:
        st.markdown("<div style='font-size:.85rem;font-weight:600;color:#8B949E;margin-bottom:.3rem'>ITENS POR STATUS</div>",unsafe_allow_html=True)
        s=df.groupby("status").size().reset_index(name="qtd")
        fig=px.bar(s,x="status",y="qtd",color="status",color_discrete_map=cm,template="plotly_dark",text="qtd")
        fig.update_traces(textposition="outside",textfont_size=11)
        fig.update_layout(showlegend=False,**chart_layout)
        st.plotly_chart(fig,use_container_width=True)

    with g2:
        st.markdown("<div style='font-size:.85rem;font-weight:600;color:#8B949E;margin-bottom:.3rem'>DISTRIBUIÇÃO POR LOJA</div>",unsafe_allow_html=True)
        l=df.groupby("loja").size().reset_index(name="qtd")
        l["nome"]=l["loja"].map({"distribuidora":"Distribuidora","sublimacao":"Sublimacao"})
        fig2=px.pie(l,names="nome",values="qtd",color_discrete_sequence=["#58A6FF","#3FB950"],hole=.55,template="plotly_dark")
        fig2.update_traces(textinfo="percent+label",textfont_size=11)
        fig2.update_layout(paper_bgcolor="#161B22",margin=dict(t=30,b=10),height=220,
                           font=dict(color="#E6EDF3"),showlegend=False)
        st.plotly_chart(fig2,use_container_width=True)

    g3,g4=st.columns(2)
    with g3:
        st.markdown("<div style='font-size:.85rem;font-weight:600;color:#8B949E;margin-bottom:.3rem'>TOP 5 MAIS COMPRADOS (qtd)</div>",unsafe_allow_html=True)
        top=df[df["status"].isin(["Comprado","Entregue"])].groupby("produto")["qtd"].sum().sort_values(ascending=True).tail(5).reset_index()
        if not top.empty:
            fig3=px.bar(top,x="qtd",y="produto",orientation="h",template="plotly_dark",
                        color_discrete_sequence=["#3FB950"],text="qtd")
            fig3.update_traces(textposition="outside")
            fig3.update_layout(showlegend=False,**chart_layout)
            st.plotly_chart(fig3,use_container_width=True)
        else:
            st.markdown("<div style='color:#8B949E;font-size:.8rem;padding:2rem 0;text-align:center'>Nenhum item comprado ainda.</div>",unsafe_allow_html=True)

    with g4:
        st.markdown("<div style='font-size:.85rem;font-weight:600;color:#8B949E;margin-bottom:.3rem'>VALOR POR SEÇÃO</div>",unsafe_allow_html=True)
        sec=df.groupby(["secao_nome","loja"])["total"].sum().reset_index().sort_values("total",ascending=True)
        sec=sec[sec["total"]>0]
        if not sec.empty:
            fig4=px.bar(sec,x="total",y="secao_nome",orientation="h",color="loja",
                        color_discrete_map={"distribuidora":"#58A6FF","sublimacao":"#3FB950"},
                        template="plotly_dark",labels={"total":"R$","secao_nome":"","loja":"Loja"})
            fig4.update_layout(legend=dict(bgcolor="#161B22",orientation="h",yanchor="bottom",y=1.02),**chart_layout)
            st.plotly_chart(fig4,use_container_width=True)
        else:
            st.markdown("<div style='color:#8B949E;font-size:.8rem;padding:2rem 0;text-align:center'>Sem valores registrados.</div>",unsafe_allow_html=True)

def pagina_loja(loja):
    info=LOJAS[loja]; cor=info["cor"]; fmc=fm()
    st.markdown(f"<div style='font-size:1.1rem;font-weight:700;color:#F0F6FC;margin-bottom:.1rem'>{info['icone']} {info['nome']}</div>",unsafe_allow_html=True)


    # BARRA PRINCIPAL
    ca,cb=st.columns([5,2])
    busca=ca.text_input("",placeholder="Buscar produto, marca, SKU...",label_visibility="collapsed",key=f"bsc_{loja}")
    with cb:
        btn1,btn2=st.columns(2)
        if btn1.button("+ Produto",use_container_width=True,type="primary",key=f"bcp_{loja}"):
            st.session_state[f"cp_{loja}"]=not st.session_state.get(f"cp_{loja}",False)
            st.session_state[f"gs_{loja}"]=False
        if btn2.button("Secoes",use_container_width=True,key=f"bgs_{loja}"):
            st.session_state[f"gs_{loja}"]=not st.session_state.get(f"gs_{loja}",False)
            st.session_state[f"cp_{loja}"]=False

    ff1,ff2=st.columns(2)
    fst=ff1.radio("",["Todos"]+ST_AT,horizontal=True,key=f"fst_{loja}",label_visibility="collapsed")
    fpr=ff2.radio("",["Todas"]+PRIO,horizontal=True,key=f"fpr_{loja}",label_visibility="collapsed")

    # PAINEL GERENCIAR SECOES
    if st.session_state.get(f"gs_{loja}"):
        st.markdown("<div style='background:#161B22;border:1px solid #30363D;border-radius:10px;padding:.8rem 1rem;margin-bottom:.8rem'>",unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:.6rem'><span style='font-size:.88rem;font-weight:700;color:#58A6FF'>Secoes — {info['nome']}</span></div>",unsafe_allow_html=True)
        secoes_g=gs(loja)
        with st.form(f"fns_{loja}"):
            gn1,gn2=st.columns([5,1])
            nomes=gn1.text_input("",placeholder="Nome da nova secao",label_visibility="collapsed")
            if gn2.form_submit_button("+ Criar",type="primary",use_container_width=True):
                if nomes.strip(): cs(loja,nomes.strip()); st.rerun()
        if secoes_g:
            for sec in secoes_g:
                with st.form(f"fsec_{sec['id']}"):
                    ge1,ge2,ge3=st.columns([5,1,1])
                    nn=ge1.text_input("",value=sec["nome"],label_visibility="collapsed")
                    if ge2.form_submit_button("Salvar",type="primary",use_container_width=True):
                        if nn.strip(): es(sec["id"],nn.strip()); st.rerun()
                    if ge3.form_submit_button("Excluir",use_container_width=True):
                        as2(sec["id"]); st.rerun()
        if st.button("Fechar",key=f"fgs_{loja}",use_container_width=False):
            st.session_state[f"gs_{loja}"]=False; st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

    # FORM CRIAR PRODUTO (com selecao de secao)
    if st.session_state.get(f"cp_{loja}"):
        secoes_disp=gs(loja)
        if not secoes_disp:
            st.warning("Crie uma secao primeiro para poder adicionar produtos.")
        else:
            st.markdown("<div style='border-top:2px solid #238636;padding-top:.8rem;margin-bottom:.8rem'>",unsafe_allow_html=True)
            st.markdown("<div style='font-size:.9rem;font-weight:700;color:#3FB950;margin-bottom:.6rem'>Novo Produto</div>",unsafe_allow_html=True)
            forns=gf(); fm2={f["nome"]:f["id"] for f in forns}; fopts=["(Nenhum)"]+list(fm2.keys())
            sec_opts={s["nome"]:s["id"] for s in secoes_disp}
            with st.form(f"fcp_{loja}"):
                r1a,r1b,r1c,r1d,r1e,r1f=st.columns([2,2.5,2,1.5,1.5,2])
                sec_esc=r1a.selectbox("Secao",list(sec_opts.keys()),label_visibility="visible")
                prod_cp=r1b.text_input("Produto *")
                marca_cp=r1c.text_input("Marca")
                sku_cp=r1d.text_input("SKU")
                ean_cp=r1e.text_input("EAN")
                forn_cp=r1f.selectbox("Fornecedor",fopts)
                r2a,r2b,r2c,r2d,r2e,r2f,r2g=st.columns([1.2,1.5,1.5,1.5,1.5,1.5,1])
                qtd_cp=r2a.number_input("Qtd",min_value=0.0,step=1.0)
                un_cp=r2b.selectbox("Unid",UNID)
                preco_cp=r2c.number_input("Preco",min_value=0.0,step=0.01,format="%.2f")
                prio_cp=r2d.selectbox("Prioridade",PRIO,index=1)
                dt_cp=r2e.date_input("Necessidade",value=None)
                img_cp=r2f.text_input("URL Img",placeholder="https://...")
                r2g.markdown("<br>",unsafe_allow_html=True)
                submitted=r2g.form_submit_button("Salvar",type="primary",use_container_width=True)
                if st.form_submit_button("Cancelar",use_container_width=False):
                    st.session_state[f"cp_{loja}"]=False; st.rerun()
                if submitted:
                    if prod_cp.strip():
                        ai(sec_opts[sec_esc],{"produto":prod_cp.strip(),"marca":marca_cp.strip(),"sku":sku_cp.strip(),"ean":ean_cp.strip(),"fornecedor_id":fm2.get(forn_cp) if forn_cp!="(Nenhum)" else None,"imagem_url":img_cp.strip() or None,"qtd":qtd_cp,"unidade":un_cp,"preco_unit":preco_cp,"total":round(qtd_cp*preco_cp,2),"prioridade":prio_cp,"dt_necessidade":str(dt_cp) if dt_cp else None,"obs":"","status":"Pendente"},u["nome"])
                        st.session_state[f"cp_{loja}"]=False; st.rerun()
                    else: st.warning("Informe o nome do produto.")
            st.markdown("</div>",unsafe_allow_html=True)

    # SELECAO EM LOTE
    sel_key=f"sel_{loja}"
    if sel_key not in st.session_state: st.session_state[sel_key]=[]
    marcados=st.session_state[sel_key]
    if marcados and not is_op():
        st.markdown(f"<div style='background:#1C2128;border:1px solid #30363D;border-radius:8px;padding:.7rem 1rem;margin-bottom:.8rem'><b style='color:#58A6FF'>{len(marcados)} item(ns) selecionado(s)</b></div>",unsafe_allow_html=True)
        la,lb,lc,ld,le=st.columns(5)
        for col,lbl,sv,tp in [(la,"Aprovar","Aprovado","primary"),(lb,"Comprado","Comprado","secondary"),(lc,"Entregue","Entregue","secondary"),(ld,"Cancelar","Cancelado","secondary")]:
            if col.button(lbl,key=f"lote_{sv}_{loja}",use_container_width=True,type=tp): ls(marcados,sv); st.session_state[sel_key]=[]; st.rerun()
        if le.button("Limpar",key=f"clr_{loja}",use_container_width=True): st.session_state[sel_key]=[]; st.rerun()

    # SECOES
    secoes=gs(loja)
    if not secoes:
        st.markdown("<div style='text-align:center;padding:3rem;background:#161B22;border:1px dashed #30363D;border-radius:12px;color:#8B949E'>Nenhuma secao. Clique em <b>Gerenciar Secoes</b> para criar.</div>",unsafe_allow_html=True); return

    total_loja=0
    for sec in secoes:
        itens_all=gi(sec["id"],sf_key=tuple(ST_AT))
        itens=itens_all[:]
        if fst!="Todos": itens=[i for i in itens if i.get("status")==fst]
        if fpr!="Todas": itens=[i for i in itens if i.get("prioridade")==fpr]
        if busca:
            b=busca.lower(); itens=[i for i in itens if b in " ".join([i.get("produto",""),i.get("marca",""),i.get("sku",""),i.get("ean","")]).lower()]
        tsec=sum(float(i.get("total") or 0) for i in itens_all); total_loja+=tsec
        npend=sum(1 for i in itens_all if i.get("status")=="Pendente")
        # Esconde secoes sem itens quando filtros ativos
        if (busca or fst!="Todos" or fpr!="Todas") and not itens: continue
        exp_key=f"exp_{sec['id']}"
        if exp_key not in st.session_state: st.session_state[exp_key]=True

        # CABECALHO DA SECAO — sem botao editar inline
        hcols=st.columns([7,1])
        pend_txt=f" &nbsp;·&nbsp; <span style='color:#D2991E'>{npend} pendentes</span>" if npend else ""
        arrow = '▼' if st.session_state[exp_key] else '▶'
        hcols[0].markdown(f"<div class='sec-hdr'><span style='font-size:1rem;font-weight:700;color:#F0F6FC'>{arrow} {sec['nome']}</span><span style='font-size:.8rem;color:#8B949E'> &nbsp;·&nbsp; {len(itens_all)} itens &nbsp;·&nbsp; {brl(tsec)}{pend_txt}</span></div>",unsafe_allow_html=True)
        if hcols[1].button("Abrir" if not st.session_state[exp_key] else "Fechar",key=f"tog_{sec['id']}",use_container_width=True):
            st.session_state[exp_key]=not st.session_state[exp_key]; st.rerun()

        # CORPO DA SECAO
        if st.session_state[exp_key]:
            st.markdown(f"<div class='sec-body' style='--bc:{cor}'>",unsafe_allow_html=True)
            if itens:
                for item in itens:
                    iid=item["id"]; sl=st.session_state.get(sel_key,[])
                    c0,c1,c2,c3,c4,c5,c6,c7,c8=st.columns([.4,3.5,1.5,.8,.8,1.5,1.2,1.2,.8])
                    sel=c0.checkbox("",value=iid in sl,key=f"chk_{iid}",label_visibility="collapsed")
                    if sel and iid not in sl: st.session_state.setdefault(sel_key,[]).append(iid)
                    elif not sel and iid in sl: st.session_state[sel_key].remove(iid)
                    img=item.get("imagem_url","")
                    parts=[]
                    if item.get("marca"): parts.append(f"Marca: {item['marca']}")
                    if item.get("sku"):   parts.append(f"SKU: {item['sku']}")
                    if item.get("ean"):   parts.append(f"EAN: {item['ean']}")
                    fnome=fmc.get(item.get("fornecedor_id"),"")
                    if fnome: parts.append(f"Fornecedor: {fnome}")
                    meta=" · ".join(parts)
                    img_html='<img src="'+img+'" style="width:34px;height:34px;object-fit:cover;border-radius:6px;border:1px solid #30363D">' if img else '<div style="width:34px;height:34px;background:#21262D;border-radius:6px;display:flex;align-items:center;justify-content:center">📦</div>'
                    meta_txt=meta
                    pnome=item.get("produto","")
                    c1.markdown(f"<div style='display:flex;align-items:center;gap:.6rem'>{img_html}<div><div class='i-nome'>{pnome}</div><div class='i-meta'>{meta_txt}</div></div></div>",unsafe_allow_html=True)
                    c2.markdown(f"<div style='font-size:.78rem;color:#8B949E;padding-top:.3rem'>{sec['nome']}</div>",unsafe_allow_html=True)
                    c3.markdown(f"<div style='text-align:center;padding-top:.3rem'>{item.get('qtd','')} {item.get('unidade','')}</div>",unsafe_allow_html=True)
                    c4.markdown(f"<div style='text-align:right;font-size:.8rem;color:#8B949E;padding-top:.3rem'>{brl(item.get('preco_unit',0))}</div>",unsafe_allow_html=True)
                    c5.markdown(f"<div style='text-align:right;font-weight:700;color:{cor};padding-top:.3rem'>{brl(item.get('total',0))}</div>",unsafe_allow_html=True)
                    c6.markdown(bdg(item.get("status",""))+" "+dbd(item.get("dt_necessidade")),unsafe_allow_html=True)
                    c7.markdown(bdg(item.get("prioridade","")),unsafe_allow_html=True)
                    with c8:
                        with st.popover("Editar"):
                            st.markdown(f"<div style='font-size:.8rem;font-weight:600;color:#F0F6FC;margin-bottom:.3rem'>{pnome}</div>",unsafe_allow_html=True)
                            if is_op():
                                st.caption("Acesso restrito.")
                            else:
                              cur_st=item.get("status","Pendente")
                              for sv in ST_ALL:
                                is_cur=sv==cur_st
                                lbl=f"✓ {sv}" if is_cur else sv
                                if st.button(lbl,key=f"st_{sv}_{iid}",use_container_width=True,type="primary" if is_cur else "secondary"):
                                    ui(iid,{"status":sv}); st.rerun()
                              st.divider()
                              if st.button("Editar",key=f"edbtn_{iid}",use_container_width=True): st.session_state[f"ed_{iid}"]=True
                              if st.button("Deletar",key=f"del_{iid}",use_container_width=True): di(iid); st.rerun()
                    if st.session_state.get(f"ed_{iid}"):
                        st.markdown("---")
                        forns2=gf(); fm3={f["nome"]:f["id"] for f in forns2}; fopts2=["(Nenhum)"]+list(fm3.keys())  # cached
                        fat="(Nenhum)"
                        if item.get("fornecedor_id"):
                            for f in forns2:
                                if f["id"]==item["fornecedor_id"]: fat=f["nome"]; break
                        with st.form(f"fedit_{iid}"):
                            st.markdown("**Editar Produto**")
                            ec1,ec2,ec3=st.columns(3)
                            ep=ec1.text_input("Produto",value=item.get("produto",""))
                            em=ec2.text_input("Marca",value=item.get("marca",""))
                            esk=ec3.text_input("SKU",value=item.get("sku",""))
                            ec4,ec5,ec6=st.columns(3)
                            ee=ec4.text_input("EAN",value=item.get("ean",""))
                            ef2=ec5.selectbox("Fornecedor",fopts2,index=fopts2.index(fat) if fat in fopts2 else 0)
                            ei=ec6.text_input("URL Imagem",value=item.get("imagem_url",""))
                            eq1,eq2,eq3,eq4=st.columns(4)
                            eq=eq1.number_input("Qtd",min_value=0.0,value=float(item.get("qtd",0)),step=1.0)
                            eun=eq2.selectbox("Unidade",UNID,index=UNID.index(item.get("unidade","UN")) if item.get("unidade","UN") in UNID else 0)
                            epr=eq3.number_input("Preco",min_value=0.0,value=float(item.get("preco_unit",0)),step=0.01,format="%.2f")
                            eprio=eq4.selectbox("Prioridade",PRIO,index=PRIO.index(item.get("prioridade","Media")) if item.get("prioridade") in PRIO else 1)
                            eobs=st.text_area("Obs",value=item.get("obs",""),height=60)
                            es1,es2=st.columns(2)
                            if es1.form_submit_button("Salvar",type="primary"):
                                ui(iid,{"produto":ep,"marca":em,"sku":esk,"ean":ee,"fornecedor_id":fm3.get(ef2) if ef2!="(Nenhum)" else None,"imagem_url":ei or None,"qtd":eq,"unidade":eun,"preco_unit":epr,"total":round(eq*epr,2),"prioridade":eprio,"obs":eobs})
                                st.session_state[f"ed_{iid}"]=False; st.rerun()
                            if es2.form_submit_button("Cancelar"): st.session_state[f"ed_{iid}"]=False; st.rerun()
            else:
                st.markdown("<div style='color:#8B949E;padding:.3rem 0;font-size:.8rem'>Sem itens nesta seção.</div>",unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

    st.markdown(f"<div class='total-bar'><span style='color:#8B949E'>{info['nome']} — Total em aberto:</span> <span style='color:{cor};font-size:1.2rem;font-weight:700;margin-left:.8rem'>{brl(total_loja)}</span></div>",unsafe_allow_html=True)


def pagina_historico():
    st.markdown("<div class='pg-title'>📅 Historico</div>",unsafe_allow_html=True)
    st.markdown("<div class='pg-sub'>Itens Comprado, Entregue ou Cancelado</div>",unsafe_allow_html=True)
    todos=ga(sf_key=tuple(ST_HI))
    if not todos: st.info("Nenhum item no historico ainda."); return
    df=pd.DataFrame(todos)
    df["loja"]=df["pc_secoes"].apply(lambda x:x["loja"] if x else "")
    df["secao_nome"]=df["pc_secoes"].apply(lambda x:x["nome"] if x else "")
    df["total"]=pd.to_numeric(df.get("total",0),errors="coerce").fillna(0)
    df["loja_nome"]=df["loja"].map({"distribuidora":"Distribuidora","sublimacao":"Sublimacao"})
    fmc=fm()
    if "fornecedor_id" in df.columns: df["fornecedor"]=df["fornecedor_id"].map(fmc).fillna("")
    f1,f2,f3,f4,f5=st.columns(5)
    fl=f1.selectbox("",["Todas","Distribuidora","Sublimacao"],key="hfl",label_visibility="collapsed")
    fs=f2.selectbox("",["Todos"]+ST_HI,key="hfs",label_visibility="collapsed")
    fp=f3.selectbox("",["Todas"]+PRIO,key="hfp",label_visibility="collapsed")
    fb=f4.text_input("","",placeholder="Produto...",key="hfb",label_visibility="collapsed")
    fsec=f5.selectbox("",["Todas"]+sorted(df["secao_nome"].unique().tolist()),key="hfsec",label_visibility="collapsed")
    dff=df.copy()
    if fl!="Todas": dff=dff[dff["loja"]==("distribuidora" if fl=="Distribuidora" else "sublimacao")]
    if fs!="Todos": dff=dff[dff["status"]==fs]
    if fp!="Todas": dff=dff[dff["prioridade"]==fp]
    if fb: dff=dff[dff["produto"].str.lower().str.contains(fb.lower(),na=False)]
    if fsec!="Todas": dff=dff[dff["secao_nome"]==fsec]
    st.markdown(f"<div style='color:#8B949E;font-size:.82rem;margin:.4rem 0'>{len(dff)} itens · Total: <b style='color:#58A6FF'>{brl(dff['total'].sum())}</b></div>",unsafe_allow_html=True)
    cols=["produto","marca","sku","ean","secao_nome","loja_nome","fornecedor","qtd","unidade","total","prioridade","status","dt_necessidade","obs","criado_por"]
    ce=[c for c in cols if c in dff.columns]
    st.dataframe(dff[ce].rename(columns={"produto":"Produto","marca":"Marca","sku":"SKU","ean":"EAN","secao_nome":"Secao","loja_nome":"Loja","fornecedor":"Fornecedor","qtd":"Qtd","unidade":"Unid","total":"Total","prioridade":"Prioridade","status":"Status","dt_necessidade":"Dt Necessidade","obs":"Obs","criado_por":"Por"}),use_container_width=True,hide_index=True,height=500)

def pagina_fornecedores():
    st.markdown("<div class='pg-title'>🏭 Fornecedores</div>",unsafe_allow_html=True)
    tab_l,tab_n=st.tabs(["Lista","Novo Fornecedor"])
    with tab_n:
        with st.form("fnovoforn"):
            c1,c2=st.columns(2); fn=c1.text_input("Nome *"); fc=c2.text_input("Contato")
            c3,c4,c5=st.columns(3); ft=c3.text_input("Telefone"); fe=c4.text_input("Email"); fcnpj=c5.text_input("CNPJ")
            fo=st.text_area("Obs",height=70)
            if st.form_submit_button("Cadastrar",type="primary"):
                if fn.strip(): cf({"nome":fn.strip(),"contato":fc,"telefone":ft,"email":fe,"cnpj":fcnpj,"observacoes":fo,"ativo":True}); st.success("Cadastrado!"); st.rerun()
                else: st.warning("Informe o nome.")
    with tab_l:
        forns=gf()
        if not forns: st.info("Nenhum fornecedor."); return
        bf=st.text_input("","",placeholder="Buscar...",key="bff",label_visibility="collapsed")
        if bf: forns=[f for f in forns if bf.lower() in f["nome"].lower()]
        for forn in forns:
            st.markdown(f"<div style='background:#161B22;border:1px solid #30363D;border-radius:10px;padding:.8rem 1rem;margin-bottom:.5rem'><b style='color:#F0F6FC'>{forn['nome']}</b>" + (f" &nbsp;·&nbsp; {forn.get('telefone','')}" if forn.get("telefone") else "") + (f" &nbsp;·&nbsp; CNPJ: {forn.get('cnpj','')}" if forn.get("cnpj") else "")+"</div>",unsafe_allow_html=True)
            with st.form(f"ef_{forn['id']}"):
                e1,e2=st.columns(2); en=e1.text_input("Nome",value=forn.get("nome","")); ec=e2.text_input("Contato",value=forn.get("contato",""))
                e3,e4,e5=st.columns(3); et=e3.text_input("Telefone",value=forn.get("telefone","")); ee=e4.text_input("Email",value=forn.get("email","")); ecnpj=e5.text_input("CNPJ",value=forn.get("cnpj",""))
                eo=st.text_area("Obs",value=forn.get("observacoes",""),height=60)
                s1,_,s3=st.columns(3)
                if s1.form_submit_button("Salvar",type="primary"): ef(forn["id"],{"nome":en,"contato":ec,"telefone":et,"email":ee,"cnpj":ecnpj,"observacoes":eo}); st.success("Salvo!"); st.rerun()
                if s3.form_submit_button("Remover"): df2(forn["id"]); st.rerun()

def pagina_exportar():
    st.markdown("<div class='pg-title'>📥 Exportar</div>",unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        le=st.selectbox("Loja",["Ambas","Distribuidora","Sublimacao"])
        lk={"Ambas":"ambas","Distribuidora":"distribuidora","Sublimacao":"sublimacao"}[le]
        inc=st.checkbox("Incluir Historico (Comprado/Entregue/Cancelado)")
    with c2:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("Gerar Excel",use_container_width=True,type="primary"):
            sf=None if inc else ST_AT; lojas_=["distribuidora","sublimacao"] if lk=="ambas" else [lk]
            wb=Workbook(); ws=wb.active; ws.title="Compras"
            def thin(): s=Side(style="thin",color="2D3748"); return Border(left=s,right=s,top=s,bottom=s)
            row=1; fme=fm()
            ws.merge_cells(f"A{row}:L{row}"); c=ws.cell(row=row,column=1,value="GRUPO PRATES - GUIA DE COMPRAS")
            c.font=Font(bold=True,size=14,color="FFFFFF"); c.fill=PatternFill("solid",start_color="0D1117")
            c.alignment=Alignment(horizontal="center"); ws.row_dimensions[row].height=28; row+=1
            hdrs=["Secao","Produto","Marca","SKU","EAN","Fornecedor","Qtd","Unid","Preco","Total","Prioridade","Status"]
            for i,h in enumerate(hdrs,1):
                ws.column_dimensions[get_column_letter(i)].width=[20,28,16,14,14,18,7,6,12,12,12,12][i-1]
                c=ws.cell(row=row,column=i,value=h); c.font=Font(bold=True,color="FFFFFF",size=9)
                c.fill=PatternFill("solid",start_color="21262D"); c.alignment=Alignment(horizontal="center"); c.border=thin()
            ws.row_dimensions[row].height=18; row+=1
            for loja in lojas_:
                info=LOJAS[loja]; secoes=gs(loja)
                ws.merge_cells(f"A{row}:L{row}"); c=ws.cell(row=row,column=1,value=f"  {info['nome'].upper()}")
                c.font=Font(bold=True,size=11,color="FFFFFF"); c.fill=PatternFill("solid",start_color="161B22")
                c.alignment=Alignment(horizontal="left"); ws.row_dimensions[row].height=20; row+=1; tl=0
                for sec in secoes:
                    for ri,item in enumerate(gi(sec["id"],sf_key=tuple(sf) if sf else None)):
                        zb="0D1117" if ri%2==0 else "161B22"
                        vals=[sec["nome"],item.get("produto",""),item.get("marca",""),item.get("sku",""),item.get("ean",""),fme.get(item.get("fornecedor_id"),""),item.get("qtd",""),item.get("unidade",""),item.get("preco_unit",""),item.get("total",""),item.get("prioridade",""),item.get("status","")]
                        for ci,v in enumerate(vals,1):
                            c=ws.cell(row=row,column=ci,value=v); c.font=Font(size=9,color="E6EDF3")
                            c.fill=PatternFill("solid",start_color=zb); c.alignment=Alignment(horizontal="center" if ci>5 else "left"); c.border=thin()
                            if ci in (9,10) and v: c.number_format='"R$" #,##0.00'
                        ws.row_dimensions[row].height=16; tl+=float(item.get("total") or 0); row+=1
                ws.merge_cells(f"A{row}:I{row}"); c=ws.cell(row=row,column=1,value=f"TOTAL {info['nome'].upper()}")
                c.font=Font(bold=True,size=10,color="FFFFFF"); c.fill=PatternFill("solid",start_color="0D1117"); c.alignment=Alignment(horizontal="right"); c.border=thin()
                c=ws.cell(row=row,column=10,value=tl); c.font=Font(bold=True,size=10,color="58A6FF"); c.fill=PatternFill("solid",start_color="0D1117"); c.number_format='"R$" #,##0.00'; c.border=thin()
                ws.row_dimensions[row].height=22; row+=2
            buf=io.BytesIO(); wb.save(buf); buf.seek(0)
            st.download_button("Baixar Excel",buf,file_name=f"Compras_{datetime.now().strftime('%Y%m%d')}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)

def pagina_admin():
    st.markdown("<div class='pg-title'>⚙️ Administracao</div>",unsafe_allow_html=True)
    tab_u,tab_s=st.tabs(["Usuarios","Secoes"])
    with tab_u:
        st.markdown("#### Novo Usuario")
        with st.form("fnu"):
            c1,c2=st.columns(2); nome=c1.text_input("Nome"); email=c2.text_input("Email")
            c3,c4=st.columns(2); senha=c3.text_input("Senha",type="password")
            acesso=c4.selectbox("Acesso",["op_dist","op_sub","op_ambas","distribuidora","sublimacao","ambas","admin"],
    format_func=lambda x:{
        "op_dist":"Operador — só Distribuidora",
        "op_sub":"Operador — só Sublimação",
        "op_ambas":"Operador — ambas as lojas",
        "distribuidora":"Gestor — só Distribuidora",
        "sublimacao":"Gestor — só Sublimação",
        "ambas":"Gestor — ambas as lojas",
        "admin":"Administrador"
    }[x])
            if st.form_submit_button("Criar",type="primary"):
                if nome and email and senha: cu(nome,email,senha,acesso); st.success("Criado!"); st.rerun()
        st.markdown("#### Usuarios")
        for usu in gu():
            st.markdown(f"<div style='background:#161B22;border:1px solid #30363D;border-radius:8px;padding:.8rem 1rem;margin-bottom:.3rem'><b style='color:#F0F6FC'>{usu['nome']}</b> · {usu['email']} · <span style='color:#8B949E'>{usu['acesso']}</span> · {'✅' if usu['ativo'] else '❌'}</div>",unsafe_allow_html=True)
            with st.form(f"eu_{usu['id']}"):
                e1,e2=st.columns(2); en=e1.text_input("Nome",value=usu["nome"]); ee=e2.text_input("Email",value=usu["email"])
                e3,e4=st.columns(2)
                _opts=["op_dist","op_sub","op_ambas","distribuidora","sublimacao","ambas","admin"]
                _fmt={"op_dist":"Op. Distribuidora","op_sub":"Op. Sublimação","op_ambas":"Op. Ambas","distribuidora":"Gestor Distribuidora","sublimacao":"Gestor Sublimação","ambas":"Gestor Ambas","admin":"Administrador"}
                ea=e3.selectbox("Acesso",_opts,index=_opts.index(usu["acesso"]) if usu["acesso"] in _opts else 0,format_func=lambda x:_fmt.get(x,x))
                ep=e4.text_input("Nova Senha",type="password")
                s1,s2=st.columns(2)
                if s1.form_submit_button("Salvar",type="primary"):
                    d={"nome":en,"email":ee,"acesso":ea}
                    if ep: d["senha_hash"]=hp(ep)
                    uu2(usu["id"],d); st.success("Salvo!"); st.rerun()
                if s2.form_submit_button("Desativar" if usu["ativo"] else "Ativar"): uu2(usu["id"],{"ativo":not usu["ativo"]}); st.rerun()
    with tab_s:
        for loja,info in LOJAS.items():
            st.markdown(f"#### {info['icone']} {info['nome']}")
            for sec in gs(loja):
                with st.form(f"as_{sec['id']}"):
                    s1,s2,s3=st.columns([4,1.5,1]); nn=s1.text_input("",value=sec["nome"],label_visibility="collapsed")
                    if s2.form_submit_button("Salvar"): es(sec["id"],nn); st.rerun()
                    if s3.form_submit_button("Excluir"): as2(sec["id"]); st.rerun()
            st.divider()

pg=st.session_state.pagina
if   pg=="dashboard":    pagina_dashboard()
elif pg=="distribuidora":
    if pv("distribuidora"): pagina_loja("distribuidora")
    else: st.error("Acesso negado.")
elif pg=="sublimacao":
    if pv("sublimacao"): pagina_loja("sublimacao")
    else: st.error("Acesso negado.")
elif pg=="historico":    pagina_historico()
elif pg=="exportar":     pagina_exportar()
elif pg=="fornecedores": pagina_fornecedores()
elif pg=="admin":
    if u["acesso"]=="admin": pagina_admin()
    else: st.error("Acesso restrito.")
