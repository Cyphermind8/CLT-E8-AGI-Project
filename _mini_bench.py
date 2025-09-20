from src.tools.json_tools_v1 import json_merge, json_sort_values, sort_json_values
import json
print(json.dumps(sort_json_values({'b':[3,2,1],'a':{'y':2,'x':1}}), sort_keys=True))
print(json.dumps(json_sort_values({'x':[3,1,2]}, key='x'), sort_keys=True))
print(json.dumps(json_merge({'a':1,'b':{'x':[1]}}, {'b':{'x':[1,2]},'c':3}), sort_keys=True))
