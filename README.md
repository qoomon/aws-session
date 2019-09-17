# aws-session

A CLI to generate and store session credentials in ~/.aws/credentials file, based on ~/.aws/config profiles


# Setup dev environment

#### Create Package
`python3 setup.py sdist bdist_wheel`

#### Local Install
`pip3 install --force-reinstall --no-deps dist/python_sandbox-0.1.0-py3-none-any.whl`

#### Deploy to PiPy
`twine upload dist/*`