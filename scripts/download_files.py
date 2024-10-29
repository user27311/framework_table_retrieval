from cord19_plus.downloadpdf.downloaders import (
    Cord19Reader,
    Index,
    Status,
    OpenAlex,
    URLDownloader,
    NotInOpenAlexError,
    NotOpenAccessError,
    PDFNotAvailableError,
    OpenAlexRateLimitError,
)
import time
import requests.exceptions
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.ERROR)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    index = Index.from_jsonl(
        "index.jsonl",  # change to location of your index
        "pdfs",  # change to location of your download dir
    )

    reader = Cord19Reader("metadata.csv")  # change to location of your metadata.csv file
    meta = reader.read_metadata(index)

    oa = OpenAlex()  # Add your email for faster downloads
    dl = URLDownloader()

    for idx, m in enumerate(meta):
        if idx % 100 == 0:
            logging.info(f"At entry: {idx}")
        try:
            oa_url = oa.find_pdf_url(m["doi"])
            req = dl.request_pdf(oa_url, return_full_request=True)
            content = req.content
            oa_url = [res.url for res in req.history]
            oa_url.append(req.url)
            index.save_file(content, m["doi"], oa_url)

        except NotInOpenAlexError:
            index.add(m["doi"], Status.NOT_IN_OPENALEX, None, None)

        except NotOpenAccessError:
            index.add(m["doi"], Status.NOT_OPEN_ACCESS, None, None)

        except PDFNotAvailableError:
            index.add(m["doi"], Status.UNAVAILABLE, None, oa_url)

        except requests.exceptions.RequestException as e:
            logger.warning(e)
