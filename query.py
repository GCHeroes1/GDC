#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, os.path
import argparse

import json
import requests

import numpy as np
import pandas as pd
import statistics



CASE_FIELDS = [
    'submitter_id',
    'case_id',
    'consent_type',

    'project.program.name',
    'primary_site',
    'disease_type',
    'diagnoses.primary_diagnosis',

    'diagnoses.age_at_diagnosis',
    'diagnoses.days_to_diagnosis',
    'diagnoses.year_of_diagnosis',

    'diagnoses.annotations.annotation_id',

    'diagnoses.classification_of_tumor',
    'diagnoses.cog_renal_stage',
    'diagnoses.laterality',
    'diagnoses.metastasis_at_diagnosis',
    'diagnoses.method_of_diagnosis',
    'diagnoses.mitotic_count',
    'diagnoses.morphology',
    'diagnoses.papillary_renal_cell_type',
    'diagnoses.percent_tumor_invasion',
    'diagnoses.prior_malignancy',
    'diagnoses.site_of_resection_or_biopsy',
    'diagnoses.sites_of_involvement',
    'diagnoses.tissue_or_organ_of_origin',
    'diagnoses.tumor_stage',

    'demographic.vital_status',
    'demographic.cause_of_death',
    'demographic.days_to_death',
    'demographic.year_of_birth',
    'demographic.year_of_death',
    'demographic.ethnicity',
    'demographic.gender',
    'demographic.race',

    'slide_ids',

    'samples.portions.slides.section_location',
    'samples.portions.slides.slide_id',
    'samples.portions.slides.submitter_id',
    'samples.portions.slides.number_proliferating_cells',
    'samples.portions.slides.percent_eosinophil_infiltration',
    'samples.portions.slides.percent_granulocyte_infiltration',
    'samples.portions.slides.percent_inflam_infiltration',
    'samples.portions.slides.percent_lymphocyte_infiltration',
    'samples.portions.slides.percent_monocyte_infiltration',
    'samples.portions.slides.percent_necrosis',
    'samples.portions.slides.percent_neutrophil_infiltration',
    'samples.portions.slides.percent_normal_cells',
    'samples.portions.slides.percent_stromal_cells',
    'samples.portions.slides.percent_tumor_cells',
    'samples.portions.slides.percent_tumor_nuclei',

    'annotations.annotation_id',
    'annotations.category',
    'annotations.classification',
    'annotations.notes',

    'state'
]

FILE_FIELDS = [
    'file_id',

    'file_name',
    'file_size',
    'type',
    'data_type',
    'data_category',
    'created_datetime',
    'updated_datetime',

    'access',
    'state',

    'imaging_date',
    'magnification',

    'annotations.annotation_id',
    'annotations.category',
    'annotations.classification',
    'annotations.notes',
    'annotations.case_id',
]

ENDPOINT = 'https://api.gdc.cancer.gov/'
CASES_ENDPOINT = ENDPOINT + 'cases'
FILES_ENDPOINT = ENDPOINT + 'files'

CASE_FILTERS = {
    'op': 'and',
    'content': [
        {
            'op': 'in',
            'content':{
                'field': 'primary_site',
                'value': ['Skin']
            }
        },
        {
            'op': 'in',
            'content': {
                'field': 'project.program.name',
                'value': "TCGA"
            }
        },
        {
            'op': '!=',
            'content': {
                'field': 'demographic.vital_status',
                'value': ['Not Reported']
            }
        },
        {
            'op': 'in',
            'content': {
                'field': 'diagnoses.primary_diagnosis',
                'value': ['Malignant melanoma, NOS']
            }
        },
        {
            'op': 'not',
            'content':{
                'field': 'slide_ids'
            }
        },
    ]
}

def process_args():
    ap = argparse.ArgumentParser(description='Get metadata from the GDC.')
    ap.add_argument('-C', '--cases', help='existing JSON file of case query results', default=None)
    ap.add_argument('-O', '--cases_out', help='file to save case query results to', default=None)

    ap.add_argument('-N', '--num_cases', help='maximum number of cases to query for', default=50)
    ap.add_argument('-p', '--primary', help='primary site of the case', default='Skin')

    ap.add_argument('-x', '--no_files', help='exit without querying slide files', action='store_true')
    ap.add_argument('-n', '--num_slides', help='maximum number of slides to query for', default=None)
    ap.add_argument('-o', '--slides_out', help='file to save slide query results to', default='slides_out.json')
    ap.add_argument('-s', '--slides_in', help='file containing slide query results', default=None)

    return ap.parse_args()


def get_cases(args):
    if args.cases:
        with open(args.cases) as f:
            return json.load(f)
    else:
        CASE_FILTERS['content'][0]['content']['value'] = [args.primary]

        params = {
            'filters' : json.dumps(CASE_FILTERS),
            'fields' : ','.join(CASE_FIELDS),
            'format' : 'JSON',
            'size' : args.num_cases
        }

        response = requests.get(CASES_ENDPOINT, params=params)

        return json.loads(response.content.decode('utf8'))

def slide_to_files(slide_id):
    filter = {
        'op' : 'and',
        'content' : [
            {
                'op' : '=',
                'content' : {
                    'field' : 'cases.samples.portions.slides.slide_id',
                    'value' : slide_id
                }
            },
            {
                'op' : '=',
                'content' : {
                    'field' : 'data_format',
                    'value' : 'SVS'
                }
            },
        ]
    }


    params = {
        'filters' : json.dumps(filter),
        'fields' : ','.join(FILE_FIELDS),
        'format' : 'JSON',
        'size' : 100
    }

    response = requests.get(FILES_ENDPOINT, params=params)

    return json.loads(response.content.decode('utf8'))



if __name__ == '__main__':
    args = process_args()
    # print(args)

    cases = get_cases(args)
    # if args.cases_out:
    #     with open(args.cases_out, 'w') as f:
    #         print(json.dumps(cases, indent=2), file=f)
    #
    # if cases['warnings']:
    #     print('NB: warnings returned:')
    #     print(cases['warnings'])
    #
    # print('%i cases returned' % len(cases['data']['hits']))
    #
    # all_slides = []
    # for hit in cases['data']['hits']:
    #     all_slides += hit['slide_ids']
    #
    # print('%i total slides' % len(all_slides))
    #
    # if args.no_files:
    #     print('exiting without query slide files')
    #     sys.exit(0)
    #
    # print('querying slide files')
    #
    # for hit in cases['data']['hits']:
    #     print('#', end='', flush=True)
    #     slides = {}
    #     for slide in hit['slide_ids']:
    #         print('.', end='', flush=True)
    #         slides[slide] = slide_to_files(slide)['data']['hits']
    #
    #     hit['slides'] = slides
    #
    # print()
    outputFile = args.slides_out
    with open(outputFile, 'w') as f:
        print(json.dumps(cases, indent=2), file=f)

    f = open(outputFile,)
    output = json.load(f)

    alive = 0
    dead = 0
    numberOfSlides = 0
    agesAtDiagnosis = []
    timeTillDeath = []
    dict_data = {"data":[]}
    mutation_genes_data = {"case_ids":[]}
    tempSlide = 0
    for i in range(0, len(output["data"]["hits"])):                                                                     # constructing json
        if "slide_ids" in output["data"]["hits"][i]:
            for slide_ids in output["data"]["hits"][i]["slide_ids"]:
                mutation_genes_data["case_ids"].append(slide_ids)
        if "demographic" in output["data"]["hits"][i]:
            if output["data"]["hits"][i]["demographic"]["vital_status"] == "Alive":
                alive+=1
            else:
                dead+=1
        for data in output["data"]["hits"][i]["samples"]:
            patient = {}
            patient["patient_id"] = output["data"]["hits"][i]["id"]
            if "slide_ids" in output["data"]["hits"][i]:
                numberOfSlides+=len(output["data"]["hits"][i]["slide_ids"])

            if "demographic" in output["data"]["hits"][i]:
                if output["data"]["hits"][i]["demographic"]["vital_status"] == "Alive":
                    patient["vital_status"] = "Alive"
                else:
                    patient["vital_status"] = "Dead"
                if "days_to_death" in output["data"]["hits"][i]["demographic"]:
                    if output["data"]["hits"][i]["demographic"]["days_to_death"] is not None:
                        timeTillDeath.append((output["data"]["hits"][i]["demographic"]["days_to_death"]/365))
                        patient["years_to_death"] = (output["data"]["hits"][i]["demographic"]["days_to_death"]/365)

            if "diagnoses" in output["data"]["hits"][i]:
                if "age_at_diagnosis" in output["data"]["hits"][i]["diagnoses"][0]:
                    if output["data"]["hits"][i]["diagnoses"][0]["age_at_diagnosis"] is not None:
                        agesAtDiagnosis.append((output["data"]["hits"][i]["diagnoses"][0]["age_at_diagnosis"]/365))
                        patient["age_at_diagnosis"] = (output["data"]["hits"][i]["diagnoses"][0]["age_at_diagnosis"] / 365)
                if "year_of_diagnosis" in output["data"]["hits"][i]["diagnoses"][0]:
                    patient["year_of_diagnosis"] = output["data"]["hits"][i]["diagnoses"][0]["year_of_diagnosis"]
                if "tumor_stage" in output["data"]["hits"][i]["diagnoses"][0]:
                    patient["tumor_stage"] = output["data"]["hits"][i]["diagnoses"][0]["tumor_stage"]
                if "tissue_or_organ_of_origin" in output["data"]["hits"][i]["diagnoses"][0]:
                    patient["tissue_or_organ_of_origin"] = output["data"]["hits"][i]["diagnoses"][0]["tissue_or_organ_of_origin"]
                if "site_of_resection_or_biopsy" in output["data"]["hits"][i]["diagnoses"][0]:
                    patient["site_of_resection_or_biopsy"] = output["data"]["hits"][i]["diagnoses"][0]["site_of_resection_or_biopsy"]
                if "prior_malignancy" in output["data"]["hits"][i]["diagnoses"][0]:
                    patient["prior_malignancy"] = output["data"]["hits"][i]["diagnoses"][0]["prior_malignancy"]
                if "primary_diagnosis" in output["data"]["hits"][i]["diagnoses"][0]:
                    patient["primary_diagnosis"] = output["data"]["hits"][i]["diagnoses"][0]["primary_diagnosis"]

            sample = data["portions"][0]["slides"][0]
            patient["slides"] = {}
            currentSlideID = sample["slide_id"]
            patient["slides"]["slide_id"] = currentSlideID
            if "slides" in output["data"]["hits"][i]:
                slideData = output["data"]["hits"][i]["slides"][currentSlideID]
                if len(slideData) >= 1:
                    if "file_id" in slideData[0]:
                        fileID = slideData[0]["file_id"]
                        patient["slides"]["file_id"] = fileID
            if "case_id" in output["data"]["hits"][i]:
                patient["slides"]["case_id"] = output["data"]["hits"][i]["case_id"]
            if "percent_stromal_cells" in sample:
                patient["slides"]["percent_stromal_cells"] = sample["percent_stromal_cells"]
            if "section_location" in sample:
                patient["slides"]["section_location"] = sample["section_location"]
            if "percent_tumor_cells" in sample:
                patient["slides"]["percent_tumor_cells"] = sample["percent_tumor_cells"]
            if "number_proliferating_cells" in sample:
                patient["slides"]["number_proliferating_cells"] = sample["number_proliferating_cells"]
            if "percent_eosinophil_infiltration" in sample:
                patient["slides"]["percent_eosinophil_infiltration"] = sample["percent_eosinophil_infiltration"]
            if "percent_inflam_infiltration" in sample:
                patient["slides"]["percent_inflam_infiltration"] = sample["percent_inflam_infiltration"]
            if "percent_neutrophil_infiltration" in sample:
                patient["slides"]["percent_neutrophil_infiltration"] = sample["percent_neutrophil_infiltration"]
            if "percent_lymphocyte_infiltration" in sample:
                patient["slides"]["percent_lymphocyte_infiltration"] = sample["percent_lymphocyte_infiltration"]
            if "percent_granulocyte_infiltration" in sample:
                patient["slides"]["percent_granulocyte_infiltration"] = sample["percent_granulocyte_infiltration"]
            if "percent_necrosis" in sample:
                patient["slides"]["percent_necrosis"] = sample["percent_necrosis"]
            if "percent_normal_cells" in sample:
                patient["slides"]["percent_normal_cells"] = sample["percent_normal_cells"]
            if "percent_monocyte_infiltration" in sample:
                patient["slides"]["percent_monocyte_infiltration"] = sample["percent_monocyte_infiltration"]
            if "percent_tumor_nuclei" in sample:
                patient["slides"]["percent_tumor_nuclei"] = sample["percent_tumor_nuclei"]
            if "submitter_id" in sample:
                patient["slides"]["submitter_id"] = sample["submitter_id"]
            codes = (sample["submitter_id"]).split("-", )
            if codes[0] == "TCGA":
                sampleCode = (codes[3][0:2])
                patient["slides"]["SampleCode"] = sampleCode
                if sampleCode == "01":
                    patient["slides"]["sample_type"] = "Primary Solid Tumor"
                if sampleCode == "06":
                    patient["slides"]["sample_type"] = "Metastatic"
                if sampleCode == "07":
                    patient["slides"]["sample_type"] = "Additional Metastatic"
                if sampleCode == "11":
                    patient["slides"]["sample_type"] = "Solid Tissue Normal"
            dict_data["data"].append(patient)

    if len(agesAtDiagnosis) > 0:                                                                                        # print stats
        print("Alive: " + str(alive) + ", Dead: " + str(dead))
        print("Median age is: " + str(statistics.median(agesAtDiagnosis)))
        q3, q1 = np.percentile(agesAtDiagnosis, [75, 25])
        iqr = q3 - q1
        print("IQR age is: " + str(iqr))
    if len(timeTillDeath) > 0:
        print("Median age till death is: " + str(statistics.median(timeTillDeath)))
    # print(mutation_genes_data)

    with open("reconstructedData.json", 'w') as new_:                                                                        # put data in json
        print(json.dumps(dict_data, indent=2), file=new_)

    with open("case_ids.json", 'w') as case_ids_:                                                                       # put slide IDs in json
        print(json.dumps(mutation_genes_data, indent=2), file=case_ids_)

    f.close()
    new_.close()
    case_ids_.close()
