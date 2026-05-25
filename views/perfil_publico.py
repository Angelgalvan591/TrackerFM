import flet as ft
from controllers.social import SocialController


def PerfilPublicoView(page: ft.Page):

    ctrl = SocialController()
    uid = getattr(page, "perfil_id", None)
    user = ctrl.get_usuario(uid) or {}

    nombre = user.get("display_name") or user.get("username", "Usuario")
    inicial = nombre[0].upper()

    siguiendo = [bool(ctrl.buscar_usuarios(user.get("username", ""), page.user_id) and
                 any(u["id"] == uid and u["siguiendo"] for u in ctrl.buscar_usuarios(user.get("username", ""), page.user_id)))]

    # verificar si ya sigue
    siguiendo = [False]
    for u in ctrl.buscar_usuarios(user.get("username", ""), page.user_id):
        if u["id"] == uid:
            siguiendo[0] = bool(u["siguiendo"])
            break

    seguidores = ctrl.get_seguidores(uid)
    siguiendo_count = ctrl.get_siguiendo(uid)

    btn_follow = ft.ElevatedButton(
        "Siguiendo" if siguiendo[0] else "Seguir",
        height=36,
        bgcolor="#333333" if siguiendo[0] else ft.Colors.WHITE,
        color="#888888" if siguiendo[0] else ft.Colors.BLACK,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
    )

    def toggle(e):
        if siguiendo[0]:
            ctrl.dejar_de_seguir(page.user_id, uid)
            siguiendo[0] = False
            btn_follow.text = "Seguir"
            btn_follow.bgcolor = ft.Colors.WHITE
            btn_follow.color = ft.Colors.BLACK
        else:
            ctrl.seguir(page.user_id, uid)
            siguiendo[0] = True
            btn_follow.text = "Siguiendo"
            btn_follow.bgcolor = "#333333"
            btn_follow.color = "#888888"
        page.update()

    btn_follow.on_click = toggle

    def fila(icon, label, value):
        return ft.Container(
            padding=14, bgcolor="#1a1a1a", border_radius=10,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, color="#888888", size=18),
                    ft.Column(spacing=2, controls=[
                        ft.Text(label, size=11, color="#888888"),
                        ft.Text(str(value) if value else "—", size=14, color=ft.Colors.WHITE),
                    ]),
                ],
            ),
        )

    return ft.View(
        route="/perfil_publico",
        bgcolor="#0a0a0a",
        padding=ft.Padding(left=20, right=20, top=20, bottom=20),
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="#888888",
                        on_click=lambda _: page.run_task(page.push_route, "/usuarios")),
                    ft.Text("Perfil", size=16, color=ft.Colors.WHITE, font_family="Audiowide"),
                    ft.Container(width=40),
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
                        spacing=8,
                        controls=[
                            ft.Container( # Avatar display
                                width=72, height=72, border_radius=36, bgcolor="#222222",
                                alignment=ft.Alignment(0, 0),
                                content=ft.Image(
                                    src=user.get("avatar_url"),
                                    width=72, height=72, border_radius=36, fit=ft.BoxFit.COVER
                                ) if user.get("avatar_url") else ft.Text(inicial, size=28, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
                            ),
                            
                            ft.Text(nombre, size=20, color=ft.Colors.WHITE, weight="bold"),
                            
                            ft.Text("@" + user.get("username", ""), size=12, color="#888888"),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=24,
                                controls=[
                                    ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.Text(str(len(seguidores)), size=18, color=ft.Colors.WHITE, weight="bold"),
                                        ft.Text("seguidores", size=11, color="#888888"),
                                    ]),
                                    ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.Text(str(len(siguiendo_count)), size=18, color=ft.Colors.WHITE, weight="bold"),
                                        ft.Text("siguiendo", size=11, color="#888888"),
                                    ]),
                                ],
                            ),
                            btn_follow,
                        ],
                    ),
                    ft.Container(height=20),
                    ft.Column(spacing=10, controls=[
                        fila(ft.Icons.INFO_OUTLINE,  "Bio",              user.get("bio")),
                        fila(ft.Icons.MUSIC_NOTE,    "Artista favorito", user.get("favorite_artist")),
                        fila(ft.Icons.QUEUE_MUSIC,   "Género favorito",  user.get("favorite_genre")),
                    ]),
                ],
            ),
        ],
    )
