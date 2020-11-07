from setuptools import setup, find_packages

setup(
    name="PyleWM",
    version="1.0",
    packages=["pylewm", "pylewm.layouts"],

    install_requires=[
        "pypiwin32>=223",
        "pystray>=0.15.0",
        "pygame>=2.0.0",
        "fuzzywuzzy>=0.18.0",
        "python-levenshtein>=0.12.0"
    ],
    package_data={
        "pylewm": ["PyleWM.png", "data/*"],
    },

    entry_points= {
        "console_scripts": [
            "PyleWM = pylewm.run:start"
        ]
    },

    author="Lucas de Vries",
    author_email="lucas@glacicle.org",

    description="A utility for tiled Window Management under the Windows OS inspired by linux tiling window managers such as i3 and awesomewm.",
    keywords="window management",
    url="https://github.com/GGLucas/PyleWM.git",
)