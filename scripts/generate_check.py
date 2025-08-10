#!/usr/bin/env python3
"""
Script to generate compliance checks from controls using LLM.
"""

from typing import List
from con_mon_v2.compliance.models import CheckResult
from con_mon_v2.utils.llm.generate import (
    generate_checks_for_all_providers,
    evaluate_check_against_rc,
)
from con_mon_v2.compliance import ControlLoader

def check_is_invalid(check_results: List[CheckResult]) -> bool:
    """
    need to validate based on any errors in check results if check should be used in production
    return True if check is invalid
    """
    pass

if __name__ == "__main__":
    controls = ControlLoader().load_all()
    checks = list()
    for control in controls:
        checks = generate_checks_for_all_providers(
            control_name=control.control_name,
            control_text=control.control_text,
            control_title=control.control_long_name,
            control_id=control.id,
        )
        for check in checks:
            check_results = evaluate_check_against_rc(check)
            counter = 0
            while check_is_invalid(check_results):
                fixed_check = generate_checks_for_all_providers(
                    control_name=control.control_name,
                    control_text=control.control_text,
                    control_title=control.control_long_name,
                    control_id=control.id,
                    check_results=check_results,
                )
                counter += 1
                if counter > 3:
                    break
        checks.extend(checks)
    print(f"{len(checks)} checks generated")
