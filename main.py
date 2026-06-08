import flet as ft
import json
import os
import pygame
from src.views.login import LoginView
from src.views.registro import RegistroView
from src.views.home import HomeView
from src.views.splash import SplashView
from src.views.perfil import PerfilView
from src.views.busqueda import BusquedaView
from src.views.usuarios import UsuariosView
from src.views.perfil_publico import PerfilPublicoView
from src.views.perfil_artista import PerfilArtistaView
from src.views.vista_album import VistaAlbumView
from src.views.actividad import ActividadView
from src.views.recuperar import RecuperarView
from src.views.resena_cancion import ResenaCancionView
from src.controllers.auth import AuthController

SESSION_FILE = os.path.join(os.path.dirname(__file__), ".session")

def guardar_sesion(user_id):
    """Guarda el ID del usuario en sesión"""
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump({"user_id": user_id}, f)
    except Exception as e:
        print(f"Error guardando sesión: {e}")

def cargar_sesion():
    """Carga el ID del usuario desde sesión"""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE) as f:
                data = json.load(f)
                uid = data.get("user_id")
                return uid if uid is not None else None
    except Exception as e:
        print(f"Error cargando sesión: {e}")
    return None

def borrar_sesion():
    """Elimina el archivo de sesión"""
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except Exception as e:
        print(f"Error borrando sesión: {e}")


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
    page.guardar_sesion = guardar_sesion
    page.borrar_sesion = borrar_sesion
    # Siempre arrancar sin sesión para forzar login
    borrar_sesion()
    page.user_id = None

    async def route_change(e):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        page.views.clear()
            
        if page.route == "/splash":
            page.views.append(SplashView(page))
        elif page.route == "/registro":
            page.views.append(RegistroView(page, auth_ctrl))
        elif page.route == "/home":
            if page.user_id is None:
                await page.push_route("/")
            else:
                page.views.append(HomeView(page))
        elif page.route == "/perfil":
            if page.user_id is None:
                await page.push_route("/")
            else:
                page.views.append(PerfilView(page, auth_ctrl))
        elif page.route == "/busqueda":
            if page.user_id is None:
                await page.push_route("/")
            else:
                page.views.append(BusquedaView(page))
        elif page.route == "/usuarios":
            if page.user_id is None:
                await page.push_route("/")
            else:
                page.views.append(UsuariosView(page))
        elif page.route == "/perfil_publico":
            if page.user_id is None:
                await page.push_route("/")
            else:
                page.views.append(PerfilPublicoView(page))
        elif page.route == "/perfil_artista":
            if page.user_id is None:
                await page.push_route("/")
            else:
                page.views.append(PerfilArtistaView(page))
        elif page.route == "/vista_album":
            if page.user_id is None:
                await page.push_route("/")
            else:
                page.views.append(VistaAlbumView(page))
        elif page.route == "/actividad":
            if page.user_id is None:
                await page.push_route("/")
            else:
                page.views.append(ActividadView(page))
        elif page.route == "/recuperar":
            page.views.append(RecuperarView(page, auth_ctrl))
        elif page.route == "/resena_cancion":
            if page.user_id is None:
                await page.push_route("/")
            else:
                page.views.append(ResenaCancionView(page))
        elif page.route == "/":
            # Al llegar al login, BORRAMOS todo rastro de sesión previa
            borrar_sesion()
            page.user_id = None
            page.views.append(LoginView(page, auth_ctrl))
        else:
            # Por seguridad, si no hay ruta y no hay user, al login y limpiamos
            if page.user_id is None:
                borrar_sesion()
            page.views.append(LoginView(page, auth_ctrl))
        page.update()

    async def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.update()
            await page.push_route(page.views[-1].route)

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
