"""A small, dependency-free desktop to-do application."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

DATA_FILE = Path(__file__).with_name("tasks.json")

@dataclass
class Task:
    id: str
    title: str
    category: str
    due_date: str
    completed: bool = False

class TaskStore:
    def load(self) -> list[Task]:
        if not DATA_FILE.exists():
            return []
        try:
            return [Task(**item) for item in json.loads(DATA_FILE.read_text(encoding="utf-8"))]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    def save(self, tasks: list[Task]) -> None:
        DATA_FILE.write_text(json.dumps([asdict(task) for task in tasks], indent=2), encoding="utf-8")

class TodoApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TaskFlow — To-Do List")
        self.geometry("820x560")
        self.minsize(720, 480)
        self.configure(bg="#f6f8fc")
        self.store = TaskStore()
        self.tasks = self.store.load()
        self.filter_value = tk.StringVar(value="All")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=33, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e9efff")
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#3b5bdb")
        style.map("Accent.TButton", background=[("active", "#2f4ac0")])
        header = tk.Frame(self, bg="#3b5bdb", padx=28, pady=22)
        header.pack(fill="x")
        tk.Label(header, text="TaskFlow", font=("Segoe UI", 22, "bold"), fg="white", bg="#3b5bdb").pack(anchor="w")
        tk.Label(header, text="Keep your day clear, focused, and moving forward.", font=("Segoe UI", 10), fg="#dbe4ff", bg="#3b5bdb").pack(anchor="w")
        form = tk.Frame(self, bg="#f6f8fc", padx=28, pady=20)
        form.pack(fill="x")
        self.title_entry = ttk.Entry(form, width=34, font=("Segoe UI", 11))
        self.title_entry.grid(row=0, column=0, padx=(0, 8), ipady=5)
        self.title_entry.insert(0, "What needs doing?")
        self.title_entry.bind("<FocusIn>", self._clear_placeholder)
        self.category_box = ttk.Combobox(form, values=("Personal", "Work", "Study", "Health"), width=12, state="readonly")
        self.category_box.set("Personal")
        self.category_box.grid(row=0, column=1, padx=8, ipady=4)
        self.due_entry = ttk.Entry(form, width=14)
        self.due_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.due_entry.grid(row=0, column=2, padx=8, ipady=5)
        ttk.Button(form, text="Add task", style="Accent.TButton", command=self.add_task).grid(row=0, column=3, padx=(8, 0), ipady=4)
        controls = tk.Frame(self, bg="#f6f8fc", padx=28)
        controls.pack(fill="x", pady=(0, 10))
        for label in ("All", "Active", "Completed"):
            ttk.Radiobutton(controls, text=label, value=label, variable=self.filter_value, command=self.refresh).pack(side="left", padx=(0, 14))
        self.summary = tk.Label(controls, bg="#f6f8fc", fg="#5c677d", font=("Segoe UI", 10))
        self.summary.pack(side="right")
        table_frame = tk.Frame(self, bg="#f6f8fc", padx=28, pady=4)
        table_frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_frame, columns=("done", "task", "category", "due"), show="headings", selectmode="browse")
        for column, text, width in (("done", "Status", 100), ("task", "Task", 380), ("category", "Category", 140), ("due", "Due date", 120)):
            self.table.heading(column, text=text)
            self.table.column(column, width=width, anchor="center" if column != "task" else "w")
        self.table.pack(fill="both", expand=True)
        actions = tk.Frame(self, bg="#f6f8fc", padx=28, pady=18)
        actions.pack(fill="x")
        ttk.Button(actions, text="Mark complete / active", command=self.toggle_task).pack(side="left")
        ttk.Button(actions, text="Delete selected", command=self.delete_task).pack(side="left", padx=8)
        ttk.Button(actions, text="Clear completed", command=self.clear_completed).pack(side="left")

    def _clear_placeholder(self, _event: tk.Event) -> None:
        if self.title_entry.get() == "What needs doing?": self.title_entry.delete(0, "end")

    def add_task(self) -> None:
        title, due_date = self.title_entry.get().strip(), self.due_entry.get().strip()
        if not title or title == "What needs doing?":
            messagebox.showwarning("Task title needed", "Please enter a task before adding it.")
            return
        try: datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Date format", "Use YYYY-MM-DD for the due date.")
            return
        self.tasks.append(Task(str(uuid.uuid4()), title, self.category_box.get(), due_date))
        self.title_entry.delete(0, "end")
        self.persist_and_refresh()

    def selected_task(self) -> Task | None:
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo("Select a task", "Choose a task from the list first.")
            return None
        return next(task for task in self.tasks if task.id == selected[0])

    def toggle_task(self) -> None:
        task = self.selected_task()
        if task:
            task.completed = not task.completed
            self.persist_and_refresh()

    def delete_task(self) -> None:
        task = self.selected_task()
        if task and messagebox.askyesno("Delete task", f"Delete '{task.title}'?"):
            self.tasks.remove(task)
            self.persist_and_refresh()

    def clear_completed(self) -> None:
        if any(task.completed for task in self.tasks):
            self.tasks = [task for task in self.tasks if not task.completed]
            self.persist_and_refresh()

    def persist_and_refresh(self) -> None:
        self.store.save(self.tasks)
        self.refresh()

    def refresh(self) -> None:
        self.table.delete(*self.table.get_children())
        visible = self.tasks
        if self.filter_value.get() == "Active": visible = [task for task in self.tasks if not task.completed]
        elif self.filter_value.get() == "Completed": visible = [task for task in self.tasks if task.completed]
        for task in sorted(visible, key=lambda item: (item.completed, item.due_date)):
            self.table.insert("", "end", iid=task.id, values=("Done" if task.completed else "Active", task.title, task.category, task.due_date))
        self.summary.config(text=f"{sum(task.completed for task in self.tasks)} of {len(self.tasks)} tasks completed")

if __name__ == "__main__":
    TodoApp().mainloop()
