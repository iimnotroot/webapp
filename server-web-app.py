import os
import socketserver
import http.server
import http.cookies
from urllib.parse import urlparse,parse_qs
import shelve
import sys
import uuid
import hashlib

def validate_args(args: list[str]):
    if len(args) != 2:
        print("usage: server-web-app.py <port>")
        exit(1)
    try:
        int(args[1])
    except ValueError:
        print("error: port must be a number")
        exit(1)

def hash_password(password: str):
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt + hashed
def verify_password(stored_password, provided_password):
    salt = stored_password[:16]
    stored_hash = stored_password[16:]
    new_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
    return new_hash == stored_hash


def verify_credentials(username, password):
    with shelve.open("credentials") as creds:
        if username in creds:
            if verify_password(creds[username], password):
                return "Log in complete"
            else:
                return "Log in failed"
        else:
            return "Log in failed"


def add_credentials(username,password):
    with shelve.open("credentials") as creds:
        if username not in creds:
            pass_hashed = hash_password(password)
            creds[username] = pass_hashed
            return "Sign up complete"
        else:
            return "Sign up failed"
def give_cookiesession(username):
    with shelve.open("cookies") as cookies:
        session_id = str(uuid.uuid4())
        cookies[session_id] = username
    return session_id

class webHandler(http.server.BaseHTTPRequestHandler):

    def home(self, username):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = f"""
                                                            <!DOCTYPE html>
                                                            <html>
                                                            <head>
                                                                <title>Web Page</title>
                                                            </head>
                                                            <body>
                                                                <p>Welcome Home {username}!</p>
                                                                <form action="/home" method="post">
                                                                <button type="submit" value="logout" name="action">Log out</button>
                                                                </form>
                                                            </body>
                                                            </html>
                                                            """
        self.wfile.write(html.encode("utf-8"))

    def login(self, msg: str):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html_login = f"""
                                                    <!DOCTYPE html>
                                                    <html>
                                                    <head>
                                                        <title>Web Page</title>
                                                    </head>
                                                    <body>
                                                        <p>Login|Sign up:</p>
                                                       <form action="/login" method="post" accept-charset="UTF-8">
                                                        <label for="username">username:</label>
                                                          <input type="text" id="username" name="username">
                                                          <br><br>
                                                          <label for="password">password:</label>
                                                          <input type="password" id="password" name="password">
                                                          <br><br>
                                                          <button type="submit" value="login" name="action">Log in</button>
                                                          <button type="submit" value="signup" name="action">Sign up</button>
                                                        </form>
                                                        <p class="message">{msg}</p>
                                                    </body>
                                                    </html>
                                                    """
        self.wfile.write(html_login.encode("utf-8"))
    def getSessionId(self):
        cookies_header = self.headers.get('Cookie')
        if cookies_header:
            cookie = http.cookies.SimpleCookie()
            cookie.load(cookies_header)
            if "session_id" in cookie:
                session_id = cookie["session_id"].value
                with shelve.open("cookies") as cookies:
                    if session_id in cookies:
                        return session_id, cookies[session_id]
                    else:
                        return None, None
            else:
                return None, None
        else:
            return None, None


    def do_GET(self):
        urlparsed = urlparse(self.path)

        if urlparsed.path == "/":
            [session_id, username] = self.getSessionId()
            if session_id is None:
                print("INFO: user not logged in, redirecting to login page...")
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            else:
                self.home(username)
        if urlparsed.path == "/login":
            self.login("Log in or Sign up")
            return
        if urlparsed.path == "/home":
            [session_id, username] = self.getSessionId()
            if session_id is not None:
                self.home(username)
            else:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()


    def do_POST(self):
        urlparsed = urlparse(self.path)
        if urlparsed.path == "/login":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            form = parse_qs(post_data)
            username = form.get('username', None)[0]
            password = form.get('password', None)[0]
            if len(username) > 25 or len(password) > 50:
                self.login("Input to long")
                print("INFO: input is too long")
                return
            action = form.get('action', None)[0]
            if action == "login":
                status: str = verify_credentials(username, password)
                if status == "Log in complete":
                    print(f"INFO: user {username} logged in, redirecting to home page...")
                    session_id = give_cookiesession(username)
                    cookie = http.cookies.SimpleCookie()
                    cookie["session_id"] = session_id
                    cookie["session_id"]["httponly"] = True
                    cookie["session_id"]["secure"] = False
                    cookie["session_id"]["samesite"] = "Strict"
                    cookie["session_id"]["max-age"] = 3600

                    self.send_response(302)
                    self.send_header("Set-Cookie", cookie.output(header='', sep=''))
                    self.send_header("Location", "/home")
                    self.end_headers()
                else:
                    print("WARNING: user not logged in, redirecting again to login page...")
                    self.login("Credentials are incorrect, please try again")
            elif action == "signup":
                status: str = add_credentials(username, password)
                if status == "Sign up complete":
                    print(f"INFO: user {username} sign up, redirecting to login page...")
                    self.login("Log in or Sign up")
                else:
                    print("WARINING: user exists, redirecting to login page...")
                    self.login("User exists, pleas try with other username")
        elif urlparsed.path == "/home":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            form = parse_qs(post_data)
            action = form.get('action', None)[0]
            if action == "logout":
                session_id, username = self.getSessionId()

                if session_id:
                    with shelve.open("cookies") as cookies:
                        if session_id in cookies:
                            del cookies[session_id]

                cookie = http.cookies.SimpleCookie()
                cookie["session_id"] = ""
                cookie["session_id"]["max-age"] = 0

                self.send_response(302)
                self.send_header("Set-Cookie", cookie.output(header='', sep=''))
                self.send_header("Location", "/login")
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()




if __name__ == "__main__":
    args = sys.argv
    validate_args(args)
    port: int = int(args[1])
    with socketserver.ThreadingTCPServer(("", port), webHandler) as webserver:
        print(f"Server running at http://localhost:{port}")
        print("CTRL + C to exit")
        webserver.serve_forever()