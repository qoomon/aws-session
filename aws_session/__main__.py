from argparse import ArgumentParser
from getpass import getpass
from configparser import ConfigParser
from datetime import datetime, timedelta
from os import path
import re

from botocore.credentials import Credentials, RefreshableCredentials
from botocore.exceptions import ProfileNotFound
from botocore.session import Session

from .configfilewriter import ConfigFileWriter

# --- CONFIGURATION ------------------------------------------------------------

SESSION_EXPIRATION_THRESHOLD = timedelta(minutes=5)

DEFAULT_SESSION_TOKEN_DURATION_SECONDS = 43200  # 12 hours
AWS_CREDENTIALS_PATH = path.expanduser(Session().get_config_variable("credentials_file"))

# ------------------------------------------------------------------------------


def handle_help(args):
    print("""\
usage: 

    get session credentials:

        aws-session get [--profile/-p <profile_name>]
        
            --profile/-p <profile_name> : select profile ['default']
            --force/-f                  : force new session
            
        To create MFA user sessions just add `session_mfa_serial` to profile config in ~/.aws/config profiles
        
        [profile john]
        session_mfa_serial = arn:aws:iam::0123456789:mfa/john
        
    list session profiles:

        aws-session list

    print help

        aws-session help
    """)


def handle_list_profiles(args):
    profile_map = Session().full_config["profiles"]
    for profile_name, profile in profile_map.items():
        if not profile_name.endswith("-session"):
            print(profile_name)


def handle_get_session_credentials(args):
    force_new = args.force_new
    profile_name = re.sub('-session$', '', args.profile_name)
    profile_config = Session().full_config["profiles"].get(profile_name)
    if not profile_config:
        raise ProfileNotFound(profile=profile_name)

    session_profile_name = f"{profile_name}-session"
    session_profile_config = Session().full_config["profiles"].get(session_profile_name) or {}

    session_expiry_time = datetime.now().astimezone()
    session_expiry_time_value = session_profile_config.get("aws_session_expiry_time")
    if session_expiry_time_value and not session_expiry_time_value == "None":
        session_expiry_time = datetime.strptime(session_expiry_time_value, "%Y-%m-%d %H:%M:%S").astimezone()

    session_expiry_duration = session_expiry_time - datetime.now().astimezone()
    if session_expiry_duration < SESSION_EXPIRATION_THRESHOLD or force_new:
        session_credentials = get_session_credentials(profile_name=profile_name, profile_config=profile_config)
        session_profile_credentials = {
            "aws_access_key_id": session_credentials.access_key,
            "aws_secret_access_key" :session_credentials.secret_key,
            "aws_session_token": session_credentials.token,
            "aws_session_expiry_time": session_credentials.expiry_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        profile_update(AWS_CREDENTIALS_PATH, session_profile_name, {
                **session_profile_credentials, # place credentials at top of credential profile
                **profile_config,
                **session_profile_credentials  # ensure old credentials are replaced by new ones
        })
        session_expiry_time = session_credentials.expiry_time
        session_expiry_duration = session_expiry_time - datetime.now().astimezone()

    print(f"Session profile: {session_profile_name}")
    print(f"Expires in {format_timedelta(session_expiry_duration)}, "
          f"at {session_expiry_time.astimezone().strftime('%Y-%m-%d %H:%M')}")


def get_session_credentials(profile_name, profile_config):
    profile_session = Session(profile=profile_name)
    profile_session_credentials = profile_session.get_credentials()
    if isinstance(profile_session_credentials, RefreshableCredentials):
        print(f"Role session")
        # populate deferred credentials
        profile_session_credentials.get_frozen_credentials()
        return SessionCredentials(
            access_key=profile_session_credentials.access_key,
            secret_key=profile_session_credentials.secret_key,
            token=profile_session_credentials.token,
            expiry_time=profile_session_credentials._expiry_time.astimezone())
    else:
        print(f"User session")
        session_duration_seconds = profile_config.get('session_duration_seconds') or DEFAULT_SESSION_TOKEN_DURATION_SECONDS
        session_mfa_serial = profile_config.get('session_mfa_serial')
        session_credentials = get_session_token(profile_session,
            DurationSeconds=session_duration_seconds,
            SerialNumber=session_mfa_serial)['Credentials']
        return SessionCredentials(
            access_key=session_credentials['AccessKeyId'],
            secret_key=session_credentials['SecretAccessKey'],
            token=session_credentials['SessionToken'],
            expiry_time=session_credentials['Expiration'].astimezone())


def get_session_token(session, DurationSeconds, SerialNumber):
    sts_client = session.create_client('sts')
    if SerialNumber:
        return sts_client.get_session_token(
            DurationSeconds=DurationSeconds or DEFAULT_SESSION_TOKEN_DURATION_SECONDS,
            SerialNumber=SerialNumber,
            TokenCode=getpass(prompt=f"Enter MFA code for {SerialNumber}: "))
    else:
        return sts_client.get_session_token(
            DurationSeconds=DurationSeconds or DEFAULT_SESSION_TOKEN_DURATION_SECONDS)


class SessionCredentials:
    def __init__(self, access_key, secret_key, token, expiry_time):
        self.access_key = access_key
        self.secret_key = secret_key
        self.token = token
        self.expiry_time = expiry_time


def format_timedelta(timedelta):
    total_seconds = int(timedelta.total_seconds())
    total_minutes = total_seconds // 60
    total_hours = total_seconds // 3600

    if total_hours:
        return f"{total_hours} hours"

    if total_minutes:
        return f"{total_minutes} minutes"

    return f"{total_seconds} seconds"


def profile_update(config_path, profile_section, config):
    current_config = ConfigParser()
    current_config.read(config_path)
    if current_config.sections() and profile_section not in current_config.sections():
        with open(config_path, "a") as config_file:
            config_file.write("\n")

    ConfigFileWriter().update_config(config_filename=config_path, new_values={
        **config,
        "__section__": profile_section
    })


def main():
    parser = ArgumentParser(add_help=False)

    parser_command = parser.add_subparsers(title="commands", dest="command")
    parser_command.required = True

    parser_command_get = parser_command.add_parser("get", help="Get session credentials")
    parser_command_get.set_defaults(func=handle_get_session_credentials)
    parser_command_get.add_argument("-p", "--profile", dest="profile_name", default="default", help="Profile name")
    parser_command_get.add_argument("-f", "--force", dest="force_new", action="store_true", help="Force new session")

    parser_command_help = parser_command.add_parser("help", help="Print help")
    parser_command_help.set_defaults(func=handle_help)

    parser_command_list = parser_command.add_parser("list", help="List profiles")
    parser_command_list.set_defaults(func=handle_list_profiles)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
