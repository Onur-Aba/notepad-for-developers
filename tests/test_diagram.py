from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication

from app.widgets.diagram_view import DiagramConnector, DiagramFreehand, DiagramScene, DiagramShape, DiagramView


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_shape_types_connections_and_round_trip(app: QApplication) -> None:
    scene = DiagramScene()
    first = scene.add_shape("square", QPointF(10, 20), "Frontend")
    second = scene.add_shape("diamond", QPointF(260, 30), "API?")
    third = scene.add_shape("ellipse", QPointF(500, 20), "Database")
    scene.add_edge(first, second)
    scene.add_edge(second, third)

    data = scene.to_data()
    shapes = [item for item in data["items"] if item["type"] == "shape"]
    assert {item["shape"] for item in shapes} == {"square", "diamond", "ellipse"}
    assert len(data["edges"]) == 2

    restored = DiagramScene()
    restored.load_data(data)
    restored_data = restored.to_data()
    assert len(restored_data["items"]) == 3
    assert len(restored_data["edges"]) == 2


def test_old_rectangle_node_data_is_backward_compatible(app: QApplication) -> None:
    scene = DiagramScene()
    scene.load_data(
        {
            "items": [{"type": "node", "id": "old", "x": 1, "y": 2, "text": "Legacy"}],
            "edges": [],
            "paths": [],
        }
    )
    shapes = [item for item in scene.items() if isinstance(item, DiagramShape)]
    assert len(shapes) == 1
    assert shapes[0].shape_type == "rect"
    assert shapes[0].text == "Legacy"


def _freehand_box(x: float, y: float, size: float = 80.0) -> QPainterPath:
    path = QPainterPath(QPointF(x, y))
    path.lineTo(x + size, y)
    path.lineTo(x + size, y + size)
    path.lineTo(x, y + size)
    path.lineTo(x, y)
    return path


def test_freehand_objects_are_connectable_and_round_trip(app: QApplication) -> None:
    scene = DiagramScene()
    first = scene.add_freehand_path(_freehand_box(10, 10))
    second = scene.add_freehand_path(_freehand_box(260, 40))

    route = QPainterPath(QPointF(90, 50))
    route.lineTo(140, 20)
    route.lineTo(210, 100)
    route.lineTo(260, 80)
    scene.add_connector_path(route, source_id=first.item_id, target_id=second.item_id)

    data = scene.to_data()
    assert data["version"] == 5
    assert len(data["paths"]) == 2
    assert all("id" in path for path in data["paths"])
    assert len(data["connectors"]) == 1
    assert data["connectors"][0]["source"] == first.item_id
    assert data["connectors"][0]["target"] == second.item_id

    restored = DiagramScene()
    restored.load_data(data)
    freehands = [item for item in restored.items() if isinstance(item, DiagramFreehand)]
    connectors = [item for item in restored.items() if isinstance(item, DiagramConnector)]
    assert len(freehands) == 2
    assert len(connectors) == 1
    assert connectors[0].source_id != connectors[0].target_id
    assert connectors[0].path().elementCount() == 4


def test_floating_connector_is_rejected(app: QApplication) -> None:
    scene = DiagramScene()
    path = QPainterPath(QPointF(10, 10))
    path.lineTo(100, 100)
    with pytest.raises(ValueError):
        scene.add_connector_path(path)


def test_freehand_connection_point_uses_drawn_contour_not_center(app: QApplication) -> None:
    scene = DiagramScene()
    freehand = scene.add_freehand_path(_freehand_box(0, 0, 100))
    point = scene._connection_point(freehand, QPointF(180, 50))
    assert point.x() == pytest.approx(100.0)
    assert point != freehand.sceneBoundingRect().center()


def test_square_is_drag_creation_tool_and_freehand_draw_is_removed(app: QApplication) -> None:
    view = DiagramView()
    assert "shape:square" in view._mode_buttons
    assert "shape:rect" not in view._mode_buttons
    assert "draw" not in view._mode_buttons
    assert "connect" in view._mode_buttons
    assert view.scene.mode == "shape:square"


def test_shape_size_persists_and_can_be_changed(app: QApplication) -> None:
    scene = DiagramScene()
    shape = scene.add_shape("ellipse", QPointF(20, 30), "Service", width=240, height=110)
    assert shape.width == pytest.approx(240.0)
    assert shape.height == pytest.approx(110.0)

    shape.set_size(310, 150)
    data = scene.to_data()
    assert data["version"] == 5
    raw = next(item for item in data["items"] if item["id"] == shape.item_id)
    assert raw["width"] == pytest.approx(310.0)
    assert raw["height"] == pytest.approx(150.0)

    restored = DiagramScene()
    restored.load_data(data)
    restored_shape = next(item for item in restored.items() if isinstance(item, DiagramShape))
    assert restored_shape.width == pytest.approx(310.0)
    assert restored_shape.height == pytest.approx(150.0)


def test_shape_preview_requires_drag_and_uses_dragged_size(app: QApplication) -> None:
    scene = DiagramScene()
    scene._begin_shape_preview("square", QPointF(10, 10))
    assert scene._finish_shape_preview(QPointF(12, 12)) is None
    assert not any(isinstance(item, DiagramShape) for item in scene.items())

    scene._begin_shape_preview("square", QPointF(20, 30))
    created = scene._finish_shape_preview(QPointF(260, 145))
    assert created is not None
    assert created.width == pytest.approx(240.0)
    assert created.height == pytest.approx(115.0)


def test_resize_from_handle_changes_shape_bounds(app: QApplication) -> None:
    scene = DiagramScene()
    shape = scene.add_shape("rounded", QPointF(100, 100), width=160, height=80)
    shape.resize_from_handle("se", QPointF(340, 250))
    assert shape.width == pytest.approx(240.0)
    assert shape.height == pytest.approx(150.0)
