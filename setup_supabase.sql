-- ============================================================
-- PRATES — GUIA DE COMPRAS  |  Script de Setup no Supabase
-- Execute este SQL no SQL Editor do seu projeto Supabase
-- ============================================================

-- 1. USUÁRIOS
CREATE TABLE IF NOT EXISTS pc_usuarios (
    id          BIGSERIAL PRIMARY KEY,
    nome        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    senha_hash  TEXT NOT NULL,
    acesso      TEXT NOT NULL DEFAULT 'ambas',
        -- valores: 'distribuidora' | 'sublimacao' | 'ambas' | 'admin'
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

-- 3. ITENS
CREATE TABLE IF NOT EXISTS pc_itens (
    id              BIGSERIAL PRIMARY KEY,
    secao_id        BIGINT REFERENCES pc_secoes(id) ON DELETE CASCADE,
    produto         TEXT NOT NULL,
    fornecedor      TEXT,
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
-- ATENÇÃO: troque a senha depois do primeiro acesso!
-- Senha padrão: prates2025
INSERT INTO pc_usuarios (nome, email, senha_hash, acesso) VALUES
    ('Administrador', 'admin@prates.com',
     '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
     -- SHA-256 de "password" — MUDE IMEDIATAMENTE
     'admin');

-- ============================================================
-- RLS (Row Level Security) — deixe desabilitado por ora
-- ou configure de acordo com suas necessidades de segurança
-- ============================================================
-- ALTER TABLE pc_usuarios ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE pc_secoes   ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE pc_itens    ENABLE ROW LEVEL SECURITY;
