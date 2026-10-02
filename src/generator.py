import random
import math
import json
from pathlib import Path

def generate_gap_instance(n: int, seed: int, tightness: float = 1.1):
    """
    Gera uma instância GAP determinística e factível.
    M (número de agentes) é derivado de N.
    Retorna m, n, costs, weights, capacities.
    """
    random.seed(seed)
    
    # Derivando M a partir de N (mínimo 2)
    m = max(2, n // 5)
    
    # Gerando custos e pesos
    costs = []
    weights = []
    for i in range(m):
        costs.append([random.randint(10, 100) for _ in range(n)])
        weights.append([random.randint(5, 50) for _ in range(n)])
        
    # Garantindo factibilidade: criamos uma atribuição aleatória válida
    assigned = {i: [] for i in range(m)}
    for j in range(n):
        # Cada tarefa é atribuída a um agente aleatório
        agent = random.randint(0, m - 1)
        assigned[agent].append(j)
        
    # Definindo as capacidades com base na atribuição secreta + folga (tightness)
    capacities = [0] * m
    for i in range(m):
        base_capacity = sum(weights[i][j] for j in assigned[i])
        # Garante pelo menos capacidade para rodar
        capacities[i] = math.ceil(base_capacity * tightness)
        
    return m, n, costs, weights, capacities

def save_instance(m, n, costs, weights, capacities, base_filename, seed, tightness):
    """
    Salva a instância no formato OR-Library para compatibilidade com TP-II,
    e um arquivo JSON adjacente com os parâmetros.
    """
    txt_path = Path(f"{base_filename}.txt")
    json_path = Path(f"{base_filename}.json")
    
    # Salvando em formato OR-Library estrito (apenas inteiros)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"{m} {n}\n")
        for i in range(m):
            f.write(" ".join(map(str, costs[i])) + "\n")
        for i in range(m):
            f.write(" ".join(map(str, weights[i])) + "\n")
        f.write(" ".join(map(str, capacities)) + "\n")
        
    # Salvando metadados
    params = {
        "n": n,
        "m": m,
        "seed": seed,
        "tightness": tightness
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(params, f, indent=4)
        
    return txt_path, json_path
