from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from pbi_cli.main_pbi_cli import cli


def _skill_names() -> list[str]:
    skills_dir = Path("src/pbi_cli/skills")
    return sorted(p.name for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").exists())


def test_default_agent_is_claude(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["skills", "install", "--yes"])

    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "skills").exists()
    assert not (tmp_path / ".agents" / "skills").exists()


def test_codex_install_path_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["skills", "install", "--agent", "codex", "--yes"])

    assert result.exit_code == 0
    for name in _skill_names():
        assert (tmp_path / ".agents" / "skills" / name / "SKILL.md").exists()
    assert not (tmp_path / ".claude").exists()


def test_all_install_to_both(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["skills", "install", "--agent", "all", "--yes"])

    assert result.exit_code == 0
    for name in _skill_names():
        assert (tmp_path / ".agents" / "skills" / name / "SKILL.md").exists()
        assert (tmp_path / ".claude" / "skills" / name / "SKILL.md").exists()


def test_list_codex_status(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    runner = CliRunner()

    runner.invoke(cli, ["skills", "install", "--agent", "codex", "--yes", "--skill", "power-bi-dax"])
    result = runner.invoke(cli, ["skills", "list", "--agent", "codex"])

    assert result.exit_code == 0
    assert "power-bi-dax" in result.output
    assert "[installed]" in result.output
    assert "Target directory (codex):" in result.output


def test_uninstall_codex_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    runner = CliRunner()

    runner.invoke(cli, ["skills", "install", "--agent", "all", "--yes", "--skill", "power-bi-dax"])
    result = runner.invoke(cli, ["skills", "uninstall", "--agent", "codex", "--skill", "power-bi-dax"])

    assert result.exit_code == 0
    assert not (tmp_path / ".agents" / "skills" / "power-bi-dax").exists()
    assert (tmp_path / ".claude" / "skills" / "power-bi-dax").exists()


def test_force_overwrites_codex_folder(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    runner = CliRunner()

    runner.invoke(cli, ["skills", "install", "--agent", "codex", "--yes", "--skill", "power-bi-dax"])
    skill_file = tmp_path / ".agents" / "skills" / "power-bi-dax" / "SKILL.md"
    skill_file.write_text("overwritten", encoding="utf-8")

    result = runner.invoke(
        cli,
        ["skills", "install", "--agent", "codex", "--yes", "--skill", "power-bi-dax", "--force"],
    )

    assert result.exit_code == 0
    assert "overwritten" not in skill_file.read_text(encoding="utf-8")
