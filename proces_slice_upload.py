from random import random
import requests
import json
import subprocess
import os
from tqdm import tqdm
import concurrent.futures
import tempfile
import openslide
from openslide import deepzoom
from image_processing import calculate_tissue_percentage
from concurrent import futures

# from slice_image import classify_tile, slice_image_parallel2, classify_tile2

path_to_slides_data = "reconstructedData.json"
endpoint = "https://api.gdc.cancer.gov/data/"
f = open(path_to_slides_data, )
output = json.load(f)


# x, y are the tile's top right corner coordinates
def classify_tile(arguments):
    slide_path, tile_number, x, y, tile_width, tile_height, level, tissue_threshold_percentage = arguments
    slide_rename_me = openslide.OpenSlide(slide_path)
    tile = slide_rename_me.read_region((x, y), level, (tile_width, tile_height))
    tissue_percentage = calculate_tissue_percentage(tile)
    if tissue_percentage > tissue_threshold_percentage:
        # print(f'tile number {tile_number} with percentage {tissue_percentage} is being saved as tile{tile_number}.png')
        tile.save(f'tiles/tile{tile_number}.png')


def slice_image_parallel2(slide_path: str, tile_size_: int, level: int, tissue_threshold_percentage: int,
                          output_folder: str, path_to_upload, file_id):
    slide_ = deepzoom.DeepZoomGenerator(openslide.open_slide(slide_path), tile_size=tile_size_, overlap=1)
    tiles_info_per_level = slide_.level_tiles
    number_of_levels = len(tiles_info_per_level)
    number_of_widths, number_of_heights = tiles_info_per_level[level]
    # print(f"level dimensions: {slide_.level_dimensions}")
    # print(f"tile dimensions: {slide_.get_tile_dimensions(17, (29, 0))}")
    # print(f"Number of widths: {number_of_widths}")
    # print(f"Number of heights: {number_of_heights}")
    # print(f"number of levels: {number_of_levels}")
    counter = 0
    total_slides = number_of_heights * number_of_widths
    # print(f"total slides: {total_slides}")
    jobs_instructions = list()
    for width_index in range(number_of_widths):
        # width = width_index * tile_size_
        for height_index in range(number_of_heights):
            # height = height_index * tile_size_
            jobs_instructions.append(
                    (slide_path, counter, width_index, height_index, tile_size_, level, tissue_threshold_percentage,
                     output_folder, path_to_upload, file_id))
            counter += 1

    p_bar = tqdm(total=len(jobs_instructions))
    with futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures_to_jobs = {ex.submit(classify_tile_rclone, job): job for job in jobs_instructions}
        for _ in futures.as_completed(futures_to_jobs):
            p_bar.update(1)
            p_bar.refresh()


def classify_tile_rclone(arguments):
    if not os.path.exists("./_tmp"):
        os.makedirs("./_tmp")
    temporary_file = tempfile.NamedTemporaryFile(dir="./_tmp")

    slide_path, tile_number, x, y, tile_size_, level, tissue_threshold_percentage, output_folder, path_to_upload, file_id = arguments
    slide_ = deepzoom.DeepZoomGenerator(openslide.OpenSlide(slide_path), tile_size=tile_size_, overlap=1)
    tile = slide_.get_tile(level, (x, y))
    tissue_percentage = calculate_tissue_percentage(tile)
    if tissue_percentage > tissue_threshold_percentage:
        # tile.save(os.path.join(output_folder, f"tile{tile_number}.png"))
        tile.save(temporary_file, "png")
        # print(path_to_upload)
        subprocess.run(["/home/rajesh/Downloads/rclone-v1.54.0-linux-amd64/rclone", "copyto", temporary_file.name,
                        f"GCDData:/FinalData/{path_to_upload}{file_id}_{tile_number}.png", "-q", "--transfers=1"])


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
        if patient["biopsy_tissue_type"] in ["Lymph", "Skin"]:
            output_list.append((data["case_id"], data["slide_id"], data["file_id"]))
    return output_list


def locate_field(file_id, field):
    for patient in output["data"]:
        if file_id == patient["slides"]["file_id"]:
            return patient[field]


def upload_path(tissue_type, years_survived):
    randomNumber = random()

    if randomNumber < 0.8:
        if tissue_type == "Skin":
            if years_survived <= 3:
                return "skin_train_dir/early/"
            else:
                return "skin_train_dir/late/"
        elif tissue_type == "Lymph":
            if years_survived <= 3:
                return "lymph_train_dir/early/"
            else:
                return "lymph_train_dir/late/"
        else:
            return 0
    else:
        if tissue_type == "Skin":
            if years_survived <= 3:
                return "skin_validation_dir/early/"
            else:
                return "skin_validation_dir/late/"
        elif tissue_type == "Lymph":
            if years_survived <= 3:
                return "lymph_validation_dir/early/"
            else:
                return "lymph_validation_dir/late/"
        else:
            return 0


def download_slide(file_id):
    if not os.path.exists("./_tmp"):
        os.makedirs("./_tmp")
    temporary_file = tempfile.NamedTemporaryFile(dir="./_tmp")

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
    tile_size = 1000

    biopsy_tissue_type = locate_field(file_id, "biopsy_tissue_type")
    years_survived = locate_field(file_id, "years_survived")
    path_to_upload = upload_path(biopsy_tissue_type, years_survived)
    # print(path_to_upload)

    if path_to_upload == 0:
        return

    slide_temp_file = download_slide(file_id)
    slide_file = slide_temp_file.name
    # print("got here")
    slice_image_parallel2(slide_file, tile_size, 14, 50, 'tiles', path_to_upload, file_id)

    # subprocess.run(["rclone", "copyto", slide_file.name, f"GCDData:/Data/{file_id}.svs", "-q", "--transfers=1"])
    # subprocess.run(["/home/rajesh/Downloads/rclone-v1.54.0-linux-amd64/rclone", "copyto", slide_file.name, f"GCDData:/Test/{file_id}.svs", "-q", "--transfers=1"])
    slide_temp_file.close()


if __name__ == "__main__":
    # list of tuples. each tuple contains case_id, slide_id, and file_id
    slides = fetch_slides(path_to_slides_data)

    # for slide_meta in slides:
    #     download_and_upload(slide_meta[2])

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_slide = {executor.submit(download_and_upload, slide_meta[2]): slide_meta for slide_meta in slides}
        pbar = tqdm(total=len(future_to_slide))
        for future in concurrent.futures.as_completed(future_to_slide):
            print(future.result())
            pbar.update(1)
            pbar.refresh()
