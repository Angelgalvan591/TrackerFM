import flet as ft


def RecuperarView(page: ft.Page, auth_controller):
    email_ref = {"value": ""}
    step = {"actual": 1}

    s = dict(
        border_radius=10, filled=True,
        fill_color="#1a1a1a",
        border_color="#333333",
        focused_border_color="#ffffff",
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color="#888888"),
    )

    def mostrar_error(msg):
        page.overlay.append(ft.SnackBar(ft.Text(msg), open=True))
        page.update()

    # --- PASO 1: elegir método ---
    correo_field = ft.TextField(label="Tu correo registrado", prefix_icon=ft.Icons.EMAIL_OUTLINED, **s)
    telefono_field = ft.TextField(
        label="Teléfono WhatsApp (ej: +521234567890)",
        prefix_icon=ft.Icons.PHONE_OUTLINED,
        visible=False, **s
    )
    metodo = {"valor": "correo"}

    btn_correo = ft.ElevatedButton(
        "📧 Correo", width=140, height=38,
        bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )
    btn_whatsapp = ft.ElevatedButton(
        "💬 WhatsApp", width=140, height=38,
        bgcolor="#222222", color="#888888",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    def seleccionar_metodo(m):
        metodo["valor"] = m
        telefono_field.visible = (m == "whatsapp")
        btn_correo.bgcolor = ft.Colors.WHITE if m == "correo" else "#222222"
        btn_correo.color = ft.Colors.BLACK if m == "correo" else "#888888"
        btn_whatsapp.bgcolor = ft.Colors.WHITE if m == "whatsapp" else "#222222"
        btn_whatsapp.color = ft.Colors.BLACK if m == "whatsapp" else "#888888"
        page.update()

    btn_correo.on_click = lambda _: seleccionar_metodo("correo")
    btn_whatsapp.on_click = lambda _: seleccionar_metodo("whatsapp")

    metodo_row = ft.Row([btn_correo, btn_whatsapp], alignment=ft.MainAxisAlignment.CENTER, spacing=8)

    async def enviar_codigo(e):
        if not correo_field.value:
            correo_field.error_text = "Ingresa tu correo"
            page.update()
            return
        correo_field.error_text = None
        email_ref["value"] = correo_field.value
        if metodo["valor"] == "correo":
            ok, msg = auth_controller.enviar_codigo_correo(correo_field.value)
        else:
            if not telefono_field.value:
                telefono_field.error_text = "Ingresa tu teléfono"
                page.update()
                return
            telefono_field.error_text = None
            ok, msg = auth_controller.enviar_codigo_whatsapp(telefono_field.value, correo_field.value)
        if ok:
            step["actual"] = 2
            contenido.controls = _paso2()
            page.update()
        else:
            mostrar_error(msg)

    def _paso1():
        return [
            ft.Text("Recuperar contraseña", size=20, color=ft.Colors.WHITE, font_family="Audiowide"),
            ft.Text("Te enviaremos un código de 6 dígitos", size=12, color="#888888"),
            ft.Divider(height=8, color="#222222"),
            metodo_row,
            correo_field,
            telefono_field,
            ft.ElevatedButton(
                "Enviar código", width=300, height=46,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=enviar_codigo,
            ),
        ]

    # --- PASO 2: ingresar código ---
    codigo_field = ft.TextField(label="Código de 6 dígitos", prefix_icon=ft.Icons.PIN_OUTLINED, **s)

    async def verificar_codigo(e):
        if not codigo_field.value:
            codigo_field.error_text = "Ingresa el código"
            page.update()
            return
        codigo_field.error_text = None
        ok, msg = auth_controller.verificar_codigo(email_ref["value"], codigo_field.value)
        if ok:
            step["actual"] = 3
            contenido.controls = _paso3()
            page.update()
        else:
            mostrar_error(msg)

    def _paso2():
        return [
            ft.Text("Ingresa el código", size=20, color=ft.Colors.WHITE, font_family="Audiowide"),
            ft.Text(f"Enviado a {email_ref['value']}", size=12, color="#888888"),
            ft.Divider(height=8, color="#222222"),
            codigo_field,
            ft.ElevatedButton(
                "Verificar", width=300, height=46,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=verificar_codigo,
            ),
        ]

    # --- PASO 3: nueva contraseña ---
    nueva_field = ft.TextField(label="Nueva contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True, **s)
    confirmar_field = ft.TextField(label="Confirmar contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True, **s)

    async def cambiar_password(e):
        nueva_field.error_text = None
        confirmar_field.error_text = None
        if not nueva_field.value:
            nueva_field.error_text = "Ingresa la nueva contraseña"
            page.update()
            return
        if nueva_field.value != confirmar_field.value:
            confirmar_field.error_text = "Las contraseñas no coinciden"
            page.update()
            return
        ok, msg = auth_controller.cambiar_password(email_ref["value"], nueva_field.value)
        if ok:
            page.overlay.append(ft.SnackBar(ft.Text("¡Contraseña actualizada!"), open=True))
            page.update()
            await page.push_route("/")
        else:
            mostrar_error(msg)

    def _paso3():
        return [
            ft.Text("Nueva contraseña", size=20, color=ft.Colors.WHITE, font_family="Audiowide"),
            ft.Text("Ya casi, pon tu nueva contraseña", size=12, color="#888888"),
            ft.Divider(height=8, color="#222222"),
            nueva_field,
            confirmar_field,
            ft.ElevatedButton(
                "Guardar", width=300, height=46,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=cambiar_password,
            ),
        ]

    contenido = ft.Column(
        tight=True, spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=_paso1(),
    )

    return ft.View(
        route="/recuperar",
        bgcolor="#0a0a0a",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=360,
                padding=ft.Padding(left=32, right=32, top=40, bottom=40),
                border_radius=16,
                bgcolor="#111111",
                border=ft.Border(
                    left=ft.BorderSide(1, "#222222"), right=ft.BorderSide(1, "#222222"),
                    top=ft.BorderSide(1, "#222222"), bottom=ft.BorderSide(1, "#222222")
                ),
                content=ft.Column(
                    tight=True, spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        contenido,
                        ft.Container(height=8),
                        ft.TextButton(
                            "← Volver al login",
                            style=ft.ButtonStyle(color="#888888"),
                            on_click=lambda _: page.run_task(page.push_route, "/"),
                        ),
                    ],
                ),
            )
        ],
    )
