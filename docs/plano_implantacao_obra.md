# Plano de Implantação — Gestão por Dados da Obra

## 1. Objetivo

Implantar uma estrutura inicial de gestão por dados para acompanhamento executivo e operacional da obra, integrando documentos, medições, contratos, fornecedores, pendências e indicadores em um ambiente centralizado.

## 2. Arquitetura MVP

Fluxo inicial:

E-mails / documentos / planilhas / relatórios / medições
→ n8n
→ MinIO
→ Python ETL
→ PostgreSQL
→ Grafana

## 3. Escopo inicial

O MVP da obra contemplará:

- Cadastro da obra;
- Cadastro de contratos;
- Cadastro de fornecedores;
- Registro de documentos;
- Registro de medições;
- Registro de pendências;
- Registro de eventos relevantes;
- Dashboard executivo inicial.

## 4. Indicadores prioritários

- Avanço físico da obra;
- Valor contratado;
- Valor medido;
- Saldo contratual;
- Quantidade de documentos recebidos;
- Pendências abertas;
- Pendências críticas;
- Status por frente de serviço;
- Última atualização dos dados.

## 5. Fontes de dados

Fontes previstas:

- Planilhas de medição;
- Relatórios diários;
- PDFs técnicos;
- E-mails;
- Fotos;
- Contratos;
- Notas e documentos administrativos;
- Registros manuais no banco.

## 6. Entregáveis da Sprint 1

- Estrutura inicial de banco de dados;
- Buckets iniciais no MinIO;
- Primeiro fluxo no n8n;
- Primeiro dashboard no Grafana;
- Registro de documentos e metadados;
- Cadastro inicial da obra.
