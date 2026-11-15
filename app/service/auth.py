import os
import json
import time
from app.client.ciam import get_new_token
from app.client.engsel import get_profile
from app.util import ensure_api_key


class Auth:
    _instance_ = None
    _initialized_ = False

    api_key = ""
    refresh_tokens = []
    active_user = None
    last_refresh_time = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance_:
            cls._instance_ = super().__new__(cls)
        return cls._instance_

    def __init__(self):
        if not self._initialized_:
            self.api_key = ensure_api_key()

            if os.path.exists("refresh-tokens.json"):
                self.load_tokens()
            else:
                with open("refresh-tokens.json", "w", encoding="utf-8") as f:
                    json.dump([], f, indent=4)

            try:
                self.load_active_number()
            except Exception as e:
                print(f"[auth] Auto-load active user gagal: {e}")

            self.last_refresh_time = int(time.time())
            self._initialized_ = True

    def load_tokens(self):
        try:
            with open("refresh-tokens.json", "r", encoding="utf-8") as f:
                refresh_tokens = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.refresh_tokens = []
            return

        self.refresh_tokens = []
        for rt in refresh_tokens:
            if "number" in rt and "refresh_token" in rt:
                self.refresh_tokens.append(rt)
            else:
                print(f"Invalid token entry: {rt}")

    def add_refresh_token(self, number: int, refresh_token: str) -> bool:
        existing = next((rt for rt in self.refresh_tokens if rt["number"] == number), None)
        if existing:
            existing["refresh_token"] = refresh_token
            self.write_tokens_to_file()
            return self.set_active_user(number)

        tokens = get_new_token(self.api_key, refresh_token, "")
        if not tokens:
            print(f"Gagal get_new_token untuk {number}.")
            return False

        access = tokens.get("access_token", "")
        idt = tokens.get("id_token", "")
        if not access or not idt:
            print("Response token tidak lengkap.")
            return False

        profile_data = get_profile(self.api_key, access, idt)
        if not isinstance(profile_data, dict) or "profile" not in profile_data:
            print("Gagal get_profile.")
            return False

        sub_id = profile_data["profile"].get("subscriber_id", "")
        sub_type = profile_data["profile"].get("subscription_type", "")

        self.refresh_tokens.append({
            "number": int(number),
            "subscriber_id": sub_id,
            "subscription_type": sub_type,
            "refresh_token": refresh_token,
        })
        self.write_tokens_to_file()

        return self.set_active_user(number)

    def remove_refresh_token(self, number: int):
        self.refresh_tokens = [rt for rt in self.refresh_tokens if rt["number"] != number]
        self.write_tokens_to_file()

        if self.active_user and self.active_user["number"] == number:
            if self.refresh_tokens:
                self.set_active_user(self.refresh_tokens[0]["number"])
            else:
                self.active_user = None
                if os.path.exists("active.number"):
                    os.remove("active.number")

    def set_active_user(self, number: int) -> bool:
        rt_entry = next((rt for rt in self.refresh_tokens if rt["number"] == number), None)
        if not rt_entry:
            print(f"No refresh token for: {number}")
            return False

        tokens = get_new_token(self.api_key, rt_entry["refresh_token"], rt_entry.get("subscriber_id", ""))
        if not tokens:
            print(f"Refresh token expired untuk {number}.")
            return False

        access = tokens.get("access_token", "")
        idt = tokens.get("id_token", "")
        if not access or not idt:
            return False

        profile_data = get_profile(self.api_key, access, idt)
        if not isinstance(profile_data, dict) or "profile" not in profile_data:
            return False

        subscriber_id = profile_data["profile"].get("subscriber_id", "")
        subscription_type = profile_data["profile"].get("subscription_type", "")

        self.active_user = {
            "number": int(number),
            "subscriber_id": subscriber_id,
            "subscription_type": subscription_type,
            "tokens": tokens,
        }
        rt_entry["subscriber_id"] = subscriber_id
        rt_entry["subscription_type"] = subscription_type
        rt_entry["refresh_token"] = tokens.get("refresh_token", rt_entry["refresh_token"])
        self.write_tokens_to_file()
        self.last_refresh_time = int(time.time())
        self.write_active_number()
        return True

    def renew_active_user_token(self) -> bool:
        if not self.active_user:
            return False

        tokens = get_new_token(
            self.api_key,
            self.active_user["tokens"]["refresh_token"],
            self.active_user["subscriber_id"],
        )
        if not tokens:
            print("Gagal renew token.")
            self.active_user = None
            return False

        self.active_user["tokens"] = tokens
        self.last_refresh_time = int(time.time())

        rt_entry = next(
            (rt for rt in self.refresh_tokens if rt["number"] == self.active_user["number"]),
            None,
        )
        if rt_entry:
            rt_entry["refresh_token"] = tokens.get("refresh_token", rt_entry["refresh_token"])
            self.write_tokens_to_file()
        return True

    def get_active_user(self):
        if not self.active_user:
            if self.refresh_tokens:
                self.set_active_user(self.refresh_tokens[0]["number"])
            return self.active_user

        if self.last_refresh_time is None or (int(time.time()) - self.last_refresh_time) > 300:
            self.renew_active_user_token()
        return self.active_user

    def get_active_tokens(self) -> dict | None:
        au = self.get_active_user()
        return au["tokens"] if au else None

    def write_tokens_to_file(self):
        with open("refresh-tokens.json", "w", encoding="utf-8") as f:
            json.dump(self.refresh_tokens, f, indent=4)

    def write_active_number(self):
        if self.active_user:
            with open("active.number", "w", encoding="utf-8") as f:
                f.write(str(self.active_user["number"]))
        else:
            if os.path.exists("active.number"):
                os.remove("active.number")

    def load_active_number(self):
        if os.path.exists("active.number"):
            with open("active.number", "r", encoding="utf-8") as f:
                ns = f.read().strip()
                if ns.isdigit():
                    self.set_active_user(int(ns))


AuthInstance = Auth()