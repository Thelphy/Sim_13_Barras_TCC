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

    # Simular (Mock) pp.runpp para lançar LoadflowNotConverged
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

    # Simular (Mock) pp.runpp para lançar uma Exception genérica
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

    # Simular (Mock) pp.runpp para lançar uma exceção
    with patch('pandapower.runpp', side_effect=Exception("Mocked error")):
        engine.run_power_flow()

    # Verificar se self.results.success foi definido como False
    assert not engine.results.success

def test_generate_pv_curve_not_success():
    engine = PowerSystemEngine()
    engine.results.success = False

    result = engine.generate_pv_curve("Bus 1")

    assert result is None
