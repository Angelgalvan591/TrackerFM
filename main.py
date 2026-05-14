import flet as ft
from views.login import LoginView
from views.registro import RegistroView
from views.home import HomeView
from controllers.auth import AuthController


def start(page: ft.Page):
    page.title = "TrackerFM"
    page.window_width = 450
    page.window_height = 700
    page.fonts = {
        "Audiowide": "/Audiowide-Regular.ttf",
        "VT323": "/VT323-Regular.ttf",
    }
    page.theme = ft.Theme(font_family="Audiowide")

    auth_ctrl = AuthController()

    def route_change(e):
        page.views.clear()
        if page.route == "/registro":
            page.views.append(RegistroView(page, auth_ctrl))
        elif page.route == "/home":
            page.views.append(HomeView(page))
        else:
            page.views.append(LoginView(page, auth_ctrl))
        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.update()
            page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    route_change(None)


def main():
    ft.run(start, assets_dir="assets")


if __name__ == "__main__":
    main()
