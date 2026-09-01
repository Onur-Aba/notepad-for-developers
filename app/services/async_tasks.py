from __future__ import annotations

import traceback
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class TaskSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()


class FunctionTask(QRunnable):
    def __init__(self, function: Callable[[], Any]) -> None:
        super().__init__()
        self.function = function
        self.signals = TaskSignals()

    @Slot()
    def run(self) -> None:
        try:
            value = self.function()
        except Exception as exc:
            self.signals.failed.emit(exc)
        else:
            self.signals.succeeded.emit(value)
        finally:
            self.signals.finished.emit()


class AsyncTaskRunner:
    def __init__(self, pool: QThreadPool | None = None) -> None:
        self.pool = pool or QThreadPool.globalInstance()
        self._tasks: set[FunctionTask] = set()

    def submit(self, function: Callable[[], Any], on_success: Callable[[Any], None] | None = None,
               on_error: Callable[[Exception], None] | None = None,
               on_finished: Callable[[], None] | None = None) -> FunctionTask:
        task = FunctionTask(function)
        self._tasks.add(task)
        if on_success:
            task.signals.succeeded.connect(on_success)
        if on_error:
            task.signals.failed.connect(on_error)
        if on_finished:
            task.signals.finished.connect(on_finished)
        task.signals.finished.connect(lambda: self._tasks.discard(task))
        self.pool.start(task)
        return task
