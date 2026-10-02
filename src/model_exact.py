import pulp
import time

def build_gap_model(instance_name, m, n, costs, weights, capacities):
    """
    Constrói a formulação matemática do GAP.
    Reutiliza a lógica exata do TP-II.
    """
    prob = pulp.LpProblem(f"GAP_{instance_name}", pulp.LpMinimize)
    
    # Variáveis
    x = {
        (i, j): pulp.LpVariable(f"x_{i}_{j}", cat='Binary')
        for i in range(m)
        for j in range(n)
    }
    
    # Função Objetivo
    prob += pulp.lpSum(costs[i][j] * x[i, j] for i in range(m) for j in range(n)), "Custo_Total"
    
    # Restrição 1: Cada tarefa deve ser feita por exatamente 1 agente
    for j in range(n):
        prob += pulp.lpSum(x[i, j] for i in range(m)) == 1, f"Tarefa_{j}_atribuida_unica"
        
    # Restrição 2: Respeitar a capacidade de cada agente
    for i in range(m):
        prob += pulp.lpSum(weights[i][j] * x[i, j] for j in range(n)) <= capacities[i], f"Capacidade_Agente_{i}"
        
    return prob, x

def solve_gap_model(prob, x, m, n, time_limit, warm_start_matrix=None):
    """
    Executa o solver exato, opcionalmente com warm start.
    Retorna métricas do solver.
    """
    # Aplicando Warm Start se fornecido
    if warm_start_matrix is not None:
        for i in range(m):
            for j in range(n):
                x[i, j].setInitialValue(warm_start_matrix[i][j])
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit, warmStart=True)
    else:
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit)
        
    start_time = time.perf_counter()
    prob.solve(solver)
    exec_time = time.perf_counter() - start_time
    
    status = pulp.LpStatus[prob.status]
    
    try:
        primal = pulp.value(prob.objective)
    except:
        primal = -1.0
        
    # Extração de best bound no CBC é inconsistente via msg=False.
    # Mas tentamos puxar se o pulp expuser.
    dual = getattr(prob, 'bestBound', None)
    if dual is None:
        if status == "Optimal":
            dual = primal
        else:
            dual = "Desconhecido" # Unknown bound without parsing logs
            
    gap = "Desconhecido"
    if primal > 0 and isinstance(dual, (int, float)) and dual > 0:
        gap = (primal - dual) / primal
        
    # Reconstroi a matriz resultante
    x_result = [[0]*n for _ in range(m)]
    if primal != -1.0:
        for i in range(m):
            for j in range(n):
                if x[i, j].varValue is not None and x[i, j].varValue > 0.5:
                    x_result[i][j] = 1
                    
    return status, exec_time, primal, dual, gap, x_result
