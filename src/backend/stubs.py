# -*- coding: utf-8 -*-
"""
Заглушки под аналитику: таблица истинности, упрощение, полином, зависимости.
Потом допишешь тела методов, не разнося по папкам, пока тут так проще.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.backend.model.circuit import Circuit


@dataclass(slots=True)
class TruthTable:
    headers: list[str] = field(default_factory=list)
    rows: list[list[int]] = field(default_factory=list)


@dataclass(slots=True)
class SimplificationReport:
    removable_node_ids: list[str] = field(default_factory=list)
    removed_count: int = 0
    fixed_inputs: dict[str, bool] = field(default_factory=dict)


class TruthTableService:
    def build_for_circuit(self, circuit: Circuit) -> TruthTable:
        raise NotImplementedError

    def build_for_node(self, circuit: Circuit, node_id: str) -> TruthTable:
        raise NotImplementedError


class SimplificationService:
    def estimate_removal(self, circuit: Circuit, fixed_inputs: dict[str, bool]) -> SimplificationReport:
        raise NotImplementedError

    def simplify(self, circuit: Circuit, fixed_inputs: dict[str, bool]) -> Circuit:
        raise NotImplementedError


class PolynomialService:
    def build_for_node(self, circuit: Circuit, node_id: str) -> str:
        raise NotImplementedError

    def build_for_circuit(self, circuit: Circuit) -> dict[str, str]:
        raise NotImplementedError


class DependencyService:
    def get_affecting_nodes(self, circuit: Circuit, node_id: str) -> list[str]:
        raise NotImplementedError
