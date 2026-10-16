"""Install a GitHub tool found in a post: clone it, detect the stack, run its install steps.

Nothing runs until you confirm. Everything goes into ~/instatools-apps/<repo>, with its own
virtualenv / node_modules, so nothing is installed system-wide.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import ai

APPS = Path(os.environ.get("INSTATOOLS_APPS", Path.home() / "instatools-apps"))


def _run(cmd: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def plan(repo_dir: Path) -> list[list[str]]:
    """Install commands for the detected stack (local, no sudo)."""
    steps: list[list[str]] = []
    f = lambda n: (repo_dir / n).exists()
    if f("pyproject.toml") or f("requirements.txt") or f("setup.py"):
        py = str(repo_dir / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
        steps.append([sys.executable, "-m", "venv", ".venv"])
        if f("requirements.txt"):
            steps.append([py, "-m", "pip", "install", "-r", "requirements.txt"])
        if f("pyproject.toml") or f("setup.py"):
            steps.append([py, "-m", "pip", "install", "-e", "."])
    if f("package.json"):
        pm = "pnpm" if f("pnpm-lock.yaml") else "yarn" if f("yarn.lock") else "npm"
        steps.append([pm, "install"])
        scripts = json.loads((repo_dir / "package.json").read_text(encoding="utf-8")).get("scripts", {})
        if "build" in scripts:
            steps.append([pm, "run", "build"])
    if f("go.mod"):
        steps.append(["go", "build", "./..."])
    if f("Cargo.toml"):
        steps.append(["cargo", "build", "--release"])
    if not steps and (f("docker-compose.yml") or f("compose.yaml")):
        steps.append(["docker", "compose", "pull"])
    return steps


def readme_notes(repo_dir: Path) -> str:
    """Ask Claude to pull env vars / extra setup out of the README (shown, never run)."""
    readme = next((p for p in repo_dir.glob("README*")), None)
    if not readme or not ai.available():
        return ""
    text = readme.read_text(encoding="utf-8", errors="ignore")[:20000]
    out = ai.ask_json([{"type": "text", "text": (
        "From this README, reply JSON only: "
        '{"what_it_is": "...", "requirements": ["..."], "env_vars": ["NAME: purpose"], '
        '"run_command": "how to start it after install", "warnings": ["paid API keys, risky permissions, etc."]}\n\n'
        + text)}], max_tokens=1200)
    lines = [f"What it is: {out.get('what_it_is','')}"]
    for k in ("requirements", "env_vars", "warnings"):
        if out.get(k):
            lines.append(f"{k.replace('_',' ').title()}: " + "; ".join(out[k]))
    if out.get("run_command"):
        lines.append(f"Run it with: {out['run_command']}")
    return "\n".join(lines)


def install(repo: str, yes: bool = False) -> Path:
    m = re.search(r"(?:github\.com/)?([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$", repo.strip())
    if not m:
        raise ValueError(f"Not a GitHub repo: {repo}")
    owner, name = m.groups()
    dest = APPS / name
    APPS.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        _run(["git", "pull", "--ff-only"], dest)
    else:
        _run(["git", "clone", "--depth", "1", f"https://github.com/{owner}/{name}.git", str(dest)], APPS)

    steps = plan(dest)
    notes = readme_notes(dest)
    print(f"\n{owner}/{name} → {dest}")
    if notes:
        print(notes)
    print("\nInstall steps:" if steps else "\nNo automatic install steps detected — see the README.")
    for s in steps:
        print("  " + " ".join(s))
    missing = sorted({s[0] for s in steps if not Path(s[0]).is_absolute() and not shutil.which(s[0])})
    if missing:
        print(f"\nMissing on this computer: {', '.join(missing)} — install them first.")
        return dest
    if steps and (yes or input("\nRun these now? [y/N] ").strip().lower() == "y"):
        for s in steps:
            _run(s, dest)
        print(f"\nInstalled {owner}/{name} in {dest}")
    return dest
