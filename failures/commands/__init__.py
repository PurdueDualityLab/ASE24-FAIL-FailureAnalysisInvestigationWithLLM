import argparse
import logging
import textwrap
from typing import Protocol

from failures.commands.scrape import ScrapeCommand
from failures.commands.summarize import SummarizeCommand
from failures.commands.embed import EmbedCommand
from failures.commands.classify import ClassifyCommand
from failures.commands.postmortem import PostmortemCommand
from failures.commands.cluster import ClusterCommand


_EPILOG = textwrap.dedent(
    """\
    Please submit feedback, ideas, and bug reports by filing a new issue at
    https://github.com/d57montes/failures/issues.
    """
)

_DESCRIPTION = textwrap.dedent(
    """\
    failures is a tool for scraping and analyzing software failures in the news.
    """
)


class Command(Protocol):
    def prepare_parser(self, parser: argparse.ArgumentParser) -> None:
        ...

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
        ...


_COMMANDS: list[Command] = [ScrapeCommand(), SummarizeCommand(), EmbedCommand(), ClassifyCommand(), PostmortemCommand(), ClusterCommand()]


def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=_DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=_EPILOG,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=1,
        help="Increase verbosity. Option is additive and can be specified up to 3 times.",
    )

    subparsers = parser.add_subparsers(
        help="Subcommand to run. See `python3.9 -m failures <command> --help` for more information.",
        dest="command",
        required=True,
    )

    for command in _COMMANDS:
        assert command.__class__.__name__.endswith("Command")
        name = command.__class__.__name__[: -len("Command")].lower()

        command_parser = subparsers.add_parser(
            name,
            help=command.__doc__,
            epilog=_EPILOG,
        )
        command_parser.set_defaults(entrypoint=command.run)
        command.prepare_parser(command_parser)

    return parser


def determine_logging_level(verbose_level: int) -> int:
    if verbose_level == 0:
        return logging.WARNING
    elif verbose_level == 1:
        return logging.INFO
    else:
        return logging.DEBUG


def main():
    parser = get_argument_parser()
    args = parser.parse_args()

    logging.basicConfig(
        filename="test.log",
        filemode='a',
        level=determine_logging_level(args.verbose),
        format="%(asctime)s %(levelname)s: %(message)s",
        force=True,
    )

    args.entrypoint(args, parser)
