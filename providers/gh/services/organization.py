from providers.service import BaseService, service_class
from github import Github
from github.Repository import Repository
from ..models.organization_models import (
    OrganizationMemberData,
    OrganizationTeamData,
    OrganizationData
)

@service_class
class OrganizationService(BaseService):
    def __init__(self, client: Github, repository: Repository):
        super().__init__(client)
        self.repo = repository

    def process(self) -> OrganizationData:
        """Collect organization data and return OrganizationData model"""
        members = []
        teams = []
        outside_collaborators = []
        members_error = None
        teams_error = None
        collaborators_error = None
        
        try:
            members = self._collect_members()
        except Exception as e:
            print(f"Failed to collect members for {self.repo.name}: {e}")
            members_error = str(e)
            
        try:
            teams = self._collect_teams()
        except Exception as e:
            print(f"Failed to collect teams for {self.repo.name}: {e}")
            teams_error = str(e)
            
        try:
            outside_collaborators = self._collect_outside_collaborators()
        except Exception as e:
            print(f"Failed to collect outside collaborators for {self.repo.name}: {e}")
            collaborators_error = str(e)
            
        return OrganizationData(
            repository=self.repo.full_name,
            members=members,
            teams=teams, 
            outside_collaborators=outside_collaborators,
            members_error=members_error,
            teams_error=teams_error,
            collaborators_error=collaborators_error
        )
    
    def _collect_organization_info(self, data, org):
        """Collect basic organization information"""
        try:
            org_info = {
                "login": org.login,
                "id": org.id,
                "name": org.name,
                "company": org.company,
                "blog": org.blog,
                "location": org.location,
                "email": org.email,
                "twitter_username": org.twitter_username,
                "description": org.description,
                "public_repos": org.public_repos,
                "public_gists": org.public_gists,
                "followers": org.followers,
                "following": org.following,
                "html_url": org.html_url,
                "created_at": org.created_at.isoformat() if org.created_at else None,
                "updated_at": org.updated_at.isoformat() if org.updated_at else None,
                "type": org.type,
                "total_private_repos": org.total_private_repos,
                "owned_private_repos": org.owned_private_repos,
                "private_gists": org.private_gists,
                "disk_usage": org.disk_usage,
                "collaborators": org.collaborators,
                "billing_email": getattr(org, 'billing_email', None),
                "plan": {
                    "name": org.plan.name if org.plan else None,
                    "space": org.plan.space if org.plan else None,
                    "private_repos": org.plan.private_repos if org.plan else None,
                    "collaborators": org.plan.collaborators if org.plan else None
                }
            }
            data["organization_info"] = org_info
            
        except Exception as e:
            print(f"Could not get organization info: {e}")
            data["organization_info"] = {"error": str(e)}
    
    def _collect_organization_members(self, data, org):
        """Collect organization members"""
        try:
            members = {}
            try:
                for member in org.get_members():
                    member_data = {
                        "login": member.login,
                        "id": member.id,
                        "type": member.type,
                        "site_admin": member.site_admin,
                        "html_url": member.html_url,
                        "avatar_url": member.avatar_url,
                        "organizations_url": member.organizations_url
                    }
                    
                    # Try to get membership details
                    try:
                        membership = org.get_membership(member.login)
                        member_data["membership"] = {
                            "role": membership.role,
                            "state": membership.state
                        }
                    except:
                        pass
                        
                    members[member.login] = member_data
                    
            except Exception as e:
                print(f"Could not access organization members (may require organization permissions): {e}")
                members = {"error": "Access denied or not available"}
                
            data["members"] = members
            
        except Exception as e:
            print(f"Error collecting organization members: {e}")
            data["members"] = {}
    
    def _collect_organization_teams(self, data, org):
        """Collect organization teams"""
        try:
            teams = {}
            try:
                for team in org.get_teams():
                    team_data = {
                        "id": team.id,
                        "name": team.name,
                        "slug": team.slug,
                        "description": team.description,
                        "privacy": team.privacy,
                        "permission": team.permission,
                        "members_count": team.members_count,
                        "repos_count": team.repos_count,
                        "created_at": team.created_at.isoformat() if team.created_at else None,
                        "updated_at": team.updated_at.isoformat() if team.updated_at else None,
                        "members": [],
                        "repositories": []
                    }
                    
                    # Try to get team members
                    try:
                        team_members = []
                        for member in team.get_members():
                            team_members.append({
                                "login": member.login,
                                "id": member.id
                            })
                        team_data["members"] = team_members
                    except:
                        pass
                    
                    # Try to get team repositories
                    try:
                        team_repos = []
                        for repo in team.get_repos():
                            team_repos.append({
                                "name": repo.name,
                                "full_name": repo.full_name,
                                "permission": getattr(repo, 'permissions', {})
                            })
                        team_data["repositories"] = team_repos
                    except:
                        pass
                        
                    teams[team.slug] = team_data
                    
            except Exception as e:
                print(f"Could not access organization teams (may require organization permissions): {e}")
                teams = {"error": "Access denied or not available"}
                
            data["teams"] = teams
            
        except Exception as e:
            print(f"Error collecting organization teams: {e}")
            data["teams"] = {}
    
    def _collect_organization_settings(self, data, org):
        """Collect organization settings"""
        try:
            settings = {}
            try:
                # Collect available organization settings
                settings = {
                    "default_repository_permission": getattr(org, 'default_repository_permission', None),
                    "has_organization_projects": getattr(org, 'has_organization_projects', None),
                    "has_repository_projects": getattr(org, 'has_repository_projects', None),
                    "hooks_url": getattr(org, 'hooks_url', None),
                    "issues_url": getattr(org, 'issues_url', None),
                    "members_url": getattr(org, 'members_url', None),
                    "public_members_url": getattr(org, 'public_members_url', None),
                    "repos_url": getattr(org, 'repos_url', None),
                    "url": getattr(org, 'url', None),
                    "members_can_create_repositories": getattr(org, 'members_can_create_repositories', None),
                    "two_factor_requirement_enabled": getattr(org, 'two_factor_requirement_enabled', None),
                    "members_allowed_repository_creation_type": getattr(org, 'members_allowed_repository_creation_type', None),
                    "members_can_create_public_repositories": getattr(org, 'members_can_create_public_repositories', None),
                    "members_can_create_private_repositories": getattr(org, 'members_can_create_private_repositories', None),
                    "members_can_create_internal_repositories": getattr(org, 'members_can_create_internal_repositories', None)
                }
                
            except Exception as e:
                print(f"Could not access organization settings: {e}")
                settings = {"error": "Access denied or not available"}
                
            data["organization_settings"] = settings
            
        except Exception as e:
            print(f"Error collecting organization settings: {e}")
            data["organization_settings"] = {}
    
    def _collect_members(self) -> list[OrganizationMemberData]:
        """Collect organization members"""
        members = []
        try:
            if self.repo.organization:
                org = self.repo.organization
                for member in org.get_members():
                    try:
                        member_data = OrganizationMemberData(
                            login=member.login,
                            id=member.id,
                            type=member.type,
                            site_admin=member.site_admin,
                            role="member"  # Default role, would need additional API calls
                        )
                        members.append(member_data)
                    except Exception as e:
                        print(f"Error processing member {member.login}: {e}")
        except Exception as e:
            print(f"Could not access organization members (may require organization permissions): {e}")
            raise e
            
        return members

    def _collect_teams(self) -> list[OrganizationTeamData]:
        """Collect organization teams"""
        teams = []
        try:
            if self.repo.organization:
                org = self.repo.organization
                for team in org.get_teams():
                    try:
                        team_data = OrganizationTeamData(
                            id=team.id,
                            name=team.name,
                            slug=team.slug,
                            description=team.description,
                            privacy=team.privacy,
                            permission=team.permission,
                            members_count=team.members_count,
                            repos_count=team.repos_count
                        )
                        teams.append(team_data)
                    except Exception as e:
                        print(f"Error processing team {team.name}: {e}")
        except Exception as e:
            print(f"Could not access organization teams (may require organization permissions): {e}")
            raise e
            
        return teams

    def _collect_outside_collaborators(self) -> list[OrganizationMemberData]:
        """Collect outside collaborators"""
        collaborators = []
        try:
            if self.repo.organization:
                org = self.repo.organization
                for collaborator in org.get_outside_collaborators():
                    try:
                        collab_data = OrganizationMemberData(
                            login=collaborator.login,
                            id=collaborator.id,
                            type=collaborator.type,
                            site_admin=collaborator.site_admin,
                            role="outside_collaborator"
                        )
                        collaborators.append(collab_data)
                    except Exception as e:
                        print(f"Error processing outside collaborator {collaborator.login}: {e}")
        except Exception as e:
            print(f"Could not access outside collaborators (may require organization permissions): {e}")
            raise e
            
        return collaborators 