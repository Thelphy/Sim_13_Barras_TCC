from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
                             QGraphicsLineItem, QGraphicsTextItem, QDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor
from data_models import BusData, LineData

class BusDialog(QDialog):
    def __init__(self, bus: BusData, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Bus: {bus.name}")
        self.bus = bus
        self.layout = QVBoxLayout(self)

        self.p_load_edit = QLineEdit(str(bus.p_load_kw))
        self.q_load_edit = QLineEdit(str(bus.q_load_kvar))
        self.p_gen_edit = QLineEdit(str(bus.p_gen_kw))

        self.layout.addWidget(QLabel("Active Load (kW):"))
        self.layout.addWidget(self.p_load_edit)
        self.layout.addWidget(QLabel("Reactive Load (kVAr):"))
        self.layout.addWidget(self.q_load_edit)
        self.layout.addWidget(QLabel("Generation (kW):"))
        self.layout.addWidget(self.p_gen_edit)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_data)
        self.layout.addWidget(save_btn)

    def save_data(self):
        try:
            self.bus.p_load_kw = float(self.p_load_edit.text())
            self.bus.q_load_kvar = float(self.q_load_edit.text())
            self.bus.p_gen_kw = float(self.p_gen_edit.text())
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter numeric values.")

class LineDialog(QDialog):
    def __init__(self, line: LineData, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Line: {line.id}")
        self.line = line
        self.layout = QVBoxLayout(self)

        self.r_edit = QLineEdit(str(line.r_ohm_per_km))
        self.x_edit = QLineEdit(str(line.x_ohm_per_km))
        self.length_edit = QLineEdit(str(line.length_km))

        self.layout.addWidget(QLabel("Resistance (Ohm/km):"))
        self.layout.addWidget(self.r_edit)
        self.layout.addWidget(QLabel("Reactance (Ohm/km):"))
        self.layout.addWidget(self.x_edit)
        self.layout.addWidget(QLabel("Length (km):"))
        self.layout.addWidget(self.length_edit)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_data)
        self.layout.addWidget(save_btn)

    def save_data(self):
        try:
            r = float(self.r_edit.text())
            x = float(self.x_edit.text())
            length = float(self.length_edit.text())
            if r < 0 or x < 0 or length < 0:
                raise ValueError("Values must be non-negative.")
            self.line.r_ohm_per_km = r
            self.line.x_ohm_per_km = x
            self.line.length_km = length
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid, non-negative numeric values.")

class GraphBusItem(QGraphicsEllipseItem):
    def __init__(self, x, y, radius, bus: BusData, diagram_view):
        super().__init__(x - radius, y - radius, radius * 2, radius * 2)
        self.bus = bus
        self.diagram_view = diagram_view
        self.setBrush(QBrush(QColor(100, 150, 255)))
        self.setPen(QPen(Qt.GlobalColor.white))
        self.setToolTip(f"{bus.name}\nType: {bus.type}")

    def mouseDoubleClickEvent(self, event):
        dialog = BusDialog(self.bus, self.diagram_view)
        if dialog.exec():
            self.diagram_view.data_updated.emit()

class GraphLineItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, line: LineData, diagram_view):
        super().__init__(x1, y1, x2, y2)
        self.line_data = line
        self.diagram_view = diagram_view
        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(3)
        self.setPen(pen)
        self.setToolTip(f"Line {line.id}\nL: {line.length_km}km")

    def mouseDoubleClickEvent(self, event):
        dialog = LineDialog(self.line_data, self.diagram_view)
        if dialog.exec():
            self.diagram_view.data_updated.emit()

class NetworkDiagram(QGraphicsView):
    data_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        from PyQt6.QtGui import QPainter; self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        self.bus_coords = {}

    def draw_network(self, system_state):
        self.scene.clear()
        self.bus_coords.clear()

        # Simple layout generation for 13 buses
        import math
        center_x, center_y = 300, 300
        radius = 200
        n_buses = len(system_state.buses)

        for i, (bus_id, bus) in enumerate(system_state.buses.items()):
            angle = 2 * math.pi * i / n_buses if n_buses > 0 else 0
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            self.bus_coords[bus_id] = (x, y)

        # Draw lines
        for line_id, line in system_state.lines.items():
            if line.from_bus in self.bus_coords and line.to_bus in self.bus_coords:
                x1, y1 = self.bus_coords[line.from_bus]
                x2, y2 = self.bus_coords[line.to_bus]
                line_item = GraphLineItem(x1, y1, x2, y2, line, self)
                self.scene.addItem(line_item)

        # Draw buses (after lines so they appear on top)
        bus_radius = 15
        for bus_id, bus in system_state.buses.items():
            x, y = self.bus_coords[bus_id]
            bus_item = GraphBusItem(x, y, bus_radius, bus, self)
            self.scene.addItem(bus_item)

            text = QGraphicsTextItem(bus.name)
            text.setDefaultTextColor(Qt.GlobalColor.white)
            text.setPos(x - bus_radius, y + bus_radius)
            self.scene.addItem(text)
