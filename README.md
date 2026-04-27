# Редактор булевых схем

Редактор булевых схем (AND, OR, XOR, EQUAL): таблица истинности, упрощение, полином, XML.

## Возможности

- схема, связи, проверка, отмена/повтор;
- таблица истинности (сервис дописать);
- упрощение при заданных входах (сервис дописать);
- полином по узлу (сервис дописать);
- зависимости узлов (сервис дописать);
- настройки вида (каркас);
- загрузка/сохранение XML (каркас в CircuitXmlBuilder).

## Стек

- Python 3.10+
- Tkinter — демо-окно (`src/frontend/tkinter_app.py`, stdlib)
- PyQt6 — целевой GUI (в репо пока каркас `MainWindow`)
- pytest
- XML через стандартную библиотеку или lxml

## Паттерны (коротко)

- Composite: схема из узлов и связей
- Visitor: accept на узлах
- Command: undo/redo
- Factory: фабрика команд
- Facade: CircuitEditorFacade для UI
- Сервисы: таблица, упрощение, полином, зависимости (отдельные классы)

## Структура

- src/common — enum, ошибки
- src/backend — model/ (узлы, схема; NodeVisitor в node.py), commands.py (команды + история), facade.py (API для UI), stubs.py (таблица истинности и пр. пока заглушки), validation/, io/
- src/frontend — окно, холст, панели
- tests — тесты

Комментарии в коде в каталоге src.

## Демо (Tkinter)

Окно на стандартном Tkinter, без PyQt. **Проще всего** — из корня репозитория:

```bash
python run.py
```

Иначе (нужен `PYTHONPATH`):

```bash
PYTHONPATH=. python3 -m src.frontend.tkinter_app
```

Либо из кода: `from src.frontend.app.main import run_tkinter_demo` и `run_tkinter_demo()`.

## Запуск каркаса (без окна)

```python
from src.frontend.app.main import create_application
w = create_application()
# w.facade — схема и команды
```

## Команда

- Боос Дмитрий Алексеевич
- Климаш Иван Витальевич
- Кузьмин Кирилл Владимирович

## Лицензия

MIT, файл LICENSE.

## Сдача

- код с комментариями;
- демо;
- отчёт (архитектура, алгоритмы, формат файла, библиотеки, задачи).
