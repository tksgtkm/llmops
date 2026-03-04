import os
import pandas as pd

def read_jp_data(sample_rate=1.0, split=None, read_product_detail=False):
    examples_path, products_path = (
        os.path.join(
            os.path.dirname(__file__),
            "esci-data",
            "shopping_queries_dataset",
            f"shopping_queries_dataset_{suffix}.parquet",
        ) for suffix in ("examples", "products")
    )

    examples_filters = [("small_version", "==", 1), ("product_locale", "==", "jp")]

    if split is not None:
        examples_filters.append(("split", "==", split))
    
    if sample_rate < 1.0:
        query_ids = pd.read_parquet(
            examples_path,
            columns=["query_id"],
            filters=examples_filters,
            engine="pyarrow"
        )["query_id"]
        query_ids = set(query_ids)

        denominator = int(1.0 / sample_rate)
        query_ids = filter(lambda query_id: query_id % denominator == 0, query_ids)

        examples_filters.append(("query_id", "in", query_ids))

    product_columns_to_read = ["product_id", "product_title"]
    if read_product_detail:
        product_columns_to_read += [
            "product_brand",
            "product_color",
            "product_description",
            "product_bullet_point",
        ]

    return pd.merge(
        pd.read_parquet(
            examples_path,
            columns=["query", "query_id", "product_id", "esci_label", "split"],
            filters=examples_filters,
            engine="pyarrow"
        ),
        pd.read_parquet(
            products_path,
            columns=product_columns_to_read,
            filters=[("product_locale", "==", "jp")],
            engine="pyarrow"
        ),
        on="product_id"
    )

if __name__ == "__main__":

    def assert_counts(sample_rate, split, query_count, row_count):
        if sample_rate == 1.0:
            if split is None:
                assert (query_count, row_count) == (10407, 297883)
            if split == "train":
                assert (query_count, row_count) == (7284, 209094)
            if split == "test":
                assert (query_count, row_count) == (3123, 88789)
        else:
            if split is None:
                assert (query_count, row_count) == (97, 2681)
            if split == "train":
                assert (query_count, row_count) == (66, 1811)
            if split == "test":
                assert (query_count, row_count) == (31, 870)

    for sample_rate in [1.0, 0.01]:
        for split in [None, "train", "test"]:
            jp_data = read_jp_data(sample_rate=sample_rate, split=split)
            query_count = len(set(jp_data["query_id"]))
            row_count = len(jp_data)
            assert_counts(sample_rate, split, query_count, row_count)

    jp_data = read_jp_data(sample_rate=0.01, split="test")
    jp_data = jp_data[jp_data.query_id == 119300]
    print(
        jp_data.to_string(
            columns=["esci_label", "query", "product_title"],
            index=False,
            max_colwidth=30
        )
    )