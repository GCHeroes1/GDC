import pandas as pd
import json

json_data_path: str = "./finalDataSet.json"

with open(json_data_path, 'r') as f:
    json_data = json.load(f)

def clean_data(data: dict):
    hits = data["data"]["hits"]
    result = list()
    for hit in hits:
        # make data more readable
        hit.update(hit["demographic"])
        hit["number_of_slides"] = len(hit["slides"])
        # hit["diagnoses"] = [entry["primary_diagnosis"] for entry in hit["diagnoses"]]

        # remove unnecessary data
        hit.pop("slide_ids")
        # hit.pop("slides")
        hit.pop("demographic")
        result.append(hit)
    return result

def to_dataframe(data: dict):
    dataframe = pd.DataFrame(data)
    return dataframe


cleaned_data = clean_data(json_data)
dataframe: pd.DataFrame = to_dataframe(cleaned_data)
print(dataframe)
dataframe.to_csv(path_or_buf="readable_data.csv")