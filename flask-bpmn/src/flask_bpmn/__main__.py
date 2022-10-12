"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Flask Bpmn."""
    print("This does nothing")


if __name__ == "__main__":
    main(prog_name="flask-bpmn")  # pragma: no cover
