# server/utils.py

import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kv_store_pb2

def write_dict_to_json(data, filepath):
    """
    Writes a dictionary to a JSON file with pretty formatting.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Dictionary written to {filepath}")
    except Exception as e:
        print(f"Failed to write JSON: {e}")

def dict_to_store(store_dict):
    return [kv_store_pb2.KeyValuePair(key=k, value=v) for k, v in store_dict.items()]

def store_to_dict(kv_list):
    return {kv.key: kv.value for kv in kv_list}

def write_line_to_txt(filepath, line, mode):
    """
    mode: "a" for append, "w" for write
    """

    folder = os.path.dirname(filepath)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
        
    with open(filepath, mode) as f:
        f.write(line + '\n')
