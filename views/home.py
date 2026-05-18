import flet as ft
import threading
import requests
import pygame
import io
from controllers.deezer import get_chart_tracks, get_chart_albums, get_chart_artists
from controllers.spotify import buscar as buscar_spotify, get_artist_full
from database.db import get_connection

reproduciendo = [None]


def _get_ultima_resena(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT r.rating, r.review_text, r.created_at,
                   a.id as album_id, a.title as album_title, a.cover_url,
                   ar.name as artist_name
            FROM reviews r
            JOIN albums a ON r.album_id = a.id
            LEFT JOIN artists ar ON a.artist_id = ar.id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception:
        return None


def HomeView(page: ft.Page):

    sidebar_open = [False]

    def ir(ruta):
        cerrar_sidebar(None)
        page.run_task(page.push_route, ruta)

    async def cerrar_sesion(e):
        page.user_id = None
        page.borrar_sesion()
        await page.push_route("/")

    # ── sidebar ────────────────────────────────────────────────────────────
    overlay = ft.GestureDetector(
        visible=False, expand=True,
        on_tap=lambda _: cerrar_sidebar(None),
        content=ft.Container(expand=True, bgcolor="#00000099"),
    )

    def nav_item(icon, label, ruta):
        return ft.TextButton(
            content=ft.Row(spacing=14, controls=[
                ft.Icon(icon, color="#cccccc", size=20),
                ft.Text(label, size=14, color="#cccccc"),
            ]),
            style=ft.ButtonStyle(
                overlay_color="#ffffff11",
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(left=16, right=16, top=12, bottom=12),
            ),
            on_click=lambda _, r=ruta: ir(r),
        )

    sidebar_panel = ft.Container(
        visible=False, width=240, bgcolor="#111111",
        content=ft.Column(spacing=0, controls=[
            ft.Container(
                height=100, bgcolor="#1a1a1a",
                padding=ft.Padding(left=20, right=20, top=40, bottom=16),
                content=ft.Text("TRACKER FM", size=16, color=ft.Colors.WHITE,
                                font_family="Audiowide", weight="bold"),
            ),
            ft.Container(height=8),
            ft.Container(
                padding=ft.Padding(left=12, right=12, top=0, bottom=0),
                content=ft.Column(spacing=4, controls=[
                    nav_item(ft.Icons.HOME_OUTLINED,  "Inicio",    "/home"),
                    nav_item(ft.Icons.SEARCH,         "Buscar",    "/busqueda"),
                    nav_item(ft.Icons.PEOPLE_OUTLINE, "Usuarios",  "/usuarios"),
                    nav_item(ft.Icons.PERSON_OUTLINE, "Mi perfil", "/perfil"),
                ]),
            ),
            ft.Container(expand=True),
            ft.Container(
                padding=ft.Padding(left=12, right=12, top=0, bottom=24),
                content=ft.TextButton(
                    content=ft.Row(spacing=14, controls=[
                        ft.Icon(ft.Icons.LOGOUT, color="#888888", size=20),
                        ft.Text("Cerrar sesión", size=14, color="#888888"),
                    ]),
                    style=ft.ButtonStyle(
                        overlay_color="#ffffff11",
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding(left=16, right=16, top=12, bottom=12),
                    ),
                    on_click=cerrar_sesion,
                ),
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

    # ── play preview ───────────────────────────────────────────────────────
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

    def ir_artista(nombre_artista):
        def _fetch():
            res = buscar_spotify(nombre_artista, "artist")
            if res:
                data = get_artist_full(res[0]["id"])
                page.artista_data = data if data else res[0]
            else:
                page.artista_data = {"name": nombre_artista, "images": [], "genres": [],
                                     "followers": {"total": 0}, "popularity": 0, "id": ""}
            page.artista_origen = "/home"
            page.run_task(page.push_route, "/perfil_artista")
        threading.Thread(target=_fetch, daemon=True).start()

    # ── cards ──────────────────────────────────────────────────────────────
    def track_card(item):
        img_xl = item.get("album", {}).get("cover_xl", "") or item.get("album", {}).get("cover_medium", "")
        artista = item.get("artist", {}).get("name", "")
        preview = item.get("preview", "")
        play_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE, icon_color="#1DB954", icon_size=26,
            disabled=not preview, style=ft.ButtonStyle(bgcolor="#00000088"),
        )
        if preview:
            play_btn.on_click = lambda _, u=preview, b=play_btn: play_preview(u, b)
        return ft.Container(
            width=140, bgcolor="#1a1a1a", border_radius=12,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(spacing=0, controls=[
                ft.Stack(controls=[
                    ft.Image(src=img_xl, width=140, height=140, fit=ft.BoxFit.COVER) if img_xl
                    else ft.Container(width=140, height=140, bgcolor="#333333"),
                    ft.Container(alignment=ft.Alignment(1, 1), padding=6, content=play_btn),
                ]),
                ft.Container(
                    padding=ft.Padding(left=10, right=10, top=8, bottom=10),
                    content=ft.Column(spacing=2, controls=[
                        ft.Text(item["title"], size=12, color=ft.Colors.WHITE, weight="bold",
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.GestureDetector(
                            on_tap=lambda _, n=artista: ir_artista(n),
                            content=ft.Text(artista, size=11, color="#1DB954",
                                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ),
                    ]),
                ),
            ]),
        )

    def album_card(item):
        img_xl = item.get("cover_xl", "") or item.get("cover_medium", "")
        artista = item.get("artist", {}).get("name", "")

        def abrir_album(_):
            page.album_data = {
                "id": "", "name": item.get("title", ""),
                "images": [{"url": img_xl}] if img_xl else [],
                "artists": [{"name": artista}],
                "release_date": str(item.get("release_date", "")),
                "total_tracks": item.get("nb_tracks", ""),
            }
            def _fetch():
                res = buscar_spotify(f"{item.get('title', '')} {artista}", "album")
                if res:
                    page.album_data = res[0]
                page.album_origen = "/home"
                page.run_task(page.push_route, "/vista_album")
            threading.Thread(target=_fetch, daemon=True).start()

        return ft.GestureDetector(
            on_tap=abrir_album,
            content=ft.Container(
                width=140, bgcolor="#1a1a1a", border_radius=12,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Column(spacing=0, controls=[
                    ft.Image(src=img_xl, width=140, height=140, fit=ft.BoxFit.COVER) if img_xl
                    else ft.Container(width=140, height=140, bgcolor="#333333",
                                      content=ft.Icon(ft.Icons.ALBUM, color="#555555", size=40),
                                      alignment=ft.Alignment(0, 0)),
                    ft.Container(
                        padding=ft.Padding(left=10, right=10, top=8, bottom=10),
                        content=ft.Column(spacing=2, controls=[
                            ft.Text(item.get("title", ""), size=12, color=ft.Colors.WHITE, weight="bold",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(artista, size=11, color="#888888",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ]),
                    ),
                ]),
            ),
        )

    def artist_card(item):
        img = item.get("picture_medium", "")
        nombre = item.get("name", "")
        return ft.GestureDetector(
            on_tap=lambda _: ir_artista(nombre),
            content=ft.Container(
                width=120, bgcolor="#1a1a1a", border_radius=12,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Stack(controls=[
                        ft.Image(src=img, width=120, height=120, fit=ft.BoxFit.COVER) if img
                        else ft.Container(width=120, height=120, bgcolor="#333333",
                                          content=ft.Icon(ft.Icons.PERSON, color="#555555", size=44),
                                          alignment=ft.Alignment(0, 0)),
                        ft.Container(width=120, height=120, gradient=ft.LinearGradient(
                            begin=ft.Alignment(0, 0), end=ft.Alignment(0, 1),
                            colors=["transparent", "#000000bb"],
                        )),
                    ]),
                    ft.Container(
                        padding=ft.Padding(left=8, right=8, top=8, bottom=10),
                        content=ft.Text(nombre, size=12, color=ft.Colors.WHITE, weight="bold",
                                        text_align=ft.TextAlign.CENTER,
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ),
                ]),
            ),
        )

    def seccion(titulo, row_ctrl):
        return ft.Column(spacing=10, controls=[
            ft.Text(titulo, size=15, color=ft.Colors.WHITE, weight="bold"),
            ft.Row(scroll=ft.ScrollMode.AUTO, spacing=10, controls=[row_ctrl]),
        ])

    def spinner():
        return ft.Container(width=60, height=140, alignment=ft.Alignment(0, 0),
                            content=ft.ProgressRing(width=22, height=22, stroke_width=2, color="#1DB954"))

    # ── placeholders ───────────────────────────────────────────────────────
    tracks_row  = ft.Row(spacing=10, controls=[spinner()])
    albums_row  = ft.Row(spacing=10, controls=[spinner()])
    artists_row = ft.Row(spacing=10, controls=[spinner()])

    featured_container = ft.Container(
        height=180, border_radius=16, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        bgcolor="#1a1a1a",
        content=ft.Container(expand=True, bgcolor="#222222",
                             content=ft.ProgressRing(width=24, height=24, stroke_width=2, color="#1DB954"),
                             alignment=ft.Alignment(0, 0)),
    )

    resena_container = ft.Container()  # se llena en el thread

    # ── carga única en background ──────────────────────────────────────────
    def cargar_todo():
        tracks  = get_chart_tracks(10)
        albums  = get_chart_albums(10)
        artists = get_chart_artists(10)

        # banner
        if tracks:
            t = tracks[0]
            img = t.get("album", {}).get("cover_xl", "") or t.get("album", {}).get("cover_medium", "")
            artista_b = t.get("artist", {}).get("name", "")
            preview_b = t.get("preview", "")
            play_btn_b = ft.IconButton(
                icon=ft.Icons.PLAY_CIRCLE_OUTLINE, icon_color=ft.Colors.WHITE, icon_size=36,
                style=ft.ButtonStyle(bgcolor="#00000066"),
            )
            if preview_b:
                play_btn_b.on_click = lambda _, u=preview_b, b=play_btn_b: play_preview(u, b)
            featured_container.content = ft.Stack(controls=[
                ft.Image(src=img, width=390, height=180, fit=ft.BoxFit.COVER) if img
                else ft.Container(expand=True, bgcolor="#222222"),
                ft.Container(expand=True, gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0),
                    colors=["#000000cc", "transparent"],
                )),
                ft.Container(
                    expand=True,
                    padding=ft.Padding(left=16, right=16, top=0, bottom=16),
                    alignment=ft.Alignment(-1, 1),
                    content=ft.Row(vertical_alignment=ft.CrossAxisAlignment.END, controls=[
                        ft.Column(spacing=3, expand=True, controls=[
                            ft.Container(
                                padding=ft.Padding(left=8, right=8, top=3, bottom=3),
                                border_radius=20, bgcolor="#1DB954",
                                content=ft.Text("TRENDING #1", size=9, color=ft.Colors.BLACK, weight="bold"),
                            ),
                            ft.Text(t["title"], size=16, color=ft.Colors.WHITE, weight="bold",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.GestureDetector(
                                on_tap=lambda _, n=artista_b: ir_artista(n),
                                content=ft.Text(artista_b, size=12, color="#cccccc",
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ),
                        ]),
                        play_btn_b,
                    ]),
                ),
            ])

        tracks_row.controls  = [track_card(t) for t in tracks]  or [ft.Text("—", color="#666")]
        albums_row.controls  = [album_card(a) for a in albums]  or [ft.Text("—", color="#666")]
        artists_row.controls = [artist_card(a) for a in artists] or [ft.Text("—", color="#666")]

        # última reseña
        resena = _get_ultima_resena(page.user_id)
        if resena:
            estrellas = "★" * int(resena["rating"]) + "☆" * (5 - int(resena["rating"]))
            resena_container.content = ft.Container(
                bgcolor="#1a1a1a", border_radius=14,
                padding=ft.Padding(left=14, right=14, top=14, bottom=14),
                content=ft.Row(spacing=14, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                    ft.Image(src=resena["cover_url"], width=70, height=70, border_radius=8,
                             fit=ft.BoxFit.COVER) if resena.get("cover_url")
                    else ft.Container(width=70, height=70, bgcolor="#333333", border_radius=8,
                                      content=ft.Icon(ft.Icons.ALBUM, color="#555555", size=28),
                                      alignment=ft.Alignment(0, 0)),
                    ft.Column(spacing=4, expand=True, controls=[
                        ft.Text(resena["album_title"], size=13, color=ft.Colors.WHITE, weight="bold",
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(resena.get("artist_name", ""), size=11, color="#1DB954",
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(estrellas, size=13, color="#f5c518"),
                        ft.Text(resena.get("review_text", ""), size=11, color="#aaaaaa",
                                max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ]),
                ]),
            )
        else:
            resena_container.content = ft.Container(
                bgcolor="#1a1a1a", border_radius=14,
                padding=ft.Padding(left=14, right=14, top=14, bottom=14),
                content=ft.Text("Aún no has reseñado ningún álbum", size=12, color="#666666"),
            )

        page.update()

    threading.Thread(target=cargar_todo, daemon=True).start()

    # ── top bar ────────────────────────────────────────────────────────────
    top_bar = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.IconButton(icon=ft.Icons.MENU, icon_color=ft.Colors.WHITE, on_click=abrir_sidebar),
            ft.Text("TRACKER FM", size=16, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
            ft.IconButton(icon=ft.Icons.SEARCH, icon_color="#888888",
                          on_click=lambda _: page.run_task(page.push_route, "/busqueda")),
        ],
    )

    body = ft.Column(
        expand=True, scroll=ft.ScrollMode.AUTO, spacing=24,
        controls=[
            featured_container,
            ft.Column(spacing=8, controls=[
                ft.Text("Tu última reseña", size=15, color=ft.Colors.WHITE, weight="bold"),
                resena_container,
            ]),
            seccion("🔥 Trending ahora", tracks_row),
            seccion("💿 Álbumes populares", albums_row),
            seccion("🎤 Artistas del momento", artists_row),
            ft.Container(height=8),
        ],
    )

    return ft.View(
        route="/home", bgcolor="#0a0a0a", padding=0,
        controls=[
            ft.Stack(expand=True, controls=[
                ft.Column(expand=True, spacing=0, controls=[
                    ft.Container(padding=ft.Padding(left=16, right=16, top=20, bottom=12), content=top_bar),
                    ft.Container(expand=True, padding=ft.Padding(left=16, right=16, top=0, bottom=0), content=body),
                ]),
                overlay,
                ft.Row(expand=True, spacing=0, controls=[sidebar_panel]),
            ]),
        ],
    )
