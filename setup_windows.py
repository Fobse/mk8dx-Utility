from cx_Freeze import setup, Executable

setup(
    name="AutoScore",
    version="1.0",
    description="Automated Scoreboard for mk8dx by Tobse",
    executables=[Executable("script.py", base="Win32GUI")],  # base="Win32GUI" verhindert ein Terminal-Fenster
    options={
        "build_exe": {
            "packages": ["os", "sys", "cv2", "easyocr", "numpy", "PyQt6"],
            #"include_files": ["config.json", "assets/"],  # Falls du zusätzliche Dateien hast
        }
    }
)
