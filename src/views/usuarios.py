import flet as ft
from TrackerFM.src.controllers.social import SocialController


def UsuariosView(page: ft.Page):

    ctrl = SocialController()
    resultados = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO)
    ACCENT = "#69A6FF"
    CARD_BG = "#122B46"
    BG_COLOR = "#08131F"

    def ir(ruta):
        cerrar_sidebar(None)
        page.run_task(page.push_route, ruta)

    # ── LÓGICA DE LA SIDEBAR ──────────────────────────────────────────
    overlay = ft.GestureDetector(
        visible=False, expand=True,
        on_tap=lambda _: cerrar_sidebar(None),
        content=ft.Container(expand=True, bgcolor="#00000099"),
    )

    def nav_item(icon, label, ruta):
        return ft.TextButton(
            content=ft.Row(spacing=14, controls=[
                ft.Icon(icon, color="#D5E0F5", size=20),
                ft.Text(label, size=14, color="#D5E0F5"),
            ]),
            style=ft.ButtonStyle(
                overlay_color="#ffffff11",
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(left=16, right=16, top=12, bottom=12),
            ),
            on_click=lambda _, r=ruta: ir(r),
        )

    sidebar_panel = ft.Container(
        visible=False, width=260, bgcolor="#0F1F33",
        content=ft.Column(spacing=0, controls=[
            ft.Container(
                height=100, bgcolor="#10243C",
                padding=ft.Padding(left=20, right=20, top=40, bottom=16),
                content=ft.Text("TRACKER FM", size=16, color=ft.Colors.WHITE,
                                font_family="Audiowide", weight="bold"),
            ),
            ft.Container(height=8),
            ft.Container(
                padding=ft.Padding(left=12, right=12, top=0, bottom=0),
                content=ft.Column(spacing=2, controls=[
                    nav_item(ft.Icons.HOME_OUTLINED,  "Home",    "/home"),
                    nav_item(ft.Icons.SEARCH,         "Buscar",  "/busqueda"),
                    nav_item(ft.Icons.PEOPLE_OUTLINE, "Usuarios",  "/usuarios"),
                    nav_item(ft.Icons.HISTORY_ROUNDED, "Mi Actividad", "/actividad"),
                    nav_item(ft.Icons.PERSON_OUTLINE, "Mi Perfil", "/perfil"),
                ]),
            ),
        ]),
    )

    def abrir_sidebar(e):
        overlay.visible = True
        sidebar_panel.visible = True
        page.update()

    def cerrar_sidebar(e):
        overlay.visible = False
        sidebar_panel.visible = False
        page.update()

    barra = ft.TextField(
        hint_text="Buscar usuarios...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=16,
        filled=True,
        fill_color=CARD_BG,
        border_color="#0F274A",
        focused_border_color=ACCENT,
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        hint_style=ft.TextStyle(color="#A8B8CE"),
        expand=True,
    )

    def card_usuario(user):
        siguiendo = [bool(user["siguiendo"])]
        nombre = user.get("display_name") or user["username"]
        inicial = nombre[0].upper()

        btn = ft.ElevatedButton(
            "Siguiendo" if siguiendo[0] else "Seguir",
            height=32,
            bgcolor="#0F1F33" if siguiendo[0] else ft.Colors.WHITE,
            color="#AAAAAA" if siguiendo[0] else ft.Colors.BLACK,
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
                btn.bgcolor = "#0F1F33"
                btn.color = "#A8B8CE"
            page.update()

        btn.on_click = toggle

        def ver_perfil(e):
            page.perfil_id = user["id"]
            page.run_task(page.push_route, "/perfil_publico")

        return ft.Container(
            padding=16, 
            bgcolor=CARD_BG, 
            border_radius=16,
            border=ft.Border.all(1, "#17354E"),
            on_click=ver_perfil,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container( # Avatar display
                        width=42, height=42, border_radius=21, bgcolor="#122B46",
                        alignment=ft.Alignment(0, 0),
                        content=ft.Image(
                            src=user.get("avatar_url"),
                            width=42, height=42, border_radius=21, fit=ft.BoxFit.COVER
                        ) if user.get("avatar_url") else ft.Text(inicial, size=18, color=ft.Colors.WHITE, font_family="Audiowide"),
                    ),
                    
                    ft.Column(spacing=2, expand=True, controls=[
                        ft.Text(nombre, size=14, color=ft.Colors.WHITE),
                        ft.Text("@" + user["username"], size=12, color="#A8B8CE"),
                    ]),
                    btn,
                ],
            ),
        )

    def buscar(e):
        if not barra.value:
            return
        resultados.controls = [ft.ProgressRing(width=20, height=20, stroke_width=2, color=ACCENT)]
        page.update()
        users = ctrl.buscar_usuarios(barra.value, page.user_id)
        resultados.controls.clear()
        if not users:
            resultados.controls.append(ft.Text("Sin resultados", color="#A8B8CE"))
        else:
            for u in users:
                resultados.controls.append(card_usuario(u))
        page.update()

    barra.on_submit = buscar

    return ft.View(
        route="/usuarios",
        bgcolor=BG_COLOR,
        padding=0,
        controls=[
            ft.Stack(expand=True, controls=[
                ft.Column(expand=True, spacing=0, controls=[
                    ft.Container(
                        padding=ft.Padding(left=20, right=20, top=20, bottom=10),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.IconButton(icon=ft.Icons.MENU_ROUNDED, icon_color="#A8B8CE", on_click=abrir_sidebar),
                                ft.Text("USUARIOS", size=16, color=ft.Colors.WHITE, font_family="Audiowide"),
                                ft.Container(width=40),
                            ],
                        ),
                    ),
                    ft.Container(padding=ft.Padding(left=20, right=20, top=10, bottom=20), expand=True, content=ft.Column([
                        ft.Row(controls=[barra]),
                        ft.Container(height=10),
                        ft.Container(expand=True, content=resultados),
                    ])),
                ]),
                overlay,
                ft.Row(expand=True, spacing=0, controls=[sidebar_panel]),
            ]),
        ],
    )