# Workshop PDF Generator

A cross-platform desktop application built with Python and Tkinter to automate the creation of workshop PDF reports from folders of screenshots. It features dynamic metadata entry (question headers and explanatory notes), live image previews, and automated PDF compilation via `reportlab`.

---

## Features

- **Folder Scanning:** Automatically discovers `.png`, `.jpg`, and `.jpeg` screenshots using `pathlib`.
- **Dynamic Form Builder:** Generates editable question headers and explanation notes for every detected image inside a scrollable view.
- **Live Image Preview:** Automatically displays a scaled thumbnail of the screenshot you are currently working on.
- **Automated PDF Export:** Compiles all questions, images, and notes into a clean, professional workshop report.
- **Cross-Platform:** Works seamlessly on Linux (Fedora/Ubuntu) and Windows.

---

## Prerequisites

Make sure you have **Python 3** installed on your system.

---

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone <your-repository-url>
   cd <repository-folder>
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment:**
   - **Linux / macOS (Bash):**
     ```bash
     source venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     venv\Scripts\Activate
     ```
   - **Windows (Command Prompt):**
     ```cmd
     venv\Scripts\activate.bat
     ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

Once your virtual environment is active, launch the app by running:
```bash
python app.py
```

---

## Quick Launch Shortcuts

### 🐧 Linux (Fedora / Bash Alias)
Add the following alias to your `~/.bashrc`:
```bash
alias workshop-pdf="cd /path/to/repository && source venv/bin/activate && python app.py"
```
Then run `source ~/.bashrc` to use `workshop-pdf` anywhere.

### 🪟 Windows (Desktop Shortcut)
1. Inside your repository folder, create a file named `run.bat` containing:
   ```cmd
   @echo off
   cd /d "%~dp0"
   call venv\Scripts\activate
   python app.py
   ```
2. Right-click `run.bat` -> **Send to** -> **Desktop (create shortcut)** for one-click launching.