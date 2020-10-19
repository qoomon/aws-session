# aws-session

[![PyPI](https://img.shields.io/pypi/v/aws-session)](https://pypi.org/project/aws-session/)

A CLI to generate and store session credentials in `~/.aws/credentials` file, based on `~/.aws/config` profiles

## Install

`pip3 install aws-session`

## Usage
```
get session credentials:

    aws-session get [--profile/-p <profile_name>]

        --profile/-p <profile_name> : select profile ['default']
        --force/-f                  : force new session

    To create MFA user sessions just add `mfa_serial` to profile config in ~/.aws/config profiles

list session profiles:

    aws-session list

purge expired session profiles:

    aws-session purge

        --force/-f                  : purge all session profiles regardles of expiration

print help

    aws-session help
```

## Setup dev environment

#### Install Dev Dependencies
```
export PATH="${PATH}:/Users/${USER}/Library/Python/3.7/bin"
export PYTHONPATH="${PYTHONPATH}:/Users/${USER}/Library/Python/3.7/bin"
pip3 install --user -r requirements.txt
pip3 install --user -r requirements-dev.txt
```

## Run
`python3 -m aws_session get`

#### Create Package
`python3 setup.py clean --all sdist bdist_wheel` 

#### Local Install
`pip3 install --force-reinstall --no-deps dist/aws_session-*-py3-none-any.whl`

#### Deploy to PiPy
`twine upload dist/*`
