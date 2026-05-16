import flet as ft
from database.db import get_connection
from controllers.social import SocialController


def PerfilView(page: ft.Page, auth_controller):

    user = {}
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (page.user_id,))
        user = cursor.fetchone() or {}
        conn.close()
    except Exception:
        pass

    nombre = user.get("display_name") or user.get("username", "Usuario")
    inicial = nombre[0].upper()

    social = SocialController()
    seguidores = social.get_seguidores(page.user_id)
    siguiendo_list = social.get_siguiendo(page.user_id)

    s = dict(
        border_radius=10, filled=True,
        fill_color="#1a1a1a",
        border_color="#333333",
        focused_border_color="#ffffff",
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color="#888888"),
    )

    f_display  = ft.TextField(label="Nombre visible", value=user.get("display_name", ""), **s)
    f_bio      = ft.TextField(label="Bio", value=user.get("bio", ""), multiline=True, **s)
    f_artist   = ft.TextField(label="Artista favorito", value=user.get("favorite_artist", ""), **s)
    f_genre    = ft.TextField(label="Género favorito", value=user.get("favorite_genre", ""), **s)

    edit_mode = [False]

    content_col = ft.Column(spacing=10)

    def fila(icon, label, value):
        return ft.Container(
            padding=14,
            bgcolor="#1a1a1a",
            border_radius=10,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, color="#888888", size=18),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(label, size=11, color="#888888"),
                            ft.Text(str(value) if value else "—", size=14, color=ft.Colors.WHITE),
                        ],
                    ),
                ],
            ),
        )

    def render_view():
        content_col.controls = [
            fila(ft.Icons.PERSON_OUTLINE, "Username",         user.get("username")),
            fila(ft.Icons.BADGE_OUTLINED, "Nombre visible",   user.get("display_name")),
            fila(ft.Icons.INFO_OUTLINE,   "Bio",              user.get("bio")),
            fila(ft.Icons.MUSIC_NOTE,     "Artista favorito", user.get("favorite_artist")),
            fila(ft.Icons.QUEUE_MUSIC,    "Género favorito",  user.get("favorite_genre")),
            fila(ft.Icons.CALENDAR_TODAY, "Miembro desde",    str(user.get("created_at", ""))[:10]),
        ]

    def render_edit():
        content_col.controls = [
            f_display, f_bio, f_artist, f_genre,
            ft.ElevatedButton(
                "Guardar",
                width=300, height=44,
                bgcolor=ft.Colors.WHITE,
                color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=guardar,
            ),
        ]

    def guardar(e):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET display_name=%s, bio=%s, favorite_artist=%s, favorite_genre=%s WHERE id=%s",
                (f_display.value, f_bio.value, f_artist.value, f_genre.value, page.user_id)
            )
            conn.commit()
            conn.close()
            user["display_name"]    = f_display.value
            user["bio"]             = f_bio.value
            user["favorite_artist"] = f_artist.value
            user["favorite_genre"]  = f_genre.value
        except Exception:
            pass
        edit_mode[0] = False
        edit_btn.icon = ft.Icons.EDIT_OUTLINED
        render_view()
        page.update()

    def toggle_edit(e):
        edit_mode[0] = not edit_mode[0]
        if edit_mode[0]:
            edit_btn.icon = ft.Icons.CLOSE
            render_edit()
        else:
            edit_btn.icon = ft.Icons.EDIT_OUTLINED
            render_view()
        page.update()

    async def volver(e):
        await page.push_route("/home")

    edit_btn = ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, icon_color="#888888", on_click=toggle_edit)

    render_view()

    return ft.View(
        route="/perfil",
        bgcolor="#0a0a0a",
        padding=ft.Padding(left=20, right=20, top=20, bottom=20),
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="#888888", on_click=volver),
                    ft.Text("Perfil", size=16, color=ft.Colors.WHITE, font_family="Audiowide"),
                    ft.Row(spacing=0, controls=[
                        edit_btn,
                        ft.IconButton(icon=ft.Icons.LOGOUT, icon_color="#888888",
                            on_click=lambda _: (page.borrar_sesion(), page.run_task(page.push_route, "/"))[1]),
                    ]),
                ],
            ),
            ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
                controls=[
                    ft.Container(height=16),
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Container(
                                width=72, height=72,
                                border_radius=36,
                                bgcolor="#222222",
                                alignment=ft.Alignment(0, 0),
                                content=ft.Text(inicial, size=28, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
                            ),
                            ft.Text(nombre, size=20, color=ft.Colors.WHITE, weight="bold"),
                            ft.Text(user.get("email", ""), size=12, color="#888888"),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=24,
                                controls=[
                                    ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.Text(str(len(seguidores)), size=18, color=ft.Colors.WHITE, weight="bold"),
                                        ft.Text("seguidores", size=11, color="#888888"),
                                    ]),
                                    ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.Text(str(len(siguiendo_list)), size=18, color=ft.Colors.WHITE, weight="bold"),
                                        ft.Text("siguiendo", size=11, color="#888888"),
                                    ]),
                                ],
                            ),
                        ],
                    ),
                    ft.Container(height=20),
                    content_col,
                ],
            ),
        ],
    )
