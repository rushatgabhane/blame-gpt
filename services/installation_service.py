import logging
from libs.sqlite.sqlite_client import Database


def add_installation(body, db: Database):
    installation = body.get("installation")
    installation_id = installation.get("id")
    account_login = installation.get("account", {}).get("login")
    account_type = installation.get("account", {}).get("type")

    db.add_installation(
        installation_id=installation_id,
        account_login=account_login,
        account_type=account_type,
    )
    logging.info(
        f"Added installation {installation_id} for account {account_login} of type {account_type}"
    )
