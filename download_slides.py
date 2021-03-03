import requests
import json
import sys
from pathlib import Path

path_to_slides_data = "reconstructedData.json"
endpoint = "https://api.gdc.cancer.gov/data/"

with open(path_to_slides_data, 'r') as f:
    slides_data = json.load(f)

def download_slide(hit_id, slide_id, file_id):
    output_path = f"slides/{hit_id}/{file_id}/"
    Path(output_path).mkdir(parents=True, exist_ok=True)    # create folders if they don't exist

    r = requests.get(endpoint + file_id, stream=True)
    total_length = r.headers.get('content-length')

    with open(output_path + file_id + ".svs", "wb") as f:
        # download progress bar
        if total_length is None: # no content length header
            f.write(r.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in r.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )
                sys.stdout.flush()
            print()


# print(slides_data)

patients = slides_data["data"]  # all slides

for patient in patients:
    patientID = patient["patient_id"]
    data = patient["slides"]
    if "slide_id" not in data:
        print("slide ID for " + patientID + " is missing")
        sys.exit()
    if "case_id" not in data:
        print("case ID for " + patientID + " is missing")
        sys.exit()
    if "file_id" not in data:
        print("file ID for " + patientID + " is missing")
        sys.exit()
    print(f"Getting Slides for case id: " + data["case_id"])
    print(f"    downloading slide with id " + data["slide_id"] + " and file id " + data["file_id"])
    download_slide(data["case_id"], data["slide_id"], data["file_id"])
    sys.exit()
# print()

        # for slide_id in patient["slide_ids"]:
        #     slide_file_images = hit["slides"][slide_id]
        #     for image in slide_file_images:
        #         file_id = image["file_id"]
        #         print(f"    downloading slide with id {slide_id} and file id {file_id}")
        #         download_slide(hit_id, slide_id, file_id)
        #         sys.exit()
        # print()




