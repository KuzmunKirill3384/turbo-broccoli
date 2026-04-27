# -*- coding: utf-8 -*-
"""
Настройки отрисовки (тема, размер). Не связаны с булевой схемой — только с тем, как окно выглядит.
Потом сюда добавят загрузку из файла и применение к виджетам.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SettingsDialog:
    theme: str = "light"
    node_size: int = 120
    font_size: int = 12
    colors: dict[str, str] = field(default_factory=dict)

    def apply_settings(self) -> None:
        return None

    def load_settings(self) -> None:
        return None

    def save_settings(self) -> None:
        return None
