from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PVPlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Configure dark style for plot
        self.figure.patch.set_facecolor('#1e1e1e')
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#2d2d2d')
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')

    def plot_curve(self, p_values, v_values, target_bus_name=""):
        self.ax.clear()

        self.ax.set_facecolor('#2d2d2d')
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')

        if not p_values or not v_values:
            self.canvas.draw()
            return

        self.ax.plot(p_values, v_values, color='#00aaff', linewidth=2, marker='o', markersize=4)

        # Highlight collapse point (Nose of the PV curve is the max power point)
        max_idx = p_values.index(max(p_values))
        collapse_p = p_values[max_idx]
        collapse_v = v_values[max_idx]
        self.ax.plot(collapse_p, collapse_v, color='red', marker='x', markersize=10, mew=2, label="Ponto de Colapso")

        title = f"Curva PV (Tensão x Potência) - Barra {target_bus_name}" if target_bus_name else "Curva PV (Tensão x Potência)"
        self.ax.set_title(title)
        self.ax.set_xlabel("Potência Ativa (MW)")
        self.ax.set_ylabel("Tensão (PU)")
        self.ax.grid(True, linestyle='--', alpha=0.5, color='gray')
        self.ax.legend(loc='upper right', facecolor='#1e1e1e', edgecolor='white', labelcolor='white')

        self.canvas.draw()


    def export_plot(self, filename):
        self.figure.savefig(filename, bbox_inches='tight')

def populate_table(table_widget: QTableWidget, data: list, headers: list):
    table_widget.clear()
    table_widget.setRowCount(len(data))
    table_widget.setColumnCount(len(headers))
    table_widget.setHorizontalHeaderLabels(headers)

    for row_idx, row_data in enumerate(data):
        for col_idx, item_data in enumerate(row_data):
            item = QTableWidgetItem(str(item_data))
            table_widget.setItem(row_idx, col_idx, item)

    table_widget.resizeColumnsToContents()
