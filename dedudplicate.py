from pathlib import Path
import hashlib
from collections import defaultdict

# -------- SETTINGS --------
SKIP_FOLDERS = {".git", "node_modules", "__pycache__"}
CHUNK_SIZE = 8192


# -------- HASH FUNCTION --------
def get_file_hash(file_path):
    hasher = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


# -------- GROUP BY SIZE (OPTIMIZATION) --------
def group_by_size(folder):
    size_map = defaultdict(list)

    for file in Path(folder).iterdir():
        if any(part in SKIP_FOLDERS for part in file.parts):
            continue

        if file.is_file():
            try:
                size_map[file.stat().st_size].append(file)
            except Exception as e:
                print(f"Error accessing {file}: {e}")

    # Only keep sizes with more than 1 file
    return {size: files for size, files in size_map.items() if len(files) > 1}


# -------- FIND DUPLICATES --------
def find_duplicates(folder):
    size_groups = group_by_size(folder)
    hash_map = defaultdict(list)

    for size, files in size_groups.items():
        for file in files:
            file_hash = get_file_hash(file)

            if file_hash:
                hash_map[file_hash].append(file)

    # Only keep actual duplicates
    duplicates = {
        h: files for h, files in hash_map.items() if len(files) > 1
    }

    return duplicates


# -------- DELETE / PREVIEW --------
def handle_duplicates(duplicates):
    total_deleted = 0
    to_delete = []

    print("\n--- Duplicate Files Found ---")
    for file_hash, files in duplicates.items():
        print(f"\nDuplicate group (hash={file_hash[:8]}...):")

        original = files[0]
        copies = files[1:]

        print(f"  Keep: {original}")

        for file in copies:
            print(f"  Duplicate: {file}")
            to_delete.append(file)

    if not to_delete:
        return 0

    print(f"\nTotal duplicates found: {len(to_delete)}")
    choice = input("Do you want to delete all these duplicates? (y/n): ").strip().lower()

    if choice == 'y':
        for file in to_delete:
            try:
                file.unlink()
                print(f"  Deleted: {file}")
                total_deleted += 1
            except Exception as e:
                print(f"  Error deleting {file}: {e}")
    else:
        print("Skipping deletion of duplicates.")

    return total_deleted

def delete_duplicates(folder):
    if not Path(folder).exists():
        print("Invalid path!")
        return 0

    print("\nScanning for duplicates...\n")

    duplicates = find_duplicates(folder)

    if not duplicates:
        print("No duplicates found ✅")
        return 0

    print(f"Found {len(duplicates)} duplicate groups")

    deleted = handle_duplicates(duplicates)

    if deleted > 0:
        print(f"\nDeleted {deleted} files")
    
    return deleted

# -------- MAIN --------
def main():
    folder = input("Enter folder path: ").strip()
    delete_duplicates(folder)

if __name__ == "__main__":
    main()