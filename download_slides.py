import requests
import json
import sys
from pathlib import Path
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
import shutil
# import rclone
import subprocess
from tqdm import tqdm

# cfg_path = "rclone.conf"
# with open(cfg_path) as f:
#    cfg = f.read()
# print(cfg)
# result = rclone.with_config(cfg).listremotes()
# print(result)
# result.listremotes()
# print(result.get('out'))
# result.run_cmd("rclone config")

# cfg = """[local]
# type = local
# nounc = true"""
# result = rclone.with_config(cfg).listremotes()

# print(result.get('code'))

path_to_slides_data = "reconstructedData.json"
endpoint = "https://api.gdc.cancer.gov/data/"

with open(path_to_slides_data, 'r') as f:
    slides_data = json.load(f)

def download_slide(hit_id, slide_id, file_id):
    output_path = f"slides/{hit_id}/{file_id}/"
    Path(output_path).mkdir(parents=True, exist_ok=True)  # create folders if they don't exist

    r = requests.get(endpoint + file_id, stream=True)
    total_length = r.headers.get('content-length')

    with open(output_path + file_id + ".svs", "wb") as f:
        if total_length is None:  # no content length header
            f.write(r.content)
        else:
            chunk_size = 1024 * 1024
            for content_chunk in tqdm(r.iter_content(chunk_size=chunk_size), total=int(total_length)//chunk_size):
                f.write(content_chunk)

# print(slides_data)

patients = slides_data["data"]  # all slides
x = 0
for patient in patients:
    patientID = patient["patient_id"]
    data = patient["slides"]
    case_id = data["case_id"]
    file_id = data["file_id"]
    if "slide_id" not in data:
        print("slide ID for " + patientID + " is missing")
        continue
    if "case_id" not in data:
        print("case ID for " + patientID + " is missing")
        continue
    if "file_id" not in data:
        print("file ID for " + patientID + " is missing")
        continue
    print(f"Getting Slides for case id: " + case_id)
    print(f"    downloading slide with id " + data["slide_id"] + " and file id " + file_id)
    download_slide(case_id, data["slide_id"], file_id)

    filepath = "slides/" + case_id + "/" + file_id + "/"
    filename = filepath + file_id + ".svs"
    rclone_path = "/home/rajesh/Downloads/rclone-v1.54.0-linux-amd64/rclone"
    data_path = "/home/rajesh/Documents/Year_3/COMP0031/gdc/" + filename
    print(data_path)

    subprocess.run([rclone_path, "copy", data_path, "GCDData:/Data", "-Pv", "--max-size", "1M", "--transfers=16"])

    # gfile.SetContentFile(filename)
    # gfile.Upload()
    # print(filename)

    if os.path.exists(filename):
        # print("yep it exists")
        shutil.rmtree("slides")
    else:
        print("file dont exist m8")
    # sys.exit()
    x+=1
    print("i have done this for the " + str(x) + " time")

