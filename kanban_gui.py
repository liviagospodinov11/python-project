
import tkinter as tk
from tkinter import messagebox, scrolledtext
from database import Database


class KanbanBoard:
    def __init__(self, root):
        self.root = root
        self.root.title("Kanban Board")
        self.root.geometry("900x600")
        
        
        self.db = Database("kanban.db")
        
        
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
        
        
        add_button = tk.Button(
            self.root,
            text="+ Add New Task",
            command=self.show_add_task_dialog,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5
        )
        add_button.pack(pady=10)
        
        
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
    
    def show_add_task_dialog(self):
        """Show dialog to add a new task"""
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
        """Refresh tasks in a specific column"""
        
        frame = self.columns[status]['frame']
        for widget in frame.winfo_children():
            widget.destroy()
        
        
        all_tasks = self.db.get_all_tasks()
        tasks = [t for t in all_tasks if t['status'] == status]
        
        
        for task in tasks:
            self.create_task_widget(frame, task, self.columns[status]['color'])
    
    def create_task_widget(self, parent, task, bg_color):
        
        task_frame = tk.Frame(
            parent,
            bg="white",
            relief=tk.RAISED,
            borderwidth=1
        )
        task_frame.pack(fill=tk.X, padx=5, pady=5)
        
        
        title_label = tk.Label(
            task_frame,
            text=task['title'],
            font=("Arial", 10, "bold"),
            bg="white",
            anchor="w",
            wraplength=250
        )
        title_label.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        
        if task['description']:
            desc_label = tk.Label(
                task_frame,
                text=task['description'],
                font=("Arial", 9),
                bg="white",
                anchor="w",
                wraplength=250,
                fg="gray"
            )
            desc_label.pack(fill=tk.X, padx=5, pady=(2, 5))
        
        
        id_label = tk.Label(
            task_frame,
            text=f"ID: {task['id']}",
            font=("Arial", 8),
            bg="white",
            fg="lightgray",
            anchor="w"
        )
        id_label.pack(fill=tk.X, padx=5, pady=(0, 5))
    
    def refresh_all_columns(self):
        """Refresh all columns"""
        for status in ["To Do", "In Progress", "Done"]:
            self.refresh_column(status)
    
    def on_closing(self):
        """Handle window close event"""
        self.db.close()
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = KanbanBoard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
