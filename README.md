# aws-session

[![PyPI](https://img.shields.io/pypi/v/aws-session)](https://pypi.org/project/aws-session/)

A CLI to generate and store session credentials in `~/.aws/credentials` file, based on `~/.aws/config profiles`

## Usage
```
usage: 

    get session credentials:

        aws-session get [--profile/-p <profile_name>]
        
            --profile/-p <profile_name> : select profile ['default']
            --force/-f                  : force new session
        
    list session profiles:

        aws-session list

    print help

        aws-session help
```

## Setup dev environment

#### Install Dev Dependencies
`pip3 install --user -r requirements.txt`

`pip3 install --user -r requirements-dev.txt`

#### Create Package
`python3 setup.py sdist bdist_wheel`

#### Local Install
`pip3 install --force-reinstall --no-deps dist/aws_session-*-py3-none-any.whl`

#### Deploy to PiPy
`twine upload dist/*`
