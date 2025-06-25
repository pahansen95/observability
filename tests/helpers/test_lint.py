import argparse

import helpers.tools.lint as lint


def test_run_default_fix(monkeypatch):
  calls = []

  def fake(cmd):
    calls.append(cmd)

  monkeypatch.setattr(lint, "run_command", fake)
  args = argparse.Namespace(paths=[], dry_run=False)
  lint.run(args)
  assert calls == [["ruff", "check", "--fix"]]


def test_run_dry_run(monkeypatch):
  calls = []

  def fake(cmd):
    calls.append(cmd)

  monkeypatch.setattr(lint, "run_command", fake)
  args = argparse.Namespace(paths=["a.py"], dry_run=True)
  lint.run(args)
  assert calls == [["ruff", "check", "a.py"]]
