import json
import os

def update_json_file(file_path, replacements):
    with open(file_path, 'r') as f:
        data = json.load(f)

    def replace_placeholders(obj):
        if isinstance(obj, dict):
            return {k: replace_placeholders(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_placeholders(i) for i in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            return os.environ.get(env_var, obj)
        else:
            return obj

    updated_data = replace_placeholders(data)

    with open(file_path, 'w') as f:
        json.dump(updated_data, f, indent=2)

# Update credentials.json
update_json_file('credentials.json', {
    'GOOGLE_CLIENT_ID': 'google-client-id',
    'GOOGLE_CLIENT_SECRET': 'google-client-secret'
})

# Update service-account.json
update_json_file('service-account.json', {
    'PRIVATE_KEY_ID': 'private-key-id',
    'PRIVATE_KEY': 'private-key',
    'CLIENT_EMAIL': 'client-email',
    'CLIENT_ID': 'client-id'
})

print("Credential files updated successfully.")