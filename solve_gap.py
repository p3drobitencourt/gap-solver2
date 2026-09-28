import pulp
import time
from pathlib import Path

from visualize_gap import plot_gap_solution

def solve_gap(instance_name, m, n, costs, weights, capacities):
    print(f"\n{'-'*40}")
    print(f"Resolvendo Instância: {instance_name} ({m} agentes, {n} tarefas)")
    print(f"{'-'*40}")
    
    # Criação do modelo de Minimização
    prob = pulp.LpProblem(f"GAP_{instance_name}", pulp.LpMinimize)
    
    # Variáveis de decisão: x[i, j] binárias
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
    
    # Configuração do Solver Exato
    # Para usar HiGHS: solver = pulp.getSolver('HiGHS', timeLimit=600)
    # Para usar Gurobi: solver = pulp.GUROBI_CMD(timeLimit=600)
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=60) # Limite de 10 minutos por instância
    
    start_time = time.time()
    prob.solve(solver)
    end_time = time.time()
    
    status = pulp.LpStatus[prob.status]
    obj_value = pulp.value(prob.objective)
    exec_time = end_time - start_time
    
    print(f"Status da Solução : {status}")
    print(f"Custo Ótimo (Z)   : {obj_value}")
    print(f"Tempo de Execução : {exec_time:.2f} segundos")
    print(f"Variáveis criadas : {m * n}")
    print(f"Restrições geradas: {m + n}")

    return prob, x


def parse_instance(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        tokens = [int(token) for token in f.read().split()]

    iterator = iter(tokens)
    m = next(iterator)
    n = next(iterator)
    costs = [[next(iterator) for _ in range(n)] for _ in range(m)]
    weights = [[next(iterator) for _ in range(n)] for _ in range(m)]
    capacities = [next(iterator) for _ in range(m)]

    return m, n, costs, weights, capacities


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    instance_files = ['a05100', 'c20400', 'e60900']
    solutions = []

    for instance_name in instance_files:
        m, n, costs, weights, capacities = parse_instance(project_root / instance_name)
        prob, x = solve_gap(instance_name, m, n, costs, weights, capacities)
        if pulp.LpStatus[prob.status] in {'Optimal', 'Feasible'}:
            solutions.append((instance_name, m, n, capacities, weights, x))

    for instance_name, m, n, capacities, weights, x in solutions:
        plot_gap_solution(instance_name, m, n, capacities, weights, x)