# -*- coding: utf-8 -*-
"""
Схема = словарь узлов (ключ id) + список рёбер Connection.

Связь Connection: выход (from_node_id, from_pin) ведёт во вход (to_node_id, to_pin).
Один вход — не больше одного провода (см. валидатор).

find_predecessors / find_successors — кто подаёт сигнал на этот узел и куда
идёт с этого (нужно для анализа зависимостей и обхода при вычислении).

clone() — глубокая копия целиком (модуль copy.deepcopy), используется перед
проверкой «а не появится ли цикл», и в командах отката.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.backend.model.node import CircuitNode

if TYPE_CHECKING:
    from src.backend.model.node import NodeVisitor


@dataclass(slots=True)
class Connection:
    id: str
    from_node_id: str
    from_pin: int
    to_node_id: str
    to_pin: int


@dataclass(slots=True)
class Circuit:
    id: str
    title: str
    nodes: dict[str, CircuitNode] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)

    def add_node(self, node: CircuitNode) -> None:
        self.nodes[node.id] = node

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        self.connections = [
            c for c in self.connections if c.from_node_id != node_id and c.to_node_id != node_id
        ]

    def get_node(self, node_id: str) -> CircuitNode:
        return self.nodes[node_id]

    def connect(self, connection: Connection) -> None:
        self.connections.append(connection)

    def disconnect(self, connection_id: str) -> None:
        self.connections = [c for c in self.connections if c.id != connection_id]

    def find_predecessors(self, node_id: str) -> list[CircuitNode]:
        prev_ids = [c.from_node_id for c in self.connections if c.to_node_id == node_id]
        return [self.nodes[i] for i in prev_ids if i in self.nodes]

    def find_successors(self, node_id: str) -> list[CircuitNode]:
        next_ids = [c.to_node_id for c in self.connections if c.from_node_id == node_id]
        return [self.nodes[i] for i in next_ids if i in self.nodes]

    def accept(self, visitor: NodeVisitor) -> list[Any]:
        return [node.accept(visitor) for node in self.nodes.values()]

    def clone(self) -> Circuit:
        return deepcopy(self)
