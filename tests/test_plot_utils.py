import pytest
from plot_utils import PVPlotWidget

def test_plot_curve_empty_lists(qapp):
    widget = PVPlotWidget()
    widget.plot_curve([], [])
    # no exception means it returned early successfully

def test_plot_curve_none_lists(qapp):
    widget = PVPlotWidget()
    widget.plot_curve(None, None)
