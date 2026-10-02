def validate_solution(n, m, costs, weights, capacities, x_matrix):
    """
    Validador independente para o GAP.
    Recebe os dados da instância e a matriz de decisão x_matrix (m x n).
    Retorna: (is_feasible, total_cost, msg)
    """
    total_cost = 0.0
    
    # 1. Checagem de dimensão
    if len(x_matrix) != m:
        return False, 0.0, "Erro: x_matrix não possui M linhas."
    for i in range(m):
        if len(x_matrix[i]) != n:
            return False, 0.0, f"Erro: Linha {i} da x_matrix não possui N colunas."
            
    # 2. Cada tarefa atribuída exatamente uma vez e valores binários
    for j in range(n):
        sum_assign = 0
        for i in range(m):
            val = x_matrix[i][j]
            if val not in (0, 1):
                return False, 0.0, f"Erro: Valor x[{i}][{j}] = {val} não é binário."
            sum_assign += val
        if sum_assign != 1:
            return False, 0.0, f"Erro: Tarefa {j} foi atribuída {sum_assign} vezes (deveria ser 1)."
            
    # 3. Capacidades respeitadas e cálculo de custo
    cargas = [0] * m
    for i in range(m):
        carga_agente = 0
        for j in range(n):
            if x_matrix[i][j] == 1:
                carga_agente += weights[i][j]
                total_cost += costs[i][j]
        cargas[i] = carga_agente
        
        if carga_agente > capacities[i]:
            return False, total_cost, f"Erro: Agente {i} excedeu a capacidade ({carga_agente} > {capacities[i]})."
            
    return True, total_cost, "Solução factível e válida."
