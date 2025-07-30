class BaseControl:
    def __init__(self, control_id: str, control_name: str, checks: list):
        self.control_id = control_id
        self.control_name = control_name
        self.checks = checks

    def evaluate(self, provider: str, data: dict):
        results = {
            "control_id": self.control_id,
            "control_name": self.control_name,
            "status": "COMPLIANT",  # Default, will aggregate below
            "checks": {}
        }
        
        statuses = []
        for check in self.checks:
            if provider == "aws":
                check_result = check.check_aws(data)
            elif provider == "google_workspace":
                check_result = check.check_google_workspace(data)
            else:
                check_result = {
                    "status": "NOT_APPLICABLE", 
                    "details": "Provider not supported"
                }
            
            results["checks"][check.__class__.__name__] = check_result
            statuses.append(check_result["status"])
        
        # Determine overall status based on individual check results
        if all(s == "COMPLIANT" for s in statuses):
            results["status"] = "COMPLIANT"
        elif any(s == "NON_COMPLIANT" for s in statuses):
            results["status"] = "NON_COMPLIANT"
        else:
            results["status"] = "PARTIAL"
        
        return results 