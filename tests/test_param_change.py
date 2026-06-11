import sys
from PyQt6.QtWidgets import QApplication
from main import MainController
from engine_sep import PowerSystemEngine

app = QApplication(sys.argv)
controller = MainController()

# Simulate what save_params does
# Read from UI and update state
for i in range(controller.ui.table_params_buses.rowCount()):
    bus_id = int(controller.ui.table_params_buses.item(i, 0).text())
    if bus_id in controller.state.buses:
        controller.state.buses[bus_id].p_load_kw = float(controller.ui.table_params_buses.item(i, 1).text())
        controller.state.buses[bus_id].q_load_kvar = float(controller.ui.table_params_buses.item(i, 2).text())
        controller.state.buses[bus_id].p_gen_kw = float(controller.ui.table_params_buses.item(i, 3).text())

for i in range(controller.ui.table_params_lines.rowCount()):
    line_id = controller.ui.table_params_lines.item(i, 0).data(256) # Qt.UserRole
    if line_id in controller.state.lines:
        controller.state.lines[line_id].r_ohm_per_km = float(controller.ui.table_params_lines.item(i, 1).text())
        controller.state.lines[line_id].x_ohm_per_km = float(controller.ui.table_params_lines.item(i, 2).text())
        controller.state.lines[line_id].length_km = float(controller.ui.table_params_lines.item(i, 3).text())

# Also modifying a parameter to see if it causes issues
controller.state.buses[645].p_load_kw = 180.0

engine = PowerSystemEngine()
engine.build_network(controller.state)
engine.run_power_flow()
print("Success after save_params logic:", engine.results.success)

if engine.results.success:
    engine.generate_pv_curve("645")
    print("PV curve points:", len(engine.results.pv_curve_p))

