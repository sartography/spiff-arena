"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Spiffworkflow Backend."""
    print("This does nothing")


if __name__ == "__main__":
    main(prog_name="spiffworkflow-backend")  # pragma: no cover
