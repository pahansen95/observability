import argparse
import contextlib
import http.server
import io
import json
import os
import threading

from helpers.tools import chat as chat_tool


class Handler(http.server.BaseHTTPRequestHandler):
  def do_POST(self) -> None:
    length = int(self.headers.get("Content-Length", "0"))
    body = self.rfile.read(length)
    self.server.received_path = self.path
    self.server.received = json.loads(body.decode())
    self.send_response(200)
    self.end_headers()
    payload = {"choices": [{"message": {"role": "assistant", "content": "pong"}}]}
    self.wfile.write(json.dumps(payload).encode())

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


def test_chat_cli_text_to_log(monkeypatch, tmp_path):
  with run_server() as srv:
    port = srv.server_address[1]
    conf = tmp_path / "conf.json"
    conf.write_text(
      json.dumps({"provider": "OpenAI", "base_url": f"http://localhost:{port}", "model": "gpt", "api_key": "$API_KEY"})
    )
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("be helpful")
    os.environ["API_KEY"] = "tok"
    args = argparse.Namespace(fmt="txt:log", prompt=str(prompt), conf=str(conf))
    stdin = io.StringIO("ping")
    stdout = io.StringIO()
    chat_tool.run(args, in_stream=stdin, out_stream=stdout)
    lines = stdout.getvalue().strip().splitlines()
    assert json.loads(lines[0])["role"] == "system"
    assert json.loads(lines[-1])["role"] == "assistant"
    assert srv.received["messages"][1]["content"] == "ping"
