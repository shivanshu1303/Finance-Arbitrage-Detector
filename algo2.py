import requests
import numpy as np
from itertools import permutations

# Function to fetch exchange rates from an API
def fetch_exchange_rates():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    response = requests.get(url)
    return response.json()["rates"]

# Function to build the graph from fetched exchange rates
def build_graph(rates):
    currencies = list(rates.keys())
    n = len(currencies)
    graph = np.full((n, n), np.inf)

    for i, currency_from in enumerate(currencies):
        for j, currency_to in enumerate(currencies):
            if currency_from != currency_to:
                graph[i, j] = -np.log(rates[currency_from] / rates[currency_to])

    return graph, currencies

# Function to build the graph from static exchange rates
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

# Bellman-Ford algorithm to detect arbitrage opportunities
def bellman_ford_all_permutations(graph, currencies):
    n = graph.shape[0]
    min_cycle = None
    min_value = np.inf
    
    for perm in permutations(range(n)):
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
                        if cycle_value < min_value:
                            min_value = cycle_value
                            min_cycle = cycle

    return min_cycle, min_value

# Function to reconstruct the cycle from the predecessor list
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

# Function to calculate the cycle value by summing the negative logarithms
def calculate_cycle_value(cycle, graph):
    value = 0
    for i in range(len(cycle) - 1):
        value += graph[cycle[i], cycle[i + 1]]
    return value

# Main execution
use_real_time_data = True

if use_real_time_data:
    rates = fetch_exchange_rates()
    graph, currencies = build_graph(rates)
else:
    graph, currencies = build_static_graph()

min_cycle, min_value = bellman_ford_all_permutations(graph, currencies)

if min_cycle:
    print("Largest arbitrage detected:")
    cycle_names = [currencies[i] for i in min_cycle]
    print(f"Cycle: {' -> '.join(cycle_names)} with value: {np.exp(-min_value)}")
else:
    print("No significant arbitrage detected")
