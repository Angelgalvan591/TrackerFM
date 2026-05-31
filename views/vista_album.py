import flet as ft
import pygame
import requests
import threading
import io
from controllers.social import SocialController
from database.db import get_connection
from controllers.deezer import get_album_details

reproduciendo = [None]


def VistaAlbumView(page: ft.Page):
    album    = getattr(page, "album_data", {})
    album_id = album.get("id", "") # Keep album_id as is
    nombre   = album.get("name", "Álbum") or album.get("title", "Álbum") # Prioritize 'name' (from Spotify-like structure) then 'title' (Deezer)
    img      = (album.get("images", [{}])[0].get("url", "") or album.get("cover_xl") or album.get("cover_big") or album.get("cover_medium")) # Prioritize existing 'images' then Deezer covers
    artistas_list = [{"name": album.get("artist", {}).get("name", ""), "id": album.get("artist", {}).get("id", "")}] if album.get("artist") else [] # Deezer has a single artist object
    artistas = ", ".join(a["name"] for a in artistas_list)
    year     = (album.get("release_date") or "")[:4]
    total    = album.get("total_tracks", "") or album.get("nb_tracks", "") # Prioritize existing 'total_tracks' then Deezer 'nb_tracks'
    origen   = getattr(page, "album_origen", "/busqueda")

    social   = SocialController()
    liked    = [social.is_album_liked(page.user_id, album_id) if album_id else False]

    like_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE if liked[0] else ft.Icons.FAVORITE_BORDER,
        icon_color="#FF6370" if liked[0] else "#A8B8CE",
        icon_size=22,
        tooltip="Quitar de favoritos" if liked[0] else "Agregar a favoritos",
    )

    def abrir_modal_resena(e):
        rating_input = ft.Slider(min=1, max=5, divisions=4, label="{value} ★", value=5, active_color="#69A6FF")
        comment_input = ft.TextField(label="¿Qué te pareció este álbum?", multiline=True, min_lines=3, border_color="#0F1F33")

        def guardar_resena(_):
            if not album_id: return
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                # Asegurar que el álbum existe en la DB (ForeignKey constraint)
                artist_id = artistas_list[0].get("id", "") if artistas_list else "0"
                artist_name = artistas_list[0].get("name", "Desconocido") if artistas_list else "Desconocido"
                
                cursor.execute("SELECT id FROM artists WHERE id = %s", (artist_id,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO artists (id, name) VALUES (%s, %s)", (artist_id, artist_name))
                
                cursor.execute("SELECT id FROM albums WHERE id = %s", (album_id,))
                if not cursor.fetchone():
                    rel_date = album.get("release_date") or (year + "-01-01" if year else None)
                    cursor.execute(
                        "INSERT INTO albums (id, artist_id, title, cover_url, release_date, total_tracks) VALUES (%s, %s, %s, %s, %s, %s)",
                        (album_id, artist_id, nombre, img, rel_date, total or None)
                    )
                
                # Insertar o actualizar reseña
                cursor.execute("DELETE FROM reviews WHERE user_id = %s AND album_id = %s", (page.user_id, album_id))
                cursor.execute(
                    "INSERT INTO reviews (user_id, album_id, rating, review_text) VALUES (%s, %s, %s, %s)",
                    (page.user_id, album_id, rating_input.value, comment_input.value)
                )
                conn.commit()
                conn.close()
                page.overlay.remove(dlg)
                page.snack_bar = ft.SnackBar(ft.Text("¡Reseña guardada!"), bgcolor="#46D7FF")
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                print(f"Error al reseñar: {ex}")

        dlg = ft.AlertDialog(
            bgcolor="#10294E",
            title=ft.Text("Escribir Reseña", font_family="Audiowide", size=18),
            content=ft.Column([
                ft.Text(f"Califica '{nombre}'", size=14, color="#A8B8CE"),
                rating_input,
                comment_input,
            ], tight=True, spacing=15),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.overlay.remove(dlg) or page.update()),
                ft.ElevatedButton("Publicar", bgcolor="#69A6FF", color="white", on_click=guardar_resena),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def abrir_modal_resena_track(track):
        track_id = str(track.get("id", ""))
        track_title = track.get("title", "Canción")
        rating_input = ft.Slider(min=1, max=5, divisions=4, label="{value} ★", value=5, active_color="#69A6FF")
        comment_input = ft.TextField(label="¿Qué te pareció esta canción?", multiline=True, min_lines=3, border_color="#0F1F33")

        def guardar_resena_track(_):
            if not track_id or not album_id: return
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                
                # Asegurar artista, album y track en DB antes de la reseña por integridad referencial
                a_id = artistas_list[0].get("id", "0") if artistas_list else "0"
                a_name = artistas_list[0].get("name", "Desconocido") if artistas_list else "Desconocido"
                cursor.execute("SELECT id FROM artists WHERE id = %s", (a_id,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO artists (id, name) VALUES (%s, %s)", (a_id, a_name))

                cursor.execute("SELECT id FROM albums WHERE id = %s", (album_id,))
                if not cursor.fetchone():
                    rel_date = album.get("release_date") or (year + "-01-01" if year else None)
                    cursor.execute(
                        "INSERT INTO albums (id, artist_id, title, cover_url, release_date, total_tracks) VALUES (%s, %s, %s, %s, %s, %s)",
                        (album_id, a_id, nombre, img, rel_date, total or None)
                    )

                cursor.execute("SELECT id FROM tracks WHERE id = %s", (track_id,))
                if not cursor.fetchone():
                    duration = track.get("duration", 0) * 1000
                    cursor.execute(
                        "INSERT INTO tracks (id, album_id, title, duration_ms, preview_url) VALUES (%s, %s, %s, %s, %s)",
                        (track_id, album_id, track_title, duration, track.get("preview", ""))
                    )

                # Insertar o actualizar reseña de canción
                cursor.execute("DELETE FROM track_reviews WHERE user_id = %s AND track_id = %s", (page.user_id, track_id))
                cursor.execute(
                    "INSERT INTO track_reviews (user_id, track_id, rating, review_text) VALUES (%s, %s, %s, %s)",
                    (page.user_id, track_id, rating_input.value, comment_input.value)
                )
                conn.commit()
                conn.close()
                page.overlay.remove(dlg)
                page.snack_bar = ft.SnackBar(ft.Text(f"Reseña de '{track_title}' guardada"), bgcolor="#46D7FF")
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                print(f"Error al reseñar canción: {ex}")

        dlg = ft.AlertDialog(
            bgcolor="#10294E",
            title=ft.Text("Reseñar Canción", font_family="Audiowide", size=18),
            content=ft.Column([
                ft.Text(f"Calificando: {track_title}", size=14, color="#A8B8CE"),
                rating_input,
                comment_input,
            ], tight=True, spacing=15),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.overlay.remove(dlg) or page.update()),
                ft.ElevatedButton("Publicar", bgcolor="#69A6FF", color="white", on_click=guardar_resena_track),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def toggle_like(e):
        if not album_id:
            return
        if liked[0]:
            social.unlike_album(page.user_id, album_id)
            liked[0] = False
            like_btn.icon = ft.Icons.FAVORITE_BORDER
            like_btn.icon_color = "#A8B8CE"
            like_btn.tooltip = "Agregar a favoritos"
        else:
            artist_id   = artistas_list[0].get("id", "") if artistas_list else ""
            artist_name = artistas_list[0].get("name", "") if artistas_list else ""
            cover_url   = img
            release_date = album.get("release_date") if album.get("release_date") else (year + "-01-01" if year else None) # Use actual release_date if available
            social.like_album(
                page.user_id, album_id, nombre, cover_url,
                artist_id, artist_name, release_date, total or None
            )
            liked[0] = True
            like_btn.icon = ft.Icons.FAVORITE
            like_btn.icon_color = "#FF6370"
            like_btn.tooltip = "Quitar de favoritos"
        page.update()

    like_btn.on_click = toggle_like
    review_btn = ft.IconButton(
        icon=ft.Icons.RATE_REVIEW_OUTLINED,
        icon_color="#A8B8CE",
        icon_size=22,
        tooltip="Escribir reseña",
        on_click=abrir_modal_resena
    )

    lista = ft.Column(spacing=8, controls=[
        ft.Container(
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(left=0, right=0, top=24, bottom=0),
            content=ft.ProgressRing(width=28, height=28, stroke_width=2, color="#69A6FF"),
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
        preview      = track.get("preview", "")
        duracion_s   = track.get("duration", 0) # Deezer returns duration in seconds
        mins         = duracion_s // 60
        segs         = duracion_s % 60
        artistas_t   = track.get("artist", {}).get("name", "") # Deezer track has single artist object
        play_btn     = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE, icon_color="#69A6FF", icon_size=24,
            disabled=not preview,
        )
        review_track_btn = ft.IconButton(
            icon=ft.Icons.RATE_REVIEW_OUTLINED,
            icon_color="#A8B8CE",
            icon_size=18,
            tooltip="Reseñar canción",
            on_click=lambda _: abrir_modal_resena_track(track)
        )
        if preview:
            play_btn.on_click = lambda _, u=preview, b=play_btn: play_preview(u, b)
        return ft.Container(
            padding=ft.Padding(left=10, right=8, top=8, bottom=8),
            border_radius=10,
            on_hover=lambda e: setattr(e.control, "bgcolor", "#122B46" if e.data == "true" else None) or e.control.update(),
            content=ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text(str(i), size=12, color="#7F90A8", width=24, text_align=ft.TextAlign.CENTER),
                ft.Column(spacing=2, expand=True, controls=[
                    ft.Text(track["title"], size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(artistas_t, size=12, color="#C1CFEB",
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ]),
                ft.Text(f"{mins}:{segs:02d}", size=11, color="#7F90A8"),
                review_track_btn,
                play_btn,
            ]),
        )

    def cargar():
        if not album_id:
            lista.controls = [ft.Text("ID de álbum no disponible", color="#6B7A8F", size=13)]
            page.update()
            return
        album_details = get_album_details(album_id)
        tracks = album_details.get("tracks", {}).get("data", [])
        if not tracks:
            lista.controls = [ft.Text("Sin canciones disponibles", color="#6B7A8F", size=13)]
            page.update()
            return

        lista.controls = [track_row(i + 1, t) for i, t in enumerate(tracks)]
        page.update()

    threading.Thread(target=cargar, daemon=True).start()

    header = ft.Container(
        padding=ft.Padding(left=20, right=20, top=16, bottom=16),
        content=ft.Row(spacing=16, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
            ft.Image(src=img, width=100, height=100, border_radius=10, fit=ft.BoxFit.COVER) if img
            else ft.Container(width=100, height=100, bgcolor="#10243C", border_radius=10,
                              content=ft.Icon(ft.Icons.ALBUM, color="#2B5F81", size=40),
                              alignment=ft.Alignment(0, 0)),
            ft.Column(spacing=6, expand=True, controls=[
                ft.Text(nombre, size=17, color=ft.Colors.WHITE, weight="bold",
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(artistas, size=13, color="#69A6FF",
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{year}  ·  {total} canciones" if total else year,
                        size=11, color="#6B7A8F"),
                ft.Row(spacing=4, controls=[like_btn, review_btn]),
            ]),
        ]),
    )

    return ft.View(
        route="/vista_album", bgcolor="#08131F", padding=0,
        controls=[
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    bgcolor="#08131F",
                    padding=ft.Padding(left=8, right=0, top=12, bottom=0),
                    content=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK, icon_color="#A8B8CE",
                        on_click=lambda _: page.run_task(page.push_route, origen),
                    ),
                ),
                ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0, controls=[
                    header,
                    ft.Divider(height=1, color="#122B46"),
                    ft.Container(
                        padding=ft.Padding(left=20, right=20, top=12, bottom=24),
                        content=lista,
                    ),
                ]),
            ]),
        ],
    )
