from cx_Freeze import setup, Executable

setup(
    name="PyleWM",
    version="1.1",

    packages=["pylewm", "pylewm.layouts", "pylewm.modes"],
    package_data={
        "pylewm": ["PyleWM.png", "data/*"],
    },

    options = {
        "build_exe": {
            "packages": ["pystray", "pylnk3", "pylewm.modes", "pylewm.layouts", "pylewm"],
        },
    },

    executables = [
        Executable("PyleWM.py", base="Win32GUI"),
    ],
)