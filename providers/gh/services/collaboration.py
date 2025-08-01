from providers.service import BaseService, service_class
from github import Github
from github.Repository import Repository
from ..models.collaboration_models import (
    IssueData,
    PullRequestData,
    CollaboratorData,
    CollaborationData
)

@service_class
class CollaborationService(BaseService):
    def __init__(self, client: Github, repository: Repository):
        super().__init__(client)
        self.repo = repository

    def process(self) -> CollaborationData:
        """Collect collaboration data and return CollaborationData model"""
        issues = []
        pull_requests = []
        collaborators = []
        
        try:
            # Collect issues
            issues = self._collect_issues()
        except Exception as e:
            print(f"Failed to collect issues for {self.repo.name}: {e}")
            
        try:
            # Collect pull requests
            pull_requests = self._collect_pull_requests()
        except Exception as e:
            print(f"Failed to collect pull requests for {self.repo.name}: {e}")
            
        try:
            # Collect collaborators
            collaborators = self._collect_collaborators()
        except Exception as e:
            print(f"Failed to collect collaborators for {self.repo.name}: {e}")
            
        return CollaborationData(
            repository=self.repo.full_name,
            issues=issues,
            pull_requests=pull_requests,
            collaborators=collaborators
        )
    
    def _collect_collaborators(self) -> list[CollaboratorData]:
        """Collect repository collaborators"""
        collaborators = []
        try:
            collaborators_list = list(self.repo.get_collaborators())
            for collaborator in collaborators_list:
                try:
                    # Extract actual boolean permission values from PyGithub object
                    permissions = {}
                    if hasattr(collaborator, 'permissions') and collaborator.permissions:
                        perms = collaborator.permissions
                        permissions = {
                            "admin": getattr(perms, 'admin', False),
                            "maintain": getattr(perms, 'maintain', False),
                            "push": getattr(perms, 'push', False),
                            "pull": getattr(perms, 'pull', False),
                            "triage": getattr(perms, 'triage', False)
                        }
                    
                    collab_data = CollaboratorData(
                        login=collaborator.login,
                        permissions=permissions,
                        role_name=None  # This would need additional API calls to determine
                    )
                    collaborators.append(collab_data)
                except Exception as e:
                    print(f"Error processing collaborator {collaborator.login}: {e}")
                    
        except Exception as e:
            print(f"Could not get collaborators for {self.repo.name}: {e}")
            
        return collaborators
    
    def _collect_issues(self) -> list[IssueData]:
        """Collect repository issues"""
        issues = []
        try:
            issue_list = list(self.repo.get_issues(state='all'))[:50]  # Limit to prevent overload
            for issue in issue_list:
                try:
                    issue_data = IssueData(
                        number=issue.number,
                        title=issue.title,
                        state=issue.state,
                        user=issue.user.login,
                        created_at=issue.created_at,
                        updated_at=issue.updated_at,
                        closed_at=issue.closed_at,
                        labels=[label.name for label in issue.labels],
                        assignees=[assignee.login for assignee in issue.assignees],
                        comments_count=issue.comments,
                        is_pull_request=issue.pull_request is not None
                    )
                    issues.append(issue_data)
                except Exception as e:
                    print(f"Error processing issue #{issue.number}: {e}")
                    
        except Exception as e:
            print(f"Could not get issues for {self.repo.name}: {e}")
            
        return issues
    
    def _collect_pull_requests(self) -> list[PullRequestData]:
        """Collect repository pull requests"""
        pull_requests = []
        try:
            pr_list = list(self.repo.get_pulls(state='all'))[:30]  # Limit to prevent overload
            for pr in pr_list:
                try:
                    pr_data = PullRequestData(
                        number=pr.number,
                        title=pr.title,
                        state=pr.state,
                        user=pr.user.login,
                        created_at=pr.created_at,
                        updated_at=pr.updated_at,
                        closed_at=pr.closed_at,
                        merged_at=pr.merged_at,
                        base_branch=pr.base.ref,
                        head_branch=pr.head.ref,
                        draft=pr.draft,
                        mergeable=pr.mergeable,
                        additions=pr.additions,
                        deletions=pr.deletions,
                        changed_files=pr.changed_files,
                        commits=pr.commits,
                        comments=pr.comments,
                        review_comments=pr.review_comments
                    )
                    pull_requests.append(pr_data)
                except Exception as e:
                    print(f"Error processing PR #{pr.number}: {e}")
                    
        except Exception as e:
            print(f"Could not get pull requests for {self.repo.name}: {e}")
            
        return pull_requests 