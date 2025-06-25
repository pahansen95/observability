import contextlib
import http.server
import json
import threading

from helpers.tools.chat import (
  AzureChatClient,
  ChatClient,
  ChatMessage,
  TextPart,
  ImagePart,
  Role,
  AnthropicChatClient,
  BedrockChatClient,
  create_client,
)


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


def test_chat_client_text():
  with run_server() as srv:
    port = srv.server_address[1]
    client = ChatClient(f"http://localhost:{port}", "tok", "gpt")
    reply = client.chat([ChatMessage(Role.USER, [TextPart("ping")])])
    assert reply == "pong"
    assert srv.received["messages"][0]["content"] == "ping"


def test_chat_client_image():
  with run_server() as srv:
    port = srv.server_address[1]
    client = ChatClient(f"http://localhost:{port}", "tok", "gpt")
    msg = ChatMessage(
      Role.USER,
      [TextPart("look"), ImagePart("http://img.test/image.png", detail="low")],
    )
    client.chat([msg])
    received = srv.received["messages"][0]["content"]
    assert received[1]["type"] == "image_url"
    assert received[1]["image_url"]["url"] == "http://img.test/image.png"


def test_azure_chat_client():
  with run_server() as srv:
    port = srv.server_address[1]
    client = AzureChatClient(
      f"http://localhost:{port}",
      "tok",
      "dep",
      api_version="2025-03-01",
    )
    client.chat([ChatMessage(Role.USER, [TextPart("ping")])])
    assert srv.received_path.startswith("/openai/deployments/dep/chat/completions")
    assert "api-version=2025-03-01" in srv.received_path
    assert "model" not in srv.received


def test_anthropic_chat_client():
  with run_server() as srv:
    port = srv.server_address[1]
    client = AnthropicChatClient(
      f"http://localhost:{port}",
      "tok",
      "claude",
      api_version="2023-06-01",
    )
    client.chat([ChatMessage(Role.USER, [TextPart("ping")])])
    assert srv.received_path == "/v1/messages"
    assert srv.received["model"] == "claude"
    assert srv.received["messages"][0]["content"] == "ping"


def test_bedrock_chat_client():
  with run_server() as srv:
    port = srv.server_address[1]
    client = BedrockChatClient(f"http://localhost:{port}", "tok", "mistral")
    client.chat([ChatMessage(Role.USER, [TextPart("ping")])])
    assert srv.received_path == "/model/mistral/invoke"


def test_create_client_providers():
  base = "http://localhost"
  cfg = {"base_url": base, "api_key": "tok", "model": "gpt", "deployment": "dep"}

  client = create_client({**cfg, "provider": "OpenAI"})
  assert isinstance(client, ChatClient) and not isinstance(
    client, (AzureChatClient, AnthropicChatClient, BedrockChatClient)
  )

  client = create_client({**cfg, "provider": "OpenAI:Azure"})
  assert isinstance(client, AzureChatClient)

  client = create_client({**cfg, "provider": "Anthropic"})
  assert isinstance(client, AnthropicChatClient)

  client = create_client({**cfg, "provider": "Anthropic:Bedrock"})
  assert isinstance(client, BedrockChatClient)
