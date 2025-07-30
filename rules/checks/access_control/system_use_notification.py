class SystemUseNotificationCheck:
    def check_aws(self, data):
        # TODO: Implement AWS-specific logic for system use notification
        # This would check for banner messages, terms of use, etc.
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "AWS system use notification check not implemented"
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace system use notification check not implemented"
        } 