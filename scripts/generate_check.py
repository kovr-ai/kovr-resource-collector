#!/usr/bin/env python3
"""
Script to generate compliance checks from controls using LLM.
"""

from con_mon_v2.compliance import get_csv_loader as compliance_loader
from con_mon_v2.utils.llm.generate import generate_check_for_control


if __name__ == "__main__":
    for control in compliance_loader().load_controls():
        generate_check_for_control(control)
        break
