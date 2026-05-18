import flet as ft
import pygame
import requests
import threading
import io
from controllers.spotify import get_album_tracks
from controllers.social import SocialController
from controllers.deezer import get_preview

reproduciendo = [None]


def VistaAlbumView(page: ft.Page):
    album    = getattr(page, "album_data", {})
    album_id = album.get("id", "")
    nombre   = album.get("name", "Álbum")
    img      = (album.get("images") or [{}])[0].get("url", "")
    artistas_list = album.get("artists", [])
    artistas = ", ".join(a["name"] for a in artistas_list)
    year     = (album.get("release_date") or "")[:4]
    total    = album.get("total_tracks", "")
    origen   = getattr(page, "album_origen", "/busqueda")

    social   = SocialController()
    liked    = [social.is_album_liked(page.user_id, album_id) if album_id else False]

    like_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE if liked[0] else ft.Icons.FAVORITE_BORDER,
        icon_color="#e05555" if liked[0] else "#888888",
        icon_size=22,
        tooltip="Quitar de favoritos" if liked[0] else "Agregar a favoritos",
    )

    def toggle_like(e):
        if not album_id:
            return
        if liked[0]:
            social.unlike_album(page.user_id, album_id)
            liked[0] = False
            like_btn.icon = ft.Icons.FAVORITE_BORDER
            like_btn.icon_color = "#888888"
            like_btn.tooltip = "Agregar a favoritos"
        else:
            artist_id   = artistas_list[0].get("id", "") if artistas_list else ""
            artist_name = artistas_list[0].get("name", "") if artistas_list else ""
            cover_url   = img
            release_date = year + "-01-01" if year else None
            social.like_album(
                page.user_id, album_id, nombre, cover_url,
                artist_id, artist_name, release_date, total or None
            )
            liked[0] = True
            like_btn.icon = ft.Icons.FAVORITE
            like_btn.icon_color = "#e05555"
            like_btn.tooltip = "Quitar de favoritos"
        page.update()

    like_btn.on_click = toggle_like

    lista = ft.Column(spacing=8, controls=[
        ft.Container(
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(left=0, right=0, top=24, bottom=0),
            content=ft.ProgressRing(width=28, height=28, stroke_width=2, color="#1DB954"),
        )
    ])

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
        preview      = track.get("preview_url", "")
        duracion_ms  = track.get("duration_ms", 0)
        mins         = duracion_ms // 60000
        segs         = (duracion_ms % 60000) // 1000
        artistas_t   = ", ".join(a["name"] for a in track.get("artists", []))
        play_btn     = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE, icon_color="#1DB954", icon_size=24,
            disabled=not preview,
        )
        if preview:
            play_btn.on_click = lambda _, u=preview, b=play_btn: play_preview(u, b)
        return ft.Container(
            padding=ft.Padding(left=12, right=8, top=8, bottom=8),
            border_radius=10, bgcolor="#1a1a1a",
            content=ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text(str(i), size=12, color="#555555", width=22),
                ft.Column(spacing=2, expand=True, controls=[
                    ft.Text(track["name"], size=13, color=ft.Colors.WHITE,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(artistas_t, size=11, color="#888888",
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ]),
                ft.Text(f"{mins}:{segs:02d}", size=11, color="#555555"),
                play_btn,
            ]),
        )

    def cargar():
        if not album_id:
            lista.controls = [ft.Text("ID de álbum no disponible", color="#666666", size=13)]
            page.update()
            return
        tracks, _ = get_album_tracks(album_id)
        if not tracks:
            lista.controls = [ft.Text("Sin canciones disponibles", color="#666666", size=13)]
            page.update()
            return
        # buscar previews en Deezer para tracks sin preview de Spotify
        primer_artista = artistas_list[0].get("name", "") if artistas_list else ""
        for t in tracks:
            if not t.get("preview_url"):
                t_artista = t.get("artists", [{}])[0].get("name", "") or primer_artista
                t["preview_url"] = get_preview(t["name"], t_artista)
        lista.controls = [track_row(i + 1, t) for i, t in enumerate(tracks)]
        page.update()

    threading.Thread(target=cargar, daemon=True).start()

    header = ft.Container(
        padding=ft.Padding(left=20, right=20, top=16, bottom=16),
        content=ft.Row(spacing=16, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
            ft.Image(src=img, width=100, height=100, border_radius=10, fit=ft.BoxFit.COVER) if img
            else ft.Container(width=100, height=100, bgcolor="#1a1a1a", border_radius=10,
                              content=ft.Icon(ft.Icons.ALBUM, color="#555555", size=40),
                              alignment=ft.Alignment(0, 0)),
            ft.Column(spacing=6, expand=True, controls=[
                ft.Text(nombre, size=17, color=ft.Colors.WHITE, weight="bold",
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(artistas, size=13, color="#1DB954",
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{year}  ·  {total} canciones" if total else year,
                        size=11, color="#666666"),
                ft.Row(spacing=4, controls=[like_btn]),
            ]),
        ]),
    )

    return ft.View(
        route="/vista_album", bgcolor="#0a0a0a", padding=0,
        controls=[
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    bgcolor="#0a0a0a",
                    padding=ft.Padding(left=8, right=0, top=12, bottom=0),
                    content=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK, icon_color="#888888",
                        on_click=lambda _: page.run_task(page.push_route, origen),
                    ),
                ),
                ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0, controls=[
                    header,
                    ft.Divider(height=1, color="#222222"),
                    ft.Container(
                        padding=ft.Padding(left=20, right=20, top=12, bottom=24),
                        content=lista,
                    ),
                ]),
            ]),
        ],
    )
