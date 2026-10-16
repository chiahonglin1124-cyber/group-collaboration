
import json
import sys
import uuid
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
    members = []

    for path in sorted(MEMBERS_DIR.glob("*.json")):
        members.append(load_json(path))

    return members

def show_group():
    group = load_group()

    print("=== Group Information ===")
    print("Protocol Version:", group["protocol_version"])
    print("Group ID:", group["group_id"])
    print("Canonical Branch:", group["canonical_branch"])
    print("Assignment File:", group["assignment_file"])
def show_members():
    print("=== Group Members ===")

    members = load_members()

    if not members:
        print("No members found.")
        return

    for member in members:
        print("Person ID:", member["person_id"])
        print("Display Name:", member["display_name"])
        print("--------------------")


def create_finding(person_id, summary):
    group = load_group()

    # 確認成員身分存在
    member_file = MEMBERS_DIR / f"{person_id}.json"

    if not member_file.is_file():
        print("Error: Member not found.")
        return

    member = load_json(member_file)

    if member.get("person_id") != person_id:
        print("Error: Member ID mismatch.")
        return

    # 使用 UTC 時間
    now = datetime.now(timezone.utc)

    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    created_at = now.isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )

    # 建立唯一事件編號
    suffix = uuid.uuid4().hex[:8]
    event_id = f"E-{timestamp}-{person_id}-{suffix}"

    # 建立符合規格的事件
    event = {
        "protocol_version": group["protocol_version"],
        "event_id": event_id,
        "event_type": "finding",
        "group_id": group["group_id"],
        "person_id": person_id,
        "created_at": created_at,
        "related_events": [],
        "summary": summary,
        "evidence": []
    }

    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    event_file = EVENTS_DIR / f"{event_id}.json"

    # 使用 x 避免覆寫既有事件
    with open(event_file, "x", encoding="utf-8") as f:
        json.dump(event, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print("Finding event created successfully!")
    print("Event ID:", event_id)
    print("Saved to:", event_file)


def main():
    if len(sys.argv) < 2:
        print("=== Group Collaboration Tool ===")
        print("Usage:")
        print("  python groupctl.py members")
        print("  python groupctl.py finding <person_id> <summary>")
        return

    command = sys.argv[1]

    if command == "group":
        show_group()

    elif command == "members":
        show_members()

    elif command == "finding":
        if len(sys.argv) < 4:
            print("Usage: finding <person_id> <summary>")
            return

        person_id = sys.argv[2]
        summary = " ".join(sys.argv[3:])

        create_finding(person_id, summary)

    else:
        print("Unknown command:", command)


if __name__ == "__main__":
    main()
