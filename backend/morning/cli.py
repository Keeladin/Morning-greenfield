from __future__ import annotations

import argparse
import getpass

from .accounts import AccountError, MorningAccounts
from .config import ConfigError, Settings
from .store import MorningStore


def _bootstrap_admin(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    if settings.database_url is None:
        raise ConfigError("MORNING_DATABASE_URL is required to bootstrap an admin")
    password = getpass.getpass("Admin password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise AccountError("password confirmation does not match")
    accounts = MorningAccounts(MorningStore(settings.database_url))
    principal = accounts.create_admin(
        username=args.username,
        password=password,
        display_name=args.display_name,
    )
    print(f"Created Morning admin {principal.display_name} ({principal.principal_id})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="morning")
    commands = parser.add_subparsers(dest="command", required=True)
    bootstrap = commands.add_parser("bootstrap-admin", help="create an approved Morning admin account")
    bootstrap.add_argument("--username", required=True)
    bootstrap.add_argument("--display-name", required=True)
    bootstrap.set_defaults(handler=_bootstrap_admin)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except (AccountError, ConfigError) as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
