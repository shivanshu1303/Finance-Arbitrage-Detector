import requests
import numpy as np
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

def fetch_exchange_rates():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    response = requests.get(url)
    return response.json()["rates"]

def filter_major_currencies(rates):
    #major_currencies = {'VND', 'SYP', 'VES', 'AFN', 'IRR', 'CUP', 'YER'}
    major_currencies = {'USD', 'ZAR', 'AUD', 'NZD', 'MXN', 'GBP', 'JPY', 'CHF'}
    filtered_rates = {k: rates[k] for k in major_currencies if k in rates}
    return filtered_rates

def build_graph(rates):
    currencies = list(rates.keys())
    n = len(currencies)
    graph = np.full((n, n), np.inf)

    for i, currency_from in enumerate(currencies):
        for j, currency_to in enumerate(currencies):
            if currency_from != currency_to:
                graph[i, j] = -np.log(rates[currency_from] / rates[currency_to])

    return graph, currencies

def build_static_graph():
    rates = {
        'USD': {'USD': 1, 'EUR': 0.741, 'GBP': 0.657, 'CHF': 1.061, 'CAD': 1.011},
        'EUR': {'USD': 1.350, 'EUR': 1, 'GBP': 0.888, 'CHF': 1.433, 'CAD': 1.366},
        'GBP': {'USD': 1.521, 'EUR': 1.126, 'GBP': 1, 'CHF': 1.614, 'CAD': 1.538},
        'CHF': {'USD': 0.943, 'EUR': 0.698, 'GBP': 0.620, 'CHF': 1, 'CAD': 0.953},
        'CAD': {'USD': 0.995, 'EUR': 0.732, 'GBP': 0.650, 'CHF': 1.049, 'CAD': 1}
    }

    currencies = list(rates.keys())
    n = len(currencies)
    graph = np.full((n, n), np.inf)

    for i, currency_from in enumerate(currencies):
        for j, currency_to in enumerate(currencies):
            if currency_from != currency_to:
                graph[i, j] = -np.log(rates[currency_from][currency_to])

    return graph, currencies

def bellman_ford_permutation(graph, perm, n):
    distance = np.full(n, np.inf)
    predecessor = np.full(n, -1)
    
    for source in perm:
        distance[source] = 0

        for _ in range(n - 1):
            for u in perm:
                for v in range(n):
                    if distance[u] + graph[u, v] < distance[v]:
                        distance[v] = distance[u] + graph[u, v]
                        predecessor[v] = u

    for u in range(n):
        for v in range(n):
            if distance[u] + graph[u, v] < distance[v]:
                cycle = get_cycle(predecessor, v)
                cycle_value = calculate_cycle_value(cycle, graph)
                return cycle, cycle_value

    return None, np.inf

def bellman_ford_all_permutations(graph, currencies, max_workers):
    n = graph.shape[0]
    min_cycle = None
    min_value = np.inf

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(bellman_ford_permutation, graph, perm, n) for perm in permutations(range(n))]
        for future in as_completed(futures):
            cycle, value = future.result()
            if cycle and value < min_value:
                min_value = value
                min_cycle = cycle

    return min_cycle, min_value

def get_cycle(predecessor, start):
    cycle = []
    visited = set()
    current = start
    while current not in visited:
        visited.add(current)
        current = predecessor[current]
    cycle_start = current
    cycle.append(cycle_start)
    current = predecessor[cycle_start]
    while current != cycle_start:
        cycle.append(current)
        current = predecessor[current]
    cycle.append(cycle_start)
    cycle.reverse()
    return cycle

def calculate_cycle_value(cycle, graph):
    value = 0
    for i in range(len(cycle) - 1):
        value += graph[cycle[i], cycle[i + 1]]
    return value

# Main execution
use_real_time_data = True
max_workers = os.cpu_count()  # Get the number of available CPU cores

if use_real_time_data:
    rates = fetch_exchange_rates()
    filtered_rates = filter_major_currencies(rates)
    graph, currencies = build_graph(filtered_rates)
else:
    graph, currencies = build_static_graph()

min_cycle, min_value = bellman_ford_all_permutations(graph, currencies, max_workers)

if min_cycle:
    print("Largest arbitrage detected:")
    cycle_names = [currencies[i] for i in min_cycle]
    print(f"Cycle: {' -> '.join(cycle_names)} with value: {np.exp(-min_value)}")
else:
    print("No significant arbitrage detected")
