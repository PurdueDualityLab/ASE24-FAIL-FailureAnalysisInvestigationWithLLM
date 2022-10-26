import argparse


class ScrapeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        ...

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        ...
