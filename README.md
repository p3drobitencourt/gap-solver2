# TP-III — Métodos Híbridos para o Problema de Atribuição Generalizada

## 1. Objetivo
O objetivo deste trabalho prático (TP-III) é implementar, avaliar e comparar abordagens para a resolução do Problema de Atribuição Generalizada (GAP). A experimentação consiste em contrapor quatro estratégias de resolução:
- **Heurística Construtiva**
- **Método Exato** (Formulação Matemática Integral)
- **Warm Start** (Método Exato acelerado por uma solução inicial)
- **Fix-and-Optimize** (Heurística de Melhoria ou Método Híbrido/Matheurística)

## 2. O Problema
O Problema de Atribuição Generalizada (GAP) consiste em designar um conjunto de `N` tarefas a um conjunto de `M` agentes.
Cada agente `i` executa a tarefa `j` com um respectivo custo `c_ij` consumindo um peso `w_ij` da sua capacidade. Cada agente possui uma capacidade máxima `C_i`.
O objetivo é minimizar o custo total de alocação de forma que **cada tarefa seja atribuída a exatamente um agente** e a capacidade dos agentes não seja violada.

A formulação matemática é dada por:

**Variáveis de Decisão:**
`x_ij ∈ {0, 1}`: 1 se a tarefa `j` for atribuída ao agente `i`, 0 caso contrário.

**Função Objetivo:**
Minimizar Z = Σ (i=1..M) Σ (j=1..N) (c_ij * x_ij)

**Restrições:**
1. Σ (i=1..M) x_ij = 1, para toda tarefa j (Atribuição Única)
2. Σ (j=1..N) (w_ij * x_ij) <= C_i, para todo agente i (Capacidade do Agente)

## 3. Estrutura do projeto

- `src/generator.py`: Módulo responsável pela geração pseudoaleatória determinística das instâncias experimentais e verificação basal de factibilidade com base em restrições de tightness.
- `src/heuristic.py`: Implementação da Heurística Construtiva Gulosa por Regret.
- `src/model_exact.py`: Implementação do Modelo Exato usando a biblioteca PuLP para invocar o solver matemático, com suporte opcional de Warm Start.
- `src/hybrid.py`: Implementação da estratégia Fix-and-Optimize.
- `src/validator.py`: Ferramenta para atestar formalmente a factibilidade da matriz de solução (validando capacidades e restrições binárias).
- `src/experiments.py`: Arquivo de orquestração local de experimentos, que registra cronômetros, limites e consolida as métricas na estrutura do CSV de saída.
- `src/visualize_official.py`: Script dedicado a consumir a saída consolidada do experimento e gerar os painéis gráficos (matplotlib) sem recalibrar os dados.
- `tests/`: Bateria automatizada cobrindo o comportamento da heurística construtiva, método híbrido e compatibilidade das execuções parciais de solver.
- `results/official/`: Diretório persistente de saída, armazenando CSVs individuais gerados por isolamento em subprocesso, CSV consolidado e JSON de metadados.
- `run_experiments.py`: Ponto de entrada do sistema. O executor orquestra iterativamente os testes de todos os cenários dimensionais em subprocessos estanques de memória.
- `requirements.txt`: Relação pura e fidedigna de dependências do Python.

## 4. Geração das instâncias
Para atestar a generalização sem interferências não controladas, o laboratório gera as instâncias dinamicamente e de forma totalmente determinística. Foram estabelecidos os seguintes parâmetros de controle:
- **N (tarefas)** = 50, 100, 150, 200, 300, 500
- **M (agentes)** = N // 5
- **Seed** = 42
- **Tightness** = 1.10

**Geração:** O algoritmo sorteia uniformemente os custos entre 10 e 100, e os pesos entre 5 e 50. Para garantir ao menos uma resposta factível na Árvore de Branch-and-Bound, constrói-se uma atribuição de segurança ("atribuição viável invisível") aleatorizada, e as capacidades dos agentes são definidas como a soma dos pesos processados nesta pseudo-atribuição incrementada pelo fator limitador *Tightness*.

## 5. Heurística
Foi implementada uma Heurística Construtiva orientada por critério *Regret* para GAP:
- **Cálculo de Regret:** Para cada tarefa não alocada, tenta-se associá-la temporariamente aos dois melhores agentes disponíveis (que ofertam o menor custo `c_ij` sem violar capacidades restantes). A diferença de custo entre o segundo melhor e o melhor agente define o valor do regret (penalidade do arrependimento).
- **Escolha da Tarefa:** A tarefa com o maior valor de regret é a mais urgente e, portanto, alocada primeiro.
- **Escolha do Agente:** Essa tarefa escolhida é direcionada ao seu agente de menor custo viável.
- Ao atualizar a capacidade residual daquele agente, refaz-se o cálculo de regret para o remanescente.
- Este método determinístico constrói e fornece, confiavelmente, uma solução factível e sem lacunas em tempos de infra-segundo.

## 6. Método Exato
O método foi escrito modelando algebricamente as matrizes através da biblioteca **PuLP**. A otimização em si delega o branch-and-cut ao executável Open Source **CBC (Coin-or branch and cut)**.

Foram declaradas matrizes em tempo de compilação representando `M x N` variáveis estritamente binárias e restrições de soma com cortes de capacidade lineares.

Para garantir validade metodológica sob cenários extensos, o modelo Exato opera sob um **limite configurado de 60 segundos**.
> O limite de 60 segundos corresponde ao argumento `timeLimit` repassado rigidamente ao executável do solver CBC. O campo `Tempo_Total` registrado pelo experimento na planilha CSV pode ser ligeiramente superior devido ao overhead irremovível de construção das matrizes no framework Python, a comunicação por escrita de arquivo temporário (MPS) com o solver e o parser do resultado logado pelo PuLP de volta ao Python.

## 7. Warm Start
A variante Warm Start integra a Heurística Regret à base Exata. A solução construtiva (matriz binária inicial) preenchida pela heurística em uma fração de segundo é embutida explicitamente e passada como *MIP Start* viável ao CBC na inicialização da rotina. Este processo é uma avaliação controlada do quanto a provisão prévia do nó viável aprimora as métricas finais do Exato dentro do limite configurado.

## 8. Fix-and-Optimize
A matheurística Fix-and-Optimize (F&O) é implementada iterativamente usando a abordagem construtiva original sob um orçamento de tempo limitado.
**Estratégia metodológica:**
- **Solução Inicial:** Atingida via Heurística Construtiva de Regret.
- **Estratégia de Fixação:** `agent_based` (agentes são escolhidos iterativamente).
- **Tamanho da Vizinhança:** 3 agentes destravados.
- **Máximo de Iterações:** 20 ciclos.
- Em cada subproblema, as alocações contidas nos M-3 agentes ficam amarradas no limitante atual.
- As variáveis e tarefas correspondentes aos 3 agentes escolhidos ficam totalmente livres e injetadas de forma autônoma no solver Exato.
- A solução devolvida é testada matematicamente pelo validador do sistema de forma contínua e isolada. Caso haja superação com um *Z* menor que o incumbent (e apenas caso atestado Factível), ela torna-se o novo marco.
- O tempo de cada iteração F&O consome iterativamente o orçamento total end-to-end de 60 segundos.

## 9. Metodologia Experimental

| Parâmetro | Valor |
| --- | --- |
| N | 50, 100, 150, 200, 300, 500 |
| M | N // 5 |
| Seed | 42 |
| Tightness | 1.10 |
| Limite CBC | 60 s |
| F&O strategy | agent_based |
| F&O size | 3 agentes |
| F&O iterations | 20 |

Cada escala (N) foi executada e logada individualmente contra os quatro métodos descritos de forma ininterrupta (`HEURISTICA`, `EXATO`, `WARM_START`, `FIX_AND_OPTIMIZE`). O isolamento em subprocessos impede degradação na máquina Python virtual.

## 10. Resultados
As análises métricas estão armazenadas consolidamente em artefatos puristas (CSVs) para revisão bibliométrica no seu diretório final:
- Tabela oficial consolidada: `results/official/official_experiment.csv`
- Metadados, assinaturas numéricas e Hashes: `results/official/official_metadata.json`

Quatro recortes analíticos foram gerados no formato de plot a partir desses dados brutos:
1. `results/official/plots/custo_vs_n.png`
2. `results/official/plots/tempo_vs_n.png`
3. `results/official/plots/fo_improvement_vs_n.png`
4. `results/official/plots/exact_status_vs_n.png`

## 11. Como Executar
O projeto está integralmente orquestrado. Certifique-se de usar `python 3.9+`.

**Instalação das dependências e solvers atrelados:**
```bash
pip install -r requirements.txt
```

**Executar a bateria completa (oficial) ou uma rodada experimental unitária:**
Para realizar a reprodução controlada que resultará na pasta de CSVs:
```bash
python run_experiments.py
```
*Observação: caso se deseje executar isoladamente um único valor de dimensão durante o uso empírico, a API permite argumentos como `python run_experiments.py --run-single-N 50 --time-limit 60.0`.*

**Gerar as Visualizações Oficiais (Matplotlib):**
Lê os CSVs já gerados na bateria e exporta gráficos rigorosos:
```bash
python src/visualize_official.py
```

## 12. Testes (QA Control)
Um conjunto básico de testes formais (pytest-like runner local) pode ser acionado em instâncias simples de depuração:
- `tests/test_heuristic.py`: Garante as reações matemáticas corretas no cálculo do Regret.
- `tests/test_hybrid.py`: Verifica se as vizinhanças destravadas pela estratégia Agent-based retornam soluções válidas e melhoradas.
- `tests/test_warm_start.py`: Audita se o PuLP absorve e traduz efetivamente a matriz de warmup para o executável base.

## 13. Observação metodológica sobre as Medições de Tempo
Ao reler e auditar a literatura metodológica final, distingue-se perfeitamente o Limite Matemático (Solver Time) e o Tempo Sistêmico Computado (Tempo_Total).
- O **solver matemático (CBC)** atua com um teto de controle inflexível alocado perfeitamente pela nossa injeção `timeLimit=60`. A partir da marca 60.0s do Branch-and-Bound, seu núcleo aborta.
- O campo `Tempo_Total` nos logs mede integralmente o cronômetro do ambiente interpretado Python. Instâncias robustas (como N=500 com 50 mil matrizes binárias operacionais) forçam o frame PuLP a traduzir um modelo de memória de mais de dois milhões de restrições em um arquivo serializado complexo (MPS) enviado e recebido de volta à memória via Parsing da matriz. Este overhead transitório não é computacionalmente "tempo de cálculo do algoritmo de Otimização", resultando na exibição de logs de `61.5s` de forma metodologicamente justificada.

## 14. Reprodutibilidade
O trabalho pauta a reprodutibilidade acadêmica através da chave universal **Seed=42**. O determinismo dos algoritmos e de geração mantém que a arquitetura dos arquivos devolva invariavelmente os mesmos resultados, que não sofrem variação nos gráficos e planilhas após re-execução do comando orquestrador `python run_experiments.py`.
