import os
import subprocess
from pathlib import Path

def run_command(cmd):
    print(f"\n🚀 Running: {cmd}")
    os.system(cmd)

def install_requirements():
    run_command("pip install -r requirements.txt")

def install_setup():
    run_command("pip install -e .")

def update_requirements():
    run_command("pip freeze > requirements.txt")
    print("✅ requirements.txt updated.")

def git_push():
    msg = input("📝 Commit message: ").strip() or "update"
    run_command("git add .")
    run_command(f"git commit -m \"{msg}\"")
    run_command("git push")

def git_pull():
    run_command("git pull")

def main_menu():
    while True:
        print("\n📦 AutoReviewX Utility Menu")
        print("1. 📁 Metadata Extraction")
        print("2. 📄 Generate APA References")
        print("3. 📊 Generate Graphs")
        print("4. 🛠️ Install requirements.txt")
        print("5. 🧱 Install setup.py (editable)")
        print("6. 📌 Update requirements.txt")
        print("7. 🚀 Git Push")
        print("8. 🔄 Git Pull")
        print("9. 🗜 Backup project as ZIP")
        print("0. ❌ Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            print("\n🧠 Metadata Extraction:")
            print("a. Single PDF")
            print("b. Intelligent Extraction")
            print("c. Batch GROBID (single PDF)")
            print("d. Batch GROBID (folder of PDFs)")
            print("e. With Config (filter + enrich)")

            sub = input("Your choice (a/b/c/d/e): ").strip().lower()
            if sub == "a":
                path = input("Path to PDF: ")
                run_command(f"autoreviewx extract --pdf {path}")
            elif sub == "b":
                path = input("Path to PDF: ")
                run_command(f"autoreviewx extract-intelligent --pdf {path}")
            elif sub == "c":
                path = input("Path to PDF: ")
                run_command(f"autoreviewx extract-grobid --pdf {path}")
            elif sub == "d":
                folder = input("Folder with PDFs: ")
                run_command(f"autoreviewx extract-grobid-batch --dir {folder}")
            elif sub == "e":
                cfg = input("Path to config.yaml: ")
                folder = input("Folder with PDFs: ")
                run_command(f"autoreviewx extract-with-config --config {cfg} --dir {folder}")


        elif choice == "2":
            csv = input("Path to extracted metadata CSV: ")
            run_command(f"autoreviewx generate-apa --input {csv}")

        elif choice == "3":
            csv = input("Path to enriched metadata CSV: ")
            custom = input("Custom output folder (blank = default): ")
            if custom.strip():
                run_command(f"autoreviewx graphs --input {csv} --output {custom}")
            else:
                run_command(f"autoreviewx graphs --input {csv}")

        elif choice == "4":
            install_requirements()

        elif choice == "5":
            install_setup()

        elif choice == "6":
            update_requirements()

        elif choice == "7":
            git_push()

        elif choice == "8":
            git_pull()

        elif choice == "9":
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"AutoReviewX-backup-{timestamp}.zip"
            print(f"📦 Creating backup: {zip_name} ...")

            # Exclude common dev folders
            run_command(
                f'zip -r {zip_name} . -x "*.venv/*" "__pycache__/*" "*.git/*" "*.DS_Store" "*.egg-info/*"'
            )
            print(f"✅ Backup created: {zip_name}")


        elif choice == "0":
            print("👋 Exiting AutoReviewX CLI.")
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()
