import flet as ft


def RegistroView(page: ft.Page, auth_controller):

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

    nombre   = ft.TextField(label="Nombre",   prefix_icon=ft.Icons.PERSON_OUTLINE, **s)
    correo   = ft.TextField(label="Correo",   prefix_icon=ft.Icons.EMAIL_OUTLINED, **s)
    contra   = ft.TextField(
        label="Contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True,
        suffix=ft.IconButton(icon=ft.Icons.VISIBILITY_OUTLINED, icon_color=ft.Colors.GREY_600, on_click=ver_contra),
        **s,
    )

    def registra(e):
        nombre.error_text = None
        correo.error_text = None
        contra.error_text = None
        error = False
        if not nombre.value:
            nombre.error_text = "Ingresa tu nombre"
            error = True
        if not correo.value:
            correo.error_text = "Ingresa tu correo"
            error = True
        if not contra.value:
            contra.error_text = "Ingresa una contraseña"
            error = True
        elif len(contra.value) > 8:
            contra.error_text = "Máximo 8 caracteres"
            error = True
        if error:
            page.update()
            return
        ok, msg = auth_controller.registrar(nombre.value, correo.value, contra.value)
        if ok:
            page.go("/")
        else:
            mostrar_error(msg)
            page.update()

    return ft.View(
        route="/registro",
        bgcolor=ft.Colors.BLACK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=360,
                padding=30,
                content=ft.Column(
                    tight=True,
                    spacing=14,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Crear una cuenta", size=22, weight="bold", color=ft.Colors.WHITE, font_family="Audiowide"),
                        ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                        nombre,
                        correo,
                        contra,
                        ft.ElevatedButton(
                            "Registrarse",
                            width=300, height=44,
                            bgcolor=ft.Colors.BLACK,
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            on_click=registra,
                        ),
                        ft.TextButton(
                            "¿Ya tienes cuenta? Inicia sesión",
                            style=ft.ButtonStyle(color=ft.Colors.GREY_600),
                            on_click=lambda _: page.go("/"),
                        ),
                    ],
                ),
            )
        ],
    )
