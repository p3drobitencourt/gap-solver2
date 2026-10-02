import time
import random
import math

def regret_greedy_heuristic(n, m, costs, weights, capacities, seed=None):
    """
    Heurística Construtiva Baseada em Arrependimento (Regret).
    
    REGRA DE SELEÇÃO:
    Para cada tarefa não atribuída, avalia-se os agentes que ainda possuem
    capacidade para recebê-la.
    Ordena-se os agentes viáveis pelo menor custo.
    Calcula-se o "arrependimento" = (Custo do 2º melhor agente) - (Custo do 1º melhor agente).
    Escolhe-se a tarefa com o MAIOR arrependimento (ou seja, a tarefa que, se
    não for alocada agora para o melhor agente, sofrerá a maior penalidade depois).
    Em caso de empates no arrependimento, o desempate é feito aleatoriamente usando a seed.
    A tarefa selecionada é então alocada ao seu melhor agente viável.
    
    Retorna: (is_feasible, x_matrix, exec_time)
    """
    start_time = time.perf_counter()
    
    if seed is not None:
        random.seed(seed)
        
    x_matrix = [[0] * n for _ in range(m)]
    rem_cap = list(capacities)
    unassigned = list(range(n))
    
    # Historico mínimo para analise
    history = {
        "tasks_assigned": 0,
        "bottlenecks_encountered": 0
    }
    
    while unassigned:
        max_regret = -1.0
        candidates_for_max = []
        
        for j in unassigned:
            # Filtra agentes viáveis para a tarefa j
            feasible_agents = []
            for i in range(m):
                if rem_cap[i] >= weights[i][j]:
                    feasible_agents.append((costs[i][j], i))
                    
            if not feasible_agents:
                # Nenhuma atribuição viável encontrada para essa tarefa
                history["bottlenecks_encountered"] += 1
                exec_time = time.perf_counter() - start_time
                return False, x_matrix, exec_time, history
                
            feasible_agents.sort(key=lambda item: item[0]) # Ordena pelo menor custo
            
            if len(feasible_agents) == 1:
                regret = math.inf # Se só tem 1 opção, o arrependimento de perdê-la é infinito
            else:
                regret = feasible_agents[1][0] - feasible_agents[0][0]
                
            if regret > max_regret:
                max_regret = regret
                candidates_for_max = [(j, feasible_agents[0][1])] # Salva a tarefa e seu melhor agente
            elif regret == max_regret:
                candidates_for_max.append((j, feasible_agents[0][1]))
                
        # Desempate aleatório via seed
        chosen_j, chosen_i = random.choice(candidates_for_max)
        
        # Efetiva a atribuição
        x_matrix[chosen_i][chosen_j] = 1
        rem_cap[chosen_i] -= weights[chosen_i][chosen_j]
        unassigned.remove(chosen_j)
        history["tasks_assigned"] += 1
        
    exec_time = time.perf_counter() - start_time
    return True, x_matrix, exec_time, history
