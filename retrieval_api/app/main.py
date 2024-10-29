from fastapi import FastAPI
import pyterrier as pt
from typing import Union
import uvicorn
import sys
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from model import Document, Table

sys.path.append("/app/")

app = FastAPI()
index = None
search_model = None
session = None

INDEX_PATH = "/app/cord19_table_index"

def init():
    global index
    global search_model
    global session
    
    if not pt.started():
        pt.init()
    print("load retrieval model")

    index  = pt.IndexFactory.of(INDEX_PATH)
    search_model = pt.BatchRetrieve(index, wmodel="BM25")
    db_vals = dotenv_values("/app/.env")

    engine = create_engine(f"postgresql+psycopg2://{db_vals['USER']}:{db_vals['PASSWORD']}@{db_vals['ADDRESS']}:{db_vals['PORT']}/{db_vals['DB']}", echo=False)
    session = Session(engine)


@app.get("/issue_docs/{query}")
def issue_docs(query: str):
    global search_model
    res = search_model.search(query)
    return {"query": query, "result": res.to_dict()}

@app.get("/issue_tables/{query}")
def issue_tables(query: str):
    global session
    rel_docs = issue_docs(query)['result']['docno']
    ranked_tables = {}

    for rank, docno in rel_docs.items():
        tables = session.query(Table).filter(Table.document_id == docno).all()
        if tables:
            ranked_tables[rank] = tables

    return {"query": query, "result" : ranked_tables}

if __name__ == "__main__":
    init()
    uvicorn.run(app, host="0.0.0.0", port=8082)