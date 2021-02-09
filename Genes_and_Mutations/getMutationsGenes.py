import json
import requests
import functools
from requests.structures import CaseInsensitiveDict
headers = CaseInsensitiveDict()
headers["Content-Type"] = "application/json"

endpoint = "https://api.gdc.cancer.gov/graphql"

with open("case_ids.json") as json_file:
    case_ids = json.load(json_file)["case_ids"]

with open("geneRequest.json") as json_file:
    gene_request = json.load(json_file)

with open("mutationRequest.json") as json_file:
    mutation_request = json.load(json_file)


# get mutations from list of case ids. Returns a dictionart where keys are case_ids which contain their mutation count
def get_mutations(case_ids: list()):
    mutation_request["variables"]["ssmCountsfilters"]["content"][1]["content"]["value"] = case_ids
    resp_json = requests.post(endpoint, headers=headers, data=json.dumps(mutation_request)).json()
    mutations = resp_json["data"]["ssmsAggregationsViewer"]["explore"]["ssms"]["aggregations"]["occurrence__case__case_id"]["buckets"]
    def merge(dict1: dict, dict2: dict):
        dict1.update(dict2)
        return dict1
    mutations = functools.reduce(lambda prev, curr: merge(prev, {curr["key"] : curr["doc_count"]}), mutations, dict())
    return mutations

# get genes from all case ids (2875 cases on 09/02/2020). Count specifies how many results to get back (should ideally be set to the number of case ids that we have)
def get_genes(count: int):
    gene_request["variables"]["cases_size"] = count # default is 100
    resp_json = requests.post(endpoint, headers=headers, data=json.dumps(gene_request)).json()
    data = resp_json["data"]["exploreCasesTableViewer"]["explore"]["cases"]["hits"]["edges"]
    genes = dict()
    for record in data:
        genes[record["node"]["case_id"]] = record["node"]["score"]
    return genes


mutations = get_mutations(case_ids)
print(f"Mutations dictionary: {mutations}")

genes = get_genes(3000)
print(f"Genes dictionary: {genes}")