import bcrypt
from database.db import get_connection


class UsuarioModel:
    def registrar(self, usuario):
        hashed = bcrypt.hashpw(usuario.password.encode(), bcrypt.gensalt()).decode()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (usuario.nombre, usuario.email, hashed)
        )
        conn.commit()
        conn.close()
        return True

    def validar_login(self, email, password):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            return user
        return None
