import json

def load_default_key(file_path):
    """
    Load the default key from a JSON file.
    If the file is not found or invalid, return the default key [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF].
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get('default_key', [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
    except Exception as e:
        print(f"Error loading default key: {e}. Using default key.")
        return [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

def validate_default_key(default_key):
    """
    Validate that the default key matches [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF].
    Returns True if the key is valid, False otherwise.
    """
    expected_key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    return default_key == expected_key

# Example usage
default_key_file = 'default_key.json'
default_key = load_default_key(default_key_file)

if validate_default_key(default_key):
    print("The default key is valid and matches [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF].")
else:
    print("The default key is invalid or does not match [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF].")
