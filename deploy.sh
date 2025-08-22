#!/bin/bash

# Exit on any error
set -e

echo "Building Docker image..."
docker build . -t connector

echo "Tagging image for ECR..."
docker tag connector:latest 296062557786.dkr.ecr.us-west-2.amazonaws.com/connector:latest

echo "Pushing image to ECR..."
docker push 296062557786.dkr.ecr.us-west-2.amazonaws.com/connector:latest

echo "✅ Successfully deployed connector to ECR!"
