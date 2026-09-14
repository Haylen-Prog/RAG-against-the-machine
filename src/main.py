import fire
from src import CLI


class Monitoring:
    def __init__(self) -> None:
        try:
            fire.Fire(CLI)
        except ValueError as error:
            print(f"[CLI_ERROR]: {error}")


def main() -> None:
    monitor = Monitoring()
    print(monitor)
