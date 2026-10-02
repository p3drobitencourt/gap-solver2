import os
import json
import hashlib
import argparse
import subprocess
import sys
import csv
from datetime import datetime
from src.generator import generate_gap_instance
from src.experiments import run_experiment, save_results_csv

def get_instance_hash(n, m, costs, weights, capacities):
    data = {"n": n, "m": m, "costs": costs, "weights": weights, "capacities": capacities}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def run_single_n(N, seed, tightness, time_limit, fo_strategy, fo_size, fo_iters):
    os.makedirs("results/official", exist_ok=True)
    instance_name = f"generated_N{N}_seed{seed}_t110"

    print(f"\n[SUBPROCESS N={N}] Gerando instância única {instance_name}...")
    m, n, costs, weights, capacities = generate_gap_instance(N, seed, tightness)
    
    instance_hash = get_instance_hash(n, m, costs, weights, capacities)
    print(f"[SUBPROCESS N={N}] Hash da Instância: {instance_hash}")
    print(f"[SUBPROCESS N={N}] Dimensões: N={n}, M={m}")

    print(f"[SUBPROCESS N={N}] Executando (Orçamento T={time_limit}s)...")
    results = run_experiment(
        instance_name=instance_name,
        n=n,
        m=m,
        costs=costs,
        weights=weights,
        capacities=capacities,
        seed=seed,
        time_limit=time_limit,
        fo_strategy=fo_strategy,
        fo_size=fo_size,
        fo_iters=fo_iters
    )

    # 4. Validação Antes de Salvar
    for row in results:
        if row["Status"] in ["Optimal", "Timeout (Feasible)", "Feasible", "Finished"]:
            if not row["Factibilidade"]:
                raise RuntimeError(f"ERRO DE VALIDAÇÃO: Método {row['Metodo']} tem Status '{row['Status']}' mas Factibilidade é False.")
        
        if row["N"] != n or row["M"] != m:
            raise RuntimeError(f"ERRO DE INSTÂNCIA: Dimensões vazaram no método {row['Metodo']}.")
        
        if row["Orcamento_Tempo"] != time_limit:
            raise RuntimeError(f"ERRO DE ORÇAMENTO: Valor divergente no método {row['Metodo']}.")
            
        if row["Gap"] == 0 or row["Gap"] == 0.0:
            if row["Status"] != "Optimal":
                raise RuntimeError(f"ERRO DE GAP: Gap=0 injetado artificialmente sem provar otimalidade no método {row['Metodo']}.")
                
        row["Instance_Hash"] = instance_hash

    # 5. Salvar CSV individual
    indiv_csv_path = f"results/official/N{N}_seed{seed}.csv"
    save_results_csv(results, indiv_csv_path)
    print(f"[SUBPROCESS N={N}] Concluído com sucesso. Salvo em {indiv_csv_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-single-N", type=int, help="Roda apenas para este N")
    parser.add_argument("--time-limit", type=float, default=60.0, help="Tempo limite para a execução")
    args = parser.parse_args()

    seed = 42
    tightness = 1.10
    fo_strategy = "agent_based"
    fo_size = 3
    fo_iters = 20

    if args.run_single_N is not None:
        run_single_n(args.run_single_N, seed, tightness, args.time_limit, fo_strategy, fo_size, fo_iters)
        return

    print("="*60)
    print("INICIANDO EXECUTOR OFICIAL TP-III (MASTER PROCESS)")
    print("="*60)

    # CONFIGURACAO DO TESTE DE CONTROLE
    test_mode = False

    if test_mode:
        sizes_N = [50]
        time_limit = 5.0
        print("MODO DE TESTE DE CONTROLE ATIVADO (Apenas N=50, T=5s).")
    else:
        sizes_N = [50, 100, 150, 200, 300, 500]
        time_limit = 60.0

    os.makedirs("results/official", exist_ok=True)
    
    completed_Ns = []
    failed_Ns = []
    hashes = {}
    
    for N in sizes_N:
        print(f"\n[MASTER] Iniciando subprocesso para N={N}...")
        cmd = [
            sys.executable, __file__, 
            "--run-single-N", str(N), 
            "--time-limit", str(time_limit)
        ]
        
        try:
            # Não capturamos a saída, deixamos ir para stdout/stderr para streaming ao vivo.
            # O sistema operacional levanta CalledProcessError se falhar.
            result = subprocess.run(cmd, check=True)
            print(f"[MASTER] Subprocesso N={N} concluído com código 0.")
            completed_Ns.append(N)
            
            # Lê o hash salvo
            indiv_csv_path = f"results/official/N{N}_seed{seed}.csv"
            if os.path.exists(indiv_csv_path):
                with open(indiv_csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        hashes[str(N)] = row.get("Instance_Hash", "")
                        break
        except subprocess.CalledProcessError as e:
            print(f"[MASTER] ERRO FATAL no subprocesso N={N}. Código de saída: {e.returncode}")
            failed_Ns.append(N)

    print("\n[MASTER] Consolidando resultados...")
    all_consolidated_results = []
    
    for N in completed_Ns:
        indiv_csv_path = f"results/official/N{N}_seed{seed}.csv"
        if os.path.exists(indiv_csv_path):
            with open(indiv_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                all_consolidated_results.extend(list(reader))
                
    consolidated_csv_path = "results/official/official_experiment.csv"
    if all_consolidated_results:
        keys = all_consolidated_results[0].keys()
        with open(consolidated_csv_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_consolidated_results)
        print(f"CSV consolidado (reconstruído limpo) salvo em: {consolidated_csv_path}")

    json_path = "results/official/official_metadata.json"
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "sizes_configured": sizes_N,
        "sizes_completed": completed_Ns,
        "sizes_failed": failed_Ns,
        "seed": seed,
        "tightness": tightness,
        "time_limit": time_limit,
        "fo_strategy": fo_strategy,
        "fo_neighborhood_size": fo_size,
        "fo_max_iterations": fo_iters,
        "instance_hashes": hashes,
        "version": "TP-III Official Runner v2.0 (Subprocess)"
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"JSON metadados salvo em: {json_path}")
    print("\nFIM.")

if __name__ == "__main__":
    main()
