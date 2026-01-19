from rich.console import Console

console = Console(highlight=False)


def prompt(message: str) -> str:
    console.print(message)
    return input("> ").strip()  # Rich prompt is not all that
