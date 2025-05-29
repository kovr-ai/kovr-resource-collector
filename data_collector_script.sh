#! /bin/sh

# Check if aws environment variables are set
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "AWS_ACCESS_KEY_ID is not set"
    exit
fi

if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "AWS_SECRET_ACCESS_KEY is not set"
    exit
fi

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

# Install requirements
pip install -r data_collector_requirements.txt --user

# Download script
curl -O https://raw.githubusercontent.com/kovr-ai/kovr-resource-collector/refs/heads/main/data_collector.py

# Run data collector
python data_collector.py --provider aws

