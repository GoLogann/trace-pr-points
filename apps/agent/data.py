ROTEIRO_METRICAS_SISP="""
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

"""

ROTEIRO_SISP_AI="""
# Contagem de Pontos de Função em Projetos de Inteligência Artificial (IA)

Este documento reúne as diretrizes do **SISP** sobre contagem de Pontos de Função (PF) em soluções de **Inteligência Artificial**, Chatbots e Painéis Analíticos, conforme o roteiro oficial de métricas.

---

## 1. Introdução

A **Inteligência Artificial (IA)** busca desenvolver algoritmos e sistemas capazes de realizar tarefas que normalmente exigem inteligência humana, como:

- Reconhecimento de padrões  
- Aprendizado e tomada de decisão  
- Processamento de linguagem natural  

No setor público, a IA é aplicada para **tomada de decisão, eficiência operacional e inovação**.

---

## 2. Fronteira da Aplicação

- Cada **fronteira impactada** deve ter contagem própria.  
- O foco deve ser a **visão do usuário**, não a tecnologia utilizada.  
- Funções replicadas em múltiplas mídias (Web, API, Mobile) geram instâncias adicionais.  

---

## 3. Escopo da Contagem de IA

- A contagem considera a **fase de operacionalização** da solução.  
- Atividades de **descoberta e treinamento** não são contempladas em PF → devem ser mensuradas em **HST (Hora de Serviço Técnico)**.  

Arquiteturas comuns:
- **Processamento em lote (batch)**
- **Execução interativa (on-demand)**

---

## 4. Processamento Batch de IA

Fluxo típico:
1. **Dados de Origem** (AIE/AL)  
2. **Explorar Dados** (EE/PE e CE/SE)  
3. **Preparar Dados** (EE/PE)  
4. **Criar Modelos** (EE/PE)  
5. **Gerar Dados Resultantes** (ALI/AL + EE/PE)  
6. **Disponibilizar Dados** (CE/SE ou PE)  
7. **Destino**: Aplicações externas  

**Regras principais:**
- Dados temporários (views, CSV transitórios, buffers) não contam.  
- Técnicas de preparação de dados (tokenização, normalização, estemização, etc.) **não contam separadamente**.  
- Cada execução de modelo é **uma função** independente da quantidade de técnicas aplicadas.  

---

## 5. Execução Interativa de IA

- **Preparar Dados**: entrada e transformação (EE/SE ou PE).  
- **Invocar Modelo**: execução sob demanda (SE ou PE).  
- **Cliente**: aplicações externas que acionam a solução.  

Regras iguais às do processamento batch, mas orientadas ao **uso síncrono**.

---

## 6. Manutenções em Soluções de IA

- Seguem as regras de manutenção já definidas no roteiro (alterações em funções de dados ou transacionais).  
- Novos modelos ou ajustes contam como **funções adicionais ou alteradas**.  

---

## 7. Contagem em ChatBots

### 7.1 Definição
Chatbots simulam conversas em linguagem natural em canais como Web, WhatsApp, Messenger etc.  
Podem ser:  
- **Regras** (árvores de decisão)  
- **IA** (redes neurais, LLMs)  
- **Híbridos**  

### 7.2 Funções de Dados
- **Dados de Diálogo** (ALI/AL)  
- **Histórico de Interações** (ALI/AL)  
- **Dados Externos** (AIE/AL)  

### 7.3 Funções Transacionais
Cada **nó de diálogo** corresponde a uma função transacional:  
- Onboarding  
- Inatividade  
- Repetição  
- Avaliação positiva/negativa  
- Feedback  
- Termos políticos  
- Impropriedades  
- Transbordo  
- Sugestões  

### 7.4 Manutenção
- Alterações de funções de dados ou de nós de diálogo contam como **funções alteradas**.  
- Novos tipos de nó contam como **funções adicionais**.  

### 7.5 Itens Fora da Contagem
- **Curadoria**  
- **Experiência do usuário (UX)**  
→ Devem ser medidos via **HST**.  

---

## 8. Contagem em Painéis Analíticos

### 8.1 Escopo
- Dashboards, gráficos, KPIs e tabelas dinâmicas.  
- Multi-plataforma (Tableau, Qlik etc.) → cada implementação conta separadamente.  

### 8.2 Regras
- Nem toda tabela = arquivo lógico. Um grupo lógico pode englobar várias tabelas.  
- Cargas de dados contam como processos elementares:  
  - Carga inicial (Full) = 1 processo.  
  - Carga incremental (Delta) = outro processo.  

---

## 9. Itens Fora da Contagem

- **Descoberta de dados**  
- **Curadoria de modelos**  
- **Experiência do usuário (UX)**  
→ Medidos via **HST**.

---

## 10. Conclusão

As diretrizes de contagem em IA, Chatbots e Painéis Analíticos garantem **padronização e precisão**, evitando superdimensionamento e refletindo a real entrega de valor para o usuário final.

"""