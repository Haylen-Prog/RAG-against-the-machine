import argparse

class Monitoring:
	def __init__(self) -> None:
		parser = argparse.ArgumentParser()
		self.res = parser.add_argument(
			"--max_chunk_size",
			default=2000,
			help="Chunk size with a default of 2000 characters (Do not go above it)")

def main():
	monitor = Monitoring()
	print(monitor.res.default)