import faiss 
import numpy as np
import glob
import pickle
from openai import OpenAI
import faiss 
from tqdm import tqdm
import pandas as pd
import tiktoken
import pyterrier as pt
from cord19_plus.data_model.embeddings import Embedding, Base
from cord19_plus.data_model.database_setup import setup_engine_session_alt
from sqlalchemy import create_engine
from dotenv import dotenv_values

db_vals = dotenv_values("/workspaces/CORD19_Plus/.env")


from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
from collections import defaultdict
import os

tiktoken_cache_dir = "/workspaces/CORD19_Plus/retrieval/tiktoken_cache"
os.environ["TIKTOKEN_CACHE_DIR"] = tiktoken_cache_dir
# validate
assert os.path.exists(os.path.join(tiktoken_cache_dir,"9b5ad71b2ce5302211f9c61530b329a4922fc6a4"))

client = OpenAI()

def cosine_similarity(a, b):
    #exspect normalized vecs
    if a:
        return np.dot(a, b)
    else:
        return 0

def search_docs(df, query, qid, n=1000, pprint=True):
   
   df.loc[:,'score'] = df.loc[:,'abstract_emb'].apply(lambda x: np.dot(x, query))
   res = df.sort_values('score', ascending=False).head(n)
   res.loc[:,'qid'] = qid
   return res

def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding

def transform_to_pt_res(df):
    df.loc[:, 'rank'] = list(range(len(df)))
    return df

def load_emb_df(paths = "/workspace/chunks_small_abstract/*"):
    chunk_paths = "/workspace/chunks_small_abstract/*"
    chunk_paths = sorted(glob.glob(chunk_paths))
    chunks = [pickle.load(open(path, "rb")) for path in chunk_paths]
    df = pd.concat(chunks)
    return df

def apply_queries(queries, df):
    results = []
    with tqdm(total = len(queries)) as pbar:
        for i, query in enumerate(queries):
            res = search_docs(df=df, query=query, qid=i+1)
            res = transform_to_pt_res(res)
            results.append(res)
            pbar.update(1)    
    res_df = pd.concat(results)
    return res_df

def build_faiss_index(df, column_to_index="emb", method="dot_product"):
    xb  = np.array(df.loc[:, column_to_index].to_list())
    d = xb.shape[1]
    index = None
    if method == "dot_product":
        index = faiss.IndexFlatIP(d)
        xb = xb.astype('float32')
        index.add(xb)  
    elif method == "euclid":
        index = faiss.IndexFlatL2(d)
        xb = xb.astype('float32')
        index.add(xb) 
    
    return index

def search(index, queries, k=1000):
    D, I = index.search(queries, k)
    return D, I

def faiss_to_pt_res(I, D, df):
    res = []
    for i in range(I.shape[0]):
        qid_res = pd.DataFrame()
        qid_res = df.iloc[I[i]].copy()
        qid_res.loc[:, 'qid'] = i + 1
        qid_res.loc[:, 'rank'] = list(range(len(qid_res)))
        qid_res.loc[:, 'score'] = list(D[i])
        res.append(qid_res)
    res = pd.concat(res)
    return res

def faiss_search_pipe(index, queries, df):
    D, I = search(index, queries)
    return faiss_to_pt_res(I, D, df)

def apply_cutoff(res, cutoff=20):
    return res[res['rank'] < cutoff]

def transform_to_catch_all(entry):
    catch_all = ""

    for key, val in entry.items():
        
        if key in ['docno', 'ir_id']:
            continue
        if isinstance(val, list):
            if val and isinstance(val[0], list):
                content = ' '.join([' '.join(sublist) for sublist in val])
            else:
                content = ' '.join(val)
        else:
            content = val

        catch_all += f"{key}: {content} | "
    
    return catch_all

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def get_embedding(text, model="text-embedding-3-small"):
   if len(text)<=3:
      return None

   text = text.replace("\n", " ")

   if num_tokens_from_string(text, "cl100k_base") <= 8192:
      return client.embeddings.create(input = [text], model=model).data[0].embedding
   
   else:
      text = " ".join(text.split(" ")[:1900])
      if num_tokens_from_string(text, "cl100k_base") <= 8192:
         return client.embeddings.create(input = [text], model=model).data[0].embedding
      else:
         print(num_tokens_from_string(text, "cl100k_base"))

   return None

def generate_document_pool_rrf_df(root_path, k=60, round_decimals=4):
    """
    Generates a sorted DataFrame containing a pool of unique documents for each topic,
    sorted by their Reciprocal Rank Fusion (RRF) scores across all retrieval systems.
    
    Args:
        root_path (str): The root directory containing ranking files. Each file should have lines
                         in the format:
                         <qid> Q0 <docno> <rank> <score> <systemname>
        k (int, optional): Smoothing constant added to each rank in the RRF calculation. Defaults to 60.
        round_decimals (int, optional): Number of decimal places to round the RRF scores. Defaults to 4.
    
    Returns:
        pd.DataFrame: A DataFrame with three columns:
                      - 'qid': The Query ID (int)
                      - 'docno': The Document ID (str)
                      - 'rrf_score': The Reciprocal Rank Fusion score of the document across all systems (float)
                      The DataFrame is sorted by 'qid' and 'rrf_score' in descending order.
    """

    if not pt.started():
        pt.init()

    # Initialize a defaultdict to store all ranks for each (qid, docno) pair
    rank_pool = defaultdict(list)

    # Iterate over all files in the root directory
    for filename in os.listdir(root_path):
        file_path = os.path.join(root_path, filename)

        # Check if the path is a file
        if os.path.isfile(file_path):
            try:
                # Read the ranking results using PyTerrier
                results = pt.io.read_results(file_path)

                # Ensure necessary columns are present
                expected_columns = {'qid', 'docno', 'rank', 'score'}
                if not expected_columns.issubset(results.columns):
                    print(f"Warning: File '{filename}' is missing expected columns. Skipping.")
                    continue

                # Iterate through each row in the DataFrame
                for _, row in results.iterrows():
                    # Extract and validate qid
                    qid_raw = row['qid']
                    try:
                        qid = int(qid_raw)
                    except (ValueError, TypeError):
                        print(f"Warning: Invalid qid '{qid_raw}' in file '{filename}'. Skipping this entry.")
                        continue

                    # Extract docno
                    docno = str(row['docno'])

                    # Extract and validate rank
                    rank = row['rank']
                    if pd.isna(rank):
                        print(f"Warning: Missing rank for docno '{docno}' in qid '{qid}' in file '{filename}'. Skipping this entry.")
                        continue

                    try:
                        rank = float(rank)
                        if rank < 0:
                            print(f"Warning: Negative rank '{rank}' for docno '{docno}' in qid '{qid}' in file '{filename}'. Skipping this entry.")                            
                            continue
                    except ValueError:
                        print(f"Warning: Invalid rank '{rank}' for docno '{docno}' in qid '{qid}' in file '{filename}'. Skipping this entry.")
                        continue

                    # Append the rank to the list for this (qid, docno) pair
                    rank_pool[(qid, docno)].append(rank)

            except Exception as e:
                print(f"Error reading file '{filename}': {e}")

    # Prepare data for the DataFrame
    data = {
        'qid': [],
        'docno': [],
        'rrf_score': []
    }

    for (qid, docno), ranks in rank_pool.items():
        if ranks:
            # Calculate RRF score: sum(1 / (rank + k)) for all ranks
            rrf_score = sum(1.0 / (rank + k) for rank in ranks)
            rrf_score = round(rrf_score, round_decimals)  # Round the RRF score
            data['qid'].append(qid)
            data['docno'].append(docno)
            data['rrf_score'].append(rrf_score)

    # Create the DataFrame
    df_pool = pd.DataFrame(data)

    # Sort the DataFrame by 'qid' ascending and 'rrf_score' descending
    df_pool_sorted = df_pool.sort_values(by=['qid', 'rrf_score'], ascending=[True, False]).reset_index(drop=True)

    return df_pool_sorted




def process_res(res):
    catch_all = transform_to_catch_all(res)
    return {'docno': res['docno'], 'emb': get_embedding(catch_all)}

def embeddings_to_db(emb_list, session):
    for dict_el in emb_list:
        emb = Embedding(docno=dict_el['docno'], embedding=dict_el['emb'])
        session.add(emb)
    session.commit()

def batch_iterator(iterable, batch_size):
    """Generator to yield batches of specified size from the iterable."""
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]

def populate_embs_from_result(result_dict, batch_size=100, max_workers=20):


    # Setup your database session (modify the connection string as needed)
    session_emb = setup_engine_session_alt(
        db_vals['USER'],
        db_vals['PASSWORD'],
        db_vals['ADDRESS'],
        db_vals['PORT'],
        db_vals['DB_EMBS'],
        Base=Base
    )

    avail_ids = set([res[0] for res in session_emb.query(Embedding.docno).all()])

    result_dict = [res for res in result_dict if res['docno'] not in avail_ids]
    print(f"{len(avail_ids)} Tables already processed")
    print(f"{len(result_dict)} Tables to process")

    
    total_batches = (len(result_dict) + batch_size - 1) // batch_size  # Ceiling division

    # Overall progress bar for batches
    with tqdm(total=total_batches, desc="Overall Progress") as overall_pbar:
        # Iterate over each batch
        for batch in batch_iterator(result_dict, batch_size):
            embeddings = []

            # Inner progress bar for processing items in the current batch
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks for the current batch
                futures = {executor.submit(process_res, res): res for res in batch}

                # As each future completes, append the result
                for future in tqdm(as_completed(futures), total=len(futures), desc="Batch Processing", leave=False):
                    try:
                        result = future.result()
                        embeddings.append(result)
                    except Exception as e:
                        print(f"Error processing item: {e}")

            # Insert the processed embeddings into the database
            try:
                embeddings_to_db(embeddings, session_emb)
            except Exception as e:
                print(f"Error inserting into DB: {e}")

            # Update the overall progress bar
            overall_pbar.update(1)

    # Close the session after all batches are processed
    session_emb.close()
    print("Processing and insertion complete.")


def get_emb_df():

    session_emb = setup_engine_session_alt(
        db_vals['USER'],
        db_vals['PASSWORD'],
        db_vals['ADDRESS'],
        db_vals['PORT'],
        db_vals['DB_EMBS'],
        Base=Base
    )
    
    all_embs = session_emb.query(Embedding).all()
    all_embs = [{'docno' : row.docno, 'embedding' : row.embedding} for row in all_embs]
    return pd.DataFrame(all_embs)