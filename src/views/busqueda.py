import flet as ft
import pygame
import requests
import threading
import io
from TrackerFM.src.controllers.deezer import buscar_deezer
from TrackerFM.src.controllers.deezer import get_artist_details

pygame.mixer.init()
reproduciendo = [None]



def BusquedaView(page: ft.Page):
    def ir(ruta):
        cerrar_sidebar(None)
        page.run_task(page.push_route, ruta)

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

    resultados = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True, controls=[
        ft.Container(
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(top=40, left=0, right=0, bottom=0),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.MUSIC_NOTE, color="#1A3A5C", size=52),
                    ft.Text("Busca canciones, álbumes o artistas", size=13, color="#2B5F81",
                            text_align=ft.TextAlign.CENTER),
                ],
            ),
        )
    ])
    filtro = ["track"]
    tipos = ["track", "album", "artist"]
    labels = ["Canciones", "Álbumes", "Artistas"]

    barra = ft.TextField(
        hint_text="Buscar canciones, álbumes, artistas...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=16,
        filled=True,
        fill_color="#10294E",
        border_color="#0F274A",
        focused_border_color="#6A98FF",
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        hint_style=ft.TextStyle(color="#A8B8CE"),
        expand=True,
    )

    def btn_filtro(label, tipo):
        activo = tipo == filtro[0]
        return ft.TextButton(
            content=ft.Text(label, color=ft.Colors.WHITE if activo else "#A8B8CE", size=13, weight="bold" if activo else None),
            style=ft.ButtonStyle(
                bgcolor="#6A98FF" if activo else "#10294E",
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding(left=16, right=16, top=6, bottom=6),
                overlay_color="#ffffff11",
            ),
            on_click=lambda _, t=tipo: cambiar_filtro(t),
        )

    filtros_row = ft.Row(spacing=8)

    def render_filtros():
        filtros_row.controls = [btn_filtro(labels[i], tipos[i]) for i in range(3)]

    def cambiar_filtro(tipo):
        filtro[0] = tipo
        render_filtros()
        page.update()
        if barra.value:
            hacer_busqueda(None)

    def play_preview(url, btn):
        def _play():
            if reproduciendo[0] == url:
                pygame.mixer.music.stop()
                reproduciendo[0] = None
                btn.icon = ft.Icons.PLAY_CIRCLE_OUTLINE
                page.update()
                return
            pygame.mixer.music.stop()
            reproduciendo[0] = url
            btn.icon = ft.Icons.STOP_CIRCLE
            page.update()
            try:
                data = requests.get(url, timeout=10).content
                pygame.mixer.music.load(io.BytesIO(data))
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(200)
            except Exception:
                pass
            if reproduciendo[0] == url:
                reproduciendo[0] = None
                btn.icon = ft.Icons.PLAY_CIRCLE_OUTLINE
                page.update()
        threading.Thread(target=_play, daemon=True).start()

    def ir_artista(artista_nombre, origen):
        def _buscar():
            res = buscar_deezer(artista_nombre, "artist", limite=1)
            if res:
                page.artista_data = res[0]
            else:
                page.artista_data = {"name": artista_nombre, "images": [], "genres": [], "followers": {"total": 0}, "popularity": 0, "id": ""}
            page.artista_origen = origen
            page.run_task(page.push_route, "/perfil_artista")
        threading.Thread(target=_buscar, daemon=True).start()

    def abrir_track(track):
        page.track_data = track
        page.track_origen = "/busqueda"
        page.run_task(page.push_route, "/resena_cancion")

    def card_track(item):
        artista_obj = item.get("artist") or {}
        artista_nombre = artista_obj.get("name", "Artista desconocido")
        album_obj = item.get("album") or {}
        img_big = album_obj.get("cover_big") or album_obj.get("cover_medium") or ""
        preview = item.get("preview", "")

        play_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color="#46D7FF",
            icon_size=28,
            disabled=not preview,
        )
        if preview:
            play_btn.on_click = lambda _, u=preview, b=play_btn: play_preview(u, b)

        review_btn = ft.IconButton(
            icon=ft.Icons.RATE_REVIEW_OUTLINED,
            icon_color="#A8B8CE",
            icon_size=22,
            tooltip="Ver reseñas",
            on_click=lambda _, t=item: abrir_track(t),
        )

        return ft.GestureDetector(
            on_tap=lambda _, t=item: abrir_track(t),
            content=ft.Container(
            bgcolor="#10294E",
            border_radius=20,
            border=ft.Border.all(1, "#0F274A"),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=True,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Stack(
                        controls=[
                            ft.Image(src=img_big, height=200, expand=True, fit=ft.BoxFit.COVER) if img_big
                            else ft.Container(height=200, bgcolor="#122B46",
                                content=ft.Icon(ft.Icons.MUSIC_NOTE, color="#1C4F7A", size=64),
                                alignment=ft.Alignment(0, 0)),
                            ft.Container(
                                height=200, expand=True,
                                gradient=ft.LinearGradient(
                                    begin=ft.Alignment(0, 0), end=ft.Alignment(0, 1),
                                    colors=["transparent", "#000000bb"],
                                ),
                            ),
                            ft.Container(
                                alignment=ft.Alignment(1, 1),
                                padding=10,
                                content=ft.Row(spacing=6, controls=[review_btn, play_btn]),
                            ),
                        ],
                    ),
                    ft.Container(
                        padding=ft.Padding(left=14, right=14, top=12, bottom=14),
                        content=ft.Column(spacing=4, controls=[
                            ft.Text(item.get("title") or item.get("name", "Sin título"), size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.GestureDetector(
                                on_tap=lambda _, n=artista_nombre: ir_artista(n, "/busqueda"),
                                content=ft.Text(artista_nombre, size=13, color="#C1CFEB",
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ),
                        ]),
                    ),
                ],
            ),
        ))

    def card_album(item):
        artista_obj = item.get("artist") or {}
        artistas = artista_obj.get("name", "Artista desconocido")
        primer_artista = artistas
        img = item.get("cover_medium", "")
        total_tracks = item.get("nb_tracks", "")
        year = (item.get("release_date") or "")[:4]

        def abrir_album(_):
            page.album_data = item
            page.album_origen = "/busqueda"
            page.run_task(page.push_route, "/vista_album")

        return ft.GestureDetector(
            on_tap=abrir_album,
            content=ft.Container(
                bgcolor="#122B46",
                border_radius=16,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                expand=True,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Stack(
                            controls=[
                                ft.Image(src=img, height=200, expand=True, fit=ft.BoxFit.COVER) if img
                                else ft.Container(height=200, bgcolor="#122B46",
                                                  content=ft.Icon(ft.Icons.ALBUM, color="#1C4F7A", size=64),
                                                  alignment=ft.Alignment(0, 0)),
                                ft.Container(
                                    height=200, expand=True,
                                    gradient=ft.LinearGradient(
                                        begin=ft.Alignment(0, 0), end=ft.Alignment(0, 1),
                                        colors=["transparent", "#000000bb"],
                                    ),
                                ),
                            ],
                        ),
                        ft.Container(
                            padding=ft.Padding(left=14, right=14, top=12, bottom=14),
                            content=ft.Column(spacing=4, controls=[
                                ft.Text(item.get("title") or item.get("name", "Sin título"), size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600,
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.GestureDetector(
                                    on_tap=lambda _, n=primer_artista: ir_artista(n, "/busqueda"),
                                    content=ft.Text(artistas, size=13, color="#C1CFEB",
                                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ),
                                ft.Text(
                                    f"{year}  ·  {total_tracks} canciones" if total_tracks else year,
                                    size=12, color="#7F90A8",
                                ),
                            ]),
                        ),
                    ],
                ),
            ),
        )

    def card_artist(item):
        img = item.get("picture_medium", "")
        seguidores = item.get("nb_fan", 0)

        def abrir(_):
            def _fetch():
                data = get_artist_details(item.get("id", ""))
                page.artista_data = data
                page.artista_origen = "/busqueda"
                page.run_task(page.push_route, "/perfil_artista")
            threading.Thread(target=_fetch, daemon=True).start()

        return ft.GestureDetector(
            on_tap=abrir,
            content=ft.Container(
                bgcolor="#122B46",
                border_radius=16,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                expand=True,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Stack(
                            controls=[
                                ft.Image(src=img, height=200, expand=True, fit=ft.BoxFit.COVER) if img
                                else ft.Container(height=200, bgcolor="#122B46",
                                                  content=ft.Icon(ft.Icons.PERSON, color="#1C4F7A", size=80),
                                                  alignment=ft.Alignment(0, 0)),
                                ft.Container(
                                    height=200, expand=True,
                                    gradient=ft.LinearGradient(
                                        begin=ft.Alignment(0, 0), end=ft.Alignment(0, 1),
                                        colors=["transparent", "#000000cc"],
                                    ),
                                ),
                            ],
                        ),
                        ft.Container(
                            padding=ft.Padding(left=14, right=14, top=12, bottom=14),
                            content=ft.Column(spacing=4, controls=[
                                ft.Text(item.get("name", ""), size=16, color=ft.Colors.WHITE, weight="bold",
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text("Artista", size=13, color="#A8B8CE"),
                            ]),
                        ),
                    ],
                ),
            ),
        )

    def hacer_busqueda(e):
        if not barra.value:
            return

        # Bloqueamos la barra para evitar múltiples búsquedas simultáneas
        barra.disabled = True
        resultados.controls = [
            ft.Container(
                content=ft.ProgressRing(width=30, height=30, stroke_width=3, color="#69A6FF"),
                padding=ft.Padding(top=50),
                alignment=ft.Alignment(0, 0)
            )
        ]
        page.update()

        def _buscar():
            try:
                query = barra.value
                tipo = filtro[0]
                items = buscar_deezer(query, tipo)
                
                new_controls = []
                if not items:
                    new_controls.append(ft.Text("Sin resultados", color="#A8B8CE"))
                elif tipo == "track":
                    new_controls = [card_track(i) for i in items]
                elif tipo == "album":
                    new_controls = [card_album(i) for i in items]
                else:
                    new_controls = [card_artist(i) for i in items]
                
                resultados.controls = new_controls
            except Exception as ex:
                print(f"Error en b\u00fasqueda: {ex}")
                resultados.controls = [ft.Text("Ocurri\u00f3 un error al buscar", color="#ff4444")]
            
            barra.disabled = False
            page.update()
        threading.Thread(target=_buscar, daemon=True).start()

    barra.on_submit = hacer_busqueda
    render_filtros()

    return ft.View(
        route="/busqueda",
        bgcolor="#08131F",
        padding=ft.Padding(left=20, right=20, top=20, bottom=20),
        controls=[
            ft.Stack(expand=True, controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.IconButton(icon=ft.Icons.MENU_ROUNDED, icon_color="#A8B8CE", on_click=abrir_sidebar),
                                ft.Text("Buscar", size=16, color=ft.Colors.WHITE, font_family="Audiowide"),
                                ft.Container(width=40),
                            ],
                        ),
                        ft.Container(height=20),
                        ft.Row(controls=[barra]),
                        ft.Container(height=10),
                        filtros_row,
                        ft.Container(height=10),
                        ft.Container(expand=True, content=resultados),
                    ],
                ),
                overlay,
                ft.Row(expand=True, spacing=0, controls=[sidebar_panel]),
            ])
        ],
    )