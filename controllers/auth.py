import bcrypt
import random
import smtplib
import os
from email.mime.text import MIMEText
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

    def enviar_codigo_correo(self, email):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if not cursor.fetchone():
                conn.close()
                return False, "No existe una cuenta con ese correo"
            conn.close()
            codigo = self._generar_codigo()
            self._guardar_codigo(email, codigo)
            load_dotenv(override=True)
            mail_user = (os.getenv("MAIL_USER") or "").strip()
            mail_pass = (os.getenv("MAIL_PASS") or "").strip().replace(" ", "")
            if not mail_user or "tu_correo" in mail_user or not mail_pass:
                return True, f"DEV:{codigo}"
            msg = MIMEText(
                f"Tu codigo de recuperacion de TrackerFM es:\n\n{codigo}\n\nExpira en 10 minutos.",
                "plain", "utf-8"
            )
            msg["Subject"] = "Recuperar contrasena - TrackerFM"
            msg["From"]    = mail_user
            msg["To"]      = email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
                s.login(mail_user, mail_pass)
                s.send_message(msg)
            return True, "Codigo enviado al correo"
        except Exception as e:
            return False, str(e)

    def enviar_codigo_whatsapp(self, telefono, email):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if not cursor.fetchone():
                conn.close()
                return False, "No existe una cuenta con ese correo"
            conn.close()
            codigo = self._generar_codigo()
            self._guardar_codigo(email, codigo)
            sid   = os.getenv("TWILIO_SID", "")
            token = os.getenv("TWILIO_TOKEN", "")
            frm   = os.getenv("TWILIO_FROM", "")
            if sid and token and frm:
                from twilio.rest import Client
                client = Client(sid, token)
                # normalizar número
                numero = telefono if telefono.startswith("+") else f"+{telefono}"
                client.messages.create(
                    body=f"Tu código de recuperación TrackerFM es: {codigo}. Expira en 10 min.",
                    from_=frm,
                    to=f"whatsapp:{numero}",
                )
                return True, "Código enviado por WhatsApp"
            else:
                return True, f"DEV:{codigo}"
        except Exception as e:
            return False, f"Error WhatsApp: {str(e)}"

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
                return False, "Código incorrecto"
            if datetime.now() > row["expira_at"]:
                return False, "El código expiró"
            return True, "Código válido"
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
            return True, "Contraseña actualizada"
        except Exception as e:
            return False, str(e)
