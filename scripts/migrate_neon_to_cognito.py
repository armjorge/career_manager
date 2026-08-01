#!/usr/bin/env python3
"""Migrate Neon Auth IDs to Cognito subjects.

Examples:
  DB_POSTGRESQL=... AWS_REGION=us-east-1 COGNITO_USER_POOL_ID=... \
    python scripts/migrate_neon_to_cognito.py --create-users
  python scripts/migrate_neon_to_cognito.py --mapping users.csv --apply --drop-fks
  python scripts/migrate_neon_to_cognito.py --mapping users.csv --create-users \
    --set-permanent-password 'ChangeMe123!'
"""

import argparse
import csv
import os
import secrets
import string
import sys
from pathlib import Path

import boto3
import psycopg2
from botocore.exceptions import ClientError
from psycopg2 import sql


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Map Neon Auth users to Cognito subjects and optionally update user_id values."
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        help="CSV with old_id,email columns; required when neon_auth.user is absent.",
    )
    parser.add_argument(
        "--create-users",
        action="store_true",
        help="Create Cognito users missing from the pool (also required in dry runs).",
    )
    parser.add_argument(
        "--set-permanent-password",
        metavar="PASSWORD",
        help="Set this permanent password for Cognito users created by this run.",
    )
    parser.add_argument(
        "--drop-fks",
        action="store_true",
        help="Run SQL/migrate_drop_neon_auth_fks.sql before applying user_id updates.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply database changes. The default is dry-run.",
    )
    return parser.parse_args()


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} must be set.")
    return value


def read_csv_mapping(path: Path) -> list[tuple[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not {"old_id", "email"}.issubset(reader.fieldnames):
            raise ValueError("Mapping CSV must have old_id,email headers.")
        mappings = [(row["old_id"].strip(), row["email"].strip()) for row in reader]
    if any(not old_id or not email for old_id, email in mappings):
        raise ValueError("Mapping CSV cannot contain blank old_id or email values.")
    return mappings


def neon_users(cursor) -> list[tuple[str, str]] | None:
    cursor.execute("SELECT to_regclass('neon_auth.\"user\"')")
    if cursor.fetchone()[0] is None:
        return None
    cursor.execute('SELECT id::text, email FROM neon_auth."user" WHERE email IS NOT NULL')
    return [(old_id, email) for old_id, email in cursor.fetchall()]


def generated_password() -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return (
        secrets.choice(string.ascii_uppercase)
        + secrets.choice(string.ascii_lowercase)
        + secrets.choice(string.digits)
        + secrets.choice("!@#$%^&*")
        + "".join(secrets.choice(alphabet) for _ in range(20))
    )


def cognito_user_by_email(client, pool_id: str, email: str) -> dict | None:
    paginator = client.get_paginator("list_users")
    for page in paginator.paginate(UserPoolId=pool_id, Filter=f'email = "{email}"'):
        users = page.get("Users", [])
        if users:
            return users[0]
    return None


def user_sub(user: dict) -> str:
    for attribute in user.get("Attributes", []):
        if attribute["Name"] == "sub":
            return attribute["Value"]
    raise ValueError(f"Cognito user {user['Username']!r} has no sub attribute.")


def resolve_cognito_user(
    client, pool_id: str, email: str, create_users: bool, permanent_password: str | None
) -> str | None:
    user = cognito_user_by_email(client, pool_id, email)
    if user:
        return user_sub(user)
    if not create_users:
        print(f"Missing Cognito user for {email}; rerun with --create-users.", file=sys.stderr)
        return None

    response = client.admin_create_user(
        UserPoolId=pool_id,
        Username=email,
        UserAttributes=[
            {"Name": "email", "Value": email},
            {"Name": "email_verified", "Value": "true"},
        ],
        MessageAction="SUPPRESS",
        TemporaryPassword=generated_password(),
    )
    username = response["User"]["Username"]
    if permanent_password:
        client.admin_set_user_password(
            UserPoolId=pool_id,
            Username=username,
            Password=permanent_password,
            Permanent=True,
        )
    return user_sub(response["User"])


def drop_neon_auth_foreign_keys(cursor) -> None:
    sql_path = Path(__file__).resolve().parents[1] / "SQL" / "migrate_drop_neon_auth_fks.sql"
    cursor.execute(sql_path.read_text(encoding="utf-8"))


def tables_with_user_id(cursor) -> list[str]:
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'consulting_tracker' AND column_name = 'user_id'
        ORDER BY table_name
        """
    )
    return [row[0] for row in cursor.fetchall()]


def apply_mappings(cursor, mappings: list[tuple[str, str]], tables: list[str]) -> None:
    for table in tables:
        statement = sql.SQL(
            "UPDATE {}.{} SET user_id = %s WHERE user_id::text = %s"
        ).format(sql.Identifier("consulting_tracker"), sql.Identifier(table))
        for old_id, new_sub in mappings:
            cursor.execute(statement, (new_sub, old_id))


def main() -> int:
    args = parse_args()
    try:
        database_url = required_env("DB_POSTGRESQL")
        aws_region = required_env("AWS_REGION")
        user_pool_id = required_env("COGNITO_USER_POOL_ID")
        cognito = boto3.client("cognito-idp", region_name=aws_region)

        with psycopg2.connect(database_url) as connection, connection.cursor() as cursor:
            mappings = neon_users(cursor)
            if mappings is None:
                if not args.mapping:
                    raise ValueError(
                        "neon_auth.user does not exist; provide --mapping old_id,email.csv."
                    )
                mappings = read_csv_mapping(args.mapping)

            resolved = []
            for old_id, email in mappings:
                new_sub = resolve_cognito_user(
                    cognito, user_pool_id, email, args.create_users, args.set_permanent_password
                )
                if new_sub:
                    print(f"{old_id} -> {new_sub} ({email})")
                    resolved.append((old_id, new_sub))

            if not args.apply:
                if args.drop_fks:
                    print("Dry run: would drop Neon Auth foreign keys.")
                print("Dry run: no database changes applied.")
                return 0

            if args.drop_fks:
                drop_neon_auth_foreign_keys(cursor)
            tables = tables_with_user_id(cursor)
            apply_mappings(cursor, resolved, tables)
            print(f"Updated {len(resolved)} user mappings across {len(tables)} tables.")
        return 0
    except (ClientError, OSError, ValueError, psycopg2.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
