import setuptools
import sys
from os import path
from pathlib import Path
__directory__=path.dirname(path.realpath(__file__))

setuptools.setup(
    name='aws-session',
    version='0.1.0',
    author="Bengt Brodersen",
    author_email="qoo@qoomon.me",
    description="A CLI to generate and store session credentials in ~/.aws/credentials file, based on ~/.aws/config profiles",
    long_description=Path(path.join(__directory__, "README.md")).read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/qoomon/aws-session",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'awscli'
    ],
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'aws-session = aws_session.cli:main',
        ]
    }
)
