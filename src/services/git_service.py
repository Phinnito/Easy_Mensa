import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def publish_changes(message: str) -> tuple[bool, str]:
    """
    Commit and push recipe/content changes when running inside a Git checkout.
    Works especially well in GitHub Codespaces, where Git authentication is
    already available.
    """
    if not (ROOT / ".git").exists():
        return False, "当前运行环境不是 Git 仓库，菜谱已保存但无法自动发布。"

    add = _run("git", "add", "data", "images")
    if add.returncode != 0:
        return False, add.stderr.strip() or "git add 失败"

    diff = _run("git", "diff", "--cached", "--quiet")
    if diff.returncode == 0:
        return True, "没有新的内容需要发布。"

    commit = _run("git", "commit", "-m", message)
    if commit.returncode != 0:
        return False, commit.stderr.strip() or commit.stdout.strip() or "git commit 失败"

    push = _run("git", "push")
    if push.returncode != 0:
        return False, push.stderr.strip() or push.stdout.strip() or "git push 失败"

    return True, "已经提交并推送到 GitHub。"
