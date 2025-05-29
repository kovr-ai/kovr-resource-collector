# Create Azure AD application
resource "azuread_application" "app" {
  display_name = "kovr-service-principal"
}

# Create service principal
resource "azuread_service_principal" "sp" {
  client_id = azuread_application.app.client_id
}

# Create service principal password
resource "azuread_service_principal_password" "sp_password" {
  service_principal_id = azuread_service_principal.sp.id
}

# Get current subscription
data "azurerm_subscription" "current" {}

# Output the credentials
output "client_id" {
  value     = azuread_application.app.client_id
  sensitive = true
}

output "client_secret" {
  value     = azuread_service_principal_password.sp_password.value
  sensitive = true
}

output "tenant_id" {
  value     = data.azurerm_subscription.current.tenant_id
  sensitive = true
}

output "subscription_id" {
  value     = data.azurerm_subscription.current.subscription_id
  sensitive = true
} 