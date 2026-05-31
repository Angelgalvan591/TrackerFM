import flet as ft


def RegistroView(page: ft.Page, auth_controller):

    def ver_contra(e):
        contra.password = not contra.password
        contra.update()

    def mostrar_error(msg):
        page.overlay.append(ft.SnackBar(ft.Text(msg), open=True))
        page.update()

    s = dict(
        border_radius=10, filled=True,
        fill_color="#122B46",
        border_color="transparent",
        focused_border_color="#69A6FF",
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color="#A8B8CE"),
    )

    fuerza_text = ft.Text("", size=11)

    def evaluar_fuerza(e):
        val = contra.value or ""
        if len(val) == 0:
            fuerza_text.value = ""
        elif len(val) < 4:
            fuerza_text.value = "Muy débil"
            fuerza_text.color = "#ff4444"
        elif len(val) < 6:
            fuerza_text.value = "Débil"
            fuerza_text.color = "#ff8800"
        elif len(val) < 8:
            fuerza_text.value = "Media"
            fuerza_text.color = "#ffcc00"
        else:
            fuerza_text.value = "Fuerte 💪"
            fuerza_text.color = "#46D7FF"
        page.update()

    nombre = ft.TextField(label="Nombre", prefix_icon=ft.Icons.PERSON_OUTLINE, max_length=20, **s)
    correo = ft.TextField(label="Correo", prefix_icon=ft.Icons.EMAIL_OUTLINED, **s)
    contra = ft.TextField(
        label="Contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True,
        max_length=8, on_change=evaluar_fuerza,
        suffix=ft.IconButton(icon=ft.Icons.VISIBILITY_OUTLINED, icon_color="#A8B8CE", on_click=ver_contra),
        **s,
    )

    async def registra(e):
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
            await page.push_route("/")
        else:
            mostrar_error(msg)
            page.update()

    return ft.View(
        route="/registro",
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
                        ft.Text("Crear cuenta", size=26, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
                        ft.Text("Únete a Tracker FM", size=13, color="#A8B8CE"),
                        ft.Divider(height=8, color="#122B46"),
                        nombre,
                        correo,
                        contra,
                        fuerza_text,
                        ft.Container(height=4),
                        ft.ElevatedButton(
                            "Registrarse",
                            width=300, height=46,
                            bgcolor=ft.Colors.WHITE,
                            color=ft.Colors.BLACK,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=registra,
                        ),
                        ft.TextButton(
                            "¿Ya tienes cuenta? Inicia sesión",
                            style=ft.ButtonStyle(color="#A8B8CE"),
                            on_click=lambda _: page.run_task(page.push_route, "/"),
                        ),
                    ],
                ),
            )
        ],
    )
