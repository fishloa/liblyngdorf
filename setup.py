"""Setup module for liblyngdorf."""
from pathlib import Path

from setuptools import setup

PROJECT_DIR = Path(__file__).parent.resolve()
README_FILE = PROJECT_DIR / "README.md"
VERSION = "0.0.1"


setup(
    name="liblyngdorf",
    version=VERSION,
    url="https://github.com/home-assistant-libs/liblyngdorf",
    download_url="https://github.com/home-assistant-libs/liblyngdorf",
    author="Alex Fishlock",
    author_email="alex.fishlock@racingjag.com",
    description="Library to control Lyngdorf devices",
    long_description=README_FILE.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=["liblyngdorf"],
    python_requires=">=3.9",
    install_requires=[],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
    ],
)
