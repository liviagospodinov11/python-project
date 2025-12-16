import json
import os


class Preferences:
    def __init__(self, prefs_file: str = "kanban_preferences.json"):
        self.prefs_file = prefs_file
        self.default_prefs = {
            "search_term": "",
            "sort_by": "created_desc"
        }
    
    def load(self) -> dict:
        try:
            if os.path.exists(self.prefs_file):
                with open(self.prefs_file, 'r') as f:
                    prefs = json.load(f)
                    return {**self.default_prefs, **prefs}
            return self.default_prefs.copy()
        except Exception as e:
            print(f"Warning: Could not load preferences: {e}")
            return self.default_prefs.copy()
    
    def save(self, search_term: str, sort_by: str):
        try:
            prefs = {
                "search_term": search_term,
                "sort_by": sort_by
            }
            with open(self.prefs_file, 'w') as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save preferences: {e}")
    
    def clear(self):
        try:
            if os.path.exists(self.prefs_file):
                os.remove(self.prefs_file)
        except Exception as e:
            print(f"Warning: Could not clear preferences: {e}")
