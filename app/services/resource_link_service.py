from __future__ import annotations

from app.database import Database
from app.models import ResourceLink


class ResourceLinkService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def link(self, *, project_id: int, resource_type: str, resource_id: str | int, repository_id: int,
             target_type: str, target_value: str = "", resource_parent_id: str | int | None = None,
             github_node_id: str | None = None) -> ResourceLink:
        return self.database.add_resource_link(
            project_id, resource_type, resource_id, repository_id, target_type, target_value,
            resource_parent_id=resource_parent_id, github_node_id=github_node_id,
        )

    def links_for(self, resource_type: str, resource_id: str | int,
                  resource_parent_id: str | int | None = None) -> list[ResourceLink]:
        return self.database.list_resource_links(resource_type, resource_id, resource_parent_id)

    def knowledge_for_target(self, repository_id: int, target_type: str, target_value: str) -> list[ResourceLink]:
        return [link for link in self.database.list_resource_links(repository_id=repository_id)
                if link.target_type == target_type and link.target_value == target_value]

    def unlink(self, link_id: int) -> None:
        self.database.remove_resource_link(link_id)
