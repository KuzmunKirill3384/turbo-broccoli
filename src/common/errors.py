# -*- coding: utf-8 -*-
"""
Свои исключения, чтобы в UI отделить «наша ошибка домена» от чужих.

ValidationException — не прошли проверку связи / цикла.
SerializationException — кривой XML или запись на диск.
"""


class CircuitEditorError(Exception):
    pass


class ValidationException(CircuitEditorError):
    pass


class SerializationException(CircuitEditorError):
    pass
