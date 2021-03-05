import pandas as pd
import json
import copy

json_data_path: str = "./reconstructedData.json"

with open(json_data_path, 'r') as f:
    json_data = json.load(f)

# with open("test3.json", 'r') as f:
#     slide_data = json.load(f)

def clean_slide_data(data: dict):
    hits = copy.deepcopy(data["data"])
    result = list()
    for hit in hits:
        # add useful field for when reading data visually
        sample_code = hit["slides"]["SampleCode"] if "slides" in hit and "SampleCode" in hit["slides"] else None
        if sample_code == None:
            hit["slides"]["sample_type"] = "No sample_type"
        if sample_code == "01":
            hit["slides"]["sample_type"] = "Primary Solid Tumor"
        elif sample_code == "06":
            hit["slides"]["sample_type"] = "Metastatic"
        elif sample_code == "07":
            hit["slides"]["sample_type"] = "Additional Metastatic"
        elif sample_code == "11":
            hit["slides"]["sample_type"] = "Solid Tissue Normal"

        result.append(hit["slides"])
    return result


# works on reconstructedData.json
def clean_data(data: dict):
    hits = copy.deepcopy(data["data"])
    result = list()
    for hit in hits:
        # make data more readable
        # hit.update(hit["slides"])

        # # add useful field for when reading data visually
        # sample_code = hit["slides"]["SampleCode"]
        # if sample_code == "01":
        #     hit["sample_type"] = "Primary Solid Tumor"
        # elif sample_code == "06":
        #     hit["sample_type"] = "Metastatic"

        # remove unnecessary data
        hit.pop("slides")

        # print(hit)
        result.append(hit)
    return result


def to_dataframe(data: dict):
    dataframe = pd.DataFrame(data)
    return dataframe


# reconstructed Data dataframe
cleaned_data = clean_data(json_data)
dataframe: pd.DataFrame = to_dataframe(cleaned_data)
print(dataframe)
print("saving main dataframe to csv")
dataframe.to_csv(path_or_buf="readable_data.csv")

# slides dataframe
slide_cleaned_data = clean_slide_data(json_data)
slide_dataframe = to_dataframe(slide_cleaned_data)
print("saving slide dataframe to csv")
slide_dataframe.to_csv("slide_data.csv")