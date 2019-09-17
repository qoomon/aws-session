from os import ( path, environ )
import sys
from botocore.credentials import JSONFileCache
from botocore.session import Session
from botocore.exceptions import NoCredentialsError, ProfileNotFound
from awscli.customizations.configure.writer import ConfigFileWriter

def argv_get(index):
    return sys.argv[index] if index < len(sys.argv) else None

def printHelp():
    print("""\
usage: 

    refresh session credentials:

        aws-session <profile_name>
        
    list session profiles:

        aws-session --list/-l

""" )

def refreshSessionCredentials(profile_name):
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
    
    # add empty line as profile separator
    current_credentials = ConfigParser()
    current_credentials.read(credentials_path)
    if current_credentials.sections() and config_section not in current_credentials.sections():
        with open(credentials_path, 'a') as credentials_file:
            credentials_file.write('\n')
                
    ConfigFileWriter().update_config({
        '__section__': session.profile,
        'aws_access_key_id': session_credentials.access_key,
        'aws_secret_access_key': session_credentials.secret_key,
        'aws_session_token': session_credentials.token
    }, credentials_path)

def printSessionProfiles():
    profile_map = Session().full_config['profiles']
    for profile_name, profile in profile_map.items():
        if profile.get('role_arn'):
            print(profile_name)

def main():
    if argv_get(1) in ('--help', '-h')  :
        printHelp()
    elif argv_get(1) in ('--list', '-l') :
        printSessionProfiles()
    else:
        profile_name = argv_get(1) \
            or environ.get('AWS_PROFILE') \
            or environ.get('AWS_DEFAULT_PROFILE') \
            or 'default'
        refreshSessionCredentials(profile_name)
  
if __name__== "__main__":
  main()