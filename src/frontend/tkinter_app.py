# -*- coding: utf-8 -*-
"""
Демо на Tkinter: холст с перетаскиванием «блоков», линии связей, режим «провод»
(два клика: от кого к кому, выход[0] → вход[0]). Данные — через фасад.
"""
from __future__ import annotations

import platform
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

from src.backend.facade import CircuitEditorFacade
from src.backend.model.elements import LogicGate
from src.backend.model.node import Point
from src.common.enums import NodeType
from src.common.errors import ValidationException

# Геометрия узла на холсте (левый верх = position в модели)
NODE_W = 100
NODE_H = 44
GRID = 20


def run_tkinter_app() -> None:
    app = _CircuitCanvasApp()
    app.mainloop()


def _tag(nid: str) -> str:
    return f"n_{nid}"


def _ui_body_font(root: tk.Tk) -> tuple[str, int]:
    f = tkfont.nametofont("TkDefaultFont", root)
    # +1 к размеру для читаемости, контраст с фоном — через тёмные foreground в стилях
    return (f.cget("family"), max(10, (f.cget("size") or 10) + 1))


def _ui_title_font(root: tk.Tk) -> tuple[str, int, str]:
    f = _ui_body_font(root)
    return (f[0], f[1] + 4, "bold")


def _canvas_label_font() -> tuple[str, int, str]:
    """Повышенный кегль и вес — хороший контраст на пастельных заливках узлов."""
    if platform.system() == "Darwin":
        return ("SF Pro Text", 11, "bold")
    if platform.system() == "Windows":
        return ("Segoe UI", 10, "bold")
    return ("sans-serif", 11, "bold")


def _apply_theme(root: tk.Tk) -> None:
    s = ttk.Style(root)
    if sys.platform == "darwin":
        pass  # оставляем нативный «aqua»
    elif "clam" in s.theme_names():
        s.theme_use("clam")
    s.configure("Header.TFrame", background="#1e2a3a")
    s.configure("HeaderTitle.TLabel", background="#1e2a3a", foreground="#ffffff", font=_ui_title_font(root))
    s.configure("HeaderSub.TLabel", background="#1e2a3a", foreground="#e4eaf2", font=(*_ui_body_font(root),))
    s.configure("Toolbar.TLabelframe", padding=(10, 6))
    s.configure(
        "Toolbar.TLabelframe.Label",
        font=(*_ui_body_font(root), "bold"),
        foreground="#ffffff",
    )
    s.configure("Pad.TButton", padding=(8, 5), font=(*_ui_body_font(root),))
    s.configure("Accent.TButton", padding=(10, 6), font=(*_ui_body_font(root), "bold"))
    s.configure("Status.TFrame", background="#1f2937")
    s.configure(
        "Status.TLabel",
        background="#1f2937",
        foreground="#ffffff",
        font=(*_ui_body_font(root), "bold"),
    )
    s.configure("Hint.TLabel", foreground="#ffffff", font=(*_ui_body_font(root),))
    s.configure("TRadiobutton", foreground="#ffffff", font=(*_ui_body_font(root),))
    # Таблица расчёта: всегда чёрный текст для читаемости.
    s.configure(
        "Treeview",
        foreground="#000000",
        background="#ffffff",
        fieldbackground="#ffffff",
        font=(*_ui_body_font(root),),
    )
    s.configure(
        "Treeview.Heading",
        foreground="#000000",
        background="#d1d5db",
        font=(*_ui_body_font(root), "bold"),
    )


class _CircuitCanvasApp:
    def __init__(self) -> None:
        self._facade = CircuitEditorFacade()
        self._facade.create_empty_circuit("Демо")
        self._i = 0
        self._root = tk.Tk()
        _apply_theme(self._root)
        self._root.title("Редактор булевых схем")
        self._root.minsize(720, 480)
        self._root.configure(bg="#1f2937")

        self._mode = tk.StringVar(master=self._root, value="move")
        self._status = tk.StringVar(master=self._root, value="")
        self._wire_from: str | None = None
        self._drag_id: str | None = None
        self._drag_last: tuple[int, int] | None = None
        self._line_to_conn_id: dict[int, str] = {}

        # ——— Шапка ———
        head = ttk.Frame(self._root, style="Header.TFrame", padding=(14, 10))
        head.pack(fill=tk.X)
        ttk.Label(head, text="Редактор схем", style="HeaderTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(
            head,
            text="Собирайте схему на поле: добавляйте элементы, перетаскивайте, в режиме «Провод» соединяйте "
            "выход (справа) со входом (слева) двумя кликами. ПКМ в режиме провода — отмена выбора.",
            style="HeaderSub.TLabel",
            wraplength=900,
        ).pack(anchor=tk.W, pady=(4, 0))

        # ——— Панель инструментов ———
        bar = ttk.Frame(self._root, padding=(10, 6, 10, 2))
        bar.pack(fill=tk.X)
        bar.columnconfigure(0, weight=0)
        bar.columnconfigure(1, weight=0)
        bar.columnconfigure(2, weight=0)
        bar.columnconfigure(3, weight=1)

        lf_add = ttk.LabelFrame(bar, text="  Новый элемент  ", style="Toolbar.TLabelframe", padding=(6, 4))
        lf_add.grid(row=0, column=0, padx=(0, 6), sticky=tk.NW)

        add_items = [
            ("Вход", NodeType.INPUT),
            ("AND", NodeType.AND),
            ("OR", NodeType.OR),
            ("XOR", NodeType.XOR),
            ("Выход", NodeType.OUTPUT),
        ]
        for idx, (text, nt) in enumerate(add_items):
            row, col = divmod(idx, 3)
            ttk.Button(lf_add, text=text, style="Pad.TButton", width=6, command=lambda t=nt: self._add(t)).grid(
                row=row, column=col, padx=2, pady=1, sticky=tk.W
            )

        lf_mode = ttk.LabelFrame(bar, text="  Режим  ", style="Toolbar.TLabelframe", padding=(6, 4))
        lf_mode.grid(row=0, column=1, padx=(0, 6), sticky=tk.NW)
        ttk.Radiobutton(
            lf_mode, text="Перемещение", variable=self._mode, value="move", command=self._on_mode_change
        ).grid(row=0, column=0, padx=2, sticky=tk.W)
        ttk.Radiobutton(
            lf_mode, text="Провод (2 клика)", variable=self._mode, value="wire", command=self._on_mode_change
        ).grid(row=0, column=1, padx=8, sticky=tk.W)
        ttk.Label(lf_mode, text="источник -> приёмник", style="Hint.TLabel").grid(
            row=1, column=0, columnspan=2, padx=2, pady=(1, 0), sticky=tk.W
        )

        lf_act = ttk.LabelFrame(bar, text="  Действия  ", style="Toolbar.TLabelframe", padding=(6, 4))
        lf_act.grid(row=0, column=2, padx=0, sticky=tk.NW)
        ttk.Button(lf_act, text="Шаг назад", style="Pad.TButton", width=11, command=self._undo).grid(
            row=0, column=0, padx=2, pady=1, sticky=tk.W
        )
        ttk.Button(lf_act, text="Очистить", style="Pad.TButton", width=11, command=self._reset).grid(
            row=0, column=1, padx=2, pady=1, sticky=tk.W
        )
        ttk.Button(
            lf_act, text="Рассчитать", style="Pad.TButton", width=11, command=self._open_calc_dialog
        ).grid(row=1, column=0, padx=2, pady=1, sticky=tk.W)
        ttk.Button(
            lf_act, text="Демо-цепочка", style="Accent.TButton", width=11, command=self._demo_chain
        ).grid(row=1, column=1, padx=2, pady=1, sticky=tk.W)

        # ——— Статус ———
        st = ttk.Frame(self._root, style="Status.TFrame", padding=(14, 8))
        st.pack(fill=tk.X)
        ttk.Label(st, textvariable=self._status, style="Status.TLabel", wraplength=1000).pack(anchor=tk.W)

        # ——— Легенда + холст ———
        area = ttk.Frame(self._root, padding=(12, 4, 12, 12))
        area.pack(fill=tk.BOTH, expand=True)

        leg = tk.Frame(area, bg="#1f2937", pady=6, padx=10)
        leg.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(leg, text="Обозначения:", style="Hint.TLabel").pack(side=tk.LEFT, padx=(0, 8))

        def _leg_dot(parent: tk.Frame, text: str, col: str) -> None:
            f = tk.Frame(parent, bg=parent.cget("bg") or "#1f2937")
            f.pack(side=tk.LEFT, padx=(0, 14))
            c = tk.Canvas(f, width=14, height=14, highlightthickness=0, bg=parent.cget("bg") or "#1f2937")
            c.create_oval(2, 2, 12, 12, fill=col, outline="#333", width=1)
            c.pack(side=tk.LEFT, padx=(0, 4))
            ttk.Label(f, text=text, style="Hint.TLabel").pack(side=tk.LEFT)

        _leg_dot(leg, "вход (слева)", "#15803d")
        _leg_dot(leg, "выход (справа)", "#b91c1c")
        _leg_dot(leg, "направление связи — стрелка", "#3d4f6b")

        canvas_frame = ttk.Frame(area)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        self._canvas = tk.Canvas(
            canvas_frame,
            bg="#f4f6f9",
            highlightthickness=1,
            highlightbackground="#c5cdd8",
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_motion)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<Button-3>", self._on_right_click)
        self._canvas.bind("<Double-Button-1>", self._on_double_click)
        self._redraw_after_id: str | None = None
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._on_mode_change()
        self._redraw()

    def _on_canvas_configure(self, e: tk.Event) -> None:
        if e.widget is not self._canvas or self._drag_id is not None:
            return
        if self._redraw_after_id is not None:
            self._root.after_cancel(self._redraw_after_id)
        self._redraw_after_id = self._root.after(120, self._deferred_grid_redraw)

    def _deferred_grid_redraw(self) -> None:
        self._redraw_after_id = None
        if self._drag_id is None:
            self._redraw()

    def mainloop(self) -> None:
        self._root.mainloop()

    def _on_mode_change(self) -> None:
        self._wire_from = None
        if self._mode.get() == "wire":
            self._set_status("Режим «Провод»: клик по блоку-источнику, затем по получателю. Правая кнопка мыши — сброс выбора.")
        else:
            self._set_status("Режим «Перемещение»: перетаскивайте блоки по полю. Для соединения переключитесь в «Провод».")
        self._redraw()

    def _on_right_click(self, _e: tk.Event) -> None:  # noqa: ARG002
        if self._wire_from is not None:
            self._wire_from = None
            self._set_status("Выбор конца провода сброшен. Начните снова, если нужно.")
            self._redraw()

    def _on_double_click(self, e: tk.Event) -> None:
        """Удаляет узел/провод двойным кликом.

        Приоритет: если попали по блоку — удаляем узел (и его связи),
        иначе пробуем удалить ближайший провод.
        """
        hit_node = self._hit_node_id(e.x, e.y)
        if hit_node is not None:
            self._facade.remove_node(hit_node)
            self._wire_from = None
            self._set_status(f"Узел '{hit_node}' удалён двойным кликом.")
            self._redraw()
            return

        items = self._canvas.find_overlapping(e.x - 3, e.y - 3, e.x + 3, e.y + 3)
        line_id: int | None = None
        for it in reversed(items):
            if self._canvas.type(it) == "line" and it in self._line_to_conn_id:
                line_id = int(it)
                break
        if line_id is None:
            closest = self._canvas.find_closest(e.x, e.y)
            if closest and self._canvas.type(closest[0]) == "line" and closest[0] in self._line_to_conn_id:
                line_id = int(closest[0])
        if line_id is None:
            return
        conn_id = self._line_to_conn_id.get(line_id)
        if not conn_id:
            return
        self._facade.disconnect(conn_id)
        self._set_status("Провод удалён двойным кликом.")
        self._redraw()

    def _set_status(self, s: str) -> None:
        self._status.set(s)

    def _hit_node_id(self, x: int, y: int) -> str | None:
        for it in reversed(self._canvas.find_overlapping(x - 3, y - 3, x + 3, y + 3)):
            for t in self._canvas.gettags(it):
                if t.startswith("n_"):
                    return t[2:]
        items2 = self._canvas.find_closest(x, y)
        if not items2:
            return None
        for t in self._canvas.gettags(items2[0]):
            if t.startswith("n_"):
                return t[2:]
        return None

    def _on_press(self, e: tk.Event) -> None:
        nid = self._hit_node_id(e.x, e.y)
        if self._mode.get() == "wire":
            if nid is None:
                return
            if self._wire_from is None:
                self._wire_from = nid
                self._set_status(f"Соединить от {self._wire_from!r} — кликните по второму блоку (приёмнику).")
                self._redraw()
                return
            if self._wire_from == nid:
                return
            a, b = self._wire_from, nid
            self._wire_from = None
            try:
                self._facade.connect(a, 0, b, 0)
            except ValidationException as err:
                messagebox.showerror("Невозможно соединить", str(err))
            self._set_status("Связь обновлена. При ошибке см. всплывающее окно.")
            self._redraw()
            return
        if nid is not None:
            self._drag_id = nid
            self._drag_last = (e.x, e.y)

    def _on_motion(self, e: tk.Event) -> None:
        if self._mode.get() != "move" or self._drag_id is None or self._drag_last is None:
            return
        dx = e.x - self._drag_last[0]
        dy = e.y - self._drag_last[1]
        self._drag_last = (e.x, e.y)
        self._canvas.move(_tag(self._drag_id), dx, dy)
        self._canvas.delete("conn")
        for c in self._facade.circuit.connections:
            self._draw_line(c.from_node_id, c.to_node_id, c.id)
        for nid in self._facade.circuit.nodes:
            self._canvas.tag_raise(_tag(nid))

    def _on_release(self, _e: tk.Event) -> None:
        if self._mode.get() != "move" or self._drag_id is None:
            return
        nid = self._drag_id
        self._drag_id = None
        self._drag_last = None
        rect = self._rect_from_canvas(nid)
        if not rect:
            return
        x1, y1 = int(rect[0]), int(rect[1])
        try:
            n = self._facade.circuit.get_node(nid)
        except KeyError:
            return
        if (x1, y1) != (n.position.x, n.position.y):
            self._facade.move_node(nid, Point(x1, y1))
        self._redraw()

    def _rect_from_canvas(self, nid: str) -> tuple[float, float, float, float] | None:
        for it in self._canvas.find_withtag(_tag(nid)):
            if self._canvas.type(it) == "rectangle":
                c = self._canvas.coords(it)
                return (c[0], c[1], c[2], c[3])
        return None

    def _add(self, t: NodeType) -> None:
        self._i += 1
        self._root.update_idletasks()
        w = max(400, int(self._canvas.winfo_width() or 600))
        h = max(300, int(self._canvas.winfo_height() or 400))
        cx = 60 + (self._i * 19) % (w - NODE_W - 40)
        cy = 60 + (self._i * 13) % (h - NODE_H - 40)
        try:
            self._facade.add_node(t, Point(cx, cy))
        except ValidationException as err:
            messagebox.showerror("Ошибка", str(err))
            return
        self._set_status(f"Добавлен элемент. Всего узлов на схеме: {len(self._facade.circuit.nodes)}.")
        self._redraw()

    def _undo(self) -> None:
        self._facade.undo()
        self._wire_from = None
        self._set_status("Откат: последнее действие отменено.")
        self._redraw()

    def _reset(self) -> None:
        self._facade.create_empty_circuit("Демо")
        self._i = 0
        self._wire_from = None
        self._set_status("Схема очищена. Добавьте элементы с панели «Новый элемент».")
        self._redraw()

    def _demo_chain(self) -> None:
        self._reset()
        try:
            p, h = 80, 160
            i1 = self._facade.add_node(NodeType.INPUT, Point(p, h - 50))
            i2 = self._facade.add_node(NodeType.INPUT, Point(p, h + 10))
            i3 = self._facade.add_node(NodeType.INPUT, Point(p, h + 70))
            g1 = self._facade.add_node(NodeType.AND, Point(p + 170, h - 20))
            g2 = self._facade.add_node(NodeType.XOR, Point(p + 340, h + 10))
            oid = self._facade.add_node(NodeType.OUTPUT, Point(p + 510, h + 10))
            # Полностью заполняем входы вентилей, чтобы расчёт работал сразу.
            self._facade.connect(i1, 0, g1, 0)
            self._facade.connect(i2, 0, g1, 1)
            self._facade.connect(g1, 0, g2, 0)
            self._facade.connect(i3, 0, g2, 1)
            self._facade.connect(g2, 0, oid, 0)
        except ValidationException as err:
            messagebox.showerror("Валидация", str(err))
        self._set_status(
            "Показана демо-цепочка: IN1,IN2 -> AND; AND,IN3 -> XOR -> OUT. "
            "Двойной клик по проводу удаляет его."
        )
        self._redraw()

    def _open_calc_dialog(self) -> None:
        """Небольшое окно: выбрать значения входов и посчитать значения выходов."""
        input_ids = sorted(
            nid for nid, node in self._facade.circuit.nodes.items() if node.node_type == NodeType.INPUT
        )
        output_ids = sorted(
            nid for nid, node in self._facade.circuit.nodes.items() if node.node_type == NodeType.OUTPUT
        )
        if not input_ids:
            messagebox.showinfo("Расчёт", "На схеме нет входных узлов (INPUT).")
            return
        if not output_ids:
            messagebox.showinfo("Расчёт", "На схеме нет выходных узлов (OUTPUT).")
            return

        dlg = tk.Toplevel(self._root)
        dlg.title("Расчёт схемы")
        dlg.geometry("760x420")
        dlg.transient(self._root)
        dlg.grab_set()
        dlg.configure(bg="#1f2937")
        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Задайте значения входов (0/1):", style="Hint.TLabel").grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8)
        )
        vars_by_id: dict[str, tk.IntVar] = {}
        for idx, nid in enumerate(input_ids, start=1):
            vars_by_id[nid] = tk.IntVar(master=dlg, value=0)
            ttk.Label(frm, text=nid, style="Hint.TLabel").grid(row=idx, column=0, sticky=tk.W, padx=(0, 10))
            ttk.Radiobutton(frm, text="0", value=0, variable=vars_by_id[nid]).grid(row=idx, column=1, sticky=tk.W)
            ttk.Radiobutton(frm, text="1", value=1, variable=vars_by_id[nid]).grid(row=idx, column=2, sticky=tk.W)

        table_cols = ["#"] + input_ids + output_ids
        table = ttk.Treeview(frm, columns=table_cols, show="headings", height=9)
        for col in table_cols:
            table.heading(col, text=col)
            w = 56 if col != "#" else 40
            table.column(col, width=w, minwidth=w, anchor=tk.CENTER, stretch=False)
        table.grid(row=1, column=3, rowspan=max(3, len(input_ids) + 1), sticky=tk.NSEW, padx=(16, 0))
        scroll = ttk.Scrollbar(frm, orient=tk.VERTICAL, command=table.yview)
        table.configure(yscrollcommand=scroll.set)
        scroll.grid(row=1, column=4, rowspan=max(3, len(input_ids) + 1), sticky=tk.NS)
        frm.columnconfigure(3, weight=1)
        frm.rowconfigure(1, weight=1)
        table.tag_configure("odd", background="#f3f4f6")
        table.tag_configure("even", background="#e5e7eb")

        def _insert_row(values: list[int]) -> None:
            row_no = len(table.get_children()) + 1
            tag = "odd" if row_no % 2 else "even"
            table.insert("", tk.END, values=[row_no, *values], tags=(tag,))

        result_text = tk.StringVar(master=dlg, value="")
        ttk.Label(frm, textvariable=result_text, style="Hint.TLabel").grid(
            row=len(input_ids) + 1, column=0, columnspan=5, sticky=tk.W, pady=(10, 4)
        )

        def _do_calc() -> None:
            inputs = {nid: bool(v.get()) for nid, v in vars_by_id.items()}
            try:
                out = self._evaluate_outputs(inputs)
            except ValueError as err:
                messagebox.showerror("Ошибка расчёта", str(err), parent=dlg)
                return
            row_values = [1 if inputs[nid] else 0 for nid in input_ids] + [1 if out[nid] else 0 for nid in output_ids]
            _insert_row(row_values)
            rendered = ", ".join(f"{nid}={1 if val else 0}" for nid, val in sorted(out.items()))
            result_text.set(f"Выходы: {rendered}")
            self._set_status(f"Расчёт выполнен: {rendered}")

        def _fill_full_table() -> None:
            table.delete(*table.get_children())
            n = len(input_ids)
            for mask in range(1 << n):
                inputs = {input_ids[i]: bool((mask >> (n - 1 - i)) & 1) for i in range(n)}
                try:
                    out = self._evaluate_outputs(inputs)
                except ValueError as err:
                    messagebox.showerror("Ошибка расчёта", str(err), parent=dlg)
                    return
                row_values = [1 if inputs[nid] else 0 for nid in input_ids] + [1 if out[nid] else 0 for nid in output_ids]
                _insert_row(row_values)
            result_text.set(f"Построена таблица истинности: {1 << n} строк.")
            self._set_status("Таблица истинности построена.")

        btns = ttk.Frame(frm)
        btns.grid(row=len(input_ids) + 2, column=0, columnspan=5, sticky=tk.EW, pady=(8, 0))
        ttk.Button(btns, text="Посчитать", style="Accent.TButton", command=_do_calc).pack(side=tk.LEFT)
        ttk.Button(btns, text="Таблица всех наборов", style="Pad.TButton", command=_fill_full_table).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(btns, text="Очистить таблицу", style="Pad.TButton", command=lambda: table.delete(*table.get_children())).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(btns, text="Закрыть", style="Pad.TButton", command=dlg.destroy).pack(side=tk.LEFT, padx=(8, 0))

    def _evaluate_outputs(self, input_values: dict[str, bool]) -> dict[str, bool]:
        """Вычисляет текущую схему рекурсивно (без таблицы истинности и без stubs-сервисов)."""
        circuit = self._facade.circuit
        incoming_by_to: dict[str, list] = {}
        for c in circuit.connections:
            incoming_by_to.setdefault(c.to_node_id, []).append(c)
        for lst in incoming_by_to.values():
            lst.sort(key=lambda x: x.to_pin)

        cache: dict[str, bool] = {}

        def resolve(node_id: str) -> bool:
            if node_id in cache:
                return cache[node_id]
            node = circuit.get_node(node_id)
            if node.node_type == NodeType.INPUT:
                val = bool(input_values.get(node_id, False))
                cache[node_id] = val
                return val
            incoming = incoming_by_to.get(node_id, [])
            if node.node_type == NodeType.OUTPUT:
                src = next((c for c in incoming if c.to_pin == 0), None)
                if src is None:
                    raise ValueError(f"У выхода '{node_id}' не подключён входной пин.")
                val = resolve(src.from_node_id)
                cache[node_id] = val
                return val
            if isinstance(node, LogicGate):
                values: list[bool] = []
                for pin_index in range(len(node.input_pins)):
                    src = next((c for c in incoming if c.to_pin == pin_index), None)
                    if src is None:
                        raise ValueError(f"У узла '{node_id}' не заполнен вход pin {pin_index}.")
                    values.append(resolve(src.from_node_id))
                val = node.evaluate(values)
                cache[node_id] = val
                return val
            raise ValueError(f"Неподдерживаемый тип узла '{node.node_type}'.")

        outputs: dict[str, bool] = {}
        for nid, node in circuit.nodes.items():
            if node.node_type == NodeType.OUTPUT:
                outputs[nid] = resolve(nid)
        return outputs

    def _node_style(self, nt: NodeType) -> tuple[str, str]:
        """(fill, outline) — спокойная палитра в одном тоне."""
        return {
            NodeType.INPUT: ("#1e3a5f", "#93c5fd"),
            NodeType.OUTPUT: ("#14532d", "#86efac"),
            NodeType.AND: ("#78350f", "#fcd34d"),
            NodeType.OR: ("#4c1d95", "#c4b5fd"),
            NodeType.XOR: ("#7c2d12", "#fdba74"),
            NodeType.EQUAL: ("#334155", "#cbd5e1"),
        }.get(nt, ("#374151", "#d1d5db"))

    def _draw_grid(self) -> None:
        w = int(self._canvas.winfo_width() or 800)
        h = int(self._canvas.winfo_height() or 600)
        for x in range(0, w + 1, GRID):
            self._canvas.create_line(x, 0, x, h, fill="#e2e6ed", width=1, tags="grid")
        for y in range(0, h + 1, GRID):
            self._canvas.create_line(0, y, w, y, fill="#e2e6ed", width=1, tags="grid")

    def _redraw(self) -> None:
        self._canvas.delete("all")
        self._line_to_conn_id.clear()
        self._draw_grid()
        for c in self._facade.circuit.connections:
            self._draw_line(c.from_node_id, c.to_node_id, c.id)
        fl = _canvas_label_font()
        for nid, node in self._facade.circuit.nodes.items():
            x, y = int(node.position.x), int(node.position.y)
            is_pick = self._mode.get() == "wire" and self._wire_from == nid
            fill, odefault = self._node_style(node.node_type)
            outline = "#b91c1c" if is_pick else odefault
            wline = 2 if is_pick else 1
            tag = _tag(nid)
            sh = 2
            self._canvas.create_rectangle(
                x + sh, y + sh, x + NODE_W + sh, y + NODE_H + sh, fill="#c5ccd6", outline="", tags=tag
            )
            self._canvas.create_rectangle(
                x, y, x + NODE_W, y + NODE_H, fill=fill, outline=outline, width=wline, tags=(tag, "block")
            )
            self._canvas.create_text(
                x + NODE_W // 2,
                y + NODE_H // 2,
                text=f"{node.node_type.value}\n{nid}",
                font=fl,
                fill="#ffffff",
                tags=(tag, "block"),
            )
            pr = 4
            self._canvas.create_oval(
                x - pr,
                y + NODE_H // 2 - pr,
                x + pr,
                y + NODE_H // 2 + pr,
                fill="#15803d",
                outline="#14532d",
                width=1,
                tags=tag,
            )
            self._canvas.create_oval(
                x + NODE_W - pr,
                y + NODE_H // 2 - pr,
                x + NODE_W + pr,
                y + NODE_H // 2 + pr,
                fill="#b91c1c",
                outline="#7f1d1d",
                width=1,
                tags=tag,
            )
        self._canvas.tag_lower("grid")
        if self._facade.circuit.connections or self._facade.circuit.nodes:
            self._canvas.configure(scrollregion=self._canvas.bbox("all") or (0, 0, 1, 1))
        else:
            self._canvas.configure(scrollregion=(0, 0, 1, 1))

    def _pin_out_xy(self, nid: str) -> tuple[int, int] | None:
        if self._drag_id == nid:
            r = self._rect_from_canvas(nid)
            if r:
                return (int(r[2]), (int(r[1]) + int(r[3])) // 2)
            return None
        try:
            n = self._facade.circuit.get_node(nid)
        except KeyError:
            return None
        return (int(n.position.x) + NODE_W, int(n.position.y) + NODE_H // 2)

    def _pin_in_xy(self, nid: str) -> tuple[int, int] | None:
        if self._drag_id == nid:
            r = self._rect_from_canvas(nid)
            if r:
                return (int(r[0]), (int(r[1]) + int(r[3])) // 2)
            return None
        try:
            n = self._facade.circuit.get_node(nid)
        except KeyError:
            return None
        return (int(n.position.x), int(n.position.y) + NODE_H // 2)

    def _draw_line(self, from_id: str, to_id: str, conn_id: str | None = None) -> None:
        a, b = self._pin_out_xy(from_id), self._pin_in_xy(to_id)
        if not a or not b:
            return
        line_id = self._canvas.create_line(
            a[0],
            a[1],
            b[0],
            b[1],
            width=2,
            fill="#000000",
            tags="conn",
            arrow=tk.LAST,
            arrowshape=(10, 12, 4),
        )
        if conn_id is not None:
            self._line_to_conn_id[int(line_id)] = conn_id


if __name__ == "__main__":
    run_tkinter_app()
