import bcrypt
from TrackerFM.src.database.db import get_connection


def guardar_track_review(user_id, track_id, track_title, artist_name, cover_url, rating, texto, album_id=None, album_title=None, artist_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if artist_id:
        cursor.execute(
            "INSERT INTO artists (id, name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=VALUES(name)",
            (str(artist_id), artist_name or "")
        )

    if album_id:
        cursor.execute(
            """INSERT INTO albums (id, artist_id, title, cover_url)
               VALUES (%s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE cover_url=COALESCE(VALUES(cover_url), cover_url),
               artist_id=COALESCE(VALUES(artist_id), artist_id)""",
            (str(album_id), str(artist_id) if artist_id else None, album_title or "", cover_url or "")
        )

    cursor.execute(
        """INSERT INTO tracks (id, album_id, title, preview_url)
           VALUES (%s, %s, %s, NULL)
           ON DUPLICATE KEY UPDATE album_id=COALESCE(VALUES(album_id), album_id), title=VALUES(title)""",
        (str(track_id), str(album_id) if album_id else None, track_title)
    )

    cursor.execute(
        """
        INSERT INTO track_reviews (user_id, track_id, rating, review_text)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE rating=%s, review_text=%s
        """,
        (user_id, str(track_id), rating, texto, rating, texto)
    )
    conn.commit()
    conn.close()


def get_track_reviews(track_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT tr.rating, tr.review_text, tr.created_at,
               u.username, u.display_name, u.avatar_url
        FROM track_reviews tr
        JOIN users u ON tr.user_id = u.id
        WHERE tr.track_id = %s
        ORDER BY tr.created_at DESC
        """,
        (str(track_id),)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_user_track_review(user_id, track_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT rating, review_text FROM track_reviews WHERE user_id=%s AND track_id=%s",
        (user_id, str(track_id))
    )
    row = cursor.fetchone()
    conn.close()
    return row


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
