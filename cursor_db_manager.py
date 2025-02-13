import os
import sqlite3
import platform
from pathlib import Path
import json
import sys
import argparse

class CursorDatabaseManager:
    def __init__(self):
        self.storage = Storage()
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
        if isinstance(error, Exception):
            error = str(error).replace('\n', ' ').strip()

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
            self._print_status("Cursor Database Manager: No updates")
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
                    self._print_status(f"Cursor Database Manager: Update success: {key.split('/')[-1]}")
                else:
                    self._print_error(f"Cursor Database Manager: Update failed: {key.split('/')[-1]}")

            conn.commit()
            self._print_status("OK")
            return True

        except sqlite3.Error as e:
            self._print_error(f"Cursor Database Manager: DB Error: {str(e)}")
            return False
        except Exception as e:
            self._print_error(f"Cursor Database Manager: Error: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()


class Storage:
    def __init__(self):
        self.system = platform.system()


    def is_windows(self):
        return self.system == "Windows"

    def is_macos(self):
        return self.system == "Darwin"

    def cursor_global_storage_path(self):
        # :: Windows
        if self.is_windows():
            appdata = os.getenv("APPDATA")
            return os.path.join(appdata, "Cursor", "User", "globalStorage")
        # :: MacOS
        elif self.is_macos():
            home = str(Path.home())
            return os.path.join(
                home,
                "Library",
                "Application Support",
                "Cursor",
                "User",
                "globalStorage",
            )
        # :: Linux
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
    parser = argparse.ArgumentParser(description='Cursor Database Manager CLI')
    parser.add_argument('--email', help='Email address for authentication')
    parser.add_argument('--access-token', help='Access token for authentication')
    parser.add_argument('--refresh-token', help='Refresh token for authentication')

    args = parser.parse_args()

    db_manager = CursorDatabaseManager()
    db_manager.update_auth(
        email=args.email,
        access_token=args.access_token,
        refresh_token=args.refresh_token
    )

if __name__ == '__main__':
    main()
