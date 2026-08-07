"""
Setup configuration for SentinelAI CLI
"""

from setuptools import setup, find_packages

setup(
    name="sentinelai",
    version="0.1.0",
    description="AI-powered defensive security agent CLI",
    author="Team Finatics",
    packages=find_packages(),
    install_requires=[
        "python-nmap>=0.0.1",
        "click>=8.1.3",
        "colorama>=0.4.6",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "sentinelai=sentinelai.cli:main",
        ],
    },
    python_requires=">=3.8",
)
