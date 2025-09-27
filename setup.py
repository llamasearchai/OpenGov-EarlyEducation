#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for OpenEarlyEducation.

Installs the package in development mode with all dependencies.
"""

import os

from setuptools import find_packages, setup

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README for long description
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="openearlyeducation",
    version="2.0.0",
    author="Nik Jois",
    author_email="nikjois@llamasearch.ai",
    description="Research-based early childhood lesson planning and scheduling system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/openearlyeducation",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.7.0",
        ],
        "docker": [
            "docker-compose>=1.29.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "openearlyeducation=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
