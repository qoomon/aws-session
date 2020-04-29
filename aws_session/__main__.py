from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import datetime, timedelta
from os import path

from botocore.credentials import RefreshableCredentials
from botocore.exceptions import ProfileNotFound
from botocore.session import Session

from .configfilewriter import ConfigFileWriter

# --- CONFIGURATION ------------------------------------------------------------

SESSION_EXPIRATION_THRESHOLD = timedelta(minutes=5)
AWS_CREDENTIALS_PATH = path.expanduser(Session().get_config_variable("credentials_file"))


# ------------------------------------------------------------------------------

def profile_update(config_path, profile_section, config):
    current_config = ConfigParser()
    current_config.read(config_path)
    if current_config.sections() and profile_section not in current_config.sections():
        with open(config_path, "a") as config_file:
            config_file.write("\n")

    ConfigFileWriter().update_config({
        **config,
        "__section__": profile_section
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
    profile_map = Session().full_config["profiles"]
    # TODO
    for profile_name, profile in profile_map.items():
        if not profile_name.endswith("-session"):
            print(profile_name)


def handle_session_credentials(args):
    force_new = args.force_new
    profile_name = args.profile_name
    profile_config = Session().full_config["profiles"].get(profile_name)
    if not profile_config:
        raise ProfileNotFound(profile=profile_name)
    if profile_config.get("aws_access_key_id") and profile_config.get("aws_secret_access_key") \
            and not profile_config.get("aws_session_token"):
        raise Exception(f"The config profile ({profile_name}) is a user profile")

    expiry_time = datetime.now().astimezone()
    expiry_time_value = profile_config.get("aws_session_expiry_time")
    if expiry_time_value and not expiry_time_value == "None":
        expiry_time = datetime.strptime(expiry_time_value, "%Y-%m-%d %H:%M:%S%z")

    expiry_duration = expiry_time - datetime.now().astimezone()
    if expiry_duration < SESSION_EXPIRATION_THRESHOLD or force_new:
        session = Session(profile=profile_name)
        session_credentials = session.get_credentials()
        if not isinstance(session_credentials, RefreshableCredentials):
            raise Exception(f"Invalid Credentials Type: {type(session_credentials)}")
        # populate deferred credentials
        session_credentials.get_frozen_credentials()

        profile_update(AWS_CREDENTIALS_PATH, profile_name, {
            "aws_access_key_id": session_credentials.access_key,
            "aws_secret_access_key": session_credentials.secret_key,
            "aws_session_token": session_credentials.token,
            "aws_session_expiry_time": session_credentials._expiry_time
        })

        expiry_time = session_credentials._expiry_time
        expiry_duration = expiry_time - datetime.now().astimezone()

    print(f"Session is valid for {format_timedelta(expiry_duration)}, "
          f"until {expiry_time.astimezone().strftime('%Y-%m-%d %H:%M')}")


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

    parser_command = parser.add_subparsers(title="commands", dest="command")
    parser_command.required = True

    parser_command_get = parser_command.add_parser("get", help="Get session credentials")
    parser_command_get.set_defaults(func=handle_session_credentials)
    parser_command_get.add_argument("-p", "--profile", default="default", dest="profile_name", help="Profile name")
    parser_command_get.add_argument("-f", "--force", action="store_true", dest="force_new", help="Force new session")

    parser_command_help = parser_command.add_parser("help", help="Print help")
    parser_command_help.set_defaults(func=handle_help)

    parser_command_list = parser_command.add_parser("list", help="List profiles")
    parser_command_list.set_defaults(func=handle_list_profiles)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
