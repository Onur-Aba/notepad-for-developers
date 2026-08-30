from __future__ import annotations

import math
import uuid
from typing import Callable

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
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


# Square/rectangle remain supported internally so diagrams created with DevNest 1.1
# keep loading, but they are intentionally not offered as creation tools anymore.
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


class DiagramShape(QGraphicsPathItem):
    def __init__(
        self,
        item_id: str,
        shape_type: str,
        text: str,
        on_changed: Callable[[], None],
    ) -> None:
        super().__init__()
        self.item_id = item_id
        self.shape_type = shape_type if shape_type in SHAPE_SIZES else "rect"
        self._on_changed = on_changed
        self._width, self._height = SHAPE_SIZES[self.shape_type]
        self.setPath(self._make_path())
        self.label = QGraphicsTextItem(text, self)
        self.label.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.label.setTextWidth(max(52.0, self._width - 20.0))
        self._position_label()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPen(_pen("#747b88", 1.6))
        self.setBrush(QBrush(QColor("#ffffff")))

    def _make_path(self) -> QPainterPath:
        rect = QRectF(0.0, 0.0, self._width, self._height)
        path = QPainterPath()
        if self.shape_type == "ellipse":
            path.addEllipse(rect)
        elif self.shape_type == "diamond":
            polygon = QPolygonF(
                [
                    QPointF(self._width / 2.0, 0.0),
                    QPointF(self._width, self._height / 2.0),
                    QPointF(self._width / 2.0, self._height),
                    QPointF(0.0, self._height / 2.0),
                ]
            )
            path.addPolygon(polygon)
            path.closeSubpath()
        elif self.shape_type == "rounded":
            path.addRoundedRect(rect, 14.0, 14.0)
        else:
            path.addRect(rect)
        return path

    def _position_label(self) -> None:
        label_height = self.label.boundingRect().height()
        self.label.setPos(10.0, max(6.0, (self._height - label_height) / 2.0))

    @property
    def text(self) -> str:
        return self.label.toPlainText()

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setBrush(QBrush(QColor(palette["fill"])))
        self.setPen(_pen(palette["stroke"], 1.6))
        self.label.setDefaultTextColor(QColor(palette["text"]))

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        return result

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        text, ok = QInputDialog.getText(None, "Edit Shape", "Text:", text=self.text)
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
        text, ok = QInputDialog.getMultiLineText(None, "Edit Text", "Text:", self.toPlainText())
        if ok:
            self.setPlainText(text)
            self._on_changed()
        event.accept()


DiagramEndpoint = DiagramShape | DiagramText


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
        self.setPen(_pen("#596273"))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"]))

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
    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["stroke"]))


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
        self.setPen(_pen("#596273"))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"]))

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
    arrow_size = 11.0
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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.mode = "select"
        self.current_path: DiagramFreehand | None = None
        self.current_connector: DiagramConnector | None = None
        self._last_draw_point: QPointF | None = None
        self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
        self.path_pen = _pen(self.palette["stroke"])
        self.loading = False
        self.setSceneRect(-2500, -2500, 5000, 5000)

    def set_mode(self, mode: str) -> None:
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
    ) -> DiagramShape:
        label = text if text is not None else SHAPE_LABELS.get(shape_type, "Shape")
        shape = DiagramShape(item_id or self._new_id(), shape_type, label, self._notify_changed)
        shape.set_theme(self.palette)
        self.addItem(shape)
        shape.setPos(pos)
        self._notify_changed()
        return shape

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

    def add_connector_path(
        self,
        path: QPainterPath,
        notify: bool = True,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> DiagramConnector:
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
            start = self._boundary_point(source, target_center)
            end = self._boundary_point(target, source_center)
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
                start = self._boundary_point(nodes[item.source_id], toward)
                points[0] = [start.x(), start.y()]
            if item.target_id and item.target_id in nodes:
                toward = QPointF(points[-2][0], points[-2][1])
                end = self._boundary_point(nodes[item.target_id], toward)
                points[-1] = [end.x(), end.y()]
            rebuilt = _path_from_points(points)
            if rebuilt is not None:
                item.setPath(rebuilt)

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
            if isinstance(item, (DiagramShape, DiagramText)):
                result[item.item_id] = item
        return result

    def _node_at(self, pos: QPointF) -> DiagramEndpoint | None:
        for item in self.items(pos):
            current = item
            while current is not None:
                if isinstance(current, (DiagramShape, DiagramText)):
                    return current
                current = current.parentItem()
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
                shape_type = self.mode.split(":", 1)[1]
                width, height = SHAPE_SIZES.get(shape_type, SHAPE_SIZES["rect"])
                self.add_shape(shape_type, pos - QPointF(width / 2.0, height / 2.0))
                event.accept()
                return
            if self.mode == "text":
                text, ok = QInputDialog.getText(None, "Text", "Text:")
                if ok:
                    self.add_text(pos, text or "Text")
                event.accept()
                return
            if self.mode == "draw":
                path = QPainterPath(pos)
                self.current_path = DiagramFreehand(path)
                self.current_path.setPen(self.path_pen)
                self.current_path.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                self.addItem(self.current_path)
                self._last_draw_point = pos
                event.accept()
                return
            if self.mode == "connect":
                path = QPainterPath(pos)
                source = self._node_at(pos)
                self.current_connector = DiagramConnector(
                    path,
                    source_id=source.item_id if source is not None else None,
                )
                self.current_connector.set_theme(self.palette)
                self.addItem(self.current_connector)
                self._last_draw_point = pos
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.mode == "draw" and self.current_path is not None:
            self._last_draw_point = self._append_sample(self.current_path, event.scenePos(), self._last_draw_point)
            event.accept()
            return
        if self.mode == "connect" and self.current_connector is not None:
            self._last_draw_point = self._append_sample(self.current_connector, event.scenePos(), self._last_draw_point)
            event.accept()
            return
        super().mouseMoveEvent(event)
        self.update_edges()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.mode in {"draw", "connect"}:
            item: QGraphicsPathItem | None = self.current_path if self.mode == "draw" else self.current_connector
            if item is not None:
                self._append_sample(item, event.scenePos(), self._last_draw_point)
                if isinstance(item, DiagramConnector):
                    target = self._node_at(event.scenePos())
                    item.target_id = target.item_id if target is not None else None
                    if item.source_id == item.target_id:
                        item.target_id = None
                if item.path().elementCount() < 2:
                    self.removeItem(item)
                self.current_path = None
                self.current_connector = None
                self._last_draw_point = None
                self._notify_changed()
            event.accept()
            return
        super().mouseReleaseEvent(event)
        self._notify_changed()

    def delete_selected(self) -> None:
        selected = list(self.selectedItems())
        if not selected:
            return
        node_ids = {item.item_id for item in selected if isinstance(item, (DiagramShape, DiagramText))}
        for item in list(self.items()):
            if isinstance(item, (DiagramEdge, DiagramConnector)) and (
                item.source_id in node_ids or item.target_id in node_ids
            ):
                self.removeItem(item)
        for item in selected:
            if item.scene() is self:
                self.removeItem(item)
        self._notify_changed()

    def duplicate_selected(self) -> None:
        selected = list(self.selectedItems())
        if not selected:
            return
        self.clearSelection()
        created = False
        offset = QPointF(24.0, 24.0)
        for item in selected:
            if isinstance(item, DiagramShape):
                copy = self.add_shape(item.shape_type, item.pos() + offset, item.text)
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramText):
                copy = self.add_text(item.pos() + offset, item.toPlainText())
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramFreehand):
                path = _translated_path(item.path(), offset)
                copy = DiagramFreehand(path)
                copy.setPen(self.path_pen)
                copy.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                self.addItem(copy)
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
                if points:
                    connector_data: dict[str, object] = {"points": points}
                    if item.source_id:
                        connector_data["source"] = item.source_id
                    if item.target_id:
                        connector_data["target"] = item.target_id
                    connectors.append(connector_data)
            elif isinstance(item, DiagramFreehand):
                points = _path_points(item.path())
                if points:
                    paths.append({"points": points})
        return {"version": 3, "items": nodes, "edges": edges, "paths": paths, "connectors": connectors}

    def load_data(self, data: dict[str, object]) -> None:
        self.loading = True
        try:
            self.current_path = None
            self.current_connector = None
            self._last_draw_point = None
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
                    item = self.add_shape(shape_type, pos, text, item_id)
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
                path_item = DiagramFreehand(path)
                path_item.set_theme(self.palette)
                path_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                self.addItem(path_item)

            for raw in data.get("connectors", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                path = _path_from_points(raw.get("points", []))
                if path is not None:
                    source_id = str(raw.get("source")) if raw.get("source") else None
                    target_id = str(raw.get("target")) if raw.get("target") else None
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

    def set_mode(self, mode: str) -> None:
        if mode == "pan":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        elif mode == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        bar = QHBoxLayout()
        bar.setContentsMargins(6, 4, 6, 0)
        self.scene = DiagramScene(self)
        self.scene.diagramChanged.connect(self.diagramChanged)
        self.canvas = DiagramCanvas(self.scene)
        self._mode_buttons: dict[str, QPushButton] = {}

        tools = [
            ("Select", "select", "Select and move diagram items"),
            ("Pan", "pan", "Pan the canvas"),
            ("Draw", "draw", "Draw any shape or line freely by hand"),
            ("Connect", "connect", "Press and drag to draw an arrow; the route is kept exactly as drawn"),
            ("Round", "shape:rounded", "Add a rounded process box"),
            ("Ellipse", "shape:ellipse", "Add an ellipse"),
            ("Diamond", "shape:diamond", "Add a diamond / decision shape"),
            ("Text", "text", "Add standalone text"),
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
            "Draw: el ile serbest çiz. Connect: basılı tutup istediğin rotayı çiz; ok eğimi ve kıvrımı çizdiğin gibi saklanır."
        )
        hint.setObjectName("diagramHint")
        hint.setContentsMargins(8, 0, 8, 2)

        root.addLayout(bar)
        root.addWidget(hint)
        root.addWidget(self.canvas, 1)
        self.set_mode("draw")

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

    def delete_selected(self) -> None:
        self.scene.delete_selected()
