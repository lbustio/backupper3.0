import shutil
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from fnmatch import fnmatch
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from colorama import init, Fore
import hashlib
import time
import argparse
import os
import stat

# Initialize colorama for colored logging output
init(autoreset=True)

# Global counters for reporting
files_copied = 0
files_ignored = 0

class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter that adds color to log messages based on the log level.
    """
    COLORS = {
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'DEBUG': Fore.BLUE
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, Fore.WHITE)
        record.msg = f"{color}{record.msg}{Fore.RESET}"
        return super().format(record)

def setup_logger():
    """
    Configures the logger with colored output and ensures the logging level shows everything.
    """
    handler = logging.StreamHandler()
    formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logging.basicConfig(level=logging.DEBUG, handlers=[handler])

def load_gitignore_patterns(gitignore_path, base_dir):
    """
    Reads the `.gitignore` file and processes its patterns correctly.
    """
    patterns = []
    if gitignore_path.exists():
        with gitignore_path.open('r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                pattern = base_dir / line
                if line.endswith('/'):
                    patterns.append(pattern)
                else:
                    patterns.append(pattern)
                    if not any(c in line for c in ['*', '?', '[']) and not '.' in line.split('/')[-1]:
                        patterns.append(pattern.with_name(pattern.name + '/'))
    return patterns

def should_ignore(file_path, patterns, base_dir):
    """
    Determines if a file should be ignored based on the `.gitignore` patterns.
    """
    abs_path = file_path.resolve()
    rel_path = abs_path.relative_to(base_dir)

    for pattern in patterns:
        try:
            if fnmatch(str(rel_path), str(pattern)) or fnmatch(file_path.name, pattern.name):
                return True
        except Exception as e:
            logging.error(f"Error comparing {rel_path} with pattern {pattern}: {e}")
    return False

def copy_file(src_file, temp_dir, base_dir):
    """
    Copies a file from the source directory to a temporary backup directory.
    """
    global files_copied
    rel_path = src_file.relative_to(base_dir)
    dest_file = temp_dir / rel_path
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dest_file)
    files_copied += 1
    logging.info(f'File copied: {src_file}')

def calculate_sha256(file):
    """
    Calculates the SHA-256 hash of a file for integrity verification.
    """
    sha256_hash = hashlib.sha256()
    with open(file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_integrity(zip_path, original_hash):
    """
    Verifies the integrity of the ZIP file by comparing its calculated SHA-256 hash
    with the original hash stored during the backup process.
    """
    calculated_hash = calculate_sha256(zip_path)
    if calculated_hash == original_hash:
        logging.info("✅ The ZIP file is valid and has not been modified.")
    else:
        logging.error("❌ The ZIP file has been altered or is corrupted!")

def remove_readonly(func, path, exc_info):
    """
    This function removes the readonly attribute of a file, allowing its deletion.
    For Unix, it changes permissions to 777; for Windows, it removes the read-only flag.
    """
    if func == os.remove or func == os.rmdir:
        if os.name == 'nt':  # Windows
            # Remove readonly attribute (if any)
            os.chmod(path, stat.S_IWRITE)
        else:  # Unix-based systems
            # Change file mode to ensure it's writable and deletable
            os.chmod(path, 0o777)
    func(path)

def copy_and_zip(src, dest, verify=False, comment=None):
    """
    Copies files from the source directory to a temporary directory, compresses them into a ZIP file,
    and optionally verifies the integrity of the ZIP file by checking its SHA-256 hash.
    """
    global files_copied, files_ignored
    start_time = time.time()

    setup_logger()

    logging.debug("Starting the backup process.")

    src = Path(src).resolve()
    dest = Path(dest).resolve()
    
    timestamp = datetime.now().strftime('%Y.%m.%d-%H.%M.%S')  # Updated format for timestamp
    folder_name = src.name  # Get the name of the source folder
    zip_name = f'{timestamp} - {folder_name}.zip'  # Combine timestamp and folder name for ZIP file name

    # Create a folder with the same name as the ZIP file (without the .zip extension)
    backup_folder = dest / f'{timestamp} - {folder_name}'
    logging.debug(f"Creating backup folder: {backup_folder}")
    backup_folder.mkdir(parents=True, exist_ok=True)

    zip_path = backup_folder / zip_name
    readme_path = backup_folder / 'readme.txt'
    temp_dir = backup_folder / f'temp_backup_{timestamp}'
    
    gitignore_path = src / '.gitignore'
    ignore_patterns = load_gitignore_patterns(gitignore_path, src)

    files_to_copy = []
    for root, dirs, files in os.walk(src):
        root_path = Path(root)

        # Skip copying files and directories inside `.git`
        if ".git" in dirs:
            dirs.remove(".git")

        dirs[:] = [d for d in dirs if not should_ignore(root_path / d, ignore_patterns, src)]

        for file in files:
            file_path = root_path / file
            if should_ignore(file_path, ignore_patterns, src):
                logging.warning(f'Ignored: {file_path}')
                files_ignored += 1
                continue
            files_to_copy.append(file_path)

    logging.debug(f"Total files to copy: {len(files_to_copy)}")

    with ThreadPoolExecutor() as executor:
        list(tqdm(executor.map(lambda f: copy_file(f, temp_dir, src), files_to_copy),
                  total=len(files_to_copy), desc="Copying files"))

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in tqdm(temp_dir.rglob('*'), total=len(files_to_copy), desc="Compressing files"):
            zipf.write(file, file.relative_to(temp_dir))

    shutil.rmtree(temp_dir, onerror=remove_readonly)

    zip_hash = calculate_sha256(zip_path)

    with readme_path.open('w', encoding='utf-8') as readme:
        readme.write(f'Backup created on: {timestamp}\n')
        readme.write(f'ZIP file created: {zip_name}\n')
        readme.write(f'SHA-256 hash of the ZIP file: {zip_hash}\n')
        if comment:
            readme.write(f'Comment: {comment}\n')

    logging.info(f'Backup completed: {zip_path}')
    logging.info(f'Readme created at: {readme_path}')
    logging.info(f'SHA-256 hash of the ZIP file: {zip_hash}')

    if verify:
        logging.info("Verifying the integrity of the ZIP file...")
        verify_integrity(zip_path, zip_hash)

    end_time = time.time()
    total_time = end_time - start_time

    logging.info(f"\nBackup Report:")
    logging.info(f"-------------------------------")
    logging.info(f"Time taken: {total_time:.2f} seconds")
    logging.info(f"Files copied: {files_copied}")
    logging.info(f"Files ignored: {files_ignored}")
    logging.info(f"Source directory: {src}")
    logging.info(f"Destination directory: {dest}")
    logging.info(f"Size of the ZIP file: {os.path.getsize(zip_path) / (1024 * 1024):.2f} MB")

    if verify:
        logging.info(f"SHA-256 hash of the ZIP file: {zip_hash}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Backup a directory while respecting .gitignore')
    parser.add_argument('source', type=str, help='Source directory to copy')
    parser.add_argument('destination', type=str, help='Destination directory to save the ZIP file')
    parser.add_argument('--verify', action='store_true', help='Verify ZIP file integrity')
    parser.add_argument('--comment', type=str, help='Add a comment or note about the content being processed')
    
    args = parser.parse_args()
    copy_and_zip(args.source, args.destination, verify=args.verify, comment=args.comment)
