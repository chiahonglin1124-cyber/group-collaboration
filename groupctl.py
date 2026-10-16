
import json
import sys
import uuid
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
GROUP_DIR = ROOT / ".group"
GROUP_FILE = GROUP_DIR / "group.json"
MEMBERS_DIR = GROUP_DIR / "members"
EVENTS_DIR = GROUP_DIR / "events"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_group():
    return load_json(GROUP_FILE)


def load_members():
    return [
        load_json(path)
        for path in sorted(MEMBERS_DIR.glob("*.json"))
    ]


def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout.strip()


def make_event(event_type, person_id, extra):
    group = load_group()

    member_file = MEMBERS_DIR / f"{person_id}.json"

    if not member_file.is_file():
        raise ValueError("Member not found.")

    member = load_json(member_file)

    if member.get("person_id") != person_id:
        raise ValueError("Member ID mismatch.")

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]

    event_id = f"E-{timestamp}-{person_id}-{suffix}"

    event = {
        "protocol_version": group["protocol_version"],
        "event_id": event_id,
        "event_type": event_type,
        "group_id": group["group_id"],
        "person_id": person_id,
        "created_at": now.isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "related_events": [],
    }

    event.update(extra)

    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EVENTS_DIR / f"{event_id}.json"

    with open(path, "x", encoding="utf-8") as f:
        json.dump(event, f, indent=4, ensure_ascii=False)
        f.write("\n")

    return path, event


def show_group():
    group = load_group()

    print("=== Group Information ===")

    for key, value in group.items():
        print(f"{key}: {value}")


def show_members():
    print("=== Group Members ===")

    for member in load_members():
        print("Person ID:", member["person_id"])
        print("Display Name:", member["display_name"])
        print("--------------------")


def create_finding(person_id, summary):
    path, event = make_event(
        "finding",
        person_id,
        {
            "summary": summary,
            "evidence": []
        }
    )

    print("Finding event created!")
    print("Event ID:", event["event_id"])
    print("File:", path)


def publish_change(person_id, summary):
    # 1. 確認成員存在
    member_file = MEMBERS_DIR / f"{person_id}.json"

    if not member_file.is_file():
        raise ValueError("Unknown member.")

    # 2. 取得目前 Branch
    branch = git("branch", "--show-current")

    if not branch.startswith(f"people/{person_id}/"):
        raise ValueError(
            "You must publish from your personal branch."
        )

    # 3. 確認程式修改已經 Commit
    status = git("status", "--porcelain")

    if status:
        raise ValueError(
            "Working tree is not clean. "
            "Commit your changes before publishing."
        )

    # 4. 取得真正的 Commit ID
    commit = git("rev-parse", "HEAD")

    # 5. 執行快速語法檢查
    print("Running Python syntax check...")

    result = subprocess.run(
        [sys.executable, "-m", "py_compile",
         str(ROOT / "groupctl.py")],
        cwd=ROOT
    )

    if result.returncode != 0:
        raise RuntimeError("Syntax check failed.")

    # 6. 推送個人工作 Branch
    print("Pushing work branch...")
    git("push", "origin", branch)

    # 7. 找出最新 Commit 修改的檔案
    changed = git(
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        "HEAD"
    )

    files_changed = changed.splitlines() if changed else []

    # 8. 建立唯一的 Change ID
    change_id = "C-" + uuid.uuid4().hex[:8]

    # 9. 建立事件
    path, event = make_event(
        "change_published",
        person_id,
        {
            "change_id": change_id,
            "branch": branch,
            "commit": commit,
            "summary": summary,
            "files_changed": files_changed,
            "interface_changes": [],
            "tests_run": [
                "python -m py_compile groupctl.py"
            ],
            "known_issues": [],
            "proposed_for_integration": True
        }
    )

    # 10. Commit 事件
    git("add", str(path.relative_to(ROOT)))

    git(
        "commit",
        "-m",
        f"Publish change event {change_id}"
    )

    # 11. Push 事件
    git("push", "origin", branch)

    print("\n=== Change Published ===")
    print("Change ID:", change_id)
    print("Event ID:", event["event_id"])
    print("Branch:", branch)
    print("Commit:", commit)
    print("Event File:", path)
    print("Published successfully!")


def sync_group():
    print("=== Group Synchronization ===")

    # 1. 記錄目前的 Git 狀態
    branch = git("branch", "--show-current")
    commit = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain"))

    print("Current branch:", branch)
    print("Current commit:", commit[:12])
    print("Uncommitted changes:", "Yes" if dirty else "No")

    # 2. 取得 GitHub 最新資料
    print("\nFetching remote updates...")
    git("fetch", "origin", "--prune", "--tags")

    group = load_group()
    canonical = "origin/" + group["canonical_branch"]

    # 3. 比較個人版本與 main
    git("rev-parse", "--verify", canonical)

    counts = git(
        "rev-list", "--left-right", "--count",
        f"HEAD...{canonical}"
    ).split()

    ahead, behind = map(int, counts)

    print("\n=== Canonical Branch ===")
    print("Canonical:", canonical)
    print("Local-only commits:", ahead)
    print("Canonical-only commits:", behind)

    # 4. 找出所有遠端分支
    refs = git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/remotes/origin"
    ).splitlines()

    # 5. 從遠端分支讀取事件
    discovered = {}

    for ref in refs:
        paths = git(
            "ls-tree", "-r", "--name-only",
            ref, "--", ".group/events/"
        ).splitlines()

        for path in paths:
            if not path.endswith(".json"):
                continue

            raw = git("show", f"{ref}:{path}")

            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                print("Invalid event JSON:", path)
                continue

            if event.get("group_id") != group["group_id"]:
                continue

            event_id = event.get("event_id")

            if event_id:
                discovered[event_id] = event

    # 6. 讀取上一次同步紀錄
    local_dir = GROUP_DIR / "local"
    local_dir.mkdir(parents=True, exist_ok=True)

    state_file = local_dir / "sync_state.json"
    known_ids = set()

    if state_file.exists():
        state = load_json(state_file)
        known_ids = set(state.get("seen_events", []))

    new_ids = set(discovered) - known_ids

    # 7. 顯示新的協作事件
    print("\n=== New Collaboration Events ===")

    if not new_ids:
        print("No new events.")
    else:
        for event_id in sorted(new_ids):
            event = discovered[event_id]

            print("--------------------")
            print("Event:", event_id)
            print("Type:", event.get("event_type"))
            print("Person:", event.get("person_id"))
            print("Summary:", event.get("summary", "N/A"))

            if "change_id" in event:
                print("Change ID:", event["change_id"])

    # 8. 儲存已讀取的事件 ID
    state = {
        "seen_events": sorted(discovered)
    }

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)
        f.write("\n")

    # 9. 提醒使用者是否需要整合
    print("\n=== Sync Summary ===")
    print("Total remote events:", len(discovered))
    print("New events:", len(new_ids))

    if behind > 0:
        print("Canonical branch has new commits.")
        print("Review before integrating them.")

    if dirty:
        print("Local changes were preserved.")

    print("No branches were merged.")
    print("Remote metadata sync completed.")

def show_status():
    print("=== Group Collaboration Status ===")

    group = load_group()
    branch = git("branch", "--show-current")
    commit = git("rev-parse", "HEAD")
    changes = git("status", "--porcelain")

    print("\n=== Identity ===")
    print("Group:", group["group_id"])
    print("Current branch:", branch)
    print("Current commit:", commit[:12])

    print("\n=== Local Changes ===")
    if changes:
        print(changes)
    else:
        print("Working tree clean.")

    print("\n=== Remote State ===")
    try:
        git("fetch", "origin", "--prune")

        canonical = (
            "origin/" + group["canonical_branch"]
        )

        canonical_commit = git(
            "rev-parse", canonical
        )

        counts = git(
            "rev-list",
            "--left-right",
            "--count",
            f"HEAD...{canonical}"
        ).split()

        ahead, behind = map(int, counts)

        print("Canonical:", canonical)
        print("Canonical commit:", canonical_commit[:12])
        print("Local-only commits:", ahead)
        print("Canonical-only commits:", behind)

    except RuntimeError as error:
        print("Remote information unavailable:", error)
        return

    print("\n=== Members ===")
    for member in load_members():
        print(
            member["person_id"],
            "-",
            member["display_name"]
        )

    print("\n=== Collaboration Events ===")

    refs = git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/remotes/origin"
    ).splitlines()

    events = {}

    for ref in refs:
        paths = git(
            "ls-tree",
            "-r",
            "--name-only",
            ref,
            "--",
            ".group/events/"
        ).splitlines()

        for path in paths:
            if not path.endswith(".json"):
                continue

            try:
                event = json.loads(
                    git("show", f"{ref}:{path}")
                )
            except (json.JSONDecodeError, RuntimeError):
                continue

            if event.get("group_id") != group["group_id"]:
                continue

            event_id = event.get("event_id")
            if event_id:
                events[event_id] = event

    ordered = sorted(
        events.values(),
        key=lambda e: e.get("created_at", ""),
        reverse=True
    )

    print("Total events:", len(ordered))

    for event in ordered[:5]:
        print("--------------------")
        print("Type:", event.get("event_type", "unknown"))
        print("Person:", event.get("person_id", "unknown"))
        print("Summary:", event.get("summary", "N/A"))

    print("\n=== Latest Test Result ===")
    tests = [
        e for e in ordered
        if e.get("event_type") == "test_result"
    ]

    if tests:
        latest = tests[0]
        print("Result:", latest.get("automated_result", "unknown"))
        print("Commit:", latest.get("commit", "unknown"))
    else:
        print("No published test results found.")

    print("\n=== Reported Blockers ===")
    blockers = [
        e for e in ordered
        if e.get("event_type") == "blocker"
    ]

    print("Reported blocker events:", len(blockers))
    if blockers:
        print("Review blockers to determine if still active.")

    print("\n=== Recommended Next Action ===")
    if changes:
        print("Review and commit local changes when ready.")
    elif behind > 0:
        print("Run SYNC and review canonical updates.")
    else:
        print("Continue development or review pending changes.")

    print("\nStatus check complete. No merge performed.")

def main():
    if len(sys.argv) < 2:
        print("Available commands:")
        print("  group")
        print("  members")
        print("  finding <person_id> <summary>")
        print("  publish <person_id> <summary>")
        return

    command = sys.argv[1]

    try:
        if command == "status":
            show_status()

        elif command == "sync":
            sync_group()

        elif command == "group":
            show_group()

        elif command == "members":
            show_members()

        elif command == "finding":
            if len(sys.argv) < 4:
                raise ValueError(
                    "Usage: finding <person_id> <summary>"
                )

            create_finding(
                sys.argv[2],
                " ".join(sys.argv[3:])
            )

        elif command == "publish":
            if len(sys.argv) < 4:
                raise ValueError(
                    "Usage: publish <person_id> <summary>"
                )

            publish_change(
                sys.argv[2],
                " ".join(sys.argv[3:])
            )

        else:
            print("Unknown command:", command)

    except (ValueError, RuntimeError, OSError) as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
