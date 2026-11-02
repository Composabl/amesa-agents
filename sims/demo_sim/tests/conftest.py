# Copyright (C) Amesa, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Pytest configuration for demo_sim tests.

This file mocks amesa_core and other private dependencies so tests can run
without the private AMESA packages installed.
"""

import sys
from unittest.mock import MagicMock

# Mock amesa_core and its submodules before any tests import them
mock_amesa_core = MagicMock()
mock_amesa_core.utils = MagicMock()
mock_amesa_core.utils.logger = MagicMock()
mock_amesa_core.utils.logger.get_logger = MagicMock(return_value=MagicMock())
mock_amesa_core.orchestration = MagicMock()
mock_amesa_core.orchestration.scenario = MagicMock()
mock_amesa_core.orchestration.scenario.scenario = MagicMock()
mock_amesa_core.orchestration.scenario.scenario.Scenario = MagicMock

sys.modules['amesa_core'] = mock_amesa_core
sys.modules['amesa_core.utils'] = mock_amesa_core.utils
sys.modules['amesa_core.utils.logger'] = mock_amesa_core.utils.logger
sys.modules['amesa_core.orchestration'] = mock_amesa_core.orchestration
sys.modules['amesa_core.orchestration.scenario'] = mock_amesa_core.orchestration.scenario
sys.modules['amesa_core.orchestration.scenario.scenario'] = mock_amesa_core.orchestration.scenario.scenario