import flet as ft
import threading
import random
from src.database.db import get_connection
from src.controllers.deezer import buscar_deezer, get_album_details, get_chart_tracks

# --- CONFIGURACIÓN ESTÉTICA ---
BG_COLOR = "#08131F"
ACCENT_COLOR = "#69A6FF" # Violeta eléctrico para el estilo Midnight Minimalist

def _get_ultima_resena(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT rating, review_text, created_at, album_id, album_title, cover_url, artist_name FROM (
                SELECT r.rating, r.review_text, r.created_at,
                       a.id as album_id, a.title as album_title, a.cover_url,
                       ar.name as artist_name
                FROM reviews r
                JOIN albums a ON r.album_id = a.id
                LEFT JOIN artists ar ON a.artist_id = ar.id
                WHERE r.user_id = %s
                UNION ALL
                SELECT tr.rating, tr.review_text, tr.created_at,
                       a.id as album_id, t.title as album_title, a.cover_url,
                       ar.name as artist_name
                FROM track_reviews tr
                JOIN tracks t ON tr.track_id = t.id
                JOIN albums a ON t.album_id = a.id
                LEFT JOIN artists ar ON a.artist_id = ar.id
                WHERE tr.user_id = %s
            ) AS combined
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id, user_id))
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
        print(f"[LOGOUT] Limpiando sesion del usuario {page.user_id}")
        # Borrar sesión primero
        page.borrar_sesion()
        # Asegurar que page.user_id se establezca a None después de borrar
        page.user_id = None
        page.update()
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
                    ft.GestureDetector(
                        on_tap=abrir_alb,
                        content=ft.Container(
                            bgcolor="#122B46",
                            border_radius=14,
                            border=ft.Border.all(1, "#1A3A5C"),
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            width=140,
                            content=ft.Column(spacing=0, controls=[
                                ft.Image(
                                    src=alb.get("cover_medium"),
                                    width=140, height=140,
                                    fit=ft.BoxFit.COVER,
                                ),
                                ft.Container(
                                    padding=ft.Padding(left=8, right=8, top=6, bottom=8),
                                    content=ft.Column(spacing=2, controls=[
                                        ft.Text(alb.get("title", ""), size=11, weight="bold",
                                                color=ft.Colors.WHITE, max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                        ft.Text(alb.get("artist", {}).get("name", ""), size=10,
                                                color="#69A6FF", max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                    ]),
                                ),
                            ]),
                        ),
                    )
                )
            page.update()

    threading.Thread(target=cargar_carousel, daemon=True).start()

    # ── canciones al azar por géneros ───────────────────────────────────────────
    GENEROS_QUERIES = [
        ("Pop",        "pop hits"),
        ("Rock",       "rock classic"),
        ("Hip-Hop",    "hip hop rap"),
        ("Electrónica","electronic dance"),
        ("R&B",        "rnb soul"),
        ("Reggaeton",  "reggaeton"),
        ("Jazz",       "jazz"),
        ("Metal",      "metal"),
    ]

    genero_activo = [GENEROS_QUERIES[0]]
    para_ti_row = ft.Row(spacing=10, scroll=ft.ScrollMode.AUTO)
    genero_chips_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)

    def cargar_para_ti(query):
        para_ti_row.controls = [
            ft.Container(
                alignment=ft.Alignment(0, 0), width=60,
                content=ft.ProgressRing(width=18, height=18, stroke_width=2, color=ACCENT_COLOR),
            )
        ]

        def _fetch():
            tracks = buscar_deezer(query, "track", limite=10)
            random.shuffle(tracks)
            controls = []
            for t in tracks[:8]:
                img = t.get("album", {}).get("cover_medium", "")
                artista = t.get("artist", {}).get("name", "")

                def abrir_album_track(_, track=t):
                    alb = track.get("album", {})
                    page.album_data = {
                        "id": alb.get("id"),
                        "name": alb.get("title"),
                        "images": [{"url": alb.get("cover_xl") or alb.get("cover_big") or alb.get("cover_medium")}],
                        "artist": track.get("artist", {}),
                        "release_date": "",
                        "total_tracks": "",
                    }
                    page.album_origen = "/home"
                    page.run_task(page.push_route, "/vista_album")

                controls.append(
                    ft.GestureDetector(
                        on_tap=abrir_album_track,
                        content=ft.Container(
                            width=120,
                            bgcolor="#122B46",
                            border_radius=12,
                            border=ft.Border.all(1, "#1A3A5C"),
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            content=ft.Column(spacing=0, controls=[
                                ft.Stack(controls=[
                                    ft.Image(src=img, width=120, height=120, fit=ft.BoxFit.COVER) if img
                                    else ft.Container(width=120, height=120, bgcolor="#0F1F33",
                                                      content=ft.Icon(ft.Icons.MUSIC_NOTE, color="#1C4F7A", size=32),
                                                      alignment=ft.Alignment(0, 0)),
                                    ft.Container(
                                        width=120, height=120,
                                        gradient=ft.LinearGradient(
                                            begin=ft.Alignment(0, 0), end=ft.Alignment(0, 1),
                                            colors=["transparent", "#000000aa"],
                                        ),
                                    ),
                                ]),
                                ft.Container(
                                    padding=ft.Padding(left=8, right=8, top=6, bottom=8),
                                    content=ft.Column(spacing=2, controls=[
                                        ft.Text(t.get("title", ""), size=11, weight="bold",
                                                color=ft.Colors.WHITE, max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                        ft.Text(artista, size=10, color="#69A6FF",
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ]),
                                ),
                            ]),
                        ),
                    )
                )
            para_ti_row.controls = controls
            page.update()
        threading.Thread(target=_fetch, daemon=True).start()

    def render_genero_chips():
        genero_chips_row.controls = [
            ft.GestureDetector(
                on_tap=lambda _, g=g: seleccionar_genero(g),
                content=ft.Container(
                    padding=ft.Padding(left=14, right=14, top=6, bottom=6),
                    border_radius=20,
                    bgcolor=ACCENT_COLOR if g == genero_activo[0] else "#10294E",
                    border=ft.Border.all(1, ACCENT_COLOR if g == genero_activo[0] else "#1A3A5C"),
                    content=ft.Text(g[0], size=12,
                                    color=ft.Colors.WHITE if g == genero_activo[0] else "#A8B8CE"),
                ),
            ) for g in GENEROS_QUERIES
        ]

    def seleccionar_genero(g):
        genero_activo[0] = g
        render_genero_chips()
        genero_chips_row.update()
        cargar_para_ti(g[1])

    render_genero_chips()
    cargar_para_ti(GENEROS_QUERIES[0][1])

    # ── visitado recientemente ─────────────────────────────────────────────────────
    recientes_row = ft.Row(spacing=10, scroll=ft.ScrollMode.AUTO)
    recientes_seccion = ft.Column(spacing=10, visible=False, controls=[
        ft.Text("Visitado recientemente", size=16, color=ft.Colors.WHITE, weight="bold"),
        recientes_row,
    ])

    def cargar_recientes():
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT album_id, album_title, cover_url, artist_name
                FROM recently_viewed
                WHERE user_id = %s
                ORDER BY viewed_at DESC
                LIMIT 10
            """, (page.user_id,))
            rows = cur.fetchall()
            conn.close()
            if not rows:
                return
            controls = []
            for r in rows:
                def abrir(_, row=r):
                    from src.controllers.deezer import get_album_details
                    def _fetch():
                        data = get_album_details(row["album_id"])
                        page.album_data = {
                            "id": data.get("id") or row["album_id"],
                            "name": data.get("title") or row["album_title"],
                            "images": [{"url": data.get("cover_xl") or data.get("cover_medium") or row["cover_url"]}],
                            "artist": data.get("artist", {"name": row["artist_name"]}),
                            "release_date": data.get("release_date", ""),
                            "total_tracks": data.get("nb_tracks", ""),
                        }
                        page.album_origen = "/home"
                        page.run_task(page.push_route, "/vista_album")
                    threading.Thread(target=_fetch, daemon=True).start()

                controls.append(
                    ft.GestureDetector(
                        on_tap=abrir,
                        content=ft.Container(
                            width=110,
                            bgcolor="#122B46",
                            border_radius=12,
                            border=ft.Border.all(1, "#1A3A5C"),
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            content=ft.Column(spacing=0, controls=[
                                ft.Image(src=r["cover_url"], width=110, height=110, fit=ft.BoxFit.COVER)
                                if r["cover_url"] else
                                ft.Container(width=110, height=110, bgcolor="#0F1F33",
                                             content=ft.Icon(ft.Icons.ALBUM, color="#1C4F7A", size=32),
                                             alignment=ft.Alignment(0, 0)),
                                ft.Container(
                                    padding=ft.Padding(left=7, right=7, top=5, bottom=7),
                                    content=ft.Column(spacing=2, controls=[
                                        ft.Text(r["album_title"] or "", size=11, weight="bold",
                                                color=ft.Colors.WHITE, max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                        ft.Text(r["artist_name"] or "", size=10, color="#69A6FF",
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ]),
                                ),
                            ]),
                        ),
                    )
                )
            recientes_row.controls = controls
            recientes_seccion.visible = True
            page.update()
        except Exception:
            pass
    threading.Thread(target=cargar_recientes, daemon=True).start()

    # ── nombre del usuario para saludo ──────────────────────────────────
    nombre_usuario_text = ft.Text("Hola 👋", size=13, color="#4A6A8A")
    
    def cargar_nombre_usuario():
        try:
            user_id = page.user_id
            if user_id is not None:
                conn = get_connection()
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT display_name, username FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                conn.close()
                if row:
                    nombre = (row.get("display_name") or row.get("username") or "Usuario")
                    nombre_usuario_text.value = f"Hola, {nombre} 👋"
                    page.update()
            else:
                print("[HOME] user_id es None")
        except Exception as e:
            print(f"[HOME] Error cargando nombre de usuario: {e}")
            import traceback
            traceback.print_exc()
    
    # Cargar nombre de usuario al iniciar
    threading.Thread(target=cargar_nombre_usuario, daemon=True).start()

    # ── top bar ────────────────────────────────────────────────────────────
    top_bar = ft.Container(
        padding=ft.Padding(bottom=5),
        content=ft.Column(spacing=4, controls=[
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
            nombre_usuario_text,
            ft.Divider(height=1, color="#122B46"),
        ])
    )

    body = ft.Column(
        expand=True, scroll=ft.ScrollMode.AUTO, spacing=25,
        controls=[
            ft.Column([
                ft.Text("Descubrir", size=22, color=ft.Colors.WHITE, weight="bold"),
                carousel_row,
            ], spacing=10),
            recientes_seccion,
            ft.Column([
                ft.Text("Para ti", size=16, color=ft.Colors.WHITE, weight="bold"),
                ft.Text("Canciones de géneros diversos", size=12, color="#4A6A8A"),
                genero_chips_row,
                para_ti_row,
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