import flet as ft
import pygame
import requests
import threading
import io
from controllers.deezer import buscar_deezer
from controllers.spotify import buscar as buscar_spotify

pygame.mixer.init()
reproduciendo = [None]  # preview_url actual


def BusquedaView(page: ft.Page):

    resultados = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
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

    def card_track(item):
        artistas = item.get("artist", {}).get("name", "")
        img = item.get("album", {}).get("cover_medium", "")
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
            padding=10, bgcolor="#1a1a1a", border_radius=10,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Image(src=img, width=48, height=48, border_radius=6, fit=ft.BoxFit.COVER) if img
                    else ft.Container(width=48, height=48, bgcolor="#333333", border_radius=6),
                    ft.Column(spacing=2, expand=True, controls=[
                        ft.Text(item["title"], size=14, color=ft.Colors.WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(artistas, size=12, color="#888888", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ]),
                    play_btn,
                ],
            ),
        )

    def card_album(item):
        artistas = ", ".join(a["name"] for a in item.get("artists", []))
        img = (item.get("images") or [{}])[0].get("url", "")
        import webbrowser
        spotify_url = item.get("external_urls", {}).get("spotify", "")
        return ft.Container(
            padding=10, bgcolor="#1a1a1a", border_radius=10,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Image(src=img, width=48, height=48, border_radius=6, fit=ft.BoxFit.COVER) if img
                    else ft.Container(width=48, height=48, bgcolor="#333333", border_radius=6),
                    ft.Column(spacing=2, expand=True, controls=[
                        ft.Text(item["name"], size=14, color=ft.Colors.WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(artistas, size=12, color="#888888", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ]),
                ],
            ),
        )

    def card_artist(item):
        img = (item.get("images") or [{}])[0].get("url", "")
        return ft.Container(
            padding=10, bgcolor="#1a1a1a", border_radius=10,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Image(src=img, width=48, height=48, border_radius=24, fit=ft.BoxFit.COVER) if img
                    else ft.Container(width=48, height=48, bgcolor="#333333", border_radius=24),
                    ft.Text(item["name"], size=14, color=ft.Colors.WHITE, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ],
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
        else:
            for item in items:
                if filtro[0] == "track":
                    resultados.controls.append(card_track(item))
                elif filtro[0] == "album":
                    resultados.controls.append(card_album(item))
                else:
                    resultados.controls.append(card_artist(item))
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
