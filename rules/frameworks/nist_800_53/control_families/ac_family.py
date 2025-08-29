from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.access_control.access_control_policy import AccessControlPolicyCheck
from rules.checks.access_control.user_account_management import UserAccountManagementCheck
from rules.checks.access_control.account_access_review import AccountAccessReviewCheck
from rules.checks.access_control.privileged_account import PrivilegedAccountCheck
from rules.checks.access_control.access_enforcement import AccessEnforcementCheck
from rules.checks.access_control.information_flow_enforcement import InformationFlowEnforcementCheck
from rules.checks.access_control.separation_of_duties import SeparationOfDutiesCheck
from rules.checks.access_control.least_privilege import LeastPrivilegeCheck
from rules.checks.access_control.unsuccessful_logon_attempts import UnsuccessfulLogonAttemptsCheck
from rules.checks.access_control.system_use_notification import SystemUseNotificationCheck
from rules.checks.access_control.previous_logon_notification import PreviousLogonNotificationCheck
from rules.checks.access_control.concurrent_session_control import ConcurrentSessionControlCheck
from rules.checks.access_control.session_lock import SessionLockCheck
from rules.checks.access_control.session_termination import SessionTerminationCheck
from rules.checks.access_control.permitted_actions_without_auth import PermittedActionsWithoutAuthCheck
from rules.checks.access_control.remote_access import RemoteAccessCheck
from rules.checks.access_control.wireless_access import WirelessAccessCheck
from rules.checks.access_control.mobile_device_access import MobileDeviceAccessCheck
from rules.checks.access_control.external_systems_access import ExternalSystemsAccessCheck
from rules.checks.access_control.information_sharing import InformationSharingCheck
from rules.checks.access_control.publicly_accessible_content import PubliclyAccessibleContentCheck

class ACFamily(BaseControlFamily):
    """Access Control (AC) Family - All AC controls grouped together"""
    
    def __init__(self):
        super().__init__(
            family_id="AC",
            family_name="Access Control"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize all AC controls"""
        controls = [
            # AC-01: Access Control Policy and Procedures
            BaseControl(
                control_id="AC-01",
                control_name="Access Control Policy and Procedures",
                checks=[AccessControlPolicyCheck()]
            ),
            
            # AC-02: Account Management
            BaseControl(
                control_id="AC-02",
                control_name="Account Management",
                checks=[
                    UserAccountManagementCheck(),
                    AccountAccessReviewCheck(),
                    PrivilegedAccountCheck()
                ]
            ),
            
            # AC-03: Access Enforcement
            BaseControl(
                control_id="AC-03",
                control_name="Access Enforcement",
                checks=[AccessEnforcementCheck()]
            ),
            
            # AC-04: Information Flow Enforcement
            BaseControl(
                control_id="AC-04",
                control_name="Information Flow Enforcement",
                checks=[InformationFlowEnforcementCheck()]
            ),
            
            # AC-05: Separation of Duties
            BaseControl(
                control_id="AC-05",
                control_name="Separation of Duties",
                checks=[SeparationOfDutiesCheck()]
            ),
            
            # AC-06: Least Privilege
            BaseControl(
                control_id="AC-06",
                control_name="Least Privilege",
                checks=[LeastPrivilegeCheck()]
            ),
            
            # AC-07: Unsuccessful Logon Attempts
            BaseControl(
                control_id="AC-07",
                control_name="Unsuccessful Logon Attempts",
                checks=[UnsuccessfulLogonAttemptsCheck()]
            ),
            
            # AC-08: System Use Notification
            BaseControl(
                control_id="AC-08",
                control_name="System Use Notification",
                checks=[SystemUseNotificationCheck()]
            ),
            
            # AC-09: Previous Logon Notification
            BaseControl(
                control_id="AC-09",
                control_name="Previous Logon Notification",
                checks=[PreviousLogonNotificationCheck()]
            ),
            
            # AC-10: Concurrent Session Control
            BaseControl(
                control_id="AC-10",
                control_name="Concurrent Session Control",
                checks=[ConcurrentSessionControlCheck()]
            ),
            
            # AC-11: Session Lock
            BaseControl(
                control_id="AC-11",
                control_name="Session Lock",
                checks=[SessionLockCheck()]
            ),
            
            # AC-12: Session Termination
            BaseControl(
                control_id="AC-12",
                control_name="Session Termination",
                checks=[SessionTerminationCheck()]
            ),
            
            # AC-14: Permitted Actions Without Identification or Authentication
            BaseControl(
                control_id="AC-14",
                control_name="Permitted Actions Without Identification or Authentication",
                checks=[PermittedActionsWithoutAuthCheck()]
            ),
            
            # AC-17: Remote Access
            BaseControl(
                control_id="AC-17",
                control_name="Remote Access",
                checks=[RemoteAccessCheck()]
            ),
            
            # AC-18: Wireless Access
            BaseControl(
                control_id="AC-18",
                control_name="Wireless Access",
                checks=[WirelessAccessCheck()]
            ),
            
            # AC-19: Access Control for Mobile Devices
            BaseControl(
                control_id="AC-19",
                control_name="Access Control for Mobile Devices",
                checks=[MobileDeviceAccessCheck()]
            ),
            
            # AC-20: Use of External Information Systems
            BaseControl(
                control_id="AC-20",
                control_name="Use of External Information Systems",
                checks=[ExternalSystemsAccessCheck()]
            ),
            
            # AC-21: Information Sharing
            BaseControl(
                control_id="AC-21",
                control_name="Information Sharing",
                checks=[InformationSharingCheck()]
            ),
            
            # AC-22: Publicly Accessible Content
            BaseControl(
                control_id="AC-22",
                control_name="Publicly Accessible Content",
                checks=[PubliclyAccessibleContentCheck()]
            ),
        ]
        
        # Add all controls to the family
        for control in controls:
            self.add_control(control) 