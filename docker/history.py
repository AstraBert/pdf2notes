import pgsql
from typing import List, Dict, Any

connection = pgsql.Connection(address=("postgres",5432),user="localhost", password="admin", database="postgres")
connection.execute("CREATE TABLE IF NOT EXISTS memory (username TEXT, content TEXT, role TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")

class ChatHistory:
    def __init__(self, connection: pgsql.Connection):
        self.connection = connection
    def update(self, username: str, content: str, role: str) -> bool:
        try:
            message = content.replace("'","''")
            self.connection.execute(f"INSERT INTO memory (username, content, role) VALUES ('{username}', '{message}', '{role}')")
            return True
        except Exception as e:
            return False
    def get(self, username: str) -> List[Dict[str, Any]] | bool:
        try:
            first_records = self.connection(f"SELECT * FROM MEMORY WHERE username = '{username}' ORDER BY created_at DESC LIMIT 10;")
            memories = []
            for m in first_records:
                memories.append(m)
            if len(memories) == 0:
                return memories
            else:
                chat_messages = [{"content": m.content, "role": m.role} for m in memories]
                return chat_messages
        except Exception as e:
            return False
    