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
    print(f"🔍 check_is_invalid called with {len(check_results) if check_results else 0} results")
    
    if not check_results:
        print("❌ No check results - considering invalid")
        return True
    
    # Debug: Print all results
    for i, result in enumerate(check_results):
        print(f"   Result {i+1}: passed={result.passed}, error={result.error}")
    
    for check_result in check_results:
        if check_result.passed is not None:
            print(f"✅ Found result with passed={check_result.passed} - considering valid")
            return False
    
    print("❌ All results have passed=None - considering invalid")
    return True

if __name__ == "__main__":
    print("🚀 Starting check generation script...")
    
    controls = ControlLoader().load_all()
    print(f"📋 Loaded {len(controls)} controls")
    
    checks = list()
    
    for control_idx, control in enumerate(controls):
        print(f"\n🎯 Processing control {control_idx + 1}/{len(controls)}: {control.control_name} - {control.control_long_name}")
        
        print("🔄 Generating initial checks for all providers...")
        checks = generate_checks_for_all_providers(
            control_name=control.control_name,
            control_text=control.control_text,
            control_title=control.control_long_name,
            control_id=control.id,
        )
        print(f"✅ Generated {len(checks)} initial checks")
        
        for check_idx, check in enumerate(checks):
            print(f"\n🔍 Processing check {check_idx + 1}/{len(checks)}: {check.name}")
            
            print("📊 Evaluating check against resources...")
            check_results = evaluate_check_against_rc(check)
            print(f"📊 Got {len(check_results)} evaluation results")
            
            current_results = check_results
            counter = 0
            max_attempts = 3
            
            print(f"🔄 Starting regeneration loop (max {max_attempts} attempts)...")
            
            while check_is_invalid(current_results):
                counter += 1
                print(f"\n🔄 Attempt {counter}/{max_attempts}: Check is invalid, regenerating with feedback...")
                
                if counter > max_attempts:
                    print(f"❌ Giving up after {max_attempts} attempts")
                    check = None
                    break
                
                print("🧠 Calling generate_checks_for_all_providers with check_results for learning...")
                print(f"   Passing {len(check_results)} accumulated results as feedback")
                
                improved_checks = generate_checks_for_all_providers(
                    control_name=control.control_name,
                    control_text=control.control_text,
                    control_title=control.control_long_name,
                    control_id=control.id,
                    check_results=check_results,
                )
                
                if not improved_checks:
                    print("❌ No improved checks generated")
                    check = None
                    break
                
                print(f"✅ Generated {len(improved_checks)} improved checks")
                check = improved_checks[0]  # Take first improved check
                print(f"🔧 Using improved check: {check.name}")
                
                print("📊 Evaluating improved check...")
                current_results = evaluate_check_against_rc(check)
                print(f"📊 Got {len(current_results)} new evaluation results")
                
                check_results.extend(current_results)
                print(f"📈 Total accumulated results: {len(check_results)}")
                
            if check is not None:
                print(f"✅ Check {check.name} is valid! Adding to final list")
                checks.append(check)
            else:
                print(f"❌ Check failed validation after {max_attempts} attempts")
        
        print(f"\n🎉 Completed control {control.control_name}")
        # Process only first control for debugging
        print("🛑 Breaking after first control for debugging")
        break
    
    print(f"\n🏁 Final result: {len(checks)} valid checks generated")
