import sys
import csv
import math
from PyQt6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem, QFileDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt

from data_models import SystemState, BusData, LineData
from ui_main import MainWindowUI
from engine_sep import PowerSystemEngine
from plot_utils import populate_table

def safe_float(val_str):
    v = float(val_str)
    if not math.isfinite(v):
        raise ValueError(f"Value '{val_str}' is not a finite float.")
    return v

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
        # 13 Bus system based on IEEE 13 Node Test Feeder layout
        self.state.buses[650] = BusData(id=650, name="650 (Slack)", vn_kv=4.16, type='slack', v_target_pu=1.0)
        self.state.buses[632] = BusData(id=632, name="632", vn_kv=4.16, type='pq', p_load_kw=0, q_load_kvar=0)
        self.state.buses[645] = BusData(id=645, name="645", vn_kv=4.16, type='pq', p_load_kw=170, q_load_kvar=125)
        self.state.buses[646] = BusData(id=646, name="646", vn_kv=4.16, type='pq', p_load_kw=0, q_load_kvar=0)
        self.state.buses[633] = BusData(id=633, name="633", vn_kv=4.16, type='pq', p_load_kw=0, q_load_kvar=0)
        self.state.buses[634] = BusData(id=634, name="634", vn_kv=0.48, type='pq', p_load_kw=400, q_load_kvar=290)
        self.state.buses[671] = BusData(id=671, name="671", vn_kv=4.16, type='pq', p_load_kw=1155, q_load_kvar=660)
        self.state.buses[684] = BusData(id=684, name="684", vn_kv=4.16, type='pq', p_load_kw=0, q_load_kvar=0)
        self.state.buses[611] = BusData(id=611, name="611", vn_kv=4.16, type='pq', p_load_kw=170, q_load_kvar=80)
        self.state.buses[652] = BusData(id=652, name="652", vn_kv=4.16, type='pq', p_load_kw=128, q_load_kvar=86)
        self.state.buses[692] = BusData(id=692, name="692", vn_kv=4.16, type='pq', p_load_kw=170, q_load_kvar=151)
        self.state.buses[675] = BusData(id=675, name="675", vn_kv=4.16, type='pq', p_load_kw=843, q_load_kvar=462)
        self.state.buses[680] = BusData(id=680, name="680", vn_kv=4.16, type='pq', p_load_kw=0, q_load_kvar=0)

        # Connect the buses
        # (id, from, to, length, r, x)
        self.state.lines[1] = LineData(1, 650, 632, 0.1, 0.3, 0.8, is_transformer=False)
        self.state.lines[2] = LineData(2, 632, 645, 0.15, 0.3, 0.8)
        self.state.lines[3] = LineData(3, 645, 646, 0.09, 0.3, 0.8)
        self.state.lines[4] = LineData(4, 632, 633, 0.15, 0.3, 0.8)
        self.state.lines[5] = LineData(5, 633, 634, 0.0, 0.0, 0.0, is_transformer=True)
        self.state.lines[6] = LineData(6, 632, 671, 0.60, 0.3, 0.8)
        self.state.lines[7] = LineData(7, 671, 684, 0.09, 0.3, 0.8)
        self.state.lines[8] = LineData(8, 684, 611, 0.09, 0.3, 0.8)
        self.state.lines[9] = LineData(9, 684, 652, 0.24, 0.3, 0.8)
        self.state.lines[10] = LineData(10, 671, 692, 0.01, 0.01, 0.01) # switch (avoid divide by zero)
        self.state.lines[11] = LineData(11, 692, 675, 0.15, 0.3, 0.8)
        self.state.lines[12] = LineData(12, 671, 680, 0.30, 0.3, 0.8)

        self.populate_params_tables()

    def setup_connections(self):
        self.ui.btn_simulate.clicked.connect(self.run_simulation)
        self.ui.diagram_view.data_updated.connect(self.on_diagram_data_updated)
        self.ui.btn_save_params.clicked.connect(self.save_params)
        self.ui.btn_export_params.clicked.connect(self.export_params)
        self.ui.btn_import_params.clicked.connect(self.import_params)

    def on_diagram_data_updated(self):
        self.update_diagram()
        self.populate_params_tables()

    def populate_params_tables(self):
        # Populate Buses
        self.ui.table_params_buses.setRowCount(len(self.state.buses))
        self.ui.table_params_buses.setColumnCount(4)
        self.ui.table_params_buses.setHorizontalHeaderLabels(["ID", "P Load (kW)", "Q Load (kVAr)", "Geração (kW)"])
        for i, (bus_id, bus) in enumerate(self.state.buses.items()):
            self.ui.table_params_buses.setItem(i, 0, QTableWidgetItem(str(bus.id)))
            self.ui.table_params_buses.setItem(i, 1, QTableWidgetItem(str(bus.p_load_kw)))
            self.ui.table_params_buses.setItem(i, 2, QTableWidgetItem(str(bus.q_load_kvar)))
            self.ui.table_params_buses.setItem(i, 3, QTableWidgetItem(str(bus.p_gen_kw)))

        # Populate Lines
        self.ui.table_params_lines.setRowCount(len(self.state.lines))
        self.ui.table_params_lines.setColumnCount(4)
        self.ui.table_params_lines.setHorizontalHeaderLabels(["ID", "R (ohm/km)", "X (ohm/km)", "Length (km)"])
        for i, (line_id, line) in enumerate(self.state.lines.items()):
            item = QTableWidgetItem(f"{line.from_bus} - {line.to_bus}")
            item.setData(Qt.ItemDataRole.UserRole, line.id)
            self.ui.table_params_lines.setItem(i, 0, item)
            self.ui.table_params_lines.setItem(i, 1, QTableWidgetItem(str(line.r_ohm_per_km)))
            self.ui.table_params_lines.setItem(i, 2, QTableWidgetItem(str(line.x_ohm_per_km)))
            self.ui.table_params_lines.setItem(i, 3, QTableWidgetItem(str(line.length_km)))

    def save_params(self):
        try:
            for i in range(self.ui.table_params_buses.rowCount()):
                bus_id = int(self.ui.table_params_buses.item(i, 0).text())
                if bus_id in self.state.buses:
                    self.state.buses[bus_id].p_load_kw = safe_float(self.ui.table_params_buses.item(i, 1).text())
                    self.state.buses[bus_id].q_load_kvar = safe_float(self.ui.table_params_buses.item(i, 2).text())
                    self.state.buses[bus_id].p_gen_kw = safe_float(self.ui.table_params_buses.item(i, 3).text())

            for i in range(self.ui.table_params_lines.rowCount()):
                line_id = self.ui.table_params_lines.item(i, 0).data(Qt.ItemDataRole.UserRole)
                if line_id in self.state.lines:
                    self.state.lines[line_id].r_ohm_per_km = safe_float(self.ui.table_params_lines.item(i, 1).text())
                    self.state.lines[line_id].x_ohm_per_km = safe_float(self.ui.table_params_lines.item(i, 2).text())
                    self.state.lines[line_id].length_km = safe_float(self.ui.table_params_lines.item(i, 3).text())

            self.update_diagram()
            QMessageBox.information(self.ui, "Sucesso", "Parâmetros salvos com sucesso!")
        except ValueError:
            QMessageBox.warning(self.ui, "Erro", "Valores inválidos inseridos. Use apenas números.")

    def export_params(self):
        filename, _ = QFileDialog.getSaveFileName(self.ui, "Exportar Parâmetros", "", "CSV Files (*.csv)")
        if not filename:
            return

        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                writer.writerow(["[Buses]"])
                writer.writerow(["ID", "P Load (kW)", "Q Load (kVAr)", "Geração (kW)"])
                for bus_id, bus in self.state.buses.items():
                    writer.writerow([bus_id, bus.p_load_kw, bus.q_load_kvar, bus.p_gen_kw])

                writer.writerow([])
                writer.writerow(["[Lines]"])
                writer.writerow(["ID", "R (ohm/km)", "X (ohm/km)", "Length (km)"])
                for line_id, line in self.state.lines.items():
                    writer.writerow([line.id, line.r_ohm_per_km, line.x_ohm_per_km, line.length_km])

            QMessageBox.information(self.ui, "Sucesso", "Parâmetros exportados com sucesso!")
        except Exception as e:
            QMessageBox.critical(self.ui, "Erro", f"Erro ao exportar: {str(e)}")

    def import_params(self):
        filename, _ = QFileDialog.getOpenFileName(self.ui, "Importar Parâmetros", "", "CSV Files (*.csv)")
        if not filename:
            return

        try:
            with open(filename, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                mode = None

                for row in reader:
                    if not row:
                        continue
                    if row[0] == "[Buses]":
                        mode = "buses"
                        continue
                    elif row[0] == "[Lines]":
                        mode = "lines"
                        continue

                    if row[0] == "ID":
                        continue

                    if mode == "buses":
                        bus_id = int(row[0])
                        if bus_id in self.state.buses:
                            self.state.buses[bus_id].p_load_kw = safe_float(row[1])
                            self.state.buses[bus_id].q_load_kvar = safe_float(row[2])
                            self.state.buses[bus_id].p_gen_kw = safe_float(row[3])
                    elif mode == "lines":
                        line_id = int(row[0])
                        if line_id in self.state.lines:
                            self.state.lines[line_id].r_ohm_per_km = safe_float(row[1])
                            self.state.lines[line_id].x_ohm_per_km = safe_float(row[2])
                            self.state.lines[line_id].length_km = safe_float(row[3])

            self.populate_params_tables()
            self.update_diagram()
            QMessageBox.information(self.ui, "Sucesso", "Parâmetros importados com sucesso!")
        except Exception as e:
            QMessageBox.critical(self.ui, "Erro", f"Erro ao importar: {str(e)}")

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
            self.ui.toast.show_toast("Erro: A simulação falhou.", False, self.ui)
            return

        self.ui.toast.show_toast("Simulação concluída com sucesso!", True, self.ui)

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

    def run(self):
        self.ui.show()
        sys.exit(self.app.exec())

if __name__ == '__main__':
    controller = MainController()
    controller.run()
