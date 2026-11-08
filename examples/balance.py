"""Fetch daily DESCO balances using an in-memory cookie session (Python 3.9+)."""

import getpass
import json
import sys
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import unquote
from urllib.request import HTTPCookieProcessor, Request, build_opener

BASE_URL = "https://prepaid.desco.org.bd/api"


class DescoClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.cookies = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookies))

    def request(self, path, body=None):
        headers = {"Accept": "application/json"}
        payload = None
        if body is not None:
            token = next(
                (cookie.value for cookie in self.cookies
                 if cookie.name == "XSRF-TOKEN"),
                None,
            )
            if not token:
                raise RuntimeError("Missing DESCO CSRF cookie; sign in first")
            headers["X-XSRF-TOKEN"] = unquote(token)
            headers["Content-Type"] = "application/json"
            payload = json.dumps(body).encode("utf-8")
        request = Request(self.base_url + path, data=payload, headers=headers)
        with self.opener.open(request, timeout=30) as response:
            data = response.read()
            return json.loads(data) if data else None

    def login(self, username, password):
        self.request("/auth/csrf")
        self.request("/auth/login", {"username": username, "password": password})

    def accounts(self):
        return self.request("/accounts")["accounts"]

    def balance(self, account_id):
        return self.request(f"/accounts/{account_id}/balance")


def main():
    try:
        client = DescoClient()
        username = input("DESCO username: ").strip()
        password = getpass.getpass("DESCO password: ")
        if not username or not password:
            raise RuntimeError("Username and password are required")
        client.login(username, password)
        del password
        accounts = client.accounts()
        if not accounts:
            print("No linked accounts. Link your electricity account in the DESCO portal.")
            return 0
        for index, account in enumerate(accounts, start=1):
            result = client.balance(account["accountId"])
            print(json.dumps({
                "linkedAccount": index,
                "balance": result.get("balance"),
                "currency": result.get("currency"),
                "balanceSnapshotAt": result.get("balanceSnapshotAt"),
                "timestampAvailable": result.get("timestampAvailable"),
                "stale": result.get("stale"),
            }, ensure_ascii=False))
        return 0
    except HTTPError as error:
        if error.code == 401:
            print("DESCO HTTP 401: login failed or session expired. Sign in again.", file=sys.stderr)
        else:
            print(f"DESCO HTTP {error.code}: request failed.", file=sys.stderr)
        error.close()
    except (URLError, TimeoutError):
        print("Could not reach DESCO. Check your connection and try again.", file=sys.stderr)
    except (RuntimeError, ValueError, KeyError, TypeError):
        print("DESCO request failed: missing credentials, CSRF cookie, or unexpected response format.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
