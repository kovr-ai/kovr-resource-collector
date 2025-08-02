from providers.service import BaseService, service_class
import random
import uuid
from datetime import datetime, timedelta


@service_class
class SecurityService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        # No real clients needed for mock data

    def process(self):
        data = {
            "key_vaults": {},
            "security_contacts": {},
            "security_alerts": {},
            "security_tasks": {},
        }

        # Generate mock Key Vaults
        print("Generating mock Key Vaults...")
        vault_count = random.randint(2, 5)
        for i in range(vault_count):
            vault_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i%3}/providers/Microsoft.KeyVault/vaults/mock-keyvault-{i}"
            vault_dict = self._generate_mock_key_vault(i)
            data["key_vaults"][vault_id] = vault_dict
            print(f"Generated Key Vault: mock-keyvault-{i}")

        # Generate mock Security Contacts
        print("Generating mock Security Contacts...")
        contact_count = random.randint(1, 3)
        for i in range(contact_count):
            contact_name = f"security-contact-{i}"
            contact_dict = self._generate_mock_security_contact(i)
            data["security_contacts"][contact_name] = contact_dict

        # Generate mock Security Alerts
        print("Generating mock Security Alerts...")
        alert_count = random.randint(3, 12)
        for i in range(alert_count):
            alert_name = f"security-alert-{i}"
            alert_dict = self._generate_mock_security_alert(i)
            data["security_alerts"][alert_name] = alert_dict

        return data

    def _generate_mock_key_vault(self, index):
        """Generate mock Key Vault data"""
        locations = ["eastus", "westus2", "centralus"]
        sku_names = ["standard", "premium"]
        
        creation_time = datetime.now() - timedelta(days=random.randint(30, 730))
        
        # Generate mock access policies
        access_policies = []
        policy_count = random.randint(1, 5)
        for i in range(policy_count):
            access_policies.append({
                "tenant_id": str(uuid.uuid4()),
                "object_id": str(uuid.uuid4()),
                "application_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
                "permissions": {
                    "keys": random.sample(["get", "list", "create", "delete", "backup", "restore", "encrypt", "decrypt"], k=random.randint(1, 4)),
                    "secrets": random.sample(["get", "list", "set", "delete", "backup", "restore"], k=random.randint(1, 3)),
                    "certificates": random.sample(["get", "list", "create", "delete", "import", "backup", "restore"], k=random.randint(1, 3)),
                }
            })
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.KeyVault/vaults/mock-keyvault-{index}",
            "name": f"mock-keyvault-{index}",
            "location": random.choice(locations),
            "resource_group": f"mock-rg-{index%3}",
            "type": "Microsoft.KeyVault/vaults",
            "vault_uri": f"https://mock-keyvault-{index}.vault.azure.net/",
            "tenant_id": str(uuid.uuid4()),
            "sku": {
                "family": "A",
                "name": random.choice(sku_names),
            },
            "enabled_for_deployment": random.choice([True, False]),
            "enabled_for_disk_encryption": random.choice([True, False]),
            "enabled_for_template_deployment": random.choice([True, False]),
            "soft_delete_retention_in_days": random.choice([7, 90]) if random.choice([True, False]) else None,
            "purge_protection_enabled": random.choice([True, False]),
            "access_policies": access_policies,
            "tags": {
                "Environment": random.choice(["Dev", "Test", "Prod"]),
                "CostCenter": f"CC{index%5}",
                "Application": f"App{index%3}",
            },
        }

    def _generate_mock_security_contact(self, index):
        """Generate mock Security Contact data"""
        emails = [
            "security@company.com",
            "admin@company.com", 
            "alerts@company.com",
            "soc@company.com"
        ]
        
        phones = [
            "+1-555-0101",
            "+1-555-0102",
            "+1-555-0103",
            "+1-555-0104"
        ]
        
        return {
            "name": f"security-contact-{index}",
            "id": f"/subscriptions/{self.subscription_id}/providers/Microsoft.Security/securityContacts/security-contact-{index}",
            "type": "Microsoft.Security/securityContacts",
            "email": random.choice(emails),
            "phone": random.choice(phones),
            "alert_notifications": random.choice(["On", "Off"]),
            "alerts_to_admins": random.choice(["On", "Off"]),
        }

    def _generate_mock_security_alert(self, index):
        """Generate mock Security Alert data"""
        alert_names = [
            "Suspicious PowerShell Activity",
            "Malware Detection",
            "Unusual Login Activity",
            "Privilege Escalation Attempt",
            "Data Exfiltration Detected",
            "Brute Force Attack",
            "Suspicious Network Activity",
            "Unauthorized Access Attempt"
        ]
        
        severities = ["High", "Medium", "Low", "Informational"]
        states = ["Active", "Dismissed", "InProgress", "Resolved"]
        vendors = ["Microsoft", "Azure Security Center", "Windows Defender ATP"]
        
        detected_time = datetime.now() - timedelta(hours=random.randint(1, 168))  # Within last week
        report_time = detected_time + timedelta(minutes=random.randint(1, 30))
        
        return {
            "name": f"security-alert-{index}",
            "id": f"/subscriptions/{self.subscription_id}/providers/Microsoft.Security/alerts/security-alert-{index}",
            "type": "Microsoft.Security/alerts",
            "state": random.choice(states),
            "report_time": report_time.isoformat(),
            "vendor_name": random.choice(vendors),
            "alert_name": random.choice(alert_names),
            "alert_display_name": random.choice(alert_names),
            "detected_time": detected_time.isoformat(),
            "description": f"Security alert for {random.choice(alert_names).lower()}",
            "remediation_steps": f"Investigate and remediate {random.choice(alert_names).lower()}",
            "action_taken": random.choice(["None", "Blocked", "Quarantined", "Investigated"]),
            "confidence_score": random.uniform(0.5, 1.0),
            "severity": random.choice(severities),
            "entities": [
                {
                    "type": "Account",
                    "name": f"user{index%10}@company.com"
                },
                {
                    "type": "Host",
                    "name": f"mock-vm-{index%5}"
                }
            ],
            "extended_properties": {
                "source_system": "Azure Security Center",
                "alert_type": random.choice(alert_names),
                "confidence": str(random.randint(70, 100)),
            },
            "intent": random.choice(["Discovery", "Execution", "Persistence", "PrivilegeEscalation", "DefenseEvasion"]),
            "compromised_entity": f"mock-vm-{index%5}",
        } 