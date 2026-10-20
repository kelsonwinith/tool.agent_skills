#!/usr/bin/env python3
"""Bootstrap companion skills for project-workflow.

Checks which required workflow and stack-specific skills are installed in the
current workspace or global agent skill directories. If any required skills are
missing, installs them via `npx skills add <repo> --skill <names...> -y`.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Dict, List, Optional, Set, Tuple

DEFAULT_REPO = "kelsonwinith/tool.agent_skills"

CORE_SKILLS: Tuple[str, ...] = (
    "project-workflow",
    "project-grill",
    "project-documentation",
    "project-plan",
    "project-implement",
)

REACT_SKILL = "project-react-architecture"
GO_SKILL = "project-go-architecture"


def detect_stacks(project_root: pathlib.Path) -> List[str]:
    """Detect project tech stacks from manifest files in project_root."""
    stacks: List[str] = []

    pkg_json = project_root / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps: Dict[str, str] = {}
            for key in ("dependencies", "devDependencies", "peerDependencies"):
                section = data.get(key)
                if isinstance(section, dict):
                    deps.update(section)
            if any(pkg in deps for pkg in ("react", "react-dom", "next")):
                stacks.append("react")
        except (OSError, json.JSONDecodeError):
            pass

    if (project_root / "go.mod").is_file():
        stacks.append("go")

    return stacks


def required_skills_for_project(
    project_root: pathlib.Path, include_all_stacks: bool = False
) -> Tuple[List[str], List[str]]:
    """Return (required_skills, detected_stacks) for project_root."""
    stacks = detect_stacks(project_root)
    skills = list(CORE_SKILLS)

    if include_all_stacks:
        skills.extend([REACT_SKILL, GO_SKILL])
    else:
        if "react" in stacks:
            skills.append(REACT_SKILL)
        if "go" in stacks:
            skills.append(GO_SKILL)

    return skills, stacks


def candidate_skill_dirs(
    project_root: pathlib.Path, home_dir: Optional[pathlib.Path] = None
) -> List[pathlib.Path]:
    """Return candidate directories where skills may be installed."""
    home = home_dir or pathlib.Path.home()
    dirs = [
        project_root / ".agents" / "skills",
        project_root / ".agent" / "skills",
        project_root / ".claude" / "skills",
        project_root / "skills",
        home / ".agents" / "skills",
        home / ".claude" / "skills",
        home / ".gemini" / "skills",
        home / ".gemini" / "config" / "skills",
    ]
    return dirs


def find_installed_skills(
    project_root: pathlib.Path, home_dir: Optional[pathlib.Path] = None
) -> Dict[str, str]:
    """Map installed skill name -> resolved SKILL.md path."""
    installed: Dict[str, str] = {}
    for base in candidate_skill_dirs(project_root, home_dir=home_dir):
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.is_file() and child.name not in installed:
                installed[child.name] = str(skill_md.resolve())
    return installed


def build_install_command(repo: str, missing_skills: List[str], global_scope: bool = False) -> List[str]:
    """Build the npx skills add command for missing skills."""
    cmd = ["npx", "skills", "add", repo, "--skill", *missing_skills, "-y"]
    if global_scope:
        cmd.append("-g")
    return cmd


def bootstrap(
    project_root: pathlib.Path,
    repo: str = DEFAULT_REPO,
    include_all_stacks: bool = False,
    dry_run: bool = False,
    global_scope: bool = False,
    home_dir: Optional[pathlib.Path] = None,
) -> Dict[str, object]:
    """Check and optionally install missing workflow skills."""
    required, stacks = required_skills_for_project(
        project_root, include_all_stacks=include_all_stacks
    )
    installed_map = find_installed_skills(project_root, home_dir=home_dir)
    missing = [name for name in required if name not in installed_map]

    install_cmd: Optional[List[str]] = None
    installed_now: List[str] = []
    status = "ok"
    error_message: Optional[str] = None

    if missing:
        install_cmd = build_install_command(repo, missing, global_scope=global_scope)
        if not dry_run:
            try:
                proc = subprocess.run(
                    install_cmd,
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode == 0:
                    installed_now = list(missing)
                    installed_map = find_installed_skills(project_root, home_dir=home_dir)
                    missing = [name for name in required if name not in installed_map]
                else:
                    status = "install_failed"
                    error_message = (proc.stderr or proc.stdout or "").strip()
            except FileNotFoundError as exc:
                status = "npx_not_found"
                error_message = str(exc)

    return {
        "status": status,
        "project_root": str(project_root.resolve()),
        "detected_stacks": stacks,
        "required_skills": required,
        "installed_skills": installed_map,
        "newly_installed": installed_now,
        "missing_skills": missing,
        "install_command": " ".join(install_cmd) if install_cmd else None,
        "error": error_message,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Auto-detect project stack and install missing project-workflow companion skills."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Target project root directory (default: current directory).",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"GitHub repo or package source for npx skills add (default: {DEFAULT_REPO}).",
    )
    parser.add_argument(
        "--all-stacks",
        action="store_true",
        help="Install both React and Go architecture skills regardless of project manifest.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check status without running npx skills add (alias for --dry-run).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be installed without executing npx skills add.",
    )
    parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Pass -g to npx skills add when installing missing skills.",
    )
    args = parser.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    result = bootstrap(
        project_root=root,
        repo=args.repo,
        include_all_stacks=args.all_stacks,
        dry_run=(args.dry_run or args.check),
        global_scope=args.global_scope,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
