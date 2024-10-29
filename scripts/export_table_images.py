import json
from pathlib import Path
from cord19_plus.downloadpdf.downloaders import Index
from papermage import Document
from cord19_plus.utils import image_from_box
import ir_datasets
import pymupdf
from itertools import groupby
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

base_path = Path("")  # set path to dataset
exports_path = base_path / Path("exports")
index_path = base_path / Path("index_subset.jsonl")
download_dir = base_path / Path("pdfs")
images_path = base_path / Path("table_images_no_margin")


ind = Index.from_jsonl(index_path, download_dir)
dataset = ir_datasets.load("cord19/trec-covid")

# done = set([tuple(im_path.stem.split("_")) for im_path in images_path.glob("*.png")])
# fail = 0
# total = 0

for export_path in exports_path.glob("*.json"):

    doc_id = export_path.stem
    doc = Document.from_json(json.load(open(export_path, "r")))

    if len(doc.get_layer("tables")) == 0:
        continue
    entities = list(doc.get_layer("tables"))
    sorted(entities, key=lambda x: x.boxes[0].page)
    for key, group in groupby(entities, key=lambda x: x.boxes[0].page):
        for table_id, table in enumerate(list(group)):
            box = table.boxes[0]
            page = box.page

            # increases resolution of image by factor 2 in every direction. Is an optional argument.
            scale = pymupdf.Matrix(2, 2)

            im_path = images_path / Path(f"{doc_id}_{page}_{table_id}.png")

            try:
                image_from_box(box, ind[doc_id].pdf_path, im_path, scale)
                logger.info(
                    f"For {doc_id} : {ind[doc_id].pdf_path} exported table nr {table_id} from page {box.page} to {im_path}"
                )
            except ValueError as e:
                logger.error(
                    f"Failed for {doc_id} table {table_id} from page {box.page}, pdf path {ind[doc_id].pdf_path}. Because of ValueError: {e}"
                )
                continue
            except pymupdf.FileNotFoundError as f:
                logger.error(f"PDF file not found for {doc_id}, {ind[doc_id].pdf_path}")
