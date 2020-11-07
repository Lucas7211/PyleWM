from cx_Freeze import setup, Executable

setup(
    name="PyleWM",
    version="1.0",

    packages=["pylewm", "pylewm.layouts"],
    package_data={
        "pylewm": ["PyleWM.png", "data/*"],
    },

    executables = [
        Executable("PyleWM.py", base="Win32GUI"),
    ],
)