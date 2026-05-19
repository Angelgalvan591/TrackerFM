import flet as ft


def RecuperarView(page: ft.Page, auth_controller):
    email_ref  = [""]
    dev_code   = [""]
    metodo_sel = ["correo"]

    s = dict(
        border_radius=10, filled=True,
        fill_color="#1a1a1a",
        border_color="#333333",
        focused_border_color="#ffffff",
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color="#888888"),
    )

    contenido = ft.Column(
        tight=True, spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def snack(msg, color="#e05555"):
        page.overlay.append(ft.SnackBar(ft.Text(msg, color=ft.Colors.WHITE), bgcolor=color, open=True))
        page.update()

    # ── PASO 1 ─────────────────────────────────────────────────────────────
    correo_field  = ft.TextField(label="Correo registrado", prefix_icon=ft.Icons.EMAIL_OUTLINED, **s)
    telefono_field = ft.TextField(label="WhatsApp (ej: +521234567890)",
                                  prefix_icon=ft.Icons.PHONE_OUTLINED, visible=False, **s)

    btn_correo = ft.ElevatedButton(
        "📧 Correo", width=140, height=38,
        bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )
    btn_wsp = ft.ElevatedButton(
        "💬 WhatsApp", width=140, height=38,
        bgcolor="#222222", color="#888888",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    def sel_metodo(m):
        metodo_sel[0] = m
        telefono_field.visible = (m == "whatsapp")
        btn_correo.bgcolor = ft.Colors.WHITE if m == "correo" else "#222222"
        btn_correo.color   = ft.Colors.BLACK if m == "correo" else "#888888"
        btn_wsp.bgcolor    = ft.Colors.WHITE if m == "whatsapp" else "#222222"
        btn_wsp.color      = ft.Colors.BLACK if m == "whatsapp" else "#888888"
        page.update()

    btn_correo.on_click = lambda _: sel_metodo("correo")
    btn_wsp.on_click    = lambda _: sel_metodo("whatsapp")

    def enviar(e):
        correo_field.error_text  = None
        telefono_field.error_text = None
        if not correo_field.value:
            correo_field.error_text = "Ingresa tu correo"
            page.update()
            return
        if metodo_sel[0] == "whatsapp" and not telefono_field.value:
            telefono_field.error_text = "Ingresa tu número de WhatsApp"
            page.update()
            return

        email_ref[0] = correo_field.value.strip()

        if metodo_sel[0] == "correo":
            ok, msg = auth_controller.enviar_codigo_correo(email_ref[0])
        else:
            ok, msg = auth_controller.enviar_codigo_whatsapp(
                telefono_field.value.strip(), email_ref[0]
            )

        if not ok:
            correo_field.error_text = msg
            page.update()
            return

        dev_code[0] = msg[4:] if msg.startswith("DEV:") else ""
        paso2()

    def paso1():
        contenido.controls = [
            ft.Icon(ft.Icons.LOCK_RESET_OUTLINED, color="#1DB954", size=40),
            ft.Text("Recuperar contraseña", size=18, color=ft.Colors.WHITE,
                    font_family="Audiowide", text_align=ft.TextAlign.CENTER),
            ft.Text("Elige cómo recibir tu código",
                    size=12, color="#888888", text_align=ft.TextAlign.CENTER),
            ft.Row([btn_correo, btn_wsp], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            correo_field,
            telefono_field,
            ft.ElevatedButton(
                "Enviar código", width=300, height=46,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=enviar,
            ),
        ]
        page.update()

    # ── PASO 2 ─────────────────────────────────────────────────────────────
    codigo_field = ft.TextField(
        label="Código de 6 dígitos", prefix_icon=ft.Icons.PIN_OUTLINED,
        max_length=6, **s
    )

    def verificar(e):
        codigo_field.error_text = None
        if not codigo_field.value:
            codigo_field.error_text = "Ingresa el código"
            page.update()
            return
        ok, msg = auth_controller.verificar_codigo(email_ref[0], codigo_field.value.strip())
        if not ok:
            codigo_field.error_text = msg
            page.update()
            return
        paso3()

    def paso2():
        destino = telefono_field.value.strip() if metodo_sel[0] == "whatsapp" else email_ref[0]
        icono   = ft.Icons.MARK_EMAIL_READ_OUTLINED if metodo_sel[0] == "correo" else ft.Icons.CHAT_OUTLINED

        aviso_dev = ft.Container(
            bgcolor="#1a2a1a", border_radius=8,
            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
            content=ft.Text(f"Modo dev — tu código es: {dev_code[0]}",
                            size=12, color="#1DB954", text_align=ft.TextAlign.CENTER),
        ) if dev_code[0] else ft.Container(height=0)

        contenido.controls = [
            ft.Icon(icono, color="#1DB954", size=40),
            ft.Text("Revisa tu código", size=18, color=ft.Colors.WHITE,
                    font_family="Audiowide", text_align=ft.TextAlign.CENTER),
            ft.Text(f"Enviado a {destino}", size=12, color="#888888",
                    text_align=ft.TextAlign.CENTER),
            aviso_dev,
            codigo_field,
            ft.ElevatedButton(
                "Verificar código", width=300, height=46,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=verificar,
            ),
            ft.TextButton("Reenviar código",
                          style=ft.ButtonStyle(color="#888888"),
                          on_click=lambda _: enviar(None)),
        ]
        page.update()

    # ── PASO 3 ─────────────────────────────────────────────────────────────
    nueva_field     = ft.TextField(label="Nueva contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE,
                                   password=True, can_reveal_password=True, **s)
    confirmar_field = ft.TextField(label="Confirmar contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE,
                                   password=True, can_reveal_password=True, **s)

    async def guardar(e):
        nueva_field.error_text     = None
        confirmar_field.error_text = None
        if len(nueva_field.value) < 6:
            nueva_field.error_text = "Mínimo 6 caracteres"
            page.update()
            return
        if nueva_field.value != confirmar_field.value:
            confirmar_field.error_text = "Las contraseñas no coinciden"
            page.update()
            return
        ok, msg = auth_controller.cambiar_password(email_ref[0], nueva_field.value)
        if ok:
            snack("¡Contraseña actualizada!", "#1DB954")
            await page.push_route("/")
        else:
            snack(msg)

    def paso3():
        contenido.controls = [
            ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#1DB954", size=40),
            ft.Text("Nueva contraseña", size=18, color=ft.Colors.WHITE,
                    font_family="Audiowide", text_align=ft.TextAlign.CENTER),
            ft.Text("Ya casi, elige tu nueva contraseña",
                    size=12, color="#888888", text_align=ft.TextAlign.CENTER),
            nueva_field,
            confirmar_field,
            ft.ElevatedButton(
                "Guardar", width=300, height=46,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=guardar,
            ),
        ]
        page.update()

    paso1()

    return ft.View(
        route="/recuperar",
        bgcolor="#0a0a0a",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=360,
                padding=ft.Padding(left=28, right=28, top=36, bottom=36),
                border_radius=16, bgcolor="#111111",
                border=ft.Border(
                    left=ft.BorderSide(1, "#222222"), right=ft.BorderSide(1, "#222222"),
                    top=ft.BorderSide(1, "#222222"),  bottom=ft.BorderSide(1, "#222222"),
                ),
                content=ft.Column(
                    tight=True, spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        contenido,
                        ft.Container(height=12),
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
