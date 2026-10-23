import pytest
from pydantic import SecretStr, ValidationError

from app.core.settings import Settings


def test_settings_accepts_mysql_pymysql_url() -> None:
    settings = Settings(
        _env_file=None,
        database_url="mysql+pymysql://profile_app:secret@localhost:3306/user_profile_management",
        session_secret="test-session-secret",
    )

    assert settings.database_url == SecretStr(
        "mysql+pymysql://profile_app:secret@localhost:3306/user_profile_management"
    )


def test_settings_rejects_non_mysql_database_url() -> None:
    with pytest.raises(ValidationError, match="mysql\\+pymysql"):
        Settings(
            _env_file=None,
            database_url="sqlite:///test.db",
            session_secret="test-session-secret",
        )


def test_settings_loads_values_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "DATABASE_URL=mysql+pymysql://profile_app:secret@localhost:3306/user_profile_management",
                "SESSION_SECRET=file-session-secret",
                "APP_ENV=test",
                "FRONTEND_ORIGIN=http://testserver",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.app_env == "test"
    assert settings.frontend_origin == "http://testserver"
    assert settings.database_url.get_secret_value().endswith(
        "/user_profile_management"
    )
