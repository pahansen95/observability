"""Utility functions for helpers."""

from __future__ import annotations

import argparse
import contextlib
import http.client
import logging
import os
import shlex
import subprocess
import sys
import urllib.parse
from pathlib import Path
from typing import Callable, Generator, Sequence

logger = logging.getLogger(__name__)


def configure_logging(verbosity: int = 0, log_file: str | None = None) -> None:
  """Configure basic logging for helper scripts."""
  level = logging.WARNING - (10 * verbosity)
  if level < logging.DEBUG:
    level = logging.DEBUG

  handlers: list[logging.Handler] = [logging.StreamHandler()]
  if log_file:
    handlers.append(logging.FileHandler(log_file))

  logging.basicConfig(
    level=level,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=handlers,
    force=True,
  )


def run_command(cmd: str | Sequence[str], *, check: bool = True, **kwargs) -> subprocess.CompletedProcess:
  """Run a command and log it."""
  if isinstance(cmd, str):
    args = shlex.split(cmd)
  else:
    args = list(cmd)

  log_args = args.copy()
  if log_args and log_args[0] == sys.executable:
    log_args[0] = "python"

  logger.info("$ %s", " ".join(shlex.quote(a) for a in log_args))
  return subprocess.run(args, check=check, **kwargs)


def check_command_exists(cmd: str) -> bool:
  """Return ``True`` if *cmd* exists in ``PATH``."""
  result = run_command(["which", cmd], check=False, capture_output=True, text=True)
  return result.returncode == 0


def add_common_args(parser: argparse.ArgumentParser) -> None:
  """Add common arguments to *parser* (logging + working directory)."""
  parser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="Increase log verbosity (can be repeated)",
  )
  parser.add_argument("--log-file", help="Write logs to this file as well")
  parser.add_argument(
    "-C",
    "--directory",
    type=Path,
    help="Change to this directory before running",
  )


def add_logging_args(parser: argparse.ArgumentParser) -> None:
  """Add common logging arguments to *parser*.

  Deprecated: Use add_common_args() instead.
  """
  parser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="Increase log verbosity (can be repeated)",
  )
  parser.add_argument("--log-file", help="Write logs to this file as well")


@contextlib.contextmanager
def working_directory(path: Path | None) -> Generator[None, None, None]:
  """Context manager to temporarily change working directory."""
  if path is None:
    yield
    return

  original = Path.cwd()
  try:
    os.chdir(path)
    logger.debug("Changed to directory: %s", path)
    yield
  finally:
    os.chdir(original)


def find_project_root(start: Path | None = None) -> Path:
  """Find project root by looking for pyproject.toml."""
  current = Path.cwd() if start is None else start

  while current != current.parent:
    if (current / "pyproject.toml").exists():
      return current
    current = current.parent

  # If no pyproject.toml found, return original directory
  return Path.cwd() if start is None else start


def setup_working_directory(args: argparse.Namespace) -> contextlib.AbstractContextManager:
  """Setup working directory based on command arguments.

  If args.directory is specified, change to that directory.
  Otherwise, change to project root (directory containing pyproject.toml).
  """
  if hasattr(args, "directory") and args.directory:
    return working_directory(args.directory)
  else:
    # Default to project root
    project_root = find_project_root()
    if project_root != Path.cwd():
      logger.debug("Changing to project root: %s", project_root)
      return working_directory(project_root)
    else:
      # Already at project root, no-op context manager
      return contextlib.nullcontext()


class HttpResponse(contextlib.AbstractContextManager):
  """Wrapper around :class:`http.client.HTTPResponse`."""

  def __init__(self, raw: http.client.HTTPResponse) -> None:
    self._raw = raw
    self._buffer: bytes | None = None
    self.status = raw.status
    self.headers = dict(raw.getheaders())

  def __enter__(self) -> "HttpResponse":
    return self

  def __exit__(self, exc_type, exc, tb) -> None:
    self._raw.close()

  def read(self) -> bytes:
    """Return the entire response body."""
    if self._buffer is None:
      self._buffer = self._raw.read()
    return self._buffer

  def stream(self, chunk_size: int = 8192) -> Generator[bytes, None, None]:
    """Yield response body data in ``chunk_size`` increments."""
    if self._buffer is not None:
      for i in range(0, len(self._buffer), chunk_size):
        yield self._buffer[i : i + chunk_size]
    else:
      while True:
        chunk = self._raw.read(chunk_size)
        if not chunk:
          break
        yield chunk


class HttpSession(contextlib.AbstractContextManager):
  """Minimal HTTP client using :mod:`http.client`."""

  def __init__(self, base_url: str, *, timeout: float | None = None) -> None:
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme not in {"http", "https"}:
      raise ValueError(f"Unsupported scheme: {parsed.scheme!r}")

    self.scheme = parsed.scheme
    self.host = parsed.hostname or ""
    self.port = parsed.port
    self.base_path = parsed.path.rstrip("/")
    self.timeout = timeout
    self._conn: http.client.HTTPConnection | None = None

  def __enter__(self) -> "HttpSession":
    conn_cls = http.client.HTTPSConnection if self.scheme == "https" else http.client.HTTPConnection
    self._conn = conn_cls(self.host, self.port, timeout=self.timeout)
    return self

  def __exit__(self, exc_type, exc, tb) -> None:
    if self._conn is not None:
      self._conn.close()

  def _make_path(self, path: str) -> str:
    if not path.startswith("/"):
      path = f"/{path}"
    return f"{self.base_path}{path}" if self.base_path else path

  @contextlib.contextmanager
  def request(
    self,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    body: str | bytes | None = None,
  ) -> Generator["HttpResponse", None, None]:
    if self._conn is None:
      raise RuntimeError("Session not active")

    target = self._make_path(path)
    data = body.encode() if isinstance(body, str) else body
    self._conn.request(method, target, body=data, headers=headers or {})
    raw = self._conn.getresponse()
    resp = HttpResponse(raw)
    try:
      yield resp
    finally:
      raw.close()

  @contextlib.contextmanager
  def get(self, path: str, *, headers: dict[str, str] | None = None) -> Generator["HttpResponse", None, None]:
    with self.request("GET", path, headers=headers) as resp:
      yield resp

  @contextlib.contextmanager
  def post(
    self,
    path: str,
    body: str | bytes | None = None,
    *,
    headers: dict[str, str] | None = None,
  ) -> Generator["HttpResponse", None, None]:
    with self.request("POST", path, headers=headers, body=body) as resp:
      yield resp

  def paginate(
    self,
    path: str,
    next_page: Callable[["HttpResponse"], str | None],
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | bytes | None = None,
    cache_body: bool = True,
  ) -> Generator["HttpResponse", None, None]:
    """Iterate over paginated responses.

    ``next_page`` should return the path for the next request or ``None``.
    If ``cache_body`` is ``True`` the response body is read before ``next_page``
    is invoked.
    """
    while True:
      with self.request(method, path, headers=headers, body=body) as resp:
        if cache_body:
          resp.read()
        next_path = next_page(resp)
        yield resp
      if next_path is None:
        break
      path = next_path
