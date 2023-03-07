"""Console script for della."""

import sys

import click


@click.command()
def main():
    """Console script for della."""
    click.echo("Replace this message by putting your code into " "della.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
