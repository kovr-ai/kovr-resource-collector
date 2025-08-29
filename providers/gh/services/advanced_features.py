from providers.service import BaseService, service_class
from github import Github
from github.Repository import Repository
from ..models.advanced_features_models import (
    TagData,
    WebhookData,
    AdvancedFeaturesData
)

@service_class
class AdvancedFeaturesService(BaseService):
    def __init__(self, client: Github, repository: Repository):
        super().__init__(client)
        self.repo = repository

    def process(self) -> AdvancedFeaturesData:
        """Collect advanced GitHub features data and return AdvancedFeaturesData model"""
        tags = []
        webhooks = []
        tags_error = None
        webhooks_error = None
        
        try:
            tags = self._collect_tags()
        except Exception as e:
            print(f"Could not get tags for {self.repo.name}: {e}")
            tags_error = str(e)
            
        try:
            webhooks = self._collect_webhooks()
        except Exception as e:
            print(f"Could not get webhooks for {self.repo.name}: {e}")
            webhooks_error = str(e)
            
        return AdvancedFeaturesData(
            repository=self.repo.full_name,
            tags=tags,
            webhooks=webhooks,
            tags_error=tags_error,
            webhooks_error=webhooks_error
        )

    def _collect_tags(self) -> list[TagData]:
        """Collect repository tags/releases"""
        tags = []
        try:
            tags_list = list(self.repo.get_tags())[:20]  # Recent 20 tags to match original
            for tag in tags_list:
                tag_data = TagData(
                    name=tag.name,
                    commit_sha=tag.commit.sha,
                    commit_date=tag.commit.commit.author.date if tag.commit.commit.author.date else None
                )
                tags.append(tag_data)
        except Exception as e:
            print(f"Could not get tags for {self.repo.name}: {e}")
            raise e
            
        return tags

    def _collect_webhooks(self) -> list[WebhookData]:
        """Collect repository webhooks"""
        webhooks = []
        try:
            hooks_list = list(self.repo.get_hooks())
            for hook in hooks_list:
                hook_data = WebhookData(
                    id=hook.id,
                    name=hook.name,
                    active=hook.active,
                    events=hook.events,
                    config={k: v for k, v in hook.config.items() if k != 'secret'},  # Filter out secrets
                    created_at=hook.created_at,
                    updated_at=hook.updated_at
                )
                webhooks.append(hook_data)
        except Exception as e:
            print(f"Could not get webhooks for {self.repo.name}: {e}")
            raise e
            
        return webhooks 