# aws-session

A CLI to generate and store session credentials in ~/.aws/credentials file, based on ~/.aws/config profiles

## Usage

* list all session profiles `aws-session -l`
* refresh session credentials for specific profile
  * by cli parameter `aws-session <PROFILE_NAME>`
  * by environment variable `export AWS_PROFILE=<PROFILE_NAME>; aws-session`


## Setup dev environment

#### Create Package
`python3 setup.py sdist bdist_wheel`

#### Local Install
`pip3 install --force-reinstall --no-deps dist/python_sandbox-0.1.0-py3-none-any.whl`

#### Deploy to PiPy
`twine upload dist/*`
