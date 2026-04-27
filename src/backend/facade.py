# -*- coding: utf-8 -*-
"""
Коротко: весь доступ UI к схеме. Поля: circuit, history, валидатор, заглушки сервисов, XML.
Создание команды — прямо здесь, без фабрики. После load / новый документ: history.clear().
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.backend.commands import (
    AddNodeCommand,
    CommandHistory,
    ConnectNodesCommand,
    DisconnectCommand,
    MoveNodeCommand,
    RemoveNodeCommand,
    SimplifyCommand,
)
from src.backend.io.xml_builder import CircuitXmlBuilder
from src.backend.model.circuit import Circuit, Connection
from src.backend.model.elements import InputNode, LogicGate, OutputNode
from src.backend.model.node import CircuitNode, Point
from src.backend.stubs import (
    DependencyService,
    PolynomialService,
    SimplificationReport,
    SimplificationService,
    TruthTable,
    TruthTableService,
)
from src.backend.validation.validator import CircuitValidator
from src.common.enums import NodeType

_GATES = frozenset((NodeType.AND, NodeType.OR, NodeType.XOR, NodeType.EQUAL))


@dataclass(slots=True)
class CircuitEditorFacade:
    circuit: Circuit = field(default_factory=lambda: Circuit(id="circuit", title="Untitled"))
    history: CommandHistory = field(default_factory=CommandHistory)
    validator: CircuitValidator = field(default_factory=CircuitValidator)
    truth_table_service: TruthTableService = field(default_factory=TruthTableService)
    simplification_service: SimplificationService = field(default_factory=SimplificationService)
    polynomial_service: PolynomialService = field(default_factory=PolynomialService)
    dependency_service: DependencyService = field(default_factory=DependencyService)
    xml_builder: CircuitXmlBuilder = field(default_factory=CircuitXmlBuilder)

    def create_empty_circuit(self, title: str) -> None:
        self.circuit = Circuit(id="circuit", title=title)
        self.history.clear()

    def add_node(self, node_type: NodeType, position: Point, label: str = "") -> str:
        n = self._node(node_type, position, label)
        self.history.run(AddNodeCommand(self.circuit, n))
        return n.id

    def remove_node(self, node_id: str) -> None:
        self.history.run(RemoveNodeCommand(self.circuit, node_id))

    def connect(self, a: str, a_pin: int, b: str, b_pin: int) -> None:
        c = Connection(id=f"{a}:{a_pin}->{b}:{b_pin}", from_node_id=a, from_pin=a_pin, to_node_id=b, to_pin=b_pin)
        self.history.run(ConnectNodesCommand(self.circuit, c, self.validator))

    def disconnect(self, connection_id: str) -> None:
        self.history.run(DisconnectCommand(self.circuit, connection_id))

    def move_node(self, node_id: str, new_pos: Point) -> None:
        n = self.circuit.get_node(node_id)
        old = Point(n.position.x, n.position.y)
        self.history.run(MoveNodeCommand(self.circuit, node_id, old, new_pos))

    def undo(self) -> None:
        self.history.undo_last()

    def redo(self) -> None:
        self.history.redo_next()

    def get_truth_table(self) -> TruthTable:
        return self.truth_table_service.build_for_circuit(self.circuit)

    def get_truth_table_for_node(self, node_id: str) -> TruthTable:
        return self.truth_table_service.build_for_node(self.circuit, node_id)

    def get_dependencies(self, node_id: str) -> list[str]:
        return self.dependency_service.get_affecting_nodes(self.circuit, node_id)

    def simplify(self, fixed_inputs: dict[str, bool]) -> SimplificationReport:
        after = self.simplification_service.simplify(self.circuit, fixed_inputs)
        rep = self.simplification_service.estimate_removal(self.circuit, fixed_inputs)
        self.history.run(SimplifyCommand(self.circuit, after=after))
        return rep

    def get_polynomial(self, node_id: str) -> str:
        return self.polynomial_service.build_for_node(self.circuit, node_id)

    def load(self, path: str) -> None:
        self.circuit = self.xml_builder.build_from_file(path)
        self.history.clear()

    def save(self, path: str) -> None:
        self.xml_builder.save_to_file(self.circuit, path)

    def _node(self, t: NodeType, pos: Point, label: str) -> CircuitNode:
        k = t.value.lower()
        n = 1 + sum(1 for x in self.circuit.nodes.values() if x.node_type == t)
        nid, lab = f"{k}{n}", (label or f"{k}{n}".upper())
        if t == NodeType.INPUT:
            return InputNode(node_id=nid, label=lab, position=pos)
        if t == NodeType.OUTPUT:
            return OutputNode(node_id=nid, label=lab, position=pos)
        if t in _GATES:
            return LogicGate(node_id=nid, label=lab, position=pos, node_type=t)
        raise ValueError(t)
