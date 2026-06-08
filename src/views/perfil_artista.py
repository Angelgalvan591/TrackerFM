import flet as ft
import pygame
import requests
import threading
import io
from src.controllers.deezer import get_artist_top_tracks, get_artist_albums, get_artist_details, get_album_details

reproduciendo = [None]


def PerfilArtistaView(page: ft.Page):
    artista = getattr(page, "artista_data", {})
    origen = getattr(page, "artista_origen", "/busqueda")
    artist_id = artista.get("id", "") # Ensure artist_id is taken from the Deezer-compatible artista_data

    # placeholders que se llenan en background
    nombre_ref   = [artista.get("name", "Artista")] # 'name' is consistent for Deezer artist search results
    img_ref      = [artista.get("picture_medium", "")] # Use Deezer's picture_medium
    seg_ref      = [artista.get("nb_fan", 0)] # Use Deezer's nb_fan
    pop_ref      = [artista.get("rank", 0)] # Use Deezer's rank as a proxy, not 0-100
    generos_ref  = [[g.get("name") for g in artista.get("genres", {}).get("data", [])] if artista.get("genres") else []] # Deezer genres are nested

    discografia_row = ft.Row(spacing=10, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(width=60, height=130, alignment=ft.Alignment(0, 0),
                     content=ft.ProgressRing(width=20, height=20, stroke_width=2, color="#69A6FF"))
    ])
    tracks_col = ft.Column(spacing=8, controls=[
        ft.Container(padding=ft.Padding(left=0, right=0, top=8, bottom=0),
                     alignment=ft.Alignment(0, 0),
                     content=ft.ProgressRing(width=20, height=20, stroke_width=2, color="#69A6FF"))
    ])

    seg_text  = ft.Text(f"{seg_ref[0]:,} seguidores", size=12, color="#B2C0D9")
    pop_bar   = ft.ProgressBar(value=pop_ref[0] / 100 if pop_ref[0] else 0,
                               bgcolor="#122B46", color="#69A6FF", height=4, border_radius=2)
    pop_label = ft.Text(f"{pop_ref[0]}/100", size=12, color="#A8B8CE")
    generos_wrap = ft.Row(wrap=True, spacing=6, controls=[])

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

    def track_row(i, track):
        preview   = track.get("preview", "") or track.get("preview_url", "")
        track_img = track.get("album", {}).get("cover_medium", "")
        play_btn  = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE, icon_color="#69A6FF", icon_size=24,
            disabled=not preview,
        )
        if preview:
            play_btn.on_click = lambda _, u=preview, b=play_btn: play_preview(u, b)

        return ft.Container(
            padding=ft.Padding(left=12, right=8, top=10, bottom=10),
            border_radius=16, bgcolor="#122B46",
            content=ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text(str(i), size=12, color="#7F90A8", width=20, text_align=ft.TextAlign.CENTER),
                ft.Image(src=track_img, width=48, height=48, border_radius=6, fit=ft.BoxFit.COVER) if track_img
                else ft.Container(width=48, height=48, bgcolor="#122B46", border_radius=6,
                                  content=ft.Icon(ft.Icons.MUSIC_NOTE, color="#1C4F7A", size=24),
                                  alignment=ft.Alignment(0, 0)),
                ft.Column(spacing=2, expand=True, controls=[
                    ft.Text(track.get("title", ""), size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(track.get("album", {}).get("title", ""), size=12, color="#C1CFEB",
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ]),
                play_btn,
            ]),
        )

    def card_album(album):
        alb_img = album.get("cover_medium", "")
        year    = (album.get("release_date") or album.get("release_date_start") or "")[:4]
        tipo    = album.get("record_type", "album").capitalize()

        def abrir(_):
            def _fetch_album_details():
                full_album_data = get_album_details(album.get("id"))
                if full_album_data:
                    page.album_data = {
                        "id": full_album_data.get("id"),
                        "name": full_album_data.get("title"),
                        "images": [{"url": full_album_data.get("cover_xl") or full_album_data.get("cover_big") or full_album_data.get("cover_medium")}] if full_album_data.get("cover_medium") else [],
                        "artists": [{"name": full_album_data.get("artist", {}).get("name", "")}],
                        "release_date": full_album_data.get("release_date"),
                        "total_tracks": full_album_data.get("nb_tracks"),
                    }
                else:
                    page.album_data = {
                        "id": album.get("id"), "name": album.get("title"),
                        "images": [{"url": album.get("cover_medium")}] if album.get("cover_medium") else [],
                        "artists": [{"name": album.get("artist", {}).get("name", "")}],
                        "release_date": album.get("release_date") or album.get("release_date_start"), "total_tracks": album.get("nb_tracks"),
                    }
                page.album_origen = "/perfil_artista"
                page.run_task(page.push_route, "/vista_album")
            threading.Thread(target=_fetch_album_details, daemon=True).start()

        return ft.GestureDetector(
            on_tap=abrir,
            content=ft.Container(
                bgcolor="#122B46", border_radius=16,
                clip_behavior=ft.ClipBehavior.HARD_EDGE, width=130,
                content=ft.Column(spacing=0, controls=[
                    ft.Image(src=alb_img, width=130, height=130, fit=ft.BoxFit.COVER) if alb_img
                    else ft.Container(width=130, height=130, bgcolor="#122B46",
                                      content=ft.Icon(ft.Icons.ALBUM, color="#1C4F7A", size=40),
                                      alignment=ft.Alignment(0, 0)),
                    ft.Container(
                        padding=ft.Padding(left=8, right=8, top=6, bottom=8),
                        content=ft.Column(spacing=2, controls=[
                            ft.Text(album.get("title", ""), size=12, color=ft.Colors.WHITE, weight="bold",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"{tipo}  ·  {year}", size=10, color="#6B7A8F"),
                        ]),
                    ),
                ]),
            ),
        )

    def cargar():
        # si el objeto no tiene followers reales, traer full
        data = artista
        if artist_id and not artista.get("nb_fan"): # Deezer uses nb_fan
            full = get_artist_details(artist_id)
            if full:
                data = full

        seg_ref[0]     = data.get("nb_fan", 0)
        pop_ref[0]     = data.get("rank", 0) # Deezer rank is not 0-100
        generos_ref[0] = [g.get("name") for g in data.get("genres", {}).get("data", [])] if data.get("genres") else []

        seg_text.value  = f"{seg_ref[0]:,} seguidores"
        pop_bar.value   = 0 # No direct popularity equivalent, set to 0
        pop_label.value = "N/A" # No direct popularity equivalent, set to N/A
        generos_wrap.controls = [
            ft.Container(
                padding=ft.Padding(left=14, right=14, top=6, bottom=6),
                border_radius=20, bgcolor="#122B46",
                content=ft.Text(g, size=11, color="#D5E0F5"),
            ) for g in generos_ref[0][:6]
        ]

        albums     = get_artist_albums(artist_id) if artist_id else []
        top_tracks = get_artist_top_tracks(artist_id) if artist_id else []

        discografia_row.controls = [card_album(a) for a in albums] if albums else [
            ft.Text("Sin discografía disponible", size=12, color="#6B7A8F")
        ]
        tracks_col.controls = [track_row(i + 1, t) for i, t in enumerate(top_tracks)] if top_tracks else [
            ft.Text("Sin canciones disponibles", size=12, color="#6B7A8F")
        ]
        page.update()

    threading.Thread(target=cargar, daemon=True).start()

    img = img_ref[0]
    nombre = nombre_ref[0]

    header = ft.Stack(
        height=280,
        controls=[
            ft.Container(
                expand=True, height=280,
                image=ft.DecorationImage(src=img, fit=ft.BoxFit.COVER) if img else None,
                bgcolor="#10243C" if not img else None,
                content=ft.Icon(ft.Icons.PERSON, color="#2B5F81", size=80) if not img else None,
                alignment=ft.Alignment(0, 0),
            ),
            ft.Container(
                expand=True, height=280,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                    colors=["#00000066", "transparent", "#08131F"],
                ),
            ),
            ft.Container(
                alignment=ft.Alignment(-1, 1),
                padding=ft.Padding(left=20, right=20, top=0, bottom=20),
                content=ft.Column(spacing=4, controls=[
                    ft.Text(nombre, size=32, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    seg_text,
                ]),
            ),
        ],
    )

    body = ft.Container(
        padding=ft.Padding(left=20, right=20, top=16, bottom=20),
        content=ft.Column(spacing=16, controls=[
            generos_wrap,
            ft.Column(spacing=4, controls=[
                ft.Row(controls=[
                    ft.Text("Popularidad", size=12, color="#A8B8CE", expand=True),
                    pop_label,
                ]),
                pop_bar,
            ]),
            ft.Text("Discografía", size=15, color=ft.Colors.WHITE, weight="bold"),
            discografia_row,
            ft.Text("Top canciones", size=15, color=ft.Colors.WHITE, weight="bold"),
            tracks_col,
        ]),
    )

    return ft.View(
        route="/perfil_artista", bgcolor="#08131F", padding=0,
        controls=[
            ft.Stack(expand=True, controls=[
                ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, controls=[header, body]),
                ft.Container(
                    padding=ft.Padding(left=8, right=0, top=12, bottom=0),
                    content=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE,
                        bgcolor="#00000066",
                        on_click=lambda _: page.run_task(page.push_route, origen),
                    ),
                ),
            ]),
        ],
    )