import time
import random
import pulp
from src.heuristic import regret_greedy_heuristic
from src.model_exact import build_gap_model
from src.validator import validate_solution

def generate_neighborhood(n, m, x_best, strategy, size, iteration, seed):
    """
    Define a vizinhança liberando um subconjunto de tarefas.
    Retorna uma lista de índices de tarefas (j) que estarão LIVRES.
    As demais tarefas serão FIXADAS no seu agente atual.
    
    Estratégias documentadas:
    - task_random: Libera 'size' tarefas aleatoriamente.
    - agent_based: Escolhe 'size' agentes aleatoriamente e libera TODAS as tarefas atualmente alocadas a eles.
    """
    rng = random.Random(seed + iteration) # garante variação determinística por iteração
    
    if strategy == "task_random":
        # Seleciona tarefas aleatórias para tentar realocar
        tasks = list(range(n))
        rng.shuffle(tasks)
        return tasks[:size]
        
    elif strategy == "agent_based":
        # Seleciona um grupo de agentes e libera as tarefas deles para tentar permutas
        agents = list(range(m))
        rng.shuffle(agents)
        chosen_agents = set(agents[:size])
        
        free_tasks = []
        for i in chosen_agents:
            for j in range(n):
                if x_best[i][j] == 1:
                    free_tasks.append(j)
        return free_tasks
        
    else:
        # Fallback para task_random
        tasks = list(range(n))
        rng.shuffle(tasks)
        return tasks[:size]

def fix_and_optimize(n, m, costs, weights, capacities, global_time_limit, seed, 
                     neighborhood_size=10, max_iterations=20, strategy="task_random"):
    """
    Matheurística Fix-and-Optimize para GAP.
    """
    start_time = time.perf_counter()
    
    # 1. Obter solução inicial via heurística construtiva
    h_is_feasible, x_best, h_time, _ = regret_greedy_heuristic(n, m, costs, weights, capacities, seed)
    
    val_ok, best_cost, _ = validate_solution(n, m, costs, weights, capacities, x_best)
    if not val_ok or not h_is_feasible:
        # Se heurística falhar, F&O aborta
        return {
            "status": "Infeasible Initial",
            "feasibility": False,
            "initial_cost": -1,
            "final_cost": -1,
            "abs_improvement": 0.0,
            "pct_improvement": 0.0,
            "num_neighborhoods": 0,
            "num_improvements": 0,
            "total_time": time.perf_counter() - start_time,
            "avg_subproblem_time": 0.0,
            "history_costs": [],
            "x_matrix": []
        }
        
    initial_cost = best_cost
    
    history_cost = [initial_cost]
    num_improvements = 0
    subproblem_times = []
    
    # Loop de iterações do F&O
    for it in range(max_iterations):
        elapsed = time.perf_counter() - start_time
        rem_time = global_time_limit - elapsed
        
        if rem_time <= 3.5:
            break # Estourou o tempo global ou margem muito pequena
            
        solver_limit = max(0.1, rem_time - 3.0)
            
        # Orçamento de tempo por subproblema (distribui o tempo restante)
        # Ex: no max 5 segundos por subproblema para garantir fluidez
        sub_time_limit = min(solver_limit, max(2.0, solver_limit / (max_iterations - it)))
        
        # Gera a vizinhança (tarefas que poderão ser realocadas)
        free_tasks = generate_neighborhood(n, m, x_best, strategy, neighborhood_size, it, seed)
        free_tasks_set = set(free_tasks)
        
        # Constrói o modelo MIP
        prob, x_vars = build_gap_model(f"fo_{it}", m, n, costs, weights, capacities)
        
        # Aplica as restrições de FIXAÇÃO e WARM START
        for i in range(m):
            for j in range(n):
                val_incumbent = x_best[i][j]
                
                # Warm start
                x_vars[i, j].setInitialValue(val_incumbent)
                
                # Fixa a variável se a tarefa NÃO estiver na vizinhança livre
                if j not in free_tasks_set:
                    # Trava a variável no valor da incumbente
                    prob += x_vars[i, j] == val_incumbent, f"Fix_{i}_{j}"
                    
        # Resolve o subproblema
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=sub_time_limit, warmStart=True)
        
        t0_sub = time.perf_counter()
        prob.solve(solver)
        t_sub = time.perf_counter() - t0_sub
        subproblem_times.append(t_sub)
        
        # Verifica se achou algo melhor
        if prob.status == pulp.LpStatusOptimal or prob.status == pulp.LpStatusNotSolved:
            try:
                new_cost = pulp.value(prob.objective)
            except:
                new_cost = best_cost
                
            # Como lidamos com ponto flutuante, exige uma melhora clara
            if new_cost is not None and new_cost < best_cost - 0.1:
                # Extrai nova matriz
                new_x = [[0]*n for _ in range(m)]
                for i in range(m):
                    for j in range(n):
                        if x_vars[i, j].varValue is not None and x_vars[i, j].varValue > 0.5:
                            new_x[i][j] = 1
                            
                # Validador independente GARANTE que não corrompeu a solução
                val_ok, check_cost, msg = validate_solution(n, m, costs, weights, capacities, new_x)
                if val_ok:
                    x_best = new_x
                    best_cost = check_cost
                    num_improvements += 1
                    
        history_cost.append(best_cost)
        
    total_time = time.perf_counter() - start_time
    avg_sub_time = sum(subproblem_times) / len(subproblem_times) if subproblem_times else 0.0
    
    abs_improvement = initial_cost - best_cost
    pct_improvement = (abs_improvement / initial_cost) * 100 if initial_cost > 0 else 0.0
    
    # Validação final rigorosa
    final_ok, final_cost_checked, _ = validate_solution(n, m, costs, weights, capacities, x_best)
    
    return {
        "status": "Finished",
        "feasibility": final_ok,
        "initial_cost": initial_cost,
        "final_cost": best_cost,
        "abs_improvement": abs_improvement,
        "pct_improvement": pct_improvement,
        "num_neighborhoods": len(subproblem_times),
        "num_improvements": num_improvements,
        "total_time": total_time,
        "avg_subproblem_time": avg_sub_time,
        "history_costs": history_cost,
        "x_matrix": x_best
    }
