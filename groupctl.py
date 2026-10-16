
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
        if command == "group":
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
