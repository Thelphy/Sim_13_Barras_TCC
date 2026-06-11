from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QPushButton, QComboBox, QLabel,
                             QTableWidget, QSplitter, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, QSettings, pyqtSignal
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

class ToastNotification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.card = QWidget()
        self.card.setObjectName("card")
        self.card_layout = QHBoxLayout(self.card)

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-weight: bold;")
        self.card_layout.addWidget(self.label)

        self.layout.addWidget(self.card)

        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 0)
        self.card.setGraphicsEffect(shadow)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide)

        self.hide()

    def show_toast(self, message, is_success, parent_widget, duration=3000):
        self.label.setText(message)
        if is_success:
            self.card.setStyleSheet("QWidget#card { background-color: #28a745; border-radius: 5px; padding: 10px; }")
        else:
            self.card.setStyleSheet("QWidget#card { background-color: #dc3545; border-radius: 5px; padding: 10px; }")

        self.adjustSize()

        if parent_widget:
            # Position at top right of parent
            parent_geom = parent_widget.geometry()
            parent_pos = parent_widget.mapToGlobal(parent_widget.rect().topLeft())

            x = parent_pos.x() + parent_geom.width() - self.width() - 20
            y = parent_pos.y() + 20

            self.move(x, y)

        self.show()
        self.timer.start(duration)

class MainWindowUI(QMainWindow):
    app_closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador SEP - 13 Barras")
        self.resize(1000, 700)

        # Load window geometry
        settings = QSettings("SimuladorSEP", "App")
        geom = settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

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

        self.toast = ToastNotification(self)


    def closeEvent(self, event):
        settings = QSettings("SimuladorSEP", "App")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        self.app_closed.emit()
        super().closeEvent(event)

    def setup_tab1(self):
        self.tab1 = QWidget()
        layout = QVBoxLayout(self.tab1)

        # Diagram
        self.diagram_view = NetworkDiagram()
        layout.addWidget(self.diagram_view, stretch=1)

        # Floating window for scenarios
        self.scenario_panel = QWidget(self.diagram_view)
        self.scenario_panel.setStyleSheet("QWidget { background-color: rgba(30, 30, 30, 230); border-radius: 8px; border: 1px solid #555; } QLabel { background: transparent; border: none; } QComboBox { background: #2d2d2d; }")
        sc_layout = QVBoxLayout(self.scenario_panel)
        lbl_sc = QLabel("Cenários")
        lbl_sc.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.combo_scenarios = QComboBox()
        sc_layout.addWidget(lbl_sc)
        sc_layout.addWidget(self.combo_scenarios)
        self.scenario_panel.move(15, 15)
        self.scenario_panel.resize(220, 80)

        # Control Panel
        from PyQt6.QtWidgets import QProgressBar
        control_panel = QHBoxLayout()
        
        lbl_authors = QLabel("Desenvolvido por Lucas Albuquerque e Lucas Kossar")
        lbl_authors.setStyleSheet("color: #aaaaaa; font-style: italic;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(150)
        self.btn_simulate = QPushButton("Iniciar Simulação")

        control_panel.addWidget(lbl_authors)
        control_panel.addStretch()
        control_panel.addWidget(self.progress_bar)
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

        # Middle third: Lines
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.addWidget(QLabel("Parâmetros das Linhas"))
        self.table_params_lines = QTableWidget()
        middle_layout.addWidget(self.table_params_lines)

        # Bottom third: Transformers
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.addWidget(QLabel("Parâmetros dos Transformadores"))
        self.table_params_trafos = QTableWidget()
        bottom_layout.addWidget(self.table_params_trafos)
        
        # Cables Configuration
        cables_widget = QWidget()
        cables_layout = QVBoxLayout(cables_widget)
        cables_layout.addWidget(QLabel("Padrões de Cabos"))
        self.table_cables = QTableWidget()
        cables_layout.addWidget(self.table_cables)
        
        cables_btn_layout = QHBoxLayout()
        self.btn_add_cable = QPushButton("Novo Cabo")
        self.btn_remove_cable = QPushButton("Remover Cabo")
        cables_btn_layout.addWidget(self.btn_add_cable)
        cables_btn_layout.addWidget(self.btn_remove_cable)
        cables_layout.addLayout(cables_btn_layout)

        horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        horizontal_splitter.addWidget(top_widget)
        horizontal_splitter.addWidget(middle_widget)
        
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        bottom_splitter.addWidget(bottom_widget)
        bottom_splitter.addWidget(cables_widget)

        splitter.addWidget(horizontal_splitter)
        splitter.addWidget(bottom_splitter)
        layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        self.btn_export_params = QPushButton("Exportar Dados")
        self.btn_import_params = QPushButton("Importar Dados")
        btn_layout.addWidget(self.btn_export_params)
        btn_layout.addWidget(self.btn_import_params)

        self.btn_save_scenario = QPushButton("Salvar Cenário")
        self.btn_delete_scenario = QPushButton("Excluir Cenário")
        btn_layout.addWidget(self.btn_save_scenario)
        btn_layout.addWidget(self.btn_delete_scenario)

        self.btn_save_params = QPushButton("Salvar Alterações")
        btn_layout.addWidget(self.btn_save_params)
        layout.addLayout(btn_layout)

        self.tabs.addTab(self.tab_params, "Parâmetros")

    def setup_tab2(self):
        self.tab2 = QWidget()
        layout = QVBoxLayout(self.tab2)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Nodal Voltages
        widget_bus = QWidget()
        layout_bus = QVBoxLayout(widget_bus)
        layout_bus.addWidget(QLabel("Resultados: Fluxo de Potência (Tensões Nodais)"))
        self.table_bus_results = QTableWidget()
        layout_bus.addWidget(self.table_bus_results)

        # Line Flows
        widget_line = QWidget()
        layout_line = QVBoxLayout(widget_line)
        layout_line.addWidget(QLabel("Resultados: Fluxo nas Linhas"))
        self.table_line_results = QTableWidget()
        layout_line.addWidget(self.table_line_results)

        # Modal Analysis Results
        widget_modal = QWidget()
        layout_modal = QVBoxLayout(widget_modal)
        layout_modal.addWidget(QLabel("Análise Modal (Autovalores Dominantes / Fatores de Participação)"))
        self.table_modal_results = QTableWidget()
        layout_modal.addWidget(self.table_modal_results)

        splitter.addWidget(widget_bus)
        splitter.addWidget(widget_line)
        splitter.addWidget(widget_modal)
        layout.addWidget(splitter)

        self.btn_export_results = QPushButton("Exportar Resultados")
        layout.addWidget(self.btn_export_results)

        self.tabs.addTab(self.tab2, "Resultados")

    def setup_tab3(self):
        self.tab3 = QWidget()
        layout = QVBoxLayout(self.tab3)
        self.pv_plot = PVPlotWidget()
        layout.addWidget(self.pv_plot)

        # PV Curve Control Panel
        from PyQt6.QtWidgets import QProgressBar
        control_panel = QHBoxLayout()
        self.lbl_target = QLabel("Barra Alvo (Curva PV):")
        self.combo_target_bus = QComboBox()
        self.progress_bar_pv = QProgressBar()
        self.progress_bar_pv.setRange(0, 0)
        self.progress_bar_pv.setTextVisible(False)
        self.progress_bar_pv.setVisible(False)
        self.progress_bar_pv.setFixedWidth(150)
        self.btn_simulate_pv = QPushButton("Gerar Curva PV")

        control_panel.addWidget(self.lbl_target)
        control_panel.addWidget(self.combo_target_bus)
        control_panel.addStretch()
        control_panel.addWidget(self.progress_bar_pv)
        control_panel.addWidget(self.btn_simulate_pv)

        layout.addLayout(control_panel)

        self.btn_export_plot = QPushButton("Exportar Gráfico")
        layout.addWidget(self.btn_export_plot)

        self.tabs.addTab(self.tab3, "Gráficos")
