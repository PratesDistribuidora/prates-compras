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
section[data-testid="stSidebar"] [data-testid="stButton"]>button{font-size:.78rem!important;padding:.25rem .5rem!important;min-height:1.8rem!important}
[data-testid="stPopover"]>div>button{background:#1C2128!important;border:1px solid #30363D!important;border-radius:6px!important;color:#E6EDF3!important}
[data-testid="stPopoverBody"] [data-testid="stButton"]>button{font-size:.72rem!important;padding:.15rem .3rem!important;min-height:1.5rem!important;line-height:1.1!important}
[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] p{font-size:.78rem!important}
[data-testid="stPopoverBody"]{padding:.5rem!important}
[data-testid="stRadio"] label{font-size:.8rem!important;padding:.1rem .4rem!important}
[data-testid="stRadio"]>div{gap:.3rem!important;flex-wrap:wrap}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p{font-size:.8rem!important}
[data-testid="stButton"]>button:hover{background:#30363D!important;border-color:#58A6FF!important;color:#58A6FF!important}
[data-testid="stButton"]>button[kind="primary"]{background:#238636!important;color:#fff!important;border-color:#2EA043!important}
[data-testid="stButton"]>button[kind="primary"]:hover{background:#2EA043!important}
[data-testid="stPopover"] button{background:#1C2128!important;color:#8B949E!important;border:1px solid #30363D!important;border-radius:6px!important}
[data-testid="stPopover"] button:hover{color:#58A6FF!important;border-color:#58A6FF!important}
[data-testid="stNumberInput"] button{padding:.1rem .3rem!important;min-height:20px!important}
[data-testid="stTextInput"] input{padding:.3rem .6rem!important;font-size:.85rem!important}
[data-testid="stSelectbox"]>div>div{padding:.3rem .6rem!important;font-size:.85rem!important}
[data-testid="stNumberInput"] input{padding:.3rem .6rem!important;font-size:.85rem!important}
[data-testid="stForm"]{background:#161B22!important;border:1px solid #30363D!important;border-radius:10px!important;padding:1rem!important}
[data-testid="stTabs"] [role="tab"]{color:#8B949E!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#58A6FF!important;border-bottom:2px solid #58A6FF!important}
hr{border-color:#21262D!important}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:#0D1117}::-webkit-scrollbar-thumb{background:#30363D;border-radius:3px}
[data-testid="stButton"]>button{font-size:.82rem!important;padding:.3rem .7rem!important}
[data-testid="stPopover"] button{background:#21262D!important;color:#8B949E!important;border:1px solid #30363D!important;border-radius:6px!important;font-size:.8rem!important;padding:.2rem .5rem!important;min-width:40px!important}
[data-testid="stPopover"] button:hover{color:#58A6FF!important;border-color:#58A6FF!important}
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
.i-meta{font-size:.75rem;color:#8B949E;margin-top:2px}
.nav-lbl{font-size:.67rem;color:#6E7681;text-transform:uppercase;letter-spacing:.1em;font-weight:600;margin:1rem 0 .3rem .2rem}
.usr-box{background:#0D1117;border:1px solid #21262D;border-radius:8px;padding:.65rem 1rem;margin:.4rem 0}
.role-tag{display:inline-block;background:#238636;color:#fff;font-size:.62rem;font-weight:700;padding:1px 8px;border-radius:20px;margin-top:3px}
.flow{display:flex;align-items:center;gap:.4rem;padding:.55rem 1rem;background:#161B22;border:1px solid #21262D;border-radius:8px;margin-bottom:1rem;flex-wrap:wrap}
.fstep{font-size:.78rem;font-weight:600;padding:.25rem .7rem;border-radius:6px}
.farr{color:#30363D}
.total-bar{background:#161B22;border:1px solid #21262D;border-radius:10px;padding:.9rem 1.4rem;margin-top:1rem;text-align:right}
.sec-hdr{background:#161B22;border:1px solid #30363D;border-radius:10px;padding:.85rem 1.1rem;margin-bottom:4px}
.sec-body{background:#0D1117;border:1px solid #21262D;border-left:3px solid var(--bc,#30363D);border-radius:0 0 10px 10px;padding:1rem;margin-bottom:1rem}
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
@st.cache_data(ttl=30)
def gf(): return sb.table("pc_fornecedores").select("*").eq("ativo",True).order("nome").execute().data or []
def cf(d): sb.table("pc_fornecedores").insert(d).execute(); st.cache_data.clear()
def ef(fid,d): sb.table("pc_fornecedores").update(d).eq("id",fid).execute(); st.cache_data.clear()
def df2(fid): sb.table("pc_fornecedores").update({"ativo":False}).eq("id",fid).execute(); st.cache_data.clear()
@st.cache_data(ttl=15)
def gs(loja): return sb.table("pc_secoes").select("*").eq("loja",loja).eq("ativa",True).order("ordem").execute().data or []
def cs(loja,nome):
    ss=gs(loja); o=(max(s["ordem"] for s in ss)+1) if ss else 1
    sb.table("pc_secoes").insert({"loja":loja,"nome":nome,"ordem":o,"ativa":True}).execute(); st.cache_data.clear()
def es(sid,nome): sb.table("pc_secoes").update({"nome":nome}).eq("id",sid).execute(); st.cache_data.clear()
def as2(sid): sb.table("pc_secoes").update({"ativa":False}).eq("id",sid).execute(); st.cache_data.clear()
@st.cache_data(ttl=15)
def gi(sid,sf_key=None):
    sf=list(sf_key) if sf_key else None
    q=sb.table("pc_itens").select("*").eq("secao_id",sid)
    if sf: q=q.in_("status",sf)
    return q.order("criado_em").execute().data or []
@st.cache_data(ttl=15)
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
def pv(loja): u=st.session_state.get("usuario"); return u and u["acesso"] in ("admin","ambas",loja)
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
        st.markdown("<div style='text-align:center;padding:70px 0 24px'><div style='font-size:3rem'>🛒</div><div style='font-size:1.9rem;font-weight:800;color:#F0F6FC'>Prates</div><div style='font-size:.9rem;color:#8B949E'>Guia de Compras</div></div>",unsafe_allow_html=True)
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
    st.markdown(f"<div style='text-align:center;padding:.8rem 0 .5rem'><img src='data:image/png;base64,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' style='width:140px;filter:brightness(1.1)'><div style='font-size:.72rem;color:#8B949E;margin-top:.3rem'>Guia de Compras</div></div>",unsafe_allow_html=True)
    roles={"admin":"Admin","ambas":"Ambas","distribuidora":"Distribuidora","sublimacao":"Sublimacao"}
    st.markdown(f"<div class='usr-box'><div style='font-weight:600;color:#F0F6FC'>👤 {u['nome']}</div><div style='font-size:.72rem;color:#8B949E'>{u['email']}</div><div class='role-tag'>{roles.get(u['acesso'],'')}</div></div>",unsafe_allow_html=True)
    st.divider()
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
    st.markdown("<div class='pg-title'>📊 Dashboard</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='pg-sub'>{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>",unsafe_allow_html=True)
    todos=ga(sf_key=None)
    if not todos: st.info("Nenhum item lancado ainda."); return
    df=pd.DataFrame(todos)
    df["loja"]=df["pc_secoes"].apply(lambda x:x["loja"] if x else "")
    df["secao_nome"]=df["pc_secoes"].apply(lambda x:x["nome"] if x else "")
    df["total"]=pd.to_numeric(df.get("total",0),errors="coerce").fillna(0)
    df["qtd"]=pd.to_numeric(df.get("qtd",0),errors="coerce").fillna(0)
    c1,c2,c3,c4,c5,c6=st.columns(6)
    for col,lbl,val,cor in [(c1,"Total Geral",brl(df["total"].sum()),"#58A6FF"),(c2,"Distribuidora",brl(df[df["loja"]=="distribuidora"]["total"].sum()),"#58A6FF"),(c3,"Sublimacao",brl(df[df["loja"]=="sublimacao"]["total"].sum()),"#3FB950"),(c4,"Pendentes",str((df["status"]=="Pendente").sum()),"#D2991E"),(c5,"Aprovados",str((df["status"]=="Aprovado").sum()),"#58A6FF"),(c6,"Entregues",str((df["status"]=="Entregue").sum()),"#3FB950")]:
        col.markdown(f"<div class='kpi-box' style='--c:{cor}'><div class='kpi-l'>{lbl}</div><div class='kpi-v'>{val}</div></div>",unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    if "dt_necessidade" in df.columns:
        urg=[]
        for _,r in df.iterrows():
            if not r.get("dt_necessidade") or r.get("status") not in ST_AT: continue
            try:
                d=(date.fromisoformat(str(r["dt_necessidade"]))-date.today()).days
                if d<=3: urg.append((d,r))
            except: pass
        if urg:
            st.markdown(f"### ⚠️ {len(urg)} item(ns) urgente(s)")
            for d,r in sorted(urg):
                st.markdown(f"<div style='background:#161B22;border:1px solid #21262D;border-radius:8px;padding:.6rem 1rem;margin-bottom:.3rem'><b style='color:#F0F6FC'>{r['produto']}</b> · <span style='color:#8B949E'>{r['secao_nome']}</span> {dbd(r['dt_necessidade'])}</div>",unsafe_allow_html=True)
            st.divider()
    g1,g2=st.columns(2)
    cm={"Pendente":"#D2991E","Aprovado":"#58A6FF","Comprado":"#A371F7","Entregue":"#3FB950","Cancelado":"#F85149"}
    with g1:
        st.markdown("#### Por Status")
        s=df.groupby("status")["total"].sum().reset_index()
        fig=px.bar(s,x="status",y="total",color="status",color_discrete_map=cm,template="plotly_dark")
        fig.update_layout(showlegend=False,paper_bgcolor="#161B22",plot_bgcolor="#0D1117",margin=dict(t=10,b=10),height=240,font=dict(color="#E6EDF3"),xaxis=dict(gridcolor="#21262D"),yaxis=dict(gridcolor="#21262D"))
        st.plotly_chart(fig,use_container_width=True)
    with g2:
        st.markdown("#### Por Loja")
        l=df.groupby("loja")["total"].sum().reset_index()
        l["nome"]=l["loja"].map({"distribuidora":"Distribuidora","sublimacao":"Sublimacao"})
        fig2=px.pie(l,names="nome",values="total",color_discrete_sequence=["#58A6FF","#3FB950"],hole=.5,template="plotly_dark")
        fig2.update_layout(paper_bgcolor="#161B22",margin=dict(t=10,b=10),height=240,font=dict(color="#E6EDF3"),legend=dict(bgcolor="#161B22"))
        st.plotly_chart(fig2,use_container_width=True)
    g3,g4=st.columns(2)
    with g3:
        st.markdown("#### Top 5 Comprados")
        top=df[df["status"].isin(["Comprado","Entregue"])].groupby("produto")["qtd"].sum().sort_values(ascending=False).head(5).reset_index()
        if not top.empty:
            fig3=px.bar(top,x="qtd",y="produto",orientation="h",template="plotly_dark",color_discrete_sequence=["#58A6FF"])
            fig3.update_layout(paper_bgcolor="#161B22",plot_bgcolor="#0D1117",margin=dict(t=10,b=10),height=240,font=dict(color="#E6EDF3"),xaxis=dict(gridcolor="#21262D"),yaxis=dict(gridcolor="#21262D"))
            st.plotly_chart(fig3,use_container_width=True)
        else: st.caption("Nenhum comprado ainda.")
    with g4:
        st.markdown("#### Por Secao")
        sec=df.groupby(["secao_nome","loja"])["total"].sum().reset_index().sort_values("total",ascending=True)
        fig4=px.bar(sec,x="total",y="secao_nome",orientation="h",color="loja",color_discrete_map={"distribuidora":"#58A6FF","sublimacao":"#3FB950"},template="plotly_dark",labels={"total":"Total","secao_nome":"","loja":"Loja"})
        fig4.update_layout(paper_bgcolor="#161B22",plot_bgcolor="#0D1117",margin=dict(t=10,b=10),height=240,font=dict(color="#E6EDF3"),xaxis=dict(gridcolor="#21262D"),yaxis=dict(gridcolor="#21262D"),legend=dict(bgcolor="#161B22"))
        st.plotly_chart(fig4,use_container_width=True)

def pagina_loja(loja):
    info=LOJAS[loja]; cor=info["cor"]; fmc=fm()
    st.markdown(f"<div class='pg-title'>{info['icone']} {info['nome']}</div>",unsafe_allow_html=True)
    st.markdown("<div class='pg-sub'>Pendente/Aprovado = lista ativa · Comprado/Entregue = Historico</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='flow'><span class='fstep' style='background:rgba(210,153,34,.15);color:#D2991E'>Pendente</span><span class='farr'>→</span><span class='fstep' style='background:rgba(88,166,255,.15);color:#58A6FF'>Aprovado</span><span class='farr'>→</span><span class='fstep' style='background:rgba(163,113,247,.2);color:#A371F7'>Comprado → Historico</span><span class='farr'>→</span><span class='fstep' style='background:rgba(63,185,80,.2);color:#3FB950'>Entregue → Historico</span></div>",unsafe_allow_html=True)

    # BARRA PRINCIPAL
    ca,cb=st.columns([5,2])
    busca=ca.text_input("",placeholder="Buscar produto, marca, SKU...",label_visibility="collapsed",key=f"bsc_{loja}")
    with cb:
        btn1,btn2=st.columns(2)
        if btn1.button("Criar Produto",use_container_width=True,type="primary",key=f"bcp_{loja}"):
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
    if marcados:
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
        # Se busca ativa e nenhum item, pula a secao
        if busca and not itens: continue
        exp_key=f"exp_{sec['id']}"
        if exp_key not in st.session_state: st.session_state[exp_key]=True

        # CABECALHO DA SECAO — sem botao editar inline
        hcols=st.columns([5,1])
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
                    meta=" · ".join(filter(None,[item.get("marca",""),item.get("sku",""),item.get("ean","")]))
                    fnome=fmc.get(item.get("fornecedor_id"),"")
                    img_html='<img src="'+img+'" style="width:34px;height:34px;object-fit:cover;border-radius:6px;border:1px solid #30363D">' if img else '<div style="width:34px;height:34px;background:#21262D;border-radius:6px;display:flex;align-items:center;justify-content:center">📦</div>'
                    meta_txt=meta+(" · "+fnome if fnome else "")
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
                            cur_st=item.get("status","Pendente")
                            for sv in ST_ALL:
                                is_cur=sv==cur_st
                                lbl=f"✓ {sv}" if is_cur else sv
                                if st.button(lbl,key=f"st_{sv}_{iid}",use_container_width=True,type="primary" if is_cur else "secondary"):
                                    ui(iid,{"status":sv}); st.rerun()
                            st.divider()
                            pe,pd2=st.columns(2)
                            if pe.button("Editar",key=f"edbtn_{iid}",use_container_width=True): st.session_state[f"ed_{iid}"]=True
                            if pd2.button("Deletar",key=f"del_{iid}",use_container_width=True): di(iid); st.rerun()
                    if st.session_state.get(f"ed_{iid}"):
                        st.markdown("---")
                        forns2=gf(); fm3={f["nome"]:f["id"] for f in forns2}; fopts2=["(Nenhum)"]+list(fm3.keys())
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
                st.markdown("<div style='color:#8B949E;padding:.5rem 0'>Nenhum item nesta secao. Clique em <b>Criar Produto</b> no topo.</div>",unsafe_allow_html=True)
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
            acesso=c4.selectbox("Acesso",["distribuidora","sublimacao","ambas","admin"])
            if st.form_submit_button("Criar",type="primary"):
                if nome and email and senha: cu(nome,email,senha,acesso); st.success("Criado!"); st.rerun()
        st.markdown("#### Usuarios")
        for usu in gu():
            st.markdown(f"<div style='background:#161B22;border:1px solid #30363D;border-radius:8px;padding:.8rem 1rem;margin-bottom:.3rem'><b style='color:#F0F6FC'>{usu['nome']}</b> · {usu['email']} · <span style='color:#8B949E'>{usu['acesso']}</span> · {'✅' if usu['ativo'] else '❌'}</div>",unsafe_allow_html=True)
            with st.form(f"eu_{usu['id']}"):
                e1,e2=st.columns(2); en=e1.text_input("Nome",value=usu["nome"]); ee=e2.text_input("Email",value=usu["email"])
                e3,e4=st.columns(2); ea=e3.selectbox("Acesso",["distribuidora","sublimacao","ambas","admin"],index=["distribuidora","sublimacao","ambas","admin"].index(usu["acesso"]))
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
