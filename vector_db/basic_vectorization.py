from sentence_transformers import SentenceTransformer

import os
import pandas as pd

def get_basic_vetorizetion_model():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

DEFAULT_ARGS = {"show_progress_bar": True}

def vectorize_with(model, args=DEFAULT_ARGS):

    def vectorize(texts):
        unique_texts = sorted(set(texts))
        vectors = model.encode(unique_texts, **args)

        text_to_vector = {text: vector for text, vector in zip(unique_texts, vectors)}
        return [text_to_vector[text] for text in texts]
    
    return vectorize

BASIC_VECTORIZED_PARQUET_PATH = os.path.join(
    os.path.dirname(__file__), "tmp", "basic-vectorized.parquet"
)

def write_basic_vectorized_data(data):
    data.to_parquet(
        BASIC_VECTORIZED_PARQUET_PATH,
        index=False,
        engine="pyarrow"
    )

def read_basic_vectorized_data():
    if os.path.isfile(BASIC_VECTORIZED_PARQUET_PATH):
        return pd.read_parquet(
            BASIC_VECTORIZED_PARQUET_PATH,
            engine="pyarrow"
        )
    
    return ValueError("事前にベクトル化したデータがありません")

def get_dimension_number_of(data):
    return len(data["query_vector"].iloc[0])

def split_into_query_and_document(data):
    return (
        data.drop_duplicates("query_id"),
        data.drop_duplicates("product_id")
    )

if __name__ == "__main__":
    from data_preparation import read_jp_data

    basic_vectorization_model = get_basic_vetorizetion_model()
    vectorize = vectorize_with(basic_vectorization_model)

    texts = [
        "HDMIケーブル",
        "電話機",
        "液晶ディスプレイ",
        "液晶テレビ",
    ]

    vectors = vectorize(texts)

    print(len(vectors))

    for vector in vectors:
        print(len(vector))
    
    jp_data = read_jp_data(sample_rate=0.01)

    jp_data["query_vector"] = vectorize(jp_data["query"])
    jp_data["title_vector"] = vectorize(jp_data["product_title"])

    write_basic_vectorized_data(jp_data)