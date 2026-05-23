from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from importlib.abc import Traversable


@dataclass(frozen=True)
class SkillTarget:
    name: str
    target_dir: Path

    def is_installed(self, skill_name: str) -> bool:
        return (self.target_dir / skill_name / "SKILL.md").exists()

    def install_skill(self, skill_name: str, source: Traversable, force: bool = False) -> bool:
        target_skill_dir = self.target_dir / skill_name
        if target_skill_dir.exists():
            if not force:
                return False
            shutil.rmtree(target_skill_dir)

        target_skill_dir.parent.mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory() as tmpdir:
            shutil.copytree(source, Path(tmpdir) / skill_name)
            shutil.copytree(Path(tmpdir) / skill_name, target_skill_dir)
        return True

    def uninstall_skill(self, skill_name: str) -> bool:
        target_skill_dir = self.target_dir / skill_name
        if not target_skill_dir.exists():
            return False
        shutil.rmtree(target_skill_dir)
        return True

    def post_install(self, installed_count: int) -> None:
        return

    def post_uninstall_all(self) -> None:
        return


class ClaudeSkillTarget(SkillTarget):
    def __init__(self) -> None:
        super().__init__(name="claude", target_dir=Path.home() / ".claude" / "skills")

    def post_install(self, installed_count: int) -> None:
        if installed_count <= 0:
            return
        from pbi_cli.core.claude_integration import ensure_claude_md_snippet

        ensure_claude_md_snippet()

    def post_uninstall_all(self) -> None:
        from pbi_cli.core.claude_integration import remove_claude_md_snippet

        remove_claude_md_snippet()


class CodexSkillTarget(SkillTarget):
    def __init__(self) -> None:
        super().__init__(name="codex", target_dir=Path.home() / ".agents" / "skills")


def get_skill_targets(agent: str) -> list[SkillTarget]:
    normalized = agent.lower()
    if normalized == "claude":
        return [ClaudeSkillTarget()]
    if normalized == "codex":
        return [CodexSkillTarget()]
    if normalized == "all":
        return [ClaudeSkillTarget(), CodexSkillTarget()]
    raise ValueError(f"Unsupported agent target: {agent}")
