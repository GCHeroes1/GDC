#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, os.path
import argparse

import json

import numpy as np
import numpy.random
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
    
#    'slide_ids',
    
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

# TCGA codes -- presumably only a *tiny* subset of these will actually occur in the Kidney data
SAMPLE_TYPES = {
    '01' : 'Primary Solid Tumor',
    '02' : 'Recurrent Solid Tumor',
    '03' : 'Primary Blood-Derived Peripheral',
    '04' : 'Recurrent Blood-Derived Marrow',
    '05' : 'Additional New Primary',
    '06' : 'Metastatic',
    '07' : 'Additional Metastatic',
    '08' : 'Human Tumor Original Cells',
    '09' : 'Primary Blood-Derived Marrow',
    '10' : 'Blood-Derived Normal',
    '11' : 'Solid Tissue Normal',
    '12' : 'Buccal Cell Normal',
    '13' : 'EBV Immortalized Normal',
    '14' : 'Bone Marrow Normal',
    '20' : 'Control Analyte',
    '40' : 'Recurred Blood-Derived Peripheral',
    '50' : 'Cell Lines',
    '60' : 'Primary Xenograft Tissue',
    '61' : 'Cell Line Derived Xenograft Tissue'
}


def process_args():
    ap = argparse.ArgumentParser(description='Get metadata from the GDC.')
    ap.add_argument('-s', '--src', help='file to read slide query results from', default='slides_out.json')
    ap.add_argument('-o', '--out', help='file to save tabulated data to', default='slides_out.tsv')
    ap.add_argument('-f', '--files', help='file to save a minimal file list to', default='slide_files.txt')
    ap.add_argument('-l', '--limit', help='maximum number of files to include', default=None)

    return ap.parse_args()

def dot_path_get(xx, path, subst):
    try:
        for pp in path.split('.'):
            xx = xx.get(pp, '')
        return xx
    except AttributeError:
        return subst

def flatten_case(case):
    return {
        'case_id' : case.get('case_id', ''),
        'primary_site' : case.get('primary_site', ''),
        'case_state' : case.get('state', ''),
        'disease_type' : case.get('disease_type', ''),
        'consent_type': case.get('consent_type', ''),
        
        'vital_status' : dot_path_get(case, 'demographic.vital_status', None),
        'ethnicity' : dot_path_get(case, 'demographic.ethnicity', None),
        'race' : dot_path_get(case, 'demographic.race', None),
        'gender' : dot_path_get(case, 'demographic.gender', None),
        'year_of_birth' : dot_path_get(case, 'demographic.year_of_birth', None),
        'year_of_death' : dot_path_get(case, 'demographic.year_of_death', None),
        'days_to_death' : dot_path_get(case, 'demographic.days_to_death', None),
        'cause_of_death' : dot_path_get(case, 'demographic.cause_of_death', None),
        
        'diagnoses_count' : len(case.get('diagnoses', [])),
        
        'primary_diagnosis' : case.get('diagnoses', [{}])[0].get('primary_diagnosis', None),
        'tumor_stage' : case.get('diagnoses', [{}])[0].get('tumor_stage', None),
        'site_of_resection_or_biopsy' : case.get('diagnoses', [{}])[0].get('site_of_resection_or_biopsy', None),
        'prior_malignancy' : case.get('diagnoses', [{}])[0].get('prior_malignancy', None),
        'classification_of_tumor' : case.get('diagnoses', [{}])[0].get('classification_of_tumor', None),
        'tissue_or_organ_of_origin' : case.get('diagnoses', [{}])[0].get('tissue_or_organ_of_origin', None),
        'year_of_diagnosis' : case.get('diagnoses', [{}])[0].get('year_of_diagnosis', None),
        'morphology' : case.get('diagnoses', [{}])[0].get('morphology', None),
        'days_to_diagnosis' : case.get('diagnoses', [{}])[0].get('days_to_diagnosis', None),
        
        'cog_renal_stage' : case.get('diagnoses', [{}])[0].get('cog_renal_stage', None),
        'laterality' : case.get('diagnoses', [{}])[0].get('laterality', None),
        'metastasis_at_diagnosis' : case.get('diagnoses', [{}])[0].get('metastasis_at_diagnosis', None),
        'method_of_diagnosis' : case.get('diagnoses', [{}])[0].get('method_of_diagnosis', None),
        'mitotic_count' : case.get('diagnoses', [{}])[0].get('mitotic_count', None),
        'papillary_renal_cell_type' : case.get('diagnoses', [{}])[0].get('papillary_renal_cell_type', None),
        'percent_tumor_invasion' : case.get('diagnoses', [{}])[0].get('percent_tumor_invasion', None),
        'sites_of_involvement' : case.get('diagnoses', [{}])[0].get('sites_of_involvement', None),
    }

def flatten_annotations(ans):
    return '|'.join([ '%s,%s,%s' % ( a.get('classification', ''),
                                     a.get('category', ''),
                                     a.get('notes', '') ) for a in ans ])

def barcodes(name):
    barcode, sample_type, normal, vial, portion, slide_code = None, None, None, None, None, None
    if name.startswith('TCGA'):
        barcode = name.split('.')[0]
        frags = barcode.split('-')
        
        if len(frags) > 3:
            sample_type = SAMPLE_TYPES.get(frags[3][:2], frags[3][:2])
            vial = frags[3][2:]
            normal = 1 if frags[3].startswith('1') else 0
        
        if len(frags) > 4: portion = frags[4]
        if len(frags) > 5: slide_code = frags[5]
    
    return {
        'barcode' : barcode,
        'sample_type' : sample_type,
        'normal' : normal,
        'vial' : vial,
        'portion' : portion,
        'slide_code' : slide_code,
    }    
            

def flatten_file(ff, slide_id):
    return {
        'slide_id' : slide_id,
        'file_id' : ff.get('file_id', ''),
        'type' : ff.get('type', None),
        'state' : ff.get('state', None),
        'created' : ff.get('created_datetime', None),
        'updated' : ff.get('updated_datetime', None),
        'access' : ff.get('access', ''),
        'data_type' : ff.get('data_type', None),
        'data_category' : ff.get('data_category', None),
        'file_name': ff.get('file_name', ''),
        'file_size': ff.get('file_size', ''),
        'imaging_date': ff.get('imaging_date', None),
        'magnification': ff.get('magnification', None),
        
        'annotations': flatten_annotations(ff.get('annotations', [])),
        
        ** barcodes(ff.get('file_name', ''))
    }

if __name__ == '__main__':
    args = process_args()
    
    with open(args.src) as f:
        src = json.load(f)
    
    print('%i cases' % len(src['data']['hits']))
    
    result = []
    
    halt = False
    
    for case in src['data']['hits']:
        if halt: break
        base = flatten_case(case)
        for slide_id in case['slides']:
            if halt: break
            for ff in case['slides'][slide_id]:
                flat = flatten_file(ff, slide_id)
                result.append({**base, **flat})
            
                if args.limit and (len(result) >= args.limit):
                    halt = True
                    break
    
    df = pd.DataFrame(result)
    df.dropna(axis=1, how='all', inplace=True)
    
    for col in df.columns:
        # force int types -- cosmetic but annoying
        if col.startswith('year') or col.startswith('day'):
            df[col] = pd.to_numeric(df[col], errors='coerce', downcast='integer')
            df[col] = df[col].astype('Int64')
    
    df.to_csv(args.out, sep='\t')
    
    dff = df[['file_id', 'file_name', 'file_size']].copy()
    dff.drop_duplicates(subset='file_id', inplace=True, ignore_index=True)
    dff.sort_values(by='file_size', inplace=True, ignore_index=True)
    dff.to_csv(args.files, header=False, index=False, sep='\t')
    
    print('%i files' % dff.shape[0])
    
                
    