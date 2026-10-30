
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_git(*args, check=True):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result


def git(*args):
    return run_git(*args).stdout.strip()


def check_clean():
    status = git("status", "--porcelain")

    if status:
        raise RuntimeError(
            "Working tree is not clean. "
            "Commit or review changes first."
        )


def integrate_commit(source_commit):
    print("=== Git Integration Workflow ===")

    branch = git("branch", "--show-current")

    if branch == "main":
        raise RuntimeError(
            "Do not integrate directly into main. "
            "Use a personal or test branch."
        )

    check_clean()

    # 確認 Git 沒有正在進行其他 Merge
    merge_head = run_git(
        "rev-parse", "-q", "--verify", "MERGE_HEAD",
        check=False
    )

    if merge_head.returncode == 0:
        raise RuntimeError(
            "An unresolved merge already exists."
        )

    # 取得遠端資料
    git("fetch", "origin", "--prune")

    # 確認來源 Commit 存在
    source_commit = git(
        "rev-parse", "--verify",
        f"{source_commit}^{{commit}}"
    )

    # 確認是否已經整合
    ancestor = run_git(
        "merge-base", "--is-ancestor",
        source_commit, "HEAD",
        check=False
    )

    if ancestor.returncode == 0:
        print("Commit already integrated.")
        return

    if ancestor.returncode != 1:
        raise RuntimeError(
            "Cannot determine commit ancestry."
        )

    print("Target branch:", branch)
    print("Source commit:", source_commit)

    print("\n=== Source Changes ===")
    print(
        git(
            "show", "--stat",
            "--format=short", source_commit
        )
    )

    # 人工確認後才嘗試 Merge
    answer = input(
        "\nType MERGE to attempt integration: "
    ).strip()

    if answer != "MERGE":
        print("Integration cancelled.")
        return

    # 執行 Git Merge，但不自動 Commit
    result = run_git(
        "merge", "--no-ff", "--no-commit",
        source_commit,
        check=False
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    # 檢查衝突
    conflicts = git(
        "diff", "--name-only", "--diff-filter=U"
    )

    if conflicts:
        print("\n=== MERGE CONFLICT ===")
        print(conflicts)
        print(
            "Inspect both versions before resolving."
        )
        print(
            "Do not commit until conflicts are resolved."
        )
        return

    if result.returncode != 0:
        raise RuntimeError(
            "Git merge failed. Inspect git status."
        )

    print("\n=== Merge Staged ===")
    print("No conflicts detected.")

    # 語法檢查
    syntax = subprocess.run(
        [
            sys.executable, "-m", "compileall",
            "-q", "groupctl.py", "src", "tests"
        ],
        cwd=ROOT
    )

    # 單元測試
    tests = subprocess.run(
        [
            sys.executable, "-m", "unittest",
            "discover", "-s", "tests",
            "-p", "test_*.py", "-v"
        ],
        cwd=ROOT
    )

    if syntax.returncode != 0 or tests.returncode != 0:
        print("\nAutomated checks FAILED.")
        print("Review the merge before committing.")
        return

    print("\nAutomated checks PASSED.")
    print("Semantic review is still required.")
    print("Merge has not been committed.")
    print("Inspect changes before completing integration.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python src/integration_workflow.py "
            "<source_commit>"
        )
        sys.exit(1)

    try:
        integrate_commit(sys.argv[1])
    except RuntimeError as error:
        print("Error:", error)
        sys.exit(1)
