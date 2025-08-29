from rules.frameworks.framework_registry import framework_registry
from datetime import datetime


class RuleEngine:
    def __init__(self, provider: str, data: dict, framework_id: str = "nist_800_53"):
        self.provider = provider
        self.data = data
        self.framework_id = framework_id
        self.framework = framework_registry.get_framework(framework_id)

        if not self.framework:
            raise ValueError(f"Framework '{framework_id}' not found in registry")

    def process(self):
        report = {
            "provider": self.provider,
            "timestamp": datetime.now().isoformat(),
            "framework": self.framework_id,
            "framework_name": self.framework.framework_name,
            "control_families": {},
            "summary": {
                "total_controls": 0,
                "compliant_controls": 0,
                "non_compliant_controls": 0,
                "partial_controls": 0,
            },
        }

        # Process each control family
        for index, family in enumerate(self.framework.control_families):
            print(
                f"Processing control family: {family.family_id} ({index + 1}/{len(self.framework.control_families)})"
            )
            family_results = {
                "family_id": family.family_id,
                "family_name": family.family_name,
                "controls": {},
                "summary": {
                    "total_controls": 0,
                    "compliant_controls": 0,
                    "non_compliant_controls": 0,
                    "partial_controls": 0,
                },
            }

            # Process each control in the family
            for control in family.get_controls():
                control_result = control.evaluate(self.provider, self.data)
                family_results["controls"][control.control_id] = control_result

                # Update family summary
                family_results["summary"]["total_controls"] += 1
                if control_result["status"] == "COMPLIANT":
                    family_results["summary"]["compliant_controls"] += 1
                elif control_result["status"] == "NON_COMPLIANT":
                    family_results["summary"]["non_compliant_controls"] += 1
                else:
                    family_results["summary"]["partial_controls"] += 1

                # Update overall summary
                report["summary"]["total_controls"] += 1
                if control_result["status"] == "COMPLIANT":
                    report["summary"]["compliant_controls"] += 1
                elif control_result["status"] == "NON_COMPLIANT":
                    report["summary"]["non_compliant_controls"] += 1
                else:
                    report["summary"]["partial_controls"] += 1

            report["control_families"][family.family_id] = family_results

        return report

    def get_available_frameworks(self):
        """Get list of available frameworks"""
        return framework_registry.list_available_frameworks()

    def get_framework_info(self):
        """Get information about the current framework"""
        return framework_registry.get_framework_info(self.framework_id)
