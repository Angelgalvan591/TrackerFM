import flet as ft
import threading
from TrackerFM.src.database.db import get_connection
from TrackerFM.src.controllers.social import SocialController
from TrackerFM.src.controllers.deezer import buscar_deezer

GENEROS = [
    "Pop", "Rock", "Hip-Hop", "Trap", "R&B", "Soul", "Jazz", "Blues",
    "Electrónica", "House", "Techno", "Reggaeton", "Salsa", "Cumbia",
    "Metal", "Punk", "Indie", "Folk", "Clásica", "Reggae", "K-Pop",
    "Funk", "Gospel", "Country", "Alternativo",
]


def PerfilView(page: ft.Page, auth_controller):
    def ir(ruta): page.run_task(page.push_route, ruta)
    ACCENT_VIOLET = "#6A98FF"
    ACCENT_CYAN = "#64D9FF"
    BG_COLOR = "#0B1020"
    CARD_BG = "#10294E"

    user = {}
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (page.user_id,))
        user = cursor.fetchone() or {}
        conn.close()
    except Exception:
        pass

    nombre  = user.get("display_name") or user.get("username", "Usuario")
    inicial = nombre[0].upper()

    social         = SocialController()
    seguidores     = social.get_seguidores(page.user_id)
    siguiendo_list = social.get_siguiendo(page.user_id)

    # ── LÓGICA DE LA SIDEBAR UNIFICADA (Overlay) ──────────────────────
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

    s = dict(
        border_radius=15,
        filled=True,
        fill_color=CARD_BG, border_color="#0F274A",
        focused_border_color=ACCENT_VIOLET, color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE, label_style=ft.TextStyle(color="#A8B8CE"),
    )

    f_display = ft.TextField(label="Nombre visible", value=user.get("display_name", "") or "", **s)
    f_bio     = ft.TextField(label="Bio", value=user.get("bio", ""), multiline=True, **s)
    f_avatar_url = ft.TextField(label="URL de Avatar", value=user.get("avatar_url", "") or "", **s)

    # ── artista favorito ───────────────────────────────────────────────────
    artista_sel    = [{"name": user.get("favorite_artist", ""), "img": ""}]
    artista_img_ref = [None]  # se construye solo cuando hay url
    artista_nombre  = ft.Text("", size=13, color=ft.Colors.WHITE,
                              max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True)
    artista_preview_row = ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
        artista_nombre
    ])

    f_artist = ft.TextField(
        label="Buscar artista", prefix_icon=ft.Icons.SEARCH,
        value=user.get("favorite_artist", ""), **s
    )
    artista_resultados = ft.Column(spacing=6)

    def actualizar_artista_preview(nombre_a, img_url):
        artista_sel[0] = {"name": nombre_a, "img": img_url}
        artista_nombre.value = nombre_a
        artista_preview_row.controls = []
        if img_url:
            artista_preview_row.controls.append(
                ft.Image(src=img_url, width=48, height=48, border_radius=24, fit=ft.BoxFit.COVER)
            )
        artista_preview_row.controls.append(artista_nombre)
        page.update()

    def buscar_artista(e):
        q = f_artist.value.strip()
        if not q:
            return
        artista_resultados.controls = [
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=ACCENT_VIOLET)
        ]
        page.update()

        def _fetch():
            res = buscar_deezer(q, "artist", limite=5)
            artista_resultados.controls = []
            for a in res:
                img = a.get("picture_medium", "")
                nombre_a = a["name"]

                def seleccionar(_, n=nombre_a, i=img):
                    actualizar_artista_preview(n, i)
                    f_artist.value = n
                    artista_resultados.controls = []
                    page.update()

                artista_resultados.controls.append(
                    ft.GestureDetector(
                        on_tap=seleccionar,
                        content=ft.Container(
                            bgcolor="#122B46", border_radius=10,
                            padding=ft.Padding(left=10, right=10, top=8, bottom=8),
                            content=ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                                ft.Image(src=img, width=36, height=36, border_radius=18,
                                         fit=ft.BoxFit.COVER) if img
                                else ft.Container(width=36, height=36, bgcolor="#0F1F33", border_radius=18),
                                ft.Text(nombre_a, size=13, color=ft.Colors.WHITE,
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True
                                ),
                            ]),
                        ),
                    )
                )
            page.update()

        threading.Thread(target=_fetch, daemon=True).start()

    f_artist.on_submit = buscar_artista

    # cargar imagen del artista actual si existe
    def cargar_artista_actual():
        nombre_actual = user.get("favorite_artist", "")
        if not nombre_actual:
            return
        res = buscar_deezer(nombre_actual, "artist", limite=1)
        if res:
            img = res[0].get("picture_medium", "")
            actualizar_artista_preview(nombre_actual, img)

    threading.Thread(target=cargar_artista_actual, daemon=True).start()

    # ── género favorito ────────────────────────────────────────────────────
    genero_sel = [user.get("favorite_genre") or ""]
    f_genre    = ft.TextField(
        label="O escribe uno personalizado",
        value=user.get("favorite_genre", ""), **s
    )

    generos_chips = ft.Row(wrap=True, spacing=6, run_spacing=6)

    def render_chips():
        generos_chips.controls = []
        for g in GENEROS:
            activo = g.lower() == genero_sel[0].lower()
            generos_chips.controls.append(
                ft.GestureDetector(
                    on_tap=lambda _, gn=g: seleccionar_genero(gn),
                    content=ft.Container(
                        padding=ft.Padding(left=12, right=12, top=6, bottom=6),
                        border_radius=20,
                        bgcolor=ACCENT_VIOLET if activo else "#0F274A",
                        content=ft.Text(g, size=12,
                                        color=ft.Colors.BLACK if activo else "#D5E0F5"),
                    ),
                )
            )

    def seleccionar_genero(g):
        genero_sel[0] = g
        f_genre.value = g
        render_chips()
        page.update()

    render_chips()

    # ── vista / edición ────────────────────────────────────────────────────
    edit_mode   = [False]
    content_col = ft.Column(spacing=10)

    avatar_display_content = ft.Container(
        width=90, height=90, border_radius=45, bgcolor="#0F274A",
        alignment=ft.Alignment(0, 0),
        border=ft.Border.all(2, ACCENT_VIOLET),
        content=ft.Text(inicial, size=28, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
    )

    def render_avatar_display():
        if user.get("avatar_url"):
            avatar_display_content.content = ft.Image(src=user.get("avatar_url"), width=90, height=90, border_radius=45, fit=ft.BoxFit.COVER)
        else:
            avatar_display_content.content = ft.Text(inicial, size=28, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold")

    def fila(icon, label, value):
        return ft.Container(
            padding=14, bgcolor=CARD_BG, border_radius=15, border=ft.Border.all(1, "#0F274A"),
            content=ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Icon(icon, color="#A8B8CE", size=18),
                ft.Column(spacing=2, controls=[
                    ft.Text(label, size=11, color="#A8B8CE"),
                    ft.Text(str(value) if value else "—", size=14, color=ft.Colors.WHITE),
                ]),
            ]),
        )

    def fila_artista():
        img_url  = artista_sel[0].get("img", "")
        nombre_a = artista_sel[0].get("name", "") or user.get("favorite_artist", "")
        icono = ft.Image(src=img_url, width=40, height=40, border_radius=20, fit=ft.BoxFit.COVER) \
            if img_url else ft.Container(
                width=40, height=40, border_radius=20, bgcolor="#0F1F33",
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.PERSON, color="#A8B8CE", size=20),
            )
        return ft.Container(
            padding=14, bgcolor=CARD_BG, border_radius=15, border=ft.Border.all(1, "#0F274A"),
            content=ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                icono,
                ft.Column(spacing=2, controls=[
                    ft.Text("Artista favorito", size=11, color="#A8B8CE"),
                    ft.Text(nombre_a or "—", size=14, color=ft.Colors.WHITE),
                ]),
            ]),
        )

    def render_view():
        content_col.controls = [
            fila(ft.Icons.PERSON_OUTLINE, "Username",        user.get("username")),
            fila(ft.Icons.BADGE_OUTLINED, "Nombre visible",  user.get("display_name")),
            fila(ft.Icons.INFO_OUTLINE,   "Bio",             user.get("bio")),
            fila(ft.Icons.IMAGE_OUTLINED, "URL de Avatar",   user.get("avatar_url")),
            fila_artista(),
            fila(ft.Icons.QUEUE_MUSIC,    "Género favorito", user.get("favorite_genre")),
            fila(ft.Icons.CALENDAR_TODAY, "Miembro desde",   str(user.get("created_at", ""))[:10]),
        ]

    def render_edit():
        f_avatar_url.value = user.get("avatar_url", "") or "" # Ensure current value is displayed
        content_col.controls = [
            f_display,
            f_bio,
            # artista
            ft.Text("Artista favorito", size=12, color="#A8B8CE"),
            ft.Row(spacing=8, controls=[
                ft.Container(expand=True, content=f_artist),
                ft.IconButton(icon=ft.Icons.SEARCH, icon_color=ACCENT_VIOLET, 
                              on_click=buscar_artista),
            ]),
            artista_resultados,
            ft.Container(
                visible=bool(artista_sel[0].get("name")),
                bgcolor="#10243C", border_radius=10,
                padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                content=artista_preview_row,
            ),
            f_avatar_url, # Add avatar URL field here
            # género
            ft.Text("Género favorito", size=12, color="#A8B8CE"),
            generos_chips,
            f_genre,
            ft.ElevatedButton(
                "Guardar", width=300, height=44,
                bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=guardar,
            ),
        ]

    def guardar(e):
        nombre_artista = f_artist.value.strip() or artista_sel[0].get("name", "")
        genero_final   = f_genre.value.strip() or genero_sel[0]
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute( # Added avatar_url to the UPDATE query
                "UPDATE users SET display_name=%s, bio=%s, favorite_artist=%s, favorite_genre=%s, avatar_url=%s WHERE id=%s",
                (f_display.value, f_bio.value, nombre_artista, genero_final, f_avatar_url.value, page.user_id)
            )
            conn.commit()
            conn.close()
            user["display_name"]    = f_display.value
            user["bio"]             = f_bio.value
            user["avatar_url"]      = f_avatar_url.value # Update local user object
            
            user["favorite_artist"] = nombre_artista
            user["favorite_genre"]  = genero_final
            genero_sel[0]           = genero_final
        except Exception:
            pass
        edit_mode[0] = False
        edit_btn.icon = ft.Icons.EDIT_OUTLINED
        render_view()
        render_avatar_display() # Update avatar display after saving
        page.update()

    def toggle_edit(e):
        edit_mode[0] = not edit_mode[0]
        if edit_mode[0]:
            edit_btn.icon = ft.Icons.CLOSE
            render_edit()
        else:
            edit_btn.icon = ft.Icons.EDIT_OUTLINED
            render_view()
        page.update()

    edit_btn = ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, icon_color="#A8B8CE", on_click=toggle_edit)

    render_avatar_display() # Initial render of avatar
    render_view()

    def abrir_sidebar(e):
        overlay.visible = True
        sidebar_panel.visible = True
        page.update()

    def cerrar_sidebar(e):
        overlay.visible = False
        sidebar_panel.visible = False
        page.update()

    return ft.View(
        route="/perfil",
        bgcolor=BG_COLOR,
        padding=0,
        controls=[
            ft.Stack(expand=True, controls=[
                ft.Column(expand=True, spacing=0, controls=[
                    ft.Container(
                        expand=True,
                        padding=40,
                        content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0,
                        controls=[
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.MENU_ROUNDED, icon_color="#A8B8CE", on_click=abrir_sidebar),
                                ft.Text("CONFIGURACIÓN DE PERFIL", size=14, color="#2C5D85", font_family="Audiowide"),
                                ft.Container(expand=True),
                                edit_btn,
                                ft.IconButton(
                                    icon=ft.Icons.LOGOUT_ROUNDED, 
                                    icon_color="#FF7AB7", 
                                    on_click=lambda _: (page.borrar_sesion(), page.run_task(page.push_route, "/"))
                                ),
                            ]),
                            ft.Container(height=30),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=6,
                                controls=[
                                    avatar_display_content, # Use the dynamic avatar content
                                    ft.Text(nombre, size=24, color=ft.Colors.WHITE, weight="bold"),
                                    ft.Text(user.get("email", ""), size=12, color="#A8B8CE"),
                                    ft.Container(height=10),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER, spacing=24,
                                        controls=[
                                            ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                                ft.Text(str(len(seguidores)), size=20, color=ft.Colors.WHITE, weight="bold"),
                                                ft.Text("SEGUIDORES", size=10, color=ACCENT_CYAN, weight="bold"),
                                            ]),
                                            ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                                ft.Text(str(len(siguiendo_list)), size=20, color=ft.Colors.WHITE, weight="bold"),
                                                ft.Text("SIGUIENDO", size=10, color=ACCENT_CYAN, weight="bold"),
                                            ]),
                                        ],
                                    ),
                                ],
                            ),
                            ft.Container(height=40),
                            content_col,
                        ],
                    )
                    )
                ]),
                overlay,
                ft.Row(expand=True, spacing=0, controls=[sidebar_panel]),
            ])
        ]
    )