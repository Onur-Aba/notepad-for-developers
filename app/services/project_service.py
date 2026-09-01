from __future__ import annotations

from app.database import Database
from app.models import Project


class ProjectService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, name: str, description: str = "") -> Project:
        return self.database.create_project(name, description)

    def rename(self, project_id: int, name: str, description: str = "") -> None:
        self.database.update_project(project_id, name, description)

    def archive(self, project_id: int) -> None:
        self.database.archive_project(project_id)

    def move_to_trash(self, project_id: int) -> None:
        self.database.trash_project(project_id)

    def restore(self, project_id: int) -> None:
        self.database.restore_project(project_id)

    def permanently_delete(self, project_id: int) -> None:
        self.database.permanently_delete_project(project_id)
