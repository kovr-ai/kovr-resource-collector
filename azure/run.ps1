#!/bin/bash

# Check if terraform is installed
if (!(Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Error "Error: terraform is not installed. Please install terraform first."
    exit 1
}

# Check if azure cli is installed
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Error: Azure CLI is not installed. Please install Azure CLI first."
    exit 1
}

# Check if we're logged into Azure
try {
    $null = az account show
}
catch {
    Write-Error "Error: Not logged into Azure. Please run 'az login' first."
    exit 1
}

# Get subscription information
Write-Host "Getting subscription information..."
$SUBSCRIPTION_ID = az account show --query id -o tsv
$TENANT_ID = az account show --query tenantId -o tsv

# Create provider.tf with the subscription information
@"
terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
    }
    azuread = {
      source = "hashicorp/azuread"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = "$SUBSCRIPTION_ID"
  tenant_id       = "$TENANT_ID"
}

provider "azuread" {
  tenant_id = "$TENANT_ID"
}
"@ | Out-File -FilePath provider.tf -Encoding utf8

# Remove any existing .terraform directory and lock file
if (Test-Path .terraform) {
    Remove-Item -Recurse -Force .terraform
}
if (Test-Path .terraform.lock.hcl) {
    Remove-Item -Force .terraform.lock.hcl
}

Write-Host "Initializing Terraform..."
terraform init

Write-Host "Applying Terraform configuration..."
terraform apply -auto-approve

# Get the outputs and format them nicely
Write-Host "`n=== Azure Credentials ==="
Write-Host "Client ID: $(terraform output -raw client_id)"
Write-Host "Client Secret: $(terraform output -raw client_secret)"
Write-Host "Tenant ID: $(terraform output -raw tenant_id)"
Write-Host "Subscription ID: $(terraform output -raw subscription_id)"
Write-Host "========================"

# Save credentials to a file
Write-Host "`nSaving credentials to azure_credentials.txt..."
@"
Client ID: $(terraform output -raw client_id)
Client Secret: $(terraform output -raw client_secret)
Tenant ID: $(terraform output -raw tenant_id)
Subscription ID: $(terraform output -raw subscription_id)
"@ | Out-File -FilePath azure_credentials.txt -Encoding utf8

# Show the contents of the credentials file
Write-Host "`nContents of azure_credentials.txt:"
Get-Content azure_credentials.txt

Write-Host "`nDone! Please send these credentials securely to your service provider." 