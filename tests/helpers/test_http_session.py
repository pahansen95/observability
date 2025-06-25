import contextlib
import http.server
import json
import threading

from helpers.utils import HttpSession, HttpResponse


class Handler(http.server.BaseHTTPRequestHandler):
  PAGES = {
    "/p1": {"next": "/p2", "data": 1},
    "/p2": {"next": "/p3", "data": 2},
    "/p3": {"next": None, "data": 3},
  }

  def do_GET(self) -> None:
    if self.path == "/ping":
      self.send_response(200)
      self.end_headers()
      self.wfile.write(b"pong")
    elif self.path in self.PAGES:
      self.send_response(200)
      self.end_headers()
      payload = json.dumps(self.PAGES[self.path]).encode()
      self.wfile.write(payload)
    else:
      self.send_response(404)
      self.end_headers()

  def log_message(self, format: str, *args) -> None:  # noqa: D401
    pass


@contextlib.contextmanager
def run_server():
  server = http.server.ThreadingHTTPServer(("localhost", 0), Handler)
  thread = threading.Thread(target=server.serve_forever)
  thread.daemon = True
  thread.start()
  try:
    yield server
  finally:
    server.shutdown()
    thread.join()


def test_http_session_get():
  with run_server() as srv:
    port = srv.server_address[1]
    with HttpSession(f"http://localhost:{port}") as sess:
      with sess.get("/ping") as resp:
        data = resp.read()
        status = resp.status
    assert status == 200
    assert data == b"pong"


def test_http_session_stream():
  with run_server() as srv:
    port = srv.server_address[1]
    with HttpSession(f"http://localhost:{port}") as sess:
      with sess.request("GET", "/ping") as resp:
        chunks = list(resp.stream(2))
        status = resp.status
    assert b"".join(chunks) == b"pong"
    assert status == 200


def extract_next(resp: HttpResponse) -> str | None:
  return json.loads(resp.read().decode())["next"]


def test_http_session_paginate():
  with run_server() as srv:
    port = srv.server_address[1]
    with HttpSession(f"http://localhost:{port}") as sess:
      pages = list(sess.paginate("/p1", extract_next))
    assert [json.loads(p.read())["data"] for p in pages] == [1, 2, 3]


def test_http_session_paginate_no_cache():
  with run_server() as srv:
    port = srv.server_address[1]
    with HttpSession(f"http://localhost:{port}") as sess:
      pages = list(sess.paginate("/p1", extract_next, cache_body=False))
    assert [json.loads(p.read())["data"] for p in pages] == [1, 2, 3]
