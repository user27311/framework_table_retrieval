from cord19_plus.pdf2json.process import process_index
from pathlib import Path

base_path = Path("")  # set path
process_index(base_path / Path("index_subset.jsonl"), base_path / Path("pdfs"), base_path / Path("exports"))
