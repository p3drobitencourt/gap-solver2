import csv
import time
from pathlib import Path
from src.generator import generate_gap_instance
from src.heuristic import regret_greedy_heuristic
from src.model_exact import build_gap_model, solve_gap_model
from src.validator import validate_solution
from src.hybrid import fix_and_optimize
import pulp

def resolve_status(pulp_status_code, exec_time, time_limit):
    """
    Função auxiliar para não transformar 'timeout' em 'ótimo'.
    O PuLP muitas vezes retorna Optimal=1 quando bate o limite de tempo
    e tem uma solução factível. Precisamos interceptar.
    """
    if exec_time >= time_limit - 1.5:
        if pulp_status_code == pulp.LpStatusOptimal or pulp_status_code == pulp.LpStatusNotSolved:
            return "Timeout (Feasible)"
        return "Timeout (No Solution)"
        
    status_str = pulp.LpStatus.get(pulp_status_code, "Undefined")
    if status_str == "Optimal":
        return "Optimal"
    elif status_str == "Not Solved":
        return "Feasible/Timeout" if pulp_status_code != pulp.LpStatusInfeasible else "Infeasible"
    return status_str

def run_experiment(instance_name, n, m, costs, weights, capacities, seed, time_limit, 
                   fo_strategy="agent_based", fo_size=3, fo_iters=20):
    
    results = []
    
    # Dicionário base de rastreio
    base_record = {
        "Instancia": instance_name,
        "N": n,
        "M": m,
        "Seed": seed,
        "Variaveis": n * m,
        "Restricoes": n + m,
        "Orcamento_Tempo": time_limit
    }

    # =========================================================================
    # 1. HEURÍSTICA PURA
    # =========================================================================
    h_ok, h_x, h_time, _ = regret_greedy_heuristic(n, m, costs, weights, capacities, seed)
    v_ok, h_cost, _ = validate_solution(n, m, costs, weights, capacities, h_x)
    
    rec_heur = base_record.copy()
    rec_heur.update({
        "Metodo": "HEURISTICA",
        "Tempo_Total": h_time,
        "Tempo_Heuristico": h_time,
        "Tempo_Exato": 0.0,
        "Tempo_Hibrido": 0.0,
        "Custo_Solucao": h_cost if h_ok else -1.0,
        "Limite_Dual": "Desconhecido",
        "Gap": "Desconhecido", # Gap heurístico isolado é desconhecido
        "Status": "Feasible" if h_ok else "Infeasible",
        "Factibilidade": v_ok,
        "FO_Custo_Inicial": "", "FO_Custo_Final": "", "FO_Melhoria": "", 
        "FO_Iters": "", "FO_Subprobs": "", "FO_Tamanho_Viz": ""
    })
    results.append(rec_heur)
    
    # =========================================================================
    # 2. EXATO PURO
    # =========================================================================
    prob_ex, x_ex = build_gap_model(f"{instance_name}_EXATO", m, n, costs, weights, capacities)
    status_ex, time_ex, primal_ex, dual_ex, gap_ex, x_res_ex = solve_gap_model(prob_ex, x_ex, m, n, time_limit, warm_start_matrix=None)
    
    real_status_ex = resolve_status(prob_ex.status, time_ex, time_limit)
    v_ok_ex, cost_ex, _ = validate_solution(n, m, costs, weights, capacities, x_res_ex)
    
    if real_status_ex == "Timeout (Feasible)":
        dual_ex = "Desconhecido"
        gap_ex = "Desconhecido"
        
    rec_exato = base_record.copy()
    rec_exato.update({
        "Metodo": "EXATO",
        "Tempo_Total": time_ex,
        "Tempo_Heuristico": 0.0,
        "Tempo_Exato": time_ex,
        "Tempo_Hibrido": 0.0,
        "Custo_Solucao": cost_ex if v_ok_ex else primal_ex,
        "Limite_Dual": dual_ex,
        "Gap": gap_ex,
        "Status": real_status_ex,
        "Factibilidade": v_ok_ex,
        "FO_Custo_Inicial": "", "FO_Custo_Final": "", "FO_Melhoria": "", 
        "FO_Iters": "", "FO_Subprobs": "", "FO_Tamanho_Viz": ""
    })
    results.append(rec_exato)

    # =========================================================================
    # 3. WARM START
    # =========================================================================
    rem_time = time_limit - h_time
    if h_ok:
        if rem_time > 0:
            prob_ws, x_ws = build_gap_model(f"{instance_name}_WS", m, n, costs, weights, capacities)
            status_ws, time_ws, primal_ws, dual_ws, gap_ws, x_res_ws = solve_gap_model(
                prob_ws, x_ws, m, n, rem_time, warm_start_matrix=h_x
            )
            real_status_ws = resolve_status(prob_ws.status, time_ws, rem_time)
            v_ok_ws, cost_ws, _ = validate_solution(n, m, costs, weights, capacities, x_res_ws)
            if real_status_ws == "Timeout (Feasible)":
                dual_ws = "Desconhecido"
                gap_ws = "Desconhecido"
        else:
            time_ws = 0.0
            primal_ws = h_cost
            dual_ws = "Desconhecido"
            gap_ws = "Desconhecido"
            real_status_ws = "Timeout (Heuristic)"
            v_ok_ws = True
            cost_ws = h_cost
    else:
        # Se heurística falhou, registra falha do WS e não mascara como Exato
        time_ws = 0.0
        primal_ws = -1.0
        dual_ws = "Desconhecido"
        gap_ws = "Desconhecido"
        real_status_ws = "Infeasible Initial"
        v_ok_ws = False
        cost_ws = -1.0

    rec_ws = base_record.copy()
    rec_ws.update({
        "Metodo": "WARM_START",
        "Tempo_Total": h_time + time_ws,
        "Tempo_Heuristico": h_time,
        "Tempo_Exato": time_ws,
        "Tempo_Hibrido": 0.0,
        "Custo_Solucao": cost_ws if v_ok_ws else primal_ws,
        "Limite_Dual": dual_ws,
        "Gap": gap_ws,
        "Status": real_status_ws,
        "Factibilidade": v_ok_ws,
        "FO_Custo_Inicial": "", "FO_Custo_Final": "", "FO_Melhoria": "", 
        "FO_Iters": "", "FO_Subprobs": "", "FO_Tamanho_Viz": ""
    })
    results.append(rec_ws)

    # =========================================================================
    # 4. FIX AND OPTIMIZE
    # =========================================================================
    fo_res = fix_and_optimize(n, m, costs, weights, capacities, time_limit, seed,
                              neighborhood_size=fo_size, max_iterations=fo_iters, strategy=fo_strategy)
    
    rec_fo = base_record.copy()
    rec_fo.update({
        "Metodo": "FIX_AND_OPTIMIZE",
        "Tempo_Total": fo_res["total_time"],
        "Tempo_Heuristico": h_time, # fo usa a mesma heuristica no início
        "Tempo_Exato": 0.0,
        "Tempo_Hibrido": fo_res["total_time"] - h_time,
        "Custo_Solucao": fo_res["final_cost"],
        "Limite_Dual": "Desconhecido", # FO é puramente primal, não garante limite inferior global
        "Gap": "Desconhecido",
        "Status": fo_res["status"],
        "Factibilidade": fo_res["feasibility"],
        "FO_Custo_Inicial": fo_res.get("initial_cost", ""), 
        "FO_Custo_Final": fo_res.get("final_cost", ""), 
        "FO_Melhoria": fo_res.get("abs_improvement", ""), 
        "FO_Iters": fo_iters, 
        "FO_Subprobs": fo_res.get("num_neighborhoods", ""), 
        "FO_Tamanho_Viz": fo_size
    })
    results.append(rec_fo)

    return results

def save_results_csv(all_results, output_file="experiment_results.csv"):
    if not all_results:
        return
        
    keys = all_results[0].keys()
    
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"Resultados salvos em {output_file}")
