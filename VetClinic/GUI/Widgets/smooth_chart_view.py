from PyQt5.QtChart import QChartView
from PyQt5.QtGui  import QPainter, QPainterPath, QBrush, QColor
from PyQt5.QtCore import Qt, QPointF

class SmoothChartView(QChartView):
    def __init__(self, chart, spline_series, y_min, parent=None):
        super().__init__(chart, parent)
        self.spline = spline_series
        self.y_min  = y_min
        self.setRenderHint(QPainter.Antialiasing)
        # Ukrywamy standardowe tło wykresu
        chart.setBackgroundVisible(False)
        self.setStyleSheet("border:none; background-color:transparent;")

    def drawBackground(self, painter: QPainter, rect):
        # 1) Najpierw pozwól Qt narysować tło i osie
        super().drawBackground(painter, rect)

        pts = list(self.spline.pointsVector()) if hasattr(self.spline, 'pointsVector') else list(self.spline.points())
        if not pts:
            return

        # 2) Budujemy path ze wszystkich punktów, mapując je do układu współrzędnych wykresu
        mapped0 = self.chart().mapToPosition(pts[0], self.spline)
        path = QPainterPath(mapped0)
        for pt in pts[1:]:
            p = self.chart().mapToPosition(pt, self.spline)
            path.lineTo(p)

        # 3) Dokładamy prostą linię do dolnej granicy plotArea i z powrotem do początku
        plot_area = self.chart().plotArea()
        bottom_y = plot_area.bottom()
        last_x  = path.currentPosition().x()
        first_x = mapped0.x()
        path.lineTo(last_x, bottom_y)
        path.lineTo(first_x, bottom_y)
        path.closeSubpath()

        # 4) Rysujemy fill **ZA** serią spline (bo jesteśmy w drawBackground)
        painter.save()
        painter.setBrush(QBrush(QColor(56,162,219,40)))   # półprzezroczysty niebieski
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        painter.restore()
