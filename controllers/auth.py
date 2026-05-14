import bcrypt
from database.db import get_connection


class AuthController:
    def registrar(self, username, email, password):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return False, "El correo ya está registrado"
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed)
            )
            conn.commit()
            conn.close()
            return True, "Usuario creado correctamente"
        except Exception as e:
            return False, str(e)

    def login(self, email, password):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            conn.close()
            if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
                return None, "Credenciales incorrectas"
            return user, "Login correcto"
        except Exception as e:
            return None, str(e)
