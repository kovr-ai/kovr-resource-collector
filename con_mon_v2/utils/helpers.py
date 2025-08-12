"""
Helper functions for con_mon - handles display and summary operations.
"""
from typing import List, Tuple, Any
from con_mon.checks.models import Check


def generate_static_result_messages(check: Check) -> tuple[str, str, str]:
    """
    Generate static success, partial, and failure messages for a check based on its properties.
    
    Args:
        check: The Check object containing check configuration
        
    Returns:
        Tuple of (success_message, partial_message, failure_message)
    """
    name = check.name
    description = check.description or ""
    
    # Extract key concepts from the name and description
    if 'github' in name.lower():
        resource_type = "GitHub repositories"
    elif 'aws' in name.lower():
        if 'ec2' in name.lower():
            resource_type = "AWS EC2 resources"
        elif 'iam' in name.lower():
            resource_type = "AWS IAM resources"
        elif 's3' in name.lower():
            resource_type = "AWS S3 resources"
        elif 'cloudwatch' in name.lower():
            resource_type = "AWS CloudWatch resources"
        elif 'cloudtrail' in name.lower():
            resource_type = "AWS CloudTrail resources"
        else:
            resource_type = "AWS resources"
    else:
        resource_type = "resources"
    
    # Generate messages based on the check logic
    operation = check.operation
    expected_value = check.expected_value
    
    if operation.name.value == '==':  # EQUAL
        if expected_value is True:
            success_msg = f"All {resource_type} meet the required condition"
            partial_msg = f"Some {resource_type} meet the required condition"
            failure_msg = f"No {resource_type} meet the required condition"
        elif expected_value is False:
            success_msg = f"All {resource_type} are properly configured"
            partial_msg = f"Some {resource_type} are properly configured"
            failure_msg = f"No {resource_type} are properly configured"
        elif expected_value == 0:
            success_msg = f"All {resource_type} have no issues"
            partial_msg = f"Some {resource_type} have no issues"
            failure_msg = f"{resource_type} have outstanding issues"
        else:
            success_msg = f"All {resource_type} meet the required criteria"
            partial_msg = f"Some {resource_type} meet the required criteria"
            failure_msg = f"No {resource_type} meet the required criteria"
    elif operation.name.value in ['>', '>=']:  # GREATER_THAN, GREATER_THAN_OR_EQUAL
        success_msg = f"All {resource_type} meet the minimum threshold"
        partial_msg = f"Some {resource_type} meet the minimum threshold"
        failure_msg = f"No {resource_type} meet the minimum threshold"
    elif operation.name.value in ['<', '<=']:  # LESS_THAN, LESS_THAN_OR_EQUAL
        success_msg = f"All {resource_type} are within acceptable limits"
        partial_msg = f"Some {resource_type} are within acceptable limits"
        failure_msg = f"No {resource_type} are within acceptable limits"
    elif operation.name.value == '!=':  # NOT_EQUAL
        success_msg = f"All {resource_type} are properly configured"
        partial_msg = f"Some {resource_type} are properly configured"
        failure_msg = f"No {resource_type} are properly configured"
    elif operation.name.value == 'custom':  # CUSTOM
        # For custom checks, generate more specific messages based on description
        if 'protected' in description.lower():
            success_msg = f"All {resource_type} have proper protection enabled"
            partial_msg = f"Some {resource_type} have proper protection enabled"
            failure_msg = f"No {resource_type} have proper protection enabled"
        elif 'security' in description.lower():
            success_msg = f"All {resource_type} meet security requirements"
            partial_msg = f"Some {resource_type} meet security requirements"
            failure_msg = f"No {resource_type} meet security requirements"
        elif 'encrypted' in description.lower():
            success_msg = f"All {resource_type} are properly encrypted"
            partial_msg = f"Some {resource_type} are properly encrypted"
            failure_msg = f"No {resource_type} are properly encrypted"
        elif 'enabled' in description.lower():
            success_msg = f"All {resource_type} have the required feature enabled"
            partial_msg = f"Some {resource_type} have the required feature enabled"
            failure_msg = f"No {resource_type} have the required feature enabled"
        else:
            success_msg = f"All {resource_type} pass the compliance check"
            partial_msg = f"Some {resource_type} pass the compliance check"
            failure_msg = f"No {resource_type} pass the compliance check"
    else:
        success_msg = f"All {resource_type} pass the compliance check"
        partial_msg = f"Some {resource_type} pass the compliance check"
        failure_msg = f"No {resource_type} pass the compliance check"
    
    return success_msg, partial_msg, failure_msg


def generate_result_message(
        check: Check, success_count: int,
        failure_count: int
) -> Tuple[str, str]:
    """
    Generate a static result message based on check properties and result counts.

    Args:
        check: The Check object containing check configuration
        success_count: Number of resources that passed the check
        failure_count: Number of resources that failed the check

    Returns:
        Static result message based on the check outcome
    """
    success_msg, partial_msg, failure_msg = generate_static_result_messages(check)

    # Determine overall result
    if failure_count == 0:
        return 'SUCCESS', success_msg
    elif success_count == 0:
        return 'FAIL', failure_msg
    else:
        return 'PARTIAL', partial_msg

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
    checks_with_errors = []
    
    for check_id, check_name, check_results in executed_check_results:
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
            checks_with_errors.append((check_id, check_name, error_results))
        
        # Determine overall result
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
        
        print(f"{status_emoji} {check_name}: {overall_result} ({success_rate}%)")
        if error_count > 0:
            print(f"   └── {error_count} execution errors, {success_count} passed, {failure_count} failed of {total_count} resources")
        else:
            print(f"   └── {success_count} passed, {failure_count} failed of {total_count} resources")
        print()
    
    # Report checks with execution errors
    if checks_with_errors:
        print("💥 **CHECKS WITH EXECUTION ERRORS**")
        print("=" * 60)
        for check_id, check_name, error_results in checks_with_errors:
            print(f"❌ Check {check_id}: {check_name}")
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
    print(f"   • Execution errors: {sum(len(errors) for _, _, errors in checks_with_errors)}")
    print(f"   • Success rate: {int((total_passed / total_executions * 100)) if total_executions > 0 else 0}%")
    
    if checks_with_errors:
        print(f"   • Checks with errors: {len(checks_with_errors)}")
        print(f"   • Error rate: {int((len(checks_with_errors) / len(executed_check_results) * 100))}%")
