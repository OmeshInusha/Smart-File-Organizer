from pathlib import Path
from datetime import datetime
import mimetypes


# -------- SETTINGS --------
SKIP_FOLDERS = {".git", "node_modules", "__pycache__"}


# -------- GET METADATA --------
def get_file_metadata(file: Path):
    try:
        stat = file.stat()

        return {
            "name": file.name,
            "path": str(file),
            "extension": file.suffix.lower(),
            "size_kb": round(stat.st_size / 1024, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "file_type": mimetypes.guess_type(file.name)[0] or "unknown"
        }

    except PermissionError:
        return None
    except Exception as e:
        print(f"[ERROR] {file}: {e}")
        return None


# -------- SCAN DIRECTORY --------
def scan_directory(folder):
    base = Path(folder)
    results = []

    for file in base.iterdir():
        try:
            if any(part in SKIP_FOLDERS for part in file.parts):
                continue

            if not file.exists():
                continue

            if file.is_file():
                metadata = get_file_metadata(file)

                if metadata:
                    results.append(metadata)

        except PermissionError:
            continue
        except Exception as e:
            print(f"[SCAN ERROR] {file}: {e}")
            continue

    return results


# -------- MAIN --------
def main():
    folder = input("Enter folder path: ").strip()

    path = Path(folder)

    if not path.exists():
        print("Invalid path!")
        return

    print("\nScanning directory...\n")

    files = scan_directory(folder)

    print(f"Found {len(files)} files\n")

    # Show sample (first 10 files)
    for f in files[:10]:
        print(f)


if __name__ == "__main__":
    main()