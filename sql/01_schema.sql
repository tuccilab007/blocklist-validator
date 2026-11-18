-- Capítulo 2 · Passo 2.3: tabelas do validador de blocklist
-- Idempotente: pode rodar várias vezes sem erro (CREATE TABLE IF NOT EXISTS).
--
-- CPF é guardado como TEXTO de 11 dígitos, sem pontos e sem traço.
-- Nunca como número: um CPF que começa com zero perderia o zero.

-- CPFs que a empresa bloqueou (ex.: mau comportamento).
CREATE TABLE IF NOT EXISTS blocklist (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cpf           TEXT NOT NULL UNIQUE CHECK (cpf ~ '^[0-9]{11}$'),
    motivo        TEXT NOT NULL,
    bloqueado_em  DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Histórico de funcionários. data_desligamento vazia = ainda trabalha na empresa.
-- A mesma pessoa pode ter mais de uma passagem (recontratação), por isso a
-- chave única é CPF + data de admissão, e não só o CPF.
CREATE TABLE IF NOT EXISTS funcionarios (
    id                 INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cpf                TEXT NOT NULL CHECK (cpf ~ '^[0-9]{11}$'),
    nome               TEXT NOT NULL,
    data_admissao      DATE NOT NULL,
    data_desligamento  DATE,
    CHECK (data_desligamento IS NULL OR data_desligamento >= data_admissao),
    UNIQUE (cpf, data_admissao)
);