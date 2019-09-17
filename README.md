# aws-session

![PyPI](https://img.shields.io/pypi/v/aws-session)

A CLI to generate and store session credentials in `~/.aws/credentials` file, based on `~/.aws/config profiles

## Usage

* list all session profiles `aws-session list`
* refresh session credentials for specific profile
  * by cli parameter `aws-session refresh <PROFILE_NAME>`
  * by environment variable `export AWS_PROFILE=<PROFILE_NAME>; aws-session refresh`


## Setup dev environment

#### Install Dev Dependencies
`pip3 install -r requirements.txt`
`pip3 install -r requirements-dev.txt`

#### Create Package
`python3 setup.py sdist bdist_wheel`

#### Local Install
`pip3 install --force-reinstall --no-deps dist/aws_session-*-py3-none-any.whl`

#### Deploy to PiPy
`twine upload dist/*`
