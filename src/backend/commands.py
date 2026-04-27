# -*- coding: utf-8 -*-
"""
Команды: у каждой два метода — execute (сделать) и undo (откатить).
История: два списка (undo, redo). Новое действие очищает redo.

Без общего «богатого» базового класса: только датаклассы с execute/undo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.backend.model.circuit import Circuit, Connection
from src.backend.model.node import CircuitNode, Point
from src.backend.validation.validator import CircuitValidator
from src.common.errors import ValidationException


def _apply_state(t: Circuit, s: Circuit) -> None:
    t.id, t.title, t.nodes, t.connections = s.id, s.title, s.nodes, s.connections


@dataclass(slots=True)
class AddNodeCommand:
    circuit: Circuit
    node: CircuitNode

    def execute(self) -> None:
        self.circuit.add_node(self.node)

    def undo(self) -> None:
        self.circuit.remove_node(self.node.id)


@dataclass(slots=True)
class RemoveNodeCommand:
    circuit: Circuit
    node_id: str
    _saved: CircuitNode | None = None
    _conns: list[Connection] = field(default_factory=list)

    def execute(self) -> None:
        self._saved = self.circuit.get_node(self.node_id).clone()
        self._conns = [c for c in self.circuit.connections if c.from_node_id == self.node_id or c.to_node_id == self.node_id]
        self.circuit.remove_node(self.node_id)

    def undo(self) -> None:
        if self._saved is None:
            return
        self.circuit.add_node(self._saved)
        for c in self._conns:
            self.circuit.connect(c)


@dataclass(slots=True)
class ConnectNodesCommand:
    circuit: Circuit
    connection: Connection
    validator: CircuitValidator

    def execute(self) -> None:
        err = self.validator.validate_connection(self.circuit, self.connection)
        if err:
            raise ValidationException(err[0].message)
        self.circuit.connect(self.connection)

    def undo(self) -> None:
        self.circuit.disconnect(self.connection.id)


@dataclass(slots=True)
class DisconnectCommand:
    circuit: Circuit
    connection_id: str
    _backup: Connection | None = None

    def execute(self) -> None:
        self._backup = next((c for c in self.circuit.connections if c.id == self.connection_id), None)
        self.circuit.disconnect(self.connection_id)

    def undo(self) -> None:
        if self._backup is not None:
            self.circuit.connect(self._backup)


@dataclass(slots=True)
class MoveNodeCommand:
    circuit: Circuit
    node_id: str
    old: Point
    new: Point

    def execute(self) -> None:
        self.circuit.get_node(self.node_id).position = self.new

    def undo(self) -> None:
        self.circuit.get_node(self.node_id).position = self.old


@dataclass(slots=True)
class SimplifyCommand:
    circuit: Circuit
    after: Circuit | None = None
    before: Circuit | None = None

    def execute(self) -> None:
        if self.after is None:
            raise ValueError("after is None")
        self.before = self.circuit.clone()
        _apply_state(self.circuit, self.after)

    def undo(self) -> None:
        if self.before is not None:
            _apply_state(self.circuit, self.before)


@dataclass(slots=True)
class CommandHistory:
    undo: list[Any] = field(default_factory=list)
    redo: list[Any] = field(default_factory=list)

    def run(self, cmd: Any) -> None:
        cmd.execute()
        self.undo.append(cmd)
        self.redo.clear()

    def undo_last(self) -> None:
        if not self.undo:
            return
        c = self.undo.pop()
        c.undo()
        self.redo.append(c)

    def redo_next(self) -> None:
        if not self.redo:
            return
        c = self.redo.pop()
        c.execute()
        self.undo.append(c)

    def clear(self) -> None:
        self.undo.clear()
        self.redo.clear()
