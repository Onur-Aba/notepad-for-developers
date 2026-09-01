from __future__ import annotations

from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QAbstractScrollArea, QSpinBox, QWidget


class NoWheelSpinBox(QSpinBox):
    """A number input whose value cannot be changed accidentally by scrolling.

    In a scrollable settings window the wheel gesture is forwarded to the
    surrounding scroll area, so hovering a number field never traps scrolling.
    """

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 - Qt API name
        parent: QWidget | None = self.parentWidget()
        while parent is not None:
            if isinstance(parent, QAbstractScrollArea):
                bar = parent.verticalScrollBar()
                delta = event.angleDelta().y()
                if delta:
                    step = max(bar.singleStep() * 3, 36)
                    direction = -1 if delta > 0 else 1
                    bar.setValue(bar.value() + direction * step)
                    event.accept()
                    return
            parent = parent.parentWidget()
        event.ignore()
