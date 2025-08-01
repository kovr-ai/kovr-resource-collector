from providers.service import BaseService, service_class
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.security import SecurityCenter


@service_class
class SecurityService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        self.keyvault_client = KeyVaultManagementClient(credential, subscription_id)
        try:
            self.security_client = SecurityCenter(credential, subscription_id)
        except:
            self.security_client = None
            print("Security Center client not available")

    def process(self):
        data = {
            "key_vaults": {},
            "security_contacts": {},
            "security_alerts": {},
            "security_tasks": {},
        }

        try:
            # Get Key Vaults
            print("Collecting Key Vaults...")
            key_vaults = self.keyvault_client.vaults.list_by_subscription()
            for vault in key_vaults:
                vault_dict = self._key_vault_to_dict(vault)
                data["key_vaults"][vault.id] = vault_dict
                print(f"Found Key Vault: {vault.name}")

        except Exception as e:
            print(f"Error collecting Key Vaults: {str(e)}")
            data["key_vaults"] = {}

        if self.security_client:
            try:
                # Get Security Contacts
                print("Collecting Security Contacts...")
                contacts = self.security_client.security_contacts.list()
                for contact in contacts:
                    contact_dict = self._security_contact_to_dict(contact)
                    data["security_contacts"][contact.name] = contact_dict

            except Exception as e:
                print(f"Error collecting Security Contacts: {str(e)}")
                data["security_contacts"] = {}

            try:
                # Get Security Alerts
                print("Collecting Security Alerts...")
                alerts = self.security_client.alerts.list()
                for alert in alerts:
                    alert_dict = self._security_alert_to_dict(alert)
                    data["security_alerts"][alert.name] = alert_dict

            except Exception as e:
                print(f"Error collecting Security Alerts: {str(e)}")
                data["security_alerts"] = {}

        return data

    def _key_vault_to_dict(self, vault):
        """Convert Key Vault object to dictionary"""
        return {
            "id": vault.id,
            "name": vault.name,
            "location": vault.location,
            "resource_group": vault.id.split('/')[4] if len(vault.id.split('/')) > 4 else None,
            "type": vault.type,
            "vault_uri": vault.properties.vault_uri if vault.properties else None,
            "tenant_id": vault.properties.tenant_id if vault.properties else None,
            "sku": {
                "family": vault.properties.sku.family if vault.properties and vault.properties.sku else None,
                "name": vault.properties.sku.name if vault.properties and vault.properties.sku else None,
            },
            "enabled_for_deployment": vault.properties.enabled_for_deployment if vault.properties else None,
            "enabled_for_disk_encryption": vault.properties.enabled_for_disk_encryption if vault.properties else None,
            "enabled_for_template_deployment": vault.properties.enabled_for_template_deployment if vault.properties else None,
            "soft_delete_retention_in_days": vault.properties.soft_delete_retention_in_days if vault.properties else None,
            "purge_protection_enabled": vault.properties.enable_purge_protection if vault.properties else None,
            "access_policies": [
                {
                    "tenant_id": policy.tenant_id,
                    "object_id": policy.object_id,
                    "application_id": policy.application_id,
                    "permissions": {
                        "keys": policy.permissions.keys if policy.permissions else [],
                        "secrets": policy.permissions.secrets if policy.permissions else [],
                        "certificates": policy.permissions.certificates if policy.permissions else [],
                    }
                }
                for policy in (vault.properties.access_policies or []) if vault.properties
            ],
            "tags": dict(vault.tags) if vault.tags else {},
        }

    def _security_contact_to_dict(self, contact):
        """Convert Security Contact object to dictionary"""
        return {
            "name": contact.name,
            "id": contact.id,
            "type": contact.type,
            "email": contact.email if hasattr(contact, 'email') else None,
            "phone": contact.phone if hasattr(contact, 'phone') else None,
            "alert_notifications": contact.alert_notifications if hasattr(contact, 'alert_notifications') else None,
            "alerts_to_admins": contact.alerts_to_admins if hasattr(contact, 'alerts_to_admins') else None,
        }

    def _security_alert_to_dict(self, alert):
        """Convert Security Alert object to dictionary"""
        return {
            "name": alert.name,
            "id": alert.id,
            "type": alert.type,
            "state": alert.state if hasattr(alert, 'state') else None,
            "report_time": alert.report_time.isoformat() if hasattr(alert, 'report_time') and alert.report_time else None,
            "vendor_name": alert.vendor_name if hasattr(alert, 'vendor_name') else None,
            "alert_name": alert.alert_name if hasattr(alert, 'alert_name') else None,
            "alert_display_name": alert.alert_display_name if hasattr(alert, 'alert_display_name') else None,
            "detected_time": alert.detected_time.isoformat() if hasattr(alert, 'detected_time') and alert.detected_time else None,
            "description": alert.description if hasattr(alert, 'description') else None,
            "remediation_steps": alert.remediation_steps if hasattr(alert, 'remediation_steps') else None,
            "action_taken": alert.action_taken if hasattr(alert, 'action_taken') else None,
            "confidence_score": alert.confidence_score if hasattr(alert, 'confidence_score') else None,
        } 