from urllib import response
from flask import Flask,jsonify, send_from_directory
import requests
import numpy as np
from itertools import permutations

app=Flask(__name__,static_folder='.')

def fetch_exchange_rates():
    
    url="https://api.exchangerate-api.com/v4/latest/USD"
    response=requests.get(url)
    return response.json()['rates']

def build_graph(rates):
    graph={}
    
    for currency_from,rate in rates.items():
        graph[currency_from]={}
        
        for currency_to,rate_to in rates.items():
            graph[currency_from][currency_to]=-np.log(rate_to/rate)
            
    return graph

def bellman_ford(graph,source,threshold=1.00):
    distance={ vertex:float('inf') for vertex in graph }
    predecessor={vertex:None for vertex in graph}
    distance[source]=0
    
    for _ in range( len(graph)-1 ):
        for u in graph:
            for v in graph[u]:
                
                if( distance[v]>distance[u]+graph[u][v] ):
                    distance[v]=distance[u]+graph[u][v]
                    predecessor[v]=u
                    
    max_cycle=None
    max_value=threshold
    
    for u in graph:
        for v in graph[u]:
            
            if( distance[v]>distance[u]+graph[u][v] ):
                
                cycle=get_cycle(predecessor,v)
                cycle_value=calculate_cycle_value(cycle,graph)
                
                if cycle_value>max_value:
                    
                    max_value=cycle_value
                    max_cycle=cycle
                    
    return max_cycle,max_value

def bellman_ford_all_permutations(graph, threshold=1.0):
    max_cycle = None
    max_value = threshold
    
    nodes = list(graph.keys())
    for perm in permutations(nodes):
        distance = {vertex: float("inf") for vertex in graph}
        predecessor = {vertex: None for vertex in graph}
        
        for source in perm:
            distance[source] = 0

            for _ in range(len(graph) - 1):
                for u in perm:
                    for v in graph[u]:
                        if distance[u] + graph[u][v] < distance[v]:
                            distance[v] = distance[u] + graph[u][v]
                            predecessor[v] = u

            for u in graph:
                for v in graph[u]:
                    if distance[u] + graph[u][v] < distance[v]:
                        cycle = get_cycle(predecessor, v)
                        cycle_value = calculate_cycle_value(cycle, graph)
                        if cycle_value > max_value:
                            max_value = cycle_value
                            max_cycle = cycle

    return max_cycle, max_value


def get_cycle(predecessor,start):
    cycle=[]
    visited=set()
    
    current=start
    while current not in visited:
        visited.add(current)
        current=predecessor[current]
        
    cycle_start=current
    
    cycle.append(cycle_start)
    
    current=predecessor[cycle_start]
    
    while current!=cycle_start:
        cycle.append(current) # This append is for the 'cycle' list and not the 'visited' set as in the above loop
        current=predecessor[current]
        
    cycle.append(cycle_start)
    cycle.reverse()
    
    return cycle
    
def calculate_cycle_value(cycle,graph):
    value=1
    
    for i in range( len(cycle)-1 ):
        
        from_currency=cycle[i]
        to_currency=cycle[i+1]
        
        value*=np.exp( -graph[from_currency][to_currency] )
        
    return value

def build_static_graph():
    rates = {
        'USD': {'USD': 1, 'EUR': 0.741, 'GBP': 0.657, 'CHF': 1.061, 'CAD': 1.011},
        'EUR': {'USD': 1.350, 'EUR': 1, 'GBP': 0.888, 'CHF': 1.433, 'CAD': 1.366},
        'GBP': {'USD': 1.521, 'EUR': 1.126, 'GBP': 1, 'CHF': 1.614, 'CAD': 1.538},
        'CHF': {'USD': 0.943, 'EUR': 0.698, 'GBP': 0.620, 'CHF': 1, 'CAD': 0.953},
        'CAD': {'USD': 0.995, 'EUR': 0.732, 'GBP': 0.650, 'CHF': 1.049, 'CAD': 1}
    }
    
    graph = {}
    for currency_from, exchanges in rates.items():
        graph[currency_from] = {}
        for currency_to, rate in exchanges.items():
            graph[currency_from][currency_to] = -np.log(rate)
    return graph

@app.route('/api/arbitrage')
def get_arbitarge():
    #rates=fetch_exchange_rates()
    #graph=build_graph(rates)
    
    graph=build_static_graph()
    
    threshold=1.0001
    
    # max_cycle,max_value=bellman_ford(graph,'USD',threshold)
    
    max_cycle,max_value=bellman_ford_all_permutations(graph,threshold)
    
    if max_cycle:
        
        return jsonify( {
            'cycle':'->'.join(max_cycle),
            'value':max_value
        } )
        
    else:
        return jsonify( {
            'message':'No significant arbitrage detected.'
        } )
        
@app.route('/')
def serve_static_index():
    return send_from_directory('.','index.html')
        
if __name__=='__main__':
    
    app.run(debug=True)