import sqlite3
import time
import random
import argparse
import os
import re
import sys
import json
from pathlib import Path
from browser_service import BrowserService
from email_service import EmailService
from enum import Enum
from typing import Optional

class VerificationStatus(Enum):
    PASSWORD_PAGE = "@name=password"
    CAPTCHA_PAGE = "@data-index=0"
    ACCOUNT_SETTINGS = "Account Settings"

class CursorAuthManager:
    def __init__(self, headless=True, platform_name="windows"):
        self.browser_service = BrowserService(headless=headless)
        self.account_data = {}
        self.platform_name = platform_name
        self.email_service = None
        self.LOGIN_URL = "https://authenticator.cursor.sh"
        self.SIGN_UP_URL = "https://authenticator.cursor.sh/sign-up"
        self.SETTINGS_URL = "https://www.cursor.com/settings"

    def _generate_browser(self):
        browser_generator = self.browser_service.init_browser()

        try:
            while True:
                yield next(browser_generator)
        except StopIteration as e:
            self.browser = e.value

    def _check_verification_success(self, tab) -> Optional[VerificationStatus]:
            for status in VerificationStatus:
                if tab.ele(status.value):
                    return status
            return None

    def handle_turnstile(self, tab, max_attempts=10, retry_interval=1):
        """Turnstile doğrulamasını yönetir.

        Args:
            tab: Tarayıcı sekmesi
            max_attempts: Maksimum deneme sayısı
            retry_interval: Denemeler arası bekleme süresi

        Yields:
            bool: Doğrulama başarılı ise True, değilse False
        """
        self._print_status("turnstile_starting")

        success_selectors = ["@name=password", "@data-index=0", "Account Settings"]
        attempts = 0

        while attempts < max_attempts:
            try:
                # Turnstile iframe'ini bul ve tıkla
                challenge = (
                    tab.ele("@id=cf-turnstile", timeout=2)
                    .child()
                    .shadow_root.ele("tag:iframe")
                    .ele("tag:body")
                    .sr("tag:input")
                )

                if challenge:
                    self._print_status("turnstile_started")
                    time.sleep(random.uniform(1, 3))
                    challenge.click()
                    time.sleep(2)

                    if self._check_verification_success(tab):
                        self._print_status("turnstile_success")
                        return

            except Exception as e:
                self._print_error(f"turnstile_attempt_failed: {str(e)}")

            if self._check_verification_success(tab):
                return

            attempts += 1
            time.sleep(retry_interval)

        self._print_error("turnstile_failed", {"max_attempts": max_attempts})

    def get_cursor_session_token(self, tab, max_attempts=3, retry_interval=2):
        self._print_status("getting_token")
        attempts = 0

        while attempts < max_attempts:
            try:
                cookies = tab.cookies()
                for cookie in cookies:
                    if cookie.get("name") == "WorkosCursorSessionToken":
                        raw_token = cookie["value"]
                        return (raw_token, raw_token.split("%3A%3A")[1])

                attempts += 1
                if attempts < max_attempts:
                    tab.refresh()
                    self._print_status("token_retry", {"attempts": attempts})
                    time.sleep(retry_interval)
                else:
                    self._print_status("max_attempts_reached")

            except Exception as e:
                self._print_error("token_error", {"error": str(e)})
                attempts += 1
                if attempts < max_attempts:
                    time.sleep(retry_interval)


        return (None, None)

    def _print_status(self, status, data=None):
        if self._contains_chinese(status):
            return

        output = {
            "status": status
        }

        if data:
            output["data"] = data
        print(json.dumps(output))
        sys.stdout.flush()

    def _contains_chinese(self, text):
        chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3000-\u303f\uf900-\ufaff]')
        return bool(chinese_pattern.search(text))

    def _print_error(self, error, data=None):
        if self._contains_chinese(error):
            return

        if isinstance(error, Exception):
            error = str(error).replace('\n', ' ').strip()

        output = {
            "error": error
        }
        if data:
            output["data"] = data
        sys.stderr.write(json.dumps(output) + "\n")


    def update_cursor_auth(self, email=None, access_token=None, refresh_token=None):
        database_manager = CursorDatabaseManager(self.platform_name)
        return database_manager.update_auth(email, access_token, refresh_token)

    def _get_random_name(self):
        """Rastgele bir isim döndürür"""
        first_names = ["Marry", "Jane", "Michael", "Stephanie", "David", "Sarah"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]
        return random.choice(first_names), random.choice(last_names)



    def _generate_password(self, length=12):
        """Güçlü bir şifre oluşturur."""

        letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        numbers = "0123456789"
        special_chars = "!@#$%^&*"
        all_chars = letters + numbers + special_chars

        while True:
            password = "".join(random.choice(all_chars) for _ in range(length))
            # En az bir harf ve bir rakam içerdiğinden emin oluyoruz
            if any(c in letters for c in password) and any(
                c in numbers for c in password
            ):
                return password

    def sign_up_account(self, tab):
        self._print_status("signup_starting")

        email, _ = self.email_service.create_email()
        self._print_status("email_created", {"email": email})
        if not email:
            self._print_error("email_creation_failed")
            return False


        password = self._generate_password()
        first_name, last_name = self._get_random_name()

        tab.get(self.SIGN_UP_URL)

        try:
            if tab.ele("@name=first_name"):
                tab.actions.click("@name=first_name").input(first_name)
                time.sleep(random.uniform(0, 1))

                tab.actions.click("@name=last_name").input(last_name)
                time.sleep(random.uniform(0, 1))

                tab.actions.click("@name=email").input(email)
                time.sleep(random.uniform(1, 2))

                tab.actions.click("@type=submit")

        except Exception as e:
            self._print_error("registration_page_error", {"error": str(e)})
            return False

        self.handle_turnstile(tab)

        try:
            if tab.ele("@name=password"):
                tab.ele("@name=password").input(password)
                time.sleep(random.uniform(1, 2))

                tab.ele("@type=submit").click()
                self._print_status("processing")

        except Exception as e:
            self._print_error("operation_failed", {"error": str(e)})
            return False

        time.sleep(random.uniform(1, 2))
        if tab.ele("This email is not available."):
            self._print_error("email_unavailable")
            return False
        elif tab.ele("Sign up is restricted."):
            self._print_error("sign_up_restricted")
            return False

        code = None
        turnstile_checked = False
        while True:
            try:
                if tab.ele("Account Settings"):
                    break
                if tab.ele("@data-index=0"):
                    code = self.email_service.get_verification_code(email)

                    if code:
                        for i, digit in enumerate(code):
                            tab.ele(f"@data-index={i}").input(digit)
                            time.sleep(random.uniform(0.3, 0.6))

                        time.sleep(1)
                    break
                else:
                    if not turnstile_checked:
                        turnstile_checked = True
                        self.handle_turnstile(tab)
            except Exception as e:
                self._print_error("verification_code_error", {"error": str(e)})

        self.handle_turnstile(tab)

        wait_time = random.randint(3, 5)
        for i in range(wait_time):
            self._print_status("waiting", {"seconds_remaining": wait_time - i})
            time.sleep(1)

        tab.get(self.SETTINGS_URL)
        time.sleep(1)
        try:
            usage_selector = (
                "css:div.col-span-2 > div > div > div > div > "
                "div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > "
                "span.font-mono.text-sm\\/\\[0\\.875rem\\]"
            )
            usage_ele = tab.ele(usage_selector)
            if usage_ele:
                usage_info = usage_ele.text
                total_usage = usage_info.split("/")[-1].strip()
                self._print_status("usage_limit", {"limit": total_usage})
        except Exception as e:
            self._print_error("usage_limit_error", {"error": str(e)})

        self.account_data = {
            "email": email,
            "password": password,
        }
        return True

    def create_cursor_account(self):
        email = None
        try:
            yield from self._generate_browser()
            tab = self.browser.latest_tab
            tab.run_js("try { turnstile.reset() } catch(e) { }")

            tab.get(self.LOGIN_URL)

            signup_success = self.sign_up_account(tab)
            if signup_success:
                raw_token, token = self.get_cursor_session_token(tab)
                if token and raw_token and isinstance(token, str):
                    email = self.email_service.email
                    try:
                        self.update_cursor_auth(
                            email=email,
                            access_token=token,
                            refresh_token=token,
                        )
                        self.account_data["token"] = raw_token
                        self._print_status("account_created", self.account_data)
                        self._print_status("OK")
                    except Exception as e:
                        self._print_error("auth_update_error", {"error": str(e)})
                else:
                    self._print_error("token_not_found")

            self._print_status("completed")

        except Exception as e:
            self._print_error(str(e))

        finally:
            if hasattr(self, 'browser') and self.browser:
                try:
                    self.browser.quit()
                except Exception as e:
                    self._print_error("browser_quit_error", {"error": str(e)})



class CursorDatabaseManager:
    def __init__(self, platform_name):
        self.storage = Storage(platform_name)
        self.db_path = self.storage.cursor_db_path()

    def _print_status(self, status, data=None):
        output = {
            "status": status
        }
        if data:
            output["data"] = data
        print(json.dumps(output))
        sys.stdout.flush()

    def _print_error(self, error, data=None):
        output = {
            "error": error
        }
        if data:
            output["data"] = data
        sys.stderr.write(json.dumps(output) + "\n")


    def update_auth(self, email=None, access_token=None, refresh_token=None):
        updates = []
        updates.append(("cursorAuth/cachedSignUpType", "Auth_0"))

        if email is not None:
            updates.append(("cursorAuth/cachedEmail", email))
        if access_token is not None:
            updates.append(("cursorAuth/accessToken", access_token))
        if refresh_token is not None:
            updates.append(("cursorAuth/refreshToken", refresh_token))

        if not updates:
            self._print_status("no_update_values")
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for key, value in updates:
                check_query = "SELECT COUNT(*) FROM itemTable WHERE key = ?"
                cursor.execute(check_query, (key,))
                if cursor.fetchone()[0] == 0:
                    insert_query = "INSERT INTO itemTable (key, value) VALUES (?, ?)"
                    cursor.execute(insert_query, (key, value))
                else:
                    update_query = "UPDATE itemTable SET value = ? WHERE key = ?"
                    cursor.execute(update_query, (value, key))

                if cursor.rowcount > 0:
                    self._print_status("auth_update_success")
                else:
                    self._print_status("auth_update_failed", {"field": key.split("/")[-1]})

            conn.commit()
            return True

        except sqlite3.Error as e:
            self._print_error("database_error", {"error": str(e)})
            return False
        except Exception as e:
            self._print_error("auth_error", {"error": str(e)})

            return False
        finally:
            if conn:
                conn.close()

class Storage:
    def __init__(self, platform_name):
        self.platform_name = platform_name.lower()

    def cursor_global_storage_path(self):
        if self.platform_name == "windows":
            appdata = os.getenv("APPDATA")
            return os.path.join(appdata, "Cursor", "User", "globalStorage")
        elif self.platform_name == "macos":
            home = str(Path.home())
            return os.path.join(
                home,
                "Library",
                "Application Support",
                "Cursor",
                "User",
                "globalStorage",
            )
        else:
            home = str(Path.home())
            return os.path.join(home, ".config", "Cursor", "User", "globalStorage")

    def cursor_storage_json_path(self):
        return os.path.join(self.cursor_global_storage_path(), "storage.json")

    def cursor_storage_json_exist(self):
        return os.path.exists(self.cursor_storage_json_path())

    def cursor_db_path(self):
        return os.path.join(self.cursor_global_storage_path(), "state.vscdb")

    def cursor_db_exist(self):
        return os.path.exists(self.cursor_db_path())


def main():
    parser = argparse.ArgumentParser(description='Cursor Auth')
    parser.add_argument('--headless', action='store_true', default=True)
    parser.add_argument('--visible', action='store_false', dest='headless')
    parser.add_argument('--email-verifier', choices=['temp', 'imap'], default='temp')
    parser.add_argument('--imap-server', default='imap.gmail.com')
    parser.add_argument('--imap-port', default='993')
    parser.add_argument('--imap-user', default='xxxx@gmail.com')
    parser.add_argument('--imap-pass', default='')
    parser.add_argument('--platform',
                       choices=['windows', 'macos', 'linux'],
                       default='windows',
                       help='(windows, macos, linux)')

    args = parser.parse_args()

    cursor_manager = CursorAuthManager(headless=args.headless, platform_name=args.platform)

    if args.email_verifier == 'imap':
        imap_settings = {
            'IMAP_SERVER': args.imap_server,
            'IMAP_PORT': args.imap_port,
            'IMAP_USER': args.imap_user,
            'IMAP_PASS': args.imap_pass
        }
        cursor_manager.email_service = EmailService(imap_settings=imap_settings)
    else:
        cursor_manager.email_service = EmailService()

    for message in cursor_manager.create_cursor_account():
        print(json.dumps({"message": message, "timestamp": time.time()}, ensure_ascii=False))
        sys.stdout.flush()

if __name__ == "__main__":
    main()
