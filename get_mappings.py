import requests
import json

for endpt in [ 'cases', 'files', 'annotations']:
    response = requests.get('https://api.gdc.cancer.gov/%s/_mapping' % endpt)
    with open ('%s_mapping.json' % endpt, 'w') as f:
        print(json.dumps(json.loads(response.content.decode('utf8')), indent=2), file=f)

