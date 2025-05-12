# setup.py
from setuptools import setup, find_packages

setup(
    name="autoreviewx",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyYAML",
        "pandas",
        "requests",
        "graphviz",
        "crossrefapi",
        "openalex",
        "streamlit", "fastapi", "uvicorn", "matplotlib", "seaborn"
    ],
    entry_points={
        "console_scripts": [
            "autoreviewx=autoreviewx.cli.main:main"
        ]
    }
)