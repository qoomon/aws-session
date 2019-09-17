from os import (path, environ)
import sys
from configparser import ConfigParser

from botocore.credentials import JSONFileCache
from botocore.session import Session
from botocore.exceptions import NoCredentialsError, ProfileNotFound
from awscli.customizations.configure.writer import ConfigFileWriter


def argv_get(index):
    return sys.argv[index] if index < len(sys.argv) else None


def print_help():
    print("""\
usage: 

    refresh session credentials:

        aws-session refresh <profile_name>
        
    list session profiles:

        aws-session list
    
    print help
    
        aws-session help

""")


def refresh_session_credentials(profile_name):
    profile_map = Session().full_config['profiles']
    # ensure profile exists
    if profile_name not in profile_map:
        raise ProfileNotFound(profile=profile_name)

    # ensure profile is session profile
    if 'role_arn' not in profile_map.get(profile_name):
        raise Exception(f'[{profile_name}] - is not a session profile')

    session = Session(profile=profile_name)

    # setup credentials cache - use aws cli credentials cache
    credentials_cache_dir = path.expanduser(
        path.join('~', '.aws', 'cli', 'cache'))
    credentials_cache = JSONFileCache(credentials_cache_dir)
    session.get_component('credential_provider') \
        .get_provider('assume-role').cache = credentials_cache

    # get session credentials
    session_credentials = session.get_credentials()
    if not session_credentials:
        raise NoCredentialsError()
    session_credentials = session_credentials.get_frozen_credentials()

    # write session credentials to credentials file
    print(f'[{session.profile}] - set session credentials')
    credentials_path = path.expanduser(
        session.get_config_variable('credentials_file'))

    config_section=session.profile
    
    # add empty line as profile separator
    current_credentials = ConfigParser()
    current_credentials.read(credentials_path)
    if current_credentials.sections() and config_section not in current_credentials.sections():
        with open(credentials_path, 'a') as credentials_file:
            credentials_file.write('\n')

    ConfigFileWriter().update_config({
        '__section__': config_section,
        'aws_access_key_id': session_credentials.access_key,
        'aws_secret_access_key': session_credentials.secret_key,
        'aws_session_token': session_credentials.token
    }, credentials_path)


def list_session_profiles():
    profile_map = Session().full_config['profiles']
    for profile_name, profile in profile_map.items():
        if profile.get('role_arn'):
            print(profile_name)


def main():
    if argv_get(1) == 'help':
        print_help()
    elif argv_get(1) == 'list':
        list_session_profiles()
    elif argv_get(1) == 'refresh':
        profile_name = argv_get(2) \
            or environ.get('AWS_PROFILE') \
            or environ.get('AWS_DEFAULT_PROFILE') \
            or 'default'
        refresh_session_credentials(profile_name)
    else:
        printHelp()
        exit(1)

if __name__ == "__main__":
    main()
