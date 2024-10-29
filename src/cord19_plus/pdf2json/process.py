import json
from papermage.recipes import CoreRecipe
from pathlib import Path
#from ..downloadpdf import Index
import logging
from tqdm import tqdm

from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger(__name__)


def process_docs_simple(folder_in: str | Path, folder_out: str | Path, save_images: bool = False):
    """
    Run papermage core recipe on pdfs in folder_in and write json-files to folder_out

    :param folder_in: source folder (containing pdfs)
    :param folder_out: destination folder (writing json files)
    :param save_images: create images from pdf-documents for later usage
    :return:
    """
    folder_in, folder_out = Path(folder_in), Path(folder_out)
    recipe = CoreRecipe()
    for f in tqdm(sorted(folder_in.glob("*.pdf"))):
        doc = recipe.run(f)
        with open(folder_out / (f.name[: f.name.rfind(".")] + ".json"), "w") as _f:
            json.dump(doc.to_json(), _f)
            if save_images:
                for i, img in enumerate(doc.images):
                    img.save(f"{_f.name[: _f.name.rfind('.')]}_p{i + 1}.png")


def process_single_doc(f: Path, folder_out: Path, save_images: bool, verbose: bool) -> None:
    """
    Process a single PDF file and save the resulting JSON and optional images.

    :param f: Path to the PDF file.
    :param folder_out: Folder where the resulting JSON file and images (if `save_images` is True) will be saved.
    :param recipe: Pre-instantiated CoreRecipe object used to process the PDFs.
    :param save_images: If True, save images extracted from the PDF.
    """
    try:
        output_json_path = folder_out / (f.name[: f.name.rfind(".")] + ".json")
        #check if file already exists
        if output_json_path.exists():
            if verbose:
                print(f"Skipping {f} because {output_json_path} already exists")
            return
        
        #check if the path is in bad_paths
        with open("/workspaces/CORD19_Plus/data/rel_pdfs/bad_paths", "r") as bad_paths:
            bad_paths_list = bad_paths.readlines()
            bad_paths_list = [path.strip() for path in bad_paths_list]
            if str(f) in bad_paths_list:
                if verbose:
                    print(f"Skipping {f} because it is in bad_paths")
                return
        
        if verbose:
            print(f"Processing {f}")
        recipe = CoreRecipe() 
        doc = recipe.run(f)
        
        with open(output_json_path, "w") as _f:

            json.dump(doc.to_json(), _f)
            
            if save_images:
                for i, img in enumerate(doc.images):
                    img_path = f"{_f.name[: _f.name.rfind('.')]}_p{i + 1}.png"
                    img.save(img_path)
    except:
        with open("/workspaces/CORD19_Plus/data/rel_pdfs/bad_paths", "a") as bad_paths:
                bad_paths.write(f"{str(f)}\n")
        logger.exception(f"Error processing {f}")
        


def process_docs_parallel(folder_in: str | Path, folder_out: str | Path, save_images: bool = False, max_workers: int = None, max_docs: int = None, verbose: bool = False) -> None:
    """
    Run papermage core recipe on PDFs in `folder_in` and write JSON files to `folder_out` in parallel.

    :param folder_in: Source folder (containing PDF files).
    :param folder_out: Destination folder (for saving JSON files and images).
    :param save_images: If True, create images from PDF documents for later usage.
    :param max_workers: Maximum number of worker threads to use. If None, defaults to the number of CPUs.
    :param max_docs: Maximum number of documents to process. If None, all documents are processed.
    :param verbose: If True, print pdf names.
    :return: None.
    """
    folder_in, folder_out = Path(folder_in), Path(folder_out)
    
    # List PDF files in the input folder
    pdf_files = sorted(folder_in.glob("*.pdf"))
    
    if max_docs:
        pdf_files = pdf_files[:max_docs]
    
    # Multi-threaded execution with ThreadPoolExecutor
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_single_doc, f, folder_out, save_images, verbose)
            for f in pdf_files
        ]
        
        # Use tqdm for showing progress
        for _ in tqdm(futures, total=len(futures), desc="Total PDFs", leave=True):
            _.result()  # This will propagate any exceptions raised during processing



def process_index(index_path: Path, pdf_dir: Path, exports_dir: Path):
    """Processes all downloaded documents inside an index."""
    index = Index.from_jsonl(index_path, pdf_dir)
    recipe = CoreRecipe()
    processed_jsons = set(exports_dir.iterdir())
    for key, row in index.items():

        if not row.pdf_path:
            continue

        if exports_dir / Path(key + ".json") in processed_jsons:
            continue
        try:
            doc = recipe.run(row.pdf_path)
        except Exception as e:
            logger.error(f"Error processing {row.pdf_path}: {e}")
            #add to the pdf_path to the bad_paths file
            
            continue

        with open(exports_dir / Path(key + ".json"), "w") as _f:
            json.dump(doc.to_json(), _f)


if __name__ == "__main__":
    #process_docs_parallel(folder_in="/workspaces/pdfs",
    #                  folder_out="/workspaces/CORD19_Plus/data/out/2024-07-23",
    #                   save_images=True,
    #               max_workers=1)

    process_docs_simple(folder_in="/workspaces/pdfs",
                        folder_out="/workspaces/CORD19_Plus/data/out/2024-07-23",
                        save_images=True)   