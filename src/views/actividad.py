import flet as ft
import pygame
import requests
import threading
import io
from src.database.db import get_connection

pygame.mixer.init()
reproduciendo = [None]

def ActividadView(page: ft.Page):
    def ir(ruta):
        cerrar_sidebar(None)
        page.run_task(page.push_route, ruta)

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

    # Paleta de colores Midnight Minimalist (Consistente con Home y Perfil)
    BG_COLOR = "#08131F"
    CARD_BG = "#122B46"
    ACCENT = "#69A6FF"
    
    # Columnas con scroll para cada pestaña
    resenas_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12)
    likes_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12)
    amigos_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12)

    def cargar_datos():
        try:
            print(f"[DEBUG] Cargando datos para user_id: {page.user_id}")
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            
            # Cargar Reseñas Reales (álbumes + canciones)
            cur.execute("""
                SELECT r.review_text as comment, r.rating, a.title, ar.name as artist, a.cover_url as img, r.created_at
                FROM reviews r
                JOIN albums a ON r.album_id = a.id
                JOIN artists ar ON a.artist_id = ar.id
                WHERE r.user_id = %s
                UNION ALL
                SELECT tr.review_text as comment, tr.rating, t.title, COALESCE(ar.name, 'Artista desconocido') as artist, COALESCE(a.cover_url, '') as img, tr.created_at
                FROM track_reviews tr
                JOIN tracks t ON tr.track_id = t.id
                LEFT JOIN albums a ON t.album_id = a.id
                LEFT JOIN artists ar ON a.artist_id = ar.id
                WHERE tr.user_id = %s
                ORDER BY created_at DESC
            """, (page.user_id, page.user_id))
            reviews_db = cur.fetchall()
            
            # Cargar Likes Reales
            cur.execute("""
                SELECT a.title, COALESCE(ar.name, 'Artista desconocido') as artist, a.cover_url as img
                FROM favorite_albums fa
                JOIN albums a ON fa.album_id = a.id
                LEFT JOIN artists ar ON a.artist_id = ar.id
                WHERE fa.user_id = %s ORDER BY fa.created_at DESC
            """, (page.user_id,))
            likes_db = cur.fetchall()
            conn.close()

            print(f"[DEBUG] reviews: {len(reviews_db)}, likes: {len(likes_db)}")
            resenas_list.controls = [
                create_card(r["title"], r["artist"], extra_info=f"{'★'*int(r['rating'])} 💬 {r['comment']}", image_url=r["img"]) 
                for r in reviews_db
            ] if reviews_db else [ft.Text("No has escrito reseñas aún.", color="#A8B8CE", italic=True)]

            likes_list.controls = [
                create_card(l["title"], l["artist"], image_url=l["img"], icon=ft.Icons.FAVORITE, icon_color="#E91E63") 
                for l in likes_db
            ] if likes_db else [ft.Text("No tienes álbumes favoritos.", color="#A8B8CE", italic=True)]
            
            resenas_list.update()
            likes_list.update()
            page.update()
        except Exception as ex:
            print(f"Error cargar_datos: {ex}")

    threading.Thread(target=cargar_datos, daemon=True).start()
    
    friends_activity = [
        {"user": "Andre", "title": "Borderline", "artist": "Tame Impala", "img": "https://e-cdns-images.dzcdn.net/images/cover/6c66687076a0b16259f9725f0a3592f6/250x250-000000-80-0-0.jpg", "preview": "https://cdns-preview-d.dzcdn.net/stream/c-d698e5967072481ec6544a4962c45300-4.mp3"},
        {"user": "Angel", "title": "The Less I Know The Better", "artist": "Tame Impala", "img": "https://e-cdns-images.dzcdn.net/images/cover/9e1cfc756886ac782e363d7915509930/250x250-000000-80-0-0.jpg", "preview": "https://cdns-preview-9.dzcdn.net/stream/c-9e1cfc756886ac782e363d7915509930-3.mp3"},
    ]

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

    def create_card(title, subtitle, extra_info=None, image_url=None, icon=None, icon_color=ACCENT, on_icon_click=None):
        return ft.Container(
            padding=16,
            bgcolor=CARD_BG,
            border_radius=16,
            border=ft.Border.all(1, "#17354E"),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            on_hover=lambda e: setattr(e.control, "border", ft.Border.all(1, ACCENT if e.data == "true" else "#17354E")) or e.control.update(),
            content=ft.Row(
                spacing=16,
                controls=[
                    ft.Image(src=image_url, width=64, height=64, border_radius=10, fit=ft.BoxFit.COVER) if image_url 
                    else ft.Container(width=64, height=64, bgcolor="#2A2F3E", border_radius=10, content=ft.Icon(ft.Icons.MUSIC_NOTE, color="#2B5F81")),
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Text(title, size=15, weight="bold", color=ft.Colors.WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(subtitle, size=13, color="#A8B8CE", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Container(
                                content=ft.Text(extra_info, size=12, italic=True, color="#B3B3B3"),
                                visible=extra_info is not None,
                                margin=ft.Margin(0, 4, 0, 0)
                            )
                        ]
                    ),
                    ft.IconButton(icon=icon, icon_color=icon_color, icon_size=22, on_click=on_icon_click) if icon else ft.Container()
                ]
            )
        )

    amigos_list.controls = [
        create_card(
            a["title"], a["artist"],
            extra_info=f"Escuchando ahora (vía {a['user']})",
            image_url=a["img"], icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
            on_icon_click=lambda e, u=a["preview"]: play_preview(u, e.control)
        ) for a in friends_activity
    ]

    tab_index = [0]
    contenido_tabs = ft.Container(expand=True, padding=20, content=resenas_list)

    def build_tab_btn(label, idx):
        selected = tab_index[0] == idx
        return ft.TextButton(
            content=ft.Text(label, color=ACCENT if selected else "#2B5F81", size=14, weight="bold" if selected else None),
            style=ft.ButtonStyle(
                overlay_color="#ffffff11",
                padding=ft.Padding(left=16, right=16, top=8, bottom=8),
            ),
            on_click=lambda _, i=idx: cambiar_tab(i),
        )

    tab_bar = ft.Row(spacing=0)

    def render_tab_bar():
        tab_bar.controls = [
            build_tab_btn("Reseñas", 0),
            build_tab_btn("Likes", 1),
            build_tab_btn("Amigos", 2),
        ]

    def cambiar_tab(idx):
        tab_index[0] = idx
        if idx == 0:
            contenido_tabs.content = resenas_list
        elif idx == 1:
            contenido_tabs.content = likes_list
        else:
            contenido_tabs.content = amigos_list
        render_tab_bar()
        tab_bar.update()
        contenido_tabs.update()

    render_tab_bar()

    return ft.View(
        route="/actividad",
        bgcolor=BG_COLOR,
        padding=0,
        controls=[
            ft.Stack(expand=True, controls=[
                ft.Column(expand=True, spacing=0, controls=[
                    ft.Container(
                        padding=ft.Padding(20, 20, 20, 10),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.IconButton(ft.Icons.MENU_ROUNDED, icon_color="#A8B8CE", on_click=abrir_sidebar),
                                ft.Text("MI MÚSICA", size=18, font_family="Audiowide", color=ft.Colors.WHITE),
                                ft.Container(width=40)
                            ]
                        )
                    ),
                    tab_bar,
                    ft.Divider(height=1, color="#122B46"),
                    contenido_tabs,
                ]),
                overlay,
                ft.Row(expand=True, spacing=0, controls=[sidebar_panel]),
            ])
        ]
    )