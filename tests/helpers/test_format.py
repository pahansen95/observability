import argparse

import helpers.tools.format as fmt


def test_run_default(monkeypatch):
    calls = []

    def fake(cmd):
        calls.append(cmd)

    monkeypatch.setattr(fmt, "run_command", fake)
    args = argparse.Namespace(paths=[], check=False)
    fmt.run(args)
    assert calls == [["ruff", "format"]]


def test_run_check(monkeypatch):
    calls = []

    def fake(cmd):
        calls.append(cmd)

    monkeypatch.setattr(fmt, "run_command", fake)
    args = argparse.Namespace(paths=["a.py"], check=True)
    fmt.run(args)
    assert calls == [["ruff", "format", "--check", "a.py"]]
