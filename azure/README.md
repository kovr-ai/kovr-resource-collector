# Azure Service Principal Generator

This directory contains Terraform configuration and scripts to generate Azure service principal credentials for programmatic access to Azure resources.

## Prerequisites

1. Azure CLI installed and configured
2. Terraform installed
3. Azure subscription with appropriate permissions

## Instructions

1. Open Azure Cloud Shell in the Azure Portal
2. Clone this repository or upload these files to your Cloud Shell
3. Navigate to the directory containing these files:
   ```bash
   cd @azure
   ```
4. Make the script executable:
   ```bash
   chmod +x run.sh
   ```
5. Ensure you're logged into Azure:
   ```bash
   az login
   ```
6. Run the script:
   ```bash
   ./run.sh
   ```

If you get a "No such file or directory" error, make sure:
1. You're in the correct directory (use `pwd` to check)
2. The script file exists (use `ls -la` to check)
3. The script has execute permissions (use `chmod +x run.sh` to add them)

## Troubleshooting

If you encounter any issues:

1. Check if you're logged into Azure:
   ```bash
   az account show
   ```

2. Verify Terraform is installed:
   ```bash
   terraform --version
   ```

3. Check file permissions:
   ```bash
   ls -la run.sh
   ```

4. If needed, manually set permissions:
   ```bash
   chmod +x run.sh
   ```

The script will:
- Initialize Terraform
- Create a service principal
- Generate necessary credentials
- Display the credentials on screen
- Save the credentials to `azure_credentials.txt`

## Security Notes

- The generated credentials will be displayed on screen and saved to a file
- Please send these credentials securely to your service provider
- The service principal will have minimal permissions by default
- You can delete the service principal from Azure Portal when no longer needed

## Output

The script will generate and display:
- Client ID (Application ID)
- Client Secret
- Tenant ID
- Subscription ID

These credentials can be used to authenticate and access Azure resources programmatically. 