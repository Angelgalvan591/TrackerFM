import flet as ft
import re


def RecuperarView(page: ft.Page, auth_controller):
    estado = {"id_usuario": None, "paso": 1}

    s = dict(
        border_radius=15, filled=True,
        fill_color="#122B46", border_color="transparent",
        focused_border_color="#69A6FF", color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE, label_style=ft.TextStyle(color="#A8B8CE"),
    )

    def notificar(texto):
        page.overlay.append(ft.SnackBar(ft.Text(texto, color=ft.Colors.WHITE), bgcolor="#0F1F33", open=True))
        page.update()

    def validar_email(valor):
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", valor))

    def validar_password(valor):
        return 8 <= len(valor) <= 30 and any(c.isupper() for c in valor) and any(c.islower() for c in valor)

    email_field = ft.TextField(label="Correo registrado", prefix_icon=ft.Icons.EMAIL_OUTLINED, **s)

    def enviar_codigo(e):
        email = email_field.value.strip()
        if not email or not validar_email(email):
            notificar("Ingresa un correo válido")
            return
        notificar("Enviando código...")
        ok, id_usuario, msg = auth_controller.solicitar_recuperacion(email)
        if ok:
            estado["id_usuario"] = id_usuario
            estado["paso"] = 2
            if msg.startswith("DEV:"):
                notificar(f"Modo dev — código: {msg[4:]}")
            construir_vista()
        else:
            notificar(f"Error: {msg}")

    paso1 = ft.Column(
        tight=True, spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.LOCK_RESET_OUTLINED, color="#69A6FF", size=40),
            ft.Text("Recuperar contraseña", size=18, color=ft.Colors.WHITE,
                    font_family="Audiowide", text_align=ft.TextAlign.CENTER),
            ft.Text("Te enviaremos un código de 6 dígitos a tu correo",
                    size=12, color="#A8B8CE", text_align=ft.TextAlign.CENTER),
            email_field,
            ft.ElevatedButton(
                "Enviar código", width=300, height=46,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=enviar_codigo,
            ),
        ],
    )

    token_field = ft.TextField(
        label="Código de 6 dígitos", prefix_icon=ft.Icons.PIN_OUTLINED,
        max_length=6, keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.CENTER, **s
    )

    def verificar_codigo(e):
        token = token_field.value.strip()
        if len(token) != 6 or not token.isdigit():
            notificar("Ingresa el código de 6 dígitos")
            return
        ok, msg = auth_controller.verificar_token(estado["id_usuario"], token)
        if ok:
            estado["paso"] = 3
            construir_vista()
        else:
            notificar(msg)

    paso2 = ft.Column(
        tight=True, spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.MARK_EMAIL_READ_OUTLINED, color="#69A6FF", size=40),
            ft.Text("Ingresa el código", size=18, color=ft.Colors.WHITE,
                    font_family="Audiowide", text_align=ft.TextAlign.CENTER),
            ft.Text("Revisa tu correo y escribe el código que recibiste",
                    size=12, color="#A8B8CE", text_align=ft.TextAlign.CENTER),
            token_field,
            ft.ElevatedButton(
                "Verificar", width=300, height=46,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=verificar_codigo,
            ),
        ],
    )

    nueva_field = ft.TextField(
        label="Nueva contraseña", password=True, can_reveal_password=True, **s
    )
    confirmar_field = ft.TextField(
        label="Confirmar contraseña", password=True, can_reveal_password=True, **s
    )

    def cambiar_password(e):
        nueva = nueva_field.value
        if not validar_password(nueva):
            notificar("Mínimo 8 caracteres, una mayúscula y una minúscula")
            return
        if nueva != confirmar_field.value:
            notificar("Las contraseñas no coinciden")
            return
        ok, msg = auth_controller.cambiar_password_por_id(estado["id_usuario"], nueva)
        if ok:
            notificar("¡Contraseña actualizada!")
            page.run_task(page.push_route, "/")
        else:
            notificar(msg)

    paso3 = ft.Column(
        tight=True, spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#69A6FF", size=40),
            ft.Text("Nueva contraseña", size=18, color=ft.Colors.WHITE,
                    font_family="Audiowide", text_align=ft.TextAlign.CENTER),
            ft.Text("Elige una contraseña segura", size=12, color="#A8B8CE"),
            nueva_field,
            confirmar_field,
            ft.ElevatedButton(
                "Guardar contraseña", width=300, height=46,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=cambiar_password,
            ),
        ],
    )

    contenido = ft.Ref[ft.Column]()

    def construir_vista():
        pasos = {1: paso1, 2: paso2, 3: paso3}
        contenido.current.controls[-1] = pasos[estado["paso"]]
        page.update()

    return ft.View(
        route="/recuperar",
        bgcolor="#08131F",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=360,
                padding=ft.Padding(left=28, right=28, top=36, bottom=36),
                border_radius=16, bgcolor="#0F1F33",
                border=ft.Border(
                    left=ft.BorderSide(1, "#122B46"), right=ft.BorderSide(1, "#122B46"),
                    top=ft.BorderSide(1, "#122B46"),  bottom=ft.BorderSide(1, "#122B46"),
                ),
                content=ft.Column(
                    ref=contenido,
                    tight=True, spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK, icon_color="#A8B8CE",
                                    on_click=lambda _: page.run_task(page.push_route, "/"),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        paso1,
                    ],
                ),
            )
        ],
    )
