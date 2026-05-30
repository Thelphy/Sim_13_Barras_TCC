from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
                             QGraphicsLineItem, QGraphicsTextItem, QDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
                             QGraphicsItemGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor
from data_models import BusData, LineData

from PyQt6.QtWidgets import QCheckBox

class BusCheckboxDialog(QDialog):
    def __init__(self, bus: BusData, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Controles: Barra {bus.name}")
        self.bus = bus
        self.layout = QVBoxLayout(self)

        self.chk_gen = QCheckBox("Geração (kW)")
        self.chk_gen.setChecked(bus.gen_enabled)
        self.chk_p_load = QCheckBox("P Load (kW)")
        self.chk_p_load.setChecked(bus.p_load_enabled)
        self.chk_q_load = QCheckBox("Q Load (VAr)")
        self.chk_q_load.setChecked(bus.q_load_enabled)

        self.layout.addWidget(self.chk_gen)
        self.layout.addWidget(self.chk_p_load)
        self.layout.addWidget(self.chk_q_load)

        save_btn = QPushButton("Aplicar")
        save_btn.clicked.connect(self.save_data)
        self.layout.addWidget(save_btn)

    def save_data(self):
        self.bus.gen_enabled = self.chk_gen.isChecked()
        self.bus.p_load_enabled = self.chk_p_load.isChecked()
        self.bus.q_load_enabled = self.chk_q_load.isChecked()
        self.accept()

class LineDialog(QDialog):
    def __init__(self, line: LineData, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Line: {line.id}")
        self.line = line
        self.layout = QVBoxLayout(self)

        self.r_edit = QLineEdit(str(line.r_ohm_per_km))
        self.x_edit = QLineEdit(str(line.x_ohm_per_km))
        self.length_edit = QLineEdit(str(line.length_km))

        self.layout.addWidget(self.chk_gen)
        self.layout.addWidget(self.chk_p_load)
        self.layout.addWidget(self.chk_q_load)

        save_btn = QPushButton("Aplicar")
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
        dialog = BusCheckboxDialog(self.bus, self.diagram_view)
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

class GraphTrafoItem(QGraphicsItemGroup):
    def __init__(self, x1, y1, x2, y2, line: LineData, diagram_view):
        super().__init__()
        self.line_data = line
        self.diagram_view = diagram_view
        self.setToolTip(f"Trafo {line.id}")

        # Draw a line from (x1,y1) to (x2,y2) but interrupted by two circles in the middle
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2

        # Draw two intersecting circles
        r = 10
        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(2)

        # Calculate angle of the line
        import math
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)

        if length == 0:
            return

        ux = dx / length
        uy = dy / length

        # Centers for the two circles
        cx1 = mx - ux * (r - 2)
        cy1 = my - uy * (r - 2)

        cx2 = mx + ux * (r - 2)
        cy2 = my + uy * (r - 2)

        c1 = QGraphicsEllipseItem(cx1 - r, cy1 - r, r * 2, r * 2)
        c2 = QGraphicsEllipseItem(cx2 - r, cy2 - r, r * 2, r * 2)

        c1.setPen(pen)
        c2.setPen(pen)
        c1.setBrush(QBrush(QColor(30, 30, 30))) # Match background
        c2.setBrush(QBrush(QColor(30, 30, 30)))

        # Lines from endpoints to the edge of the circles
        l1_end_x = cx1 - ux * r
        l1_end_y = cy1 - uy * r

        l2_start_x = cx2 + ux * r
        l2_start_y = cy2 + uy * r

        line1 = QGraphicsLineItem(x1, y1, l1_end_x, l1_end_y)
        line2 = QGraphicsLineItem(l2_start_x, l2_start_y, x2, y2)

        line1.setPen(pen)
        line2.setPen(pen)

        self.addToGroup(line1)
        self.addToGroup(line2)
        self.addToGroup(c1)
        self.addToGroup(c2)


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

        # Hardcoded layout based on the IEEE 13 bus system image
        # x, y coordinates
        coords = {
            650: (400, 100),
            632: (400, 200),
            645: (250, 200),
            646: (100, 200),
            633: (550, 200),
            634: (700, 200),
            671: (400, 400),
            684: (250, 400),
            611: (100, 400),
            652: (250, 550),
            692: (550, 400),
            675: (700, 400),
            680: (400, 550)
        }

        for bus_id, bus in system_state.buses.items():
            if bus_id in coords:
                self.bus_coords[bus_id] = coords[bus_id]
            else:
                self.bus_coords[bus_id] = (400, 300) # fallback

        # Draw lines
        for line_id, line in system_state.lines.items():
            if line.from_bus in self.bus_coords and line.to_bus in self.bus_coords:
                x1, y1 = self.bus_coords[line.from_bus]
                x2, y2 = self.bus_coords[line.to_bus]
                if line.is_transformer:
                    item = GraphTrafoItem(x1, y1, x2, y2, line, self)
                else:
                    item = GraphLineItem(x1, y1, x2, y2, line, self)
                self.scene.addItem(item)

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
