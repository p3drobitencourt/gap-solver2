import time
import hashlib
import json
from src.generator import generate_gap_instance
from src.heuristic import regret_greedy_heuristic
from src.model_exact import build_gap_model, solve_gap_model
from src.validator import validate_solution
from src.hybrid import fix_and_optimize
import pulp

def get_instance_hash(n, m, costs, weights, capacities):
    data = {"n": n, "m": m, "costs": costs, "weights": weights, "capacities": capacities}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def verify_reproducibility():
    print("--- 10. VERIFICAR REPRODUTIBILIDADE ---")
    m1, n1, c1, w1, cap1 = generate_gap_instance(100, 42, 1.10)
    hash1 = get_instance_hash(n1, m1, c1, w1, cap1)
    
    m2, n2, c2, w2, cap2 = generate_gap_instance(100, 42, 1.10)
    hash2 = get_instance_hash(n2, m2, c2, w2, cap2)
    
    m3, n3, c3, w3, cap3 = generate_gap_instance(100, 43, 1.10)
    hash3 = get_instance_hash(n3, m3, c3, w3, cap3)
    
    print(f"Seed 42 (run 1) Hash: {hash1}")
    print(f"Seed 42 (run 2) Hash: {hash2}")
    print(f"Seed 43         Hash: {hash3}")
    print(f"Mesma seed bate? {hash1 == hash2}")
    print(f"Seeds diferentes batem? {hash1 == hash3}")
    print()

def run_calibration():
    print("--- 4. CALIBRAÇÃO EMPÍRICA DOS TAMANHOS ---")
    sizes = [50, 100, 150, 200, 300, 500]
    seed = 42
    tightness = 1.10
    T_calibracao = 5.0
    
    print(f"{'N':>5} | {'M':>3} | {'Vars':>6} | {'Rest':>4} | {'T_Gen':>6} | {'T_Heur':>6} | {'Ex_Stat':>10} | {'T_Exat':>6} | {'FO_Stat':>10} | {'T_FO':>6}")
    print("-" * 85)
    
    for n in sizes:
        # Geração
        t0 = time.perf_counter()
        m, n_out, costs, weights, capacities = generate_gap_instance(n, seed, tightness)
        t_gen = time.perf_counter() - t0
        
        # Heuristica
        ok_h, x_h, t_heur, _ = regret_greedy_heuristic(n, m, costs, weights, capacities, seed)
        _, cost_h, _ = validate_solution(n, m, costs, weights, capacities, x_h)
        
        # Exato Puro
        prob_ex, x_ex = build_gap_model(f"CALIB_{n}_EX", m, n, costs, weights, capacities)
        status_ex, t_exat, primal_ex, dual_ex, gap_ex, x_res_ex = solve_gap_model(
            prob_ex, x_ex, m, n, T_calibracao, warm_start_matrix=None
        )
        
        # Ajustar status igual ao orquestrador
        real_status_ex = pulp.LpStatus.get(prob_ex.status, "Undefined")
        if t_exat >= T_calibracao - 1.5:
            if prob_ex.status in [pulp.LpStatusOptimal, pulp.LpStatusNotSolved]:
                real_status_ex = "Timeout (Feasible)"
        if real_status_ex == "Not Solved" and prob_ex.status != pulp.LpStatusInfeasible:
            real_status_ex = "Feasible/Timeout"
        
        # FO
        fo_res = fix_and_optimize(
            n, m, costs, weights, capacities, T_calibracao, seed,
            neighborhood_size=3, max_iterations=20, strategy="agent_based"
        )
        t_fo = fo_res["total_time"]
        stat_fo = fo_res["status"]
        
        print(f"{n:5d} | {m:3d} | {n*m:6d} | {n+m:4d} | {t_gen:6.3f} | {t_heur:6.3f} | {real_status_ex:>10} | {t_exat:6.3f} | {stat_fo:>10} | {t_fo:6.3f}")

if __name__ == "__main__":
    verify_reproducibility()
    run_calibration()
