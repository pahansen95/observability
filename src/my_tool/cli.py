"""Command line interface."""

import argparse


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(prog="my-tool")
    parser.add_argument(
        "--message",
        default="Hello from my-tool",
        help="Message to display",
    )
    args = parser.parse_args(argv)
    print(args.message)

if __name__ == "__main__":
    main()
