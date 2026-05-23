"""Skill installer commands for Claude Code and Codex integration."""

from __future__ import annotations

import importlib.resources
from typing import TYPE_CHECKING

import click

from pbi_cli.core.skill_targets import ClaudeSkillTarget, get_skill_targets

if TYPE_CHECKING:
    from importlib.abc import Traversable


def _get_bundled_skills() -> dict[str, Traversable]:
    """Return a mapping of skill-name -> Traversable for each bundled skill."""
    skills_pkg = importlib.resources.files("pbi_cli.skills")
    result: dict[str, Traversable] = {}
    for item in skills_pkg.iterdir():
        if item.is_dir() and (item / "SKILL.md").is_file():
            result[item.name] = item
    return result


@click.group("skills")
def skills() -> None:
    """Manage agent skills for Power BI workflows."""


def _agent_option(f):
    return click.option(
        "--agent",
        type=click.Choice(["claude", "codex", "all"], case_sensitive=False),
        default="claude",
        show_default=True,
        help="Agent skill target to manage.",
    )(f)


@skills.command("list")
@_agent_option
def skills_list(agent: str) -> None:
    """List available and installed skills."""
    bundled = _get_bundled_skills()
    if not bundled:
        click.echo("No bundled skills found.", err=True)
        return

    for target in get_skill_targets(agent):
        click.echo(f"Available Power BI skills ({target.name}):\n", err=True)
        for name in sorted(bundled):
            status = "installed" if target.is_installed(name) else "not installed"
            click.echo(f"  {name:<30} [{status}]", err=True)
        click.echo(f"\nTarget directory ({target.name}): {target.target_dir}\n", err=True)


@skills.command("install")
@click.option("--skill", "skill_name", default=None, help="Install a specific skill.")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing installations.")
@click.option("--yes", "yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt.")
@_agent_option
def skills_install(skill_name: str | None, force: bool, yes: bool, agent: str) -> None:
    """Install Power BI skills to configured target directory/directories."""
    bundled = _get_bundled_skills()
    if not bundled:
        click.echo("No bundled skills found.", err=True)
        return

    if skill_name and skill_name not in bundled:
        raise click.ClickException(
            f"Unknown skill '{skill_name}'. Available: {', '.join(sorted(bundled))}"
        )

    targets = get_skill_targets(agent)
    to_install = (
        {skill_name: bundled[skill_name]} if skill_name and skill_name in bundled else bundled
    )

    if not yes:
        click.echo("This command will install Power BI skills for selected target(s):\n")
        for target in targets:
            if isinstance(target, ClaudeSkillTarget):
                click.echo(
                    f"  {'~/.claude/skills/power-bi-*/':<52} "
                    f"copy {len(to_install)} skill folder(s)"
                )
                click.echo(f"  {'~/.claude/CLAUDE.md':<52} append pbi-cli skill trigger block")
                click.echo("\nThis affects ALL Claude Code sessions, not just Power BI work.\n")
            else:
                click.echo(
                    f"  {'~/.agents/skills/power-bi-*/':<52} "
                    f"copy {len(to_install)} skill folder(s)"
                )

        if not click.confirm("\nProceed?", default=False):
            click.echo("Aborted.")
            return

    installed_by_target: dict[str, int] = {target.name: 0 for target in targets}
    for target in targets:
        for name, source in sorted(to_install.items()):
            if target.is_installed(name) and not force:
                click.echo(
                    f"  [{target.name}] {name}: already installed (use --force to overwrite)",
                    err=True,
                )
                continue

            target.install_skill(name, source, force=force)
            installed_by_target[target.name] += 1
            click.echo(f"  [{target.name}] {name}: installed", err=True)

        target.post_install(installed_by_target[target.name])
        click.echo(
            f"\n[{target.name}] {installed_by_target[target.name]} "
            f"skill(s) installed to {target.target_dir}",
            err=True,
        )


@skills.command("uninstall")
@click.option("--skill", "skill_name", default=None, help="Uninstall a specific skill.")
@_agent_option
def skills_uninstall(skill_name: str | None, agent: str) -> None:
    """Remove installed skills from configured target directory/directories."""
    bundled = _get_bundled_skills()
    targets = get_skill_targets(agent)
    names = [skill_name] if skill_name else sorted(bundled)

    for target in targets:
        removed_count = 0
        for name in names:
            if not target.uninstall_skill(name):
                click.echo(f"  [{target.name}] {name}: not installed", err=True)
                continue

            removed_count += 1
            click.echo(f"  [{target.name}] {name}: removed", err=True)

        click.echo(f"\n[{target.name}] {removed_count} skill(s) removed.", err=True)

        if skill_name is None:
            target.post_uninstall_all()
