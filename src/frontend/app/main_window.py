# -*- coding: utf-8 -*-
"""
Главное окно в виде обычного класса (без Qt), чтобы логику тестировать без GUI.

facade — всё, что касается схемы: смотри CircuitEditorFacade.
canvas_view, панели — заглушки: хранят состояние, которое потом привяжешь к виджетам.

refresh_all вызывай после любой команды, которая меняет схему, чтобы перерисовать холст.
show_error — пока просто строка; в Qt сюда вставят QMessageBox.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.backend.facade import CircuitEditorFacade
from src.frontend.canvas.view import CircuitCanvasView
from src.frontend.dialogs.settings_dialog import SettingsDialog
from src.frontend.panels.polynomial_panel import PolynomialPanel
from src.frontend.panels.simplification_panel import SimplificationPanel
from src.frontend.panels.truth_table_panel import TruthTablePanel


@dataclass(slots=True)
class MainWindow:
    facade: CircuitEditorFacade
    canvas_view: CircuitCanvasView = field(default_factory=CircuitCanvasView)
    truth_table_panel: TruthTablePanel = field(default_factory=TruthTablePanel)
    simplification_panel: SimplificationPanel = field(default_factory=SimplificationPanel)
    polynomial_panel: PolynomialPanel = field(default_factory=PolynomialPanel)
    settings_dialog: SettingsDialog = field(default_factory=SettingsDialog)
    last_error_message: str = ""

    def bind_actions(self) -> None:
        return None

    def refresh_all(self) -> None:
        self.canvas_view.render_circuit(self.facade.circuit)

    def show_error(self, message: str) -> None:
        self.last_error_message = message
