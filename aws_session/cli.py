from os import (path, environ)
import re
from argparse import ArgumentParser
from configparser import ConfigParser
from getpass import getpass
from datetime import datetime, timezone, timedelta

from botocore.credentials import JSONFileCache
from botocore.session import Session
from botocore.exceptions import ProfileNotFound
from .configfilewriter import ConfigFileWriter

# ------------------------------------------------------------------------------

AWS_CREDENTIALS_PATH = path.expanduser(
    Session().get_config_variable('credentials_file'))
    
AWS_CACHE_DIR = path.expanduser(
        path.join('~', '.aws', 'cli', 'cache'))
        
SESSION_EXPIRATION_THRESHOLD = timedelta(minutes=5)        
        
DEFAULT_SESSION_DURATION = timedelta(hours=12)

# ------------------------------------------------------------------------------
    
def profile_update(config_path, profile_section, config):
    
    current_config = ConfigParser()
    current_config.read(config_path)
    if current_config.sections() and profile_section not in current_config.sections():
        with open(config_path, 'a') as config_file:
            config_file.write('\n')

    ConfigFileWriter().update_config({
        **config,
        '__section__': profile_section
    }, config_path)


def handle_help(args):
    print("""\
usage: 

    get session credentials:

        aws-session get [--profile/-p <profile_name>]
        
            --profile/-p <profile_name> : select profile ['default']
            --force/-f                  : force new session
        
    list session profiles:

        aws-session list

    print help

        aws-session help
    """)


def handle_list_profiles(args):
    profile_map = Session().full_config['profiles']
    for profile_name, profile in profile_map.items():
        if profile_name.endswith('-session'):
            print(profile_name)


def handle_session_credentials(args):
    force_new = args.force_new
    profile_name = args.profile_name
    profile_properties = Session().full_config['profiles'].get(profile_name)
    if not profile_properties:
        raise ProfileNotFound(profile=profile_name)
    if not args.profile_name.endswith('-session'):
        raise Exception(f"selected profile '{profile_name}' is not a session profile")

    session_source_profile = profile_properties.get('session_source_profile')
    if not session_source_profile:
        raise Exception(f"selected profile '{profile_name}' is missing session_source_profile property")
    
    session_expiration_value = profile_properties.get('session_expiration')
    if session_expiration_value:
        session_expiration = datetime.strptime(session_expiration_value, '%Y-%m-%d %H:%M:%S%z')
    else:
        session_expiration = datetime.now().astimezone()

    session_expiration_duration =  session_expiration  - datetime.now().astimezone()
    if force_new or session_expiration_duration < SESSION_EXPIRATION_THRESHOLD:      
        session_duration_seconds = profile_properties.get('session_duration_seconds') or int(DEFAULT_SESSION_DURATION.total_seconds())
        session_mfa_serial = profile_properties.get('session_mfa_serial')
        
        source_session = Session(profile=session_source_profile)
        source_session_sts_client = source_session.create_client('sts')
        
        if session_mfa_serial:
            session_mfa_code = getpass(prompt=f"Enter MFA code for {session_mfa_serial}: ")
            session = source_session_sts_client.get_session_token(
                DurationSeconds=session_duration_seconds,
                SerialNumber=session_mfa_serial,
                TokenCode=session_mfa_code)
        else:
            session = source_session_sts_client.get_session_token(
                DurationSeconds=session_duration_seconds)
                
        session_access_key_id = session['Credentials']['AccessKeyId']
        session_secret_access_key = session['Credentials']['SecretAccessKey']
        session_token = session['Credentials']['SessionToken']
        session_expiration = session['Credentials']['Expiration']
        session_expiration_duration =  session_expiration  - datetime.now().astimezone()
        
        profile_update(AWS_CREDENTIALS_PATH, profile_name, {
            'aws_access_key_id': session_access_key_id,
            'aws_secret_access_key': session_secret_access_key,
            'aws_session_token': session_token,
            'session_expiration': session_expiration
        })
        
    print(f"Session is valid for {format_timedelta(session_expiration_duration)}, until {session_expiration.astimezone().strftime('%Y-%m-%d %H:%M')}")


def format_timedelta(timedelta):
    total_seconds = int(timedelta.total_seconds())
    total_minutes = total_seconds // 60
    total_hours = total_seconds // 3600
    
    if total_hours:
        return f"{total_hours} hours"
        
    if total_minutes:
        return f"{total_minutes} minutes"
    
    return f"{total_seconds} seconds"


def main():
    parser = ArgumentParser(add_help=False)
    

    parser_command = parser.add_subparsers(title='commands',dest='command')
    parser_command.required = True
    
    parser_command_get = parser_command.add_parser('get', help="Get session credentials")
    parser_command_get.set_defaults(func=handle_session_credentials)
    parser_command_get.add_argument('-p', '--profile', default='default', dest='profile_name', help='Profile name')
    parser_command_get.add_argument('-f', '--force', action='store_true', dest='force_new', help='Force new session')

    parser_command_help = parser_command.add_parser('help', help="Print help")
    parser_command_help.set_defaults(func=handle_help)

    parser_command_list = parser_command.add_parser('list', help="List profiles")
    parser_command_list.set_defaults(func=handle_list_profiles)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
