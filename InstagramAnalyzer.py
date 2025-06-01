# instagram_analyzer.py
import instaloader
import time
import random
from instaloader.exceptions import ConnectionException, QueryReturnedBadRequestException


class InstagramAnalyzer:
    def __init__(self, username):
        self.username = username
        self.loader = instaloader.Instaloader(
            sleep=True,  # Activa delays automáticos
            quiet=False,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.profile = None
        self.followers = set()
        self.followees = set()

    def login(self):
        """Carga sesión desde archivo local o solicita login."""
        try:
            self.loader.load_session_from_file(self.username)
            print("[✓] Sesión cargada correctamente.")
            return True
        except FileNotFoundError:
            print("[!] No se encontró una sesión guardada. Iniciando sesión manual.")
            password = input("Introduce tu contraseña de Instagram: ")
            try:
                self.loader.login(self.username, password)
                self.loader.save_session_to_file()
                print("[✓] Sesión iniciada y guardada.")
                return True
            except Exception as e:
                print(f"[✗] Error al iniciar sesión: {e}")
                return False

    def safe_request(self, func, *args, **kwargs):
        """Ejecuta una función con manejo de errores y reintentos."""
        max_retries = 3
        base_delay = 60  # 1 minuto base

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (ConnectionException, QueryReturnedBadRequestException) as e:
                if "429" in str(e) or "rate limit" in str(e).lower():
                    delay = base_delay * (2 ** attempt) + random.randint(30, 120)
                    print(f"[!] Rate limit detectado. Esperando {delay} segundos...")
                    time.sleep(delay)
                elif "401" in str(e):
                    print("[!] Error 401: Posible problema de autenticación o rate limit severo.")
                    delay = 300 + random.randint(60, 180)  # 5-8 minutos
                    print(f"[!] Esperando {delay} segundos antes del siguiente intento...")
                    time.sleep(delay)
                else:
                    print(f"[!] Error en intento {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(30 + random.randint(10, 30))

        raise Exception(f"Falló después de {max_retries} intentos")

    def fetch_profile_data(self):
        """Carga el perfil y obtiene seguidores/seguidos con manejo de errores."""
        try:
            print("[→] Cargando perfil...")
            self.profile = self.safe_request(
                instaloader.Profile.from_username,
                self.loader.context,
                self.username
            )

            print(f"[✓] Perfil cargado: @{self.profile.username}")
            print(f"[→] Total seguidores: {self.profile.followers}")
            print(f"[→] Total seguidos: {self.profile.followees}")

            # Obtener seguidores con delays
            print("[→] Obteniendo lista de seguidores...")
            self.followers = self._get_followers_safely()

            print("[→] Obteniendo lista de seguidos...")
            self.followees = self._get_followees_safely()

            print(f"[✓] Datos obtenidos - Seguidores: {len(self.followers)} | Seguidos: {len(self.followees)}")

        except Exception as e:
            print(f"[✗] Error al obtener datos del perfil: {e}")
            raise

    def _get_followers_safely(self):
        """Obtiene seguidores con manejo de rate limiting."""
        followers = set()
        count = 0

        try:
            for follower in self.profile.get_followers():
                followers.add(follower.username)
                count += 1

                # Delay progresivo cada cierta cantidad
                if count % 100 == 0:
                    delay = random.randint(30, 60)
                    print(f"[→] Procesados {count} seguidores. Pausa de {delay}s...")
                    time.sleep(delay)
                elif count % 20 == 0:
                    time.sleep(random.randint(5, 15))

        except Exception as e:
            print(f"[!] Error obteniendo seguidores: {e}")
            print(f"[→] Se obtuvieron {len(followers)} seguidores antes del error")

        return followers

    def _get_followees_safely(self):
        """Obtiene seguidos con manejo de rate limiting."""
        followees = set()
        count = 0

        try:
            for followee in self.profile.get_followees():
                followees.add(followee.username)
                count += 1

                # Delay progresivo cada cierta cantidad
                if count % 100 == 0:
                    delay = random.randint(30, 60)
                    print(f"[→] Procesados {count} seguidos. Pausa de {delay}s...")
                    time.sleep(delay)
                elif count % 20 == 0:
                    time.sleep(random.randint(5, 15))

        except Exception as e:
            print(f"[!] Error obteniendo seguidos: {e}")
            print(f"[→] Se obtuvieron {len(followees)} seguidos antes del error")

        return followees

    def get_not_following_back(self):
        """Usuarios que tú sigues pero no te siguen."""
        not_following_back = self.followees - self.followers
        print(f"[→] Usuarios que no te siguen de vuelta: {len(not_following_back)}")
        return not_following_back

    def get_not_followed_by_you(self):
        """Usuarios que te siguen pero tú no sigues."""
        not_followed = self.followers - self.followees
        print(f"[→] Usuarios que te siguen pero no sigues: {len(not_followed)}")
        return not_followed

    #def save_results(self, filename="instagram_analysis.txt"):
    #    """Guarda los resultados en un archivo."""
    #    not_following_back = self.get_not_following_back()
    #    not_followed = self.get_not_followed_by_you()
    #
    #    with open(filename, 'w', encoding='utf-8') as f:
    #        f.write(f"=== ANÁLISIS DE INSTAGRAM PARA @{self.username} ===\n\n")
    #        f.write(f"Total seguidores: {len(self.followers)}\n")
    #        f.write(f"Total seguidos: {len(self.followees)}\n\n")
    #
    #        f.write("=== USUARIOS QUE NO TE SIGUEN DE VUELTA ===\n")
    #        for user in sorted(not_following_back):
    #            f.write(f"- @{user}\n")
    #
    #        f.write(f"\n=== USUARIOS QUE TE SIGUEN PERO NO SIGUES ===\n")
    #        for user in sorted(not_followed):
    #            f.write(f"- @{user}\n")

        print(f"[✓] Resultados guardados en {filename}")
