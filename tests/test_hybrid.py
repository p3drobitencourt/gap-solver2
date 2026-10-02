import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from src.generator import generate_gap_instance
from src.hybrid import fix_and_optimize

def run_tests():
    n, m = 100, 20
    seed = 42
    time_limit = 20.0 # Orçamento global para a matheurística
    
    print(f"Gerando instância teste N={n}, M={m}...")
    _, _, costs, weights, capacities = generate_gap_instance(n, seed, 1.1)
    
    strategies = [
        {"name": "task_random", "size": 15},
        {"name": "agent_based", "size": 3}
    ]
    
    for strat in strategies:
        print(f"\n{'='*60}")
        print(f"Testando F&O | Estratégia: {strat['name']} | Tamanho da Vizinhança: {strat['size']}")
        print(f"{'='*60}")
        
        result = fix_and_optimize(
            n=n, m=m, costs=costs, weights=weights, capacities=capacities,
            global_time_limit=time_limit,
            seed=seed,
            neighborhood_size=strat['size'],
            max_iterations=10,
            strategy=strat['name']
        )
        
        if result["status"] == "Infeasible Initial":
            print("Heurística construtiva falhou em gerar solução inicial.")
            continue
            
        print(f"Status Final        : {result['status']}")
        print(f"Factível (Validador): {result['feasibility']}")
        print(f"Custo Inicial (H)   : {result['initial_cost']:.1f}")
        print(f"Custo Final (F&O)   : {result['final_cost']:.1f}")
        print(f"Melhoria Absoluta   : {result['abs_improvement']:.1f}")
        print(f"Melhoria Percentual : {result['pct_improvement']:.2f}%")
        print(f"Vizinhanças Avaliad.: {result['num_neighborhoods']}")
        print(f"Qtd de Melhorias    : {result['num_improvements']}")
        print(f"Tempo Total         : {result['total_time']:.3f} s")
        print(f"Tempo Médio Subprob.: {result['avg_subproblem_time']:.3f} s")
        print(f"Evolução dos Custos : {result['history_costs']}")

if __name__ == "__main__":
    run_tests()
