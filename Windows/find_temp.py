import requests
import json

d = requests.get('http://localhost:8085/data.json', timeout=3).json()

def find_temp(node):
    result = []
    for c in node.get('Children', []):
        if 'Temperature' in c.get('Text', ''):
            result.append((c['Text'], c.get('Value')))
        result.extend(find_temp(c))
    return result

temps = find_temp(d)
print("Temperature sensors found:")
for name, value in temps:
    print(f"  {name}: {value}")