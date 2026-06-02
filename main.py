import sys
import csv
import math
import json
from PyQt6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem, QFileDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSettings

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
        self.load_settings()
        self.setup_connections()

        # Initial draw
        self.update_diagram()
        self.populate_params_tables()
        self.populate_target_combo()


    def save_settings(self):
        settings = QSettings("SimuladorSEP", "Parametros")

        # Save buses
        buses_data = {}
        for bus_id, bus in self.state.buses.items():
            buses_data[bus_id] = {
                "p_load_kw": bus.p_load_kw,
                "q_load_kvar": bus.q_load_kvar,
                "p_gen_kw": bus.p_gen_kw
            }
        settings.setValue("buses", json.dumps(buses_data))

        # Save lines
        lines_data = {}
        for line_id, line in self.state.lines.items():
            lines_data[line_id] = {
                "r_ohm_per_km": line.r_ohm_per_km,
                "x_ohm_per_km": line.x_ohm_per_km,
                "length_km": line.length_km,
                "sn_mva": line.sn_mva,
                "vk_percent": line.vk_percent,
                "vkr_percent": line.vkr_percent,
                "pfe_kw": line.pfe_kw,
                "i0_percent": line.i0_percent
            }
        settings.setValue("lines", json.dumps(lines_data))

    def load_settings(self):
        settings = QSettings("SimuladorSEP", "Parametros")

        buses_str = settings.value("buses", "")
        if buses_str:
            try:
                buses_data = json.loads(buses_str)
                for bus_id_str, data in buses_data.items():
                    bus_id = int(bus_id_str)
                    if bus_id in self.state.buses:
                        self.state.buses[bus_id].p_load_kw = float(data.get("p_load_kw", self.state.buses[bus_id].p_load_kw))
                        self.state.buses[bus_id].q_load_kvar = float(data.get("q_load_kvar", self.state.buses[bus_id].q_load_kvar))
                        self.state.buses[bus_id].p_gen_kw = float(data.get("p_gen_kw", self.state.buses[bus_id].p_gen_kw))
            except Exception as e:
                print("Erro ao carregar parâmetros de barras:", e)

        lines_str = settings.value("lines", "")
        if lines_str:
            try:
                lines_data = json.loads(lines_str)
                for line_id_str, data in lines_data.items():
                    line_id = int(line_id_str)
                    if line_id in self.state.lines:
                        self.state.lines[line_id].r_ohm_per_km = float(data.get("r_ohm_per_km", self.state.lines[line_id].r_ohm_per_km))
                        self.state.lines[line_id].x_ohm_per_km = float(data.get("x_ohm_per_km", self.state.lines[line_id].x_ohm_per_km))
                        self.state.lines[line_id].length_km = float(data.get("length_km", self.state.lines[line_id].length_km))
                        self.state.lines[line_id].sn_mva = float(data.get("sn_mva", self.state.lines[line_id].sn_mva))
                        self.state.lines[line_id].vk_percent = float(data.get("vk_percent", self.state.lines[line_id].vk_percent))
                        self.state.lines[line_id].vkr_percent = float(data.get("vkr_percent", self.state.lines[line_id].vkr_percent))
                        self.state.lines[line_id].pfe_kw = float(data.get("pfe_kw", self.state.lines[line_id].pfe_kw))
                        self.state.lines[line_id].i0_percent = float(data.get("i0_percent", self.state.lines[line_id].i0_percent))
            except Exception as e:
                print("Erro ao carregar parâmetros de linhas:", e)

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
        self.state.lines[5] = LineData(5, 633, 634, 0.0, 0.0, 0.0, is_transformer=True, sn_mva=0.5, vk_percent=2.0, vkr_percent=0.5, pfe_kw=1.0, i0_percent=0.5)
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
        self.ui.btn_export_results.clicked.connect(self.export_results)
        self.ui.btn_export_plot.clicked.connect(self.export_plot)
        self.ui.app_closed.connect(self.save_settings)

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
        normal_lines = [l for l in self.state.lines.values() if not l.is_transformer]
        self.ui.table_params_lines.setRowCount(len(normal_lines))
        self.ui.table_params_lines.setColumnCount(4)
        self.ui.table_params_lines.setHorizontalHeaderLabels(["ID", "R (ohm/km)", "X (ohm/km)", "Length (km)"])
        for i, line in enumerate(normal_lines):
            item = QTableWidgetItem(f"{line.from_bus} - {line.to_bus}")
            item.setData(Qt.ItemDataRole.UserRole, line.id)
            self.ui.table_params_lines.setItem(i, 0, item)
            self.ui.table_params_lines.setItem(i, 1, QTableWidgetItem(str(line.r_ohm_per_km)))
            self.ui.table_params_lines.setItem(i, 2, QTableWidgetItem(str(line.x_ohm_per_km)))
            self.ui.table_params_lines.setItem(i, 3, QTableWidgetItem(str(line.length_km)))

        # Populate Transformers
        trafos = [l for l in self.state.lines.values() if l.is_transformer]
        self.ui.table_params_trafos.setRowCount(len(trafos))
        self.ui.table_params_trafos.setColumnCount(6)
        self.ui.table_params_trafos.setHorizontalHeaderLabels(["ID", "Sn (MVA)", "vk (%)", "vkr (%)", "pfe (kW)", "i0 (%)"])
        for i, trafo in enumerate(trafos):
            item = QTableWidgetItem(f"{trafo.from_bus} - {trafo.to_bus}")
            item.setData(Qt.ItemDataRole.UserRole, trafo.id)
            self.ui.table_params_trafos.setItem(i, 0, item)
            self.ui.table_params_trafos.setItem(i, 1, QTableWidgetItem(str(trafo.sn_mva)))
            self.ui.table_params_trafos.setItem(i, 2, QTableWidgetItem(str(trafo.vk_percent)))
            self.ui.table_params_trafos.setItem(i, 3, QTableWidgetItem(str(trafo.vkr_percent)))
            self.ui.table_params_trafos.setItem(i, 4, QTableWidgetItem(str(trafo.pfe_kw)))
            self.ui.table_params_trafos.setItem(i, 5, QTableWidgetItem(str(trafo.i0_percent)))

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

            for i in range(self.ui.table_params_trafos.rowCount()):
                trafo_id = self.ui.table_params_trafos.item(i, 0).data(Qt.ItemDataRole.UserRole)
                if trafo_id in self.state.lines:
                    self.state.lines[trafo_id].sn_mva = safe_float(self.ui.table_params_trafos.item(i, 1).text())
                    self.state.lines[trafo_id].vk_percent = safe_float(self.ui.table_params_trafos.item(i, 2).text())
                    self.state.lines[trafo_id].vkr_percent = safe_float(self.ui.table_params_trafos.item(i, 3).text())
                    self.state.lines[trafo_id].pfe_kw = safe_float(self.ui.table_params_trafos.item(i, 4).text())
                    self.state.lines[trafo_id].i0_percent = safe_float(self.ui.table_params_trafos.item(i, 5).text())

            self.update_diagram()
            self.save_settings()
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
                    if not line.is_transformer:
                        writer.writerow([line.id, line.r_ohm_per_km, line.x_ohm_per_km, line.length_km])

                writer.writerow([])
                writer.writerow(["[Transformers]"])
                writer.writerow(["ID", "Sn (MVA)", "vk (%)", "vkr (%)", "pfe (kW)", "i0 (%)"])
                for line_id, line in self.state.lines.items():
                    if line.is_transformer:
                        writer.writerow([line.id, line.sn_mva, line.vk_percent, line.vkr_percent, line.pfe_kw, line.i0_percent])

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
                    elif row[0] == "[Transformers]":
                        mode = "transformers"
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
                    elif mode == "transformers":
                        trafo_id = int(row[0])
                        if trafo_id in self.state.lines:
                            self.state.lines[trafo_id].sn_mva = safe_float(row[1])
                            self.state.lines[trafo_id].vk_percent = safe_float(row[2])
                            self.state.lines[trafo_id].vkr_percent = safe_float(row[3])
                            self.state.lines[trafo_id].pfe_kw = safe_float(row[4])
                            self.state.lines[trafo_id].i0_percent = safe_float(row[5])

            self.populate_params_tables()
            self.update_diagram()
            self.save_settings()
            QMessageBox.information(self.ui, "Sucesso", "Parâmetros importados com sucesso!")
        except Exception as e:
            QMessageBox.critical(self.ui, "Erro", f"Erro ao importar: {str(e)}")



    def export_plot(self):
        filename, _ = QFileDialog.getSaveFileName(self.ui, "Exportar Gráfico", "", "Images (*.png *.jpg *.jpeg)")
        if not filename:
            return

        try:
            self.ui.pv_plot.export_plot(filename)
            QMessageBox.information(self.ui, "Sucesso", "Gráfico exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self.ui, "Erro", f"Erro ao exportar: {str(e)}")

    def export_results(self):
        filename, _ = QFileDialog.getSaveFileName(self.ui, "Exportar Resultados", "", "CSV Files (*.csv)")
        if not filename:
            return

        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Export Bus Results
                writer.writerow(["[Fluxo de Potência (Tensões Nodais)]"])
                headers = []
                for j in range(self.ui.table_bus_results.columnCount()):
                    headers.append(self.ui.table_bus_results.horizontalHeaderItem(j).text())
                writer.writerow(headers)

                for i in range(self.ui.table_bus_results.rowCount()):
                    row_data = []
                    for j in range(self.ui.table_bus_results.columnCount()):
                        item = self.ui.table_bus_results.item(i, j)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                writer.writerow([])

                # Export Line Results
                writer.writerow(["[Fluxo nas Linhas]"])
                headers = []
                for j in range(self.ui.table_line_results.columnCount()):
                    headers.append(self.ui.table_line_results.horizontalHeaderItem(j).text())
                writer.writerow(headers)

                for i in range(self.ui.table_line_results.rowCount()):
                    row_data = []
                    for j in range(self.ui.table_line_results.columnCount()):
                        item = self.ui.table_line_results.item(i, j)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                writer.writerow([])

                # Export Modal Analysis Results
                writer.writerow(["[Análise Modal]"])
                headers = []
                for j in range(self.ui.table_modal_results.columnCount()):
                    headers.append(self.ui.table_modal_results.horizontalHeaderItem(j).text())
                writer.writerow(headers)

                for i in range(self.ui.table_modal_results.rowCount()):
                    row_data = []
                    for j in range(self.ui.table_modal_results.columnCount()):
                        item = self.ui.table_modal_results.item(i, j)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QMessageBox.information(self.ui, "Sucesso", "Resultados exportados com sucesso!")
        except Exception as e:
            QMessageBox.critical(self.ui, "Erro", f"Erro ao exportar: {str(e)}")

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
