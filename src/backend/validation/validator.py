# -*- coding: utf-8 -*-
"""
Проверки перед тем, как считать схему «корректной»:

1) Нет ориентированного цикла (иначе не определён порядок вычисления в
   комбинационной схеме). Проверка: обход в глубину, если вернулись в вершину,
   которая ещё в стеке рекурсии — цикл.

2) На каждый входной пин не больше одного провода; индекс пина в допустимых границах.

3) При добавлении новой связи: копируем схему, добавляем ребро, снова ищем цикл.
   Так мы ловим циклы, которые появились только из-за этого ребра.

ValidationError — просто структура: код (для if в коде), текст (для пользователя),
при желании список затронутых id.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.backend.model.circuit import Circuit, Connection


@dataclass(slots=True)
class ValidationError:
    code: str
    message: str
    related_node_ids: list[str] = field(default_factory=list)


class CircuitValidator:
    def validate_circuit(self, circuit: Circuit) -> list[ValidationError]:
        err: list[ValidationError] = []
        err.extend(self.check_cycles(circuit))
        err.extend(self.check_pin_limits(circuit))
        return err

    def validate_connection(self, circuit: Circuit, connection: Connection) -> list[ValidationError]:
        err: list[ValidationError] = []
        err.extend(self.check_node_existence(circuit, connection))
        if err:
            return err

        if connection.from_node_id == connection.to_node_id:
            err.append(
                ValidationError(
                    code="SELF_LOOP",
                    message="A node cannot be connected to itself.",
                    related_node_ids=[connection.from_node_id],
                )
            )

        src = circuit.get_node(connection.from_node_id)
        tgt = circuit.get_node(connection.to_node_id)

        if not (0 <= connection.from_pin < len(src.output_pins)):
            err.append(
                ValidationError(
                    code="INVALID_SOURCE_PIN",
                    message="Source output pin index is out of range.",
                    related_node_ids=[connection.from_node_id],
                )
            )

        if not tgt.can_accept_input(connection.to_pin):
            err.append(
                ValidationError(
                    code="INVALID_TARGET_PIN",
                    message="Target input pin index is out of range.",
                    related_node_ids=[connection.to_node_id],
                )
            )

        if any(
            e.to_node_id == connection.to_node_id and e.to_pin == connection.to_pin for e in circuit.connections
        ):
            err.append(
                ValidationError(
                    code="TARGET_PIN_OCCUPIED",
                    message="The target input pin already has a connection.",
                    related_node_ids=[connection.to_node_id],
                )
            )

        if err:
            return err

        tmp = circuit.clone()
        tmp.connect(connection)
        err.extend(self.check_cycles(tmp))
        return err

    def check_cycles(self, circuit: Circuit) -> list[ValidationError]:
        graph: dict[str, list[str]] = {nid: [] for nid in circuit.nodes}
        for c in circuit.connections:
            graph.setdefault(c.from_node_id, []).append(c.to_node_id)

        seen: set[str] = set()
        stack: set[str] = set()
        bad: set[str] = set()

        def dfs(n: str) -> None:
            if n in stack:
                bad.add(n)
                return
            if n in seen:
                return
            stack.add(n)
            for v in graph.get(n, []):
                dfs(v)
                if v in bad:
                    bad.add(n)
            stack.remove(n)
            seen.add(n)

        for nid in circuit.nodes:
            dfs(nid)

        if not bad:
            return []
        return [
            ValidationError(
                code="CYCLE_DETECTED",
                message="The circuit contains a cycle.",
                related_node_ids=sorted(bad),
            )
        ]

    def check_pin_limits(self, circuit: Circuit) -> list[ValidationError]:
        err: list[ValidationError] = []
        count: dict[tuple[str, int], int] = {}
        for c in circuit.connections:
            key = (c.to_node_id, c.to_pin)
            count[key] = count.get(key, 0) + 1

        for (nid, pin), n in count.items():
            if n > 1:
                err.append(
                    ValidationError(
                        code="MULTIPLE_INPUT_CONNECTIONS",
                        message="An input pin has more than one incoming connection.",
                        related_node_ids=[nid],
                    )
                )
            if nid not in circuit.nodes:
                continue
            node = circuit.get_node(nid)
            if not node.can_accept_input(pin):
                err.append(
                    ValidationError(
                        code="INPUT_PIN_OUT_OF_RANGE",
                        message="A connection references an input pin outside the node bounds.",
                        related_node_ids=[nid],
                    )
                )
        return err

    def check_node_existence(self, circuit: Circuit, connection: Connection) -> list[ValidationError]:
        err: list[ValidationError] = []
        if connection.from_node_id not in circuit.nodes:
            err.append(
                ValidationError(
                    code="SOURCE_NODE_NOT_FOUND",
                    message="The source node does not exist.",
                    related_node_ids=[connection.from_node_id],
                )
            )
        if connection.to_node_id not in circuit.nodes:
            err.append(
                ValidationError(
                    code="TARGET_NODE_NOT_FOUND",
                    message="The target node does not exist.",
                    related_node_ids=[connection.to_node_id],
                )
            )
        return err
