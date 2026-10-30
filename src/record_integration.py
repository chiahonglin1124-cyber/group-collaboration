
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from groupctl import load_group, load_json, make_event, MEMBERS_DIR


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
        raise RuntimeError(
            result.stderr.strip() or "Git command failed"
        )

    return result


def git(*args):
    return run_git(*args).stdout.strip()


def all_events(group_id):
    """搜尋所有遠端分支上的協作事件。"""
    refs = git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/remotes/origin"
    ).splitlines()

    events = {}

    for ref in refs:
        paths = git(
            "ls-tree", "-r", "--name-only",
            ref, "--", ".group/events/"
        ).splitlines()

        for path in paths:
            if not path.endswith(".json"):
                continue

            result = run_git(
                "show", f"{ref}:{path}", check=False
            )

            if result.returncode != 0:
                continue

            try:
                event = json.loads(result.stdout)
            except json.JSONDecodeError:
                continue

            if event.get("group_id") == group_id:
                event_id = event.get("event_id")
                if event_id:
                    events[event_id] = event

    return list(events.values())


def is_ancestor(old_commit, new_commit):
    result = run_git(
        "merge-base", "--is-ancestor",
        old_commit, new_commit,
        check=False
    )

    if result.returncode == 0:
        return True

    if result.returncode == 1:
        return False

    raise RuntimeError("Cannot verify Git history.")


def record_integration(person_id, change_id):
    print("=== INT Result Verification ===")

    member_file = MEMBERS_DIR / f"{person_id}.json"

    if not member_file.is_file():
        raise ValueError("Unknown member.")

    member = load_json(member_file)

    if member.get("person_id") != person_id:
        raise ValueError("Member identity mismatch.")

    branch = git("branch", "--show-current")

    if not branch.startswith(f"people/{person_id}/"):
        raise ValueError("Use your own personal branch.")

    if git("status", "--porcelain"):
        raise RuntimeError("Working tree must be clean.")

    if run_git(
        "rev-parse", "-q", "--verify", "MERGE_HEAD",
        check=False
    ).returncode == 0:
        raise RuntimeError("An unfinished merge exists.")

    git("fetch", "origin", "--prune")

    merge_commit = git("rev-parse", "HEAD")
    remote_commit = git(
        "rev-parse", f"origin/{branch}"
    )

    if merge_commit != remote_commit:
        raise RuntimeError(
            "Push your merge commit before recording INT."
        )

    group = load_group()
    events = all_events(group["group_id"])

    publications = [
        e for e in events
        if e.get("event_type") == "change_published"
        and e.get("change_id") == change_id
    ]

    if not publications:
        raise ValueError("Published Change ID not found.")

    # 同一筆 PUB 可能出現在多個遠端分支
    unique = {e["event_id"]: e for e in publications}

    if len(unique) != 1:
        raise ValueError(
            "Multiple distinct publication events found."
        )

    publication = next(iter(unique.values()))
    source_commit = publication.get("commit")

    if not source_commit:
        raise ValueError("Publication has no source commit.")

    if not is_ancestor(source_commit, merge_commit):
        raise RuntimeError(
            "Published source commit is not integrated."
        )

    # 避免重複發布相同分支、相同 Change 的成功紀錄
    existing = [
        e for e in events
        if e.get("event_type") == "integration_result"
        and e.get("change_id") == change_id
        and e.get("target_branch") == branch
        and e.get("result") == "success"
        and is_ancestor(
            source_commit,
            e.get("merge_commit", "")
        )
    ]

    if existing:
        raise RuntimeError(
            "A successful integration_result already exists."
        )

    print("Change ID:", change_id)
    print("Source commit:", source_commit)
    print("Target branch:", branch)
    print("Integrated HEAD:", merge_commit)

    # 檢查編譯
    print("\n=== Syntax Check ===")

    syntax = subprocess.run(
        [
            sys.executable, "-m", "compileall",
            "-q", "groupctl.py", "src", "tests"
        ],
        cwd=ROOT
    )

    if syntax.returncode != 0:
        raise RuntimeError("Syntax check FAILED.")

    print("Syntax: PASS")

    # 執行自動化測試
    print("\n=== Unit Tests ===")

    tests = subprocess.run(
        [
            sys.executable, "-m", "unittest",
            "discover", "-s", "tests",
            "-p", "test_*.py", "-v"
        ],
        cwd=ROOT
    )

    if tests.returncode != 0:
        raise RuntimeError("Unit tests FAILED.")

    print("Tests: PASS")

    # 檢查執行測試後有沒有追蹤檔案被修改
    if git("status", "--porcelain"):
        raise RuntimeError(
            "Tests changed working tree; inspect before publishing."
        )

    # 人工語意審查
    print("\n=== Semantic Review ===")
    print("Review the integrated functionality.")
    print("Confirm source and target behavior are compatible.")

    answer = input(
        "Semantic review passed? (yes/no): "
    ).strip().lower()

    semantic_pass = answer == "yes"

    conflict_summary = input(
        "Conflict handling summary "
        "(enter 'none' if no conflicts): "
    ).strip()

    if not conflict_summary:
        raise ValueError("Conflict summary is required.")

    conflicts = []

    if conflict_summary.lower() != "none":
        print(
            "You must accurately document which files "
            "had conflicts."
        )

        raw = input(
            "Conflicted file paths, separated by commas: "
        ).strip()

        if not raw:
            raise ValueError(
                "Conflict paths are required."
            )

        conflicts = [
            path.strip()
            for path in raw.split(",")
            if path.strip()
        ]

    result = (
        "success" if semantic_pass else "needs_human"
    )

    # 最後一次明確確認
    print("\n=== Proposed Integration Result ===")
    print("Change:", change_id)
    print("Commit:", merge_commit)
    print("Build: pass")
    print("Tests: pass")
    print(
        "Semantic review:",
        "pass" if semantic_pass else "needs_human"
    )
    print("Result:", result)

    answer = input(
        "Type PUBLISH INT to create and push the event: "
    ).strip()

    if answer != "PUBLISH INT":
        print("Cancelled. No event created.")
        return

    event_path, event = make_event(
        "integration_result",
        person_id,
        {
            "related_events": [publication["event_id"]],
            "change_id": change_id,
            "target_branch": branch,
            "result": result,
            "merge_commit": merge_commit,
            "conflicts": conflicts,
            "conflict_resolution_summary": conflict_summary,
            "verification": {
                "build": "pass",
                "tests": "pass",
                "semantic_review": (
                    "pass" if semantic_pass else "needs_human"
                )
            },
            "summary": (
                f"Integrated {change_id}; "
                f"verification result: {result}."
            )
        }
    )

    relative_path = event_path.relative_to(ROOT)

    git("add", str(relative_path))
    git(
        "commit", "-m",
        f"Record INT result for {change_id}"
    )
    git("push", "origin", branch)

    print("\n=== Integration Result Published ===")
    print("Event ID:", event["event_id"])
    print("Change ID:", change_id)
    print("Result:", result)
    print("Merge commit:", merge_commit)


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python src/record_integration.py "
            "<person_id> <change_id>"
        )
        return 1

    try:
        record_integration(sys.argv[1], sys.argv[2])
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print("Error:", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
