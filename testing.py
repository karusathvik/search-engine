import json
from math import log



with open('bins/bin_a.jsonl', 'r') as file:
    for line in file:
        data = json.loads(line.strip())
        for term in data.values():
            size = len(term)+1
            for t in term:
                t[1] *= log(20000/size)
        sorted_data = sorted(term, key=lambda x: x[1], reverse = True)
        break

# Print or use the collected data

