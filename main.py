# main.py
from InstagramAnalyzer import InstagramAnalyzer


def main():
    username = input("Introduce tu nombre de usuario de Instagram: ")
    analyzer = InstagramAnalyzer(username)

    analyzer.login()
    analyzer.fetch_profile_data()

    print("\n👤 Usuarios que tú sigues pero no te siguen:")
    for user in sorted(analyzer.get_not_following_back()):
        print(f"  - {user}")

    print("\n👤 Usuarios que te siguen pero tú no sigues:")
    for user in sorted(analyzer.get_not_followed_by_you()):
        print(f"  - {user}")


if __name__ == "__main__":
    main()
