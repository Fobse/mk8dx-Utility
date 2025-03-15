from cx_Freeze import setup, Executable

setup(
    name="AutoScore",
    version="1.0",
    description="Auotmated Scoreboard for mk8dx by Tobse",
    executables=[Executable("script.py")],  # macOS braucht kein "Win32GUI"
    options={
        "build_exe": {
            "packages": ["os", "sys", "cv2", "easyocr", "numpy", "PyQt6"],
            "include_files": ["config.json", "assets/"],  # Falls du zusätzliche Dateien hast
        }
    }
)
