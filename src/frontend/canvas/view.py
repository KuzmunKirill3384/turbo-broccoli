# -*- coding: utf-8 -*-
"""
Простейшее состояние «холста»: какие узлы выделены и какие подсвечены (путь от входов).

render_circuit выбрасывает из выделения id узлов, которых уже нет в схеме
(после удаления), чтобы не держать мусор.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.backend.model.circuit import Circuit


@dataclass(slots=True)
class CircuitCanvasView:
    selected_node_ids: list[str] = field(default_factory=list)
    highlighted_node_ids: list[str] = field(default_factory=list)

    def render_circuit(self, circuit: Circuit) -> None:
        self.selected_node_ids = [nid for nid in self.selected_node_ids if nid in circuit.nodes]

    def highlight_nodes(self, node_ids: list[str]) -> None:
        self.highlighted_node_ids = list(node_ids)

    def clear_selection(self) -> None:
        self.selected_node_ids.clear()
