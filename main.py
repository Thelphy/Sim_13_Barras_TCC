import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal

from data_models import SystemState, BusData, LineData
from ui_main import MainWindowUI
from engine_sep import PowerSystemEngine
from plot_utils import populate_table

class SimulationThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, state, target_bus):
        super().__init__()
        self.state = state
        self.target_bus = target_bus

    def run(self):
        engine = PowerSystemEngine()
        engine.build_network(self.state)
        engine.run_power_flow()
        engine.run_modal_analysis()
        if self.target_bus:
            engine.generate_pv_curve(self.target_bus)
        self.finished.emit(engine.results)

class MainController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ui = MainWindowUI()
        self.state = SystemState()

        self.init_default_data()
        self.setup_connections()

        # Initial draw
        self.update_diagram()
        self.populate_target_combo()

    def init_default_data(self):
        # 13 Bus system (Simplified generic parameters)
        # Bus 1 is Slack, Bus 2-13 are PQ or PV
        self.state.buses[1] = BusData(id=1, name="B1 (Slack)", vn_kv=13.8, type='slack', v_target_pu=1.0)
        self.state.buses[2] = BusData(id=2, name="B2", vn_kv=13.8, type='pq', p_load_kw=1000, q_load_kvar=500)
        self.state.buses[3] = BusData(id=3, name="B3", vn_kv=13.8, type='pq', p_load_kw=800, q_load_kvar=400)
        self.state.buses[4] = BusData(id=4, name="B4", vn_kv=13.8, type='pq', p_load_kw=1200, q_load_kvar=600)
        self.state.buses[5] = BusData(id=5, name="B5", vn_kv=13.8, type='pq', p_load_kw=500, q_load_kvar=200)
        self.state.buses[6] = BusData(id=6, name="B6", vn_kv=13.8, type='pq', p_load_kw=400, q_load_kvar=150)
        self.state.buses[7] = BusData(id=7, name="B7", vn_kv=13.8, type='pq', p_load_kw=900, q_load_kvar=450)
        self.state.buses[8] = BusData(id=8, name="B8", vn_kv=13.8, type='pq', p_load_kw=1100, q_load_kvar=550)
        self.state.buses[9] = BusData(id=9, name="B9", vn_kv=13.8, type='pq', p_load_kw=600, q_load_kvar=300)
        self.state.buses[10] = BusData(id=10, name="B10", vn_kv=13.8, type='pq', p_load_kw=700, q_load_kvar=350)
        self.state.buses[11] = BusData(id=11, name="B11", vn_kv=13.8, type='pq', p_load_kw=850, q_load_kvar=400)
        self.state.buses[12] = BusData(id=12, name="B12", vn_kv=13.8, type='pq', p_load_kw=950, q_load_kvar=450)
        self.state.buses[13] = BusData(id=13, name="B13", vn_kv=13.8, type='pq', p_load_kw=1050, q_load_kvar=500)

        # Connect the buses radially/meshed
        self.state.lines[1] = LineData(1, 1, 2, 5.0, 0.1, 0.3)
        self.state.lines[2] = LineData(2, 2, 3, 2.0, 0.05, 0.1)
        self.state.lines[3] = LineData(3, 3, 4, 3.0, 0.08, 0.15)
        self.state.lines[4] = LineData(4, 2, 5, 4.0, 0.12, 0.2)
        self.state.lines[5] = LineData(5, 5, 6, 2.5, 0.06, 0.12)
        self.state.lines[6] = LineData(6, 4, 7, 3.5, 0.09, 0.18)
        self.state.lines[7] = LineData(7, 7, 8, 1.5, 0.04, 0.08)
        self.state.lines[8] = LineData(8, 5, 9, 4.5, 0.11, 0.22)
        self.state.lines[9] = LineData(9, 9, 10, 2.0, 0.05, 0.1)
        self.state.lines[10] = LineData(10, 10, 11, 3.0, 0.07, 0.14)
        self.state.lines[11] = LineData(11, 8, 12, 5.5, 0.13, 0.25)
        self.state.lines[12] = LineData(12, 12, 13, 1.0, 0.02, 0.05)

    def setup_connections(self):
        self.ui.btn_simulate.clicked.connect(self.run_simulation)
        self.ui.diagram_view.data_updated.connect(self.update_diagram)

    def populate_target_combo(self):
        self.ui.combo_target_bus.clear()
        for bus in self.state.buses.values():
            if bus.type == 'pq':
                self.ui.combo_target_bus.addItem(bus.name)

    def update_diagram(self):
        self.ui.diagram_view.draw_network(self.state)

    def run_simulation(self):
        self.ui.btn_simulate.setEnabled(False)
        self.ui.btn_simulate.setText("Simulando...")

        target_bus = self.ui.combo_target_bus.currentText()

        self.thread = SimulationThread(self.state, target_bus)
        self.thread.finished.connect(self.on_simulation_finished)
        self.thread.start()

    def on_simulation_finished(self, results):
        self.ui.btn_simulate.setEnabled(True)
        self.ui.btn_simulate.setText("Iniciar Simulação")

        if not results.success:
            QMessageBox.critical(self.ui, "Erro", "A simulação (fluxo de potência) divergiu ou falhou.")
            return

        # Update UI Tables
        bus_headers = ["Barra", "V (PU)", "Ângulo (°)", "P (MW)", "Q (MVAr)"]
        populate_table(self.ui.table_bus_results, results.bus_results, bus_headers)

        line_headers = ["Linha", "P_in (MW)", "Q_in (MVAr)", "P_out (MW)", "Q_out (MVAr)", "Perda (MW)", "Carga (%)"]
        populate_table(self.ui.table_line_results, results.line_results, line_headers)

        modal_data = []
        if results.participation_factors:
            for i, (bus_name, pf) in enumerate(results.participation_factors.items()):
                eig_val = results.eigenvalues[i] if i < len(results.eigenvalues) else "-"
                modal_data.append([bus_name, f"{eig_val}", f"{pf:.4f}"])

        modal_headers = ["Barra", "Autovalor (Real)", "Fator de Participação"]
        populate_table(self.ui.table_modal_results, modal_data, modal_headers)

        # Update Plot
        self.ui.pv_plot.plot_curve(results.pv_curve_p, results.pv_curve_v)

        # Switch focus to results tab
        self.ui.tabs.setCurrentIndex(1)

    def run(self):
        self.ui.show()
        sys.exit(self.app.exec())

if __name__ == '__main__':
    controller = MainController()
    controller.run()
