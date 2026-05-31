import flet as ft
import time
import threading


def SplashView(page: ft.Page):

    def esperar_y_navegar():
        time.sleep(2)
        destino = "/home" if getattr(page, "user_id", None) else "/"
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
                spacing=6,
                controls=[
                    ft.Text("TRACKER", size=48, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
                    ft.Text("FM", size=20, color="#C1CFEB", font_family="Audiowide"),
                    ft.Container(height=30),
                    ft.ProgressRing(width=20, height=20, stroke_width=2, color="#C1CFEB"),
                ],
            )
        ],
    )
