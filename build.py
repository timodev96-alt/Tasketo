import os
import shutil
import subprocess
import sys

def build():
    script_name = "main.py"
    app_name = "Tasketo"
    
    print(f"--- Starting build process for: {app_name} ---")

    folders_to_clean = ['dist', 'build']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Cleaned up: {folder}")

    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        f"--name={app_name}",
        script_name
    ]

    print("--- Executing PyInstaller... ---")
    try:
        subprocess.check_call(cmd)
        print("\n--- Build completed successfully! ---")
        print(f"Executable found in: dist/{app_name}.exe")
    except subprocess.CalledProcessError:
        print("\n--- Error: Build process failed ---")
        sys.exit(1)

if __name__ == "__main__":
    try:
        import PyInstaller
        build()
    except ImportError:
        print("Error: PyInstaller is not installed. Please install it using: pip install pyinstaller")