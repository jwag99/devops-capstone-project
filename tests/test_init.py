import importlib
import unittest
from unittest.mock import patch

import service


class TestServiceInitialization(unittest.TestCase):

    def test_init_db_failure_exits_with_code_4(self):
        """It should log the database error and exit with code 4"""

        with patch(
            "service.models.init_db",
            side_effect=Exception("database unavailable"),
        ), patch(
            "service.sys.exit",
            side_effect=SystemExit(4),
        ) as mock_exit, patch(
            "logging.Logger.critical"
        ) as mock_critical:

            with self.assertRaises(SystemExit):
                importlib.reload(service)

        mock_critical.assert_called_once()
        message = mock_critical.call_args[0]

        self.assertIn("Cannot continue", message[0])
        self.assertIn("database unavailable", str(message[1]))
        mock_exit.assert_called_once_with(4)