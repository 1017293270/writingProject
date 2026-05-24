from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "ai_novel_platform"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls.from_mapping(os.environ)

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> "Settings":
        return cls(
            db_host=values.get("AI_NOVEL_DB_HOST", "127.0.0.1"),
            db_port=int(values.get("AI_NOVEL_DB_PORT", "3306")),
            db_user=values.get("AI_NOVEL_DB_USER", "root"),
            db_password=values.get("AI_NOVEL_DB_PASSWORD", ""),
            db_name=values.get("AI_NOVEL_DB_NAME", "ai_novel_platform"),
        )

    def connection_config(self) -> dict[str, object]:
        config: dict[str, object] = {
            "host": self.db_host,
            "port": self.db_port,
            "user": self.db_user,
            "password": self.db_password,
        }
        if self.db_name:
            config["database"] = self.db_name
        return config
