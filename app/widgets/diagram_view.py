from __future__ import annotations

import math
import uuid
from typing import Callable

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# Shape defaults are used for legacy data and programmatic creation. New shapes are
# created by click-dragging their desired bounds, so these values are only fallbacks.
SHAPE_SIZES: dict[str, tuple[float, float]] = {
    "square": (92.0, 92.0),
    "rect": (160.0, 82.0),
    "rounded": (160.0, 82.0),
    "ellipse": (150.0, 90.0),
    "diamond": (150.0, 100.0),
}

SHAPE_LABELS: dict[str, str] = {
    "square": "Square",
    "rect": "Rectangle",
    "rounded": "Rounded",
    "ellipse": "Ellipse",
    "diamond": "Diamond",
}

MIN_SHAPE_WIDTH = 36.0
MIN_SHAPE_HEIGHT = 28.0
HANDLE_SIZE = 10.0
MIN_CREATE_DRAG = 6.0


DEFAULT_DIAGRAM_PALETTE: dict[str, str] = {
    "background": "#f7f8fa",
    "grid_minor": "#edf0f3",
    "grid_major": "#dde1e6",
    "stroke": "#596273",
    "fill": "#ffffff",
    "text": "#202124",
    "connector": "#596273",
}


def _pen(color: str, width: float = 2.0) -> QPen:
    return QPen(QColor(color), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)


def _make_shape_path(shape_type: str, width: float, height: float) -> QPainterPath:
    rect = QRectF(0.0, 0.0, max(1.0, width), max(1.0, height))
    path = QPainterPath()
    if shape_type == "ellipse":
        path.addEllipse(rect)
    elif shape_type == "diamond":
        polygon = QPolygonF(
            [
                QPointF(width / 2.0, 0.0),
                QPointF(width, height / 2.0),
                QPointF(width / 2.0, height),
                QPointF(0.0, height / 2.0),
            ]
        )
        path.addPolygon(polygon)
        path.closeSubpath()
    elif shape_type == "rounded":
        radius = min(18.0, max(6.0, min(width, height) * 0.18))
        path.addRoundedRect(rect, radius, radius)
    else:
        path.addRect(rect)
    return path


def _path_points(path: QPainterPath) -> list[list[float]]:
    return [[path.elementAt(i).x, path.elementAt(i).y] for i in range(path.elementCount())]


def _translated_path(path: QPainterPath, offset: QPointF) -> QPainterPath:
    points = _path_points(path)
    if not points:
        return QPainterPath()
    translated = QPainterPath(QPointF(points[0][0] + offset.x(), points[0][1] + offset.y()))
    for x, y in points[1:]:
        translated.lineTo(x + offset.x(), y + offset.y())
    return translated


def _path_from_points(points: object) -> QPainterPath | None:
    if not isinstance(points, list) or not points:
        return None
    first = points[0]
    if not isinstance(first, list) or len(first) < 2:
        return None
    try:
        path = QPainterPath(QPointF(float(first[0]), float(first[1])))
        for point in points[1:]:
            if isinstance(point, list) and len(point) >= 2:
                path.lineTo(float(point[0]), float(point[1]))
        return path
    except (TypeError, ValueError):
        return None


class DiagramResizeHandle(QGraphicsRectItem):
    """Small drag handle used to resize a DiagramShape after creation."""

    _CURSORS = {
        "nw": Qt.CursorShape.SizeFDiagCursor,
        "se": Qt.CursorShape.SizeFDiagCursor,
        "ne": Qt.CursorShape.SizeBDiagCursor,
        "sw": Qt.CursorShape.SizeBDiagCursor,
        "n": Qt.CursorShape.SizeVerCursor,
        "s": Qt.CursorShape.SizeVerCursor,
        "e": Qt.CursorShape.SizeHorCursor,
        "w": Qt.CursorShape.SizeHorCursor,
    }

    def __init__(self, owner: "DiagramShape", role: str) -> None:
        half = HANDLE_SIZE / 2.0
        super().__init__(-half, -half, HANDLE_SIZE, HANDLE_SIZE, owner)
        self.owner = owner
        self.role = role
        self.setZValue(30.0)
        self.setCursor(self._CURSORS[role])
        self.setBrush(QBrush(QColor("#ffffff")))
        self.setPen(_pen("#4f8cff", 1.4))
        self.setVisible(False)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setBrush(QBrush(QColor(palette["fill"])))
        self.setPen(_pen(palette["connector"], 1.4))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.owner.resize_from_handle(self.role, event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.owner.finish_resize()
        event.accept()


class DiagramShape(QGraphicsPathItem):
    def __init__(
        self,
        item_id: str,
        shape_type: str,
        text: str,
        on_changed: Callable[[], None],
        width: float | None = None,
        height: float | None = None,
    ) -> None:
        super().__init__()
        self.item_id = item_id
        self.shape_type = shape_type if shape_type in SHAPE_SIZES else "rect"
        self._on_changed = on_changed
        default_width, default_height = SHAPE_SIZES[self.shape_type]
        self._width = max(MIN_SHAPE_WIDTH, float(width if width is not None else default_width))
        self._height = max(MIN_SHAPE_HEIGHT, float(height if height is not None else default_height))
        self.setPath(_make_shape_path(self.shape_type, self._width, self._height))
        self.label = QGraphicsTextItem(text, self)
        self.label.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.label.setTextWidth(max(28.0, self._width - 20.0))
        self.review_badge = QGraphicsTextItem("", self)
        self.review_badge.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.review_badge.setScale(0.72)
        self._review_status: str | None = None
        self._position_label()
        self._position_review_badge()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPen(_pen("#747b88", 1.6))
        self.setBrush(QBrush(QColor("#ffffff")))
        self._handles = {role: DiagramResizeHandle(self, role) for role in ("nw", "n", "ne", "e", "se", "s", "sw", "w")}
        self._position_handles()

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    def _position_label(self) -> None:
        self.label.setTextWidth(max(28.0, self._width - 20.0))
        label_height = self.label.boundingRect().height()
        self.label.setPos(10.0, max(4.0, (self._height - label_height) / 2.0))

    def _position_review_badge(self) -> None:
        self.review_badge.setPos(6.0, self._height + 2.0)

    def set_review_status(self, status: str | None) -> None:
        self._review_status = status
        labels = {
            "current": "✓ Current",
            "needs_review": "⚠ Needs Review",
            "not_reviewed": "○ Not Reviewed",
            "cannot_compare": "! Cannot Compare",
        }
        colors = {
            "current": "#2f855a",
            "needs_review": "#b7791f",
            "not_reviewed": "#718096",
            "cannot_compare": "#c53030",
        }
        self.review_badge.setPlainText(labels.get(status or "", ""))
        if status in colors:
            self.review_badge.setDefaultTextColor(QColor(colors[status]))
        self.review_badge.setVisible(bool(status))
        self._position_review_badge()

    def _position_handles(self) -> None:
        x_mid = self._width / 2.0
        y_mid = self._height / 2.0
        positions = {
            "nw": QPointF(0.0, 0.0),
            "n": QPointF(x_mid, 0.0),
            "ne": QPointF(self._width, 0.0),
            "e": QPointF(self._width, y_mid),
            "se": QPointF(self._width, self._height),
            "s": QPointF(x_mid, self._height),
            "sw": QPointF(0.0, self._height),
            "w": QPointF(0.0, y_mid),
        }
        for role, handle in self._handles.items():
            handle.setPos(positions[role])

    def set_size(self, width: float, height: float, *, notify: bool = True) -> None:
        self._width = max(MIN_SHAPE_WIDTH, float(width))
        self._height = max(MIN_SHAPE_HEIGHT, float(height))
        self.setPath(_make_shape_path(self.shape_type, self._width, self._height))
        self._position_label()
        self._position_review_badge()
        self._position_handles()
        if notify:
            self._on_changed()

    def resize_from_handle(self, role: str, scene_pos: QPointF) -> None:
        left = self.x()
        top = self.y()
        right = left + self._width
        bottom = top + self._height

        if "w" in role:
            left = min(scene_pos.x(), right - MIN_SHAPE_WIDTH)
        if "e" in role:
            right = max(scene_pos.x(), left + MIN_SHAPE_WIDTH)
        if "n" in role:
            top = min(scene_pos.y(), bottom - MIN_SHAPE_HEIGHT)
        if "s" in role:
            bottom = max(scene_pos.y(), top + MIN_SHAPE_HEIGHT)

        self.setPos(left, top)
        self.set_size(right - left, bottom - top, notify=False)
        self._on_changed()

    def finish_resize(self) -> None:
        self._on_changed()

    @property
    def text(self) -> str:
        return self.label.toPlainText()

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setBrush(QBrush(QColor(palette["fill"])))
        self.setPen(_pen(palette["stroke"], 1.6))
        self.label.setDefaultTextColor(QColor(palette["text"]))
        for handle in self._handles.values():
            handle.set_theme(palette)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            selected = bool(value)
            for handle in self._handles.values():
                handle.setVisible(selected)
        return result

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        app = QApplication.instance()
        tr = bool(app is not None and app.property("devnestLanguage") == "tr")
        text, ok = QInputDialog.getText(None, "Şekil Yazısını Düzenle" if tr else "Edit Shape", "Yazı:" if tr else "Text:", text=self.text)
        if ok:
            self.label.setPlainText(text or SHAPE_LABELS.get(self.shape_type, "Shape"))
            self._position_label()
            self._on_changed()
        event.accept()


class DiagramText(QGraphicsTextItem):
    def __init__(self, item_id: str, text: str, on_changed: Callable[[], None]) -> None:
        super().__init__(text)
        self.item_id = item_id
        self._on_changed = on_changed
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setDefaultTextColor(QColor(palette["text"]))

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        return result

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        app = QApplication.instance()
        tr = bool(app is not None and app.property("devnestLanguage") == "tr")
        text, ok = QInputDialog.getMultiLineText(None, "Yazıyı Düzenle" if tr else "Edit Text", "Yazı:" if tr else "Text:", self.toPlainText())
        if ok:
            self.setPlainText(text)
            self._on_changed()
        event.accept()


class DiagramEdge(QGraphicsPathItem):
    """Legacy node-to-node edge kept for old DevNest diagrams."""

    def __init__(self, source_id: str, target_id: str) -> None:
        super().__init__()
        self.source_id = source_id
        self.target_id = target_id
        self._start = QPointF()
        self._end = QPointF()
        self.setZValue(-10)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(_pen("#596273", 2.6))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"], 2.6))

    def set_endpoints(self, start: QPointF, end: QPointF) -> None:
        self._start = start
        self._end = end
        path = QPainterPath(start)
        path.lineTo(end)
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        _paint_arrow_head(painter, self.path(), self.pen())


class DiagramFreehand(QGraphicsPathItem):
    """A freehand drawing that can also act as a connection endpoint."""

    def __init__(
        self,
        item_id: str,
        path: QPainterPath | None,
        on_changed: Callable[[], None],
    ) -> None:
        super().__init__(path or QPainterPath())
        self.item_id = item_id
        self._on_changed = on_changed
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["stroke"], 2.2))

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        return result


DiagramEndpoint = DiagramShape | DiagramText | DiagramFreehand


class DiagramConnector(QGraphicsPathItem):
    """A hand-drawn arrow whose route can optionally stay attached to shapes."""

    def __init__(
        self,
        path: QPainterPath | None = None,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> None:
        super().__init__(path or QPainterPath())
        self.source_id = source_id
        self.target_id = target_id
        self.setZValue(-6)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(_pen("#596273", 2.6))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"], 2.6))

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        _paint_arrow_head(painter, self.path(), self.pen())


def _paint_arrow_head(painter: QPainter, path: QPainterPath, pen: QPen) -> None:
    count = path.elementCount()
    if count < 2:
        return
    end_element = path.elementAt(count - 1)
    end = QPointF(end_element.x, end_element.y)
    previous: QPointF | None = None
    for index in range(count - 2, -1, -1):
        element = path.elementAt(index)
        candidate = QPointF(element.x, element.y)
        if QLineF(candidate, end).length() >= 2.0:
            previous = candidate
            break
    if previous is None:
        return
    line = QLineF(previous, end)
    angle = math.atan2(-line.dy(), line.dx())
    arrow_size = 16.0
    left = end - QPointF(
        math.sin(angle + math.pi / 3.0) * arrow_size,
        math.cos(angle + math.pi / 3.0) * arrow_size,
    )
    right = end - QPointF(
        math.sin(angle + math.pi - math.pi / 3.0) * arrow_size,
        math.cos(angle + math.pi - math.pi / 3.0) * arrow_size,
    )
    painter.setBrush(pen.color())
    painter.setPen(pen)
    painter.drawPolygon(QPolygonF([end, left, right]))


class DiagramScene(QGraphicsScene):
    diagramChanged = Signal()
    itemsDeleted = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.mode = "select"
        self.current_path: DiagramFreehand | None = None  # legacy only
        self.current_connector: DiagramConnector | None = None
        self._last_draw_point: QPointF | None = None
        self._shape_preview: QGraphicsPathItem | None = None
        self._shape_start: QPointF | None = None
        self._shape_type: str | None = None
        self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
        self.path_pen = _pen(self.palette["stroke"])
        self.loading = False
        self.setSceneRect(-2500, -2500, 5000, 5000)

    def set_mode(self, mode: str) -> None:
        self._cancel_shape_preview()
        if self.current_connector is not None and self.current_connector.scene() is self:
            self.removeItem(self.current_connector)
        self.mode = mode
        self.current_path = None
        self.current_connector = None
        self._last_draw_point = None

    def _notify_changed(self) -> None:
        self.update_connections()
        if not self.loading:
            self.diagramChanged.emit()

    @staticmethod
    def _new_id() -> str:
        return uuid.uuid4().hex

    def add_shape(
        self,
        shape_type: str,
        pos: QPointF,
        text: str | None = None,
        item_id: str | None = None,
        width: float | None = None,
        height: float | None = None,
        notify: bool = True,
    ) -> DiagramShape:
        label = text if text is not None else SHAPE_LABELS.get(shape_type, "Shape")
        shape = DiagramShape(
            item_id or self._new_id(),
            shape_type,
            label,
            self._notify_changed,
            width=width,
            height=height,
        )
        shape.set_theme(self.palette)
        self.addItem(shape)
        shape.setPos(pos)
        if notify:
            self._notify_changed()
        return shape

    @staticmethod
    def _drag_rect(start: QPointF, end: QPointF) -> QRectF:
        return QRectF(start, end).normalized()

    def _begin_shape_preview(self, shape_type: str, pos: QPointF) -> None:
        self._cancel_shape_preview()
        self._shape_start = pos
        self._shape_type = shape_type if shape_type in SHAPE_SIZES else "square"
        preview = QGraphicsPathItem()
        preview.setZValue(50.0)
        pen = _pen(self.palette["connector"], 1.6)
        pen.setStyle(Qt.PenStyle.DashLine)
        preview.setPen(pen)
        fill = QColor(self.palette["fill"])
        fill.setAlpha(72)
        preview.setBrush(QBrush(fill))
        preview.setPath(_make_shape_path(self._shape_type, 1.0, 1.0))
        preview.setPos(pos)
        self.addItem(preview)
        self._shape_preview = preview

    def _update_shape_preview(self, pos: QPointF) -> None:
        if self._shape_preview is None or self._shape_start is None or self._shape_type is None:
            return
        rect = self._drag_rect(self._shape_start, pos)
        self._shape_preview.setPos(rect.topLeft())
        self._shape_preview.setPath(
            _make_shape_path(self._shape_type, max(1.0, rect.width()), max(1.0, rect.height()))
        )

    def _finish_shape_preview(self, pos: QPointF) -> DiagramShape | None:
        if self._shape_preview is None or self._shape_start is None or self._shape_type is None:
            self._cancel_shape_preview()
            return None
        rect = self._drag_rect(self._shape_start, pos)
        shape_type = self._shape_type
        self._cancel_shape_preview()
        if rect.width() < MIN_CREATE_DRAG or rect.height() < MIN_CREATE_DRAG:
            return None
        width = max(MIN_SHAPE_WIDTH, rect.width())
        height = max(MIN_SHAPE_HEIGHT, rect.height())
        shape = self.add_shape(
            shape_type,
            rect.topLeft(),
            width=width,
            height=height,
            notify=False,
        )
        self.clearSelection()
        shape.setSelected(True)
        self._notify_changed()
        return shape

    def _cancel_shape_preview(self) -> None:
        if self._shape_preview is not None and self._shape_preview.scene() is self:
            self.removeItem(self._shape_preview)
        self._shape_preview = None
        self._shape_start = None
        self._shape_type = None

    def add_text(self, pos: QPointF, text: str = "Text", item_id: str | None = None) -> DiagramText:
        item = DiagramText(item_id or self._new_id(), text, self._notify_changed)
        item.set_theme(self.palette)
        self.addItem(item)
        item.setPos(pos)
        self._notify_changed()
        return item

    def add_edge(self, source: DiagramEndpoint, target: DiagramEndpoint) -> DiagramEdge:
        if source.item_id == target.item_id:
            raise ValueError("A diagram item cannot connect to itself")
        edge = DiagramEdge(source.item_id, target.item_id)
        edge.set_theme(self.palette)
        self.addItem(edge)
        self.update_edges()
        self._notify_changed()
        return edge

    def add_freehand_path(
        self,
        path: QPainterPath,
        item_id: str | None = None,
        notify: bool = True,
    ) -> DiagramFreehand:
        item = DiagramFreehand(item_id or self._new_id(), path, self._notify_changed)
        item.set_theme(self.palette)
        self.addItem(item)
        if notify:
            self._notify_changed()
        return item

    def add_connector_path(
        self,
        path: QPainterPath,
        notify: bool = True,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> DiagramConnector:
        if not source_id or not target_id or source_id == target_id:
            raise ValueError("A connector must link two different diagram items")
        nodes = self._nodes_by_id()
        if source_id not in nodes or target_id not in nodes:
            raise ValueError("Connector endpoints must exist in the scene")
        connector = DiagramConnector(path, source_id=source_id, target_id=target_id)
        connector.set_theme(self.palette)
        self.addItem(connector)
        if notify:
            self._notify_changed()
        return connector

    def update_connections(self) -> None:
        self.update_edges()
        self.update_drawn_connectors()

    def update_edges(self) -> None:
        nodes = self._nodes_by_id()
        for item in self.items():
            if not isinstance(item, DiagramEdge):
                continue
            source = nodes.get(item.source_id)
            target = nodes.get(item.target_id)
            if source is None or target is None:
                continue
            source_center = source.sceneBoundingRect().center()
            target_center = target.sceneBoundingRect().center()
            start = self._connection_point(source, target_center)
            end = self._connection_point(target, source_center)
            item.set_endpoints(start, end)

    def update_drawn_connectors(self) -> None:
        nodes = self._nodes_by_id()
        for item in self.items():
            if not isinstance(item, DiagramConnector):
                continue
            points = _path_points(item.path())
            if len(points) < 2:
                continue
            if item.source_id and item.source_id in nodes:
                toward = QPointF(points[1][0], points[1][1])
                start = self._connection_point(nodes[item.source_id], toward)
                points[0] = [start.x(), start.y()]
            if item.target_id and item.target_id in nodes:
                toward = QPointF(points[-2][0], points[-2][1])
                end = self._connection_point(nodes[item.target_id], toward)
                points[-1] = [end.x(), end.y()]
            rebuilt = _path_from_points(points)
            if rebuilt is not None:
                item.setPath(rebuilt)

    @staticmethod
    def _scene_path(item: DiagramFreehand) -> QPainterPath:
        points = _path_points(item.path())
        if not points:
            return QPainterPath()
        first = item.mapToScene(QPointF(points[0][0], points[0][1]))
        scene_path = QPainterPath(first)
        for x, y in points[1:]:
            scene_point = item.mapToScene(QPointF(x, y))
            scene_path.lineTo(scene_point)
        return scene_path

    def _connection_point(self, item: DiagramEndpoint, toward: QPointF) -> QPointF:
        if isinstance(item, DiagramFreehand):
            # Freehand objects have no artificial center anchor. Attach the
            # connector to the actual drawn contour point nearest to the drag.
            scene_path = self._scene_path(item)
            points = _path_points(scene_path)
            if not points:
                return item.sceneBoundingRect().center()
            best = min(
                (QPointF(x, y) for x, y in points),
                key=lambda point: QLineF(point, toward).length(),
            )
            return best
        return self._boundary_point(item, toward)

    def _boundary_point(self, item: DiagramEndpoint, toward: QPointF) -> QPointF:
        rect = item.sceneBoundingRect()
        center = rect.center()
        dx = toward.x() - center.x()
        dy = toward.y() - center.y()
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            return center
        half_w = max(1.0, rect.width() / 2.0)
        half_h = max(1.0, rect.height() / 2.0)
        shape_type = item.shape_type if isinstance(item, DiagramShape) else "rect"
        if shape_type == "ellipse":
            scale = 1.0 / math.sqrt((dx / half_w) ** 2 + (dy / half_h) ** 2)
        elif shape_type == "diamond":
            scale = 1.0 / (abs(dx) / half_w + abs(dy) / half_h)
        else:
            scale = min(half_w / max(abs(dx), 1e-6), half_h / max(abs(dy), 1e-6))
        return QPointF(center.x() + dx * scale, center.y() + dy * scale)

    def _nodes_by_id(self) -> dict[str, DiagramEndpoint]:
        result: dict[str, DiagramEndpoint] = {}
        for item in self.items():
            if isinstance(item, (DiagramShape, DiagramText, DiagramFreehand)):
                result[item.item_id] = item
        return result

    def _endpoint_at(self, pos: QPointF) -> DiagramEndpoint | None:
        # First prefer the exact Qt hit-test, including child text labels.
        for item in self.items(pos):
            current = item
            while current is not None:
                if isinstance(current, (DiagramShape, DiagramText, DiagramFreehand)):
                    return current
                current = current.parentItem()

        # A hand-drawn box/circle often has an empty interior. Treat the interior
        # of its bounding box as a practical hit area so connecting does not
        # require pixel-perfect clicking on the pen stroke. Smallest match wins.
        candidates: list[DiagramFreehand] = []
        for item in self.items():
            if isinstance(item, DiagramFreehand) and item.sceneBoundingRect().adjusted(-8, -8, 8, 8).contains(pos):
                candidates.append(item)
        if candidates:
            return min(candidates, key=lambda item: item.sceneBoundingRect().width() * item.sceneBoundingRect().height())
        return None

    @staticmethod
    def _append_sample(item: QGraphicsPathItem, pos: QPointF, previous: QPointF | None) -> QPointF:
        if previous is not None and QLineF(previous, pos).length() < 1.5:
            return previous
        path = item.path()
        path.lineTo(pos)
        item.setPath(path)
        return pos

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        pos = event.scenePos()
        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode.startswith("shape:"):
                self._begin_shape_preview(self.mode.split(":", 1)[1], pos)
                event.accept()
                return
            if self.mode == "text":
                app = QApplication.instance()
                tr = bool(app is not None and app.property("devnestLanguage") == "tr")
                text, ok = QInputDialog.getText(None, "Yazı Ekle" if tr else "Text", "Yazı:" if tr else "Text:")
                if ok:
                    self.add_text(pos, text or "Text")
                event.accept()
                return
            if self.mode == "connect":
                source = self._endpoint_at(pos)
                if source is None:
                    self.current_connector = None
                    self._last_draw_point = None
                    event.accept()
                    return
                start = self._connection_point(source, pos)
                path = QPainterPath(start)
                self.current_connector = DiagramConnector(path, source_id=source.item_id)
                self.current_connector.set_theme(self.palette)
                self.addItem(self.current_connector)
                self._last_draw_point = start
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.mode.startswith("shape:") and self._shape_preview is not None:
            self._update_shape_preview(event.scenePos())
            event.accept()
            return
        if self.mode == "connect" and self.current_connector is not None:
            self._last_draw_point = self._append_sample(
                self.current_connector, event.scenePos(), self._last_draw_point
            )
            points = _path_points(self.current_connector.path())
            nodes = self._nodes_by_id()
            source = nodes.get(self.current_connector.source_id or "")
            if source is not None and len(points) >= 2:
                toward = QPointF(points[1][0], points[1][1])
                start = self._connection_point(source, toward)
                points[0] = [start.x(), start.y()]
                rebuilt = _path_from_points(points)
                if rebuilt is not None:
                    self.current_connector.setPath(rebuilt)
            event.accept()
            return
        super().mouseMoveEvent(event)
        self.update_connections()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.mode.startswith("shape:"):
            self._finish_shape_preview(event.scenePos())
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton and self.mode == "connect":
            item = self.current_connector
            if item is not None:
                self._append_sample(item, event.scenePos(), self._last_draw_point)
                keep_item = item.path().elementCount() >= 2
                target = self._endpoint_at(event.scenePos())
                valid_target = (
                    target is not None
                    and item.source_id is not None
                    and target.item_id != item.source_id
                )
                if not valid_target:
                    keep_item = False
                else:
                    item.target_id = target.item_id
                    points = _path_points(item.path())
                    if len(points) >= 2:
                        end = self._connection_point(target, QPointF(points[-2][0], points[-2][1]))
                        points[-1] = [end.x(), end.y()]
                        rebuilt = _path_from_points(points)
                        if rebuilt is not None:
                            item.setPath(rebuilt)
                if not keep_item and item.scene() is self:
                    self.removeItem(item)
                self.current_connector = None
                self._last_draw_point = None
                if keep_item:
                    self._notify_changed()
            event.accept()
            return

        super().mouseReleaseEvent(event)
        self._notify_changed()

    def delete_selected(self) -> None:
        selected = list(self.selectedItems())
        if not selected:
            return
        node_ids = {item.item_id for item in selected if isinstance(item, (DiagramShape, DiagramText, DiagramFreehand))}
        for item in list(self.items()):
            if isinstance(item, (DiagramEdge, DiagramConnector)) and (
                item.source_id in node_ids or item.target_id in node_ids
            ):
                self.removeItem(item)
        for item in selected:
            if item.scene() is self:
                self.removeItem(item)
        if node_ids:
            self.itemsDeleted.emit(sorted(node_ids))
        self._notify_changed()

    def set_review_statuses(self, statuses: dict[str, str]) -> None:
        for item in self.items():
            if isinstance(item, DiagramShape):
                item.set_review_status(statuses.get(item.item_id))

    def duplicate_selected(self) -> None:
        selected = list(self.selectedItems())
        if not selected:
            return
        self.clearSelection()
        created = False
        offset = QPointF(24.0, 24.0)
        for item in selected:
            if isinstance(item, DiagramShape):
                copy = self.add_shape(item.shape_type, item.pos() + offset, item.text, width=item.width, height=item.height)
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramText):
                copy = self.add_text(item.pos() + offset, item.toPlainText())
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramFreehand):
                scene_path = self._scene_path(item)
                path = _translated_path(scene_path, offset)
                copy = self.add_freehand_path(path, notify=False)
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramConnector):
                path = _translated_path(item.path(), offset)
                copy = self.add_connector_path(
                    path, notify=False, source_id=item.source_id, target_id=item.target_id
                )
                copy.setSelected(True)
                created = True
        if created:
            self._notify_changed()

    def set_theme(self, palette: dict[str, str] | bool) -> None:
        if isinstance(palette, bool):
            # Compatibility with older caller code/tests.
            palette = {
                **DEFAULT_DIAGRAM_PALETTE,
                **(
                    {
                        "background": "#151515",
                        "grid_minor": "#1d1d1d",
                        "grid_major": "#292929",
                        "stroke": "#c4c7cc",
                        "fill": "#1b1b1b",
                        "text": "#f0f0f0",
                        "connector": "#c4c7cc",
                    }
                    if palette
                    else {}
                ),
            }
        self.palette = {**DEFAULT_DIAGRAM_PALETTE, **palette}
        self.setBackgroundBrush(QBrush(QColor(self.palette["background"])))
        self.path_pen = _pen(self.palette["stroke"])
        for item in self.items():
            if isinstance(item, (DiagramShape, DiagramText, DiagramEdge, DiagramFreehand, DiagramConnector)):
                item.set_theme(self.palette)

    def to_data(self) -> dict[str, object]:
        nodes: list[dict[str, object]] = []
        edges: list[dict[str, object]] = []
        paths: list[dict[str, object]] = []
        connectors: list[dict[str, object]] = []
        for item in self.items():
            if isinstance(item, DiagramShape):
                nodes.append(
                    {
                        "type": "shape",
                        "shape": item.shape_type,
                        "id": item.item_id,
                        "x": item.x(),
                        "y": item.y(),
                        "text": item.text,
                        "width": item.width,
                        "height": item.height,
                    }
                )
            elif isinstance(item, DiagramText):
                nodes.append(
                    {
                        "type": "text",
                        "id": item.item_id,
                        "x": item.x(),
                        "y": item.y(),
                        "text": item.toPlainText(),
                    }
                )
            elif isinstance(item, DiagramEdge):
                edges.append({"source": item.source_id, "target": item.target_id})
            elif isinstance(item, DiagramConnector):
                points = _path_points(item.path())
                if (
                    points
                    and item.source_id
                    and item.target_id
                    and item.source_id != item.target_id
                ):
                    connectors.append(
                        {
                            "points": points,
                            "source": item.source_id,
                            "target": item.target_id,
                        }
                    )
            elif isinstance(item, DiagramFreehand):
                points = _path_points(self._scene_path(item))
                if points:
                    paths.append({"id": item.item_id, "points": points})
        return {"version": 5, "items": nodes, "edges": edges, "paths": paths, "connectors": connectors}

    def load_data(self, data: dict[str, object]) -> None:
        self.loading = True
        try:
            self.current_path = None
            self.current_connector = None
            self._last_draw_point = None
            self._shape_preview = None
            self._shape_start = None
            self._shape_type = None
            self.clear()
            id_map: dict[str, DiagramEndpoint] = {}
            for raw in data.get("items", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                item_id = str(raw.get("id", self._new_id()))
                try:
                    pos = QPointF(float(raw.get("x", 0.0)), float(raw.get("y", 0.0)))
                except (TypeError, ValueError):
                    pos = QPointF()
                text = str(raw.get("text", "Shape"))
                item_type = str(raw.get("type", "node"))
                if item_type == "text":
                    item = self.add_text(pos, text, item_id)
                else:
                    # Version 1 stored rectangle nodes as type="node" without a shape field.
                    shape_type = str(raw.get("shape", "rect"))
                    try:
                        width = float(raw["width"]) if "width" in raw else None
                        height = float(raw["height"]) if "height" in raw else None
                    except (TypeError, ValueError):
                        width = None
                        height = None
                    item = self.add_shape(
                        shape_type, pos, text, item_id, width=width, height=height, notify=False
                    )
                id_map[item_id] = item

            for raw in data.get("edges", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                source = id_map.get(str(raw.get("source", "")))
                target = id_map.get(str(raw.get("target", "")))
                if source is not None and target is not None and source is not target:
                    self.add_edge(source, target)

            for raw in data.get("paths", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                path = _path_from_points(raw.get("points", []))
                if path is None:
                    continue
                item_id = str(raw.get("id", self._new_id()))
                path_item = self.add_freehand_path(path, item_id=item_id, notify=False)
                id_map[item_id] = path_item

            for raw in data.get("connectors", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                path = _path_from_points(raw.get("points", []))
                if path is not None:
                    source_id = str(raw.get("source")) if raw.get("source") else None
                    target_id = str(raw.get("target")) if raw.get("target") else None
                    # Version 4+ only accepts connectors that are anchored at both ends.
                    # Legacy floating connectors are intentionally ignored instead of
                    # reintroducing arrows that point to empty canvas space.
                    if (
                        source_id in id_map
                        and target_id in id_map
                        and source_id != target_id
                    ):
                        self.add_connector_path(
                            path, notify=False, source_id=source_id, target_id=target_id
                        )

            self.update_connections()
            self.set_theme(self.palette)
        finally:
            self.loading = False


class DiagramCanvas(QGraphicsView):
    def __init__(self, scene: DiagramScene, parent=None) -> None:
        super().__init__(scene, parent)
        self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self._middle_panning = False
        self._middle_pan_pos = QPointF()


    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._middle_panning = True
            self._middle_pan_pos = event.position()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._middle_panning:
            current = event.position()
            delta = current - self._middle_pan_pos
            self._middle_pan_pos = current
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._middle_panning:
            self._middle_panning = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def set_mode(self, mode: str) -> None:
        if mode == "pan":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        elif mode == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)

    def set_theme(self, palette: dict[str, str] | bool) -> None:
        if isinstance(palette, bool):
            self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
            if palette:
                self.palette.update(
                    {
                        "background": "#151515",
                        "grid_minor": "#1d1d1d",
                        "grid_major": "#292929",
                    }
                )
        else:
            self.palette = {**DEFAULT_DIAGRAM_PALETTE, **palette}
        self.viewport().update()

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor(self.palette["background"]))
        minor = 25
        major = 100
        left = int(math.floor(rect.left() / minor) * minor)
        top = int(math.floor(rect.top() / minor) * minor)
        minor_pen = QPen(QColor(self.palette["grid_minor"]), 1.0)
        major_pen = QPen(QColor(self.palette["grid_major"]), 1.0)
        x = left
        while x < rect.right():
            painter.setPen(major_pen if x % major == 0 else minor_pen)
            painter.drawLine(QLineF(float(x), rect.top(), float(x), rect.bottom()))
            x += minor
        y = top
        while y < rect.bottom():
            painter.setPen(major_pen if y % major == 0 else minor_pen)
            painter.drawLine(QLineF(rect.left(), float(y), rect.right(), float(y)))
            y += minor

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def keyPressEvent(self, event) -> None:
        scene = self.scene()
        if isinstance(scene, DiagramScene):
            if event.key() == Qt.Key.Key_Delete:
                scene.delete_selected()
                event.accept()
                return
            if event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                scene.duplicate_selected()
                event.accept()
                return
        super().keyPressEvent(event)

    def fit_all(self) -> None:
        scene = self.scene()
        if scene is None:
            return
        bounds = scene.itemsBoundingRect()
        if bounds.isNull() or bounds.isEmpty():
            self.resetTransform()
            return
        self.fitInView(bounds.adjusted(-60, -60, 60, 60), Qt.AspectRatioMode.KeepAspectRatio)


class DiagramView(QWidget):
    diagramChanged = Signal()
    itemsDeleted = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        bar = QHBoxLayout()
        bar.setContentsMargins(6, 4, 6, 0)
        self.scene = DiagramScene(self)
        self.scene.diagramChanged.connect(self.diagramChanged)
        self.scene.itemsDeleted.connect(self.itemsDeleted)
        self.canvas = DiagramCanvas(self.scene)
        self._mode_buttons: dict[str, QPushButton] = {}

        tools = [
            ("Select", "select", "Select/move items; selected shapes show resize handles"),
            ("Pan", "pan", "Pan the canvas (middle mouse drag works in every tool)"),
            ("Square", "shape:square", "Press and drag to draw a box at exactly the size you want; stretch it into a rectangle if needed"),
            ("Round", "shape:rounded", "Press and drag to draw a rounded box at the size you want"),
            ("Ellipse", "shape:ellipse", "Press and drag to draw an ellipse at the size you want"),
            ("Diamond", "shape:diamond", "Press and drag to draw a decision diamond at the size you want"),
            ("Text", "text", "Add standalone text"),
            ("Connect", "connect", "Start on one existing item and drag any route to another item; the arrow points to the target"),
        ]
        for label, mode, tooltip in tools:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setToolTip(tooltip)
            button.clicked.connect(lambda _checked=False, m=mode: self.set_mode(m))
            bar.addWidget(button)
            self._mode_buttons[mode] = button

        bar.addStretch(1)
        duplicate = QPushButton("Duplicate")
        duplicate.setToolTip("Duplicate selected diagram items (Ctrl+D)")
        duplicate.clicked.connect(self.scene.duplicate_selected)
        fit = QPushButton("Fit")
        fit.setToolTip("Fit all diagram items in view")
        fit.clicked.connect(self.canvas.fit_all)
        zoom_out = QPushButton("−")
        zoom_out.setToolTip("Zoom out")
        zoom_out.clicked.connect(lambda: self.canvas.scale(0.85, 0.85))
        zoom_in = QPushButton("+")
        zoom_in.setToolTip("Zoom in")
        zoom_in.clicked.connect(lambda: self.canvas.scale(1.15, 1.15))
        delete = QPushButton("Delete")
        delete.setToolTip("Delete selected diagram items (Delete)")
        delete.clicked.connect(self.scene.delete_selected)
        for button in (duplicate, fit, zoom_out, zoom_in, delete):
            bar.addWidget(button)

        hint = QLabel(
            "Square/Round/Ellipse/Diamond: basılı tutup sürükleyerek istediğin boyutta çiz. Select: seçili şeklin 8 tutamacından yeniden boyutlandır. Connect: bir öğeden diğerine rota çiz. Orta mouse: canvas taşı."
        )
        hint.setObjectName("diagramHint")
        hint.setContentsMargins(8, 0, 8, 2)

        root.addLayout(bar)
        root.addWidget(hint)
        root.addWidget(self.canvas, 1)
        self.set_mode("shape:square")

    def set_mode(self, mode: str) -> None:
        self.scene.set_mode(mode)
        self.canvas.set_mode(mode)
        for button_mode, button in self._mode_buttons.items():
            button.setChecked(button_mode == mode)

    def set_theme(self, palette: dict[str, str] | bool) -> None:
        self.scene.set_theme(palette)
        self.canvas.set_theme(palette)

    def load_data(self, data: dict[str, object]) -> None:
        self.scene.load_data(data)
        self.canvas.resetTransform()

    def to_data(self) -> dict[str, object]:
        return self.scene.to_data()

    def set_review_statuses(self, statuses: dict[str, str]) -> None:
        self.scene.set_review_statuses(statuses)

    def delete_selected(self) -> None:
        self.scene.delete_selected()
