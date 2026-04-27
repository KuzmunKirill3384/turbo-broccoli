#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Единая точка входа: GUI на Tkinter (без установки пакета и без PYTHONPATH вручную).
Запуск из корня репозитория:  python run.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> None:
    from src.frontend.tkinter_app import run_tkinter_app

    run_tkinter_app()


if __name__ == "__main__":
    main()
