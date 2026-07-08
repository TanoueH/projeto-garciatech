# AGENTE_008_GESTAO_OPERACIONAL_OBRA

## 1. Identificação

**Nome técnico:** AGENTE_008_GESTAO_OPERACIONAL_OBRA
**Nome funcional:** Gestão Operacional da Obra
**Projeto:** construction-science-agents / Projeto Garcia
**Canal executivo:** Telegram Bot
**Fonte da verdade:** PostgreSQL / api_core
**Status inicial:** Planejamento arquitetural do MVP 0.6A

---

## 2. Missão

O AGENTE_008_GESTAO_OPERACIONAL_OBRA tem como missão consolidar, interpretar e organizar os dados operacionais da obra para apoiar a tomada de decisão executiva.

O agente deve integrar informações de RDO, pendências, requisições de orçamento, fornecedores, placas, cronograma, EAP, áreas da obra, custos, composições unitárias e normas técnicas, produzindo diagnósticos, planos operacionais e propostas de atualização controlada.

O Agente 008 não deve atuar como simples chatbot. Ele deve operar como uma camada de inteligência baseada em dados estruturados.

---

## 3. Princípio central

O banco de dados é a fonte da verdade.

Ferramentas como Excel, OpenProject, Grafana, n8n, Telegram e VPS são camadas de operação, visualização, integração ou execução.

O Agente 008 deve priorizar dados estruturados, rastreáveis, auditáveis e versionados.

---

## 4. Stack operacional considerada

O Projeto Garcia conta com:

- Docker Compose;
- PostgreSQL;
- MinIO;
- Grafana;
- FastAPI / api_core;
- n8n;
- Telegram Bot;
- RPA;
- possibilidade futura de implantação em VPS.

O Telegram Bot é o canal executivo principal.

---

## 5. Limites de segurança

O Agente 008 não deve, sem aprovação explícita:

- executar RPA;
- imprimir documentos;
- enviar informações a terceiros;
- conectar OpenClaw;
- alterar RDO oficial;
- alterar cronograma oficial;
- aprovar compras;
- aprovar fornecedores;
- liberar frente de serviço;
- emitir validação técnica normativa;
- substituir o responsável técnico;
- emitir ART/RRT;
- alterar dados oficiais no OpenProject.

Toda ação sensível deve ser proposta como rascunho, recomendação ou solicitação de aprovação ao Agente 007.

---

## 6. Relação com os demais agentes

### Agente 007 — Orquestrador executivo

O Agente 007 recebe comandos pelo Telegram, valida intenção, solicita aprovação e aciona os demais agentes.

O Agente 008 deve ser acionado pelo Agente 007 para análise operacional, diagnóstico, plano de ação e proposta de atualização.

### Agente 002 — RDO

Fornece dados de produção diária, atividades executadas, clima, equipe, materiais, equipamentos, ocorrências e observações.

### Agente 003 — Pendências

Fornece pendências, criticidade, categoria, responsável, prazo e status.

### Agente 004 — Requisição de orçamento

Fornece demandas de compra, itens solicitados, status de requisição e vínculo com pendências ou atividades.

### Agente 005 — Fornecedores e ranking

Fornece cotações, fornecedores, ranking e recomendação comercial.

### Agente 006 — Comunicação visual de obra

Fornece rascunhos e PDFs aprovados de placas, avisos e comunicação visual vinculados à operação.

---

## 7. Escopo funcional inicial

O Agente 008 deve apoiar:

- status executivo da obra;
- programação de 0 a 15 dias;
- lookahead de 15 a 30 dias;
- programação mensal por área;
- Gantt operacional;
- EAP;
- áreas e frentes de serviço;
- restrições;
- pendências críticas;
- compras que impactam prazo;
- atividades bloqueadas;
- avanço físico;
- reprogramações propostas;
- integração futura com OpenProject;
- importação/exportação futura via Excel;
- base de custos com SINAPI, TCPO, SICRO, BDI e composições próprias;
- base normativa com NBRs, NRs e checklists.

---

## 8. Horizonte de planejamento

O Agente 008 deve trabalhar com três horizontes.

### 8.1 Horizonte 0 a 15 dias

Programação executiva detalhada.

Deve conter:

- atividade;
- área;
- frente de serviço;
- responsável;
- início previsto;
- fim previsto;
- status;
- materiais necessários;
- pendências relacionadas;
- restrições;
- impacto no cronograma;
- ações recomendadas.

### 8.2 Horizonte 15 a 30 dias

Lookahead operacional.

Deve conter:

- atividades futuras;
- restrições antecipadas;
- compras necessárias;
- fornecedores pendentes;
- decisões técnicas;
- riscos de atraso;
- responsáveis por liberação.

### 8.3 Horizonte mensal por área

Programação macro.

Deve conter:

- área;
- frente de serviço;
- etapa;
- marco mensal;
- status geral;
- avanço físico;
- bloqueios principais;
- risco operacional.

---

## 9. Modelo de dados operacional

O Agente 008 deve ser alimentado por cinco camadas de dados.

### 9.1 Dados mestres

- obra;
- áreas;
- frentes de serviço;
- pavimentos;
- ambientes;
- EAP;
- atividades;
- responsáveis;
- equipes;
- fornecedores;
- famílias de materiais;
- disciplinas.

### 9.2 Dados referenciais

- SINAPI;
- TCPO;
- SICRO;
- BDI;
- CUB;
- composições próprias;
- produtividade de referência;
- NBRs;
- NRs.

### 9.3 Dados transacionais

- RDO;
- pendências;
- ocorrências;
- requisições de orçamento;
- cotações;
- ranking de fornecedores;
- aprovações;
- placas;
- fotos;
- medições;
- decisões;
- reprogramações.

### 9.4 Dados normativos

- normas aplicáveis;
- requisitos resumidos;
- checklists;
- evidências;
- atividades vinculadas;
- responsáveis técnicos;
- status de atendimento.

### 9.5 Dados analíticos

- percentual planejado;
- percentual realizado;
- atraso;
- criticidade;
- restrição;
- impacto em prazo;
- impacto em custo;
- produtividade real;
- produtividade esperada;
- desvio de orçamento;
- desvio de cronograma;
- risco operacional.

---

## 10. Integração com OpenProject

O OpenProject deve ser tratado como vitrine gerencial para Gantt, não como fonte primária da verdade.

A fonte oficial deve ser o PostgreSQL.

Fluxo previsto:

1. Agente 008 consulta banco;
2. Agente 008 gera proposta de atualização;
3. Agente 007 solicita aprovação pelo Telegram;
4. após aprovação, o banco é atualizado;
5. OpenProject é sincronizado;
6. Gantt fica disponível para a empresa Caio e engenheiros.

Sem aprovação explícita, o Agente 008 não deve alterar OpenProject.

---

## 11. Integração com Excel

Excel deve ser usado como entrada e saída controlada.

Usos permitidos:

- importação de cronograma;
- importação de EAP;
- importação de orçamento;
- importação de composições;
- exportação de programação semanal;
- exportação de pendências;
- exportação de relatório executivo.

Excel não deve ser a fonte oficial da verdade.

Fluxo correto:

Excel → staging → validação → normalização → PostgreSQL.

---

## 12. Custos e composições

O Agente 008 deve prever integração futura com:

- SINAPI;
- TCPO, respeitando licença;
- SICRO;
- BDI;
- CUB;
- composições próprias;
- produtividade própria;
- histórico real de obra.

As composições de referência não devem ser confundidas com atividades reais da obra.

Composição de referência é dado técnico-econômico.
Atividade de obra é unidade operacional vinculada a área, prazo, equipe, frente, responsável e produção real.

---

## 13. Normas técnicas

O Agente 008 deve prever uma base normativa estruturada.

A base deve conter:

- código da norma;
- título;
- versão;
- ano;
- disciplina;
- escopo resumido;
- requisito resumido;
- item ou cláusula de referência;
- evidência exigida;
- atividade vinculada;
- responsável pela validação;
- status.

O sistema não deve armazenar texto integral de NBR sem licença.

O sistema não deve redistribuir PDF de norma no Git.

A IA não deve inventar requisito normativo.

---

## 14. Tabelas propostas para fases futuras

### MVP 0.6A

- areas_obra;
- eap_obra;
- atividades_cronograma;
- dependencias_atividades;
- restricoes_atividade;
- planos_operacionais_obra.

### MVP 0.6B

- snapshots_cronograma;
- atualizacoes_cronograma;
- apontamentos_producao;
- medicoes_obra.

### MVP 0.6C

- fontes_referencia_custos;
- insumos_referencia;
- composicoes_referencia;
- composicao_itens;
- atividade_composicao_ref;
- bdi_modelos;
- orcamento_itens.

### MVP 0.6D

- normas_tecnicas;
- requisitos_normativos;
- atividade_norma_map;
- checklists_normativos;
- evidencias_normativas.

---

## 15. Comandos Telegram previstos

Comandos iniciais:

- /status_obra OBRA-001
- /cronograma_15d OBRA-001
- /lookahead_30d OBRA-001
- /programacao_mensal OBRA-001
- /area_status OBRA-001 AREA-01
- /pendencias_criticas OBRA-001
- /restricoes OBRA-001
- /compras_impacto_cronograma OBRA-001
- /plano_amanha OBRA-001
- /reuniao_obra OBRA-001

---

## 16. Saídas esperadas

O Agente 008 deve produzir:

- resumo executivo;
- diagnóstico operacional;
- plano de amanhã;
- programação de 0 a 15 dias;
- lookahead de 15 a 30 dias;
- programação mensal por área;
- lista de restrições;
- pendências críticas;
- atividades bloqueadas;
- compras que impactam prazo;
- decisões necessárias;
- riscos de atraso;
- propostas de reprogramação;
- comandos candidatos para outros agentes.

---

## 17. Critérios de aceite do MVP 0.6A

O MVP 0.6A será considerado aceito quando:

1. existir documentação oficial do Agente 008;
2. o agente tiver missão e limites definidos;
3. a fonte da verdade estiver definida como PostgreSQL;
4. Excel estiver definido apenas como entrada/saída controlada;
5. OpenProject estiver definido como vitrine de Gantt;
6. os horizontes 0–15 dias, 15–30 dias e mensal por área estiverem documentados;
7. as primeiras tabelas de cronograma/EAP estiverem propostas;
8. os comandos Telegram iniciais estiverem definidos;
9. as integrações com Agentes 002 a 007 estiverem documentadas;
10. as regras de aprovação explícita estiverem preservadas.

---

## 18. Roadmap

### MVP 0.6A — Arquitetura e documentação

Definir o Agente 008, suas responsabilidades, limites, dados, comandos e tabelas.

### MVP 0.6B — Banco mínimo

Criar tabelas de áreas, EAP, atividades, dependências, restrições e planos operacionais.

### MVP 0.6C — Consulta operacional via Telegram

Permitir que o Agente 007 consulte o Agente 008 para status, cronograma 15 dias, lookahead 30 dias e programação mensal.

### MVP 0.6D — Gantt/OpenProject

Sincronizar atividades aprovadas com OpenProject para visualização pela empresa Caio e engenheiros.

### MVP 0.6E — Custos e composições

Integrar SINAPI, TCPO, SICRO, BDI e composições próprias.

### MVP 0.6F — Normas e checklists

Criar base estruturada de NBRs, NRs, requisitos, checklists e evidências.

---

## 19. Regra final

O Agente 008 deve ser iniciado como motor de gestão operacional baseado em dados.

Ele não deve ser implementado como chatbot genérico.

A ordem correta é:

1. dados mestres;
2. EAP;
3. cronograma;
4. restrições;
5. RDO;
6. pendências;
7. compras;
8. custos;
9. normas;
10. Gantt;
11. decisões executivas aprovadas.
