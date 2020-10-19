import os
import re
from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import datetime, timedelta
from getpass import getpass
from os import path

from botocore.credentials import RefreshableCredentials
from botocore.session import Session

# --- CONFIGURATION ------------------------------------------------------------

SESSION_PROFILE_SUFFIX = "--session"
SESSION_EXPIRATION_THRESHOLD = timedelta(minutes=5)

DEFAULT_SESSION_TOKEN_DURATION_SECONDS = 43200  # 12 hours
AWS_CREDENTIALS_PATH = path.expanduser(Session().get_config_variable("credentials_file"))


# ------------------------------------------------------------------------------


def handle_help(args):
    print(
        """\
usage:

    get session credentials:

        aws-session get [--profile/-p <profile_name>]

            --profile/-p <profile_name> : select profile ['default']
            --force/-f                  : force new session

        To create MFA user sessions just add `mfa_serial` to profile config in ~/.aws/config profiles

    list session profiles:

        aws-session list

    purge expired session profiles:

        aws-session purge

            --force/-f                  : purge all session profiles regardles of expiration

    print help

        aws-session help
    """
    )


def handle_get_session_credentials(args):
    force_new = args.force_new
    # ensure source profile name if session profile name is passed
    profile_name = re.sub(f"{re.escape(SESSION_PROFILE_SUFFIX)}$", "", args.profile_name)

    session_profile_name = f"{profile_name}{SESSION_PROFILE_SUFFIX}"
    session_profile_config = get_profile(session_profile_name) or {}

    session_expiry_time = datetime.now().astimezone()
    session_expiry_time_value = session_profile_config.get("aws_session_expiry_time")
    if session_expiry_time_value:
        session_expiry_time = datetime.strptime(session_expiry_time_value, "%Y-%m-%d %H:%M:%S").astimezone()

    session_expiry_duration = session_expiry_time - datetime.now().astimezone()
    if session_expiry_duration < SESSION_EXPIRATION_THRESHOLD or force_new:
        session_credentials = get_session_credentials(profile_name)
        session_profile_credentials = {
            "aws_access_key_id": session_credentials.access_key,
            "aws_secret_access_key": session_credentials.secret_key,
            "aws_session_token": session_credentials.token,
            "aws_session_expiry_time": session_credentials.expiry_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        source_profile_config = get_profile(profile_name)
        # purge credential and session configuration from source profile
        for config_variable in [
            "credential_source",
            "source_profile",
            "mfa_serial",
            "session_mfa_serial",
            "role_arn",
            "role_session_name",
            "external_id",
            "web_identity_token_file",
            "credential_process",
            "duration_seconds",
            "session_duration_seconds",
        ]:
            if config_variable in source_profile_config:
                del source_profile_config[config_variable]

        session_profile_config = {
            **session_profile_credentials,  # place credentials at top of credential profile
            **source_profile_config,  # add source profile config
            **session_profile_credentials,  # ensure old credentials are replaced by new ones
        }

        replace_session_profile(AWS_CREDENTIALS_PATH, session_profile_name, session_profile_config)
        session_expiry_time = session_credentials.expiry_time
        session_expiry_duration = session_expiry_time - datetime.now().astimezone()

    print(f"Session profile: {session_profile_name}")
    print(
        f"Expires in {format_timedelta(session_expiry_duration)}, "
        f"at {session_expiry_time.astimezone().strftime('%Y-%m-%d %H:%M')}"
    )


def handle_list_profiles(args):
    for profile_name in sorted(get_profiles().keys()):
        print(profile_name)


def handle_purge_session_credentials(args):
    force_delete = args.force_delete

    for profile_name, profile_config in get_profiles().items():
        if profile_name.endswith(SESSION_PROFILE_SUFFIX):
            session_expiry_time = datetime.now().astimezone()
            session_expiry_time_value = profile_config.get("aws_session_expiry_time")
            if session_expiry_time_value:
                session_expiry_time = datetime.strptime(session_expiry_time_value, "%Y-%m-%d %H:%M:%S").astimezone()

            session_expiry_duration = session_expiry_time - datetime.now().astimezone()
            if session_expiry_duration < SESSION_EXPIRATION_THRESHOLD or force_delete:
                print(f"Delete session profile: {profile_name}")
                delete_session_profile(AWS_CREDENTIALS_PATH, profile_name)


def get_session_credentials(profile_name):
    profile_session = Session(profile=profile_name)
    profile_session_credentials = profile_session.get_credentials()
    if isinstance(profile_session_credentials, RefreshableCredentials):
        # populate deferred credentials
        profile_session_credentials.get_frozen_credentials()
        return SessionCredentials(
            access_key=profile_session_credentials.access_key,
            secret_key=profile_session_credentials.secret_key,
            token=profile_session_credentials.token,
            expiry_time=profile_session_credentials._expiry_time.astimezone(),
        )
    else:
        session_credentials = get_session_token(profile_session)["Credentials"]
        return SessionCredentials(
            access_key=session_credentials["AccessKeyId"],
            secret_key=session_credentials["SecretAccessKey"],
            token=session_credentials["SessionToken"],
            expiry_time=session_credentials["Expiration"].astimezone(),
        )


def get_session_token(profile_session):
    profile = get_profile(profile_session.profile)

    session_duration_seconds = (
            profile.get("duration_seconds")
            or profile.get("session_duration_seconds")
            or DEFAULT_SESSION_TOKEN_DURATION_SECONDS
    )

    session_mfa_serial = (
            profile.get("mfa_serial")
            or profile.get("session_mfa_serial")
    )

    sts_client = profile_session.create_client("sts")
    if session_mfa_serial:
        return sts_client.get_session_token(
            DurationSeconds=session_duration_seconds,
            SerialNumber=session_mfa_serial,
            TokenCode=getpass(prompt=f"Enter MFA code for {session_mfa_serial}: "),
        )
    else:
        return sts_client.get_session_token(DurationSeconds=session_duration_seconds)


class SessionCredentials:
    def __init__(self, access_key, secret_key, token, expiry_time):
        self.access_key = access_key
        self.secret_key = secret_key
        self.token = token
        self.expiry_time = expiry_time


def format_timedelta(delta):
    total_seconds = int(delta.total_seconds())
    total_minutes = total_seconds // 60
    total_hours = total_seconds // 3600

    if total_hours:
        return f"{total_hours} hours"

    if total_minutes:
        return f"{total_minutes} minutes"

    return f"{total_seconds} seconds"


def get_profiles():
    return Session().full_config["profiles"]


def get_profile(profile_name):
    return Session().full_config["profiles"].get(profile_name)


def delete_session_profile(config_path, profile_name):
    profile_section = f"[{profile_name}]"

    with open(config_path, "r+") as config_file:
        lines = config_file.readlines()
        config_file.seek(0)

        profile_section_regex = re.compile(f"^{re.escape(profile_section)}")

        keep = True
        for line in lines:
            if keep:
                if profile_section_regex.match(line):  # profile section start
                    keep = False
            elif line.startswith("["):  # new section start
                keep = True

            if keep:
                config_file.write(line)

        config_file.truncate()


def add_session_profile(config_path, profile_name, config):
    profile_section = f"[{profile_name}]"
    current_config = ConfigParser()
    current_config.read(config_path)

    # ensure empty line before appending new profile section
    with open(config_path, "rb+") as config_file:
        config_file.seek(0, os.SEEK_END)
        char_count = config_file.tell()
        if char_count == 0:
            pass
        elif char_count == 1:
            config_file.seek(-1, os.SEEK_END)
            if config_file.read(1).decode() != "\n":
                config_file.write("\n\n".encode())
        else:
            config_file.seek(-2, os.SEEK_END)
            if config_file.read(2).decode() != "\n\n":
                config_file.write("\n".encode())
                config_file.seek(-2, os.SEEK_END)
                if config_file.read(2).decode() != "\n\n":
                    config_file.write("\n".encode())

    # append new profile section
    with open(config_path, "a") as config_file:
        config_file.write(f"{profile_section}\n")
        for key, value in config.items():
            config_file.write(f"{key} = {value}\n")


def replace_session_profile(config_path, profile_name, config):
    delete_session_profile(config_path, profile_name)
    add_session_profile(config_path, profile_name, config)


def main():
    parser = ArgumentParser(add_help=False)

    parser_command = parser.add_subparsers(title="commands", dest="command")
    parser_command.required = True

    parser_command_help = parser_command.add_parser("help", help="Print help")
    parser_command_help.set_defaults(func=handle_help)

    parser_command_get = parser_command.add_parser("get", help="Get session credentials")
    parser_command_get.set_defaults(func=handle_get_session_credentials)
    parser_command_get.add_argument(
        "-p", "--profile", dest="profile_name", default="default",
        help="Profile name"
    )
    parser_command_get.add_argument(
        "-f", "--force", dest="force_new", action="store_true",
        help="Force new session"
    )

    parser_command_get = parser_command.add_parser("purge", help="Purge expired session profiles")
    parser_command_get.set_defaults(func=handle_purge_session_credentials)
    parser_command_get.add_argument(
        "-f", "--force", dest="force_delete", action="store_true",
        help="Force delete all session profiles"
    )

    parser_command_list = parser_command.add_parser("list", help="List profiles")
    parser_command_list.set_defaults(func=handle_list_profiles)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
