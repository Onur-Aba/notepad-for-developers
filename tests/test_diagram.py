from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication

from app.widgets.diagram_view import DiagramConnector, DiagramScene, DiagramShape, DiagramView


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


def test_hand_drawn_connector_round_trip(app: QApplication) -> None:
    scene = DiagramScene()
    path = QPainterPath(QPointF(10, 10))
    path.lineTo(80, 40)
    path.lineTo(120, 15)
    path.lineTo(190, 80)
    scene.add_connector_path(path)

    data = scene.to_data()
    assert data["version"] == 3
    assert len(data["connectors"]) == 1
    assert len(data["connectors"][0]["points"]) == 4

    restored = DiagramScene()
    restored.load_data(data)
    connectors = [item for item in restored.items() if isinstance(item, DiagramConnector)]
    assert len(connectors) == 1
    assert connectors[0].path().elementCount() == 4


def test_square_and_rectangle_are_not_creation_buttons(app: QApplication) -> None:
    view = DiagramView()
    assert "shape:square" not in view._mode_buttons
    assert "shape:rect" not in view._mode_buttons
    assert "draw" in view._mode_buttons
    assert "connect" in view._mode_buttons
