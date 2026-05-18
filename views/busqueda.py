import flet as ft
import pygame
import requests
import threading
import io
from controllers.deezer import buscar_deezer
from controllers.spotify import buscar as buscar_spotify, get_artist_full

pygame.mixer.init()
reproduciendo = [None]


def BusquedaView(page: ft.Page):

    resultados = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO)
    filtro = ["track"]
    tipos = ["track", "album", "artist"]
    labels = ["Canciones", "Álbumes", "Artistas"]

    barra = ft.TextField(
        hint_text="Buscar canciones, álbumes, artistas...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=30,
        filled=True,
        fill_color="#1a1a1a",
        border_color="#333333",
        focused_border_color="#ffffff",
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
                bgcolor="#333333" if activo else "transparent",
                shape=ft.RoundedRectangleBorder(radius=20),
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
            res = buscar_spotify(artista_nombre, "artist")
            if res:
                data = get_artist_full(res[0]["id"])
                page.artista_data = data if data else res[0]
            else:
                page.artista_data = {"name": artista_nombre, "images": [], "genres": [], "followers": {"total": 0}, "popularity": 0, "id": ""}
            page.artista_origen = origen
            page.run_task(page.push_route, "/perfil_artista")
        threading.Thread(target=_buscar, daemon=True).start()

    def card_track(item):
        artista_nombre = item.get("artist", {}).get("name", "")
        img_big = item.get("album", {}).get("cover_xl", "") or item.get("album", {}).get("cover_medium", "")
        preview = item.get("preview", "")

        play_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color="#1DB954",
            icon_size=28,
            disabled=not preview,
            style=ft.ButtonStyle(bgcolor="#00000088"),
        )
        if preview:
            play_btn.on_click = lambda _, u=preview, b=play_btn: play_preview(u, b)

        return ft.Container(
            bgcolor="#1a1a1a",
            border_radius=14,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=True,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Stack(
                        controls=[
                            ft.Image(src=img_big, width=float("inf"), height=160, fit=ft.BoxFit.COVER, expand=True) if img_big
                            else ft.Container(height=160, bgcolor="#333333", expand=True),
                            ft.Container(
                                alignment=ft.Alignment(1, 1),
                                padding=6,
                                content=play_btn,
                            ),
                        ],
                    ),
                    ft.Container(
                        padding=ft.Padding(left=10, right=10, top=8, bottom=10),
                        content=ft.Column(spacing=3, controls=[
                            ft.Text(item["title"], size=13, color=ft.Colors.WHITE, weight="bold",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.GestureDetector(
                                on_tap=lambda _, n=artista_nombre: ir_artista(n, "/busqueda"),
                                content=ft.Text(artista_nombre, size=11, color="#1DB954",
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ),
                        ]),
                    ),
                ],
            ),
        )

    def card_album(item):
        artistas = ", ".join(a["name"] for a in item.get("artists", []))
        primer_artista = item.get("artists", [{}])[0].get("name", "")
        img = (item.get("images") or [{}])[0].get("url", "")
        total_tracks = item.get("total_tracks", "")
        year = (item.get("release_date") or "")[:4]

        def abrir_album(_):
            page.album_data = item
            page.album_origen = "/busqueda"
            page.run_task(page.push_route, "/vista_album")

        return ft.GestureDetector(
            on_tap=abrir_album,
            content=ft.Container(
                bgcolor="#1a1a1a",
                border_radius=14,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                expand=True,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Image(src=img, height=160, fit=ft.BoxFit.COVER, expand=True) if img
                        else ft.Container(height=160, bgcolor="#333333", expand=True,
                                          content=ft.Icon(ft.Icons.ALBUM, color="#555555", size=48),
                                          alignment=ft.Alignment(0, 0)),
                        ft.Container(
                            padding=ft.Padding(left=10, right=10, top=8, bottom=10),
                            content=ft.Column(spacing=3, controls=[
                                ft.Text(item["name"], size=13, color=ft.Colors.WHITE, weight="bold",
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.GestureDetector(
                                    on_tap=lambda _, n=primer_artista: ir_artista(n, "/busqueda"),
                                    content=ft.Text(artistas, size=11, color="#1DB954",
                                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ),
                                ft.Text(
                                    f"{year}  ·  {total_tracks} canciones" if total_tracks else year,
                                    size=10, color="#666666",
                                ),
                            ]),
                        ),
                    ],
                ),
            ),
        )

    def card_artist(item):
        img = (item.get("images") or [{}])[0].get("url", "")
        generos = item.get("genres", [])
        seguidores = item.get("followers", {}).get("total", 0)

        def abrir(_):
            def _fetch():
                data = get_artist_full(item["id"])
                page.artista_data = data if data else item
                page.artista_origen = "/busqueda"
                page.run_task(page.push_route, "/perfil_artista")
            threading.Thread(target=_fetch, daemon=True).start()

        return ft.GestureDetector(
            on_tap=abrir,
            content=ft.Container(
                bgcolor="#1a1a1a",
                border_radius=14,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                expand=True,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Stack(
                            controls=[
                                ft.Image(src=img, height=160, fit=ft.BoxFit.COVER, expand=True) if img
                                else ft.Container(height=160, bgcolor="#333333", expand=True,
                                                  content=ft.Icon(ft.Icons.PERSON, color="#555555", size=56),
                                                  alignment=ft.Alignment(0, 0)),
                                ft.Container(
                                    height=160,
                                    gradient=ft.LinearGradient(
                                        begin=ft.Alignment(0, 0),
                                        end=ft.Alignment(0, 1),
                                        colors=["transparent", "#000000cc"],
                                    ),
                                    expand=True,
                                ),
                            ],
                        ),
                        ft.Container(
                            padding=ft.Padding(left=10, right=10, top=8, bottom=10),
                            content=ft.Column(spacing=3, controls=[
                                ft.Text(item["name"], size=13, color=ft.Colors.WHITE, weight="bold",
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(
                                    generos[0].capitalize() if generos else "Artista",
                                    size=11, color="#888888",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(f"{seguidores:,} seguidores", size=10, color="#666666"),
                            ]),
                        ),
                    ],
                ),
            ),
        )

    def hacer_busqueda(e):
        if not barra.value:
            return
        resultados.controls = [ft.ProgressRing(width=20, height=20, stroke_width=2, color="#888888")]
        page.update()

        if filtro[0] == "track":
            items = buscar_deezer(barra.value)
        else:
            items = buscar_spotify(barra.value, filtro[0])

        resultados.controls.clear()
        if not items:
            resultados.controls.append(ft.Text("Sin resultados", color="#888888"))
        elif filtro[0] == "track":
            for i in range(0, len(items), 2):
                par = items[i:i + 2]
                row_controls = [card_track(par[0])]
                if len(par) == 2:
                    row_controls.append(card_track(par[1]))
                else:
                    row_controls.append(ft.Container(expand=True))
                resultados.controls.append(ft.Row(spacing=12, controls=row_controls))
        else:
            fn = card_album if filtro[0] == "album" else card_artist
            for i in range(0, len(items), 2):
                par = items[i:i + 2]
                row_controls = [fn(par[0])]
                if len(par) == 2:
                    row_controls.append(fn(par[1]))
                else:
                    row_controls.append(ft.Container(expand=True))
                resultados.controls.append(ft.Row(spacing=12, controls=row_controls))
        page.update()

    barra.on_submit = hacer_busqueda
    render_filtros()

    return ft.View(
        route="/busqueda",
        bgcolor="#0a0a0a",
        padding=ft.Padding(left=20, right=20, top=20, bottom=20),
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="#888888",
                        on_click=lambda _: page.run_task(page.push_route, "/home")),
                    ft.Text("Buscar", size=16, color=ft.Colors.WHITE, font_family="Audiowide"),
                    ft.Container(width=40),
                ],
            ),
            ft.Container(height=10),
            ft.Row(controls=[barra]),
            ft.Container(height=8),
            filtros_row,
            ft.Container(height=10),
            ft.Container(expand=True, content=resultados),
        ],
    )
