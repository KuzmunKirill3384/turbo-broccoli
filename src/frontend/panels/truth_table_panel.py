# -*- coding: utf-8 -*-
"""
Данные таблицы истинности приходят с бэка (TruthTable); панель хранит последнюю версию.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.backend.stubs import TruthTable


@dataclass(slots=True)
class TruthTablePanel:
    current_table: TruthTable = field(default_factory=TruthTable)

    def show_table(self, table: TruthTable) -> None:
        self.current_table = table
