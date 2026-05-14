import flet as ft


def HomeView(page: ft.Page):
    return ft.View(
        route="/home",
        bgcolor=ft.Colors.BLACK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("TRACKER", size=40, color=ft.Colors.WHITE, font_family="Audiowide"),
        ],
    )
