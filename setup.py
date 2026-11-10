from setuptools import setup, find_packages

setup(
    name="scandisk",
    version="0.1.0",
    description="Disk Analyzer - A tool for analyzing disk space usage",
    author="Damien Moreau",
    package_dir={"": "."},
    packages=find_packages(where="."),
    install_requires=[
        "PyQt6==6.4.0",
    ],
    entry_points={
        "console_scripts": [
            "scandisk=scandisk.main:main",
        ],
    },
)
