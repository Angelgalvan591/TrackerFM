import bcrypt
import random
import smtplib
import os
from email.message import EmailMessage
from datetime import datetime, timedelta
from src.database.db import get_connection
from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)


class AuthController:

    def registrar(self, username, email, password):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            email = email.strip()
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
            email = email.strip()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            conn.close()
            if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
                return None, "Credenciales incorrectas"
            return user, "Login correcto"
        except Exception as e:
            return None, str(e)

    def _generar_codigo(self):
        return str(random.randint(100000, 999999))

    def _guardar_codigo(self, email, codigo):
        conn = get_connection()
        cursor = conn.cursor()
        expira = datetime.now() + timedelta(minutes=10)
        cursor.execute("DELETE FROM password_resets WHERE email = %s", (email,))
        cursor.execute(
            "INSERT INTO password_resets (email, codigo, expira_at) VALUES (%s, %s, %s)",
            (email, codigo, expira)
        )
        conn.commit()
        conn.close()

    def solicitar_recuperacion(self, email):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            conn.close()
            if not user:
                return False, None, "No existe una cuenta con ese correo"
            codigo = self._generar_codigo()
            self._guardar_codigo(email, codigo)
            mail_user = (os.getenv("MAIL_USER") or "").strip()
            mail_pass = (os.getenv("MAIL_PASS") or "").strip().replace(" ", "")
            if not mail_user or "tu_correo" in mail_user or not mail_pass:
                print(f"[DEV] Codigo: {codigo}")
                return True, user["id"], f"DEV:{codigo}"

            msg = EmailMessage()
            msg["Subject"] = "Recuperar contrasena - TrackerFM"
            msg["From"] = mail_user
            msg["To"] = email
            msg.set_content(
                f"Hola,\n\n"
                f"Recibimos una solicitud para restablecer la contrasena de tu cuenta en TrackerFM, "
                f"tu diario musical personal.\n\n"
                f"Tu codigo de verificacion es:\n\n"
                f"    {codigo}\n\n"
                f"Este codigo expira en 10 minutos. Si no solicitaste esto, ignora este mensaje y tu cuenta seguira segura.\n\n"
                f"-- El equipo de TrackerFM",
                charset="utf-8"
            )

            import sys
            if sys.platform == "win32":
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15, local_hostname="localhost") as s:
                s.login(mail_user, mail_pass)
                s.send_message(msg)

            print("Correo enviado exitosamente")
            return True, user["id"], "Codigo enviado al correo"
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error SMTP: {e}".encode("ascii", errors="replace").decode())
            return False, None, str(e).encode("ascii", errors="replace").decode()

    def verificar_token(self, user_id, token):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                return False, "Usuario no encontrado"
            return self.verificar_codigo(row["email"], token)
        except Exception as e:
            return False, str(e)

    def verificar_codigo(self, email, codigo):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM password_resets WHERE email = %s AND codigo = %s",
                (email, codigo)
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return False, "Codigo incorrecto"
            if datetime.now() > row["expira_at"]:
                return False, "El codigo expiro"
            return True, "Codigo valido"
        except Exception as e:
            return False, str(e)

    def cambiar_password_por_id(self, user_id, nueva_password):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                return False, "Usuario no encontrado"
            return self.cambiar_password(row["email"], nueva_password)
        except Exception as e:
            return False, str(e)

    def cambiar_password(self, email, nueva_password):
        try:
            hashed = bcrypt.hashpw(nueva_password.encode(), bcrypt.gensalt()).decode()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed, email))
            cursor.execute("DELETE FROM password_resets WHERE email = %s", (email,))
            conn.commit()
            conn.close()
            return True, "Contrasena actualizada"
        except Exception as e:
            return False, str(e)
