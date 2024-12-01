import json
from math import log
import shelve

count = 0
min = 100000000
max = -100000000000
diff = max-min
vals = set()



with shelve.open("url_id.shelve", writeback=True) as s:
    for key, values in s.items():
        vals.add(0.4+values[3]*0.3)



# Print or use the collected data

print(count)
print(sorted(vals))
print(min)
print(max)