import requests
import numpy as np
from itertools import permutations

def fetch_exchange_rates():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    response = requests.get(url)
    return response.json()["rates"]

rates = fetch_exchange_rates()

print(rates)