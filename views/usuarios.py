import flet as ft
from controllers.social import SocialController


def UsuariosView(page: ft.Page):

    ctrl = SocialController()
    resultados = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

    barra = ft.TextField(
        hint_text="Buscar usuarios...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=30,
        filled=True,
        fill_color="#1a1a1a",
        border_color="#333333",
        focused_border_color="#ffffff",
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        hint_style=ft.TextStyle(color="#888888"),
        expand=True,
    )

    def card_usuario(user):
        siguiendo = [bool(user["siguiendo"])]
        nombre = user.get("display_name") or user["username"]
        inicial = nombre[0].upper()

        btn = ft.ElevatedButton(
            "Siguiendo" if siguiendo[0] else "Seguir",
            height=32,
            bgcolor="#333333" if siguiendo[0] else ft.Colors.WHITE,
            color="#888888" if siguiendo[0] else ft.Colors.BLACK,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
        )

        def toggle(e):
            if siguiendo[0]:
                ctrl.dejar_de_seguir(page.user_id, user["id"])
                siguiendo[0] = False
                btn.text = "Seguir"
                btn.bgcolor = ft.Colors.WHITE
                btn.color = ft.Colors.BLACK
            else:
                ctrl.seguir(page.user_id, user["id"])
                siguiendo[0] = True
                btn.text = "Siguiendo"
                btn.bgcolor = "#333333"
                btn.color = "#888888"
            page.update()

        btn.on_click = toggle

        def ver_perfil(e):
            page.perfil_id = user["id"]
            page.run_task(page.push_route, "/perfil_publico")

        return ft.Container(
            padding=12, bgcolor="#1a1a1a", border_radius=10,
            on_click=ver_perfil,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=42, height=42, border_radius=21,
                        bgcolor="#222222",
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(inicial, size=18, color=ft.Colors.WHITE, font_family="Audiowide"),
                    ),
                    ft.Column(spacing=2, expand=True, controls=[
                        ft.Text(nombre, size=14, color=ft.Colors.WHITE),
                        ft.Text("@" + user["username"], size=12, color="#888888"),
                    ]),
                    btn,
                ],
            ),
        )

    def buscar(e):
        if not barra.value:
            return
        resultados.controls = [ft.ProgressRing(width=20, height=20, stroke_width=2, color="#888888")]
        page.update()
        users = ctrl.buscar_usuarios(barra.value, page.user_id)
        resultados.controls.clear()
        if not users:
            resultados.controls.append(ft.Text("Sin resultados", color="#888888"))
        else:
            for u in users:
                resultados.controls.append(card_usuario(u))
        page.update()

    barra.on_submit = buscar

    return ft.View(
        route="/usuarios",
        bgcolor="#0a0a0a",
        padding=ft.Padding(left=20, right=20, top=20, bottom=20),
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="#888888",
                        on_click=lambda _: page.run_task(page.push_route, "/home")),
                    ft.Text("Usuarios", size=16, color=ft.Colors.WHITE, font_family="Audiowide"),
                    ft.Container(width=40),
                ],
            ),
            ft.Container(height=10),
            ft.Row(controls=[barra]),
            ft.Container(height=10),
            ft.Container(expand=True, content=resultados),
        ],
    )
