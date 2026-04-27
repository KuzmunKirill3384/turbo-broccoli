# -*- coding: utf-8 -*-
"""
Сюда кладётся последняя строка полинома, которую вернул facade.get_polynomial.
Сама формула считается на бэкенде, панель только хранит текст для отображения.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PolynomialPanel:
    current_node_id: str | None = None
    current_polynomial: str = ""

    def show_polynomial(self, node_id: str, polynomial: str) -> None:
        self.current_node_id = node_id
        self.current_polynomial = polynomial
