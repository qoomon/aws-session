from os import (path, environ)
import sys
from argparse import ArgumentParser
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

    set session credentials:

        aws-session set [--profile/-p <profile_name>]
        
            --profile/-p <profile_name> : select profile ['default']
        
    list session profiles:

        aws-session list

    print help

        aws-session help

""")

def handle_help(args):
    print_help()


def handle_list_session_profiles(args):
    profile_map = Session().full_config['profiles']
    for profile_name, profile in profile_map.items():
        if profile.get('role_arn'):
            print(profile_name)


def handle_get_session_credentials(args):
    profile_name = args.profile_name or 'default'
    
    profile_map = Session().full_config['profiles']
    # ensure profile exists
    if profile_name not in profile_map:
        raise ProfileNotFound(profile=profile_name)

    # ensure profile is session profile
    if 'role_arn' not in profile_map.get(profile_name):
        raise Exception('not a session profile')

    session = Session(profile=profile_name)

    # setup credentials cache - use aws cli credentials cache
    session.get_component('credential_provider').get_provider('assume-role')\
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


def main():
    parser = ArgumentParser(add_help=False)

    parser_command = parser.add_subparsers(title='commands',dest='command',required=True)

    parser_command_help = parser_command.add_parser('help', help="Print help")
    parser_command_help.set_defaults(func=handle_help)

    parser_command_list = parser_command.add_parser('list', help="List session profiles")
    parser_command_list.set_defaults(func=handle_list_session_profiles)

    parser_command_set = parser_command.add_parser('set', help="Set session credentials")
    parser_command_set.add_argument('-p', '--profile', dest='profile_name', help='Profile name')
    parser_command_set.add_argument('--force', action='store_true', dest='force_refresh', help='Force session credentials refresh')
    parser_command_set.set_defaults(func=handle_get_session_credentials)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
