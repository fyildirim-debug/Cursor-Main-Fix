import requests
import time
import imaplib
from email import message_from_bytes
import random
import json
import sys
from datetime import datetime, timedelta


class EmailService:
    def __init__(self, imap_settings=None):
        self.mail_api_url = "https://tempmail.so/us/api"
        self.email = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Content-Type": "application/json",
            "Sec-Ch-Ua-Platform": "Windows",
            "X-Inbox-Lifespan": "600",
            "Sec-Ch-Ua": "Chromium;v=131, Not_A Brand;v=24",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://tempmail.so/",
        }
        self.session_cookie = None
        self.tm_session = ""
        self.imap_settings = imap_settings

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


    def _process_cookie(self, set_cookie):
        """Set-Cookie header'ından tm_session cookie'sini ayıklar"""
        if not set_cookie:
            return None

        try:
            tm_sessions = set_cookie.split("tm_session=")
            if len(tm_sessions) > 2:
                cookie_value = tm_sessions[-1]
            elif len(tm_sessions) == 2:
                cookie_value = tm_sessions[1]
            else:
                cookie_value = tm_sessions[0].split(";")[0]

            return cookie_value.split(";")[0]
        except Exception:
            return None

    def _update_headers_with_cookie(self):
        """Headers'ı cookie ile günceller"""
        if self.tm_session and "Cookie" not in self.headers:
            self.headers = self.headers | {"Cookie": f"tm_session={self.tm_session}"}

    def create_email(self):
        """Yeni bir email adresi oluşturur"""
        self._print_status("creating_email")

        try:
            if self.imap_settings:
                email_parts = self.imap_settings["IMAP_USER"].split("@")
                domain = email_parts[1]
                is_gmail = domain == "gmail.com"

                if is_gmail and random.random() < 0.5:
                    domain = "googlemail.com"

                username = email_parts[0]
                if not is_gmail:
                    username_chars = list(username)
                    num_dots = random.randint(1, len(username) - 1)
                    dot_positions = random.sample(range(1, len(username)), num_dots)

                    for pos in sorted(dot_positions, reverse=True):
                        username_chars.insert(pos, ".")

                    new_username = "".join(username_chars)
                    email = f"{new_username}@{domain}"
                else:
                    email = f"{username}@{domain}"

                self._print_status("email_created", {"email": email})
                return email, None

            response = requests.get(f"{self.mail_api_url}/inbox", headers=self.headers)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0 and result.get("message") == "Success":
                    data = result.get("data", {})
                    self.email = data.get("name")

                    set_cookie = response.headers.get("Set-Cookie", "")
                    cookie_value = self._process_cookie(set_cookie)

                    if cookie_value:
                        self.tm_session = cookie_value
                        self._update_headers_with_cookie()

                    self._print_status("email_created", {"email": self.email})
                    return self.email, None

            self._print_status("email_creation_failed")
            return None, None

        except Exception as e:
            self._print_error(str(e))
            return None, None

    def get_verification_code(self, email, max_attempts=20, delay=2):
        """E-posta adresine gelen doğrulama kodunu alır"""
        self._print_status("verification_starting")

        try:
            if self.imap_settings:
                code = self._get_verification_code_imap(email, max_attempts, delay)
            else:
                code = self._get_verification_code_api(email, max_attempts, delay)
            return code

        except Exception as e:
            self._print_error(f"verification_failed", {"error": str(e)})
            return None

    def _get_verification_code_api(self, email, max_attempts, delay):
        """API için doğrulama kodunu alır"""
        import re

        for attempt in range(max_attempts):
            self._print_status("checking_inbox", {"attempt": attempt + 1})
            try:
                response = requests.get(f"{self.mail_api_url}/inbox", headers=self.headers)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0 and result.get("message") == "Success":
                        data = result.get("data", {})
                        inbox = data.get("inbox", [])

                        if inbox:
                            for message in inbox:
                                text_body = message.get("textBody", "")
                                code_match = re.search(r"\b(\d{6})\b", text_body)
                                if code_match:
                                    verification_code = code_match.group(1)
                                    self._print_status("code_found", {"code": verification_code})
                                    return verification_code

                time.sleep(delay)

            except Exception as e:
                self._print_error("mail_api_error", {"error": str(e)})
                time.sleep(delay)

        self._print_status("verification_failed")
        return None

    def _get_verification_code_imap(self, email, max_attempts, delay):
        """IMAP üzerinden doğrulama kodunu alır"""
        for attempt in range(max_attempts):
            self._print_status("connecting_imap")
            try:
                imap = imaplib.IMAP4_SSL(
                    self.imap_settings["IMAP_SERVER"],
                    int(self.imap_settings["IMAP_PORT"]),
                )
                imap.login(
                    self.imap_settings["IMAP_USER"],
                    self.imap_settings["IMAP_PASS"]
                )
                self._print_status("imap_connected")
                imap.select("INBOX")

                one_minute_ago = (datetime.now() - timedelta(minutes=1)).strftime("%d-%b-%Y")
                _, messages = imap.search(
                    None,
                    "UNSEEN",
                    f'(FROM "no-reply@cursor.sh" SINCE "{one_minute_ago}")'
                )
                message_nums = messages[0].split()

                if not message_nums:
                    self._print_status("waiting_for_email")
                    imap.close()
                    imap.logout()
                    time.sleep(delay)
                    continue

                latest_email_id = message_nums[-1]
                _, msg_data = imap.fetch(latest_email_id, "(RFC822)")
                email_body = message_from_bytes(msg_data[0][1])

                body_text = ""
                if email_body.is_multipart():
                    for part in email_body.walk():
                        if part.get_content_type() in ["text/plain", "text/html"]:
                            try:
                                content = part.get_payload(decode=True).decode()
                                body_text += content + "\n"
                            except Exception as e:
                                self._print_error("imap_content_read_error", {"error": str(e)})
                                continue
                else:
                    body_text = email_body.get_payload(decode=True).decode()


                import re
                codes = re.findall(r"\b\d{6}\b", body_text)

                if codes:
                    code = codes[0]
                    self._print_status("code_found", {"code": code})

                    imap.store(latest_email_id, "+FLAGS", "\\Deleted")
                    imap.expunge()
                    imap.close()
                    imap.logout()
                    return code

                imap.close()
                imap.logout()
                time.sleep(delay)

            except Exception as e:
                self._print_error("imap_error", {"error": str(e)})
                return None


        self._print_status("verification_failed")
        return None
