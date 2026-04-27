# -*- coding: utf-8 -*-
"""
Тип узла на схеме. str + Enum, чтобы и сравнивать с строкой, и перечислять в цикле.

INPUT/OUTPUT — края схемы. AND, OR, XOR, EQUAL — вентили (у нас один класс LogicGate,
различается этим полем).
"""
from enum import Enum


class NodeType(str, Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    EQUAL = "EQUAL"
