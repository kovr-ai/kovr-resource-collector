#! /bin/sh

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "pip could not be found. Please install it and try again."
    exit
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "curl could not be found. Please install it and try again."
    exit
fi

# Download requirements file using curl
curl -O https://raw.githubusercontent.com/kovr-ai/kovr-resource-collector/refs/heads/main/data_collector_requirements.txt

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install requirements
pip install -r data_collector_requirements.txt

# Download script
curl -O https://raw.githubusercontent.com/kovr-ai/kovr-resource-collector/refs/heads/main/azure/run.ps1
curl -O https://raw.githubusercontent.com/kovr-ai/kovr-resource-collector/refs/heads/main/azure/main.tf

chmod +x run.ps1

# Run terraform
pwsh run.ps1