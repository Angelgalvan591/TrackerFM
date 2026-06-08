import flet as ft
import time
import threading


def SplashView(page: ft.Page):

    def esperar_y_navegar():
        time.sleep(1.0)
        # Verificación explícita contra None
        uid = getattr(page, "user_id", None)
        # Si el ID es 0 o None, mejor mandar al login para estar seguros
        destino = "/home" if (uid is not None and uid != 0) else "/"
        page.run_task(page.push_route, destino)

    threading.Thread(target=esperar_y_navegar, daemon=True).start()

    return ft.View(
        route="/splash",
        bgcolor="#08131F",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                controls=[
                    ft.Container(
                        width=80, height=80, border_radius=40,
                        bgcolor="#10243C",
                        border=ft.Border.all(2, "#69A6FF"),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("TR", size=36, color="#69A6FF", font_family="Audiowide", weight="bold"),
                    ),
                    ft.Container(height=20),
                    ft.Text("TRACKER", size=42, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
                    ft.Text("FM", size=18, color="#69A6FF", font_family="Audiowide"),
                    ft.Container(height=8),
                    ft.Text("tu música, tu historia", size=12, color="#4A6A8A", italic=True),
                    ft.Container(height=40),
                    ft.ProgressRing(width=18, height=18, stroke_width=2, color="#69A6FF"),
                ],
            )
        ],
    )