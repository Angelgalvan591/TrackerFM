import flet as ft


def LoginView(page: ft.Page, auth_controller):

    def ver_contra(e):
        contra.password = not contra.password
        contra.update()

    def mostrar_error(msg):
        page.overlay.append(ft.SnackBar(ft.Text(msg), open=True))
        page.update()

    s = dict(
        border_radius=8, filled=True,
        fill_color=ft.Colors.GREY_100,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.BLACK,
        color=ft.Colors.BLACK,
        label_style=ft.TextStyle(color=ft.Colors.GREY_600),
    )

    correo = ft.TextField(label="Correo electrónico", prefix_icon=ft.Icons.EMAIL_OUTLINED, **s)
    contra = ft.TextField(
        label="Contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True,
        suffix=ft.IconButton(icon=ft.Icons.VISIBILITY_OUTLINED, icon_color=ft.Colors.GREY_600, on_click=ver_contra),
        **s,
    )

    def login_click(e):
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
            page.go("/home")
        else:
            mostrar_error(msg)
            page.update()

    return ft.View(
        route="/",
        bgcolor=ft.Colors.BLACK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=340,
                padding=30,
                content=ft.Column(
                    tight=True,
                    spacing=14,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("TrackerFM", size=22, weight="bold", color=ft.Colors.WHITE, font_family="Audiowide"),
                        ft.Text("Inicia sesión", size=13, color=ft.Colors.GREY_600, font_family="VT323"),
                        ft.Divider(height=6, color=ft.Colors.TRANSPARENT),
                        correo,
                        contra,
                        ft.ElevatedButton(
                            "Entrar",
                            width=300, height=44,
                            bgcolor=ft.Colors.BLACK,
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            on_click=login_click,
                        ),
                        ft.TextButton(
                            "¿Sin cuenta? Regístrate",
                            style=ft.ButtonStyle(color=ft.Colors.GREY_600),
                            on_click=lambda _: page.go("/registro"),
                        ),
                    ],
                ),
            )
        ],
    )
