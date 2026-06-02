from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
                             QGraphicsLineItem, QGraphicsTextItem, QDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
                             QGraphicsItemGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor
from data_models import BusData, LineData


class BusDialog(QDialog):
    def __init__(self, bus: BusData, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar Barra: {bus.name}")
        self.bus = bus
        self.layout = QVBoxLayout(self)

        self.p_load_edit = QLineEdit(str(bus.p_load_kw))
        self.q_load_edit = QLineEdit(str(bus.q_load_kvar))
        self.p_gen_edit = QLineEdit(str(bus.p_gen_kw))

        self.layout.addWidget(QLabel("P Load (kW):"))
        self.layout.addWidget(self.p_load_edit)
        self.layout.addWidget(QLabel("Q Load (kVAr):"))
        self.layout.addWidget(self.q_load_edit)
        self.layout.addWidget(QLabel("Geração (kW):"))
        self.layout.addWidget(self.p_gen_edit)

        save_btn = QPushButton("Aplicar")
        save_btn.clicked.connect(self.save_data)
        self.layout.addWidget(save_btn)

    def save_data(self):
        try:
            p_load = float(self.p_load_edit.text())
            q_load = float(self.q_load_edit.text())
            p_gen = float(self.p_gen_edit.text())

            self.bus.p_load_kw = p_load
            self.bus.q_load_kvar = q_load
            self.bus.p_gen_kw = p_gen

            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values.")

class LineDialog(QDialog):
    def __init__(self, line: LineData, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Line: {line.id}")
        self.line = line
        self.layout = QVBoxLayout(self)

        self.r_edit = QLineEdit(str(line.r_ohm_per_km))
        self.x_edit = QLineEdit(str(line.x_ohm_per_km))
        self.length_edit = QLineEdit(str(line.length_km))

        self.layout.addWidget(QLabel("R (ohm/km):"))
        self.layout.addWidget(self.r_edit)
        self.layout.addWidget(QLabel("X (ohm/km):"))
        self.layout.addWidget(self.x_edit)
        self.layout.addWidget(QLabel("Length (km):"))
        self.layout.addWidget(self.length_edit)

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

class TrafoDialog(QDialog):
    def __init__(self, line: LineData, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Transformer: {line.id}")
        self.line = line
        self.layout = QVBoxLayout(self)

        self.sn_edit = QLineEdit(str(line.sn_mva))
        self.vk_edit = QLineEdit(str(line.vk_percent))
        self.vkr_edit = QLineEdit(str(line.vkr_percent))
        self.pfe_edit = QLineEdit(str(line.pfe_kw))
        self.i0_edit = QLineEdit(str(line.i0_percent))

        self.layout.addWidget(QLabel("Sn (MVA):"))
        self.layout.addWidget(self.sn_edit)
        self.layout.addWidget(QLabel("vk (%):"))
        self.layout.addWidget(self.vk_edit)
        self.layout.addWidget(QLabel("vkr (%):"))
        self.layout.addWidget(self.vkr_edit)
        self.layout.addWidget(QLabel("pfe (kW):"))
        self.layout.addWidget(self.pfe_edit)
        self.layout.addWidget(QLabel("i0 (%):"))
        self.layout.addWidget(self.i0_edit)

        save_btn = QPushButton("Aplicar")
        save_btn.clicked.connect(self.save_data)
        self.layout.addWidget(save_btn)

    def save_data(self):
        try:
            sn = float(self.sn_edit.text())
            vk = float(self.vk_edit.text())
            vkr = float(self.vkr_edit.text())
            pfe = float(self.pfe_edit.text())
            i0 = float(self.i0_edit.text())
            if sn < 0 or vk < 0 or vkr < 0 or pfe < 0 or i0 < 0:
                raise ValueError("Values must be non-negative.")
            self.line.sn_mva = sn
            self.line.vk_percent = vk
            self.line.vkr_percent = vkr
            self.line.pfe_kw = pfe
            self.line.i0_percent = i0
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

    def mouseDoubleClickEvent(self, event):
        dialog = TrafoDialog(self.line_data, self.diagram_view)
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
