import sys
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from src.generator import generate_gap_instance
from src.heuristic import regret_greedy_heuristic
from src.model_exact import build_gap_model, solve_gap_model
from src.validator import validate_solution

def run_mode_exato(n, m, costs, weights, capacities, time_limit):
    prob, x = build_gap_model(f"exato_{n}", m, n, costs, weights, capacities)
    status, exec_time, primal, dual, gap, x_result = solve_gap_model(prob, x, m, n, time_limit, warm_start_matrix=None)
    
    val_feasible, total_cost, msg = validate_solution(n, m, costs, weights, capacities, x_result)
    
    return {
        "method": "EXATO",
        "heuristic_time": 0.0,
        "solver_time": exec_time,
        "total_time": exec_time,
        "primal": primal,
        "dual": dual,
        "gap": gap,
        "status": status,
        "feasibility": val_feasible,
        "final_cost": total_cost
    }

def run_mode_warm_start(n, m, costs, weights, capacities, time_limit, seed):
    total_start = time.perf_counter()
    
    # 1. Heurística
    h_is_feasible, h_x_matrix, h_time, _ = regret_greedy_heuristic(n, m, costs, weights, capacities, seed)
    
    if not h_is_feasible:
        # Fallback se heuristica falhar (em instancias muito apertadas)
        return run_mode_exato(n, m, costs, weights, capacities, time_limit)
        
    # 2. Solver com Warm Start
    solver_time_limit = max(1.0, time_limit - h_time) # desconta o tempo gasto na heurística
    prob, x = build_gap_model(f"ws_{n}", m, n, costs, weights, capacities)
    status, s_time, primal, dual, gap, x_result = solve_gap_model(prob, x, m, n, solver_time_limit, warm_start_matrix=h_x_matrix)
    
    total_time = time.perf_counter() - total_start
    val_feasible, total_cost, msg = validate_solution(n, m, costs, weights, capacities, x_result)
    
    return {
        "method": "WARM_START",
        "heuristic_time": h_time,
        "solver_time": s_time,
        "total_time": total_time,
        "primal": primal,
        "dual": dual,
        "gap": gap,
        "status": status,
        "feasibility": val_feasible,
        "final_cost": total_cost
    }

def run_mode_heuristica(n, m, costs, weights, capacities, seed):
    h_is_feasible, h_x_matrix, h_time, _ = regret_greedy_heuristic(n, m, costs, weights, capacities, seed)
    
    val_feasible, total_cost, msg = validate_solution(n, m, costs, weights, capacities, h_x_matrix)
    
    return {
        "method": "HEURISTICA",
        "heuristic_time": h_time,
        "solver_time": 0.0,
        "total_time": h_time,
        "primal": total_cost if h_is_feasible else -1.0,
        "dual": 0.0,
        "gap": 1.0, # gap infinito/100%
        "status": "Feasible" if h_is_feasible else "Infeasible",
        "feasibility": val_feasible,
        "final_cost": total_cost
    }

def run_tests():
    test_ns = [50, 100, 200]
    seed = 42
    time_limit = 10.0 # budget de 10s para ver se WARM_START afeta algo nas grandes
    
    print(f"{'N':>4} | {'Method':>12} | {'Total_T':>8} | {'Heur_T':>8} | {'Solv_T':>8} | {'Primal':>8} | {'Dual':>8} | {'Status':>10} | {'Feas?'}")
    print("-" * 95)
    
    for n in test_ns:
        # Gera instancia factível
        m, _, costs, weights, capacities = generate_gap_instance(n, seed, 1.1)
        
        # Modo HEURISTICA
        res_h = run_mode_heuristica(n, m, costs, weights, capacities, seed)
        print(f"{n:4d} | {res_h['method']:>12} | {res_h['total_time']:8.3f} | {res_h['heuristic_time']:8.3f} | {res_h['solver_time']:8.3f} | {res_h['primal']:8.1f} | {res_h['dual']:8.1f} | {res_h['status']:>10} | {res_h['feasibility']}")
        
        # Modo EXATO
        res_e = run_mode_exato(n, m, costs, weights, capacities, time_limit)
        print(f"{n:4d} | {res_e['method']:>12} | {res_e['total_time']:8.3f} | {res_e['heuristic_time']:8.3f} | {res_e['solver_time']:8.3f} | {res_e['primal']:8.1f} | {res_e['dual']:8.1f} | {res_e['status']:>10} | {res_e['feasibility']}")
        
        # Modo WARM_START
        res_w = run_mode_warm_start(n, m, costs, weights, capacities, time_limit, seed)
        print(f"{n:4d} | {res_w['method']:>12} | {res_w['total_time']:8.3f} | {res_w['heuristic_time']:8.3f} | {res_w['solver_time']:8.3f} | {res_w['primal']:8.1f} | {res_w['dual']:8.1f} | {res_w['status']:>10} | {res_w['feasibility']}")
        
        print("-" * 95)

if __name__ == "__main__":
    run_tests()
