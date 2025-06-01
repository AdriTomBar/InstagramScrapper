# instagram_playwright.py
from playwright.sync_api import sync_playwright
import time
import random
import json
import os
from datetime import datetime


class InstagramPlaywrightAnalyzer:
    def __init__(self):
        self.page = None
        self.browser = None
        self.context = None
        self.followers = set()
        self.following = set()

    def setup_browser(self, headless=False):
        """Configura el navegador con Playwright."""
        self.playwright = sync_playwright().start()

        # Configuración del navegador
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )

        # Crear contexto con configuración anti-detección
        self.context = self.browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='es-ES',
            timezone_id='Europe/Madrid'
        )

        # Crear página
        self.page = self.context.new_page()

        # Interceptar y modificar headers
        self.page.route('**/*', self.modify_headers)

        print("[✓] Navegador configurado correctamente")

    def modify_headers(self, route):
        """Modifica headers para evitar detección."""
        headers = route.request.headers
        headers.update({
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'upgrade-insecure-requests': '1',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
            'accept-encoding': 'gzip, deflate, br'
        })
        route.continue_(headers=headers)

    def human_delay(self, min_seconds=1, max_seconds=3):
        """Genera delays humanos aleatorios."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def human_type(self, selector, text, delay_range=(0.05, 0.15)):
        """Escribe texto con velocidad humana."""
        element = self.page.locator(selector)
        element.click()
        self.page.keyboard.press('Control+A')  # Seleccionar

        for char in text:
            self.page.keyboard.type(char)
            time.sleep(random.uniform(*delay_range))

    def login(self, username, password):
        """Inicia sesión en Instagram."""
        print("[→] Navegando a Instagram...")
        self.page.goto('https://www.instagram.com/')
        self.human_delay(3, 5)

        # Aceptar cookies si aparece el banner
        try:
            if self.page.locator('button:has-text("Permitir cookies esenciales y opcionales")').is_visible(
                    timeout=3000):
                self.page.click('button:has-text("Permitir cookies esenciales y opcionales")')
                self.human_delay(1, 2)
        except:
            pass

        # Ir a login si no está ya ahí
        if not self.page.url.__contains__('login'):
            self.page.goto('https://www.instagram.com/accounts/login/')
            self.human_delay(2, 4)

        print("[→] Iniciando sesión...")

        # Esperar a que aparezcan los campos
        self.page.wait_for_selector('input[name="username"]', timeout=10000)

        # Llenar credenciales
        self.human_type('input[name="username"]', username)
        self.human_delay(1, 2)
        self.human_type('input[name="password"]', password)
        self.human_delay(1, 2)

        # Hacer click en login
        self.page.click('button[type="submit"]')

        # Esperar a que termine el login
        print("[→] Esperando confirmación de login...")
        self.page.wait_for_url('https://www.instagram.com/', timeout=15000)

        # Manejar posibles pop-ups
        self.handle_popups()
        print("[✓] Login exitoso")

    def handle_popups(self):
        """Maneja los pop-ups comunes de Instagram."""
        popups_to_handle = [
            'button:has-text("Ahora no")',
            'button:has-text("Not Now")',
            'button:has-text("No permitir")',
            'button:has-text("Cancelar")',
            '[aria-label="Close"]'
        ]

        for popup_selector in popups_to_handle:
            try:
                if self.page.locator(popup_selector).is_visible(timeout=2000):
                    self.page.click(popup_selector)
                    self.human_delay(1, 2)
            except:
                continue

    def go_to_profile(self, username):
        """Navega al perfil del usuario."""
        print(f"[→] Navegando al perfil @{username}")
        self.page.goto(f'https://www.instagram.com/{username}/')
        self.page.wait_for_load_state('networkidle')
        self.human_delay(2, 4)

        # Verificar que el perfil existe
        if self.page.locator('text="Esta página no está disponible"').is_visible():
            raise Exception(f"El perfil @{username} no existe o es privado")

    def get_profile_stats(self):
        """Obtiene estadísticas básicas del perfil."""
        try:
            # Buscar el contador de seguidores
            followers_text = self.page.locator('a[href*="/followers/"] span').first.inner_text()
            following_text = self.page.locator('a[href*="/following/"] span').first.inner_text()

            return {
                'followers': self.parse_count(followers_text),
                'following': self.parse_count(following_text)
            }
        except Exception as e:
            print(f"[!] Error obteniendo estadísticas: {e}")
            return {'followers': 0, 'following': 0}

    def parse_count(self, text):
        """Convierte texto como '1.5K' a número."""
        text = text.replace(',', '').replace('.', '')
        if 'K' in text:
            return int(float(text.replace('K', '')) * 1000)
        elif 'M' in text:
            return int(float(text.replace('M', '')) * 1000000)
        else:
            return int(text) if text.isdigit() else 0

    def click_followers(self):
        """Hace click en la lista de seguidores."""
        print("[→] Abriendo lista de seguidores...")
        self.page.click('a[href*="/followers/"]')
        self.page.wait_for_selector('[role="dialog"]', timeout=10000)
        self.human_delay(2, 3)

    def click_following(self):
        """Hace click en la lista de seguidos."""
        print("[→] Abriendo lista de seguidos...")
        self.page.click('a[href*="/following/"]')
        self.page.wait_for_selector('[role="dialog"]', timeout=10000)
        self.human_delay(2, 3)

    def collect_users_from_modal(self, max_users=500, user_type="usuarios"):
        """Recolecta usuarios del modal abierto."""
        users = set()
        consecutive_no_new = 0
        max_consecutive = 5

        print(f"[→] Recolectando {user_type}...")

        modal = self.page.locator('[role="dialog"]')

        while len(users) < max_users and consecutive_no_new < max_consecutive:
            # Obtener usuarios actuales en el modal
            user_links = modal.locator('a[href*="/"][href*="/"][href*="/"]').all()

            current_batch = set()
            for link in user_links:
                try:
                    href = link.get_attribute('href')
                    if href and href.count('/') >= 2:
                        username = href.split('/')[1]
                        if username and not username.startswith(('#', 'explore', 'reels')):
                            current_batch.add(username)
                except:
                    continue

            # Verificar si hay nuevos usuarios
            new_users = current_batch - users
            if new_users:
                users.update(new_users)
                consecutive_no_new = 0
                print(f"[→] {user_type.capitalize()}: {len(users)}")
            else:
                consecutive_no_new += 1

            # Scroll dentro del modal
            modal.scroll_into_view_if_needed()
            modal.evaluate('element => element.scrollTop += 400')

            # Delay humano más largo para evitar rate limiting
            self.human_delay(2, 4)

            # Verificar si hemos llegado al final
            if consecutive_no_new >= 3:
                # Intentar scroll más agresivo
                modal.evaluate('element => element.scrollTop = element.scrollHeight')
                self.human_delay(3, 5)

        return users

    def close_modal(self):
        """Cierra el modal actual."""
        try:
            # Buscar botón de cerrar
            close_selectors = [
                '[aria-label="Cerrar"]',
                '[aria-label="Close"]',
                'svg[aria-label="Cerrar"]',
                'button:has(svg[aria-label="Cerrar"])'
            ]

            for selector in close_selectors:
                if self.page.locator(selector).is_visible():
                    self.page.click(selector)
                    self.human_delay(1, 2)
                    break
        except:
            # Alternativamente, presionar Escape
            self.page.keyboard.press('Escape')
            self.human_delay(1, 2)

    def analyze_account(self, target_username, max_users_per_list=300):
        """Analiza una cuenta completa."""
        print(f"\n=== ANALIZANDO @{target_username} ===")

        # Ir al perfil
        self.go_to_profile(target_username)

        # Obtener estadísticas básicas
        stats = self.get_profile_stats()
        print(f"[→] Seguidores: {stats['followers']:,} | Siguiendo: {stats['following']:,}")

        # Obtener seguidores
        self.click_followers()
        self.followers = self.collect_users_from_modal(max_users_per_list, "seguidores")
        self.close_modal()

        self.human_delay(3, 5)  # Delay más largo entre listas

        # Obtener seguidos
        self.click_following()
        self.following = self.collect_users_from_modal(max_users_per_list, "seguidos")
        self.close_modal()

        # Calcular análisis
        not_following_back = self.following - self.followers
        not_followed_back = self.followers - self.following

        results = {
            'target_username': target_username,
            'stats': stats,
            'followers': self.followers,
            'following': self.following,
            'not_following_back': not_following_back,
            'not_followed_back': not_followed_back,
            'analysis_date': datetime.now().isoformat()
        }

        return results

    def save_results(self, results, filename=None):
        """Guarda los resultados en un archivo JSON."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"instagram_analysis_{results['target_username']}_{timestamp}.json"

        # Convertir sets a listas para JSON
        json_data = {
            'target_username': results['target_username'],
            'analysis_date': results['analysis_date'],
            'stats': results['stats'],
            'summary': {
                'followers_collected': len(results['followers']),
                'following_collected': len(results['following']),
                'not_following_back_count': len(results['not_following_back']),
                'not_followed_back_count': len(results['not_followed_back'])
            },
            'followers': sorted(list(results['followers'])),
            'following': sorted(list(results['following'])),
            'not_following_back': sorted(list(results['not_following_back'])),
            'not_followed_back': sorted(list(results['not_followed_back']))
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"[✓] Resultados guardados en {filename}")

        # También crear un archivo de texto resumido
        txt_filename = filename.replace('.json', '_resumen.txt')
        self.create_text_summary(json_data, txt_filename)

    def create_text_summary(self, data, filename):
        """Crea un resumen en texto plano."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== ANÁLISIS DE INSTAGRAM: @{data['target_username']} ===\n")
            f.write(f"Fecha: {data['analysis_date']}\n\n")

            f.write("=== ESTADÍSTICAS ===\n")
            f.write(f"Seguidores totales: {data['stats']['followers']:,}\n")
            f.write(f"Siguiendo totales: {data['stats']['following']:,}\n")
            f.write(f"Seguidores analizados: {data['summary']['followers_collected']:,}\n")
            f.write(f"Siguiendo analizados: {data['summary']['following_collected']:,}\n\n")

            f.write("=== USUARIOS QUE NO TE SIGUEN DE VUELTA ===\n")
            f.write(f"Total: {len(data['not_following_back'])} usuarios\n\n")
            for user in data['not_following_back']:
                f.write(f"• @{user}\n")

            f.write(f"\n=== USUARIOS QUE TE SIGUEN PERO NO SIGUES ===\n")
            f.write(f"Total: {len(data['not_followed_back'])} usuarios\n\n")
            for user in data['not_followed_back']:
                f.write(f"• @{user}\n")

        print(f"[✓] Resumen guardado en {filename}")

    def close(self):
        """Cierra el navegador."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


def main():
    analyzer = InstagramPlaywrightAnalyzer()

    try:
        # Configuración
        print("=== INSTAGRAM ANALYZER CON PLAYWRIGHT ===\n")

        headless = input("¿Ejecutar en modo invisible? (s/n): ").lower() == 's'
        analyzer.setup_browser(headless=headless)

        # Credenciales
        username = input("Tu usuario de Instagram: ")
        password = input("Tu contraseña: ")
        target_account = input("Cuenta a analizar: ")

        max_users = input("Máximo usuarios por lista (default: 300): ")
        max_users = int(max_users) if max_users.isdigit() else 300

        # Ejecutar análisis
        analyzer.login(username, password)
        results = analyzer.analyze_account(target_account, max_users)
        analyzer.save_results(results)

        # Mostrar resumen
        print(f"\n=== RESUMEN FINAL ===")
        print(f"Seguidores analizados: {len(results['followers']):,}")
        print(f"Siguiendo analizados: {len(results['following']):,}")
        print(f"No te siguen de vuelta: {len(results['not_following_back']):,}")
        print(f"Te siguen pero no sigues: {len(results['not_followed_back']):,}")

    except Exception as e:
        print(f"\n[✗] Error durante el análisis: {e}")
        print("[!] Recomendación: Espera unos minutos antes de intentar de nuevo")

    finally:
        analyzer.close()
        print("\n[✓] Análisis completado")


if __name__ == "__main__":
    main()