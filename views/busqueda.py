import flet as ft
import pygame
import requests
import threading
import io
from controllers.deezer import buscar_deezer
from controllers.deezer import get_artist_details

pygame.mixer.init()
reproduciendo = [None]


def BusquedaView(page: ft.Page):

    resultados = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
    filtro = ["track"]
    tipos = ["track", "album", "artist"]
    labels = ["Canciones", "Álbumes", "Artistas"]

    barra = ft.TextField(
        hint_text="Buscar canciones, álbumes, artistas...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=16,
        filled=True,
        fill_color="#111827",
        border_color="#1A2133",
        focused_border_color="#7C3AED",
        color=ft.Colors.WHITE,
        cursor_color=ft.Colors.WHITE,
        hint_style=ft.TextStyle(color="#888888"),
        expand=True,
    )

    def btn_filtro(label, tipo):
        activo = tipo == filtro[0]
        return ft.TextButton(
            label,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE if activo else "#888888",
                bgcolor="#7C3AED" if activo else "transparent",
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding(left=16, right=16, top=6, bottom=6),
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

    def card_track(item):
        artista_obj = item.get("artist") or {}
        artista_nombre = artista_obj.get("name", "Artista desconocido")
        album_obj = item.get("album") or {}
        img_big = album_obj.get("cover_big") or album_obj.get("cover_medium") or ""
        preview = item.get("preview", "")

        play_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color="#1DB954",
            icon_size=28,
            disabled=not preview,
        )
        if preview:
            play_btn.on_click = lambda _, u=preview, b=play_btn: play_preview(u, b)

        return ft.Container(
            bgcolor="#111827",
            border_radius=20,
            border=ft.Border.all(1, "#1A2133"),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=True,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Stack(
                        controls=[
                            ft.Image(src=img_big, height=140, width=400, fit=ft.BoxFit.COVER) if img_big
                            else ft.Container(height=140, bgcolor="#222222"),
                            ft.Container(
                                alignment=ft.Alignment(1, 1),
                                padding=8,
                                content=play_btn,
                            ),
                        ],
                    ),
                    ft.Container(
                        padding=ft.Padding(left=12, right=12, top=10, bottom=12),
                        content=ft.Column(spacing=3, controls=[
                            ft.Text(item.get("title") or item.get("name", "Sin título"), size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.GestureDetector(
                                on_tap=lambda _, n=artista_nombre: ir_artista(n, "/busqueda"),
                                content=ft.Text(artista_nombre, size=12, color="#b3b3b3",
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ),
                        ]),
                    ),
                ],
            ),
        )

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
                bgcolor="#1E212E",
                border_radius=16,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                expand=True,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Image(src=img, height=140, width=400, fit=ft.BoxFit.COVER) if img
                        else ft.Container(height=140, bgcolor="#222222",
                                          content=ft.Icon(ft.Icons.ALBUM, color="#444444", size=48),
                                          alignment=ft.Alignment(0, 0)),
                        ft.Container(
                            padding=ft.Padding(left=12, right=12, top=10, bottom=12),
                            content=ft.Column(spacing=3, controls=[
                                ft.Text(item.get("title") or item.get("name", "Sin título"), size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600,
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.GestureDetector(
                                    on_tap=lambda _, n=primer_artista: ir_artista(n, "/busqueda"),
                                    content=ft.Text(artistas, size=12, color="#b3b3b3",
                                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ),
                                ft.Text(
                                    f"{year}  ·  {total_tracks} canciones" if total_tracks else year,
                                    size=11, color="#777777",
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
                bgcolor="#1E212E",
                border_radius=16,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                expand=True,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Stack(
                            controls=[
                                ft.Image(src=img, height=140, width=400, fit=ft.BoxFit.COVER) if img
                                else ft.Container(height=140, bgcolor="#222222",
                                                  content=ft.Icon(ft.Icons.PERSON, color="#444444", size=56),
                                                  alignment=ft.Alignment(0, 0)),
                                ft.Container(
                                    height=140, expand=True,
                                    gradient=ft.LinearGradient(
                                        begin=ft.Alignment(0, 0), end=ft.Alignment(0, 1),
                                        colors=["transparent", "#000000cc"],
                                    ),
                                ),
                            ],
                        ),
                        ft.Container(
                            padding=ft.Padding(left=12, right=12, top=12, bottom=12),
                            content=ft.Column(spacing=2, controls=[
                                ft.Text(item.get("name", ""), size=14, color=ft.Colors.WHITE, weight="bold",
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text("Artista",
                                    size=12, color="#888888",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                ),
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
                content=ft.ProgressRing(width=30, height=30, stroke_width=3, color="#6C63FF"),
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
                    new_controls.append(ft.Text("Sin resultados", color="#888888"))
                elif tipo == "track":
                    for i in range(0, len(items), 2):
                        par = items[i:i + 2]
                        row_controls = [card_track(par[0])]
                        if len(par) == 2:
                            row_controls.append(card_track(par[1]))
                        else:
                            row_controls.append(ft.Container(expand=True))
                        new_controls.append(ft.Row(spacing=12, controls=row_controls))
                else:
                    fn = card_album if tipo == "album" else card_artist
                    for i in range(0, len(items), 2):
                        par = items[i:i + 2]
                        row_controls = [fn(par[0])]
                        if len(par) == 2:
                            row_controls.append(fn(par[1]))
                        else:
                            row_controls.append(ft.Container(expand=True))
                        new_controls.append(ft.Row(spacing=12, controls=row_controls))
                
                resultados.controls = new_controls
            except Exception as ex:
                print(f"Error en búsqueda: {ex}")
                resultados.controls = [ft.Text(f"Error: {ex}", color="#ff4444")]
            
            # Restauramos la interfaz
            barra.disabled = False
            page.update()
            # Verificamos que sigamos en la vista de búsqueda antes de forzar el update del contenedor
            if page.route == "/busqueda":
                resultados.update()

        threading.Thread(target=_buscar, daemon=True).start()

    barra.on_submit = hacer_busqueda
    render_filtros()

    return ft.View(
        route="/busqueda",
        bgcolor="#0F111A",
        padding=ft.Padding(left=20, right=20, top=20, bottom=20),
        controls=[
            ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="#888888",
                                on_click=lambda _: page.run_task(page.push_route, "/home"), icon_size=24),
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
        ],
    )