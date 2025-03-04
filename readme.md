# 📦 Backup Utility - Automated Directory Backup with `.gitignore` Support

## 📖 Description
This script allows you to **create compressed backups** of a directory while **respecting the `.gitignore` file**.  
It supports **multithreading** for faster file copying, **SHA-256 checksum verification**, and logs the process details.

The backup is stored in a structured directory containing:
- A **ZIP file** named with the timestamp and source folder name.
- A **`readme.txt`** containing the backup details, including the file list and checksum.

---

## 🛠 Features
✅ **Respects `.gitignore`** – Excludes files/folders ignored by Git.  
✅ **Multithreaded copying** – Speeds up file transfer using multiple threads.  
✅ **ZIP compression** – Efficiently compresses the copied files.  
✅ **SHA-256 integrity check** – Ensures the ZIP file is not corrupted.  
✅ **Structured backup folder** – Stores the ZIP and log file in a dedicated folder.  
✅ **Command-line interface** – Easily configurable with parameters.  

---

## 📂 Backup Folder Structure
After running the script, your backup will be stored in the following format:

<destination_directory>/
\
│── 2025.03.04-09.05.00-source_folder/
\
│ │── 2025.03.04-09.05.00-source_folder.zip
\
│ │── readme.txt


- **`2025.03.04-09.05.00-source_folder/`** → The folder that contains the backup.
- **`2025.03.04-09.05.00-source_folder.zip`** → The compressed backup.
- **`readme.txt`** → Contains backup details (date, file list, SHA-256 hash, etc.).

---

## 🚀 Installation & Requirements
This script requires Python 3.7+ and some external dependencies.  
To install the required packages, run:

```bash
pip install -r requirements.txt
```

If you don't have a ``requirements.txt``, manually install dependencies:

```bash
pip install tqdm colorama
```

## ⚡ Usage

Run the script with the following command:

```bash
python backupper.py <source_directory> <destination_directory> [options]
```

### Example Usage

```bash
python backupper.py /home/user/project /mnt/backup --verify --comment "Backup before deployment"
```

### **Command-Line Options**
| Option           | Description |
|-----------------|-------------|
| `<source>`      | The directory to back up. |
| `<destination>` | The directory where the backup will be stored. |
| `--verify`      | (Optional) Verifies the ZIP integrity using SHA-256. |
| `--comment`     | (Optional) Adds a comment to `readme.txt`. |

## 📝 readme.txt Contents

Each backup includes a readme.txt file with details such as:

```bash
🔹🔹🔹 BACKUP REPORT 🔹🔹🔹

📅 Created on: 2025.03.04-09.05.00
📦 ZIP file: 2025.03.04-09.05.00-source_folder.zip
📏 Size: 120.45 MB
🔑 SHA-256: a3f1d9e7a6b...
📝 Comment: Backup before deployment

📂 Files Copied (142):
  - src/main.py
  - src/utils/helpers.py
  - assets/logo.png

🚫 Files Ignored (5):
  - .git/
  - node_modules/
```

## 🛠 Contributing

Feel free to fork this repository, open an issue, or submit a pull request with improvements.

### How to Contribute

1. Fork the repository on GitHub.

2. Clone your fork to your local machine:

```bash
git clone https://github.com/your-username/backupper.git
```

3. Create a new branch:

```bash
git checkout -b feature/improve-logging
```

4. Make your changes and commit:

```bash
git commit -m "Improved logging system"
```

5. Push to GitHub and create a pull request

## 🏆 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 📬 Contact

For questions or suggestions, feel free to reach out:

📧 Email: lbustio@gmail.com

Feel free to customize it with your **GitHub username**, **email**, and **social links** before up