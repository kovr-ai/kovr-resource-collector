var migrations = {
  checks: [
    {
      "id": "owasp-latest-remove-unnecessary-features-and-components-S3Resource",
      "name": "owasp-latest-remove-unnecessary-features-and-components-S3Resource",
      "description": "",
      "output_statements": {"failure": "The S3 bucket has unnecessary features or public access enabled, increasing the attack surface and potential security risks.", "partial": "Some S3 bucket configurations align with the OWASP check, but others may still expose unnecessary features or public access.", "success": "The S3 bucket has unnecessary features and public access properly disabled or removed."},
      "fix_details": {"description": "If an S3 bucket has unnecessary features or public access enabled, these configurations should be reviewed and adjusted to align with the OWASP check.", "instructions": ["Review the public access block settings for the S3 bucket and ensure that 'block_public_acls', 'block_public_policy', 'ignore_public_acls', and 'restrict_public_buckets' are all set to true.", "Disable website hosting for the S3 bucket if it is not required by setting 'website_enabled' to false.", "Review any other bucket configurations or settings that may enable unnecessary features or public access and disable or remove them as appropriate."], "estimated_time": "15-30 minutes", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for public_access_block in fetched_value:\n        if not (public_access_block.block_public_acls and\n                public_access_block.block_public_policy and\n                public_access_block.ignore_public_acls and\n                public_access_block.restrict_public_buckets):\n            result = False\n            break"}, "field_path": "buckets[*].public_access_block", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.757517",
      "updated_at": "2025-09-02 22:03:57.757529",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-comprehensive-logging-mechanisms-UserResource",
      "name": "owasp-latest-implement-comprehensive-logging-mechanisms-UserResource",
      "description": "",
      "output_statements": {"failure": "Comprehensive logging mechanisms for the UserResource have not been implemented, leaving user account activities unmonitored and increasing the risk of security incidents going undetected.", "partial": "Comprehensive logging mechanisms for the UserResource have been partially implemented, but some critical fields or activities may not be logged, potentially leading to gaps in visibility and incident response capabilities.", "success": "Comprehensive logging mechanisms for the UserResource have been implemented successfully, enabling effective monitoring and incident response."},
      "fix_details": {"description": "To fully implement comprehensive logging mechanisms for the UserResource, audit logging must be enabled and configured to capture relevant user account activities.", "instructions": ["1. Navigate to the Google Cloud Console and select the appropriate project.", "2. Enable the Cloud Audit Logs API for the project.", "3. Configure audit logging for the UserResource by selecting the appropriate log types and log sinks.", "4. Review and customize the log retention policy to ensure logs are retained for the desired period.", "5. Set up log monitoring and alerting to detect and respond to potential security incidents or policy violations."], "estimated_time": "30 minutes", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    # Implement comprehensive logging for user security events\n    if fetched_value:\n        result = True\n    else:\n        result = False"}, "field_path": "security_info.isEnrolledIn2Sv", "resource_type": "con_mon.mappings.google.UserResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.761267",
      "updated_at": "2025-09-02 22:03:57.761275",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-validate-access-controls-on-the-server-side-IAMResource",
      "name": "owasp-latest-validate-access-controls-on-the-server-side-IAMResource",
      "description": "",
      "output_statements": {"failure": "Access controls defined in IAM policies are not properly implemented or violate best practices.", "partial": "Some access controls defined in IAM policies are properly implemented, but others require attention.", "success": "Access controls defined in IAM policies are properly implemented and follow best practices."},
      "fix_details": {"description": "If the check fails or partially passes, it indicates that the access controls defined in IAM policies need to be reviewed and updated to follow best practices.", "instructions": ["Review the IAM policies and their statements to identify any overly permissive or insecure access controls.", "Update the policies to follow the principle of least privilege, granting only the necessary permissions required for specific tasks or roles.", "Implement conditions and resource constraints to further restrict access based on specific criteria, such as IP addresses, time ranges, or resource tags.", "Review and rotate access keys regularly to mitigate the risk of unauthorized access.", "Implement multi-factor authentication (MFA) for privileged user accounts to add an extra layer of security."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            condition = getattr(statement, 'Condition', None)\n            if condition is None:\n                result = False\n                break\n            else:\n                resource = getattr(statement, 'Resource', None)\n                action = getattr(statement, 'Action', None)\n                if resource and action:\n                    if '*' in resource or '*' in action:\n                        result = False\n                        break\n                    else:\n                        result = True\n                else:\n                    result = False\n                    break"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.765109",
      "updated_at": "2025-09-02 22:03:57.765112",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-software-supply-chain-practices-CloudTrailResource",
      "name": "owasp-latest-implement-secure-software-supply-chain-practices-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured to log relevant events or store logs in a secure and immutable location, which can compromise secure software supply chain practices.", "partial": "CloudTrail is partially configured to log relevant events and store logs in a secure and immutable location, but additional configuration is required to fully implement secure software supply chain practices.", "success": "CloudTrail is configured to log relevant events and store logs in a secure and immutable location, enabling secure software supply chain practices."},
      "fix_details": {"description": "To fully implement secure software supply chain practices using CloudTrail, ensure that relevant events are being logged, logs are stored in a secure and immutable location, and log file validation is enabled.", "instructions": ["1. Review the CloudTrail trail configuration and ensure that relevant event selectors are enabled to capture API calls and events related to software deployments and infrastructure changes.", "2. Configure CloudTrail to store logs in an S3 bucket with appropriate access controls and versioning enabled to ensure log immutability.", "3. Enable log file validation to ensure the integrity of CloudTrail logs.", "4. Configure CloudTrail to log events across all regions if your software supply chain spans multiple regions.", "5. Regularly review and analyze CloudTrail logs to monitor for any suspicious or unauthorized activities related to your software supply chain."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for log_file_validation_enabled in fetched_value:\n        if log_file_validation_enabled:\n            result = True\n            break"}, "field_path": "trails[*].log_file_validation_enabled", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.768263",
      "updated_at": "2025-09-02 22:03:57.768265",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-conduct-penetration-testing-CloudTrailResource",
      "name": "owasp-latest-conduct-penetration-testing-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured properly or log file validation is disabled, hindering the ability to conduct comprehensive penetration testing and security analysis.", "partial": "CloudTrail is partially configured to capture relevant events, but some settings may need adjustment to enable comprehensive penetration testing and security analysis.", "success": "CloudTrail is configured to capture relevant events and log file validation is enabled, allowing for effective penetration testing and security analysis."},
      "fix_details": {"description": "To ensure CloudTrail is properly configured for penetration testing and security analysis, you may need to adjust the event selectors, enable log file validation, and configure multi-region trails.", "instructions": ["Review the CloudTrail event selectors and ensure they capture all relevant API calls and events for your resources.", "Enable log file validation to ensure the integrity and completeness of CloudTrail logs.", "Configure multi-region trails if you have resources in multiple AWS regions to ensure comprehensive logging."], "estimated_time": "30 minutes", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for values_list in fetched_value:\n        if 'AWS::CloudTrail::Trail' in values_list:\n            result = True\n            break"}, "field_path": "trails[*].event_selectors[*].data_resources.values[*]", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.770612",
      "updated_at": "2025-09-02 22:03:57.770616",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-log-security-relevant-events-CloudWatchResource",
      "name": "owasp-latest-log-security-relevant-events-CloudWatchResource",
      "description": "",
      "output_statements": {"failure": "CloudWatch is not configured to log and monitor security-relevant events, which may hinder incident response and forensic analysis capabilities.", "partial": "CloudWatch is partially configured to log and monitor security-relevant events, but additional configuration may be required to ensure comprehensive coverage.", "success": "CloudWatch is configured to log and monitor security-relevant events, enabling effective incident response and forensic analysis."},
      "fix_details": {"description": "If CloudWatch is not properly configured to log and monitor security-relevant events, the following steps can be taken to remediate the issue:", "instructions": ["1. Identify the AWS resources and services that generate security-relevant logs (e.g., VPC Flow Logs, AWS WAF logs, CloudTrail logs, etc.).", "2. Create CloudWatch Log Groups to collect and store the identified log sources.", "3. Configure Metric Filters within the Log Groups to extract and monitor specific security-relevant events or patterns.", "4. Set appropriate log retention periods for the Log Groups to ensure logs are available for incident response and forensic analysis.", "5. Configure CloudWatch Alarms to trigger notifications or automated actions based on specific security-relevant events or metrics."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    has_metric_filters = any(count > 0 for count in fetched_value)\n    result = has_metric_filters"}, "field_path": "log_groups[*].metric_filter_count", "resource_type": "con_mon.mappings.aws.CloudWatchResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.773187",
      "updated_at": "2025-09-02 22:03:57.773190",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-centralized-log-management-CloudTrailResource",
      "name": "owasp-latest-implement-centralized-log-management-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured correctly, or log data is not being centralized, hindering log management and analysis capabilities.", "partial": "CloudTrail is partially configured for centralized log management, but some services or regions may not be covered, limiting visibility and analysis capabilities.", "success": "CloudTrail is configured to capture and centralize logs from AWS services, enabling effective log management and analysis."},
      "fix_details": {"description": "If CloudTrail is not configured correctly or log data is not being centralized, follow these steps to remediate the issue:", "instructions": ["1. Create or update an AWS CloudTrail trail to capture logs from all AWS services and regions.", "2. Configure the trail to deliver log files to an Amazon S3 bucket for centralized storage and analysis.", "3. Enable log file validation to ensure log file integrity and completeness.", "4. Configure event selectors to capture specific types of events or data resources based on your organization's requirements.", "5. Enable insights selectors to analyze and detect specific patterns or anomalies in the log data.", "6. Review and update CloudTrail configurations regularly to ensure comprehensive log coverage and alignment with security best practices."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for is_logging in fetched_value:\n        if is_logging:\n            result = True\n            break"}, "field_path": "trails[*].is_logging", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.775865",
      "updated_at": "2025-09-02 22:03:57.775866",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-follow-data-protection-regulations-S3Resource",
      "name": "owasp-latest-follow-data-protection-regulations-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 buckets are not configured in compliance with data protection regulations and industry standards. Review the bucket configurations and implement the recommended fixes.", "partial": "Some S3 buckets are configured in compliance with data protection regulations and industry standards, but others require attention. Review the bucket configurations and implement the recommended fixes.", "success": "All S3 buckets are configured in compliance with data protection regulations and industry standards."},
      "fix_details": {"description": "Ensure that all S3 buckets have appropriate encryption and public access controls enabled to protect sensitive data and comply with data protection regulations.", "instructions": ["Enable server-side encryption for all S3 buckets using a secure encryption algorithm (e.g., AES-256) and a customer-managed or AWS-managed KMS key.", "Configure public access block settings to block public access to buckets and objects, including disabling public ACLs, public bucket policies, and cross-account access.", "Review and update bucket policies and ACLs to restrict access to only authorized users and services.", "Implement logging and monitoring for S3 bucket access and configuration changes.", "Regularly review and update S3 bucket configurations to ensure ongoing compliance with data protection regulations and industry standards."], "estimated_time": "30 minutes to 1 hour per S3 bucket (depending on complexity)", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for bucket_encryption_enabled in fetched_value:\n        if bucket_encryption_enabled:\n            result = True\n        else:\n            result = False\n            break"}, "field_path": "buckets[*].encryption.enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.778315",
      "updated_at": "2025-09-02 22:03:57.778316",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-validate-access-controls-on-the-server-side-CloudTrailResource",
      "name": "owasp-latest-validate-access-controls-on-the-server-side-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail trails and event selectors are not configured to capture and analyze access control-related events, preventing proper validation of server-side access controls.", "partial": "CloudTrail trails and event selectors are partially configured to capture and analyze access control-related events, but additional configuration may be required for comprehensive validation of server-side access controls.", "success": "CloudTrail trails and event selectors are configured to capture and analyze access control-related events, allowing for proper validation of server-side access controls."},
      "fix_details": {"description": "If CloudTrail trails and event selectors are not properly configured to capture and analyze access control-related events, remediation steps are required.", "instructions": ["Review the existing CloudTrail trails and event selectors to identify any gaps in capturing access control-related events.", "Configure event selectors to include relevant data resources and management events related to access control.", "Ensure that the read_write_type parameter is set to capture both read and write events.", "Enable log file validation and configure appropriate log retention policies.", "Set up monitoring and alerting mechanisms to detect and respond to potential access control violations."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for values_list in fetched_value:\n        if 'arn:aws:s3:::' in values_list:\n            result = True\n            break"}, "field_path": "trails[*].event_selectors[*].data_resources.values[*]", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.780666",
      "updated_at": "2025-09-02 22:03:57.780667",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-comprehensive-logging-mechanisms-S3Resource",
      "name": "owasp-latest-implement-comprehensive-logging-mechanisms-S3Resource",
      "description": "",
      "output_statements": {"failure": "S3 bucket logging is not enabled, which may limit visibility into access requests and activities.", "partial": "Some S3 buckets have logging enabled, while others do not, resulting in partial visibility into access requests and activities.", "success": "S3 bucket logging is enabled, providing comprehensive logging mechanisms for monitoring access and activities."},
      "fix_details": {"description": "To enable comprehensive logging for S3 buckets, server access logging must be configured for each bucket.", "instructions": ["1. Open the AWS Management Console and navigate to the S3 service.", "2. Select the bucket for which you want to enable logging.", "3. Go to the 'Properties' tab and click on 'Server access logging'.", "4. Enable logging and specify a target bucket and optional prefix for log file delivery.", "5. Review and save the logging configuration.", "6. Repeat these steps for any other buckets that require logging."], "estimated_time": "5-10 minutes per bucket", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for logging_enabled in fetched_value:\n        if logging_enabled:\n            result = True\n            break"}, "field_path": "buckets[*].logging_enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.782699",
      "updated_at": "2025-09-02 22:03:57.782700",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-configuration-management-processes-IAMResource",
      "name": "owasp-latest-implement-secure-configuration-management-processes-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM policies and associated user access are not being managed through a secure configuration management process, increasing the risk of unauthorized or unintended changes that could introduce vulnerabilities or compliance issues.", "partial": "Some aspects of IAM policy and user access management follow secure configuration management processes, but there are gaps or inconsistencies that need to be addressed.", "success": "IAM policies and associated user access are being managed through a secure configuration management process."},
      "fix_details": {"description": "If the IAM resource is not being managed through a secure configuration management process, the following steps should be taken:", "instructions": ["Establish a formal process for reviewing, testing, and approving IAM policy changes before deployment.", "Implement version control and change tracking for IAM policies.", "Regularly review IAM policies, user access keys, and MFA device assignments for appropriateness and potential risks.", "Ensure that IAM policy changes are properly documented, tested, and approved by appropriate stakeholders before deployment.", "Implement automated monitoring and alerting for unauthorized or high-risk IAM policy changes."], "estimated_time": "2-4 weeks", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            condition = getattr(statement, 'Condition', None)\n            if condition is None:\n                result = False\n                break\n            else:\n                # Implement additional checks on condition to ensure secure configuration\n                pass\n        elif isinstance(statement, dict) and statement.get('Effect') == 'Allow':\n            condition = statement.get('Condition')\n            if condition is None:\n                result = False\n                break\n            else:\n                # Implement additional checks on condition to ensure secure configuration\n                pass"}, "field_path": "policies[].default_version.Document.Statement[*]", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.785215",
      "updated_at": "2025-09-02 22:03:57.785216",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-establish-incident-response-plans-CloudTrailResource",
      "name": "owasp-latest-establish-incident-response-plans-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured properly to support incident response and monitoring requirements.", "partial": "CloudTrail is partially configured, but additional configuration is required to fully support incident response and monitoring.", "success": "CloudTrail is configured to capture and log relevant events, enabling effective incident response and monitoring."},
      "fix_details": {"description": "To ensure CloudTrail is properly configured for incident response, you may need to adjust event selectors, enable log file validation, configure multi-region logging, and integrate with appropriate storage and encryption services.", "instructions": ["Review and update the event selectors to capture relevant management events, data events, and insights.", "Enable log file validation to ensure log integrity and prevent tampering.", "Configure CloudTrail to log events across multiple regions if necessary.", "Integrate CloudTrail with Amazon S3 for secure log storage and AWS KMS for encryption at rest.", "Regularly review and monitor CloudTrail logs for potential security incidents or anomalies."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for is_logging in fetched_value:\n        if is_logging:\n            result = True\n            break"}, "field_path": "trails[*].is_logging", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.787035",
      "updated_at": "2025-09-02 22:03:57.787036",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-follow-data-protection-regulations-IAMResource",
      "name": "owasp-latest-follow-data-protection-regulations-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM policies or user access keys are not configured in compliance with data protection regulations, potentially exposing sensitive data to unauthorized access.", "partial": "Some IAM policies or user access keys are not configured in compliance with data protection regulations, potentially exposing sensitive data to unauthorized access.", "success": "IAM policies and user access keys are configured in compliance with data protection regulations."},
      "fix_details": {"description": "If the check fails or partially passes, it indicates that IAM policies or user access keys are not configured correctly to comply with data protection regulations. This could lead to unauthorized access to sensitive data, potentially resulting in regulatory violations and fines.", "instructions": ["Review IAM policies and identify any overly permissive policies or policies that grant access to sensitive data without proper controls.", "Modify or remove policies that violate data protection regulations, following the principle of least privilege.", "Review user access keys and disable or rotate any keys that are no longer needed or have been compromised.", "Implement additional access controls, such as multi-factor authentication (MFA) and conditional access policies, to further secure access to sensitive data."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            condition = getattr(statement, 'Condition', None)\n            if condition:\n                for condition_key, condition_value in condition.items():\n                    if 'aws:PrincipalOrgPaths' in condition_key:\n                        for org_path in condition_value:\n                            if org_path.startswith('/data-protection/'):\n                                result = True\n                            else:\n                                result = False\n                                break\n                    else:\n                        result = False\n                        break\n            else:\n                result = False\n                break\n        else:\n            continue"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.789266",
      "updated_at": "2025-09-02 22:03:57.789267",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-key-management-S3Resource",
      "name": "owasp-latest-implement-secure-key-management-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 buckets do not have server-side encryption enabled or are using an insecure encryption configuration, violating secure key management practices.", "partial": "Some S3 buckets have secure encryption settings, while others may have issues with key management implementation.", "success": "The S3 bucket(s) have server-side encryption enabled using a secure KMS key, implementing proper key management practices."},
      "fix_details": {"description": "If any S3 buckets are found to have insecure encryption settings or are not using KMS keys for encryption, the configuration needs to be updated to enable server-side encryption with a secure KMS key.", "instructions": ["Identify the S3 buckets with insecure encryption settings or no encryption enabled.", "Create a new KMS key or use an existing secure KMS key for encryption.", "Update the bucket encryption configuration to enable server-side encryption using the secure KMS key.", "Verify that the encryption settings have been applied correctly and all data in the bucket is encrypted using the secure KMS key."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for encryption_enabled in fetched_value:\n        if encryption_enabled:\n            result = True\n            break"}, "field_path": "buckets[].encryption.enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.790957",
      "updated_at": "2025-09-02 22:03:57.790958",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-CloudWatchResource",
      "name": "owasp-latest-implement-comprehensive-monitoring-mechanisms-CloudWatchResource",
      "description": "",
      "output_statements": {"failure": "The AWS CloudWatch resource is not configured with comprehensive monitoring mechanisms, leaving the organization vulnerable to undetected security incidents, unauthorized access attempts, and potential data breaches.", "partial": "The AWS CloudWatch resource has some monitoring mechanisms in place, but additional configurations or enhancements are required to achieve comprehensive monitoring for effective detection and response to security incidents and unauthorized access attempts.", "success": "The AWS CloudWatch resource is configured with comprehensive monitoring mechanisms, including alarms, dashboards, and log analysis, enabling effective detection and response to security incidents and unauthorized access attempts."},
      "fix_details": {"description": "If the AWS CloudWatch resource is not configured with comprehensive monitoring mechanisms, the following steps can be taken to remediate the issue:", "instructions": ["1. Review the existing CloudWatch alarms and ensure they cover critical metrics and resources relevant to security monitoring.", "2. Create additional alarms for monitoring security-related metrics, such as unauthorized access attempts, suspicious user activities, and potential data breaches.", "3. Configure CloudWatch Logs to collect and analyze log data from relevant AWS services and applications for security-related events.", "4. Create CloudWatch Dashboards to visualize and monitor security-related metrics and log data in a centralized view.", "5. Integrate CloudWatch with other security monitoring tools or services for advanced threat detection and incident response capabilities."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for metric_filter_count in fetched_value:\n        if metric_filter_count >= 1:\n            result = True\n            break"}, "field_path": "log_groups[*].metric_filter_count", "resource_type": "con_mon.mappings.aws.CloudWatchResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.793101",
      "updated_at": "2025-09-02 22:03:57.793102",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-logging-mechanisms-CloudTrailResource",
      "name": "owasp-latest-implement-secure-logging-mechanisms-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured to log all relevant events, logs are not being delivered to a secure location, or log file integrity is not being validated.", "partial": "CloudTrail is partially configured to meet secure logging requirements, but some settings need to be adjusted or additional configurations are required.", "success": "CloudTrail is configured to log all management and data events, deliver logs to a secure S3 bucket, and validate log file integrity using log file validation."},
      "fix_details": {"description": "If CloudTrail is not configured correctly, adjustments may be needed to ensure comprehensive logging, secure log delivery, and log file integrity validation.", "instructions": ["1. Enable CloudTrail logging for all regions and configure event selectors to capture management and data events from all AWS services.", "2. Create or specify an Amazon S3 bucket for log delivery, and configure appropriate bucket policies and encryption settings to secure the logs.", "3. Enable log file validation to ensure the integrity of CloudTrail logs.", "4. (Optional) Configure CloudTrail to use AWS Key Management Service (KMS) for additional encryption of log files.", "5. Review and update CloudTrail configurations periodically to ensure compliance with secure logging requirements."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for is_logging in fetched_value:\n        if is_logging:\n            result = True\n            break"}, "field_path": "trails[*].is_logging", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.794800",
      "updated_at": "2025-09-02 22:03:57.794801",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-enforce-least-privileges-CloudTrailResource",
      "name": "owasp-latest-enforce-least-privileges-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured with appropriate event selectors and data resource filters to enforce least privilege. Excessive or unnecessary resource access is being logged.", "partial": "CloudTrail is partially configured with event selectors and data resource filters to enforce least privilege, but some unnecessary resource access is still being logged.", "success": "CloudTrail is configured with appropriate event selectors and data resource filters to enforce least privilege by logging and monitoring access to only the necessary resources and actions."},
      "fix_details": {"description": "If CloudTrail is not properly configured to enforce least privilege, you need to review and update the event selectors and data resource filters for your CloudTrail trails.", "instructions": ["1. Review the existing CloudTrail trails and their event selectors and data resource filters.", "2. Identify any unnecessary or excessive resource access being logged.", "3. Update the event selectors and data resource filters to include only the necessary resources and actions required for specific roles and entities.", "4. Test and validate the updated configurations to ensure least privilege is enforced."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for values_list in fetched_value:\n        if not values_list:\n            continue\n        for value in values_list:\n            if value == '?':\n                result = False\n                break\n        else:\n            result = True\n            break"}, "field_path": "event_selectors[*].data_resources.values[*]", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.796628",
      "updated_at": "2025-09-02 22:03:57.796629",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-authentication-mechanisms-IAMResource",
      "name": "owasp-latest-implement-secure-authentication-mechanisms-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM is not configured with secure authentication mechanisms, leaving the AWS account vulnerable to authentication attacks.", "partial": "IAM has some secure authentication mechanisms configured, but additional measures are recommended for comprehensive protection.", "success": "IAM is configured with secure authentication mechanisms, including MFA, strong password policies, and access key rotation."},
      "fix_details": {"description": "If IAM is not configured with secure authentication mechanisms, you need to enable MFA for all IAM users, enforce strong password policies, and rotate access keys regularly.", "instructions": ["Enable MFA for all IAM users by configuring virtual or hardware MFA devices.", "Set a strong password policy for IAM users, including minimum length, complexity requirements, and periodic rotation.", "Rotate access keys for all IAM users on a regular basis (e.g., every 90 days).", "Review and update IAM policies to enforce least privilege access and restrict sensitive actions."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for mfa_device_type in fetched_value:\n        if mfa_device_type and mfa_device_type.lower() in ['virtual', 'u2f']:\n            result = True\n            break"}, "field_path": "users[].mfa_devices[].type", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.798147",
      "updated_at": "2025-09-02 22:03:57.798148",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-proper-access-control-mechanisms-S3Resource",
      "name": "owasp-latest-implement-proper-access-control-mechanisms-S3Resource",
      "description": "",
      "output_statements": {"failure": "The S3 buckets do not have proper access control mechanisms configured, potentially allowing unauthorized access and operations.", "partial": "Some S3 buckets have proper access control mechanisms configured, while others may be vulnerable to unauthorized access and operations.", "success": "The S3 buckets have proper access control mechanisms configured, ensuring that only authorized users or entities can access and perform operations on the buckets and their contents."},
      "fix_details": {"description": "If the S3 buckets do not have proper access control mechanisms configured, you need to review and update the bucket policies, ACLs, and IAM role assignments to ensure that only authorized users or entities can access and perform operations on the buckets and their contents.", "instructions": ["Review the bucket policies and ensure that they only grant access to authorized users or entities.", "Review the bucket ACLs and ensure that they only grant access to authorized users or entities.", "Review the IAM role assignments and ensure that only authorized roles have access to the S3 buckets.", "Enable the public access block settings for the S3 buckets to prevent public access.", "Regularly review and audit the access control mechanisms to ensure they remain secure and up-to-date."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for public_access_block in fetched_value:\n        if not (public_access_block.block_public_acls and\n                public_access_block.block_public_policy and\n                public_access_block.ignore_public_acls and\n                public_access_block.restrict_public_buckets):\n            result = False\n            break"}, "field_path": "buckets[*].public_access_block", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.800046",
      "updated_at": "2025-09-02 22:03:57.800046",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-comprehensive-logging-mechanisms-CloudTrailResource",
      "name": "owasp-latest-implement-comprehensive-logging-mechanisms-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail trails are not configured to capture comprehensive logs, or log file validation is disabled, or logs are not securely stored.", "partial": "CloudTrail trails are partially configured to capture logs, but some critical events or resources are not included, or log file validation is not enabled, or logs are not securely stored.", "success": "CloudTrail trails are configured to capture comprehensive logs of account activity, including API calls, console actions, and security-related events. Log file validation is enabled, and logs are securely stored in an S3 bucket."},
      "fix_details": {"description": "If CloudTrail trails are not configured correctly or log file validation is disabled, remediation steps are required to ensure comprehensive logging mechanisms are implemented.", "instructions": ["1. Review the existing CloudTrail trails and their event selectors to ensure they capture all relevant API calls, console actions, and security-related events across AWS services and resources.", "2. Enable log file validation for each CloudTrail trail to ensure log integrity and detect potential tampering.", "3. Configure CloudTrail trails to securely store logs in an S3 bucket with appropriate access controls and encryption.", "4. Consider enabling multi-region trails to capture events from all AWS regions.", "5. Regularly review and update CloudTrail configurations to ensure comprehensive logging coverage as new services or resources are added."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for is_logging in fetched_value:\n        if is_logging:\n            result = True\n            break"}, "field_path": "trails[*].is_logging", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.801938",
      "updated_at": "2025-09-02 22:03:57.801939",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-remove-unnecessary-features-and-components-IAMResource",
      "name": "owasp-latest-remove-unnecessary-features-and-components-IAMResource",
      "description": "",
      "output_statements": {"failure": "Unnecessary or overly permissive policies or policy statements were identified in the IAM resource.", "partial": "Some unnecessary or overly permissive policies or policy statements were identified in the IAM resource, but others may still exist.", "success": "No unnecessary policies or policy statements were found in the IAM resource."},
      "fix_details": {"description": "If unnecessary or overly permissive policies or policy statements are identified, they should be reviewed and removed or modified to align with the principle of least privilege.", "instructions": ["Review all IAM policies and their statements, focusing on the 'Action' and 'Resource' fields.", "Identify policies or statements that grant unnecessary or overly broad permissions.", "Remove or modify these policies or statements to restrict access to only the necessary resources and actions.", "Ensure that all remaining policies and statements adhere to the principle of least privilege."], "estimated_time": "30 minutes to 2 hours, depending on the number of policies and statements", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for actions in fetched_value:\n        for action in actions:\n            if action.startswith('*'):\n                result = False\n                break\n        if not result:\n            break"}, "field_path": "policies[].default_version.Document.Statement[].Action[]", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.803415",
      "updated_at": "2025-09-02 22:03:57.803415",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-regularly-review-and-update-security-procedures-IAMResource",
      "name": "owasp-latest-regularly-review-and-update-security-procedures-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM policies have not been reviewed or updated in a timely manner, potentially exposing the organization to security risks and compliance violations.", "partial": "Some IAM policies have been reviewed and updated, but others may still require attention to ensure a comprehensive and up-to-date security posture.", "success": "IAM policies have been reviewed and updated to align with the latest security best practices, address emerging threats, and comply with regulatory requirements."},
      "fix_details": {"description": "Review and update IAM policies to ensure they align with the latest security best practices, address emerging threats, and comply with regulatory requirements.", "instructions": ["Identify all IAM policies and their associated resources", "Review each policy's permissions, conditions, and resource access to identify potential security risks or outdated configurations", "Update or remove policies as needed to address identified issues and align with the latest security best practices", "Implement a regular review and update process for IAM policies to ensure ongoing security and compliance"], "estimated_time": "1-2 hours for initial review and update, with ongoing maintenance as needed", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for actions in fetched_value:\n        if isinstance(actions, list):\n            for action in actions:\n                if action.startswith('iam:'):\n                    result = True\n                    break\n        elif isinstance(actions, str):\n            if actions.startswith('iam:'):\n                result = True\n                break"}, "field_path": "policies[*].default_version.Document.Statement[*].Action", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.805097",
      "updated_at": "2025-09-02 22:03:57.805097",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-use-secure-defaults-IAMResource",
      "name": "owasp-latest-use-secure-defaults-IAMResource",
      "description": "",
      "output_statements": {"failure": "One or more IAM policies have insecure default configurations, granting excessive permissions or enabling unnecessary services.", "partial": "Some IAM policies have secure defaults, but others require review and remediation.", "success": "IAM policies are configured with secure default settings, granting only the necessary permissions and denying all other actions."},
      "fix_details": {"description": "Insecure default IAM policy configurations must be updated to follow the principle of least privilege and disable unnecessary services.", "instructions": ["Review all IAM policies and their default versions.", "Identify policy statements granting overly permissive actions or resources.", "Update the policy documents to restrict permissions to only the required actions and resources.", "Ensure all unnecessary services are explicitly denied in the policies.", "Apply the updated policies and validate the changes."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            if hasattr(statement, 'Action') and '*' in statement.Action:\n                result = False\n                break\n            elif hasattr(statement, 'Resource') and '*' in statement.Resource:\n                result = False\n                break"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.806664",
      "updated_at": "2025-09-02 22:03:57.806664",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-validate-and-sanitize-all-user-input-UserResource",
      "name": "owasp-latest-validate-and-sanitize-all-user-input-UserResource",
      "description": "",
      "output_statements": {"failure": "One or more user input fields in the UserResource are not being properly validated and sanitized, leaving the system vulnerable to injection attacks and other input-related vulnerabilities.", "partial": "Some user input fields in the UserResource are being validated and sanitized, but others are not, leaving the system partially vulnerable to injection attacks and other input-related vulnerabilities.", "success": "All user input fields in the UserResource are properly validated and sanitized, mitigating the risk of injection attacks and other input-related vulnerabilities."},
      "fix_details": {"description": "Implement input validation and sanitization mechanisms for all user-provided data in the UserResource.", "instructions": ["Identify all fields that accept user input, including contact_info.emails[].address, contact_info.phones[].value, and profile_info.languages[].languageCode.", "Implement input validation rules to ensure that user input conforms to expected formats and does not contain malicious characters or patterns.", "Sanitize user input by removing or encoding potentially dangerous characters or patterns before storing or processing the data.", "Update the application code to use the validated and sanitized input values instead of the raw user input.", "Implement regular testing and monitoring to ensure the input validation and sanitization mechanisms are working as intended."], "estimated_time": "2-4 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for email in fetched_value:\n        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$', email):\n            break\n    else:\n        result = True"}, "field_path": "contact_info.emails[].address", "resource_type": "con_mon.mappings.google.UserResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.808359",
      "updated_at": "2025-09-02 22:03:57.808359",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-enforce-least-privilege-principles-IAMResource",
      "name": "owasp-latest-enforce-least-privilege-principles-IAMResource",
      "description": "",
      "output_statements": {"failure": "One or more IAM policies or user access keys violate the principle of least privilege by granting excessive permissions beyond the required scope.", "partial": "Some IAM policies and user access keys adhere to the principle of least privilege, while others grant excessive permissions.", "success": "All IAM policies and user access keys adhere to the principle of least privilege, granting only the necessary permissions required for their intended functions."},
      "fix_details": {"description": "If the check fails or partially passes, it indicates that IAM policies or user access keys grant excessive permissions beyond the required scope. This increases the attack surface and potential for unauthorized access or misuse.", "instructions": ["Review all IAM policies and identify statements granting overly permissive actions or resource access.", "Modify or create new policies with more restrictive permissions, following the principle of least privilege.", "Review user access keys and remove or disable keys with unnecessary permissions.", "Implement regular audits and reviews to ensure ongoing compliance with least privilege principles."], "estimated_time": "1-2 hours for initial review and remediation, ongoing maintenance required", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            if hasattr(statement, 'Action') and '*' in statement.Action:\n                result = False\n                break\n            if hasattr(statement, 'Resource') and '*' in statement.Resource:\n                result = False\n                break\n        elif isinstance(statement, dict):\n            if statement.get('Effect') == 'Allow':\n                if statement.get('Action') and '*' in statement.get('Action'):\n                    result = False\n                    break\n                if statement.get('Resource') and '*' in statement.get('Resource'):\n                    result = False\n                    break"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.810113",
      "updated_at": "2025-09-02 22:03:57.810114",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-validate-access-controls-on-the-server-side-UserResource",
      "name": "owasp-latest-validate-access-controls-on-the-server-side-UserResource",
      "description": "",
      "output_statements": {"failure": "Access controls for the UserResource are not properly implemented on the server-side, allowing unauthorized access or modification of sensitive user data.", "partial": "Access controls for the UserResource are partially implemented on the server-side, but some issues or gaps were identified that could lead to unauthorized access or modification of sensitive user data.", "success": "Access controls for the UserResource are properly implemented on the server-side, ensuring that only authorized users can access and modify sensitive user data."},
      "fix_details": {"description": "If access control issues are identified, it is crucial to review and update the server-side logic and configurations to ensure that only authorized users or entities can access and modify user data based on their assigned privileges and security settings.", "instructions": ["Review the server-side code and configurations related to user authentication, authorization, and access control mechanisms.", "Implement proper checks and validations to ensure that only users with the appropriate administrative privileges or security settings can access and modify sensitive user data.", "Regularly review and update access control policies and configurations to align with the latest security best practices and organizational requirements.", "Implement logging and monitoring mechanisms to detect and respond to potential access control violations or unauthorized access attempts."], "estimated_time": "1-2 hours for initial review and basic fixes, but ongoing maintenance and updates may be required.", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    # Check if the user is enrolled in two-step verification\n    result = fetched_value"}, "field_path": "security_info.isEnrolledIn2Sv", "resource_type": "con_mon.mappings.google.UserResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.811744",
      "updated_at": "2025-09-02 22:03:57.811745",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-provide-security-awareness-training-IAMResource",
      "name": "owasp-latest-provide-security-awareness-training-IAMResource",
      "description": "",
      "output_statements": {"failure": "One or more IAM users have not completed the required security awareness training, and their access is not properly restricted based on training completion status.", "partial": "Some IAM users have completed the required security awareness training, but others have not, and access restrictions based on training completion status are inconsistent.", "success": "All IAM users have completed the required security awareness training, and their access is properly restricted based on training completion status."},
      "fix_details": {"description": "If IAM users are found to have incomplete or missing security awareness training, their access should be restricted until they complete the required training.", "instructions": ["1. Identify IAM users who have not completed the required security awareness training.", "2. Create or update an IAM policy that restricts access for users who have not completed the training.", "3. Attach the policy to the non-compliant users or groups.", "4. Provide the necessary training resources and instructions to the non-compliant users.", "5. Monitor and update user access as they complete the training."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            condition = getattr(statement, 'Condition', None)\n            if condition:\n                for condition_key, condition_value in condition.items():\n                    if condition_key == 'Bool' and 'aws:MultiFactorAuthPresent' in condition_value.values():\n                        result = True\n                        break\n            else:\n                result = True\n                break"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.813478",
      "updated_at": "2025-09-02 22:03:57.813478",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-proper-access-control-mechanisms-UserResource",
      "name": "owasp-latest-implement-proper-access-control-mechanisms-UserResource",
      "description": "",
      "output_statements": {"failure": "Proper access control mechanisms have not been implemented for the UserResource, leaving sensitive data and resources vulnerable to unauthorized access.", "partial": "Access control mechanisms have been partially implemented for the UserResource, but further improvements are required to ensure comprehensive protection against unauthorized access.", "success": "Proper access control mechanisms have been implemented for the UserResource, ensuring that only authorized users can access and perform operations on sensitive data and resources."},
      "fix_details": {"description": "If proper access control mechanisms are not implemented or require improvements, follow these steps to enhance the security posture:", "instructions": ["Review the admin_info fields (isAdmin, isDelegatedAdmin) and organizational_info.orgUnitPath to identify administrative users and organizational unit hierarchy.", "Define and implement role-based access control (RBAC) policies based on the identified administrative users and organizational units.", "Regularly review and update access control policies to ensure they align with the principle of least privilege and reflect changes in user roles and responsibilities.", "Implement additional access control measures, such as attribute-based access control (ABAC) or multi-factor authentication (MFA), as needed for enhanced security."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    if isinstance(fetched_value, bool):\n        if fetched_value:\n            result = True\n        else:\n            # Non-admin users should not have isAdmin set to False\n            result = False\n    else:\n        # Invalid data type for isAdmin field\n        result = False"}, "field_path": "admin_info.isAdmin", "resource_type": "con_mon.mappings.google.UserResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.815040",
      "updated_at": "2025-09-02 22:03:57.815041",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-establish-disaster-recovery-plans-S3Resource",
      "name": "owasp-latest-establish-disaster-recovery-plans-S3Resource",
      "description": "",
      "output_statements": {"failure": "S3 buckets lack essential disaster recovery measures, such as versioning, encryption, logging, or cross-region replication, putting data at risk in the event of a disruptive incident or disaster.", "partial": "Some S3 buckets have disaster recovery measures in place, but others lack essential features like versioning, encryption, logging, or cross-region replication, leaving data partially at risk.", "success": "S3 buckets have adequate disaster recovery measures in place, including versioning, encryption, logging, and cross-region replication."},
      "fix_details": {"description": "To ensure adequate disaster recovery measures for S3 buckets, enable versioning, encryption, logging, and cross-region replication for all buckets.", "instructions": ["Enable versioning for all S3 buckets to maintain a history of object versions and facilitate recovery from accidental deletions or overwrites.", "Enable server-side encryption for all S3 buckets using AWS-managed keys (SSE-S3) or customer-managed keys (SSE-KMS) to protect data at rest.", "Enable access logging for all S3 buckets to maintain a detailed record of access requests for auditing and forensic purposes.", "Configure cross-region replication for critical S3 buckets to replicate data to a different AWS region, ensuring data availability and enabling recovery in case of a regional disaster."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for versioning_status in fetched_value:\n        if versioning_status == 'Enabled':\n            result = True\n            break"}, "field_path": "buckets[*].versioning_status", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.816650",
      "updated_at": "2025-09-02 22:03:57.816651",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-regularly-review-and-update-configurations-S3Resource",
      "name": "owasp-latest-regularly-review-and-update-configurations-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 bucket configurations are outdated or insecure, posing potential risks.", "partial": "Some S3 bucket configurations are up-to-date, but others require review and updates.", "success": "All S3 bucket configurations are up-to-date and aligned with security best practices."},
      "fix_details": {"description": "Review and update S3 bucket configurations to align with security best practices and address any identified issues.", "instructions": ["Identify S3 buckets with outdated or insecure configurations based on the security check findings.", "Update encryption settings to use the latest and most secure encryption algorithms and key management practices.", "Configure public access blocks to restrict public access and prevent accidental data exposure.", "Enable logging and versioning for auditing and data recovery purposes.", "Review and update any other relevant S3 bucket configurations based on the latest security guidelines."], "estimated_time": "30 minutes to 2 hours, depending on the number of S3 buckets and configurations to review and update.", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for encryption_enabled in fetched_value:\n        if encryption_enabled:\n            result = True\n            break"}, "field_path": "buckets[*].encryption.enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.818076",
      "updated_at": "2025-09-02 22:03:57.818076",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-monitor-for-security-advisories-CloudTrailResource",
      "name": "owasp-latest-monitor-for-security-advisories-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured to log relevant events and data resources, and no process is in place to monitor for security advisories from external sources.", "partial": "CloudTrail is partially configured to log relevant events and data resources, but a comprehensive process for monitoring security advisories from external sources is missing.", "success": "CloudTrail is configured to log relevant events and data resources, and a process is in place to monitor for security advisories from external sources."},
      "fix_details": {"description": "To address this security check, you need to establish a process for monitoring security advisories from software vendors, security researchers, and other relevant sources.", "instructions": ["Identify the software and services used within your organization and their respective vendors or sources for security advisories.", "Subscribe to mailing lists, RSS feeds, or other notification channels provided by these vendors or sources.", "Implement a process for reviewing and acting upon received security advisories, such as patching or mitigating identified vulnerabilities.", "Consider using a centralized vulnerability management solution to streamline the process of monitoring and addressing security advisories."], "estimated_time": "1-2 hours for initial setup, ongoing effort for monitoring and addressing advisories", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for is_logging in fetched_value:\n        if is_logging:\n            result = True\n            break"}, "field_path": "trails[*].is_logging", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.819643",
      "updated_at": "2025-09-02 22:03:57.819643",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-monitor-for-suspicious-activities-CloudTrailResource",
      "name": "owasp-latest-monitor-for-suspicious-activities-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured to capture and monitor relevant API calls and events, hindering the ability to detect suspicious activities across your AWS account.", "partial": "CloudTrail is partially configured to capture and monitor API calls and events, but additional configuration is required to ensure comprehensive monitoring for suspicious activities.", "success": "CloudTrail is configured to capture and monitor relevant API calls and events, enabling effective detection of suspicious activities across your AWS account."},
      "fix_details": {"description": "If CloudTrail is not properly configured to monitor for suspicious activities, you need to review and update the trail settings and event selectors.", "instructions": ["1. Review the existing CloudTrail trails and event selectors to identify any gaps in monitoring coverage.", "2. Update the event selectors to include relevant data resources and event types that should be monitored for suspicious activities.", "3. Ensure that log file validation is enabled for integrity verification.", "4. Configure multi-region trails if you need to monitor activities across multiple AWS regions.", "5. Integrate CloudTrail with other AWS services like S3 for log storage and analysis.", "6. Set up alerts and notifications for specific event patterns or anomalies."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for values_list in fetched_value:\n        if 'AWS::Lambda::Function' in values_list and 'AWS::S3::Object' in values_list:\n            result = True\n            break"}, "field_path": "trails[*].event_selectors[*].data_resources.values[*]", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.821137",
      "updated_at": "2025-09-02 22:03:57.821137",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-S3Resource",
      "name": "owasp-latest-implement-comprehensive-monitoring-mechanisms-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 buckets do not have logging enabled or have public access enabled, increasing the risk of security incidents and unauthorized access going undetected.", "partial": "Some S3 buckets have logging enabled and public access restricted, while others do not, resulting in partial implementation of comprehensive monitoring mechanisms.", "success": "All S3 buckets have logging enabled, and public access is appropriately restricted, ensuring comprehensive monitoring and security."},
      "fix_details": {"description": "To fully implement comprehensive monitoring mechanisms for S3 buckets, ensure that logging is enabled for all buckets and that public access is appropriately restricted.", "instructions": ["1. Review the list of S3 buckets and identify those without logging enabled or with public access enabled.", "2. For buckets without logging enabled, enable server access logging and configure a log bucket to store the access logs.", "3. For buckets with public access enabled, review the public access settings and apply appropriate restrictions using the public access block settings.", "4. Continuously monitor the S3 access logs and public access settings to detect and respond to any security incidents or unauthorized access attempts."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for logging_enabled in fetched_value:\n        if logging_enabled:\n            result = True\n            break"}, "field_path": "buckets[*].logging_enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.822542",
      "updated_at": "2025-09-02 22:03:57.822543",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-IAMResource",
      "name": "owasp-latest-implement-comprehensive-monitoring-mechanisms-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM policies, user access keys, and MFA devices are not being monitored effectively, leaving the organization vulnerable to unauthorized access and potential security incidents.", "partial": "Some aspects of IAM policies, user access keys, and MFA devices are being monitored, but there are gaps in the monitoring coverage, potentially leaving the organization exposed to certain types of security incidents.", "success": "IAM policies, user access keys, and MFA devices are being monitored effectively for unauthorized access attempts and potential security incidents."},
      "fix_details": {"description": "If the monitoring mechanisms for IAM policies, user access keys, and MFA devices are found to be inadequate, the following steps can be taken to improve the monitoring coverage:", "instructions": ["Implement centralized logging and monitoring for all IAM policy changes, including policy creation, modification, and deletion.", "Monitor user access key usage, including last used date, region, and service, and rotate or disable inactive or unused access keys.", "Monitor MFA device assignments and usage, and enforce MFA for all privileged user accounts.", "Integrate IAM monitoring with a Security Information and Event Management (SIEM) solution for centralized analysis and correlation of security events.", "Establish alerting and notification mechanisms for suspicious or unauthorized activities related to IAM policies, user access keys, and MFA devices."], "estimated_time": "1-2 hours for initial setup, ongoing monitoring and maintenance", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            if hasattr(statement, 'Action') and 'iam:*' in statement.Action:\n                if hasattr(statement, 'Resource') and '*' in statement.Resource:\n                    result = True\n                    break"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.824137",
      "updated_at": "2025-09-02 22:03:57.824137",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-encryption-for-data-in-transit-S3Resource",
      "name": "owasp-latest-implement-encryption-for-data-in-transit-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 buckets do not have encryption for data in transit enabled using SSL/TLS.", "partial": "Some S3 buckets have encryption for data in transit enabled using SSL/TLS, but others do not.", "success": "All S3 buckets have encryption for data in transit enabled using SSL/TLS."},
      "fix_details": {"description": "For S3 buckets that do not have encryption for data in transit enabled, the encryption settings need to be updated.", "instructions": ["1. Open the AWS Management Console and navigate to the S3 service.", "2. Select the bucket that needs encryption for data in transit enabled.", "3. Go to the 'Properties' tab and click on 'Default encryption'.", "4. Enable 'AWS-managed key (SSE-S3)' or 'AWS Key Management Service key (SSE-KMS)' encryption.", "5. Save the changes to apply the encryption settings."], "estimated_time": "5-10 minutes per bucket", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for bucket_encryption in fetched_value:\n        if bucket_encryption and bucket_encryption.enabled:\n            result = True\n            break"}, "field_path": "buckets[].encryption.enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.825302",
      "updated_at": "2025-09-02 22:03:57.825303",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-enforce-password-policies-IAMResource",
      "name": "owasp-latest-enforce-password-policies-IAMResource",
      "description": "",
      "output_statements": {"failure": "The IAM password policies do not enforce strong password requirements, leaving the system vulnerable to weak or easily guessable passwords.", "partial": "The IAM password policies partially enforce strong password requirements, but some critical aspects are missing or not properly configured.", "success": "The IAM password policies enforce strong password requirements, including minimum length, complexity rules, expiration periods, and restrictions on password reuse."},
      "fix_details": {"description": "If the IAM password policies do not meet the required standards, they need to be updated or created to enforce strong password requirements.", "instructions": ["Review the existing IAM password policies and identify any missing or inadequate requirements.", "Create a new IAM password policy or update the existing one to include the necessary requirements, such as minimum password length, complexity rules, expiration periods, and restrictions on password reuse.", "Attach the updated or new IAM password policy to the relevant IAM users or groups.", "Communicate the new password policy requirements to users and provide guidance on updating their passwords accordingly."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            condition = getattr(statement, 'Condition', None)\n            if condition:\n                if 'PasswordPolicy' in condition:\n                    password_policy = condition['PasswordPolicy']\n                    min_length = password_policy.get('MinimumPasswordLength', 0)\n                    require_symbols = password_policy.get('RequireSymbols', False)\n                    require_numbers = password_policy.get('RequireNumbers', False)\n                    require_uppercase = password_policy.get('RequireUppercaseCharacters', False)\n                    require_lowercase = password_policy.get('RequireLowercaseCharacters', False)\n                    max_age = password_policy.get('MaxPasswordAge', 0)\n                    password_reuse_prevention = password_policy.get('PasswordReusePrevention', 0)\n                    if min_length >= 8 and require_symbols and require_numbers and require_uppercase and require_lowercase and max_age <= 90 and password_reuse_prevention >= 24:\n                        result = True\n                        break"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.826959",
      "updated_at": "2025-09-02 22:03:57.826960",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-regularly-review-and-update-security-policies-IAMResource",
      "name": "owasp-latest-regularly-review-and-update-security-policies-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM policies have not been reviewed or updated in a timely manner, potentially exposing the organization to security risks.", "partial": "Some IAM policies have been reviewed and updated, but others may require attention to ensure compliance with security requirements.", "success": "IAM policies are regularly reviewed and updated to align with the organization's security requirements and industry best practices."},
      "fix_details": {"description": "If IAM policies are found to be outdated or non-compliant, they should be reviewed and updated to align with the organization's security requirements and industry best practices.", "instructions": ["Establish a regular review schedule for IAM policies (e.g., quarterly, annually).", "Review each IAM policy's creation date, last update date, and attached entities (users, roles, groups).", "Assess if the policy's permissions and access controls align with the organization's security requirements and industry best practices.", "Update or create new policies as needed, ensuring proper access controls and least privilege principles are applied.", "Communicate policy changes to relevant stakeholders and provide training if necessary.", "Monitor and audit IAM policy changes and access activities for ongoing compliance."], "estimated_time": "The time required for reviewing and updating IAM policies can vary depending on the number of policies, their complexity, and the organization's size. It may take several hours to several days for a comprehensive review and update process.", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\n# Check if any policy was updated within the last 365 days\ntoday = datetime.datetime.now().date()\none_year_ago = today - datetime.timedelta(days=365)\n\nif fetched_value is not None:\n    for update_date in fetched_value:\n        if update_date is not None:\n            update_date = update_date.date()\n            if update_date >= one_year_ago:\n                result = True\n                break"}, "field_path": "policies[].update_date", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.828642",
      "updated_at": "2025-09-02 22:03:57.828642",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-use-secure-defaults-CloudTrailResource",
      "name": "owasp-latest-use-secure-defaults-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured with secure defaults, potentially missing critical API events or logging to an insecure location.", "partial": "CloudTrail is partially configured with secure defaults, but some settings may need to be adjusted to ensure comprehensive event logging and secure storage.", "success": "CloudTrail is configured with secure defaults, capturing all relevant API events and logging them to a secure S3 bucket."},
      "fix_details": {"description": "If CloudTrail is not configured with secure defaults, several settings need to be adjusted to ensure comprehensive event logging and secure storage.", "instructions": ["Enable log file validation to ensure log file integrity", "Configure event selectors to capture all relevant API events, including management events and read/write operations", "Include global service events to capture activities across all AWS services", "Set up a secure S3 bucket and prefix for log storage, with appropriate access controls and encryption", "Enable multi-region trail if operating across multiple AWS regions"], "estimated_time": "30 minutes", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for log_file_validation_enabled in fetched_value:\n        if log_file_validation_enabled:\n            result = True\n            break"}, "field_path": "trails[*].log_file_validation_enabled", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.829870",
      "updated_at": "2025-09-02 22:03:57.829871",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-logging-mechanisms-S3Resource",
      "name": "owasp-latest-implement-secure-logging-mechanisms-S3Resource",
      "description": "",
      "output_statements": {"failure": "S3 bucket access logging is not enabled, which violates the secure logging mechanisms requirement.", "partial": "Some S3 buckets have access logging enabled, while others do not. Secure logging mechanisms are partially implemented.", "success": "S3 bucket access logging is enabled, ensuring secure logging mechanisms are implemented."},
      "fix_details": {"description": "To fully implement secure logging mechanisms for AWS S3 buckets, access logging must be enabled for all buckets.", "instructions": ["1. Open the AWS Management Console and navigate to the S3 service.", "2. Select the bucket for which you want to enable access logging.", "3. Click on the 'Properties' tab, and then click on the 'Server access logging' section.", "4. Enable access logging by selecting a target bucket and prefix for the log files.", "5. Repeat steps 2-4 for all remaining buckets that do not have access logging enabled."], "estimated_time": "10-15 minutes per bucket", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for logging_enabled in fetched_value:\n        if logging_enabled:\n            result = True\n            break"}, "field_path": "buckets[*].logging_enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.831030",
      "updated_at": "2025-09-02 22:03:57.831030",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-configuration-management-processes-CloudTrailResource",
      "name": "owasp-latest-implement-secure-configuration-management-processes-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured correctly, which may lead to unauthorized or unintended changes going undetected, compromising system integrity and security.", "partial": "CloudTrail is partially configured, but some settings may need to be adjusted to fully support secure configuration management processes.", "success": "CloudTrail is configured correctly to track and monitor changes made to AWS resources, supporting secure configuration management processes."},
      "fix_details": {"description": "To fully implement secure configuration management processes using CloudTrail, ensure that CloudTrail is enabled, configured to log all management events, and integrated with appropriate monitoring and alerting systems.", "instructions": ["1. Enable CloudTrail for all regions and configure it to log all management events.", "2. Configure CloudTrail to log data events for specific resource types that are critical to your organization.", "3. Configure CloudTrail to deliver logs to a secure and centralized S3 bucket.", "4. Enable log file validation to ensure log integrity.", "5. Configure CloudTrail to send logs to a monitoring and alerting system (e.g., CloudWatch) to detect and respond to unauthorized or unintended changes.", "6. Implement processes to review CloudTrail logs regularly and investigate any suspicious activity."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for log_file_validation_enabled in fetched_value:\n        if log_file_validation_enabled:\n            result = True\n            break"}, "field_path": "trails[*].log_file_validation_enabled", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.832359",
      "updated_at": "2025-09-02 22:03:57.832360",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-use-secure-defaults-S3Resource",
      "name": "owasp-latest-use-secure-defaults-S3Resource",
      "description": "",
      "output_statements": {"failure": "The S3 bucket is not configured with secure defaults, potentially exposing sensitive data to unauthorized access.", "partial": "Some aspects of the S3 bucket configuration adhere to secure defaults, but there are still areas that need improvement.", "success": "The S3 bucket is configured with secure defaults, including encryption, public access restrictions, versioning, and logging."},
      "fix_details": {"description": "If the S3 bucket is not configured with secure defaults, the following steps should be taken to remediate the issue:", "instructions": ["Enable encryption for the S3 bucket using AWS-managed keys (SSE-S3) or customer-managed keys (SSE-KMS).", "Configure the S3 bucket's public access block to block public access control lists (ACLs), block public bucket policies, ignore public ACLs, and restrict public bucket access.", "Enable versioning for the S3 bucket to protect against accidental deletion or overwrites.", "Enable server access logging for the S3 bucket to capture access requests for audit and analysis purposes."], "estimated_time": "15 minutes", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for encryption_enabled in fetched_value:\n        if encryption_enabled:\n            result = True\n        else:\n            result = False\n            break"}, "field_path": "buckets[*].encryption.enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.833535",
      "updated_at": "2025-09-02 22:03:57.833536",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-monitor-for-suspicious-activities-CloudWatchResource",
      "name": "owasp-latest-monitor-for-suspicious-activities-CloudWatchResource",
      "description": "",
      "output_statements": {"failure": "CloudWatch alarms and log monitoring are not configured to detect and alert on suspicious activities across AWS resources and applications.", "partial": "CloudWatch alarms and log monitoring are partially configured to detect and alert on suspicious activities across AWS resources and applications.", "success": "CloudWatch alarms and log monitoring are configured to detect and alert on suspicious activities across AWS resources and applications."},
      "fix_details": {"description": "To fully implement the 'owasp-latest-monitor-for-suspicious-activities' security check using AWS CloudWatch, you need to configure CloudWatch alarms and log monitoring to detect and alert on suspicious activities.", "instructions": ["1. Identify the AWS resources and applications that need to be monitored for suspicious activities.", "2. Define the metrics and log events that indicate suspicious activities for each resource or application.", "3. Create CloudWatch alarms with appropriate thresholds and alarm actions (e.g., sending notifications, triggering AWS Lambda functions) for the identified metrics.", "4. Configure CloudWatch log monitoring and metric filters to capture and analyze relevant log events for suspicious activities.", "5. Set up alarm notifications and response procedures to investigate and mitigate any detected suspicious activities."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for alarm_actions in fetched_value:\n        for action in alarm_actions:\n            if action.startswith('arn:aws:sns:'):\n                result = True\n                break"}, "field_path": "alarms[*].alarm_actions", "resource_type": "con_mon.mappings.aws.CloudWatchResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.834870",
      "updated_at": "2025-09-02 22:03:57.834871",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-data-masking-S3Resource",
      "name": "owasp-latest-implement-data-masking-S3Resource",
      "description": "",
      "output_statements": {"failure": "The S3 bucket(s) do not have encryption enabled or have public access allowed, failing to implement data masking for sensitive data.", "partial": "Some S3 buckets have encryption enabled and restricted public access, while others do not, partially implementing data masking.", "success": "The S3 bucket(s) have encryption enabled and public access is appropriately restricted, implementing data masking for sensitive data."},
      "fix_details": {"description": "To fully implement data masking for S3 buckets, encryption must be enabled, and public access must be restricted.", "instructions": ["1. Enable server-side encryption (SSE-S3 or SSE-KMS) for all S3 buckets containing sensitive data.", "2. Configure bucket policies and access controls to restrict public access to authorized users and applications only.", "3. Enable the S3 Block Public Access settings to prevent future public access grants.", "4. Regularly review and audit S3 bucket configurations to ensure data masking controls remain in place."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for encryption_enabled in fetched_value:\n        if encryption_enabled:\n            result = True\n            break"}, "field_path": "buckets[*].encryption.enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.836027",
      "updated_at": "2025-09-02 22:03:57.836028",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-use-secure-communication-protocols-(e.g.,-https)-S3Resource",
      "name": "owasp-latest-use-secure-communication-protocols-(e.g.,-https)-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 buckets do not have encryption enabled or have public access allowed, which increases the risk of unauthorized access and data tampering, violating the OWASP recommendation to use secure communication protocols.", "partial": "Some S3 buckets have encryption enabled and public access restricted, while others do not, partially aligning with the OWASP recommendation to use secure communication protocols.", "success": "The S3 bucket(s) have encryption enabled, and public access is appropriately restricted, aligning with the OWASP recommendation to use secure communication protocols."},
      "fix_details": {"description": "For S3 buckets that do not have encryption enabled or have public access allowed, the following steps should be taken to align with the OWASP recommendation:", "instructions": ["Enable server-side encryption for the S3 bucket using AWS-managed keys (SSE-S3) or customer-managed keys (SSE-KMS).", "Configure the S3 bucket's public access block settings to block public access control lists (ACLs), block public bucket policies, ignore public ACLs, and restrict public bucket access.", "Review and remove any existing public access policies or ACLs that grant public access to the bucket or its objects."], "estimated_time": "15-30 minutes per bucket", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for encryption_enabled in fetched_value:\n        if encryption_enabled:\n            result = True\n            break"}, "field_path": "buckets[*].encryption.enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.837268",
      "updated_at": "2025-09-02 22:03:57.837269",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-proper-access-control-mechanisms-IAMResource",
      "name": "owasp-latest-implement-proper-access-control-mechanisms-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM policies and user access controls are not properly configured, allowing unauthorized access or excessive privileges.", "partial": "Some IAM policies and user access controls are properly configured, but others need attention to fully enforce least privilege and prevent unauthorized access.", "success": "IAM policies and user access controls are properly configured to enforce least privilege and prevent unauthorized access."},
      "fix_details": {"description": "If issues are found with IAM policies or user access controls, they need to be reviewed and updated to align with the principle of least privilege and industry best practices for access control.", "instructions": ["Review all IAM policies and ensure they follow the principle of least privilege, granting only the necessary permissions required for specific roles or tasks.", "Review all IAM user accounts and ensure they have appropriate access keys and MFA devices configured for secure authentication and authorization.", "Remove or disable any unnecessary or overly permissive policies or user access keys.", "Implement regular audits and reviews of IAM policies and user access controls to maintain a secure access control posture."], "estimated_time": "1-2 hours for initial review and remediation, ongoing maintenance required", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            if hasattr(statement, 'Action') and 'iam:*' in statement.Action:\n                if hasattr(statement, 'Resource') and '*' in statement.Resource:\n                    result = False\n                    break\n            elif hasattr(statement, 'NotAction') and 'iam:*' not in statement.NotAction:\n                if hasattr(statement, 'Resource') and '*' in statement.Resource:\n                    result = False\n                    break\n        elif isinstance(statement, dict):\n            if statement.get('Effect') == 'Allow':\n                if 'iam:*' in statement.get('Action', []):\n                    if '*' in statement.get('Resource', []):\n                        result = False\n                        break\n                elif 'iam:*' not in statement.get('NotAction', []):\n                    if '*' in statement.get('Resource', []):\n                        result = False\n                        break\n    else:\n        result = True"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.838944",
      "updated_at": "2025-09-02 22:03:57.838944",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-key-management-IAMResource",
      "name": "owasp-latest-implement-secure-key-management-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM access keys are not regularly rotated, MFA is not enabled for privileged users, or overly permissive access policies are in place, increasing the risk of unauthorized access and data breaches.", "partial": "IAM access keys are regularly rotated, MFA is enabled for privileged users, and least-privilege access policies are implemented, ensuring secure key management practices.", "success": "IAM access keys are regularly rotated, MFA is enabled for privileged users, and least-privilege access policies are implemented, ensuring secure key management practices."},
      "fix_details": {"description": "If secure key management practices are not properly implemented, remediation steps should be taken to address the identified issues.", "instructions": ["Review and update IAM access key rotation policies to ensure regular rotation (e.g., every 90 days).", "Enable MFA for all privileged IAM users and enforce its use.", "Review and update IAM policies to follow the principle of least privilege, granting only the necessary permissions required for specific roles and tasks.", "Implement centralized logging and monitoring for IAM activities to detect and respond to potential security incidents."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for access_key_status in fetched_value:\n        if access_key_status == 'Active':\n            # Check if the access key is older than 90 days\n                        now = datetime.datetime.utcnow()\n            for user in fetched_value:\n                for access_key in user.access_keys:\n                    if access_key.status == 'Active':\n                        create_date = access_key.create_date\n                        age = now - create_date\n                        if age.days > 90:\n                            result = False\n                            break\n        else:\n            result = False\n            break"}, "field_path": "users[].access_keys[].status", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.840340",
      "updated_at": "2025-09-02 22:03:57.840341",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-proper-access-control-mechanisms-CloudTrailResource",
      "name": "owasp-latest-implement-proper-access-control-mechanisms-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured to log relevant API calls and events, hindering the ability to monitor and enforce access control mechanisms effectively.", "partial": "CloudTrail is partially configured to log API calls and events, but some critical events or resources may not be covered, potentially leaving gaps in access control monitoring and enforcement.", "success": "CloudTrail is configured to log all relevant API calls and events, enabling effective monitoring and auditing of access control mechanisms."},
      "fix_details": {"description": "To ensure proper access control monitoring and enforcement, CloudTrail should be configured to log all relevant API calls and events, including management events and data events for specific resources.", "instructions": ["Review the current CloudTrail trail configurations and event selectors to identify any gaps in logging coverage.", "Update the event selectors to include all necessary data resources and management events relevant to your organization's access control policies.", "Ensure that the CloudTrail trail is configured to log events across all required AWS regions and services.", "Set up appropriate log monitoring and analysis mechanisms to detect and respond to potential access control violations or unauthorized activities."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for value in fetched_value:\n        if value == 'arn:aws:s3:::':\n            result = True\n            break"}, "field_path": "trails[].event_selectors[].data_resources.values[]", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.841634",
      "updated_at": "2025-09-02 22:03:57.841635",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-remove-unnecessary-features-and-components-CloudTrailResource",
      "name": "owasp-latest-remove-unnecessary-features-and-components-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is configured to log unnecessary events or resources, increasing the attack surface and potentially exposing sensitive data or unnecessary components.", "partial": "CloudTrail is partially configured to log only necessary events and resources, but some unnecessary components or sensitive data may still be exposed.", "success": "CloudTrail is configured to log only necessary events and resources, minimizing the exposure of unnecessary components and reducing the attack surface."},
      "fix_details": {"description": "Review and update the CloudTrail event selectors and data resources to ensure that only necessary events and resources are being logged.", "instructions": ["1. Identify the events and resources that are essential for your organization's operations and security monitoring.", "2. Review the existing CloudTrail event selectors and data resources to identify any unnecessary or overly broad configurations.", "3. Update the event selectors and data resources to include only the necessary events and resources.", "4. Test and validate the updated CloudTrail configuration to ensure that essential events and resources are still being captured."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    allowed_resources = ['AWS::S3::Object', 'AWS::Lambda::Function', 'AWS::EC2::Instance']\n    for resource_list in fetched_value:\n        for resource in resource_list:\n            if resource not in allowed_resources:\n                break\n        else:\n            result = True\n            break"}, "field_path": "trails[*].event_selectors[*].data_resources.values[*]", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.842927",
      "updated_at": "2025-09-02 22:03:57.842927",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-follow-data-protection-regulations-CloudTrailResource",
      "name": "owasp-latest-follow-data-protection-regulations-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured to capture relevant data events, or logs are not securely stored and protected, failing to meet the requirements of the 'owasp-latest-follow-data-protection-regulations' security check.", "partial": "CloudTrail is partially configured to capture relevant data events, but there are gaps or issues with log storage and protection, partially meeting the requirements of the 'owasp-latest-follow-data-protection-regulations' security check.", "success": "CloudTrail is configured to capture relevant data events, and logs are securely stored and protected, meeting the requirements of the 'owasp-latest-follow-data-protection-regulations' security check."},
      "fix_details": {"description": "If CloudTrail is not properly configured to capture and securely store data access events, the following steps should be taken to remediate the issue:", "instructions": ["1. Review the CloudTrail event selectors and ensure that relevant data resources (e.g., S3 buckets, DynamoDB tables) are included in the data_resources.values field.", "2. Set the event_selectors.read_write_type field to 'All' to capture both read and write events.", "3. Enable log file validation by setting the log_file_validation_enabled field to true.", "4. Ensure that logs are stored in a secure and centralized location by configuring an appropriate s3_bucket_name and s3_key_prefix.", "5. If necessary, enable encryption for log files by specifying a kms_key_id.", "6. Consider enabling multi-region trail (is_multi_region_trail) to capture events across multiple AWS regions."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    sensitive_data_types = ['AWS::S3Object', 'AWS::Lambda::Function', 'AWS::DynamoDB::Table']\n    for data_resource_values in fetched_value:\n        if any(value in sensitive_data_types for value in data_resource_values):\n            result = True\n            break"}, "field_path": "trails[*].event_selectors[*].data_resources.values[*]", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.844404",
      "updated_at": "2025-09-02 22:03:57.844404",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-enforce-least-privilege-principles-UserResource",
      "name": "owasp-latest-enforce-least-privilege-principles-UserResource",
      "description": "",
      "output_statements": {"failure": "The user account has excessive privileges or access rights that violate the principle of least privilege.", "partial": "Some aspects of the user account's privileges and access controls align with the principle of least privilege, but there are areas that require further review and adjustment.", "success": "The user account adheres to the principle of least privilege, with appropriate roles, group memberships, and access controls in place."},
      "fix_details": {"description": "If the user account has excessive privileges or access rights, the following steps can be taken to remediate the issue:", "instructions": ["Review the user's roles and group memberships, and remove any unnecessary or excessive permissions.", "Implement role-based access control (RBAC) and assign the user only the roles required for their job functions.", "Configure access control lists (ACLs) to restrict the user's access to specific resources or data.", "Enable two-factor authentication (2FA) for the user account to enhance security and reduce the risk of unauthorized access.", "Regularly review and audit user privileges and access rights to ensure they remain aligned with the principle of least privilege."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    # Check if the user is an admin\n    is_admin = fetched_value\n    \n    # Check if the user is enrolled in 2-step verification\n    is_enrolled_in_2sv = fetched_value.get('security_info', {}).get('isEnrolledIn2Sv', False)\n    \n    # Enforce least privilege by ensuring non-admin users are enrolled in 2-step verification\n    if not is_admin and is_enrolled_in_2sv:\n        result = True"}, "field_path": "admin_info.isAdmin", "resource_type": "con_mon.mappings.google.UserResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.845964",
      "updated_at": "2025-09-02 22:03:57.845964",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-conduct-regular-security-testing-IAMResource",
      "name": "owasp-latest-conduct-regular-security-testing-IAMResource",
      "description": "",
      "output_statements": {"failure": "One or more IAM policies have been found to be overly permissive, user access keys are inactive or insecure, or MFA devices are not properly configured, posing potential security risks.", "partial": "While some IAM policies and user configurations are secure, there are areas that require attention to mitigate potential security risks.", "success": "IAM policies, user access keys, and MFA devices have been reviewed, and no security risks or misconfigurations were identified."},
      "fix_details": {"description": "If security risks or misconfigurations are identified in IAM policies, user access keys, or MFA device configurations, remediation steps should be taken to address these issues.", "instructions": ["Review IAM policies and remove any unnecessary or overly permissive permissions.", "Rotate or deactivate any inactive or insecure user access keys.", "Ensure that MFA devices are properly configured and enabled for all IAM users with privileged access.", "Implement regular security testing and monitoring to identify and address any new vulnerabilities or misconfigurations."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Action'):\n            actions = statement.Action\n        elif isinstance(statement, dict):\n            actions = statement.get('Action')\n        else:\n            actions = getattr(statement, 'Action', None)\n\n        if actions:\n            if isinstance(actions, str):\n                actions = [actions]\n\n            if any(action.startswith('iam:') for action in actions):\n                result = True\n                break"}, "field_path": "policies[].default_version.Document.Statement[].Action", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.847315",
      "updated_at": "2025-09-02 22:03:57.847316",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-regularly-review-and-update-configurations-CloudTrailResource",
      "name": "owasp-latest-regularly-review-and-update-configurations-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured correctly to capture relevant API calls and events, hindering the ability to regularly review and update system configurations.", "partial": "CloudTrail is partially configured to capture API calls and events, but additional configuration changes are required to fully enable regular reviews and updates of system configurations.", "success": "CloudTrail is configured correctly to capture relevant API calls and events, enabling regular reviews and updates of system configurations."},
      "fix_details": {"description": "If CloudTrail is not configured correctly, the following steps can be taken to remediate the issue:", "instructions": ["1. Enable CloudTrail logging for all regions and ensure it is capturing all management events.", "2. Configure CloudTrail to capture data events for relevant AWS services and resources.", "3. Enable log file validation to ensure the integrity of CloudTrail logs.", "4. Configure CloudTrail to deliver logs to a secure and centralized S3 bucket for long-term storage and analysis.", "5. Regularly review CloudTrail logs for any potential misconfigurations, unauthorized access attempts, or other security-related events, and take appropriate actions to update system configurations as needed."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for is_logging in fetched_value:\n        if is_logging:\n            result = True\n            break"}, "field_path": "trails[*].is_logging", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.848578",
      "updated_at": "2025-09-02 22:03:57.848578",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-enforce-least-privileges-S3Resource",
      "name": "owasp-latest-enforce-least-privileges-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 buckets have excessive permissions or public access enabled, violating the principle of least privilege.", "partial": "Some S3 buckets have appropriate access controls, but others may have excessive permissions or public access enabled.", "success": "The S3 bucket(s) have appropriate access controls configured to enforce the principle of least privilege."},
      "fix_details": {"description": "If S3 buckets are found to have excessive permissions or public access enabled, the access controls need to be tightened to enforce the principle of least privilege.", "instructions": ["Review the bucket policies and access control lists (ACLs) for each non-compliant S3 bucket.", "Remove any unnecessary permissions or public access grants.", "Configure the public access block settings to restrict public access as needed.", "Use AWS Identity and Access Management (IAM) policies to grant only the minimum required permissions to users, roles, and applications accessing the S3 buckets."], "estimated_time": "30 minutes to 1 hour per non-compliant bucket", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for public_access_block in fetched_value:\n        if not (public_access_block.block_public_acls and\n                public_access_block.block_public_policy and\n                public_access_block.ignore_public_acls and\n                public_access_block.restrict_public_buckets):\n            result = False\n            break"}, "field_path": "buckets[*].public_access_block", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.849775",
      "updated_at": "2025-09-02 22:03:57.849776",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-role-based-access-control-(rbac)-IAMResource",
      "name": "owasp-latest-implement-role-based-access-control-(rbac)-IAMResource",
      "description": "",
      "output_statements": {"failure": "The AWS IAM resource has not implemented Role-Based Access Control (RBAC) effectively. Policies, user accounts, or MFA devices are not configured correctly.", "partial": "The AWS IAM resource has partially implemented Role-Based Access Control (RBAC). Some aspects, such as policies, user accounts, or MFA devices, may require further configuration.", "success": "The AWS IAM resource has implemented Role-Based Access Control (RBAC) effectively, with appropriate policies, user accounts, and MFA devices configured."},
      "fix_details": {"description": "If the IAM resource is not configured correctly for RBAC, the following steps can be taken to remediate the issue:", "instructions": ["Review and update IAM policies to ensure they follow the principle of least privilege and grant only the necessary permissions to users, groups, or roles.", "Create or modify user accounts, groups, and roles as needed, and assign appropriate policies to them based on their job functions.", "Enable and enforce multi-factor authentication (MFA) for all IAM users to add an extra layer of security.", "Regularly review and audit IAM configurations to ensure they remain up-to-date and aligned with your organization's security requirements."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            if hasattr(statement, 'Action') and 'iam:*' in statement.Action:\n                if hasattr(statement, 'Resource') and '*' in statement.Resource:\n                    result = False\n                    break\n            elif hasattr(statement, 'NotAction') and 'iam:*' not in statement.NotAction:\n                if hasattr(statement, 'Resource') and '*' in statement.Resource:\n                    result = False\n                    break\n        elif isinstance(statement, dict):\n            if statement.get('Effect') == 'Allow':\n                if 'iam:*' in statement.get('Action', []):\n                    if '*' in statement.get('Resource', []):\n                        result = False\n                        break\n                elif 'iam:*' not in statement.get('NotAction', []):\n                    if '*' in statement.get('Resource', []):\n                        result = False\n                        break\n    else:\n        result = True"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.851391",
      "updated_at": "2025-09-02 22:03:57.851391",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-deployment-processes-CloudTrailResource",
      "name": "owasp-latest-implement-secure-deployment-processes-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured properly to capture and log API activity and events, hindering the ability to monitor and audit secure deployments.", "partial": "CloudTrail is partially configured to capture and log API activity and events, but additional configuration is required to fully support secure deployment monitoring and auditing.", "success": "CloudTrail is configured to capture and log all relevant API activity and events, enabling secure deployment monitoring and auditing."},
      "fix_details": {"description": "If CloudTrail is not configured properly, it needs to be set up to capture and log all relevant API activity and events related to deployments.", "instructions": ["1. Enable CloudTrail and create a new trail or modify an existing one.", "2. Configure the trail to log all management events and data events for relevant AWS services.", "3. Specify an S3 bucket to store the CloudTrail logs.", "4. Enable log file validation to ensure log integrity.", "5. Configure additional settings as needed, such as multi-region trails or custom event selectors."], "estimated_time": "30 minutes", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for is_logging in fetched_value:\n        if is_logging:\n            result = True\n            break"}, "field_path": "trails[*].is_logging", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.852585",
      "updated_at": "2025-09-02 22:03:57.852586",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-comprehensive-logging-mechanisms-CloudWatchResource",
      "name": "owasp-latest-implement-comprehensive-logging-mechanisms-CloudWatchResource",
      "description": "",
      "output_statements": {"failure": "CloudWatch is not configured to collect and analyze logs from relevant AWS services and applications, hindering comprehensive logging and monitoring of system activities and security events.", "partial": "CloudWatch is partially configured to collect and analyze logs from some AWS services and applications, but additional configuration is required to achieve comprehensive logging and monitoring of system activities and security events.", "success": "CloudWatch is configured to collect and analyze logs from relevant AWS services and applications, enabling comprehensive logging and monitoring of system activities and security events."},
      "fix_details": {"description": "If CloudWatch is not properly configured for comprehensive logging, you need to set up Log Groups, Metric Filters, and Alarms to capture and analyze log data from relevant AWS services and applications.", "instructions": ["Identify the AWS services and applications that require logging and monitoring.", "Create CloudWatch Log Groups to collect log data from these services and applications.", "Configure Metric Filters to define custom metrics based on log patterns and events of interest.", "Set up CloudWatch Alarms to receive notifications and trigger actions based on specific metric thresholds or conditions.", "Review and adjust the log retention period for each Log Group based on your organization's requirements."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for retention_days in fetched_value:\n        if retention_days is not None and retention_days >= 365:\n            result = True\n            break"}, "field_path": "log_groups[*].retention_in_days", "resource_type": "con_mon.mappings.aws.CloudWatchResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.853964",
      "updated_at": "2025-09-02 22:03:57.853964",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-regularly-review-and-update-security-procedures-CloudTrailResource",
      "name": "owasp-latest-regularly-review-and-update-security-procedures-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured to capture relevant events or store logs securely, hindering the ability to regularly review and update security procedures.", "partial": "CloudTrail is partially configured to capture events and store logs, but additional configuration may be needed to enable comprehensive regular reviews and updates to security procedures.", "success": "CloudTrail is configured to capture relevant events and store logs in a secure location, enabling regular review and updates to security procedures."},
      "fix_details": {"description": "If CloudTrail is not configured correctly, it may not capture all relevant events or store logs securely, making it difficult to regularly review and update security procedures.", "instructions": ["Review the CloudTrail event selectors and ensure they capture all relevant API calls and events for your organization.", "Configure CloudTrail to store logs in a secure S3 bucket with appropriate access controls and encryption.", "Enable log file validation to ensure log integrity and detect tampering.", "Set up automated log analysis and alerting to facilitate regular reviews and identify potential security issues."], "estimated_time": "1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for is_logging in fetched_value:\n        if is_logging:\n            result = True\n            break"}, "field_path": "trails[*].is_logging", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.855140",
      "updated_at": "2025-09-02 22:03:57.855141",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-enforce-least-privilege-principles-CloudTrailResource",
      "name": "owasp-latest-enforce-least-privilege-principles-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured with appropriate event selectors and data resource filters to enforce least privilege. Excessive permissions or unauthorized access attempts may go undetected.", "partial": "CloudTrail is partially configured with event selectors and data resource filters to enforce least privilege, but some resources or services may not be adequately monitored.", "success": "CloudTrail is configured with appropriate event selectors and data resource filters to enforce least privilege by logging and auditing access to specific AWS resources and services."},
      "fix_details": {"description": "To fully implement the 'owasp-latest-enforce-least-privilege-principles' security check using CloudTrail, you need to configure appropriate event selectors and data resource filters to log and monitor access to specific AWS resources and services.", "instructions": ["1. Review your AWS environment and identify the resources and services that require access monitoring and auditing.", "2. Create or modify CloudTrail trails with event selectors that include the relevant data resources and services.", "3. Configure the event selectors to log both read and write events, as well as management events if applicable.", "4. Ensure that the CloudTrail trails are configured to log to a secure and centralized location, such as an S3 bucket with appropriate access controls.", "5. Regularly review the CloudTrail logs to identify and remediate any excessive permissions or unauthorized access attempts."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for values_list in fetched_value:\n        if not values_list:\n            continue\n        for value in values_list:\n            if value == 'arn:aws:s3:::':\n                result = True\n                break\n        if result:\n            break"}, "field_path": "trails[*].event_selectors[*].data_resources.values[*]", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.856584",
      "updated_at": "2025-09-02 22:03:57.856585",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-regularly-update-and-patch-third-party-components-GithubResource",
      "name": "owasp-latest-regularly-update-and-patch-third-party-components-GithubResource",
      "description": "",
      "output_statements": {"failure": "The repository has one or more vulnerabilities in third-party dependencies that require patching or updating.", "partial": "Some third-party dependencies have been updated, but there are still outstanding vulnerabilities that need to be addressed.", "success": "The repository has no outstanding vulnerabilities in third-party dependencies, and all components are up-to-date."},
      "fix_details": {"description": "If vulnerabilities are identified in third-party dependencies, they should be addressed by updating or patching the affected components.", "instructions": ["Review the security_data.vulnerability_alerts and security_data.security_advisories fields to identify vulnerable dependencies.", "Check the project's dependency management system (e.g., package.json, requirements.txt) for available updates or patches.", "Update or patch the affected dependencies according to the project's update process.", "Verify that the vulnerabilities have been resolved by checking the security_data fields again."], "estimated_time": "30 minutes to 2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    has_vulnerabilities = False\n    for dependency in fetched_value:\n        if dependency.vulnerabilities:\n            has_vulnerabilities = True\n            break\n    result = not has_vulnerabilities"}, "field_path": "security_data.dependency_graph", "resource_type": "con_mon.mappings.github.GithubResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.857767",
      "updated_at": "2025-09-02 22:03:57.857767",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-encryption-for-data-at-rest-S3Resource",
      "name": "owasp-latest-implement-encryption-for-data-at-rest-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 buckets do not have encryption enabled, or are using an insecure encryption method (SSE-S3).", "partial": "Some S3 buckets have encryption enabled using a secure encryption method, while others do not or are using an insecure encryption method.", "success": "All S3 buckets have encryption enabled using a secure encryption method (SSE-KMS or SSE-C) and a valid KMS key."},
      "fix_details": {"description": "For any S3 buckets that do not have encryption enabled, or are using an insecure encryption method (SSE-S3), encryption needs to be enabled using a secure method (SSE-KMS or SSE-C) and a valid KMS key.", "instructions": ["Identify the S3 buckets that do not have encryption enabled or are using SSE-S3.", "Create a new KMS key or use an existing KMS key for encryption.", "Update the bucket encryption configuration to enable SSE-KMS or SSE-C using the KMS key.", "Verify that encryption is enabled and using the correct encryption method and KMS key."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for bucket_encryption in fetched_value:\n        if bucket_encryption:\n            result = True\n            break"}, "field_path": "buckets[*].encryption.enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.858937",
      "updated_at": "2025-09-02 22:03:57.858938",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-logging-mechanisms-CloudWatchResource",
      "name": "owasp-latest-implement-secure-logging-mechanisms-CloudWatchResource",
      "description": "",
      "output_statements": {"failure": "CloudWatch Log Groups are not configured with appropriate log retention policies, encryption, or metric filters/alarms to implement secure logging mechanisms.", "partial": "CloudWatch Log Groups are partially configured with appropriate log retention policies, encryption, and metric filters/alarms to implement secure logging mechanisms, but some aspects are missing or misconfigured.", "success": "CloudWatch Log Groups are configured with appropriate log retention policies, encryption, and metric filters/alarms to implement secure logging mechanisms."},
      "fix_details": {"description": "To fully implement secure logging mechanisms using AWS CloudWatch, ensure that Log Groups are configured with appropriate log retention policies, encryption using AWS KMS keys, and Metric Filters/Alarms to monitor and respond to specific log patterns or conditions.", "instructions": ["1. Review existing CloudWatch Log Groups and ensure they have appropriate log retention policies set based on organizational requirements and regulatory compliance.", "2. Enable encryption for Log Groups using AWS KMS keys to protect the confidentiality of log data.", "3. Configure CloudWatch Metric Filters to analyze log data and identify specific patterns or conditions of interest.", "4. Create CloudWatch Alarms based on the Metric Filters to trigger actions (e.g., notifications, automated responses) when specific conditions are met.", "5. Review and test the configured Metric Filters and Alarms to ensure they are functioning as expected and providing the desired monitoring and incident response capabilities."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for retention_days in fetched_value:\n        if retention_days is not None and retention_days >= 365:\n            result = True\n            break"}, "field_path": "log_groups[*].retention_in_days", "resource_type": "con_mon.mappings.aws.CloudWatchResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.860406",
      "updated_at": "2025-09-02 22:03:57.860407",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-monitor-for-suspicious-activities-IAMResource",
      "name": "owasp-latest-monitor-for-suspicious-activities-IAMResource",
      "description": "",
      "output_statements": {"failure": "Suspicious activities were detected in the IAM policies, user access keys, or MFA device configurations. Review the findings and take appropriate action.", "partial": "Some potential issues were identified in the IAM policies, user access keys, or MFA device configurations. Further investigation is recommended.", "success": "No suspicious activities were detected in the IAM policies, user access keys, or MFA device configurations."},
      "fix_details": {"description": "If suspicious activities are detected, remediation steps may include reviewing and updating IAM policies, rotating access keys, enabling MFA for users, and investigating any unauthorized access attempts.", "instructions": ["Review the identified IAM policies for overly permissive statements and update them to follow the principle of least privilege.", "Rotate any access keys that show suspicious activity or have been inactive for an extended period.", "Enable MFA for all IAM users and enforce its usage.", "Investigate any unauthorized access attempts or unusual activity patterns detected in the logs."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            condition = getattr(statement, 'Condition', None)\n            if condition:\n                # Check if the condition allows overly permissive access\n                if 'StringEquals' in condition and 'AWS:SourceIp' in condition['StringEquals'] and condition['StringEquals']['AWS:SourceIp'] == '0.0.0.0/0':\n                    result = False\n                    break\n                elif 'NotIpAddress' in condition and condition['NotIpAddress'] == '0.0.0.0/0':\n                    result = False\n                    break\n            else:\n                # Unconditional Allow statement\n                result = False\n                break\n        elif isinstance(statement, dict) and statement.get('Effect') == 'Allow':\n            condition = statement.get('Condition')\n            if condition:\n                # Check if the condition allows overly permissive access\n                if 'StringEquals' in condition and 'AWS:SourceIp' in condition['StringEquals'] and condition['StringEquals']['AWS:SourceIp'] == '0.0.0.0/0':\n                    result = False\n                    break\n                elif 'NotIpAddress' in condition and condition['NotIpAddress'] == '0.0.0.0/0':\n                    result = False\n                    break\n            else:\n                # Unconditional Allow statement\n                result = False\n                break\n    else:\n        result = True"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.862263",
      "updated_at": "2025-09-02 22:03:57.862263",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-multi-factor-authentication-UserResource",
      "name": "owasp-latest-implement-multi-factor-authentication-UserResource",
      "description": "",
      "output_statements": {"failure": "Multi-factor authentication is not implemented or enforced for the user account.", "partial": "Multi-factor authentication is implemented but not enforced for the user account.", "success": "Multi-factor authentication is implemented and enforced for the user account."},
      "fix_details": {"description": "If MFA is not implemented or enforced, you need to enable and enforce Google's Two-Step Verification for the user account.", "instructions": ["1. Access the Google Admin console for your organization.", "2. Navigate to the Users section and select the user account.", "3. Under the Account > Security section, enable 'Enforced 2-Step Verification' for the user.", "4. Follow the prompts to enroll the user in 2-Step Verification."], "estimated_time": "10 minutes", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    # Check if the user is enrolled in 2SV (MFA)\n    result = fetched_value"}, "field_path": "security_info.isEnrolledIn2Sv", "resource_type": "con_mon.mappings.google.UserResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.863289",
      "updated_at": "2025-09-02 22:03:57.863290",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-comprehensive-logging-mechanisms-IAMResource",
      "name": "owasp-latest-implement-comprehensive-logging-mechanisms-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM logging mechanisms are not properly configured or comprehensive logs are not being generated for policy changes, access key usage, and MFA device assignments.", "partial": "IAM logging mechanisms are partially configured, but some gaps exist in logging policy changes, access key usage, or MFA device assignments.", "success": "IAM logging mechanisms are properly configured and comprehensive logs are being generated for policy changes, access key usage, and MFA device assignments."},
      "fix_details": {"description": "Ensure that AWS CloudTrail is enabled and configured to capture all IAM events, including policy changes, access key usage, and MFA device assignments.", "instructions": ["1. Open the AWS CloudTrail console and navigate to the 'Trails' section.", "2. Create a new trail or edit an existing trail to include all IAM events.", "3. Configure the trail to deliver logs to an S3 bucket or CloudWatch Logs for long-term storage and analysis.", "4. Review and analyze the CloudTrail logs regularly to identify and investigate any suspicious or unauthorized activities."], "estimated_time": "30 minutes", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            condition = getattr(statement, 'Condition', None)\n            if condition:\n                for condition_key, condition_value in condition.items():\n                    if 'aws:MultiFactorAuthAge' in condition_key:\n                        result = True\n                        break\n            else:\n                result = False\n                break"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.864617",
      "updated_at": "2025-09-02 22:03:57.864617",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-password-strength-requirements-IAMResource",
      "name": "owasp-latest-implement-password-strength-requirements-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM password policies do not meet the latest OWASP password strength requirements. Weak password policies increase the risk of unauthorized access.", "partial": "Some IAM password policies meet the OWASP requirements, but others do not. Inconsistent password strength increases the risk of unauthorized access.", "success": "IAM password policies are configured to meet or exceed the latest OWASP password strength requirements."},
      "fix_details": {"description": "If IAM password policies do not meet the OWASP requirements, they need to be updated to enforce stronger password complexity rules.", "instructions": ["Review the current IAM password policy and identify areas that do not comply with OWASP recommendations.", "Update the IAM password policy to include requirements for minimum password length, complexity rules (e.g., a mix of uppercase, lowercase, numbers, and special characters), and regular password expiration/rotation.", "Communicate the updated password policy to all IAM users and provide guidance on creating compliant passwords.", "Monitor and enforce the new password policy to ensure ongoing compliance."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            condition = getattr(statement, 'Condition', None)\n            if condition:\n                if 'PasswordPolicy' in condition:\n                    password_policy = condition['PasswordPolicy']\n                    min_length = password_policy.get('MinimumPasswordLength', 0)\n                    require_numbers = password_policy.get('RequireNumbers', False)\n                    require_symbols = password_policy.get('RequireSymbols', False)\n                    require_uppercase = password_policy.get('RequireUppercaseCharacters', False)\n                    require_lowercase = password_policy.get('RequireLowercaseCharacters', False)\n                    if min_length >= 12 and require_numbers and require_symbols and require_uppercase and require_lowercase:\n                        result = True\n                        break"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.866131",
      "updated_at": "2025-09-02 22:03:57.866131",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-CloudTrailResource",
      "name": "owasp-latest-implement-comprehensive-monitoring-mechanisms-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured properly to capture and log API activities, leaving the organization vulnerable to undetected security incidents and unauthorized access attempts.", "partial": "CloudTrail is partially configured to capture and log API activities, but some critical events or services may not be monitored, potentially leaving gaps in the organization's security monitoring capabilities.", "success": "CloudTrail is configured to capture and log API activities across AWS services, enabling comprehensive monitoring and detection of potential security incidents."},
      "fix_details": {"description": "To fully implement comprehensive monitoring mechanisms using CloudTrail, ensure that all relevant event selectors are configured, log file validation is enabled, and CloudTrail trails are set up to capture API activities across all required AWS services and resources.", "instructions": ["Review the existing CloudTrail trails and event selectors to identify any gaps in monitoring coverage.", "Configure event selectors to capture API activities for all critical AWS services and resources, including management events and read/write operations.", "Enable log file validation for CloudTrail trails to ensure the integrity and completeness of log files.", "Set up CloudTrail trails to capture API activities across all required AWS regions, if applicable.", "Configure CloudTrail to deliver log files to a secure and centralized S3 bucket for long-term storage and analysis."], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for is_logging in fetched_value:\n        if is_logging:\n            result = True\n            break"}, "field_path": "trails[*].is_logging", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.867497",
      "updated_at": "2025-09-02 22:03:57.867497",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-protect-against-brute-force-attacks-IAMResource",
      "name": "owasp-latest-protect-against-brute-force-attacks-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM user accounts are not properly configured to protect against brute force attacks. Weak password policies, lack of MFA enforcement, and/or stale access keys increase the risk of successful brute force attacks.", "partial": "Some IAM user accounts are properly configured to protect against brute force attacks, but others may be vulnerable due to weak password policies, lack of MFA enforcement, and/or stale access keys.", "success": "IAM user accounts are properly configured with strong password policies, MFA requirements, and access key rotation to protect against brute force attacks."},
      "fix_details": {"description": "To properly protect against brute force attacks, IAM user accounts should be configured with strong password policies, MFA enforcement, and regular access key rotation.", "instructions": ["Review and update the IAM password policy to enforce strong password requirements (e.g., minimum length, complexity, expiration)", "Enable MFA for all IAM user accounts and enforce its use for all AWS management operations", "Configure automatic access key rotation for all IAM user accounts to regularly invalidate and replace access keys", "Monitor and respond to any potential brute force attack attempts through CloudTrail logs and AWS Security Hub findings"], "estimated_time": "1-2 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Action'):\n            actions = statement.Action\n        elif isinstance(statement, dict):\n            actions = statement.get('Action')\n        else:\n            actions = getattr(statement, 'Action', [])\n\n        if isinstance(actions, list):\n            if 'iam:ChangePassword' in actions and 'iam:CreateAccessKey' in actions:\n                result = True\n                break\n        elif actions == '*':\n            result = True\n            break"}, "field_path": "policies[].default_version.Document.Statement[].Action", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.869227",
      "updated_at": "2025-09-02 22:03:57.869227",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-software-composition-analysis-(sca)-process-GithubResource",
      "name": "owasp-latest-implement-software-composition-analysis-(sca)-process-GithubResource",
      "description": "",
      "output_statements": {"failure": "The repository does not have an effective Software Composition Analysis (SCA) process in place, and may be at risk of security vulnerabilities and licensing issues.", "partial": "The repository has a partial Software Composition Analysis (SCA) process in place, but may be missing some components or not scanning regularly.", "success": "The repository has an effective Software Composition Analysis (SCA) process in place, with regular scans for vulnerabilities, dependencies, and security advisories."},
      "fix_details": {"description": "If the repository does not have an effective SCA process in place, the following steps can be taken to implement one:", "instructions": ["1. Enable and configure the GitHub Advanced Security features, including Dependabot alerts, code scanning, and secret scanning.", "2. Set up regular scans for vulnerabilities, dependencies, and security advisories using the GitHub API or third-party tools.", "3. Review and address any identified vulnerabilities, licensing issues, or outdated components.", "4. Establish a process for monitoring and responding to new vulnerabilities and security advisories as they are released."], "estimated_time": "1-2 hours for initial setup, ongoing maintenance as needed", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    has_dependency_graph = fetched_value\n    if has_dependency_graph:\n        result = True"}, "field_path": "security_data.dependency_graph", "resource_type": "con_mon.mappings.github.GithubResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.870453",
      "updated_at": "2025-09-02 22:03:57.870454",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-establish-incident-response-plans-CloudWatchResource",
      "name": "owasp-latest-establish-incident-response-plans-CloudWatchResource",
      "description": "",
      "output_statements": {"failure": "CloudWatch is not properly configured to detect and respond to security incidents, hindering the organization's ability to implement an effective incident response plan.", "partial": "CloudWatch has some configurations in place for incident detection and response, but additional improvements are needed to fully support an effective incident response plan.", "success": "CloudWatch alarms and log groups are configured to detect and respond to security incidents, supporting an effective incident response plan."},
      "fix_details": {"description": "To fully leverage CloudWatch for incident response, you need to ensure that appropriate alarms, log groups, and actions are configured.", "instructions": ["Review your AWS resources and applications to identify critical events and metrics that should be monitored for security incidents.", "Create CloudWatch alarms with appropriate thresholds and conditions to detect these events and metrics.", "Configure alarm actions to trigger notifications (e.g., SNS topics, Lambda functions) and automated responses (e.g., AWS Systems Manager Automation documents) when alarms are triggered.", "Set up log groups to collect and retain relevant logs from your AWS resources and applications for incident investigation and forensics.", "Regularly review and update your CloudWatch configurations as your environment and security requirements evolve."], "estimated_time": "1-2 hours for initial setup, ongoing maintenance as needed", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for alarm_actions in fetched_value:\n        for action in alarm_actions:\n            if action.startswith('arn:aws:sns:'):\n                result = True\n                break"}, "field_path": "alarms[*].alarm_actions", "resource_type": "con_mon.mappings.aws.CloudWatchResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.871820",
      "updated_at": "2025-09-02 22:03:57.871820",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-software-supply-chain-practices-GithubResource",
      "name": "owasp-latest-implement-secure-software-supply-chain-practices-GithubResource",
      "description": "",
      "output_statements": {"failure": "The repository lacks proper implementation of secure software supply chain practices. Automated workflows, access controls, and security scanning capabilities are missing or misconfigured.", "partial": "The repository has partially implemented secure software supply chain practices, but there are areas that require further attention and improvement.", "success": "The repository has implemented secure software supply chain practices, including automated workflows, access controls, and security scanning."},
      "fix_details": {"description": "If the repository is found to be lacking in secure software supply chain practices, the following steps can be taken to remediate the issues:", "instructions": ["Review and configure GitHub Actions workflows for automated build, testing, and deployment processes.", "Implement proper access controls and permissions for collaborators based on the principle of least privilege.", "Enable and configure security features like Dependabot for dependency scanning, CodeQL for code analysis, and secret scanning for detecting exposed secrets.", "Review and address any identified security advisories or vulnerability alerts.", "Establish processes and documentation for maintaining secure software supply chain practices throughout the repository's lifecycle."], "estimated_time": "1-2 hours for initial setup, ongoing maintenance required", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    # Check if security features are enabled\n    result = fetched_value"}, "field_path": "security_data.security_features_enabled", "resource_type": "con_mon.mappings.github.GithubResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.873116",
      "updated_at": "2025-09-02 22:03:57.873117",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-regularly-review-and-update-configurations-IAMResource",
      "name": "owasp-latest-regularly-review-and-update-configurations-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM policies have not been reviewed or updated in a timely manner, potentially exposing the environment to security risks.", "partial": "Some IAM policies have been reviewed and updated, but others may still require attention.", "success": "IAM policies are regularly reviewed and updated to maintain a secure posture."},
      "fix_details": {"description": "If IAM policies are found to be outdated or misconfigured, they should be reviewed and updated to align with the latest security best practices and organizational requirements.", "instructions": ["Identify all IAM policies and their associated resources.", "Review each policy document, statements, actions, conditions, and resources for potential misconfigurations or excessive permissions.", "Update or create new policies to address any identified issues, following the principle of least privilege.", "Implement a regular review and update process for IAM policies, aligning with organizational policies and industry standards."], "estimated_time": "1-2 hours for initial review and update, ongoing maintenance as needed", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\n# Check if any policy was updated more than 90 days ago\ntoday = datetime.datetime.now().date()\nfor update_date in fetched_value:\n    if update_date is not None:\n        last_update = datetime.datetime.strptime(update_date, '%Y-%m-%dT%H:%M:%S+00:00').date()\n        days_since_update = (today - last_update).days\n        if days_since_update > 90:\n            result = False\n            break\n    else:\n        result = False\n        break\nelse:\n    result = True"}, "field_path": "policies[*].update_date", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.874392",
      "updated_at": "2025-09-02 22:03:57.874392",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-enforce-least-privileges-UserResource",
      "name": "owasp-latest-enforce-least-privileges-UserResource",
      "description": "",
      "output_statements": {"failure": "The user account has been granted excessive privileges beyond what is necessary for their intended functions, violating the principle of least privilege.", "partial": "Some aspects of the user account's privileges align with the principle of least privilege, but there are areas that require further review and potential adjustment.", "success": "The user account has been configured with the minimum required privileges based on their role and responsibilities within the organization."},
      "fix_details": {"description": "If the user account has been granted excessive privileges, the following steps should be taken to remediate the issue and enforce the principle of least privilege:", "instructions": ["Review the user's role and responsibilities within the organization to determine the minimum required privileges.", "Remove any unnecessary administrative roles or privileges from the user account.", "Ensure the user is assigned to the appropriate organizational unit based on their role and access requirements.", "Enable and enforce two-step verification (2SV) for the user account to add an extra layer of security.", "Regularly review and audit user privileges to ensure they remain aligned with the principle of least privilege."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    # Check if the user is an admin\n    if fetched_value:\n        result = False\n    else:\n        # User is not an admin, which follows the principle of least privilege\n        result = True"}, "field_path": "admin_info.isAdmin", "resource_type": "con_mon.mappings.google.UserResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.875812",
      "updated_at": "2025-09-02 22:03:57.875812",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-follow-security-hardening-guidelines-S3Resource",
      "name": "owasp-latest-follow-security-hardening-guidelines-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 buckets are not configured according to the OWASP security hardening guidelines, with issues related to encryption, public access, versioning, or logging.", "partial": "Some S3 buckets are configured according to the OWASP security hardening guidelines, but others have issues related to encryption, public access, versioning, or logging.", "success": "The S3 buckets are configured according to the OWASP security hardening guidelines, with encryption enabled, public access restricted, versioning and logging enabled."},
      "fix_details": {"description": "For S3 buckets not compliant with the OWASP security hardening guidelines, the following fixes may be required:", "instructions": ["Enable encryption at rest using AWS-managed keys (SSE-S3) or customer-managed keys (SSE-KMS)", "Configure public access block settings to restrict public access to the bucket and objects", "Enable versioning to protect against accidental deletion or overwrites", "Enable access logging to monitor and audit bucket access"], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for encryption_enabled in fetched_value:\n        if encryption_enabled:\n            result = True\n        else:\n            result = False\n            break"}, "field_path": "buckets[*].encryption.enabled", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.876997",
      "updated_at": "2025-09-02 22:03:57.876997",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-log-security-relevant-events-CloudTrailResource",
      "name": "owasp-latest-log-security-relevant-events-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured to log security-relevant events across your AWS environment, failing the 'owasp-latest-log-security-relevant-events' check.", "partial": "CloudTrail is partially configured to log security-relevant events across your AWS environment, partially meeting the requirements of the 'owasp-latest-log-security-relevant-events' check.", "success": "CloudTrail is configured to log security-relevant events across your AWS environment, meeting the requirements of the 'owasp-latest-log-security-relevant-events' check."},
      "fix_details": {"description": "If CloudTrail is not properly configured to log security-relevant events, you need to review and update your trail and event selector settings.", "instructions": ["1. Ensure that CloudTrail is enabled and configured to log events across all regions and services relevant to your environment.", "2. Review the event selectors for your CloudTrail trails and ensure that they include data resources and event types related to security-relevant events, such as authentication, authorization, and access management events.", "3. Enable 'include_management_events' and set 'read_write_type' to 'All' for your event selectors to capture both read and write events.", "4. Verify that your CloudTrail logs are being delivered to a secure and centralized location, such as an S3 bucket or CloudWatch Logs, for long-term retention and analysis."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for values_list in fetched_value:\n        if 'AWS::CloudTrail::Event' in values_list:\n            result = True\n            break"}, "field_path": "trails[*].event_selectors[*].data_resources.values[*]", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.878325",
      "updated_at": "2025-09-02 22:03:57.878325",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-centralized-log-management-CloudWatchResource",
      "name": "owasp-latest-implement-centralized-log-management-CloudWatchResource",
      "description": "",
      "output_statements": {"failure": "No CloudWatch Log Groups or Log Streams are configured, preventing centralized log management and hindering security monitoring capabilities.", "partial": "Some CloudWatch Log Groups and Log Streams are configured, but log data from critical sources may be missing, limiting the effectiveness of centralized log management.", "success": "CloudWatch Log Groups and Log Streams are configured to centralize log data from multiple sources, enabling effective log management and security monitoring."},
      "fix_details": {"description": "If CloudWatch Log Groups and Log Streams are not configured or are missing critical log sources, you need to set them up or update them to enable centralized log management.", "instructions": ["1. Identify the AWS resources, applications, and custom log sources that need to be centralized.", "2. Create or update CloudWatch Log Groups to organize and store log data from different sources.", "3. Configure Log Streams within each Log Group to ingest log data from the identified sources.", "4. Set appropriate log retention periods and encryption settings for the Log Groups based on your requirements.", "5. Configure CloudWatch Metric Filters and Alarms to monitor and alert on specific log patterns or events.", "6. Integrate CloudWatch Logs with other AWS services or third-party tools for advanced log analysis, visualization, and security monitoring."], "estimated_time": "30 minutes to 2 hours, depending on the number of log sources and complexity", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\n# Check if any log group name starts with '/aws/lambda/'\nif fetched_value is not None:\n    for log_group_name in fetched_value:\n        if log_group_name.startswith('/aws/lambda/'):\n            result = True\n            break"}, "field_path": "log_groups[*].log_group_name", "resource_type": "con_mon.mappings.aws.CloudWatchResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.879761",
      "updated_at": "2025-09-02 22:03:57.879762",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-multi-factor-authentication-IAMResource",
      "name": "owasp-latest-implement-multi-factor-authentication-IAMResource",
      "description": "",
      "output_statements": {"failure": "One or more IAM users do not have multi-factor authentication (MFA) enabled, increasing the risk of unauthorized access.", "partial": "N/A", "success": "All IAM users have multi-factor authentication (MFA) enabled, ensuring an additional layer of security beyond just passwords."},
      "fix_details": {"description": "For any IAM users without MFA enabled, MFA needs to be configured and enforced.", "instructions": ["Identify IAM users without MFA devices listed under 'users[].mfa_devices'", "For each user without MFA, enable MFA by following AWS documentation: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa.html", "Consider implementing an IAM password policy to require MFA for all IAM users"], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None or not fetched_value:\n    result = False\nelse:\n    mfa_enabled_users = []\n    for user in fetched_value:\n        if user and hasattr(user, 'enable_date'):\n            mfa_enabled_users.append(user)\n    if not mfa_enabled_users:\n        result = False"}, "field_path": "users[*].mfa_devices[*]", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.880803",
      "updated_at": "2025-09-02 22:03:57.880804",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-enforce-least-privileges-IAMResource",
      "name": "owasp-latest-enforce-least-privileges-IAMResource",
      "description": "",
      "output_statements": {"failure": "One or more IAM policies or user permissions violate the principle of least privilege by granting excessive privileges.", "partial": "Some IAM policies and user permissions follow the principle of least privilege, but others grant excessive privileges.", "success": "All IAM policies and user permissions adhere to the principle of least privilege, granting only the necessary access rights."},
      "fix_details": {"description": "If excessive privileges are identified, the affected IAM policies and user permissions need to be reviewed and updated to follow the principle of least privilege.", "instructions": ["Identify the IAM policies and user permissions that grant excessive privileges.", "Review the policy documents and user access rights to determine the minimum required permissions.", "Update the affected policies and user permissions to remove unnecessary privileges.", "Implement a regular review process to ensure least privilege is maintained."], "estimated_time": "1-2 hours for initial review and remediation, ongoing maintenance required", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = True\n\nif fetched_value is None:\n    result = False\nelse:\n    for statement in fetched_value:\n        if hasattr(statement, 'Effect') and statement.Effect == 'Allow':\n            if hasattr(statement, 'Action') and '*' in statement.Action:\n                result = False\n                break\n            if hasattr(statement, 'Resource') and '*' in statement.Resource:\n                result = False\n                break"}, "field_path": "policies[].default_version.Document.Statement", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.882232",
      "updated_at": "2025-09-02 22:03:57.882233",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-implement-secure-deployment-processes-IAMResource",
      "name": "owasp-latest-implement-secure-deployment-processes-IAMResource",
      "description": "",
      "output_statements": {"failure": "IAM policies and/or user access controls are not properly configured, increasing the risk of insecure deployments.", "partial": "Some aspects of IAM policies and user access controls support secure deployments, but other areas need improvement.", "success": "IAM policies and user access controls are properly configured to support secure deployment processes."},
      "fix_details": {"description": "Ensure IAM policies follow least privilege principles and segregate duties for deployment roles. Enforce MFA for IAM users involved in deployments. Rotate access keys regularly.", "instructions": ["Review all IAM policies and remove any overly permissive statements", "Create separate IAM roles for different deployment stages/environments", "Configure IAM password policies to enforce strong credentials", "Enable MFA for all IAM users with deployment permissions", "Set an expiration period for all IAM user access keys"], "estimated_time": "2-4 hours", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    secure_deployment_actions = ['iam:PassRole', 'iam:AddUserToGroup', 'iam:CreateAccessKey', 'iam:UpdateAccessKey', 'iam:DeleteAccessKey', 'iam:EnableMFADevice', 'iam:ResyncMFADevice']\n    for action in fetched_value:\n        if isinstance(action, str) and action in secure_deployment_actions:\n            result = True\n            break"}, "field_path": "policies[].default_version.Document.Statement[].Action", "resource_type": "con_mon.mappings.aws.IAMResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.883448",
      "updated_at": "2025-09-02 22:03:57.883449",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-enforce-least-privilege-principles-S3Resource",
      "name": "owasp-latest-enforce-least-privilege-principles-S3Resource",
      "description": "",
      "output_statements": {"failure": "One or more S3 buckets have excessive permissions, lack encryption, or allow public access, violating the principle of least privilege.", "partial": "Some S3 buckets are configured correctly, while others have issues with access controls, encryption, or public access settings, partially violating the principle of least privilege.", "success": "The S3 buckets are configured with appropriate access controls, encryption, and public access restrictions, adhering to the principle of least privilege."},
      "fix_details": {"description": "If any S3 buckets are found to have excessive permissions, lack encryption, or allow public access, these issues need to be addressed to comply with the principle of least privilege.", "instructions": ["Review the bucket policies and access control lists (ACLs) for each S3 bucket and remove any unnecessary permissions or public access grants.", "Enable server-side encryption for all S3 buckets using AWS-managed keys (SSE-S3) or customer-managed keys (SSE-KMS).", "Configure the public access block settings for each S3 bucket to block public access, public ACLs, and public bucket policies.", "Regularly review and audit S3 bucket configurations to ensure they remain compliant with the principle of least privilege."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for block_public_acls in fetched_value:\n        if block_public_acls:\n            result = True\n        else:\n            result = False\n            break"}, "field_path": "buckets[].public_access_block.block_public_acls", "resource_type": "con_mon.mappings.aws.S3Resource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.884854",
      "updated_at": "2025-09-02 22:03:57.884855",
      "is_deleted": false
    },
    {
      "id": "owasp-latest-conduct-regular-security-testing-CloudTrailResource",
      "name": "owasp-latest-conduct-regular-security-testing-CloudTrailResource",
      "description": "",
      "output_statements": {"failure": "CloudTrail is not configured to capture relevant events and activities, hindering regular security testing and monitoring.", "partial": "CloudTrail is partially configured to capture relevant events and activities, but additional configuration may be required for comprehensive security testing and monitoring.", "success": "CloudTrail is configured to capture relevant events and activities, enabling regular security testing and monitoring."},
      "fix_details": {"description": "If CloudTrail is not configured properly, it may not capture all relevant events and activities, making it difficult to conduct regular security testing and monitoring.", "instructions": ["Review the CloudTrail trail configurations and ensure that relevant data resources, management events, and read/write operations are being captured.", "Enable log file validation to ensure the integrity of CloudTrail logs.", "Consider enabling multi-region trails to capture events from all AWS regions.", "Regularly review CloudTrail logs and set up alerts or notifications for suspicious activities."], "estimated_time": "30 minutes to 1 hour", "automation_available": true},
      "created_by": "system",
      "category": "security",
      "metadata": {"tags": [], "category": "security", "severity": "medium", "operation": {"name": "custom", "logic": "result = False\n\nif fetched_value is None:\n    result = False\nelse:\n    for log_file_validation_enabled in fetched_value:\n        if log_file_validation_enabled:\n            result = True\n            break"}, "field_path": "trails[*].log_file_validation_enabled", "resource_type": "con_mon.mappings.aws.CloudTrailResource", "expected_value": null},
      "updated_by": "system",
      "created_at": "2025-09-02 22:03:57.886013",
      "updated_at": "2025-09-02 22:03:57.886014",
      "is_deleted": false
    }
  ],
  control_check_mapping: [
    {
      "control_id": 300,
      "check_id": "owasp-latest-remove-unnecessary-features-and-components-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 166,
      "check_id": "owasp-latest-implement-comprehensive-logging-mechanisms-UserResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 171,
      "check_id": "owasp-latest-implement-comprehensive-logging-mechanisms-UserResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 16,
      "check_id": "owasp-latest-validate-access-controls-on-the-server-side-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 808,
      "check_id": "owasp-latest-implement-secure-software-supply-chain-practices-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 260,
      "check_id": "owasp-latest-conduct-penetration-testing-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 166,
      "check_id": "owasp-latest-log-security-relevant-events-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 171,
      "check_id": "owasp-latest-log-security-relevant-events-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 183,
      "check_id": "owasp-latest-implement-centralized-log-management-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 988,
      "check_id": "owasp-latest-follow-data-protection-regulations-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 16,
      "check_id": "owasp-latest-validate-access-controls-on-the-server-side-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 166,
      "check_id": "owasp-latest-implement-comprehensive-logging-mechanisms-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 171,
      "check_id": "owasp-latest-implement-comprehensive-logging-mechanisms-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 267,
      "check_id": "owasp-latest-implement-secure-configuration-management-processes-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 275,
      "check_id": "owasp-latest-implement-secure-configuration-management-processes-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 492,
      "check_id": "owasp-latest-establish-incident-response-plans-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 988,
      "check_id": "owasp-latest-follow-data-protection-regulations-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 941,
      "check_id": "owasp-latest-implement-secure-key-management-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 948,
      "check_id": "owasp-latest-implement-secure-key-management-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 183,
      "check_id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 1064,
      "check_id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 166,
      "check_id": "owasp-latest-implement-secure-logging-mechanisms-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 171,
      "check_id": "owasp-latest-implement-secure-logging-mechanisms-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 66,
      "check_id": "owasp-latest-enforce-least-privileges-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 16,
      "check_id": "owasp-latest-implement-secure-authentication-mechanisms-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 16,
      "check_id": "owasp-latest-implement-proper-access-control-mechanisms-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 166,
      "check_id": "owasp-latest-implement-comprehensive-logging-mechanisms-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 171,
      "check_id": "owasp-latest-implement-comprehensive-logging-mechanisms-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 300,
      "check_id": "owasp-latest-remove-unnecessary-features-and-components-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 646,
      "check_id": "owasp-latest-regularly-review-and-update-security-procedures-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 295,
      "check_id": "owasp-latest-use-secure-defaults-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 1119,
      "check_id": "owasp-latest-validate-and-sanitize-all-user-input-UserResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 66,
      "check_id": "owasp-latest-enforce-least-privilege-principles-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 16,
      "check_id": "owasp-latest-validate-access-controls-on-the-server-side-UserResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 149,
      "check_id": "owasp-latest-provide-security-awareness-training-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 16,
      "check_id": "owasp-latest-implement-proper-access-control-mechanisms-UserResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 333,
      "check_id": "owasp-latest-establish-disaster-recovery-plans-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 295,
      "check_id": "owasp-latest-regularly-review-and-update-configurations-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 1046,
      "check_id": "owasp-latest-monitor-for-security-advisories-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 183,
      "check_id": "owasp-latest-monitor-for-suspicious-activities-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 183,
      "check_id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 1064,
      "check_id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 183,
      "check_id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 1064,
      "check_id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 931,
      "check_id": "owasp-latest-implement-encryption-for-data-in-transit-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 418,
      "check_id": "owasp-latest-enforce-password-policies-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 646,
      "check_id": "owasp-latest-regularly-review-and-update-security-policies-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 295,
      "check_id": "owasp-latest-use-secure-defaults-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 166,
      "check_id": "owasp-latest-implement-secure-logging-mechanisms-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 171,
      "check_id": "owasp-latest-implement-secure-logging-mechanisms-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 267,
      "check_id": "owasp-latest-implement-secure-configuration-management-processes-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 275,
      "check_id": "owasp-latest-implement-secure-configuration-management-processes-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 295,
      "check_id": "owasp-latest-use-secure-defaults-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 183,
      "check_id": "owasp-latest-monitor-for-suspicious-activities-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 988,
      "check_id": "owasp-latest-implement-data-masking-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 931,
      "check_id": "owasp-latest-use-secure-communication-protocols-(e.g.,-https)-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 16,
      "check_id": "owasp-latest-implement-proper-access-control-mechanisms-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 941,
      "check_id": "owasp-latest-implement-secure-key-management-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 948,
      "check_id": "owasp-latest-implement-secure-key-management-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 16,
      "check_id": "owasp-latest-implement-proper-access-control-mechanisms-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 300,
      "check_id": "owasp-latest-remove-unnecessary-features-and-components-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 988,
      "check_id": "owasp-latest-follow-data-protection-regulations-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 66,
      "check_id": "owasp-latest-enforce-least-privilege-principles-UserResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 235,
      "check_id": "owasp-latest-conduct-regular-security-testing-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 721,
      "check_id": "owasp-latest-conduct-regular-security-testing-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 295,
      "check_id": "owasp-latest-regularly-review-and-update-configurations-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 66,
      "check_id": "owasp-latest-enforce-least-privileges-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 16,
      "check_id": "owasp-latest-implement-role-based-access-control-(rbac)-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 267,
      "check_id": "owasp-latest-implement-secure-deployment-processes-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 808,
      "check_id": "owasp-latest-implement-secure-deployment-processes-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 166,
      "check_id": "owasp-latest-implement-comprehensive-logging-mechanisms-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 171,
      "check_id": "owasp-latest-implement-comprehensive-logging-mechanisms-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 646,
      "check_id": "owasp-latest-regularly-review-and-update-security-procedures-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 66,
      "check_id": "owasp-latest-enforce-least-privilege-principles-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 816,
      "check_id": "owasp-latest-regularly-update-and-patch-third-party-components-GithubResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 988,
      "check_id": "owasp-latest-implement-encryption-for-data-at-rest-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 166,
      "check_id": "owasp-latest-implement-secure-logging-mechanisms-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 171,
      "check_id": "owasp-latest-implement-secure-logging-mechanisms-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 183,
      "check_id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 1064,
      "check_id": "owasp-latest-implement-comprehensive-monitoring-mechanisms-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 77,
      "check_id": "owasp-latest-protect-against-brute-force-attacks-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 808,
      "check_id": "owasp-latest-implement-software-composition-analysis-(sca)-process-GithubResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 492,
      "check_id": "owasp-latest-establish-incident-response-plans-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 808,
      "check_id": "owasp-latest-implement-secure-software-supply-chain-practices-GithubResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 295,
      "check_id": "owasp-latest-regularly-review-and-update-configurations-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 66,
      "check_id": "owasp-latest-enforce-least-privileges-UserResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 295,
      "check_id": "owasp-latest-follow-security-hardening-guidelines-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 166,
      "check_id": "owasp-latest-log-security-relevant-events-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 171,
      "check_id": "owasp-latest-log-security-relevant-events-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 183,
      "check_id": "owasp-latest-implement-centralized-log-management-CloudWatchResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 389,
      "check_id": "owasp-latest-implement-multi-factor-authentication-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 66,
      "check_id": "owasp-latest-enforce-least-privileges-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 267,
      "check_id": "owasp-latest-implement-secure-deployment-processes-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 808,
      "check_id": "owasp-latest-implement-secure-deployment-processes-IAMResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 66,
      "check_id": "owasp-latest-enforce-least-privilege-principles-S3Resource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 235,
      "check_id": "owasp-latest-conduct-regular-security-testing-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    },
    {
      "control_id": 721,
      "check_id": "owasp-latest-conduct-regular-security-testing-CloudTrailResource",
      "created_at": "2025-09-02 16:36:22.455292",
      "updated_at": "2025-09-02 16:36:22.455292",
      "is_deleted": false
    }
  ]
}