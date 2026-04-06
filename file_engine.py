import json
import shutil
from pathlib import Path
from datetime import datetime


# -------- 1. EXECUTE AND CREATE BACKUP LOG --------
def execute_plan(base_folder, plan):
    base = Path(base_folder).resolve()

    # Create a unique backup log file for this run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = base / f".revert_log_{timestamp}.json"

    backup_log = []
    moves = plan.get("moves", []) + plan.get("renames", [])

    print(f"\n🚀 Applying {len(moves)} file operations...")

    for item in moves:
        try:
            src = base / item["from"]
            dest = base / item["to"]

            # Safety checks
            if not src.exists():
                print(f"  [SKIP] Not found: {src.name}")
                continue
            if dest.exists():
                print(f"  [SKIP] Destination exists: {dest.name}")
                continue

            # Create target folder and move
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))

            # Record the successful move in our log
            backup_log.append({
                "original_path": str(src),
                "current_path": str(dest)
            })

            print(f"  [MOVED] {src.name} → {dest.relative_to(base)}")

        except Exception as e:
            print(f"  [ERROR] Failed to move {item['from']}: {e}")

    # Save the transaction log ONLY if moves happened
    if backup_log:
        with open(log_file, "w") as f:
            json.dump(backup_log, f, indent=2)
        print(f"\n✅ Done! Revert log saved to: {log_file.name}")
    else:
        print("\n⚠️ No files were moved.")

    return log_file


# -------- 2. REVERT CHANGES --------
def revert_changes(log_file_path):
    log_file = Path(log_file_path)

    if not log_file.exists():
        print(f"❌ Revert log not found: {log_file}")
        return

    print(f"\n⏪ Reverting changes using {log_file.name}...")

    with open(log_file, "r") as f:
        backup_log = json.load(f)

    for item in backup_log:
        src = Path(item["current_path"])  # Where it is now
        dest = Path(item["original_path"])  # Where it used to be

        try:
            if src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                print(f"  [REVERTED] {src.name}")
            else:
                print(f"  [MISSING] Cannot find {src.name} to revert.")
        except Exception as e:
            print(f"  [ERROR] Failed to revert {src.name}: {e}")

    # Clean up the log file after a successful revert
    log_file.unlink()

    # Clean up empty directories left behind by the revert
    clean_empty_directories(log_file.parent)
    print("\n✅ Revert complete!")


# -------- 3. CLEANUP HELPER --------
def clean_empty_directories(folder):
    """Recursively deletes empty folders left behind after reverting."""
    base = Path(folder)
    for dir_path in sorted(base.rglob('*'), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            try:
                dir_path.rmdir()
            except Exception:
                pass


# -------- MAIN (TESTING) --------
if __name__ == "__main__":
    # Fake LLM output for testing
    sample_plan = {
        "moves": [
            {"from": "test1.txt", "to": "Documents/test1.txt"},
            {"from": "test2.jpg", "to": "Images/Vacation/test2.jpg"}
        ]
    }

    # 1. Create fake files to test with
    Path("test1.txt").touch()
    Path("test2.jpg").touch()

    # 2. Execute the move (This will generate a .revert_log_xxx.json file)
    log_path = execute_plan(".", sample_plan)

    # 3. Ask user if they want to revert
    undo = input("\nDo you want to revert these changes? (y/n): ")
    if undo.lower() == 'y' and log_path:
        revert_changes(log_path)