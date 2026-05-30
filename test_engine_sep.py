import pytest
from unittest.mock import patch
import pandapower as pp
import io
import sys
from engine_sep import PowerSystemEngine
from data_models import SystemState

def test_run_power_flow_loadflow_not_converged_exception(capsys):
    engine = PowerSystemEngine()
    state = SystemState()
    engine.build_network(state)

    # Mock pp.runpp to raise LoadflowNotConverged
    with patch('pandapower.runpp', side_effect=pp.powerflow.LoadflowNotConverged("Mocked exception")):
        engine.run_power_flow()

    captured = capsys.readouterr()
    assert "Power flow failed: Loadflow did not converge." in captured.out
    assert "Mocked exception" not in captured.out
    assert not engine.results.success

def test_run_power_flow_generic_exception(capsys):
    engine = PowerSystemEngine()
    state = SystemState()
    engine.build_network(state)

    # Mock pp.runpp to raise a generic Exception
    with patch('pandapower.runpp', side_effect=Exception("Secret generic error")):
        engine.run_power_flow()

    captured = capsys.readouterr()
    assert "Power flow failed: An unexpected error occurred." in captured.out
    assert "Secret generic error" not in captured.out
    assert not engine.results.success

def test_run_power_flow_error_path():
    engine = PowerSystemEngine()
    state = SystemState()
    engine.build_network(state)

    # Mock pp.runpp to raise an exception as per the issue rationale
    with patch('pandapower.runpp', side_effect=Exception("Mocked error")):
        engine.run_power_flow()

    # Checking that self.results.success is set to False
    assert not engine.results.success

def test_run_modal_analysis_generic_exception(capsys):
    engine = PowerSystemEngine()
    engine.results.success = True  # Bypass early return

    # In engine_sep.py, it accesses self.net._ppc['internal']['Ybus']
    # If self.net._ppc is None, it throws a TypeError which we can catch
    # But wait, it might just catch TypeError.
    # Let's mock a property. We will just delete _ppc to raise AttributeError.
    del engine.net._ppc

    engine.run_modal_analysis()

    captured = capsys.readouterr()
    assert "Modal analysis failed: An unexpected error occurred." in captured.out
    assert "Secret modal error" not in captured.out
