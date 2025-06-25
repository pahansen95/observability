# helpers/bootstrap/platform.py - Updated for Homebrew preference

from __future__ import annotations

import logging
import os
import platform as _platform
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict

from helpers.bootstrap.verify import verify_tool
from helpers.utils import run_command, check_command_exists

logger = logging.getLogger(__name__)


class Platform:
    """Base platform handler."""

    name = "generic"

    def install_uv(self) -> Dict[str, Any]:
        raise NotImplementedError

    def install_pyenv(self) -> Dict[str, Any]:
        raise NotImplementedError

    def check_prerequisites(self) -> Dict[str, bool]:
        raise NotImplementedError


class PosixPlatform(Platform):
    """Common logic for POSIX systems."""

    def install_uv_via_installer(self) -> Dict[str, Any]:
        """Fallback to official installer script."""
        result = {"uv": {"installed": False, "version": None, "error": None}}
        try:
            logger.info("Installing uv via official installer...")
            installer_url = "https://astral.sh/uv/install.sh"
            with urllib.request.urlopen(installer_url) as response:
                installer_script = response.read().decode("utf-8")

            process = subprocess.Popen(
                ["sh", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = process.communicate(installer_script)
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "uv installer", stderr)

            # After installation, update PATH for current session
            common_paths = [
                Path.home() / ".local" / "bin",
                Path.home() / ".cargo" / "bin",
            ]
            
            for path in common_paths:
                if (path / "uv").exists():
                    logger.info("Found uv at %s, updating PATH", path)
                    current_path = os.environ.get("PATH", "")
                    if str(path) not in current_path:
                        os.environ["PATH"] = f"{path}:{current_path}"
                    break

            verification = verify_tool("uv")
            if verification["installed"]:
                result["uv"]["installed"] = True
                result["uv"]["version"] = verification["version"]
                logger.info("uv installed successfully: %s", verification["version"])
            else:
                result["uv"]["error"] = "uv not found after installation"
                logger.error("uv installation verification failed")
        except Exception as e:
            result["uv"]["error"] = str(e)
            logger.error("Failed to install uv: %s", e)
        return result

    def install_uv(self) -> Dict[str, Any]:
        """Install uv, preferring Homebrew where available."""
        result = {"uv": {"installed": False, "version": None, "error": None}}
        
        # Check if already installed
        existing = verify_tool("uv")
        if existing["installed"]:
            result["uv"]["installed"] = True
            result["uv"]["version"] = existing["version"]
            logger.info("uv already installed: %s", existing["version"])
            return result
        
        # Prefer Homebrew on systems where it's available
        if check_command_exists("brew"):
            logger.info("Homebrew found, attempting to install uv via brew...")
            try:
                run_command(["brew", "install", "uv"], check=True)
                verification = verify_tool("uv")
                if verification["installed"]:
                    result["uv"]["installed"] = True
                    result["uv"]["version"] = verification["version"]
                    logger.info("uv installed via Homebrew: %s", verification["version"])
                    return result
            except subprocess.CalledProcessError as e:
                logger.warning("Homebrew installation failed: %s", e)
                logger.info("Falling back to official installer...")
        
        # Fall back to official installer
        return self.install_uv_via_installer()

    def check_prerequisites(self) -> Dict[str, bool]:
        checks = {
            "git_available": check_command_exists("git"),
            "python_version_ok": sys.version_info >= (3, 7),
            "venv_available": run_command([sys.executable, "-m", "venv", "--help"], check=False).returncode == 0,
            "download_tool_available": check_command_exists("curl") or check_command_exists("wget"),
        }
        return checks


class LinuxPlatform(PosixPlatform):
    name = "linux"

    def install_pyenv(self) -> Dict[str, Any]:
        result = {"pyenv": {"installed": False, "version": None, "error": None}}
        existing = verify_tool("pyenv")
        if existing["installed"]:
            result["pyenv"]["installed"] = True
            result["pyenv"]["version"] = existing["version"]
            logger.info("pyenv already installed: %s", existing["version"])
            return result
        
        # Check for Homebrew on Linux (Linuxbrew)
        if check_command_exists("brew"):
            try:
                logger.info("Installing pyenv via Homebrew...")
                run_command(["brew", "install", "pyenv"], check=True)
                verification = verify_tool("pyenv")
                if verification["installed"]:
                    result["pyenv"]["installed"] = True
                    result["pyenv"]["version"] = verification["version"]
                    logger.info("pyenv installed via Homebrew: %s", verification["version"])
                    return result
            except subprocess.CalledProcessError:
                logger.warning("Homebrew installation failed, falling back to git...")
        
        # Fall back to git installation
        try:
            logger.info("Installing pyenv via git...")
            pyenv_root = Path.home() / ".pyenv"
            if not pyenv_root.exists():
                run_command(["git", "clone", "https://github.com/pyenv/pyenv.git", str(pyenv_root)])
            
            # Update shell configuration
            shell_config = Path.home() / ".bashrc"
            if (Path.home() / ".zshrc").exists():
                shell_config = Path.home() / ".zshrc"
            
            pyenv_init = (
                '\n# pyenv\n'
                'export PYENV_ROOT="$HOME/.pyenv"\n'
                'export PATH="$PYENV_ROOT/bin:$PATH"\n'
                'eval "$(pyenv init -)"\n'
            )
            
            if shell_config.exists():
                content = shell_config.read_text()
                if "PYENV_ROOT" not in content:
                    shell_config.write_text(content + pyenv_init)
                    logger.info("Added pyenv to shell configuration")
            
            result["pyenv"]["installed"] = True
            result["pyenv"]["version"] = "git installation"
        except Exception as e:
            result["pyenv"]["error"] = str(e)
            logger.error("Failed to install pyenv: %s", e)
        
        return result


class MacOSPlatform(PosixPlatform):
    name = "macos"

    def install_pyenv(self) -> Dict[str, Any]:
        result = {"pyenv": {"installed": False, "version": None, "error": None}}
        existing = verify_tool("pyenv")
        if existing["installed"]:
            result["pyenv"]["installed"] = True
            result["pyenv"]["version"] = existing["version"]
            logger.info("pyenv already installed: %s", existing["version"])
            return result
        
        if check_command_exists("brew"):
            try:
                logger.info("Installing pyenv via Homebrew...")
                run_command(["brew", "install", "pyenv"], check=True)
                verification = verify_tool("pyenv")
                if verification["installed"]:
                    result["pyenv"]["installed"] = True
                    result["pyenv"]["version"] = verification["version"]
                    logger.info("pyenv installed via Homebrew: %s", verification["version"])
                else:
                    result["pyenv"]["error"] = "pyenv not found after Homebrew installation"
            except subprocess.CalledProcessError as e:
                result["pyenv"]["error"] = str(e)
                logger.error("Failed to install pyenv via Homebrew: %s", e)
        else:
            result["pyenv"]["error"] = "Homebrew not found - please install Homebrew first"
            logger.error("Homebrew not found, cannot install pyenv")
        
        return result


class WindowsPlatform(Platform):
    name = "windows"

    def install_uv(self) -> Dict[str, Any]:
        result = {"uv": {"installed": False, "version": None, "error": None}}
        existing = verify_tool("uv")
        if existing["installed"]:
            result["uv"]["installed"] = True
            result["uv"]["version"] = existing["version"]
            logger.info("uv already installed: %s", existing["version"])
            return result
        
        # Check for Scoop
        if check_command_exists("scoop"):
            try:
                logger.info("Installing uv via Scoop...")
                run_command(["scoop", "install", "uv"], check=True)
                verification = verify_tool("uv")
                if verification["installed"]:
                    result["uv"]["installed"] = True
                    result["uv"]["version"] = verification["version"]
                    return result
            except subprocess.CalledProcessError:
                logger.warning("Scoop installation failed")
        
        # Fall back to PowerShell installer
        try:
            logger.info("Installing uv via PowerShell...")
            ps_cmd = "irm https://astral.sh/uv/install.ps1 | iex"
            subprocess.run(["powershell", "-Command", ps_cmd], check=True)
            verification = verify_tool("uv")
            if verification["installed"]:
                result["uv"]["installed"] = True
                result["uv"]["version"] = verification["version"]
        except Exception as e:
            result["uv"]["error"] = str(e)
            logger.error("Failed to install uv: %s", e)
        
        return result

    def install_pyenv(self) -> Dict[str, Any]:
        result = {"pyenv": {"installed": False, "version": None, "error": None}}
        
        # Check for pyenv-win
        if check_command_exists("pyenv"):
            existing = verify_tool("pyenv")
            if existing["installed"]:
                result["pyenv"]["installed"] = True
                result["pyenv"]["version"] = existing["version"]
                return result
        
        result["pyenv"]["error"] = "Please install pyenv-win manually: https://github.com/pyenv-win/pyenv-win"
        logger.warning("pyenv installation not automated on Windows")
        return result

    def check_prerequisites(self) -> Dict[str, bool]:
        checks = {
            "git_available": check_command_exists("git"),
            "python_version_ok": sys.version_info >= (3, 7),
            "venv_available": run_command([sys.executable, "-m", "venv", "--help"], check=False).returncode == 0,
        }
        return checks


def get_platform_handler() -> Platform:
    system = _platform.system()
    if system == "Linux":
        return LinuxPlatform()
    if system == "Darwin":
        return MacOSPlatform()
    if system == "Windows":
        return WindowsPlatform()
    logger.warning("Unknown platform %s, using generic handler", system)
    return LinuxPlatform()