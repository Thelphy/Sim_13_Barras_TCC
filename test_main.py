import os
import pytest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from main import MainController

@patch('main.MainWindowUI')
@patch('main.QApplication')
def test_main_init_default_data(mock_qapp, mock_ui):
    controller = MainController()

    # The init_default_data is called in __init__

    # 1. Check dictionary sizes
    assert len(controller.state.buses) == 13, "Should have 13 buses"
    assert len(controller.state.lines) == 12, "Should have 12 lines"

    # 2. Check some specific keys and values for Buses
    assert 650 in controller.state.buses
    assert controller.state.buses[650].name == "650 (Slack)"
    assert controller.state.buses[650].type == "slack"
    assert controller.state.buses[650].vn_kv == 115.0

    assert 634 in controller.state.buses
    assert controller.state.buses[634].vn_kv == 0.48
    assert controller.state.buses[634].p_load_kw == 400

    assert 671 in controller.state.buses
    assert controller.state.buses[671].q_load_kvar == 660

    # 3. Check some specific keys and values for Lines
    assert 1 in controller.state.lines
    assert controller.state.lines[1].is_transformer is True
    assert controller.state.lines[1].from_bus == 650
    assert controller.state.lines[1].to_bus == 632

    assert 5 in controller.state.lines
    assert controller.state.lines[5].is_transformer is True

    assert 2 in controller.state.lines
    assert controller.state.lines[2].from_bus == 632
    assert controller.state.lines[2].to_bus == 645
    assert controller.state.lines[2].length_km == 0.15
