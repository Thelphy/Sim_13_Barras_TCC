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
    padding: 15px 30px;
    border: 1px solid #3a3a3a;
    font-size: 16px;
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
    font-size: 18px;
}
QComboBox {
    background-color: #2d2d2d;
    color: white;
    border: 1px solid #3a3a3a;
    padding: 8px;
    font-size: 16px;
}
QTableWidget {
    background-color: #2d2d2d;
    color: white;
    gridline-color: #3a3a3a;
    border: none;
    font-size: 14px;
}
QHeaderView::section {
    background-color: #3a3a3a;
    color: white;
    padding: 8px;
    border: 1px solid #2d2d2d;
    font-size: 14px;
}
"""

# Classe que implementa uma notificação flutuante tipo 'Toast' na interface
class ToastNotification(QWidget):
    # Inicializa o componente de notificação Toast e seu layout
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
        self.label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        self.card_layout.addWidget(self.label)

        self.layout.addWidget(self.card)

        # Sombra
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 0)
        self.card.setGraphicsEffect(shadow)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide)

        self.hide()

    # Função para exibir a mensagem na tela com duração definida e cor correspondente (sucesso/erro)
    def show_toast(self, message, is_success, parent_widget, duration=3000):
        self.label.setText(message)
        if is_success:
            self.card.setStyleSheet("QWidget#card { background-color: #28a745; border-radius: 8px; padding: 15px; }")
        else:
            self.card.setStyleSheet("QWidget#card { background-color: #dc3545; border-radius: 8px; padding: 15px; }")

        self.adjustSize()

        if parent_widget:
            # Posicionar no canto superior direito do pai
            parent_geom = parent_widget.geometry()
            parent_pos = parent_widget.mapToGlobal(parent_widget.rect().topLeft())

            x = parent_pos.x() + parent_geom.width() - self.width() - 20
            y = parent_pos.y() + 20

            self.move(x, y)

        self.show()
        self.timer.start(duration)

# Classe principal que estrutura e define toda a interface gráfica de usuário (UI)
class MainWindowUI(QMainWindow):
    app_closed = pyqtSignal()

    # Construtor da interface principal, onde as abas e os layouts são instanciados
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TCC Lucass 13 Bus")
        self.resize(1200, 800)

        # Carregar geometria da janela
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


    # Evento capturado ao fechar a janela para salvar as configurações de geometria
    def closeEvent(self, event):
        settings = QSettings("SimuladorSEP", "App")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        self.app_closed.emit()
        super().closeEvent(event)

    # Configuração da Aba 1, que contém o diagrama da rede elétrica
    def setup_tab1(self):
        self.tab1 = QWidget()
        layout = QVBoxLayout(self.tab1)

        # Diagrama
        self.diagram_view = NetworkDiagram()
        layout.addWidget(self.diagram_view, stretch=1)

        # Janela flutuante para cenários
        self.scenario_panel = QWidget(self.diagram_view)
        self.scenario_panel.setStyleSheet("QWidget { background-color: rgba(30, 30, 30, 230); border-radius: 12px; border: 1px solid #555; } QLabel { background: transparent; border: none; font-size: 16px; } QComboBox { background: #2d2d2d; font-size: 16px; padding: 8px; }")
        sc_layout = QVBoxLayout(self.scenario_panel)
        lbl_sc = QLabel("Cenários")
        lbl_sc.setStyleSheet("font-weight: bold; font-size: 18px;")
        self.combo_scenarios = QComboBox()
        sc_layout.addWidget(lbl_sc)
        sc_layout.addWidget(self.combo_scenarios)
        self.scenario_panel.move(20, 20)
        self.scenario_panel.resize(280, 110)

        # Painel de Controle
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

    # Configuração da Aba de Parâmetros, que contém as tabelas de dados do sistema
    def setup_tab_params(self):
        self.tab_params = QWidget()
        layout = QVBoxLayout(self.tab_params)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Metade superior: Barras
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addWidget(QLabel("Parâmetros das Barras"))
        self.table_params_buses = QTableWidget()
        top_layout.addWidget(self.table_params_buses)

        # Terço médio: Linhas
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.addWidget(QLabel("Parâmetros das Linhas"))
        self.table_params_lines = QTableWidget()
        middle_layout.addWidget(self.table_params_lines)

        # Terço inferior: Transformadores
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.addWidget(QLabel("Parâmetros dos Transformadores"))
        self.table_params_trafos = QTableWidget()
        bottom_layout.addWidget(self.table_params_trafos)
        
        # Configuração de Cabos
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
        self.btn_rename_scenario = QPushButton("Renomear Cenário")
        self.btn_delete_scenario = QPushButton("Excluir Cenário")
        btn_layout.addWidget(self.btn_save_scenario)
        btn_layout.addWidget(self.btn_rename_scenario)
        btn_layout.addWidget(self.btn_delete_scenario)

        self.btn_save_params = QPushButton("Salvar Alterações")
        btn_layout.addWidget(self.btn_save_params)
        layout.addLayout(btn_layout)

        self.tabs.addTab(self.tab_params, "Parâmetros")

    # Configuração da Aba de Resultados, que exibe as tabelas de fluxo de potência
    def setup_tab2(self):
        self.tab2 = QWidget()
        layout = QVBoxLayout(self.tab2)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Tensões Nodais
        widget_bus = QWidget()
        layout_bus = QVBoxLayout(widget_bus)
        layout_bus.addWidget(QLabel("Resultados: Fluxo de Potência (Tensões Nodais)"))
        self.table_bus_results = QTableWidget()
        layout_bus.addWidget(self.table_bus_results)

        # Fluxos nas Linhas
        widget_line = QWidget()
        layout_line = QVBoxLayout(widget_line)
        layout_line.addWidget(QLabel("Resultados: Fluxo nas Linhas"))
        self.table_line_results = QTableWidget()
        layout_line.addWidget(self.table_line_results)

        splitter.addWidget(widget_bus)
        splitter.addWidget(widget_line)
        layout.addWidget(splitter)

        self.btn_export_results = QPushButton("Exportar Resultados")
        layout.addWidget(self.btn_export_results)

        self.tabs.addTab(self.tab2, "Resultados")

    # Configuração da Aba de Gráficos, focada na exibição das Curvas PV
    def setup_tab3(self):
        self.tab3 = QWidget()
        layout = QVBoxLayout(self.tab3)
        self.pv_plot = PVPlotWidget()
        layout.addWidget(self.pv_plot)

        # Painel de Controle da Curva PV
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
