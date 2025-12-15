
import sqlite3
from typing import Optional, List, Dict
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "kanban.db"):
        
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def create_tables(self):
        
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'To Do',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self.conn.commit()
    
    def create_task(self, title: str, description: str = "", status: str = "To Do") -> Optional[int]:
       
        # Validation
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        
        if status not in ["To Do", "In Progress", "Done"]:
            status = "To Do"
        
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO tasks (title, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (title.strip(), description.strip(), status, now, now))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_tasks(self) -> List[Dict]:
       
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_task(self, task_id: int, title: str = None, description: str = None, 
                   status: str = None) -> bool:
       
        # Get existing task
        existing = self.get_task(task_id)
        if not existing:
            return False
        
        # Prepare updates
        updates = {}
        if title is not None:
            if not title.strip():
                raise ValueError("Task title cannot be empty")
            updates['title'] = title.strip()
        
        if description is not None:
            updates['description'] = description.strip()
        
        if status is not None:
            if status not in ["To Do", "In Progress", "Done"]:
                raise ValueError("Invalid status")
            updates['status'] = status
        
        if not updates:
            return True
        
        updates['updated_at'] = datetime.now().isoformat()
        
        # Build query
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [task_id]
        
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        
        return cursor.rowcount > 0
    
    def delete_task(self, task_id: int) -> bool:
       
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close(self):
       
        if self.conn:
            self.conn.close()
