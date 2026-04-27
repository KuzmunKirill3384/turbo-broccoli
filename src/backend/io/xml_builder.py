# -*- coding: utf-8 -*-
"""
Загрузка и сохранение схемы в файл XML. Сейчас методы не реализованы — это каркас.

План реализации:
- build_from_file: прочитать файл, разобрать дерево тегов, собрать Circuit
- save_to_file: взять Circuit, сформировать строку XML, записать на диск

parse_meta / parse_nodes / parse_connections / parse_layout разбиты, чтобы
в одном методе не путать метаданные и геометрию.

CircuitMetadata — заголовок файла (название, автор), не путать с id схемы внутри Circuit.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.backend.model.circuit import Circuit, Connection
from src.backend.model.node import Point


@dataclass(slots=True)
class CircuitMetadata:
    title: str = ""
    description: str = ""
    author: str = ""
    version: str = "1.0"


class CircuitXmlBuilder:
    def build_from_file(self, path: str) -> Circuit:
        raise NotImplementedError

    def build_from_string(self, xml: str) -> Circuit:
        raise NotImplementedError

    def serialize(self, circuit: Circuit) -> str:
        raise NotImplementedError

    def save_to_file(self, circuit: Circuit, path: str) -> None:
        raise NotImplementedError

    def parse_meta(self, root: object) -> CircuitMetadata:
        raise NotImplementedError

    def parse_nodes(self, root: object) -> list[object]:
        raise NotImplementedError

    def parse_connections(self, root: object) -> list[Connection]:
        raise NotImplementedError

    def parse_layout(self, root: object) -> dict[str, Point]:
        raise NotImplementedError
