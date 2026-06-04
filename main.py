import flet as ft
import json
import os
import pygame
from views.login import LoginView
from views.registro import RegistroView
from views.home import HomeView
from views.splash import SplashView
from views.perfil import PerfilView
from views.busqueda import BusquedaView
from views.usuarios import UsuariosView
from views.perfil_publico import PerfilPublicoView
from views.perfil_artista import PerfilArtistaView
from views.vista_album import VistaAlbumView
from views.actividad import ActividadView
from views.recuperar import RecuperarView
from views.resena_cancion import ResenaCancionView
from controllers.auth import AuthController

SESSION_FILE = os.path.join(os.path.dirname(__file__), ".session")

def guardar_sesion(user_id):
    with open(SESSION_FILE, "w") as f:
        json.dump({"user_id": user_id}, f)

def cargar_sesion():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            uid = json.load(f).get("user_id")
            return uid if uid else None
    return None

def borrar_sesion():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)


async def start(page: ft.Page):
    page.title = "TrackerFM"
    page.window.width = 390
    page.window.height = 880
    page.window.min_width = 390
    page.window.max_width = 390
    page.window.resizable = False
    page.window.title_bar_hidden = False
    page.window.title_bar_buttons_hidden = False
    page.bgcolor = "#08131F"
    page.padding = 0
    page.fonts = {
        "Audiowide": "/Audiowide-Regular.ttf",
        "VT323": "/VT323-Regular.ttf",
    }
    page.theme = ft.Theme(font_family="Audiowide", color_scheme_seed="#69A6FF")

    auth_ctrl = AuthController()
    page.user_id = cargar_sesion()
    page.guardar_sesion = guardar_sesion
    page.borrar_sesion = borrar_sesion

    async def route_change(e):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        page.views.clear()
        if page.route == "/splash":
            page.views.append(SplashView(page))
        elif page.route == "/registro":
            page.views.append(RegistroView(page, auth_ctrl))
        elif page.route == "/home":
            page.views.append(HomeView(page))
        elif page.route == "/perfil":
            page.views.append(PerfilView(page, auth_ctrl))
        elif page.route == "/busqueda":
            page.views.append(BusquedaView(page))
        elif page.route == "/usuarios":
            page.views.append(UsuariosView(page))
        elif page.route == "/perfil_publico":
            page.views.append(PerfilPublicoView(page))
        elif page.route == "/perfil_artista":
            page.views.append(PerfilArtistaView(page))
        elif page.route == "/vista_album":
            page.views.append(VistaAlbumView(page))
        elif page.route == "/actividad":
            page.views.append(ActividadView(page))
        elif page.route == "/recuperar":
            page.views.append(RecuperarView(page, auth_ctrl))
        elif page.route == "/resena_cancion":
            page.views.append(ResenaCancionView(page))
        else:
            page.views.append(LoginView(page, auth_ctrl))
        page.update()

    async def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.update()
            await page.push_route(page.views[-1].route)

    def window_event(e):
        if e.data == "close":
            page.window.destroy()

    page.window.prevent_close = True
    page.on_window_event = window_event
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    await page.push_route("/splash")


def main():
    ft.run(
        start,
        assets_dir="assets",
        view=ft.AppView.FLET_APP,
    )


if __name__ == "__main__":
    main()