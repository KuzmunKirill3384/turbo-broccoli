# -*- coding: utf-8 -*-
"""
Три сущности на схеме (проще, чем отдельный класс на каждый вентиль):

1) InputNode  — ножка «вход схемы», значение берётся из context при переборе
   или из default_value, если задали.
2) OutputNode  — куда выводим результат; в cache должен лежать итог (его пишет
   код оценки схемы, когда дойдёт до выхода).
3) LogicGate  — ОДНА класс для AND, OR, XOR, EQUAL: отличается только полем
   node_type. Функция boolean по входам вынесена в _eval_gate, чтобы глазами
   увидеть таблицу в одном месте.

Старый вариант с AndGate, OrGate, XorGate, EqualGate делал ровно то же, но
засорял проект копипастой.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.backend.model.node import CircuitNode, EvaluationContext, InputPin, NodeVisitor, OutputPin, Point
from src.common.enums import NodeType


@dataclass(slots=True)
class InputNode(CircuitNode):
    default_value: bool | None = None

    def __init__(self, node_id: str, label: str, position: Point, default_value: bool | None = None) -> None:
        # Явный вызов базы: super() с dataclass+ABC в Py3 иногда ломается
        CircuitNode.__init__(
            self,
            id=node_id,
            label=label,
            node_type=NodeType.INPUT,
            input_pins=[],
            output_pins=[OutputPin(index=0)],
            position=position,
        )
        self.default_value = default_value

    def set_value(self, value: bool) -> None:
        self.default_value = value

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_input(self)

    def get_value(self, context: EvaluationContext) -> bool:
        if self.id in context.input_values:
            return context.input_values[self.id]
        if self.default_value is None:
            raise ValueError(f"Input node '{self.id}' has no value in the evaluation context.")
        return self.default_value

    def clone(self) -> InputNode:
        return InputNode(
            node_id=self.id,
            label=self.label,
            position=Point(self.position.x, self.position.y),
            default_value=self.default_value,
        )


@dataclass(slots=True)
class OutputNode(CircuitNode):
    def __init__(self, node_id: str, label: str, position: Point) -> None:
        CircuitNode.__init__(
            self,
            id=node_id,
            label=label,
            node_type=NodeType.OUTPUT,
            input_pins=[InputPin(index=0)],
            output_pins=[],
            position=position,
        )

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_output(self)

    def get_value(self, context: EvaluationContext) -> bool:
        if self.id not in context.cache:
            raise ValueError(f"Output node '{self.id}' is not resolved in the evaluation context.")
        return context.cache[self.id]

    def clone(self) -> OutputNode:
        return OutputNode(node_id=self.id, label=self.label, position=Point(self.position.x, self.position.y))


def _eval_gate(gate_type: NodeType, inputs: list[bool]) -> bool:
    if gate_type == NodeType.AND:
        return all(inputs)
    if gate_type == NodeType.OR:
        return any(inputs)
    if gate_type == NodeType.XOR:
        return sum(1 for v in inputs if v) % 2 == 1
    if gate_type == NodeType.EQUAL:
        return len(set(inputs)) <= 1
    raise ValueError(f"Не вентиль: {gate_type}")


@dataclass(slots=True)
class LogicGate(CircuitNode):
    """
    Вентиль с двумя входами по умолчанию (arity=2), один выход.
    get_value смотрит в cache: туда кладёшь результат, когда в программе
    оценки дошла очередь до этого id.
    """
    arity: int

    def __init__(
        self,
        node_id: str,
        label: str,
        position: Point,
        node_type: NodeType,
        arity: int = 2,
    ) -> None:
        if node_type not in (NodeType.AND, NodeType.OR, NodeType.XOR, NodeType.EQUAL):
            raise ValueError(f"LogicGate only for gate types, got {node_type}")
        CircuitNode.__init__(
            self,
            id=node_id,
            label=label,
            node_type=node_type,
            input_pins=[InputPin(index=i) for i in range(arity)],
            output_pins=[OutputPin(index=0)],
            position=position,
        )
        self.arity = arity

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_gate(self)

    def evaluate(self, inputs: list[bool]) -> bool:
        return _eval_gate(self.node_type, inputs)

    def get_value(self, context: EvaluationContext) -> bool:
        if self.id not in context.cache:
            raise ValueError(f"Gate node '{self.id}' is not resolved in the evaluation context.")
        return context.cache[self.id]

    def clone(self) -> LogicGate:
        return LogicGate(
            node_id=self.id,
            label=self.label,
            position=Point(self.position.x, self.position.y),
            node_type=self.node_type,
            arity=self.arity,
        )
