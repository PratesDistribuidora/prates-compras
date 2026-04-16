-- ============================================================
-- PRATES — GUIA DE COMPRAS  |  Script de Setup no Supabase
-- Execute este SQL no SQL Editor do seu projeto Supabase
-- ============================================================

-- 1. USUÁRIOS
-- Níveis de acesso válidos:
--   'admin'      → tudo, incluindo painel de administração
--   'ambas'      → Gestor: Distribuidora + Sublimação
--   'distribuidora' → Gestor: apenas Distribuidora
--   'sublimacao' → Gestor: apenas Sublimação
--   'op_ambas'   → Operador: Distribuidora + Sublimação (sem editar/excluir)
--   'op_dist'    → Operador: apenas Distribuidora (sem editar/excluir)
--   'op_sub'     → Operador: apenas Sublimação (sem editar/excluir)
CREATE TABLE IF NOT EXISTS pc_usuarios (
    id          BIGSERIAL PRIMARY KEY,
    nome        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    senha_hash  TEXT NOT NULL,
    acesso      TEXT NOT NULL DEFAULT 'ambas',
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ DEFAULT NOW()
);

-- 2. SEÇÕES (por loja)
CREATE TABLE IF NOT EXISTS pc_secoes (
    id      BIGSERIAL PRIMARY KEY,
    loja    TEXT NOT NULL,   -- 'distribuidora' | 'sublimacao'
    nome    TEXT NOT NULL,
    ordem   INTEGER NOT NULL DEFAULT 1,
    ativa   BOOLEAN NOT NULL DEFAULT TRUE
);

-- 3. FORNECEDORES
CREATE TABLE IF NOT EXISTS pc_fornecedores (
    id           BIGSERIAL PRIMARY KEY,
    nome         TEXT NOT NULL,
    contato      TEXT,
    telefone     TEXT,
    email        TEXT,
    cnpj         TEXT,
    observacoes  TEXT,
    ativo        BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em    TIMESTAMPTZ DEFAULT NOW()
);

-- 4. ITENS
CREATE TABLE IF NOT EXISTS pc_itens (
    id              BIGSERIAL PRIMARY KEY,
    secao_id        BIGINT REFERENCES pc_secoes(id) ON DELETE CASCADE,
    produto         TEXT NOT NULL,
    marca           TEXT,
    sku             TEXT,
    ean             TEXT,
    fornecedor_id   BIGINT REFERENCES pc_fornecedores(id) ON DELETE SET NULL,
    imagem_url      TEXT,
    qtd             NUMERIC(10,2) DEFAULT 0,
    unidade         TEXT DEFAULT 'UN',
    preco_unit      NUMERIC(12,2) DEFAULT 0,
    total           NUMERIC(14,2) DEFAULT 0,
    prioridade      TEXT DEFAULT 'Média',   -- 'Alta' | 'Média' | 'Baixa'
    status          TEXT DEFAULT 'Pendente',
        -- 'Pendente' | 'Aprovado' | 'Comprado' | 'Entregue' | 'Cancelado'
    dt_necessidade  DATE,
    obs             TEXT,
    criado_por      TEXT,
    criado_em       TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em   TIMESTAMPTZ DEFAULT NOW()
);

-- 5. AUDITORIA
CREATE TABLE IF NOT EXISTS pc_auditoria (
    id          BIGSERIAL PRIMARY KEY,
    usuario     TEXT,
    acao        TEXT NOT NULL,
    tabela      TEXT,
    registro_id BIGINT,
    detalhes    TEXT,
    ip          TEXT,
    criado_em   TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- MIGRAÇÃO: normalizar prioridade (rodar apenas se necessário)
-- Se você já tinha dados com "Media" sem acento, execute:
-- UPDATE pc_itens SET prioridade = 'Média' WHERE prioridade = 'Media';
-- ============================================================

-- ============================================================
-- DADOS INICIAIS
-- ============================================================

-- Seções da Prates Distribuidora
INSERT INTO pc_secoes (loja, nome, ordem) VALUES
    ('distribuidora', 'Carregadores e Cabos',  1),
    ('distribuidora', 'Fones e Áudio',          2),
    ('distribuidora', 'Suportes e Veicular',    3),
    ('distribuidora', 'Informática',            4),
    ('distribuidora', 'Eletrônicos Gerais',     5);

-- Seções da Prates Sublimação
INSERT INTO pc_secoes (loja, nome, ordem) VALUES
    ('sublimacao', 'Camisetas / Blusas',  1),
    ('sublimacao', 'Canecas e Cerâmica',  2),
    ('sublimacao', 'Mousepad / Squeeze',  3),
    ('sublimacao', 'Papel e Insumos',     4),
    ('sublimacao', 'Equipamentos',        5);

-- Usuário administrador inicial
-- ATENÇÃO: troque a senha após o primeiro acesso pelo próprio painel Admin!
-- Senha padrão: prates2025
-- Hash bcrypt gerado pelo app — troque via painel Admin assim que logar.
-- Para gerar um novo hash bcrypt: python -c "import bcrypt; print(bcrypt.hashpw(b'prates2025', bcrypt.gensalt()).decode())"
INSERT INTO pc_usuarios (nome, email, senha_hash, acesso) VALUES
    ('Administrador', 'admin@prates.com',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlJbekEUdzp7WCNmkp/r/sNbK',
     -- bcrypt de "prates2025" — MUDE IMEDIATAMENTE via painel Admin
     'admin');

-- ============================================================
-- RLS (Row Level Security)
-- A anon key do Supabase dá acesso direto às tabelas via API.
-- Habilitar RLS + policy abaixo bloqueia acesso sem token válido.
-- O app acessa via service_role key (secrets), por isso continua funcionando.
-- ============================================================
ALTER TABLE pc_usuarios    ENABLE ROW LEVEL SECURITY;
ALTER TABLE pc_secoes      ENABLE ROW LEVEL SECURITY;
ALTER TABLE pc_itens       ENABLE ROW LEVEL SECURITY;
ALTER TABLE pc_fornecedores ENABLE ROW LEVEL SECURITY;
ALTER TABLE pc_auditoria   ENABLE ROW LEVEL SECURITY;

-- Nega acesso via anon key (acesso só via service_role ou authenticated)
CREATE POLICY "Sem acesso anônimo" ON pc_usuarios    FOR ALL TO anon USING (false);
CREATE POLICY "Sem acesso anônimo" ON pc_secoes      FOR ALL TO anon USING (false);
CREATE POLICY "Sem acesso anônimo" ON pc_itens       FOR ALL TO anon USING (false);
CREATE POLICY "Sem acesso anônimo" ON pc_fornecedores FOR ALL TO anon USING (false);
CREATE POLICY "Sem acesso anônimo" ON pc_auditoria   FOR ALL TO anon USING (false);
