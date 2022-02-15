# see https://github.com/ArekSredzki/electron-release-server/blob/master/docs/urls.md
# see https://github.com/ArekSredzki/electron-release-server/blob/master/docs/api.md
# see https://github.com/ArekSredzki/electron-release-server/issues/79#issuecomment-263068900

import argparse
import os
import textwrap

import requests
import yaml


def login(base_url, ca_file, username, password):
    response = requests.post(
        base_url + "/api/auth/login", verify=ca_file, json={"username": username, "password": password}
    )
    response.raise_for_status()
    return response.json()["token"]


def parse_version(path):
    if os.path.isfile(path):
        path = os.path.dirname(path)

    for yml_file in os.listdir(path):
        if "latest.yml" in yml_file:
            yml_file = os.path.join(path, yml_file)
            with open(yml_file) as file:
                yml_data = yaml.safe_load(file)
                return yml_data["version"]


def create_version_if_needed(base_url, ca_file, token, channel, version, notes=""):
    response = requests.get(
        base_url + "/api/version/%s" % version, verify=ca_file, headers={"Authorization": "Bearer %s" % token}
    )
    if response.status_code == 200:
        return
    response = requests.post(
        base_url + "/api/version",
        verify=ca_file,
        headers={"Authorization": "Bearer %s" % token},
        json={"name": version, "notes": notes, "channel": {"name": channel}},
    )
    response.raise_for_status()


def create_asset(base_url, ca_file, token, version, platform, path):
    if os.path.isdir(path):
        for file in os.listdir(path):
            if file.endswith(".exe"):
                path = os.path.join(path, file)
                break
        else:
            raise SystemExit("No executable was found for upload")

    response = requests.post(
        base_url + "/api/asset",
        verify=ca_file,
        headers={"Authorization": "Bearer %s" % token},
        data={
            "version": version,
            "platform": platform,
        },
        files={"file": open(path, "rb")},
    )
    response.raise_for_status()


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="Publishes an asset to the electron-release-server.",
    epilog=textwrap.dedent(
        """
        example:
          export ERS_USERNAME=vagrant
          export ERS_PASSWORD=vagrant
          %(prog)s stable 1.0.0 windows_64 hello-world-electron/dist/*1.0.0.exe
        """
    ),
)
parser.add_argument("--channel", choices=["stable", "rc", "beta", "alpha"])
parser.add_argument("--version", default="")
parser.add_argument("--platform", choices=["windows_64", "windows_32", "osx_64", "linux_64", "linux_32"])
parser.add_argument("--path")
parser.add_argument("--notes")
parser.add_argument("--base-url", default="https://127.0.0.1")
parser.add_argument("--username", default=os.environ.get("ERS_USERNAME"))
parser.add_argument("--password", default=os.environ.get("ERS_PASSWORD"))
parser.add_argument("--ca-file", default="")
args = parser.parse_args()

if args.version:
    version = args.version
else:
    version = parse_version(args.path)

if not version:
    raise SystemExit("No version is specified")

token = login(args.base_url, args.ca_file, args.username, args.password)
create_version_if_needed(args.base_url, args.ca_file, token, args.channel, version, notes=args.notes)
create_asset(args.base_url, args.ca_file, token, version, args.platform, args.path)
