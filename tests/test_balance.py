"""Exercise the real HTTP/cookie flow without calling DESCO."""

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError

from examples.balance import DescoClient


class Portal(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, status, body, cookie=None):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_GET(self):
        if self.path == "/api/auth/csrf":
            self.respond(200, {}, "XSRF-TOKEN=test%2Btoken; Path=/")
        elif "session=authenticated" not in self.headers.get("Cookie", ""):
            self.respond(401, {"errorCode": "AUTHENTICATION_REQUIRED"})
        elif self.path == "/api/accounts":
            self.respond(200, {"accounts": [{"accountId": 123, "accountNo": "87654321"}]})
        elif self.path == "/api/accounts/123/balance":
            self.respond(200, {"accountNo": "87654321", "balance": 500.25, "stale": False})
        else:
            self.respond(404, {})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        valid = (
            self.path == "/api/auth/login"
            and self.headers.get("X-XSRF-TOKEN") == "test+token"
            and "XSRF-TOKEN=test%2Btoken" in self.headers.get("Cookie", "")
            and self.headers.get("Content-Type") == "application/json"
            and body == {"username": "test-user", "password": "test-password"}
        )
        if valid:
            self.respond(200, {}, "session=authenticated; HttpOnly; Path=/")
        else:
            self.respond(401, {})


class BalanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Portal)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/api"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_login_cookies_csrf_and_balance(self):
        client = DescoClient(self.base_url)
        client.login("test-user", "test-password")
        account = client.accounts()[0]
        result = client.balance(account["accountId"])
        self.assertEqual(result["balance"], 500.25)
        self.assertEqual(result["accountNo"], account["accountNo"])
        self.assertFalse(result["stale"])

    def test_missing_session_is_not_treated_as_balance(self):
        with self.assertRaises(HTTPError) as caught:
            DescoClient(self.base_url).balance(123)
        self.assertEqual(caught.exception.code, 401)
        caught.exception.close()

    def test_invalid_login_does_not_establish_session(self):
        client = DescoClient(self.base_url)
        with self.assertRaises(HTTPError) as caught:
            client.login("test-user", "wrong-password")
        self.assertEqual(caught.exception.code, 401)
        caught.exception.close()
        with self.assertRaises(HTTPError) as expired:
            client.accounts()
        expired.exception.close()


if __name__ == "__main__":
    unittest.main()
