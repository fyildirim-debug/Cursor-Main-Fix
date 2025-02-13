import json
import os
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time

class UserAgentService:
    def __init__(self):
        self.user_agents_url = "https://www.whatismybrowser.com/guides/the-latest-user-agent/android"
        self.cache_file = os.path.join(os.path.dirname(__file__), "user_agents_cache.json")
        self.cache_duration = timedelta(days=1)

    def _is_cache_valid(self):
        """Cache dosyasının geçerli olup olmadığını kontrol eder"""
        if not os.path.exists(self.cache_file):
            return False

        file_time = datetime.fromtimestamp(os.path.getmtime(self.cache_file))
        return datetime.now() - file_time < self.cache_duration

    def _fetch_user_agents(self):
        """User agent'ları web sitesinden scraping ile çeker. Başarısız olursa 3 saniye bekleyip tekrar dener."""
        for attempt in range(2):  # 2 deneme: ilk deneme ve bir tekrar
            try:
                response = requests.get(self.user_agents_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    user_agents = [span.text.strip() for span in soup.select("span.code")]
                    return user_agents if user_agents else None

                if attempt == 0:  # İlk denemede başarısız olduysa
                    time.sleep(3)  # 3 saniye bekle
                    continue

                return None
            except Exception as e:
                if attempt == 0:  # İlk denemede hata aldıysa
                    time.sleep(3)  # 3 saniye bekle
                    continue
                return None

    def _save_to_cache(self, user_agents):
        """User agent'ları cache dosyasına kaydeder"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(user_agents, f)
        except Exception as e:
            pass

    def _read_from_cache(self):
        """Cache dosyasından user agent'ları okur"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return None

    def get_random_user_agent(self):
        """Rastgele bir user agent döndürür"""
        import random

        if not self._is_cache_valid():
            user_agents = self._fetch_user_agents()
            if user_agents:
                self._save_to_cache(user_agents)
        else:
            user_agents = self._read_from_cache()

        if not user_agents:
            return None

        return random.choice(user_agents)
