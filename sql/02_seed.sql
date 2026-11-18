-- Capítulo 2 · Passo 2.4: dados FICTÍCIOS para o projeto de portfólio
-- Idempotente: ON CONFLICT DO NOTHING faz o script poder rodar várias vezes
-- sem duplicar nada (a chave única das tabelas é quem barra a repetição).
--
-- Os CPFs abaixo foram gerados pela regra dos dígitos verificadores, só para
-- teste. Não pertencem a pessoas reais de propósito (pode haver coincidência
-- por acaso, como em qualquer número válido). Nomes também são inventados.

-- Pessoas bloqueadas pela empresa.
INSERT INTO blocklist (cpf, motivo, bloqueado_em) VALUES
    ('52998224725', 'Mau comportamento', '2024-03-12'),
    ('11144477735', 'Fraude em documentos', '2025-01-20'),
    ('12345678909', 'Acordo interno de não recontratação', '2025-08-04')
ON CONFLICT (cpf) DO NOTHING;

-- Histórico de funcionários (data_desligamento NULL = ainda trabalha).
-- 12345678909: passagem curta (43 dias) E está na blocklist (testa a precedência)
-- 24681357928: saiu com 74 dias de casa
-- 13579246828: saiu com exatamente 90 dias (limite da regra)
-- 31415926590: saiu com 91 dias (um dia acima do limite)
-- 27182818205: ex-funcionário com muito tempo de casa
-- 16180339805: funcionária ativa, admitida recentemente (não é ex-funcionária)
-- 98765432100: duas passagens, uma de 60 dias e outra longa (recontratação)
INSERT INTO funcionarios (cpf, nome, data_admissao, data_desligamento) VALUES
    ('12345678909', 'Marcos Teixeira', '2025-06-02', '2025-07-15'),
    ('24681357928', 'Juliana Prado', '2026-01-05', '2026-03-20'),
    ('13579246828', 'Rafael Nogueira', '2026-02-01', '2026-05-02'),
    ('31415926590', 'Beatriz Lacerda', '2026-02-01', '2026-05-03'),
    ('27182818205', 'Eduardo Farias', '2019-03-01', '2024-08-30'),
    ('16180339805', 'Patrícia Vieira', '2026-09-01', NULL),
    ('98765432100', 'Fernando Rocha', '2020-02-03', '2020-04-03'),
    ('98765432100', 'Fernando Rocha', '2021-05-10', '2025-11-28')
ON CONFLICT (cpf, data_admissao) DO NOTHING;