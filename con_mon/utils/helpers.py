"""
Helper functions for con_mon - handles display and summary operations.
"""
from typing import List, Tuple, Any


def print_summary(executed_check_results: List[Tuple[int, str, List[Any]]]):
    """
    Print summary of executed check results.
    
    Args:
        executed_check_results: List of (check_id, check_name, check_results) tuples
    """
    print(f"\n📊 **EXECUTION SUMMARY**")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    total_executions = 0
    
    for check_id, check_name, check_results in executed_check_results:
        success_count = sum(1 for result in check_results if result.passed)
        failure_count = sum(1 for result in check_results if not result.passed)
        total_count = len(check_results)
        
        total_passed += success_count
        total_failed += failure_count
        total_executions += total_count
        
        # Determine overall result
        if failure_count == 0:
            overall_result = 'PASS'
            status_emoji = '✅'
        elif success_count == 0:
            overall_result = 'FAIL'
            status_emoji = '❌'
        else:
            overall_result = 'MIXED'
            status_emoji = '⚠️'
        
        success_rate = int((success_count / total_count * 100)) if total_count > 0 else 0
        print(f"{status_emoji} {check_name}: {overall_result} ({success_rate}%)")
        print(f"   └── {success_count} passed, {failure_count} failed of {total_count} resources")
        print()
    
    print("=" * 60)
    print(f"🎯 **Overall Results:**")
    print(f"   • Total check executions: {total_executions}")
    print(f"   • Successful checks: {total_passed}")
    print(f"   • Failed checks: {total_failed}")
    print(f"   • Success rate: {int((total_passed / total_executions * 100)) if total_executions > 0 else 0}%")
