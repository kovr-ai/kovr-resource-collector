from providers.service import BaseService, service_class
from github import Github
from github.Repository import Repository
from ..models.base_models import (
    RepositoryBasicInfo, 
    RepositoryMetadata, 
    BranchData, 
    StatisticsData, 
    RepositoriesData
)

@service_class
class RepositoriesService(BaseService):
    def __init__(self, client: Github, repository: Repository):
        super().__init__(client)
        self.repo = repository

    def process(self) -> RepositoriesData:
        """Collect basic repository data and return RepositoriesData model"""
        try:
            # Create basic info model
            basic_info = RepositoryBasicInfo(
                id=self.repo.id,
                name=self.repo.name,
                full_name=self.repo.full_name,
                description=self.repo.description,
                private=self.repo.private,
                owner=self.repo.owner.login,
                html_url=self.repo.html_url,
                clone_url=self.repo.clone_url,
                ssh_url=self.repo.ssh_url,
                size=self.repo.size,
                language=self.repo.language,
                created_at=self.repo.created_at,
                updated_at=self.repo.updated_at,
                pushed_at=self.repo.pushed_at,
                stargazers_count=self.repo.stargazers_count,
                watchers_count=self.repo.watchers_count,
                forks_count=self.repo.forks_count,
                open_issues_count=self.repo.open_issues_count,
                archived=self.repo.archived,
                disabled=self.repo.disabled
            )
            
            # Create metadata model
            metadata = RepositoryMetadata(
                default_branch=self.repo.default_branch,
                topics=self.repo.get_topics() if hasattr(self.repo, 'get_topics') else [],
                has_issues=self.repo.has_issues,
                has_projects=self.repo.has_projects,
                has_wiki=self.repo.has_wiki,
                has_pages=self.repo.has_pages,
                has_downloads=self.repo.has_downloads,
                has_discussions=getattr(self.repo, 'has_discussions', False),
                is_template=getattr(self.repo, 'is_template', False),
                license={"name": self.repo.license.name, "key": self.repo.license.key} if self.repo.license else None
            )
            
            # Collect branch data
            branches = self._collect_branches()
            
            # Collect statistics
            statistics = self._collect_statistics()
            
            # Create and return the complete model
            return RepositoriesData(
                repository=self.repo.full_name,
                basic_info=basic_info,
                metadata=metadata,
                branches=branches,
                statistics=statistics
            )
            
        except Exception as e:
            print(f"Error collecting repository data for {self.repo.name}: {e}")
            # Return minimal model with error info
            basic_info = RepositoryBasicInfo(
                id=getattr(self.repo, 'id', 0),
                name=getattr(self.repo, 'name', 'unknown'),
                full_name=getattr(self.repo, 'full_name', 'unknown'),
                private=getattr(self.repo, 'private', True),
                owner=getattr(self.repo.owner, 'login', 'unknown') if hasattr(self.repo, 'owner') else 'unknown',
                html_url=getattr(self.repo, 'html_url', ''),
                clone_url=getattr(self.repo, 'clone_url', ''),
                ssh_url=getattr(self.repo, 'ssh_url', ''),
                size=getattr(self.repo, 'size', 0),
                created_at=getattr(self.repo, 'created_at', None)
            )
            
            metadata = RepositoryMetadata(default_branch="main")
            statistics = StatisticsData()
            
            return RepositoriesData(
                repository=getattr(self.repo, 'full_name', 'unknown'),
                basic_info=basic_info,
                metadata=metadata,
                branches=[],
                statistics=statistics
            )

    def _collect_branches(self) -> list[BranchData]:
        """Collect repository branches data"""
        branches = []
        try:
            branch_list = list(self.repo.get_branches())[:10]  # Limit to 10 branches
            for branch in branch_list:
                branch_data = BranchData(
                    name=branch.name,
                    sha=branch.commit.sha,
                    protected=branch.protected,
                    protection_details={}  # Could be expanded with actual protection data
                )
                branches.append(branch_data)
        except Exception as e:
            print(f"Could not get branches for {self.repo.name}: {e}")
            
        return branches

    def _collect_statistics(self) -> StatisticsData:
        """Collect repository statistics"""
        try:
            # Get languages
            languages = {}
            try:
                languages = self.repo.get_languages()
            except Exception as e:
                print(f"Could not get languages for {self.repo.name}: {e}")
            
            # Get contributors count
            contributors_count = 0
            try:
                contributors = list(self.repo.get_contributors())
                contributors_count = len(contributors)
            except Exception as e:
                print(f"Could not get contributors for {self.repo.name}: {e}")
                
            return StatisticsData(
                total_commits=0,  # Would require more complex API calls
                contributors_count=contributors_count,
                languages=languages,
                code_frequency=[]  # Would require additional API calls
            )
            
        except Exception as e:
            print(f"Could not get statistics for {self.repo.name}: {e}")
            return StatisticsData() 