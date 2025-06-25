import subprocess
import pytest

from helpers.tools import __main__ as tools_main


def test_main_unknown_tool():
  with pytest.raises(SystemExit) as excinfo:
    tools_main.main(["nope"])

  assert excinfo.value.code == 2


def test_main_error(monkeypatch):
  def fail(args):
    raise subprocess.CalledProcessError(2, ["cmd"])

  def register(subparsers):
    p = subparsers.add_parser("fake")
    p.set_defaults(func=fail)

  monkeypatch.setattr(tools_main, "load_tools", lambda: None)
  tools_main.TOOL_REGISTRY["fake"] = register
  code = tools_main.main(["fake"])
  assert code == 2
  del tools_main.TOOL_REGISTRY["fake"]


def test_main_unexpected(monkeypatch):
  def fail(args):
    raise RuntimeError("boom")

  def register(subparsers):
    p = subparsers.add_parser("boom")
    p.set_defaults(func=fail)

  monkeypatch.setattr(tools_main, "load_tools", lambda: None)
  tools_main.TOOL_REGISTRY["boom"] = register
  code = tools_main.main(["boom"])
  assert code == 1
  del tools_main.TOOL_REGISTRY["boom"]
