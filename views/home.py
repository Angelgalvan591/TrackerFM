import flet as ft
import threading
import random
from database.db import get_connection
from controllers.deezer import buscar_deezer, get_album_details

# --- CONFIGURACIÓN ESTÉTICA ---
BG_COLOR = "#08131F"
ACCENT_COLOR = "#69A6FF" # Violeta eléctrico para el estilo Midnight Minimalist

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

    def ir(ruta):
        cerrar_sidebar(None)
        page.run_task(page.push_route, ruta)

    async def cerrar_sesion(e):
        page.user_id = None
        page.borrar_sesion()
        await page.push_route("/")

    # ── LÓGICA DE LA SIDEBAR UNIFICADA ─────────────────────────────────────
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
            ft.Container(expand=True),
            ft.Container(
                padding=ft.Padding(left=12, right=12, top=0, bottom=24),
                content=ft.TextButton(
                    content=ft.Row(spacing=14, controls=[
                        ft.Icon(ft.Icons.LOGOUT, color="#A8B8CE", size=20),
                        ft.Text("Cerrar sesión", size=14, color="#A8B8CE"),
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

    # ── última reseña ──────────────────────────────────────────────────────
    resena_slot = ft.Column(spacing=0, controls=[
        ft.Container(
            alignment=ft.Alignment(0, 0), height=80,
            content=ft.ProgressRing(width=22, height=22, stroke_width=2, color=ACCENT_COLOR),
        )
    ])

    def cargar_resena():
        resena = _get_ultima_resena(page.user_id)
        if resena:
            estrellas = "★" * int(resena["rating"]) + "☆" * (5 - int(resena["rating"]))

            def abrir_album(_):
                def _fetch():
                    album_data = None
                    if resena['album_id']:
                        album_data = get_album_details(resena['album_id'])

                    if album_data and album_data.get("id"):
                        page.album_data = {
                            "id": album_data.get("id"),
                            "name": album_data.get("title"),
                            "images": [{"url": album_data.get("cover_xl") or album_data.get("cover_big") or album_data.get("cover_medium")}] if album_data.get("cover_medium") else [],
                            "artists": [{"name": album_data.get("artist", {}).get("name", "")}],
                            "release_date": album_data.get("release_date"),
                            "total_tracks": album_data.get("nb_tracks"),
                        }
                    else:
                        res = buscar_deezer(f"{resena['album_title']} {resena.get('artist_name','')}", "album", limite=1)
                        if res:
                            deezer_album = res[0]
                            page.album_data = {
                                "id": deezer_album.get("id"),
                                "name": deezer_album.get("title"),
                                "images": [{"url": deezer_album.get("cover_xl") or deezer_album.get("cover_big") or deezer_album.get("cover_medium")}] if deezer_album.get("cover_medium") else [],
                                "artists": [{"name": deezer_album.get("artist", {}).get("name", "")}],
                                "release_date": deezer_album.get("release_date"),
                                "total_tracks": deezer_album.get("nb_tracks"),
                            }
                        else:
                            page.album_data = {
                                "id": resena["album_id"],
                                "name": resena["album_title"],
                                "images": [{"url": resena["cover_url"]}] if resena.get("cover_url") else [],
                                "artists": [{"name": resena.get("artist_name", "")}],
                                "release_date": "",
                                "total_tracks": "",
                            }
                    page.album_origen = "/home"
                    page.run_task(page.push_route, "/vista_album")
                threading.Thread(target=_fetch, daemon=True).start()

            resena_slot.controls = [
                ft.GestureDetector(
                    on_tap=abrir_album,
                    content=ft.Container(
                        bgcolor="#122B46", border_radius=14,
                        padding=ft.Padding(left=14, right=14, top=14, bottom=14),
                        content=ft.Row(spacing=14, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                            ft.Image(src=resena["cover_url"], width=72, height=72, border_radius=8,
                                     fit=ft.BoxFit.COVER) if resena.get("cover_url")
                            else ft.Container(width=72, height=72, bgcolor="#0F1F33", border_radius=8,
                                              content=ft.Icon(ft.Icons.ALBUM, color="#2B5F81", size=28),
                                              alignment=ft.Alignment(0, 0)),
                            ft.Column(spacing=4, expand=True, controls=[
                                ft.Text(resena["album_title"], size=14, color=ft.Colors.WHITE,
                                        weight="bold", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(resena.get("artist_name", ""), size=12, color=ACCENT_COLOR,
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(estrellas, size=14, color="#FFC542"),
                                ft.Text(resena.get("review_text", ""), size=11, color="#B2C0D9",
                                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            ]),
                        ]),
                    ),
                )
            ]
        else:
            resena_slot.controls = [
                ft.Container(
                    bgcolor="#122B46", border_radius=14,
                    padding=ft.Padding(left=16, right=16, top=20, bottom=20),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.RATE_REVIEW_OUTLINED, color="#1C4F7A", size=36),
                            ft.Text("Aún no has reseñado ningún álbum",
                                    size=12, color="#6B7A8F", text_align=ft.TextAlign.CENTER),
                            ft.TextButton(
                                "Buscar álbumes",
                                style=ft.ButtonStyle(color=ACCENT_COLOR),
                                on_click=lambda _: ir("/busqueda"),
                            ),
                        ],
                    ),
                )
            ]
        page.update()

    threading.Thread(target=cargar_resena, daemon=True).start()

    # ── carrusel de álbumes (Tendencias) ───────────────────────────────────
    carousel_row = ft.Row(spacing=15, scroll=ft.ScrollMode.AUTO)

    def cargar_carousel():
        items = buscar_deezer("hits 2024", "album", limite=8)
        if items:
            for alb in items:
                def abrir_alb(e, a=alb):
                    page.album_data = a
                    page.album_origen = "/home"
                    page.run_task(page.push_route, "/vista_album")

                carousel_row.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                width=140, height=140, border_radius=10,
                                image=ft.DecorationImage(
                                    src=alb.get("cover_medium"),
                                    fit=ft.BoxFit.COVER,
                                ),
                            ),
                            ft.Text(alb.get("title", ""), size=11, weight="bold", color="white", max_lines=1, width=140)
                        ], horizontal_alignment="center"),
                        on_click=abrir_alb,
                    )
                )
            page.update()

    threading.Thread(target=cargar_carousel, daemon=True).start()

    # ── top bar ────────────────────────────────────────────────────────────
    top_bar = ft.Container(
        padding=ft.Padding(bottom=5),
        content=ft.Column([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(icon=ft.Icons.MENU_ROUNDED, icon_color="#A8B8CE", on_click=abrir_sidebar),
                    ft.Text("TRACKER FM", size=18, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
                    ft.IconButton(icon=ft.Icons.SEARCH_ROUNDED, icon_color="#A8B8CE",
                                  on_click=lambda _: page.run_task(page.push_route, "/busqueda")),
                ],
            ),
            ft.Divider(height=1, color="#122B46")
        ])
    )

    body = ft.Column(
        expand=True, scroll=ft.ScrollMode.AUTO, spacing=25,
        controls=[
            ft.Column([
                ft.Text("Descubrir", size=22, color=ft.Colors.WHITE, weight="bold"),
                carousel_row,
            ], spacing=10),
            ft.Column([
                ft.Text("Tu actividad reciente", size=16, color="#A8B8CE", weight="w500"),
                resena_slot,
            ], spacing=10),
        ],
    )

    return ft.View(
        route="/home", bgcolor=BG_COLOR, padding=0,
        controls=[
            ft.Stack(expand=True, controls=[
                ft.Column(expand=True, spacing=0, controls=[
                    ft.Container(
                        padding=ft.Padding(left=20, right=20, top=20, bottom=10),
                        content=top_bar,
                    ),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding(left=20, right=20, top=10, bottom=20),
                        content=body,
                    ),
                ]),
                # Sidebar (Capa superior)
                overlay,
                ft.Row(expand=True, spacing=0, controls=[sidebar_panel]),
            ]),
        ],
    )
