# server/utils.py

import json

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