# -*- coding: utf-8 -*-
"""
Точка входа «собрать окно»: создаём пустой фасад с пустой схемой и MainWindow.

Дальше в реальном приложении: запуск QApplication, показ MainWindow,
связь сигналов кнопок с facade.add_node и т.д.
"""
from src.backend.facade import CircuitEditorFacade
from src.frontend.app.main_window import MainWindow


def create_application() -> MainWindow:
    return MainWindow(facade=CircuitEditorFacade())
