import flet as ft
from TrackerFM.src.models.usuarios import guardar_track_review, get_track_reviews, get_user_track_review


def ResenaCancionView(page: ft.Page):
    track = getattr(page, "track_data", {})
    origen = getattr(page, "track_origen", "/busqueda")
    
    track_id = str(track.get("id", ""))
    titulo = track.get("title", "Cancion")
    artista_obj = track.get("artist", {})
    artista = artista_obj.get("name", "Artista")
    artista_id = artista_obj.get("id", "")
    album_obj = track.get("album", {})
    cover = album_obj.get("cover_medium", "")
    album_id = str(album_obj.get("id", "")) if album_obj.get("id") else ""
    album_title = album_obj.get("title", "")
    
    # Obtener reseña existente del usuario
    mi_resena = get_user_track_review(page.user_id, track_id) if page.user_id and track_id else None
    
    rating_ref = [mi_resena.get("rating", 0) if mi_resena else 0]
    txt_resena = ft.TextField(
        hint_text="Escribe tu reseña...",
        multiline=True,
        min_lines=4,
        max_lines=6,
        border_radius=12,
        filled=True,
        fill_color="#10294E",
        border_color="#0F274A",
        focused_border_color="#6A98FF",
        color=ft.Colors.WHITE,
        hint_style=ft.TextStyle(color="#A8B8CE"),
        value=mi_resena.get("review_text", "") if mi_resena else "",
    )
    
    def star_btn(n):
        activo = n <= rating_ref[0]
        return ft.IconButton(
            icon=ft.Icons.STAR if activo else ft.Icons.STAR_BORDER,
            icon_color="#FFD700" if activo else "#A8B8CE",
            icon_size=32,
            on_click=lambda _: set_rating(n),
        )
    
    stars_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
        controls=[star_btn(i) for i in range(1, 6)],
    )
    
    def set_rating(n):
        rating_ref[0] = n
        stars_row.controls = [star_btn(i) for i in range(1, 6)]
        page.update()
    
    def guardar(_):
        if not rating_ref[0]:
            return
        guardar_track_review(
            page.user_id, track_id, titulo, artista, cover,
            rating_ref[0], txt_resena.value or "",
            album_id=album_id, album_title=album_title, artist_id=artista_id
        )
        page.run_task(page.push_route, origen)
    
    resenas_col = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def cargar_resenas():
        reviews = get_track_reviews(track_id) if track_id else []
        if not reviews:
            resenas_col.controls = [
                ft.Text("Sin reseñas aún", size=13, color="#A8B8CE", text_align=ft.TextAlign.CENTER)
            ]
        else:
            resenas_col.controls = [card_review(r) for r in reviews]
        page.update()
    
    def card_review(r):
        usuario = r.get("display_name") or r.get("username", "Usuario")
        estrellas = "★" * int(r.get("rating", 0)) + "☆" * (5 - int(r.get("rating", 0)))
        fecha = str(r.get("created_at", ""))[:10]
        
        return ft.Container(
            bgcolor="#10294E",
            border_radius=16,
            padding=ft.Padding(12, 12, 12, 12),
            content=ft.Column(spacing=6, controls=[
                ft.Row(spacing=8, controls=[
                    ft.Text(usuario, size=14, color=ft.Colors.WHITE, weight="bold"),
                    ft.Text(estrellas, size=14, color="#FFD700"),
                ]),
                ft.Text(r.get("review_text", ""), size=13, color="#D5E0F5"),
                ft.Text(fecha, size=11, color="#7F90A8"),
            ]),
        )
    
    cargar_resenas()
    
    return ft.View(
        route="/resena_cancion",
        bgcolor="#08131F",
        padding=0,
        controls=[
            ft.Column(
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                controls=[
                    # Header
                    ft.Container(
                        padding=ft.Padding(20, 20, 20, 20),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=ft.Colors.WHITE,
                                    on_click=lambda _: page.run_task(page.push_route, origen),
                                ),
                                ft.Text("Reseñar canción", size=16, color=ft.Colors.WHITE, font_family="Audiowide"),
                                ft.Container(width=40),
                            ],
                        ),
                    ),
                    # Info canción
                    ft.Container(
                        padding=ft.Padding(20, 0, 20, 20),
                        content=ft.Row(spacing=12, controls=[
                            ft.Image(src=cover, width=80, height=80, border_radius=8, fit=ft.BoxFit.COVER) if cover
                            else ft.Container(width=80, height=80, bgcolor="#122B46", border_radius=8),
                            ft.Column(spacing=4, expand=True, controls=[
                                ft.Text(titulo, size=16, color=ft.Colors.WHITE, weight="bold", max_lines=2),
                                ft.Text(artista, size=14, color="#C1CFEB", max_lines=1),
                            ]),
                        ]),
                    ),
                    # Form
                    ft.Container(
                        padding=ft.Padding(20, 0, 20, 20),
                        content=ft.Column(spacing=12, controls=[
                            ft.Text("Tu calificación", size=14, color=ft.Colors.WHITE),
                            stars_row,
                            txt_resena,
                            ft.ElevatedButton(
                                content=ft.Text("Guardar reseña", color=ft.Colors.WHITE),
                                bgcolor="#6A98FF",
                                width=200,
                                height=44,
                                on_click=guardar,
                            ),
                        ]),
                    ),
                    ft.Divider(height=1, color="#10294E"),
                    # Reseñas
                    ft.Container(
                        padding=ft.Padding(20, 16, 20, 20),
                        content=ft.Column(spacing=12, controls=[
                            ft.Text("Reseñas de la comunidad", size=15, color=ft.Colors.WHITE, weight="bold"),
                            ft.Container(height=300, content=resenas_col),
                        ]),
                    ),
                ],
            ),
        ],
    )
