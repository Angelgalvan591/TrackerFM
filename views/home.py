import flet as ft


def HomeView(page: ft.Page):

    async def cerrar_sesion(e):
        page.user_id = None
        page.borrar_sesion()
        await page.push_route("/")

    top_bar = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("TRACKER FM", size=18, color=ft.Colors.WHITE, font_family="Audiowide", weight="bold"),
            ft.Row(
                spacing=4,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.PEOPLE_OUTLINE,
                        icon_color="#888888",
                        tooltip="Usuarios",
                        on_click=lambda _: page.run_task(page.push_route, "/usuarios"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.SEARCH,
                        icon_color="#888888",
                        tooltip="Buscar",
                        on_click=lambda _: page.run_task(page.push_route, "/busqueda"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PERSON_OUTLINE,
                        icon_color="#888888",
                        tooltip="Perfil",
                        on_click=lambda _: page.run_task(page.push_route, "/perfil"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color="#888888",
                        tooltip="Cerrar sesión",
                        on_click=cerrar_sesion,
                    ),
                ],
            ),
        ],
    )

    return ft.View(
        route="/home",
        bgcolor="#0a0a0a",
        padding=ft.Padding(left=20, right=20, top=20, bottom=20),
        controls=[
            top_bar,
        ],
    )
