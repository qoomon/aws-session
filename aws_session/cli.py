from os import (path, environ)
import sys
from configparser import ConfigParser

from botocore.credentials import JSONFileCache
from botocore.session import Session
from botocore.exceptions import NoCredentialsError, ProfileNotFound
from awscli.customizations.configure.writer import ConfigFileWriter

aws_credentials_path = path.expanduser(
    Session().get_config_variable('credentials_file'))
    
aws_cache_dir = path.expanduser(
        path.join('~', '.aws', 'cli', 'cache'))

def argv_get(index):
    return sys.argv[index] if index < len(sys.argv) else None
    
def profile_update(config_path, profile_section, config):

    # add empty line as profile separator
    current_config = ConfigParser()
    current_config.read(config_path)
    if current_config.sections() and profile_section not in current_config.sections():
        with open(config_path, 'a') as config_file:
            config_file.write('\n')

    ConfigFileWriter().update_config({
        **config,
        '__section__': profile_section
    }, config_path)


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
        raise Exception('not a session profile')

    session = Session(profile=profile_name)

    # setup credentials cache - use aws cli credentials cache
    session.get_component('credential_provider'.get_provider('assume-role')\
        .cache = JSONFileCache(aws_cache_dir)

    # get session credentials
    session_credentials = session.get_credentials()
    if not session_credentials:
        raise NoCredentialsError()
    session_credentials = session_credentials.get_frozen_credentials()

    # write session credentials to credentials file
    print('set session credentials')
    profile_update(aws_credentials_path, session.profile, {
        'aws_access_key_id': session_credentials.access_key,
        'aws_secret_access_key': session_credentials.secret_key,
        'aws_session_token': session_credentials.token
    })


def handle_list_session_profiles():
    profile_map = Session().full_config['profiles']
    for profile_name, profile in profile_map.items():
        if profile.get('role_arn'):
            print(profile_name)


def handle_refresh_profile_credentials():
    profile_name = argv_get(2) \
        or environ.get('AWS_PROFILE') \
        or environ.get('AWS_DEFAULT_PROFILE') \
        or 'default'
    refresh_session_credentials(profile_name)


def main():
    if argv_get(1) == 'help':
        print_help()
    elif argv_get(1) == 'list':
        handle_list_session_profiles()
    elif argv_get(1) == 'refresh':
        handle_refresh_profile_credentials()
    else:
        printHelp()
        exit(1)


if __name__ == "__main__":
    main()
