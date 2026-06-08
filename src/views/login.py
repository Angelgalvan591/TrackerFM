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
            
        user, msg = auth_controller.login(correo.value.strip(), contra.value)
        if user:
            # 1. Asignar ID fresco
            nuevo_id = int(user["id"])
            page.user_id = nuevo_id
            # 2. Guardar en disco inmediatamente
            page.guardar_sesion(nuevo_id)
            # 3. Navegar al Home
            page.update()
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
                        ft.Container(
                            width=64, height=64, border_radius=32,
                            bgcolor="#10243C",
                            border=ft.Border.all(2, ACCENT),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text("T", size=26, color=ACCENT, font_family="Audiowide", weight="bold"),
                        ),
                        ft.Container(height=4),
                        ft.Text("TRACKER FM", size=24, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
                        ft.Text("tu música, tu historia", size=11, color="#4A6A8A", italic=True),
                        ft.Divider(height=20, color="#122B46"),
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
                            content=ft.Text("¿Sin cuenta? Regístrate", color="#A8B8CE", size=13),
                            style=ft.ButtonStyle(overlay_color="#ffffff11"),
                            on_click=lambda _: page.run_task(page.push_route, "/registro"),
                        ),
                        ft.TextButton(
                            content=ft.Text("¿Olvidaste tu contraseña?", color="#4A6A8A", size=12),
                            style=ft.ButtonStyle(overlay_color="#ffffff11"),
                            on_click=lambda _: page.run_task(page.push_route, "/recuperar"),
                        ),
                    ],
                ),
            )
        ],
    )