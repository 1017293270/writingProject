from writing_project.config import Settings


def test_settings_from_mapping_uses_defaults():
    settings = Settings.from_mapping({"AI_NOVEL_DB_USER": "writer", "AI_NOVEL_DB_NAME": "novels"})

    assert settings.db_host == "127.0.0.1"
    assert settings.db_port == 3306
    assert settings.db_user == "writer"
    assert settings.db_password == ""
    assert settings.db_name == "novels"


def test_settings_connection_config_excludes_database_when_empty():
    settings = Settings(db_user="root", db_name="")

    assert settings.connection_config() == {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "",
    }
