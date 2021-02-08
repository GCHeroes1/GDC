#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, os.path
import argparse

import json
import requests

import numpy as np
import pandas as pd



CASE_FIELDS = [
    'submitter_id',
    'case_id',
    'consent_type',

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
            'op': '!=',
            'content': {
                'field': 'demographic.vital_status',
                'value': ['Not Reported']
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

# NEW_FILTERS = {
#     "op": "and",
#       "content": [
#         {
#           "op": "in",
#           "content": {
#             "field": "cases.primary_site",
#             "value": [
#               "skin"
#             ]
#           }
#         },
#         {
#           "op": "in",
#           "content": {
#             "field": "occurrence.case.case_id",
#             "value": [
#               "e5bc45ce-8a14-40b5-b9b5-ce45609fef3a",
#               "49f961af-1126-431d-93cd-18941c1738f3",
#               "9817ec15-605a-40db-b848-2199e5ccbb7b",
#               "beab616a-256e-48f3-a458-028897a6138c",
#               "af915978-c5e1-4dd4-ab0e-d2be5ac0ae4f",
#               "449c9d70-d8aa-41d4-beeb-0bbfc73a23d8",
#               "44b5453a-3009-43b9-bc34-71a11a6d5e63",
#               "3429967f-4f77-4894-bf27-c4a22698ca92",
#               "ef608754-3f87-458e-9bcf-4434c54c8c9e",
#               "83d05b9a-f409-4169-bef9-e772d2cfbfaf",
#               "ceb45393-54ee-4801-8c6f-c0aa66e37e60",
#               "590b5e18-d837-4c0e-becf-80520db57c0f",
#               "4a4f5ee9-b588-4357-b058-effbfb53e2c3",
#               "dde0b2be-ea43-4de7-8feb-ccdc073c6978",
#               "46801be1-f035-421f-aae4-81baf3bb8d40",
#               "d781260c-f969-456e-bf16-044dc5b181a4",
#               "b8a1732f-c1cb-4a02-af4f-61b63d3d52df",
#               "1af5d168-a3ff-4648-b195-ede2e7a5ca26",
#               "0a4b780e-8143-4118-ad98-fd2a2a6678c3",
#               "d6283ab0-9019-4ad2-93aa-2e6b39cd9641"
#             ]
#           }
#         }
#       ],
#     }



def process_args():
    ap = argparse.ArgumentParser(description='Get metadata from the GDC.')
    ap.add_argument('-C', '--cases', help='existing JSON file of case query results', default=None)
    ap.add_argument('-O', '--cases_out', help='file to save case query results to', default=None)
    
    ap.add_argument('-N', '--num_cases', help='maximum number of cases to query for', default=50)
    ap.add_argument('-p', '--primary', help='primary site of the case', default='Skin')
    
    ap.add_argument('-x', '--no_files', help='exit without querying slide files', action='store_true')
    ap.add_argument('-n', '--num_slides', help='maximum number of slides to query for', default=None)
    ap.add_argument('-o', '--slides_out', help='file to save slide query results to', default='slides_out.json')

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
    
    cases = get_cases(args)
    if args.cases_out:
        with open(args.cases_out, 'w') as f:
            print(json.dumps(cases, indent=2), file=f)
    
    if cases['warnings']:
        print('NB: warnings returned:')
        print(cases['warnings'])
    
    print('%i cases returned' % len(cases['data']['hits']))
    
    all_slides = []
    for hit in cases['data']['hits']:
        all_slides += hit['slide_ids']
    
    print('%i total slides' % len(all_slides))
    
    if args.no_files:
        print('exiting without query slide files')
        sys.exit(0)
    
    print('querying slide files')
    
    for hit in cases['data']['hits']:
        print('#', end='', flush=True)
        slides = {}
        for slide in hit['slide_ids']:
            print('.', end='', flush=True)
            slides[slide] = slide_to_files(slide)['data']['hits']
        
        hit['slides'] = slides
    
    print()
    
    with open(args.slides_out, 'w') as f:
        print(json.dumps(cases, indent=2), file=f)