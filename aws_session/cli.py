from os import ( path, environ )
import sys
from botocore.credentials import JSONFileCache
from botocore.session import Session
from botocore.exceptions import NoCredentialsError, ProfileNotFound
from awscli.customizations.configure.writer import ConfigFileWriter

def argv_get(index):
    return sys.argv[index] if index < len(sys.argv) else None

def main():
    profile_map = Session().full_config['profiles']

    if argv_get(1) == '-l':
        ########## List Command ####################################################
        for profile_name, profile in profile_map.items():
            if profile.get('role_arn'):
                print(profile_name)
    else:
        ########## Main Command ####################################################
        profile_name = argv_get(1) \
            or environ.get('AWS_PROFILE') \
            or environ.get('AWS_DEFAULT_PROFILE') \
            or 'default'

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
        credentials_filename = path.expanduser(
            session.get_config_variable('credentials_file'))
        ConfigFileWriter().update_config({
            '__section__': 'test-' + session.profile,
            'aws_access_key_id': session_credentials.access_key,
            'aws_secret_access_key': session_credentials.secret_key,
            'aws_session_token': session_credentials.token
        }, credentials_filename)
  
if __name__== "__main__":
  main()