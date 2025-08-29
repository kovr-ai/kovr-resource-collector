from providers.service import BaseService, service_class
from github import Github
from github.Repository import Repository
from ..models.actions_models import WorkflowRun, WorkflowData, ActionsData

@service_class
class ActionsService(BaseService):
    def __init__(self, client: Github, repository: Repository):
        super().__init__(client)
        self.repo = repository

    def process(self) -> ActionsData:
        """Collect GitHub Actions/CI-CD data and return ActionsData model"""
        workflows_dict = {}
        
        try:
            workflows_list = list(self.repo.get_workflows())
            
            for workflow in workflows_list:
                try:
                    # Collect recent workflow runs
                    recent_runs = []
                    runs_list = list(workflow.get_runs())[:10]  # Limit recent runs
                    for run in runs_list:
                        run_data = WorkflowRun(
                            id=run.id,
                            name=run.name or workflow.name,
                            head_branch=run.head_branch,
                            head_sha=run.head_sha,
                            status=run.status,
                            conclusion=run.conclusion,
                            created_at=run.created_at,
                            updated_at=run.updated_at,
                            run_number=getattr(run, 'run_number', 0),
                            run_attempt=getattr(run, 'run_attempt', 1)
                        )
                        recent_runs.append(run_data)
                        
                    # Create workflow data model
                    workflow_data = WorkflowData(
                        id=workflow.id,
                        name=workflow.name,
                        path=workflow.path,
                        state=workflow.state,
                        created_at=workflow.created_at,
                        updated_at=workflow.updated_at,
                        badge_url=workflow.badge_url,
                        recent_runs=recent_runs
                    )
                    
                    workflows_dict[workflow.name] = workflow_data
                    
                except Exception as e:
                    print(f"Error collecting workflow data for {workflow.name}: {e}")
                    # Create minimal workflow data for failed workflows
                    workflow_data = WorkflowData(
                        id=getattr(workflow, 'id', 0),
                        name=getattr(workflow, 'name', 'unknown'),
                        path=getattr(workflow, 'path', ''),
                        state=getattr(workflow, 'state', 'unknown'),  
                        created_at=getattr(workflow, 'created_at', None),
                        updated_at=getattr(workflow, 'updated_at', None),
                        badge_url=getattr(workflow, 'badge_url', ''),
                        recent_runs=[]
                    )
                    workflows_dict[workflow.name] = workflow_data
                    
        except Exception as e:
            print(f"Could not get workflows for {self.repo.name}: {e}")
            
        # Create and return the complete ActionsData model
        return ActionsData(
            repository=self.repo.full_name,
            workflows=workflows_dict
        ) 