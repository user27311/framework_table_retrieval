import json
import pickle 
from cord19_plus.labelers import GPT
from cord19_plus.data_model.database_setup import setup_engine_session
from cord19_plus.data_model.model import Table
from pathlib import Path
from dotenv import load_dotenv
import os
import autoqrels
import ir_datasets
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").disabled = True
logging.getLogger("sqlalchemy.engine.Engine").disabled = True


def prepare_table_for_gpt(table: Table) -> str:
    document = {
            "caption": table.caption,
            "relation": table.content_json
        }
    return str(document)


if __name__ == '__main__':

    base = Path(__name__).parent # name of parent folder
    qrels_path = base / Path("/workspaces/CORD19_Plus/data/tables.qrels")

    if not qrels_path.parent.is_dir():
        raise ValueError(f"{qrels_path} is not a directory")
    
    dataset = ir_datasets.load("cord19/trec-covid")
    
    subset = base / Path("data/subset_1_results")  # dir containing
    prompt = """
    

            """
    gpt = GPT(dataset, os.getenv("OPENAI_API_KEY"), "gpt-4o-mini")
    topic = autoqrels.text.query_text(dataset, ["1"], None)
    logger.info(f"Selected Topic: {topic}")

    session = setup_engine_session("cord19_user", os.getenv("PASSWORD"), os.getenv("ADDRESS"), os.getenv("PORT"), os.getenv("DB"))
    tables = session.query(Table).all()

    queries = [prepare_table_for_gpt(table) for table in tables] 
    labels = gpt._infer_zeroshot_text(autoqrels.text.query_text(dataset, ["1"], None), queries)
    logger.info(f"Computed labels: {labels}")


    with open(qrels_path, "w")  as fp:
        for table, label in zip(tables, labels):
            fp.write(f"{1} {0} {table.ir_tab_id} {label}\n")
        
        logging.info(f"Saved Qrels under {qrels_path}")
