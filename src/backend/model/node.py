# -*- coding: utf-8 -*-
"""
Узел схемы: id, label, тип, пины, позиция. accept(visitor) — обход (Visitor).
context при вычислении: input_values (входы), cache (посчитанные узлы).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.common.enums import NodeType


class NodeVisitor(ABC):
    """Один вызов на тип: вход, выход, любой вентиль (LogicGate)."""

    @abstractmethod
    def visit_input(self, node: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def visit_output(self, node: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def visit_gate(self, node: Any) -> Any:
        raise NotImplementedError


@dataclass(slots=True)
class Point:
    x: float
    y: float


@dataclass(slots=True)
class InputPin:
    index: int
    connected_from: str | None = None


@dataclass(slots=True)
class OutputPin:
    index: int


@dataclass(slots=True)
class EvaluationContext:
    input_values: dict[str, bool] = field(default_factory=dict)
    cache: dict[str, bool] = field(default_factory=dict)


@dataclass(slots=True)
class CircuitNode(ABC):
    id: str
    label: str
    node_type: NodeType
    input_pins: list[InputPin]
    output_pins: list[OutputPin]
    position: Point

    @abstractmethod
    def accept(self, visitor: NodeVisitor) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_value(self, context: EvaluationContext) -> bool:
        raise NotImplementedError

    def can_accept_input(self, pin_index: int) -> bool:
        return 0 <= pin_index < len(self.input_pins)

    @abstractmethod
    def clone(self) -> CircuitNode:
        raise NotImplementedError
