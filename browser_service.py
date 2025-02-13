from DrissionPage import ChromiumOptions, Chromium
import sys
import os
import json
from user_agent_service import UserAgentService

class BrowserService:
    def __init__(self, headless=True):
        self.browser = None
        self.headless = headless
        self.user_agent_service = UserAgentService()

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

    def init_browser(self):
        """Tarayıcıyı başlatır"""
        self._print_status("init_browser_starting")
        co_generator = self._get_browser_options()
        try:
            while True:
                yield next(co_generator)
        except StopIteration as e:
            self.co = e.value
            self.quit()
            self.browser = self._get_browser_with_user_agent()

            return self.browser

    def _get_browser_with_user_agent(self):
        """Rastgele bir user agent ile tarayıcıyı yapılandırır"""
        try:
           user_agent = self.user_agent_service.get_random_user_agent()
           self.co.set_user_agent(user_agent)
           self.browser = Chromium(self.co)
           self._print_status("user_agent_set", {"user_agent": user_agent})
           return self.browser
        except Exception as e:
            self.browser = Chromium(self.co)
            return self.browser

    def _get_browser_options(self):
        """Tarayıcı ayarlarını yapılandırır"""

        co = ChromiumOptions()

        co.set_argument("--lang=en-US")  # Dili İngilizce'ye ayarla
        co.set_pref("intl.accept_languages", "en-US")

        try:
            extension_path_generator = self._get_extension_path()
            while True:
                yield next(extension_path_generator)
        except StopIteration as e:
            if e.value:
                co.add_extension(e.value)
        except Exception as e:
            yield f"Chrome extension loading error: {e}"

        co.set_pref("credentials_enable_service", False)
        co.set_argument("--hide-crash-restore-bubble")
        co.auto_port()


        # Headless (tarayıcı görünürlüğü) mod ayarı
        if self.headless:
            co.set_argument("--headless=new")

        # Mac ve Linux sistemlerinde performans için özel ayarlar
        if sys.platform in ["darwin", "linux"]:
            co.set_argument("--no-sandbox")
            co.set_argument("--disable-gpu")

        return co

    def _get_extension_path(self):
        """Turnstile Patch eklentisinin yolunu döndürür"""
        try:
            extension_path = os.path.join(os.path.dirname(__file__), "turnstilePatch")

            if not os.path.exists(extension_path):
                raise FileNotFoundError(
                    f"Extension directory not found: {extension_path}"
                )

            # Dizin içeriğini kontrol et
            if not os.path.exists(os.path.join(extension_path, "manifest.json")):
                raise FileNotFoundError(
                    f"manifest.json not found in extension directory"
                )

            return extension_path

        except Exception as e:
            yield f"Extension path error: {str(e)}"
            return None

    def quit(self):
        """Tarayıcıyı kapatır"""
        if self.browser:
            self.browser.quit()
