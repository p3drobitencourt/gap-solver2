import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from solve_gap import parse_instance
from src.heuristic import regret_greedy_heuristic
from src.validator import validate_solution

def run_tests():
    instances = ['a05100', 'c20400', 'e60900']
    
    print(f"{'Instância':>10} | {'Status':>10} | {'Custo':>8} | {'Tempo (s)':>10} | {'Histórico'}")
    print("-" * 80)
    
    for inst in instances:
        file_path = project_root.parent / inst
        m, n, costs, weights, capacities = parse_instance(file_path)
        
        # Roda Heurística
        is_feasible, x_matrix, exec_time, history = regret_greedy_heuristic(
            n, m, costs, weights, capacities, seed=42
        )
        
        # Validação Independente
        val_feasible, total_cost, msg = validate_solution(
            n, m, costs, weights, capacities, x_matrix
        )
        
        status = "Factível" if (is_feasible and val_feasible) else "Infactível"
        if not val_feasible and is_feasible:
            status = "Erro Validação"
            
        print(f"{inst:>10} | {status:>10} | {total_cost:8.1f} | {exec_time:10.5f} | {history}")
        if status != "Factível":
            print(f"  -> Detalhe: {msg}")

if __name__ == "__main__":
    run_tests()
