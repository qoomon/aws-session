import setuptools
import sys
import os
__directory__=os.path.dirname(os.path.realpath(__file__))
os.chdir(__directory__)

def read_text(file_name):
    with open(file_name) as file:
        return file.read()

setuptools.setup(
    name='aws-session',
    version='0.1.0',
    author="Bengt Brodersen",
    author_email="me@qoomon.me",
    description="A CLI to generate and store session credentials in ~/.aws/credentials file, based on ~/.aws/config profiles",
    long_description=read_text("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/qoomon/aws-session",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'awscli',
        'botocore'
    ],
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'aws-session = aws_session.cli:main',
        ]
    }
)
