import flet as ft


def LoginView(page: ft.Page, auth_controller):
    ACCENT = "#69A6FF"

    def ver_contra(e):
        contra.password = not contra.password
        contra.update()

    def mostrar_error(msg):
        page.overlay.append(ft.SnackBar(ft.Text(msg), open=True))
        page.update()

    s = dict(
        border_radius=12, filled=True,
        fill_color="#122B46",
        border_color="transparent",
        focused_border_color=ACCENT,
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color="#A8B8CE"),
    )

    correo = ft.TextField(label="Correo", prefix_icon=ft.Icons.EMAIL_OUTLINED, **s)
    contra = ft.TextField(
        label="Contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True,
        suffix=ft.IconButton(icon=ft.Icons.VISIBILITY_OUTLINED, icon_color="#A8B8CE", on_click=ver_contra),
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
        bgcolor="#08131F",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=360,
                padding=ft.Padding(left=32, right=32, top=40, bottom=40),
                border_radius=16,
                bgcolor="#10243C",
                content=ft.Column(
                    tight=True,
                    spacing=16,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("TRACKER FM", size=26, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
                        ft.Text("Inicia sesión", size=13, color="#A8B8CE"),
                        ft.Divider(height=8, color="#122B46"),
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
                            style=ft.ButtonStyle(color="#A8B8CE"),
                            on_click=lambda _: page.run_task(page.push_route, "/registro"),
                        ),
                        ft.TextButton(
                            "¿Olvidaste tu contraseña?",
                            style=ft.ButtonStyle(color="#A8B8CE"),
                            on_click=lambda _: page.run_task(page.push_route, "/recuperar"),
                        ),
                    ],
                ),
            )
        ],
    )
