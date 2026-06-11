import os
import pytest
from unittest.mock import patch, MagicMock

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import sys
from PyQt6.QtWidgets import QApplication

from main import MainController
from data_models import SystemState

def test_main_init_default_data():
    class MockController(MainController):
        def __init__(self):
            self.state = SystemState()

            # mock populate so it doesn't crash
            self.populate_params_tables = MagicMock()
            self.update_diagram = MagicMock()

            self.init_default_data()

    controller = MockController()

    assert len(controller.state.buses) == 13
    assert len(controller.state.lines) == 12

    assert 650 in controller.state.buses
    assert controller.state.buses[650].name == "650 (Slack)"
    assert controller.state.buses[650].type == "slack"
    assert controller.state.buses[650].vn_kv == 13.8

    assert 634 in controller.state.buses
    assert controller.state.buses[634].vn_kv == 0.22
    assert controller.state.buses[634].p_load_kw == 340

    assert 671 in controller.state.buses
    assert controller.state.buses[671].q_load_kvar == 660

    assert 1 in controller.state.lines
    assert controller.state.lines[1].is_transformer is False
    assert controller.state.lines[1].from_bus == 650
    assert controller.state.lines[1].to_bus == 632

    assert 5 in controller.state.lines
    assert controller.state.lines[5].is_transformer is True

    assert 2 in controller.state.lines
    assert controller.state.lines[2].from_bus == 632
    assert controller.state.lines[2].to_bus == 645
    assert controller.state.lines[2].length_km == 0.1524
