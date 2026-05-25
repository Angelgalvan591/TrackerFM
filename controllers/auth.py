import bcrypt
import random
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from database.db import get_connection
from dotenv import load_dotenv

load_dotenv()


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
            load_dotenv(override=True)
            mail_user = (os.getenv("MAIL_USER") or "").strip()
            mail_pass = (os.getenv("MAIL_PASS") or "").strip().replace(" ", "")
            if not mail_user or "tu_correo" in mail_user or not mail_pass:
                print(f"[DEV] Codigo: {codigo}")
                return True, user["id"], f"DEV:{codigo}"
            msg = MIMEMultipart()
            msg["Subject"] = "Recuperar contrasena - TrackerFM"
            msg["From"]    = mail_user
            msg["To"]      = email
            msg.attach(MIMEText(
                f"Tu codigo de recuperacion de TrackerFM es:\n\n{codigo}\n\nExpira en 10 minutos.",
                "plain", "utf-8"
            ))
            # Usamos un contexto de tiempo de espera más corto y aseguramos el cierre
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
                s.login(mail_user, mail_pass)
                s.sendmail(mail_user, [email], msg.as_bytes())
            print(f"Correo enviado exitosamente a {email}")
            return True, user["id"], "Codigo enviado al correo"
        except Exception as e:
            print(f"Error SMTP: {e}")
            return False, None, str(e)

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
