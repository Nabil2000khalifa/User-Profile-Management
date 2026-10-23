from unittest.mock import MagicMock

from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError

from app.db.session import check_database_connection


def test_database_health_returns_true_when_select_succeeds() -> None:
    engine = MagicMock(spec=Engine)
    connection = engine.connect.return_value.__enter__.return_value

    assert check_database_connection(engine) is True
    connection.execute.assert_called_once()


def test_database_health_returns_false_for_database_error() -> None:
    engine = MagicMock(spec=Engine)
    engine.connect.side_effect = OperationalError("SELECT 1", {}, Exception("offline"))

    assert check_database_connection(engine) is False
