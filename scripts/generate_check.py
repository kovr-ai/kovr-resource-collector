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
    Validate based on any errors in check results if check should be used in production.
    Return True if check is invalid and should be regenerated.
    
    A check is considered invalid if:
    1. All results failed (no passing results)
    2. There are critical errors (syntax errors, field not found, etc.)
    3. The check logic appears to be fundamentally flawed
    
    Args:
        check_results: List of CheckResult objects from evaluating the check
        
    Returns:
        bool: True if check is invalid and should be regenerated, False if acceptable
    """
    if not check_results:
        return True

    for check_result in check_results:
        if check_result.passed is not None:
            return False
    return True

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
            current_results = check_results
            counter = 0
            while check_is_invalid(current_results):
                check = generate_checks_for_all_providers(
                    control_name=control.control_name,
                    control_text=control.control_text,
                    control_title=control.control_long_name,
                    control_id=control.id,
                    check_results=check_results,
                )
                current_results = evaluate_check_against_rc(check)
                check_results.extend(current_results)
                counter += 1
                if counter > 3:
                    check = None
                    break
            if check is not None:
                checks.append(check)
    print(f"{len(checks)} checks generated")
