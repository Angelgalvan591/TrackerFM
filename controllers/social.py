from database.db import get_connection


class SocialController:

    def get_usuario(self, user_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def buscar_usuarios(self, query, user_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.username, u.display_name, u.avatar_url,
                   EXISTS(SELECT 1 FROM followers WHERE follower_id=%s AND following_id=u.id) AS siguiendo
            FROM users u
            WHERE u.id != %s AND (u.username LIKE %s OR u.display_name LIKE %s)
            LIMIT 20
        """, (user_id, user_id, f"%{query}%", f"%{query}%"))
        result = cursor.fetchall()
        conn.close()
        return result

    def seguir(self, follower_id, following_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT IGNORE INTO followers (follower_id, following_id) VALUES (%s, %s)",
            (follower_id, following_id)
        )
        conn.commit()
        conn.close()

    def dejar_de_seguir(self, follower_id, following_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM followers WHERE follower_id=%s AND following_id=%s",
            (follower_id, following_id)
        )
        conn.commit()
        conn.close()

    def get_seguidores(self, user_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.username, u.display_name
            FROM followers f JOIN users u ON u.id = f.follower_id
            WHERE f.following_id = %s
        """, (user_id,))
        result = cursor.fetchall()
        conn.close()
        return result

    def get_siguiendo(self, user_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.username, u.display_name
            FROM followers f JOIN users u ON u.id = f.following_id
            WHERE f.follower_id = %s
        """, (user_id,))
        result = cursor.fetchall()
        conn.close()
        return result
