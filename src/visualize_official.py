import os
import csv
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches

def load_data(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def plot_custo_vs_n(data, output_dir):
    ns = sorted(list(set(int(row['N']) for row in data)))
    
    cost_h = []
    cost_e = []
    cost_fo = []
    
    status_e = []
    
    for n in ns:
        for row in data:
            if int(row['N']) == n:
                if row['Metodo'] == 'HEURISTICA':
                    cost_h.append(float(row['Custo_Solucao']))
                elif row['Metodo'] == 'EXATO':
                    cost_e.append(float(row['Custo_Solucao']))
                    status_e.append(row['Status'])
                elif row['Metodo'] == 'FIX_AND_OPTIMIZE':
                    cost_fo.append(float(row['Custo_Solucao']))
                    
    plt.figure(figsize=(10, 6))
    plt.plot(ns, cost_h, marker='o', label='Heurística', color='tab:blue')
    plt.plot(ns, cost_fo, marker='^', label='Fix-and-Optimize', color='tab:green')
    
    # Exato: separar Optimal e Timeout
    e_opt_n, e_opt_c = [], []
    e_time_n, e_time_c = [], []
    for idx, n in enumerate(ns):
        if status_e[idx] == 'Optimal':
            e_opt_n.append(n)
            e_opt_c.append(cost_e[idx])
        else:
            e_time_n.append(n)
            e_time_c.append(cost_e[idx])
            
    # Conecta todos do exato com uma linha fina de background para não quebrar o visual da série
    plt.plot(ns, cost_e, linestyle='-', color='gray', alpha=0.3)
            
    plt.plot(e_opt_n, e_opt_c, marker='s', linestyle='', color='tab:red', label='Exato (Ótimo Comprovado)')
    plt.plot(e_time_n, e_time_c, marker='X', linestyle='', color='tab:orange', markersize=10, label='Exato (Timeout/Factível - Sem prova)')
    
    plt.title('Custo da Solução vs Tamanho da Instância (N)')
    plt.xlabel('Tamanho N (Tarefas)')
    plt.ylabel('Custo da Solução (Minimização)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'custo_vs_n.png'), dpi=300)
    plt.close()

def plot_tempo_vs_n(data, output_dir):
    ns = sorted(list(set(int(row['N']) for row in data)))
    
    time_h, time_e, time_ws, time_fo = [], [], [], []
    
    for n in ns:
        for row in data:
            if int(row['N']) == n:
                if row['Metodo'] == 'HEURISTICA': time_h.append(float(row['Tempo_Total']))
                elif row['Metodo'] == 'EXATO': time_e.append(float(row['Tempo_Total']))
                elif row['Metodo'] == 'WARM_START': time_ws.append(float(row['Tempo_Total']))
                elif row['Metodo'] == 'FIX_AND_OPTIMIZE': time_fo.append(float(row['Tempo_Total']))
                
    plt.figure(figsize=(10, 6))
    plt.plot(ns, time_h, marker='o', label='Heurística')
    plt.plot(ns, time_e, marker='s', label='Exato')
    plt.plot(ns, time_ws, marker='v', label='Warm Start')
    plt.plot(ns, time_fo, marker='^', label='Fix-and-Optimize')
    
    plt.axhline(y=60, color='r', linestyle='--', label='Orçamento do Solver CBC (60s)')
    
    plt.title('Tempo Total (End-to-End) vs Tamanho da Instância (N)\nNota: Tempos > 60s refletem overhead de construção Python e PuLP I/O (MPS/Sol)')
    plt.xlabel('Tamanho N (Tarefas)')
    plt.ylabel('Tempo Total (segundos)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'tempo_vs_n.png'), dpi=300)
    plt.close()

def plot_fo_improvement_vs_n(data, output_dir):
    ns = sorted(list(set(int(row['N']) for row in data)))
    
    ini_cost = []
    fin_cost = []
    
    for n in ns:
        for row in data:
            if int(row['N']) == n and row['Metodo'] == 'FIX_AND_OPTIMIZE':
                ini_cost.append(float(row['FO_Custo_Inicial']))
                fin_cost.append(float(row['FO_Custo_Final']))
                
    x = np.arange(len(ns))
    width = 0.35
    
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, ini_cost, width, label='Custo Inicial (Heurística construtiva)')
    plt.bar(x + width/2, fin_cost, width, label='Custo Final (Fix-and-Optimize)')
    
    for i in range(len(ns)):
        improvement = ini_cost[i] - fin_cost[i]
        plt.text(x[i], max(ini_cost[i], fin_cost[i]) + (max(ini_cost)*0.02), f'Melhoria: {improvement}', ha='center', fontweight='bold')
    
    plt.title('Fix-and-Optimize: Comparativo Custo Inicial vs Final')
    plt.xlabel('Tamanho N (Tarefas)')
    plt.ylabel('Custo da Solução')
    plt.xticks(x, ns)
    
    # Define ylim to give room for text
    plt.ylim(0, max(ini_cost) * 1.15)
    
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fo_improvement_vs_n.png'), dpi=300)
    plt.close()

def plot_exact_status_vs_n(data, output_dir):
    ns = sorted(list(set(int(row['N']) for row in data)))
    
    status_e = []
    for n in ns:
        for row in data:
            if int(row['N']) == n and row['Metodo'] == 'EXATO':
                status_e.append(row['Status'])
                
    colors = ['tab:green' if s == 'Optimal' else 'tab:red' for s in status_e]
    
    plt.figure(figsize=(10, 3))
    plt.scatter(ns, [1]*len(ns), c=colors, s=500, marker='s', edgecolors='black')
    
    opt_patch = mpatches.Patch(color='tab:green', label='Optimal (Ótimo Comprovado)')
    time_patch = mpatches.Patch(color='tab:red', label='Timeout (Solução Factível subótima / Gap Desconhecido)')
    
    plt.yticks([])
    plt.xlabel('Tamanho N (Tarefas)')
    plt.title('Evolução do Status do Algoritmo Exato por Tamanho de Instância')
    plt.legend(handles=[opt_patch, time_patch], loc='lower right')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'exact_status_vs_n.png'), dpi=300)
    plt.close()

def main():
    csv_file = 'results/official/official_experiment.csv'
    output_dir = 'results/official/plots'
    
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(csv_file):
        print(f"Erro: Arquivo {csv_file} não encontrado.")
        return
        
    data = load_data(csv_file)
    print(f"Lidos {len(data)} registros do arquivo oficial.")
    
    plot_custo_vs_n(data, output_dir)
    plot_tempo_vs_n(data, output_dir)
    plot_fo_improvement_vs_n(data, output_dir)
    plot_exact_status_vs_n(data, output_dir)
    
    print(f"Gráficos gerados com sucesso em {output_dir}")

if __name__ == '__main__':
    main()
