import setuptools
import os
__directory__=os.path.dirname(os.path.realpath(__file__))
os.chdir(__directory__)

def read_text(file_name):
    with open(file_name) as file:
        return file.read()

setuptools.setup(
    name='aws-session',
    version='5.4.0',
    author="Bengt Brodersen",
    author_email="me@qoomon.me",
    description="A CLI to generate session credentials based on ~/.aws/config profiles and store them as profile in ~/.aws/credentials file",
    long_description=read_text("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/qoomon/aws-session",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: System :: Systems Administration",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators"
    ],
    install_requires=[
        'botocore>=1.16.0,<2'
    ],
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'aws-session = aws_session.__main__:main',
        ]
    }
)
