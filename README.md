# 🛒 Prates — Guia de Compras

Sistema online de lançamento e gestão de compras para o Grupo Prates.  
Desenvolvido em **Python + Streamlit**, banco de dados **Supabase**.

---

## ✅ Funcionalidades

- 🔐 **Login por usuário** com controle de acesso por loja
- 📦 **Prates Distribuidora** — seções: Carregadores, Fones, Suportes, Informática, Eletrônicos
- 🎨 **Prates Sublimação** — seções: Blusas, Canecas, Mousepad, Papel/Insumos, Equipamentos
- ➕ **Criar e renomear seções** ilimitadas por loja
- 📝 **Lançar, editar e deletar itens** por seção
- 🔄 **Alterar status** do item: Pendente → Aprovado → Comprado → Entregue → Cancelado
- 📊 **Dashboard** com gráficos: totais por status, por loja, por seção, por prioridade
- 📥 **Exportar Excel** (.xlsx) com subtotais e formatação
- 📄 **Exportar PDF** pronto para impressão
- ⚙️ **Painel Admin** para gerenciar usuários e seções

---

## 🚀 Como publicar no Streamlit Cloud

### Passo 1 — Supabase

1. Acesse [supabase.com](https://supabase.com) e abra seu projeto
2. Vá em **SQL Editor**
3. Cole e execute o conteúdo de `setup_supabase.sql`
4. Anote a **URL** e a **anon key** do projeto  
   *(Settings → API → Project URL e anon public key)*

### Passo 2 — GitHub

1. Crie um novo repositório no GitHub (ex: `prates-compras`)
2. Faça upload de todos os arquivos desta pasta
3. **Importante:** NÃO envie o arquivo `.streamlit/secrets.toml`
4. Adicione ao `.gitignore`:
   ```
   .streamlit/secrets.toml
   ```

### Passo 3 — Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Clique em **New app**
3. Selecione o repositório `prates-compras`
4. Main file: `app.py`
5. Clique em **Advanced settings → Secrets** e cole:
   ```toml
   SUPABASE_URL = "https://XXXXXXXXXXXXXXXX.supabase.co"
   SUPABASE_KEY = "sua_anon_key_aqui"
   ```
6. Clique em **Deploy**

---

## 🔐 Primeiro acesso

| Campo  | Valor                |
|--------|----------------------|
| E-mail | admin@prates.com     |
| Senha  | password             |

> ⚠️ **Mude a senha do admin imediatamente após o primeiro acesso!**  
> Para isso, vá no Supabase → Table Editor → pc_usuarios → edite o registro.
> Gere o hash SHA-256 da nova senha em [sha256.online](https://emn178.github.io/online-tools/sha256.html)

---

## 👥 Níveis de acesso

| Nível          | O que pode ver/fazer                  |
|----------------|----------------------------------------|
| `admin`        | Tudo, incluindo painel de administração|
| `ambas`        | Distribuidora + Sublimação             |
| `distribuidora`| Apenas Prates Distribuidora            |
| `sublimacao`   | Apenas Prates Sublimação               |

---

## 📁 Estrutura do repositório

```
prates-compras/
├── app.py                  ← aplicação principal
├── requirements.txt        ← dependências Python
├── setup_supabase.sql      ← script de criação das tabelas
└── .streamlit/
    └── secrets.toml        ← suas credenciais (NÃO publicar no GitHub)
```

---

## 🔄 Como atualizar o sistema

Mesmo fluxo dos outros sistemas Prates:

```
1. Edite o app.py localmente
2. git add .
3. git commit -m "descrição da mudança"
4. git push
5. Streamlit Cloud atualiza automaticamente
```
