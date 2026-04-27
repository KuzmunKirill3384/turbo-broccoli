# -*- coding: utf-8 -*-
"""
fixed_inputs — какие входы схемы зафиксировали в True/False перед упрощением.
latest_report — что вернул facade.simplify (сколько узлов убрали и т.д.).

collect_fixed_inputs копирует словарь, чтобы UI не менял общий объект по ссылке случайно.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.backend.stubs import SimplificationReport


@dataclass(slots=True)
class SimplificationPanel:
    fixed_inputs: dict[str, bool] = field(default_factory=dict)
    latest_report: SimplificationReport = field(default_factory=SimplificationReport)

    def collect_fixed_inputs(self) -> dict[str, bool]:
        return dict(self.fixed_inputs)

    def show_report(self, report: SimplificationReport) -> None:
        self.latest_report = report
