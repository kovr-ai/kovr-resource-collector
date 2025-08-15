"""
Helper functions for con_mon - handles display and summary operations.
"""
from typing import List, Tuple, Any
from con_mon.compliance.models import Check
from con_mon.compliance.models.checks import CheckResult


def print_summary(
    executed_check_results: List[
        Tuple[Check, List[CheckResult]]
    ]
):
    """
    Print summary of executed check results.
    
    Args:
        executed_check_results: List of (check, check_results) tuples
                                where check is a Check object with result_summary() method
    """
    print("\n📊 **EXECUTION SUMMARY**")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    total_executions = 0
    checks_with_errors = []
    
    for check, check_results in executed_check_results:
        # Separate clean results from error results
        clean_results = [r for r in check_results if not r.error]
        error_results = [r for r in check_results if r.error]
        
        # Count pass/fail for clean results only
        success_count = sum(1 for result in clean_results if result.passed)
        failure_count = sum(1 for result in clean_results if not result.passed)
        error_count = len(error_results)
        total_count = len(check_results)
        
        total_passed += success_count
        total_failed += failure_count
        total_executions += total_count
        
        # Track checks with errors for separate reporting
        if error_results:
            checks_with_errors.append((check, error_results))
        
        # Use Check.result_summary() for database-driven messages
        result_message = check.result_summary(check_results)
        
        # Determine overall result status
        if error_count > 0:
            overall_result = 'ERROR'
            status_emoji = '💥'
            success_rate = 0  # Error means no meaningful success rate
        elif failure_count == 0:
            overall_result = 'PASS'
            status_emoji = '✅'
            success_rate = int((success_count / total_count * 100)) if total_count > 0 else 0
        elif success_count == 0:
            overall_result = 'FAIL'
            status_emoji = '❌'
            success_rate = 0
        else:
            overall_result = 'MIXED'
            status_emoji = '⚠️'
            success_rate = int((success_count / total_count * 100)) if total_count > 0 else 0
        
        # Display check result with database-driven message
        print(f"{status_emoji} {check.name}: {overall_result} ({success_rate}%)")
        print(f"   └── {result_message}")
        if error_count > 0:
            print(f"   └── {error_count} execution errors, {success_count} passed, {failure_count} failed of {total_count} resources")
        else:
            print(f"   └── {success_count} passed, {failure_count} failed of {total_count} resources")
        print()
    
    # Report checks with execution errors
    if checks_with_errors:
        print("💥 **CHECKS WITH EXECUTION ERRORS**")
        print("=" * 60)
        for check, error_results in checks_with_errors:
            print(f"❌ Check {check.id}: {check.name}")
            print(f"   • {len(error_results)} resources had execution errors")
            
            # Show first error as sample for debugging
            if error_results:
                sample_error = error_results[0]
                print(f"   • Sample error: {sample_error.error}")
            print()
    
    print("=" * 60)
    print(f"🎯 **Overall Results:**")
    print(f"   • Total check executions: {total_executions}")
    print(f"   • Successful checks: {total_passed}")
    print(f"   • Failed checks: {total_failed}")
    print(f"   • Execution errors: {sum(len(errors) for _, errors in checks_with_errors)}")
    print(f"   • Success rate: {int((total_passed / total_executions * 100)) if total_executions > 0 else 0}%")
    
    if checks_with_errors:
        print(f"   • Checks with errors: {len(checks_with_errors)}")
        print(f"   • Error rate: {int((len(checks_with_errors) / len(executed_check_results) * 100))}%")
