from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QPushButton, QComboBox, QLabel,
                             QTableWidget, QSplitter)
from PyQt6.QtCore import Qt
from diagram_view import NetworkDiagram
from plot_utils import PVPlotWidget

DARK_STYLE = """
QMainWindow {
    background-color: #1e1e1e;
    color: white;
}
QTabWidget::pane {
    border: 1px solid #3a3a3a;
    background: #1e1e1e;
}
QTabBar::tab {
    background: #2d2d2d;
    color: white;
    padding: 10px 20px;
    border: 1px solid #3a3a3a;
}
QTabBar::tab:selected {
    background: #007acc;
}
QPushButton {
    background-color: #007acc;
    color: white;
    border: none;
    padding: 10px;
    font-weight: bold;
    border-radius: 5px;
}
QPushButton:hover {
    background-color: #005999;
}
QLabel {
    color: white;
    font-size: 14px;
}
QComboBox {
    background-color: #2d2d2d;
    color: white;
    border: 1px solid #3a3a3a;
    padding: 5px;
}
QTableWidget {
    background-color: #2d2d2d;
    color: white;
    gridline-color: #3a3a3a;
    border: none;
}
QHeaderView::section {
    background-color: #3a3a3a;
    color: white;
    padding: 4px;
    border: 1px solid #2d2d2d;
}
"""

class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador SEP - 13 Barras")
        self.resize(1000, 700)
        self.setStyleSheet(DARK_STYLE)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.setup_tab1()
        self.setup_tab_params()
        self.setup_tab2()
        self.setup_tab3()

    def setup_tab1(self):
        self.tab1 = QWidget()
        layout = QVBoxLayout(self.tab1)

        # Diagram
        self.diagram_view = NetworkDiagram()
        layout.addWidget(self.diagram_view, stretch=1)

        # Control Panel
        control_panel = QHBoxLayout()
        self.lbl_target = QLabel("Barra Alvo (Curva PV):")
        self.combo_target_bus = QComboBox()
        self.btn_simulate = QPushButton("Iniciar Simulação")

        control_panel.addWidget(self.lbl_target)
        control_panel.addWidget(self.combo_target_bus)
        control_panel.addStretch()
        control_panel.addWidget(self.btn_simulate)

        layout.addLayout(control_panel)
        self.tabs.addTab(self.tab1, "Principal (Diagrama)")

    def setup_tab_params(self):
        self.tab_params = QWidget()
        layout = QVBoxLayout(self.tab_params)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top half: Buses
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addWidget(QLabel("Parâmetros das Barras"))
        self.table_params_buses = QTableWidget()
        top_layout.addWidget(self.table_params_buses)

        # Bottom half: Lines
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.addWidget(QLabel("Parâmetros das Linhas"))
        self.table_params_lines = QTableWidget()
        bottom_layout.addWidget(self.table_params_lines)

        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        self.btn_export_params = QPushButton("Exportar Dados (CSV)")
        self.btn_import_params = QPushButton("Importar Dados (CSV)")
        btn_layout.addWidget(self.btn_export_params)
        btn_layout.addWidget(self.btn_import_params)

        self.btn_save_params = QPushButton("Salvar Alterações")
        btn_layout.addWidget(self.btn_save_params)
        layout.addLayout(btn_layout)

        self.tabs.addTab(self.tab_params, "Parâmetros")

    def setup_tab2(self):
        self.tab2 = QWidget()
        layout = QVBoxLayout(self.tab2)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top half: Power Flow Results
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addWidget(QLabel("Resultados: Fluxo de Potência (Tensões Nodais)"))
        self.table_bus_results = QTableWidget()
        top_layout.addWidget(self.table_bus_results)

        top_layout.addWidget(QLabel("Resultados: Fluxo nas Linhas"))
        self.table_line_results = QTableWidget()
        top_layout.addWidget(self.table_line_results)

        # Bottom half: Modal Analysis Results
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.addWidget(QLabel("Análise Modal (Menores Autovalores / Fatores de Participação)"))
        self.table_modal_results = QTableWidget()
        bottom_layout.addWidget(self.table_modal_results)

        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        layout.addWidget(splitter)

        self.tabs.addTab(self.tab2, "Resultados")

    def setup_tab3(self):
        self.tab3 = QWidget()
        layout = QVBoxLayout(self.tab3)
        self.pv_plot = PVPlotWidget()
        layout.addWidget(self.pv_plot)
        self.tabs.addTab(self.tab3, "Gráficos")
