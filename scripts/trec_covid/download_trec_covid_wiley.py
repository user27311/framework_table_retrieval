import json
from pathlib import Path
from cord19_plus.downloadpdf import (
    WileyURLDownloader,
    Index,
    Status,
    PDFNotAvailableError,
    RateLimitError,
    WileyQuoataException,
)
from requests.exceptions import RequestException
import logging
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    base_path = Path("")  # set path
    oa_requests_path = base_path / Path("oa-requests")
    index_path = base_path / Path("index.jsonl")
    pdfs_path = base_path / Path("pdfs")

    index = Index.from_jsonl(index_path, pdfs_path)

    all_dois = []

    for doc_path in oa_requests_path.iterdir():
        doc = json.load(open(doc_path, "r"))
        for req in doc:
            all_dois.extend(req)

    keys_to_pop = []
    for key in index.keys():
        if index[key].pdf_url and "wiley" in index[key].pdf_url and not index[key].pdf_path:
            keys_to_pop.append(key)

    for key in keys_to_pop:
        index.pop(key)

    index.overwrite()

    wiley_dois = [doi[0] for doi in all_dois if doi[1] and "wiley" in doi[1]]
    dl = WileyURLDownloader()

    for idx, doi in enumerate(wiley_dois):
        if doi not in index:
            try:
                pdf_url = "https://api.wiley.com/onlinelibrary/tdm/v1/articles/" + dl._doi_strip(doi)
                pdf_bytes = dl.request_pdf(pdf_url)
                index.save_file(pdf_bytes, doi, doi)
                time.sleep(0.8)
            except WileyQuoataException as e:
                logger.exception(e)
                time.sleep(60)

            except RateLimitError as e:
                logger.exception(e)
                exit()

            except PDFNotAvailableError as e:
                logger.exception(e)
                index.add(doi, Status.UNAVAILABLE, None, pdf_url)

            except RequestException as e:
                index.add(doi, Status.REQUEST_ERROR, None, pdf_url)

            except Exception as e:
                exit()

            if idx % 100:
                logger.info(f"checked {idx} pdfs")
