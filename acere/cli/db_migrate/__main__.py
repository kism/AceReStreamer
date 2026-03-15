"""CLI for database migrations."""

import argparse
import sys
from typing import TYPE_CHECKING

from sqlmodel import create_engine

from acere.constants import DEFAULT_INSTANCE_PATH
from acere.database.migration import runner
from acere.instances.paths import get_app_path_handler, setup_app_path_handler
from acere.utils.cli import console
from acere.version import PROGRAM_NAME, __version__

if TYPE_CHECKING:
    from alembic.script import Script
else:
    Script = object


def _setup_engine():
    setup_app_path_handler(DEFAULT_INSTANCE_PATH)
    path_handler = get_app_path_handler()
    if not path_handler.database_file.exists():
        console.print(f"[red]Database not found:[/red] {path_handler.database_file}")
        sys.exit(1)
    return create_engine(f"sqlite:///{path_handler.database_file}", echo=False)


def _get_all_revisions() -> list[Script]:
    from alembic.config import Config  # noqa: PLC0415
    from alembic.script import ScriptDirectory  # noqa: PLC0415

    cfg = Config()
    cfg.set_main_option("script_location", str(runner._MIGRATION_DIR))  # noqa: SLF001
    return list(ScriptDirectory.from_config(cfg).walk_revisions())


def cmd_current(args: argparse.Namespace) -> None:  # noqa: ARG001
    engine = _setup_engine()
    current = runner.get_current_revision(engine)
    engine.dispose()

    all_revisions = _get_all_revisions()
    head = all_revisions[0].revision if all_revisions else None

    if current is None:
        console.print("Current revision: [yellow]None[/yellow] (no migrations applied)")
    elif current == head:
        console.print(f"Current revision: [green]{current}[/green] (at head)")
    else:
        console.print(f"Current revision: [yellow]{current}[/yellow]")

    if all_revisions:
        console.print("\nAvailable revisions:")
        for rev in reversed(all_revisions):
            marker = " [green]✓[/green]" if rev.revision == current else ""
            console.print(f"  {rev.revision}  {rev.doc}{marker}")


def cmd_upgrade(args: argparse.Namespace) -> None:
    engine = _setup_engine()
    console.print(f"Upgrading to: [bold]{args.revision}[/bold]")
    runner.upgrade(engine, args.revision)
    engine.dispose()
    current = runner.get_current_revision(engine)
    console.print(f"Done. Current revision: [green]{current}[/green]")


def cmd_downgrade(args: argparse.Namespace) -> None:
    engine = _setup_engine()
    console.print(f"Downgrading to: [bold]{args.revision}[/bold]")
    runner.downgrade(engine, args.revision)
    engine.dispose()
    current = runner.get_current_revision(engine)
    console.print(f"Done. Current revision: [yellow]{current or 'None'}[/yellow]")


def main() -> None:
    """CLI for database migrations."""
    parser = argparse.ArgumentParser(
        prog="acerestreamer-migrate",
        description=f"{PROGRAM_NAME} database migration tool v{__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")
    subparsers.required = True

    subparsers.add_parser("current", help="Show current revision and available revisions")

    upgrade_p = subparsers.add_parser("upgrade", help="Upgrade to a revision (default: head)")
    upgrade_p.add_argument("revision", nargs="?", default="head", help="Target revision (default: head)")

    downgrade_p = subparsers.add_parser("downgrade", help="Downgrade to a revision")
    downgrade_p.add_argument("revision", help="Target revision (e.g. 0001, base)")

    args = parser.parse_args()

    if args.command == "current":
        cmd_current(args)
    elif args.command == "upgrade":
        cmd_upgrade(args)
    elif args.command == "downgrade":
        cmd_downgrade(args)


if __name__ == "__main__":
    main()
