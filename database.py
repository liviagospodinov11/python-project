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
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to connect to database: {str(e)}")
    
    def create_tables(self):
        try:
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
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to create tables: {str(e)}")
    
    def create_task(self, title: str, description: str = "", status: str = "To Do") -> Optional[int]:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        
        if status not in ["To Do", "In Progress", "Done"]:
            status = "To Do"
        
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO tasks (title, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (title.strip(), description.strip(), status, now, now))
            
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Failed to create task: {str(e)}")
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to retrieve task: {str(e)}")
    
    def get_all_tasks(self, search_term: str = None, sort_by: str = "created_desc") -> List[Dict]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM tasks"
        params = []
        
        if search_term and search_term.strip():
            query += " WHERE title LIKE ? OR description LIKE ?"
            search_pattern = f"%{search_term.strip()}%"
            params = [search_pattern, search_pattern]
        
        sort_mapping = {
            "created_desc": "created_at DESC",
            "created_asc": "created_at ASC",
            "updated_desc": "updated_at DESC",
            "updated_asc": "updated_at ASC",
            "title_asc": "title ASC",
            "title_desc": "title DESC"
        }
        
        order_clause = sort_mapping.get(sort_by, "created_at DESC")
        query += f" ORDER BY {order_clause}"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def update_task(self, task_id: int, title: str = None, description: str = None, 
                   status: str = None) -> bool:
        try:
            existing = self.get_task(task_id)
            if not existing:
                return False
            
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
            
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [task_id]
            
            cursor = self.conn.cursor()
            cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
            self.conn.commit()
            
            return cursor.rowcount > 0
        except ValueError:
            raise
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Failed to update task: {str(e)}")
    
    def delete_task(self, task_id: int) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Failed to delete task: {str(e)}")
    
    def close(self):
        if self.conn:
            self.conn.close()
