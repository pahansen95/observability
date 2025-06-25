from helpers.bootstrap.verify import verify_tool, verify_venv
import importlib
import subprocess
from pathlib import Path

import helpers.tools.python as pytools

dx = importlib.import_module("helpers.bootstrap.40_dx")
verify_pre_commit_hooks = dx.verify_pre_commit_hooks
install_pre_commit_hooks = dx.install_pre_commit_hooks


def test_verify_tool_python():
  res = verify_tool("python")
  assert res["installed"]
  assert res["version"] is not None


def test_verify_tool_missing():
  res = verify_tool("unlikely_tool")
  assert not res["installed"]


def test_verify_venv(tmp_path):
  venv_path = tmp_path / "env"
  import venv

  venv.EnvBuilder(with_pip=True).create(venv_path)

  res = verify_venv(venv_path)
  assert res["valid"]
  assert not res["corrupt"]


def test_verify_venv_corrupt(tmp_path):
  venv_path = tmp_path / "env"
  venv_path.mkdir()
  (venv_path / "pyvenv.cfg").write_text("# fake")
  res = verify_venv(venv_path)
  assert not res["valid"]
  assert res["corrupt"]


def test_verify_pre_commit_hooks(tmp_path):
  hooks = tmp_path / ".git" / "hooks"
  hooks.mkdir(parents=True)
  (hooks / "pre-commit").write_text("echo")
  res = verify_pre_commit_hooks(tmp_path)
  assert res["pre_commit"]["installed"]


def test_install_pre_commit_hooks_invokes_precommit(monkeypatch, tmp_path):
  calls: list[list[str]] = []

  def fake_run(cmd, *args, **kwargs):
    calls.append(cmd)
    return subprocess.CompletedProcess(cmd, 0)

  monkeypatch.setattr(dx, "run_command", fake_run)
  monkeypatch.setattr(pytools, "resolve_venv_path", lambda name: Path("env"))

  precommit = tmp_path / "env" / "bin" / "pre-commit"
  precommit.parent.mkdir(parents=True)
  precommit.write_text("echo")

  res = install_pre_commit_hooks(tmp_path)

  assert calls[0] == [str(precommit), "install"]
  assert res["pre_commit"]["installed"]


def test_install_pre_commit_hooks_missing(monkeypatch, tmp_path):
  monkeypatch.setattr(pytools, "resolve_venv_path", lambda name: Path("env"))
  res = install_pre_commit_hooks(tmp_path)
  assert not res["pre_commit"]["installed"]
  assert res["pre_commit"]["error"] == "pre-commit not found"
