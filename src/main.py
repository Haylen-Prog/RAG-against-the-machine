import fire
from src import CLI


class Monitoring:
	def __init__(self) -> None:
		fire.Fire(CLI)


def main():
	monitor = Monitoring()
