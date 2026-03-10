import socketserver
import http.server
import http.cookies
from urllib.parse import urlparse,parse_qs
import shelve
import sys
import uuid

def validate_args(args: list[str]):
    if len(args) != 2:
        print("usage: server-web-app.py <port>")
        exit(1)
    try:
        int(args[1])
    except ValueError:
        print("error: port must be a number")
        exit(1)
class webHandler(http.server.BaseHTTPRequestHandler):

    def home(self, username):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = f"""
                                                            <!DOCTYPE html>
                                                            <html>
                                                            <head>
                                                                <title>Pagina web</title>
                                                            </head>
                                                            <body>
                                                                <p>Welcome Home {username}!</p>
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
                                                        <title>Pagina web</title>
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



        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = """<!DOCTYPE html>"""
        self.wfile.write(html.encode("utf-8"))

    def verify_credentials(self, username, password):
        with shelve.open("credentials") as creds:
            if username in creds and password in creds[username]:
                return True
            else:
                return False

    def add_credentials(self,username,password):
        with shelve.open("credentials") as creds:
            if username not in creds:
                creds[username] = password
                return True
            else:
                return False
    def give_cookiesession(self, username):
        with shelve.open("cookies") as cookies:
            session_id = str(uuid.uuid4())
            cookies[session_id] = username
        return session_id

    def do_POST(self):
        urlparsed = urlparse(self.path)
        if urlparsed.path == "/login":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            form = parse_qs(post_data)
            username = form.get('username', None)[0]
            password = form.get('password', None)[0]
            action = form.get('action', None)[0]
            if action == "login":
                if self.verify_credentials(username, password):
                    print("INFO: user logged in, redirecting to home page...")
                    session_id = self.give_cookiesession(username)
                    cookie = http.cookies.SimpleCookie()
                    cookie["session_id"] = session_id

                    self.send_response(301)
                    self.send_header("Set-Cookie", cookie.output(header='', sep=''))
                    self.send_header("Location", "/home")
                    self.home(username)
                else:
                    print("WARNING: user not logged in, redirecting again to login page...")
                    self.login("Credentials are incorrect, please try again")
            elif action == "signup":
                if self.add_credentials(username, password):
                    print("INFO: user sign up, redirecting to login page...")
                    self.login("Log in or Sign up")
                else:
                    print("WARINING: user exists, redirecting to login page...")
                    self.login("User exists, pleas try with other username")

        self.send_response(404)




if __name__ == "__main__":
    args = sys.argv
    validate_args(args)
    port: int = int(args[1])
    with socketserver.ThreadingTCPServer(("", port), webHandler) as webserver:
        print(f"Server running at http://localhost:{port}")
        print("CTRL + C to exit")
        webserver.serve_forever()