# setup.py for AudiencePulse
from setuptools import setup, find_packages

setup(
    name="audiencepulse",
    version="1.0.0",
    description="YouTube Comment Intelligence Platform",
    author="AudiencePulse Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "youtube-comment-downloader",
        "pandas",
        "tqdm",
        "groq",
        "python-dotenv",
        "streamlit",
        "gspread",
        "oauth2client",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "flake8",
        ],
    },
    entry_points={
        "console_scripts": [
            "audiencepulse=pipeline:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
