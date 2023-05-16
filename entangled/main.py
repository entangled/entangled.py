import click

from .tangle import tangle

@click.group
def main():
    pass


main.add_command(tangle)


if __name__ == "__main__":
    main()
