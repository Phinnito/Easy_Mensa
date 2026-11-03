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


def _message(result: subprocess.CompletedProcess, fallback: str) -> str:
    return result.stderr.strip() or result.stdout.strip() or fallback


def publish_changes(message: str) -> tuple[bool, str]:
    """
    Safely publish recipe/content changes from a Codespace.

    The remote main branch can move independently (for example when the app
    code is updated through GitHub). We therefore commit recipe changes first,
    fetch the latest remote main, rebase the local recipe commit on top of it,
    and only then push.
    """
    if not (ROOT / ".git").exists():
        return False, "当前运行环境不是 Git 仓库，菜谱已保存但无法自动发布。"

    add = _run("git", "add", "data", "images")
    if add.returncode != 0:
        return False, _message(add, "git add 失败")

    diff = _run("git", "diff", "--cached", "--quiet")

    if diff.returncode == 1:
        commit = _run("git", "commit", "-m", message)
        if commit.returncode != 0:
            return False, _message(commit, "git commit 失败")
    elif diff.returncode != 0:
        return False, _message(diff, "检查待提交内容失败")

    fetch = _run("git", "fetch", "origin", "main")
    if fetch.returncode != 0:
        return False, _message(fetch, "获取 GitHub 最新版本失败")

    rebase = _run("git", "rebase", "origin/main")
    if rebase.returncode != 0:
        _run("git", "rebase", "--abort")
        return False, (
            "GitHub 最新版本与当前菜谱发生冲突，已自动取消合并，没有丢失本地菜谱。"
            "请稍后再试。\n\n"
            + _message(rebase, "git rebase 失败")
        )

    push = _run("git", "push", "origin", "HEAD:main")
    if push.returncode != 0:
        return False, _message(push, "git push 失败")

    return True, "已经同步 GitHub 最新版本，并成功发布菜谱。"
