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
[data-testid="stButton"]>button{background:#21262D!important;color:#E6EDF3!important;border:1px solid #30363D!important;border-radius:8px!important;font-weight:500!important}
[data-testid="stButton"]>button:hover{background:#30363D!important;border-color:#58A6FF!important;color:#58A6FF!important}
[data-testid="stButton"]>button[kind="primary"]{background:#238636!important;color:#fff!important;border-color:#2EA043!important}
[data-testid="stButton"]>button[kind="primary"]:hover{background:#2EA043!important}
[data-testid="stForm"]{background:#161B22!important;border:1px solid #30363D!important;border-radius:10px!important;padding:1rem!important}
[data-testid="stTabs"] [role="tab"]{color:#8B949E!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#58A6FF!important;border-bottom:2px solid #58A6FF!important}
hr{border-color:#21262D!important}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:#0D1117}::-webkit-scrollbar-thumb{background:#30363D;border-radius:3px}
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
.sec-header{background:#161B22;border:1px solid #30363D;border-radius:10px;padding:.9rem 1.2rem;margin-bottom:4px;display:flex;align-items:center;justify-content:space-between;cursor:pointer}
.sec-title{font-size:1rem;font-weight:700;color:#F0F6FC}
.sec-meta{font-size:.8rem;color:#8B949E}
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
def gf(): return sb.table("pc_fornecedores").select("*").eq("ativo",True).order("nome").execute().data or []
def cf(d): sb.table("pc_fornecedores").insert(d).execute()
def ef(fid,d): sb.table("pc_fornecedores").update(d).eq("id",fid).execute()
def df2(fid): sb.table("pc_fornecedores").update({"ativo":False}).eq("id",fid).execute()
def gs(loja): return sb.table("pc_secoes").select("*").eq("loja",loja).eq("ativa",True).order("ordem").execute().data or []
def cs(loja,nome):
    ss=gs(loja); o=(max(s["ordem"] for s in ss)+1) if ss else 1
    sb.table("pc_secoes").insert({"loja":loja,"nome":nome,"ordem":o,"ativa":True}).execute()
def es(sid,nome): sb.table("pc_secoes").update({"nome":nome}).eq("id",sid).execute()
def as2(sid): sb.table("pc_secoes").update({"ativa":False}).eq("id",sid).execute()
def gi(sid,sf=None):
    q=sb.table("pc_itens").select("*").eq("secao_id",sid)
    if sf: q=q.in_("status",sf)
    return q.order("criado_em").execute().data or []
def ga(sf=None):
    q=sb.table("pc_itens").select("*, pc_secoes(nome,loja)")
    if sf: q=q.in_("status",sf)
    return q.execute().data or []
def ai(sid,d,user):
    d.update({"secao_id":sid,"criado_por":user,"criado_em":datetime.now().isoformat(),"atualizado_em":datetime.now().isoformat()})
    sb.table("pc_itens").insert(d).execute()
def ui(iid,d): d["atualizado_em"]=datetime.now().isoformat(); sb.table("pc_itens").update(d).eq("id",iid).execute()
def di(iid): sb.table("pc_itens").delete().eq("id",iid).execute()
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
    st.markdown("<div style='text-align:center;padding:1.2rem 0 .8rem'><div style='font-size:2.2rem'>🛒</div><div style='font-size:1rem;font-weight:700;color:#F0F6FC'>Guia de Compras</div><div style='font-size:.72rem;color:#8B949E'>Grupo Prates</div></div>",unsafe_allow_html=True)
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
    todos=ga()
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

def form_item(key,item=None):
    forns=gf(); fm2={f["nome"]:f["id"] for f in forns}; fopts=["(Nenhum)"]+list(fm2.keys())
    fatual="(Nenhum)"
    if item and item.get("fornecedor_id"):
        for f in forns:
            if f["id"]==item["fornecedor_id"]: fatual=f["nome"]; break
    with st.form(key):
        st.markdown("**Dados do Produto**")
        c1,c2,c3=st.columns(3)
        prod=c1.text_input("Produto *",value=item.get("produto","") if item else "")
        marca=c2.text_input("Marca",value=item.get("marca","") if item else "")
        sku=c3.text_input("SKU",value=item.get("sku","") if item else "")
        c4,c5,c6=st.columns(3)
        ean=c4.text_input("EAN",value=item.get("ean","") if item else "")
        forn=c5.selectbox("Fornecedor",fopts,index=fopts.index(fatual) if fatual in fopts else 0)
        img=c6.text_input("URL Imagem",value=item.get("imagem_url","") if item else "")
        st.markdown("**Quantidade e Preco**")
        q1,q2,q3,q4,q5=st.columns(5)
        qtd=q1.number_input("Qtd *",min_value=0.0,value=float(item.get("qtd",0) if item else 0),step=1.0)
        un=q2.selectbox("Unidade",UNID,index=UNID.index(item.get("unidade","UN")) if item and item.get("unidade","UN") in UNID else 0)
        preco=q3.number_input("Preco Unit.",min_value=0.0,value=float(item.get("preco_unit",0) if item else 0),step=0.01,format="%.2f")
        prio=q4.selectbox("Prioridade",PRIO,index=PRIO.index(item.get("prioridade","Media")) if item and item.get("prioridade") in PRIO else 1)
        dt=q5.date_input("Dt Necessidade",value=None)
        obs=st.text_area("Observacoes",value=item.get("obs","") if item else "",height=60)
        if st.form_submit_button("Salvar" if item else "Adicionar",type="primary"):
            if not prod.strip(): st.warning("Informe o produto."); return None
            return {"produto":prod.strip(),"marca":marca.strip(),"sku":sku.strip(),"ean":ean.strip(),"fornecedor_id":fm2.get(forn) if forn!="(Nenhum)" else None,"imagem_url":img.strip() or None,"qtd":qtd,"unidade":un,"preco_unit":preco,"total":round(qtd*preco,2),"prioridade":prio,"dt_necessidade":str(dt) if dt else None,"obs":obs.strip(),"status":item.get("status","Pendente") if item else "Pendente"}
    return None

def pagina_loja(loja):
    info=LOJAS[loja]; cor=info["cor"]; fmc=fm()
    st.markdown(f"<div class='pg-title'>{info['icone']} {info['nome']}</div>",unsafe_allow_html=True)
    st.markdown("<div class='pg-sub'>Lista ativa (Pendente/Aprovado). Comprado e Entregue vao para o Historico.</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='flow'><span class='fstep' style='background:rgba(210,153,34,.15);color:#D2991E'>Pendente</span><span class='farr'>→</span><span class='fstep' style='background:rgba(88,166,255,.15);color:#58A6FF'>Aprovado</span><span class='farr'>→</span><span class='fstep' style='background:rgba(163,113,247,.2);color:#A371F7'>Comprado → Historico</span><span class='farr'>→</span><span class='fstep' style='background:rgba(63,185,80,.2);color:#3FB950'>Entregue → Historico</span></div>",unsafe_allow_html=True)

    ca,cb,cc,cd=st.columns([3,1,1,1])
    busca=ca.text_input("",placeholder="Buscar produto, marca, SKU...",label_visibility="collapsed",key=f"bsc_{loja}")
    fst=cb.selectbox("",["Todos"]+ST_AT,key=f"fst_{loja}",label_visibility="collapsed")
    fpr=cc.selectbox("",["Todas"]+PRIO,key=f"fpr_{loja}",label_visibility="collapsed")
    if cd.button("+ Nova Secao",use_container_width=True,key=f"bns_{loja}"): st.session_state[f"ns_{loja}"]=True

    if st.session_state.get(f"ns_{loja}"):
        with st.form(f"fns_{loja}"):
            st.markdown("**Nova Secao**"); nomes=st.text_input("Nome da nova secao")
            x1,x2=st.columns(2)
            if x1.form_submit_button("Criar",type="primary"):
                if nomes.strip(): cs(loja,nomes.strip()); st.session_state[f"ns_{loja}"]=False; st.rerun()
            if x2.form_submit_button("Cancelar"): st.session_state[f"ns_{loja}"]=False; st.rerun()

    sel_key=f"sel_{loja}"
    if sel_key not in st.session_state: st.session_state[sel_key]=[]
    marcados=st.session_state[sel_key]
    if marcados:
        st.markdown(f"<div style='background:#1C2128;border:1px solid #30363D;border-radius:8px;padding:.7rem 1rem;margin-bottom:.8rem'><b style='color:#58A6FF'>{len(marcados)} item(ns) selecionado(s)</b></div>",unsafe_allow_html=True)
        la,lb,lc,ld,le=st.columns(5)
        for col,lbl,sv,tp in [(la,"Aprovar","Aprovado","primary"),(lb,"Comprado","Comprado","secondary"),(lc,"Entregue","Entregue","secondary"),(ld,"Cancelar","Cancelado","secondary")]:
            if col.button(lbl,key=f"lote_{sv}_{loja}",use_container_width=True,type=tp): ls(marcados,sv); st.session_state[sel_key]=[]; st.rerun()
        if le.button("Limpar",key=f"clr_{loja}",use_container_width=True): st.session_state[sel_key]=[]; st.rerun()

    secoes=gs(loja)
    if not secoes:
        st.markdown("<div style='text-align:center;padding:3rem;background:#161B22;border:1px dashed #30363D;border-radius:12px;color:#8B949E'>Nenhuma secao. Clique em <b>+ Nova Secao</b>.</div>",unsafe_allow_html=True); return

    total_loja=0
    for sec in secoes:
        itens_all=gi(sec["id"],sf=ST_AT)
        itens=itens_all[:]
        if fst!="Todos": itens=[i for i in itens if i.get("status")==fst]
        if fpr!="Todas": itens=[i for i in itens if i.get("prioridade")==fpr]
        if busca:
            b=busca.lower(); itens=[i for i in itens if b in " ".join([i.get("produto",""),i.get("marca",""),i.get("sku",""),i.get("ean","")]).lower()]
        tsec=sum(float(i.get("total") or 0) for i in itens_all); total_loja+=tsec
        npend=sum(1 for i in itens_all if i.get("status")=="Pendente")
        exp_key=f"exp_{sec['id']}"
        if exp_key not in st.session_state: st.session_state[exp_key]=True

        # CABECALHO DA SECAO — sem st.expander
        hcols=st.columns([6,1])
        with hcols[0]:
            st.markdown(f"""<div class='sec-header'>
                <div>
                    <span class='sec-title'>{'▼' if st.session_state[exp_key] else '▶'} {sec['nome']}</span>
                    <span class='sec-meta'> &nbsp;·&nbsp; {len(itens_all)} itens &nbsp;·&nbsp; {brl(tsec)}{' &nbsp;·&nbsp; <span style="color:#D2991E">'+str(npend)+' pendentes</span>' if npend else ''}</span>
                </div>
            </div>""",unsafe_allow_html=True)
        with hcols[1]:
            lbl="Fechar" if st.session_state[exp_key] else "Abrir"
            if st.button(lbl,key=f"tog_{sec['id']}",use_container_width=True):
                st.session_state[exp_key]=not st.session_state[exp_key]; st.rerun()

        if st.session_state[exp_key]:
            with st.container():
                st.markdown("<div class='sec-body'>",unsafe_allow_html=True)

                # Editar/arquivar secao
                sc1,sc2,sc3=st.columns([4,1.5,1])
                nn=sc1.text_input("",value=sec["nome"],key=f"rn_{sec['id']}",label_visibility="collapsed",placeholder="Renomear secao...")
                if sc2.button("Salvar nome",key=f"svn_{sec['id']}",use_container_width=True):
                    if nn.strip() and nn!=sec["nome"]: es(sec["id"],nn.strip()); st.rerun()
                if sc3.button("Arquivar",key=f"arc_{sec['id']}",use_container_width=True): as2(sec["id"]); st.rerun()

                st.markdown("<hr style='margin:.6rem 0'>",unsafe_allow_html=True)

                if itens:
                    for item in itens:
                        iid=item["id"]; sl=st.session_state.get(sel_key,[])
                        c0,c1,c2,c3,c4,c5,c6,c7,c8=st.columns([.4,3.5,1.5,.8,.8,1.5,1.2,1.2,.8])
                        sel=c0.checkbox("",value=iid in sl,key=f"chk_{iid}",label_visibility="collapsed")
                        if sel and iid not in sl: st.session_state.setdefault(sel_key,[]).append(iid)
                        elif not sel and iid in sl: st.session_state[sel_key].remove(iid)
                        img=item.get("imagem_url",""); meta=" · ".join(filter(None,[item.get("marca",""),item.get("sku",""),item.get("ean","")])); fnome=fmc.get(item.get("fornecedor_id"),"")
                        c1.markdown(f"<div style='display:flex;align-items:center;gap:.6rem'>{'<img src=\"'+img+'\" style=\"width:34px;height:34px;object-fit:cover;border-radius:6px;border:1px solid #30363D\">' if img else '<div style=\"width:34px;height:34px;background:#21262D;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:.8rem\">📦</div>'}<div><div class=\"i-nome\">{item.get(\"produto\",\"\")}</div><div class=\"i-meta\">{meta}{\" · \"+fnome if fnome else \"\"}</div></div></div>",unsafe_allow_html=True)
                        c2.markdown(f"<div style='font-size:.78rem;color:#8B949E;padding-top:.3rem'>{sec['nome']}</div>",unsafe_allow_html=True)
                        c3.markdown(f"<div style='text-align:center;padding-top:.3rem'>{item.get('qtd','')} {item.get('unidade','')}</div>",unsafe_allow_html=True)
                        c4.markdown(f"<div style='text-align:right;font-size:.8rem;color:#8B949E;padding-top:.3rem'>{brl(item.get('preco_unit',0))}</div>",unsafe_allow_html=True)
                        c5.markdown(f"<div style='text-align:right;font-weight:700;color:{cor};padding-top:.3rem'>{brl(item.get('total',0))}</div>",unsafe_allow_html=True)
                        c6.markdown(bdg(item.get("status",""))+" "+dbd(item.get("dt_necessidade")),unsafe_allow_html=True)
                        c7.markdown(bdg(item.get("prioridade","")),unsafe_allow_html=True)
                        with c8:
                            with st.popover("opcoes"):
                                st.markdown(f"**{item.get('produto','')}**")
                                if img: st.image(img,width=100)
                                nst=st.selectbox("Status",ST_ALL,index=ST_ALL.index(item.get("status","Pendente")),key=f"pst_{iid}")
                                if st.button("Salvar status",key=f"svst_{iid}",type="primary"): ui(iid,{"status":nst}); st.rerun()
                                st.divider()
                                if st.button("Editar",key=f"edbtn_{iid}"): st.session_state[f"ed_{iid}"]=True
                                if st.button("Deletar",key=f"del_{iid}"): di(iid); st.rerun()
                        if st.session_state.get(f"ed_{iid}"):
                            st.markdown("---"); r=form_item(f"fedit_{iid}",item=item)
                            if r is not None: ui(iid,r); st.session_state[f"ed_{iid}"]=False; st.rerun()
                            if st.button("Cancelar",key=f"ced_{iid}"): st.session_state[f"ed_{iid}"]=False; st.rerun()
                else:
                    st.markdown("<div style='color:#8B949E;padding:.5rem 0'>Nenhum item nesta secao.</div>",unsafe_allow_html=True)

                st.markdown("<hr style='margin:.6rem 0'>",unsafe_allow_html=True)
                st.markdown("**Adicionar item nesta secao**")
                r=form_item(f"fadd_{sec['id']}")
                if r is not None: ai(sec["id"],r,u["nome"]); st.rerun()
                st.markdown("</div>",unsafe_allow_html=True)

    st.markdown(f"<div class='total-bar'><span style='color:#8B949E'>{info['nome']} — Total em aberto:</span> <span style='color:{cor};font-size:1.2rem;font-weight:700;margin-left:.8rem'>{brl(total_loja)}</span></div>",unsafe_allow_html=True)

def pagina_historico():
    st.markdown("<div class='pg-title'>📅 Historico</div>",unsafe_allow_html=True)
    st.markdown("<div class='pg-sub'>Itens Comprado, Entregue ou Cancelado</div>",unsafe_allow_html=True)
    todos=ga(sf=ST_HI)
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
            st.markdown(f"<div style='background:#161B22;border:1px solid #30363D;border-radius:10px;padding:1rem;margin-bottom:.6rem'>",unsafe_allow_html=True)
            st.markdown(f"**{forn['nome']}**" + (f" · {forn.get('telefone','')}" if forn.get("telefone") else "") + (f" · CNPJ: {forn.get('cnpj','')}" if forn.get("cnpj") else ""))
            with st.form(f"ef_{forn['id']}"):
                e1,e2=st.columns(2); en=e1.text_input("Nome",value=forn.get("nome","")); ec=e2.text_input("Contato",value=forn.get("contato",""))
                e3,e4,e5=st.columns(3); et=e3.text_input("Telefone",value=forn.get("telefone","")); ee=e4.text_input("Email",value=forn.get("email","")); ecnpj=e5.text_input("CNPJ",value=forn.get("cnpj",""))
                eo=st.text_area("Obs",value=forn.get("observacoes",""),height=60)
                s1,_,s3=st.columns(3)
                if s1.form_submit_button("Salvar",type="primary"): ef(forn["id"],{"nome":en,"contato":ec,"telefone":et,"email":ee,"cnpj":ecnpj,"observacoes":eo}); st.success("Salvo!"); st.rerun()
                if s3.form_submit_button("Remover"): df2(forn["id"]); st.rerun()
            st.markdown("</div>",unsafe_allow_html=True)

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
                    for ri,item in enumerate(gi(sec["id"],sf=sf)):
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
            st.markdown(f"<div style='background:#161B22;border:1px solid #30363D;border-radius:8px;padding:.8rem 1rem;margin-bottom:.5rem'><b style='color:#F0F6FC'>{usu['nome']}</b> · {usu['email']} · <span style='color:#8B949E'>{usu['acesso']}</span> · {'✅ Ativo' if usu['ativo'] else '❌ Inativo'}</div>",unsafe_allow_html=True)
            with st.form(f"eu_{usu['id']}"):
                e1,e2=st.columns(2); en=e1.text_input("Nome",value=usu["nome"]); ee=e2.text_input("Email",value=usu["email"])
                e3,e4=st.columns(2); ea=e3.selectbox("Acesso",["distribuidora","sublimacao","ambas","admin"],index=["distribuidora","sublimacao","ambas","admin"].index(usu["acesso"]))
                ep=e4.text_input("Nova Senha (em branco = manter)",type="password")
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
