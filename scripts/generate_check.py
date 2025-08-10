#!/usr/bin/env python3
"""
Script to generate compliance checks from controls using LLM.
"""

from con_mon_v2.utils.llm.generate import (
    generate_checks_for_all_providers,
    evaluate_check_against_rc,
)
from con_mon_v2.compliance import ControlLoader

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
            all_results = evaluate_check_against_rc(check)
        checks.extend(checks)
    print(f"{len(checks)} checks generated")
