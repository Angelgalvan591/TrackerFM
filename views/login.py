import flet as ft


def LoginView(page: ft.Page, auth_controller):

    def ver_contra(e):
        contra.password = not contra.password
        contra.update()

    def mostrar_error(msg):
        page.overlay.append(ft.SnackBar(ft.Text(msg), open=True))
        page.update()

    s = dict(
        border_radius=10, filled=True,
        fill_color="#1a1a1a",
        border_color="#333333",
        focused_border_color="#ffffff",
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color="#888888"),
    )

    correo = ft.TextField(label="Correo", prefix_icon=ft.Icons.EMAIL_OUTLINED, **s)
    contra = ft.TextField(
        label="Contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True,
        suffix=ft.IconButton(icon=ft.Icons.VISIBILITY_OUTLINED, icon_color="#888888", on_click=ver_contra),
        **s,
    )

    async def login_click(e):
        correo.error_text = None
        contra.error_text = None
        error = False
        if not correo.value:
            correo.error_text = "Ingresa tu correo"
            error = True
        if not contra.value:
            contra.error_text = "Ingresa tu contraseña"
            error = True
        if error:
            page.update()
            return
        user, msg = auth_controller.login(correo.value, contra.value)
        if user:
            page.user_id = user["id"]
            page.guardar_sesion(user["id"])
            await page.push_route("/home")
        else:
            mostrar_error(msg)
            page.update()

    return ft.View(
        route="/",
        bgcolor="#0a0a0a",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=360,
                padding=ft.Padding(left=32, right=32, top=40, bottom=40),
                border_radius=16,
                bgcolor="#111111",
                border=ft.Border(left=ft.BorderSide(1, "#222222"), right=ft.BorderSide(1, "#222222"), top=ft.BorderSide(1, "#222222"), bottom=ft.BorderSide(1, "#222222")),
                content=ft.Column(
                    tight=True,
                    spacing=16,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("TRACKER FM", size=26, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
                        ft.Text("Inicia sesión", size=13, color="#888888"),
                        ft.Divider(height=8, color="#222222"),
                        correo,
                        contra,
                        ft.Container(height=4),
                        ft.ElevatedButton(
                            "Entrar",
                            width=300, height=46,
                            bgcolor=ft.Colors.WHITE,
                            color=ft.Colors.BLACK,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=login_click,
                        ),
                        ft.TextButton(
                            "¿Sin cuenta? Regístrate",
                            style=ft.ButtonStyle(color="#888888"),
                            on_click=lambda _: page.run_task(page.push_route, "/registro"),
                        ),
                        ft.TextButton(
                            "¿Olvidaste tu contraseña?",
                            style=ft.ButtonStyle(color="#888888"),
                            on_click=lambda _: page.run_task(page.push_route, "/recuperar"),
                        ),
                    ],
                ),
            )
        ],
    )
