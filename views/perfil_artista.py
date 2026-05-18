import flet as ft
import pygame
import requests
import threading
import io
from controllers.spotify import get_artist_top_tracks, get_artist_albums, get_artist_full

reproduciendo = [None]


def PerfilArtistaView(page: ft.Page):
    artista = getattr(page, "artista_data", {})
    artist_id = artista.get("id", "")
    origen = getattr(page, "artista_origen", "/busqueda")

    # placeholders que se llenan en background
    nombre_ref   = [artista.get("name", "Artista")]
    img_ref      = [(artista.get("images") or [{}])[0].get("url", "")]
    seg_ref      = [artista.get("followers", {}).get("total", 0)]
    pop_ref      = [artista.get("popularity", 0)]
    generos_ref  = [artista.get("genres", [])]

    discografia_row = ft.Row(spacing=10, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(width=60, height=130, alignment=ft.Alignment(0, 0),
                     content=ft.ProgressRing(width=20, height=20, stroke_width=2, color="#1DB954"))
    ])
    tracks_col = ft.Column(spacing=8, controls=[
        ft.Container(padding=ft.Padding(left=0, right=0, top=8, bottom=0),
                     alignment=ft.Alignment(0, 0),
                     content=ft.ProgressRing(width=20, height=20, stroke_width=2, color="#1DB954"))
    ])

    seg_text  = ft.Text(f"{seg_ref[0]:,} seguidores", size=12, color="#aaaaaa")
    pop_bar   = ft.ProgressBar(value=pop_ref[0] / 100 if pop_ref[0] else 0,
                               bgcolor="#222222", color="#1DB954", height=4, border_radius=2)
    pop_label = ft.Text(f"{pop_ref[0]}/100", size=12, color="#888888")
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
        preview   = track.get("preview_url", "")
        track_img = (track.get("album", {}).get("images") or [{}])[0].get("url", "")
        play_btn  = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE, icon_color="#1DB954", icon_size=24,
            disabled=not preview,
        )
        if preview:
            play_btn.on_click = lambda _, u=preview, b=play_btn: play_preview(u, b)
        return ft.Container(
            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
            border_radius=10, bgcolor="#1a1a1a",
            content=ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text(str(i), size=13, color="#555555", width=18),
                ft.Image(src=track_img, width=42, height=42, border_radius=6, fit=ft.BoxFit.COVER) if track_img
                else ft.Container(width=42, height=42, bgcolor="#333333", border_radius=6),
                ft.Column(spacing=2, expand=True, controls=[
                    ft.Text(track["name"], size=13, color=ft.Colors.WHITE,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(track.get("album", {}).get("name", ""), size=11, color="#888888",
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ]),
                play_btn,
            ]),
        )

    def card_album(album):
        alb_img = (album.get("images") or [{}])[0].get("url", "")
        year    = (album.get("release_date") or "")[:4]
        tipo    = album.get("album_type", "album").capitalize()

        def abrir(_):
            page.album_data   = album
            page.album_origen = "/perfil_artista"
            page.run_task(page.push_route, "/vista_album")

        return ft.GestureDetector(
            on_tap=abrir,
            content=ft.Container(
                bgcolor="#1a1a1a", border_radius=12,
                clip_behavior=ft.ClipBehavior.HARD_EDGE, width=130,
                content=ft.Column(spacing=0, controls=[
                    ft.Image(src=alb_img, width=130, height=130, fit=ft.BoxFit.COVER) if alb_img
                    else ft.Container(width=130, height=130, bgcolor="#333333",
                                      content=ft.Icon(ft.Icons.ALBUM, color="#555555", size=40),
                                      alignment=ft.Alignment(0, 0)),
                    ft.Container(
                        padding=ft.Padding(left=8, right=8, top=6, bottom=8),
                        content=ft.Column(spacing=2, controls=[
                            ft.Text(album["name"], size=12, color=ft.Colors.WHITE, weight="bold",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"{tipo}  ·  {year}", size=10, color="#666666"),
                        ]),
                    ),
                ]),
            ),
        )

    def cargar():
        # si el objeto no tiene followers reales, traer full
        data = artista
        if artist_id and not artista.get("followers", {}).get("total"):
            full = get_artist_full(artist_id)
            if full:
                data = full

        seg_ref[0]     = data.get("followers", {}).get("total", 0)
        pop_ref[0]     = data.get("popularity", 0)
        generos_ref[0] = data.get("genres", [])

        seg_text.value  = f"{seg_ref[0]:,} seguidores"
        pop_bar.value   = pop_ref[0] / 100
        pop_label.value = f"{pop_ref[0]}/100"
        generos_wrap.controls = [
            ft.Container(
                padding=ft.Padding(left=12, right=12, top=4, bottom=4),
                border_radius=20, bgcolor="#222222",
                content=ft.Text(g, size=11, color="#cccccc"),
            ) for g in generos_ref[0][:6]
        ]

        albums     = get_artist_albums(artist_id) if artist_id else []
        top_tracks = get_artist_top_tracks(artist_id) if artist_id else []

        discografia_row.controls = [card_album(a) for a in albums] if albums else [
            ft.Text("Sin discografía disponible", size=12, color="#666666")
        ]
        tracks_col.controls = [track_row(i + 1, t) for i, t in enumerate(top_tracks)] if top_tracks else [
            ft.Text("Sin canciones disponibles", size=12, color="#666666")
        ]
        page.update()

    threading.Thread(target=cargar, daemon=True).start()

    img = img_ref[0]
    nombre = nombre_ref[0]

    header = ft.Stack(
        height=220,
        controls=[
            ft.Image(src=img, width=390, height=220, fit=ft.BoxFit.COVER) if img
            else ft.Container(width=390, height=220, bgcolor="#1a1a1a"),
            ft.Container(
                width=390, height=220,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                    colors=["transparent", "#0a0a0a"],
                ),
            ),
            ft.Container(
                alignment=ft.Alignment(-1, 1),
                padding=ft.Padding(left=20, right=20, top=0, bottom=16),
                content=ft.Column(spacing=4, controls=[
                    ft.Text(nombre, size=26, color=ft.Colors.WHITE, weight="bold"),
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
                    ft.Text("Popularidad", size=12, color="#888888", expand=True),
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
        route="/perfil_artista", bgcolor="#0a0a0a", padding=0,
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
