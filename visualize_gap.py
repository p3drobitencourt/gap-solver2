import matplotlib.pyplot as plt
import numpy as np

def plot_gap_solution(instance_name, m, n, capacities, weights, x_vars):
    """
    Gera gráficos de barras mostrando a alocação e o uso de capacidade dos agentes.
    """
    used_capacities = [0] * m
    tasks_per_agent = [0] * m
    
    # Extrai os valores das variáveis resolvidas
    for i in range(m):
        for j in range(n):
            # Se a tarefa j foi atribuída ao agente i (valor > 0.5 para lidar com flutuações binárias)
            if x_vars[i, j].varValue is not None and x_vars[i, j].varValue > 0.5:
                used_capacities[i] += weights[i][j]
                tasks_per_agent[i] += 1
                
    agents = np.arange(m)
    
    # Criação da figura com dois subgráficos lado a lado
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # ---------------------------------------------------------
    # Gráfico 1: Utilização de Capacidade (Barras Sobrepostas)
    # ---------------------------------------------------------
    ax1.bar(agents, capacities, color='#d3d3d3', edgecolor='black', label='Capacidade Máxima')
    ax1.bar(agents, used_capacities, color='#2ca02c', alpha=0.8, label='Capacidade Utilizada')
    
    ax1.set_title(f'Instância {instance_name}: Utilização de Capacidade', fontsize=14, pad=15)
    ax1.set_xlabel('ID do Agente', fontsize=12)
    ax1.set_ylabel('Recursos Consumidos', fontsize=12)
    ax1.set_xticks(agents)
    
    # Rotaciona os labels no eixo X se houver muitos agentes (ex: instância de 60 agentes)
    if m > 25:
        ax1.tick_params(axis='x', rotation=90, labelsize=8)
    
    ax1.legend()
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # ---------------------------------------------------------
    # Gráfico 2: Quantidade de Tarefas Atribuídas
    # ---------------------------------------------------------
    bars = ax2.bar(agents, tasks_per_agent, color='#1f77b4', edgecolor='black')
    
    ax2.set_title(f'Instância {instance_name}: Tarefas Atribuídas', fontsize=14, pad=15)
    ax2.set_xlabel('ID do Agente', fontsize=12)
    ax2.set_ylabel('Quantidade de Tarefas', fontsize=12)
    ax2.set_xticks(agents)
    
    if m > 25:
        ax2.tick_params(axis='x', rotation=90, labelsize=8)
        
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adiciona os números acima das barras apenas se houver espaço (poucos agentes)
    if m <= 25:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                     f'{int(height)}', ha='center', va='bottom', fontsize=10)

    # Ajusta o layout para evitar sobreposição
    plt.tight_layout()
    plt.show()