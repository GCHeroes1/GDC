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
                'value': ['Kidney']
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
    ap.add_argument('-p', '--primary', help='primary site of the case', default='Kidney')
    
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
    
    
    
    
