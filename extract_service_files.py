import os
import json

service_path = f'./prowler/providers/aws/services'

# List to store all _client filenames
client_files = []

# Walk through the directory and find all files
for root, dirs, files in os.walk(service_path):
    print(root, dirs, files)
    for file in files:
        if file.endswith('_client.py'):
            # Append only the filename to the list (not the full path)
            client_files.append(file)

# save the client_files to json
with open('aws_service_client_files.json', 'w+') as f:
    json.dump(client_files, f)