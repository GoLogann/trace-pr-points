# Roteiro de Métricas de Software 3.0 – SISP

Este documento apresenta as orientações oficiais para a **Contagem de Pontos de Função (PF)** conforme a versão 3.0 do roteiro SISP.

---

## 1. Introdução

O roteiro busca uniformizar a **mensuração de software** no âmbito da Administração Pública, garantindo **precisão, comparabilidade e transparência** em contratos de desenvolvimento, manutenção e evolução de sistemas.

---

## 2. Definições Básicas

### 2.1 Análise de Pontos de Função (APF)
Método tradicional baseado em funções de dados e funções transacionais.

### 2.2 SNAP Function Points (SFP)
Extensão que contabiliza processos elementares.

### 2.3 Funções de Dados
- **ALI (Arquivo Lógico Interno)**: dados mantidos pela aplicação.  
- **AIE (Arquivo de Interface Externa)**: dados lidos de outra aplicação.  
- **AL (Arquivo Lógico)**: dados lógicos identificados pelo usuário.  

### 2.4 Funções Transacionais
- **EE (Entrada Externa)**: inclusão, alteração ou exclusão.  
- **SE (Saída Externa)**: processamento com cálculos/transformações.  
- **CE (Consulta Externa)**: leitura simples.  
- **PE (Processo Elementar)**: unidade mínima de processamento.  

---

## 3. Tabelas de Complexidade e Peso

| Tipo | Baixa | Média | Alta |
|------|-------|-------|------|
| EE   | 3 PF  | 4 PF  | 6 PF |
| SE   | 4 PF  | 5 PF  | 7 PF |
| CE   | 3 PF  | 4 PF  | 6 PF |
| ALI  | 7 PF  | 10 PF | 15 PF|
| AIE  | 5 PF  | 7 PF  | 10 PF|

*(valores conforme IFPUG adaptado ao roteiro 3.0)*

---

## 4. Regras de Contagem

### 4.1 CRUD e APIs
- Inclusão/Alteração/Exclusão → **EE**  
- Consulta simples → **CE**  
- Consulta com cálculos/transformação → **SE**  

### 4.2 Componentes Reusáveis
- Contam **apenas uma vez**, mesmo que usados em várias funcionalidades.  

### 4.3 Multi-Mídia
- Cada mídia (Web, Mobile, API, Batch) → **contagem separada**.  

### 4.4 Manutenção
- **Incluídas, alteradas, excluídas** → contabilizadas individualmente.  
- Deve considerar impacto em funções de dados e transacionais.  

---

## 5. Casos Específicos

### 5.1 Inteligência Artificial
- Escopo centrado na **operação da solução**, não em descoberta/treinamento.  
- Arquiteturas **batch** e **interativa** → regras específicas de contagem.  

### 5.2 ChatBots
- **Funções de dados**: diálogos, histórico, integrações externas.  
- **Funções transacionais**: cada tipo de nó de diálogo (onboarding, repetição, avaliação, etc.).  

### 5.3 Painéis Analíticos
- Gráficos, KPIs e dashboards contam como funções de saída.  
- Multi-plataforma = contagem separada.  

### 5.4 DW/BI
- Regras específicas para **ETL, staging e repositórios analíticos**.  
- Dados temporários não contam.  

---

## 6. Métrica HST (Hora de Serviço Técnico)

Utilizada para atividades fora do escopo da APF:  
- Descoberta de dados  
- UX/Design  
- Curadoria de modelos  
- Treinamento de IA  

---

## 7. Conclusão

O Roteiro de Métricas 3.0 é um **refinamento sucessivo**, que:  
- Adapta a contagem a novos paradigmas (IA, Chatbots, APIs, Dashboards).  
- Evita superdimensionamento e duplicidades.  
- Garante **padronização, precisão contratual e transparência**.
