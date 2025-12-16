import tkinter as tk
from tkinter import messagebox, scrolledtext
from database import Database
from preferences import Preferences


class KanbanBoard:
    def __init__(self, root):
        self.root = root
        self.root.title("Kanban Board")
        self.root.geometry("900x600")
        
        try:
            self.db = Database("kanban.db")
        except Exception as e:
            messagebox.showerror(
                "Database Error",
                f"Failed to initialize database:\n{str(e)}\n\nThe application will now close."
            )
            root.destroy()
            return
        
        self.dragged_task = None
        self.drag_widget = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self.prefs = Preferences()
        saved_prefs = self.prefs.load()
        
        self.search_var = tk.StringVar(value=saved_prefs.get("search_term", ""))
        self.sort_var = tk.StringVar(value=saved_prefs.get("sort_by", "created_desc"))
        
        self.setup_ui()
        self.refresh_all_columns()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        title_label = tk.Label(
            self.root, 
            text="Kanban Board", 
            font=("Arial", 20, "bold"),
            pady=10
        )
        title_label.pack()
        
        controls_frame = tk.Frame(self.root)
        controls_frame.pack(pady=10, padx=10, fill=tk.X)
        
        add_button = tk.Button(
            controls_frame,
            text="+ Add New Task",
            command=self.show_add_task_dialog,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        search_frame = tk.Frame(controls_frame)
        search_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(search_frame, text="Search:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 10), width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind('<Return>', lambda e: self.apply_filters())
        
        search_btn = tk.Button(
            search_frame,
            text="🔍",
            command=self.apply_filters,
            font=("Arial", 10),
            padx=5
        )
        search_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = tk.Button(
            search_frame,
            text="Clear",
            command=self.clear_filters,
            font=("Arial", 9),
            padx=5
        )
        clear_btn.pack(side=tk.LEFT)
        
        sort_frame = tk.Frame(controls_frame)
        sort_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(sort_frame, text="Sort by:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        sort_options = [
            ("Newest First", "created_desc"),
            ("Oldest First", "created_asc"),
            ("Recently Updated", "updated_desc"),
            ("Title A-Z", "title_asc"),
            ("Title Z-A", "title_desc")
        ]
        
        sort_menu = tk.OptionMenu(
            sort_frame,
            self.sort_var,
            *[opt[1] for opt in sort_options],
            command=lambda _: self.apply_filters()
        )
        sort_menu.config(font=("Arial", 9))
        sort_menu.pack(side=tk.LEFT)
        
        for text, value in sort_options:
            sort_menu['menu'].entryconfigure(sort_options.index((text, value)), label=text)
        
        columns_frame = tk.Frame(self.root)
        columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.columns = {}
        statuses = ["To Do", "In Progress", "Done"]
        colors = ["#ffebee", "#fff3e0", "#e8f5e9"]
        
        for i, (status, color) in enumerate(zip(statuses, colors)):
            column_frame = tk.Frame(columns_frame, bg=color, relief=tk.RAISED, borderwidth=2)
            column_frame.grid(row=0, column=i, sticky="nsew", padx=5)
            columns_frame.grid_columnconfigure(i, weight=1)
            columns_frame.grid_rowconfigure(0, weight=1)
            
            header = tk.Label(
                column_frame,
                text=status,
                font=("Arial", 14, "bold"),
                bg=color,
                pady=10
            )
            header.pack()
            
            canvas = tk.Canvas(column_frame, bg=color, highlightthickness=0)
            scrollbar = tk.Scrollbar(column_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=color)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e, c=canvas: c.configure(scrollregion=c.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            self.columns[status] = {
                'frame': scrollable_frame,
                'canvas': canvas,
                'color': color
            }
            
            scrollable_frame.bind("<ButtonRelease-1>", lambda e, s=status: self.on_drop(e, s))
            canvas.bind("<ButtonRelease-1>", lambda e, s=status: self.on_drop(e, s))
    
    def show_add_task_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Task")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Task Title:", font=("Arial", 10)).pack(pady=(10, 0))
        title_entry = tk.Entry(dialog, font=("Arial", 10), width=40)
        title_entry.pack(pady=5)
        title_entry.focus()
        
        tk.Label(dialog, text="Description:", font=("Arial", 10)).pack(pady=(10, 0))
        desc_text = tk.Text(dialog, font=("Arial", 10), width=40, height=5)
        desc_text.pack(pady=5)
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def save_task():
            title = title_entry.get().strip()
            description = desc_text.get("1.0", tk.END).strip()
            
            if not title:
                messagebox.showerror("Error", "Task title cannot be empty!")
                return
            
            try:
                self.db.create_task(title, description, "To Do")
                self.refresh_column("To Do")
                dialog.destroy()
                messagebox.showinfo("Success", "Task added successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create task: {str(e)}")
        
        tk.Button(
            button_frame,
            text="Save",
            command=save_task,
            bg="#4CAF50",
            fg="white",
            padx=20
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            padx=20
        ).pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: save_task())
    
    def refresh_column(self, status):
        try:
            frame = self.columns[status]['frame']
            for widget in frame.winfo_children():
                widget.destroy()
            
            search_term = self.search_var.get()
            sort_by = self.sort_var.get()
            
            all_tasks = self.db.get_all_tasks(search_term=search_term, sort_by=sort_by)
            tasks = [t for t in all_tasks if t['status'] == status]
            
            if not tasks and search_term:
                no_results_label = tk.Label(
                    frame,
                    text="No matching tasks",
                    font=("Arial", 9, "italic"),
                    fg="gray",
                    bg=self.columns[status]['color']
                )
                no_results_label.pack(pady=20)
            
            for task in tasks:
                self.create_task_widget(frame, task, self.columns[status]['color'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh column: {str(e)}")
    
    def create_task_widget(self, parent, task, bg_color):
        task_frame = tk.Frame(
            parent,
            bg="white",
            relief=tk.RAISED,
            borderwidth=1,
            cursor="hand2"
        )
        task_frame.pack(fill=tk.X, padx=5, pady=5)
        
        task_frame.bind("<Button-1>", lambda e: self.on_drag_start(e, task, task_frame))
        task_frame.bind("<B1-Motion>", self.on_drag_motion)
        task_frame.bind("<ButtonRelease-1>", self.on_drag_release)
        
        title_label = tk.Label(
            task_frame,
            text=task['title'],
            font=("Arial", 10, "bold"),
            bg="white",
            anchor="w",
            wraplength=250,
            cursor="hand2"
        )
        title_label.pack(fill=tk.X, padx=5, pady=(5, 0))
        title_label.bind("<Button-1>", lambda e: self.on_drag_start(e, task, task_frame))
        title_label.bind("<B1-Motion>", self.on_drag_motion)
        title_label.bind("<ButtonRelease-1>", self.on_drag_release)
        
        if task['description']:
            desc_label = tk.Label(
                task_frame,
                text=task['description'],
                font=("Arial", 9),
                bg="white",
                anchor="w",
                wraplength=250,
                fg="gray",
                cursor="hand2"
            )
            desc_label.pack(fill=tk.X, padx=5, pady=(2, 5))
            desc_label.bind("<Button-1>", lambda e: self.on_drag_start(e, task, task_frame))
            desc_label.bind("<B1-Motion>", self.on_drag_motion)
            desc_label.bind("<ButtonRelease-1>", self.on_drag_release)
        
        id_label = tk.Label(
            task_frame,
            text=f"ID: {task['id']}",
            font=("Arial", 8),
            bg="white",
            fg="lightgray",
            anchor="w",
            cursor="hand2"
        )
        id_label.pack(fill=tk.X, padx=5, pady=(0, 2))
        id_label.bind("<Button-1>", lambda e: self.on_drag_start(e, task, task_frame))
        id_label.bind("<B1-Motion>", self.on_drag_motion)
        id_label.bind("<ButtonRelease-1>", self.on_drag_release)
        
        buttons_frame = tk.Frame(task_frame, bg="white")
        buttons_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        edit_btn = tk.Button(
            buttons_frame,
            text="Edit",
            command=lambda: self.show_edit_task_dialog(task),
            font=("Arial", 8),
            bg="#2196F3",
            fg="white",
            padx=5,
            pady=2
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        delete_btn = tk.Button(
            buttons_frame,
            text="Delete",
            command=lambda: self.delete_task(task['id']),
            font=("Arial", 8),
            bg="#f44336",
            fg="white",
            padx=5,
            pady=2
        )
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        current_status = task['status']
        if current_status != "To Do":
            move_todo_btn = tk.Button(
                buttons_frame,
                text="← To Do",
                command=lambda: self.move_task(task['id'], "To Do"),
                font=("Arial", 8),
                bg="#ff9800",
                fg="white",
                padx=5,
                pady=2
            )
            move_todo_btn.pack(side=tk.LEFT, padx=2)
        
        if current_status != "In Progress":
            move_progress_btn = tk.Button(
                buttons_frame,
                text="↔ Progress",
                command=lambda: self.move_task(task['id'], "In Progress"),
                font=("Arial", 8),
                bg="#ff9800",
                fg="white",
                padx=5,
                pady=2
            )
            move_progress_btn.pack(side=tk.LEFT, padx=2)
        
        if current_status != "Done":
            move_done_btn = tk.Button(
                buttons_frame,
                text="Done →",
                command=lambda: self.move_task(task['id'], "Done"),
                font=("Arial", 8),
                bg="#ff9800",
                fg="white",
                padx=5,
                pady=2
            )
            move_done_btn.pack(side=tk.LEFT, padx=2)
    
    def refresh_all_columns(self):
        for status in ["To Do", "In Progress", "Done"]:
            self.refresh_column(status)
    
    def show_edit_task_dialog(self, task):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Task")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Task Title:", font=("Arial", 10)).pack(pady=(10, 0))
        title_entry = tk.Entry(dialog, font=("Arial", 10), width=40)
        title_entry.insert(0, task['title'])
        title_entry.pack(pady=5)
        title_entry.focus()
        
        tk.Label(dialog, text="Description:", font=("Arial", 10)).pack(pady=(10, 0))
        desc_text = tk.Text(dialog, font=("Arial", 10), width=40, height=5)
        desc_text.insert("1.0", task['description'])
        desc_text.pack(pady=5)
        
        tk.Label(dialog, text="Status:", font=("Arial", 10)).pack(pady=(10, 0))
        status_var = tk.StringVar(value=task['status'])
        status_frame = tk.Frame(dialog)
        status_frame.pack(pady=5)
        
        for status in ["To Do", "In Progress", "Done"]:
            tk.Radiobutton(
                status_frame,
                text=status,
                variable=status_var,
                value=status,
                font=("Arial", 9)
            ).pack(side=tk.LEFT, padx=5)
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def save_changes():
            title = title_entry.get().strip()
            description = desc_text.get("1.0", tk.END).strip()
            status = status_var.get()
            
            if not title:
                messagebox.showerror("Error", "Task title cannot be empty!")
                return
            
            try:
                self.db.update_task(task['id'], title=title, description=description, status=status)
                self.refresh_all_columns()
                dialog.destroy()
                messagebox.showinfo("Success", "Task updated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update task: {str(e)}")
        
        tk.Button(
            button_frame,
            text="Save Changes",
            command=save_changes,
            bg="#4CAF50",
            fg="white",
            padx=20
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            padx=20
        ).pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: save_changes())
    
    def delete_task(self, task_id):
        result = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this task?",
            icon='warning'
        )
        
        if result:
            try:
                self.db.delete_task(task_id)
                self.refresh_all_columns()
                messagebox.showinfo("Success", "Task deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete task: {str(e)}")
    
    def move_task(self, task_id, new_status):
        try:
            self.db.update_task(task_id, status=new_status)
            self.refresh_all_columns()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move task: {str(e)}")
    
    def on_drag_start(self, event, task, widget):
        self.dragged_task = task
        self.drag_widget = widget
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        widget.config(relief=tk.SUNKEN, bg="#e0e0e0")
    
    def on_drag_motion(self, event):
        if self.drag_widget and self.dragged_task:
            self.drag_widget.config(cursor="fleur")
    
    def on_drag_release(self, event):
        if not self.dragged_task or not self.drag_widget:
            return
        
        self.drag_widget.config(relief=tk.RAISED, bg="white", cursor="hand2")
        
        x = event.x_root
        y = event.y_root
        
        target_status = None
        for status, column_data in self.columns.items():
            frame = column_data['frame']
            canvas = column_data['canvas']
            
            frame_x = frame.winfo_rootx()
            frame_y = frame.winfo_rooty()
            frame_width = frame.winfo_width()
            frame_height = frame.winfo_height()
            
            canvas_x = canvas.winfo_rootx()
            canvas_y = canvas.winfo_rooty()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if (canvas_x <= x <= canvas_x + canvas_width and 
                canvas_y <= y <= canvas_y + canvas_height):
                target_status = status
                break
        
        if target_status and target_status != self.dragged_task['status']:
            try:
                self.db.update_task(self.dragged_task['id'], status=target_status)
                self.refresh_all_columns()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move task: {str(e)}")
        
        self.dragged_task = None
        self.drag_widget = None
    
    def on_drop(self, event, status):
        if self.dragged_task and self.dragged_task['status'] != status:
            try:
                self.db.update_task(self.dragged_task['id'], status=status)
                self.refresh_all_columns()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move task: {str(e)}")
        
        self.dragged_task = None
        self.drag_widget = None
    
    def apply_filters(self):
        try:
            self.refresh_all_columns()
            self.prefs.save(self.search_var.get(), self.sort_var.get())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filters: {str(e)}")
    
    def clear_filters(self):
        try:
            self.search_var.set("")
            self.sort_var.set("created_desc")
            self.refresh_all_columns()
            self.prefs.save("", "created_desc")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear filters: {str(e)}")
    
    def on_closing(self):
        self.db.close()
        self.root.destroy()


def main():
    try:
        root = tk.Tk()
        app = KanbanBoard(root)
        root.mainloop()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
