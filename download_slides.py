import requests
import json
import subprocess
import os
from tqdm import tqdm
import concurrent.futures
import tempfile

path_to_slides_data = "reconstructedData.json"
endpoint = "https://api.gdc.cancer.gov/data/"


def fetch_slides(slides_path):
    output_list = []
    with open(slides_path, 'r') as infile:
        slides_data = json.load(infile)

    patients = slides_data["data"]  # all slides
    for patient in patients:
        patient_id = patient["patient_id"]
        data = patient["slides"]
        if "slide_id" not in data:
            print("slide ID for " + patient_id + " is missing")
            continue
        if "case_id" not in data:
            print("case ID for " + patient_id + " is missing")
            continue
        if "file_id" not in data:
            print("file ID for " + patient_id + " is missing")
            continue
        output_list.append((data["case_id"], data["slide_id"], data["file_id"]))
    return output_list


def download_slide(file_id):
    if not os.path.exists("./_tmp"):
        os.makedirs("./_tmp")
    temporary_file = tempfile.NamedTemporaryFile(dir="./_tmp")
    # output_path = f"slides/{hit_id}/{file_id}/"
    # Path(output_path).mkdir(parents=True, exist_ok=True)  # create folders if they don't exist

    r = requests.get(endpoint + file_id, stream=True)
    total_length = r.headers.get('content-length')

    if total_length is None:  # no content length header
        temporary_file.write(r.content)
    else:
        chunk_size = 1024 * 1024
        for content_chunk in r.iter_content(chunk_size=chunk_size):
            temporary_file.write(content_chunk)

    return temporary_file


def download_and_upload(file_id):
    slide_file = download_slide(file_id)

    subprocess.run(["rclone", "copyto", slide_file.name, f"GCDData:{file_id}.svs", "-q", "--transfers=1"])
    slide_file.close()


if __name__ == "__main__":
    # list of tuples. each tuple contains case_id, slide_id, and file_id
    slides = fetch_slides(path_to_slides_data)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        future_to_slide = {executor.submit(download_and_upload, slide_meta[2]): slide_meta for slide_meta in slides}
        pbar = tqdm(total=len(future_to_slide))
        for future in concurrent.futures.as_completed(future_to_slide):
            pbar.update(1)
            pbar.refresh()
            # slide_meta = future_to_slide[future]
            # print(f"Done downloading and uploading file {slide_meta[2]}")
            # slide_file = future.result()
            # print(f"Downloaded {slide_meta[2]}")
            # try:
            #     # replace f"local:tempdir/Data/slides/{slide_meta[0]}/{slide_meta[2]}.svs" with the actual path you
            #     # want to take. For example, f"GCDData:/Data/slides/{slide_meta[0]}/{slide_meta[2]}". Up to you.
            #
            #     # also, I'm pretty sure your previous file naming scheme was wrong, it never used slide_id and only
            #     # used file_id. It also created a directory called file_id despite the filename _also_ being file_id
            #
            #     print(f"Uploaded {slide_meta[2]}")
            # noinspection PyBroadException
            # except:
            #     print("shit")