import openslide
from openslide import deepzoom
from image_processing import calculate_tissue_percentage
# import multiprocessing
from tqdm import tqdm
from concurrent import futures
import os

# def slice_image_parallel(slide_path: openslide, tile_size: int, level: int, tissue_threshold_percentage: int):
# 	slide = deepzoom.DeepZoomGenerator(openslide.OpenSlide(slide_path), tile_size=tile_size, overlap=1)
# 	tiles_info_per_level = slide.level_tiles
# 	number_of_levels = len(tiles_info_per_level)
# 	number_of_widths, number_of_heights = tiles_info_per_level[number_of_levels - 1 - level]
# 	print(f"level dimensions: {slide.level_dimensions}")
# 	print(f"tile dimensions: {slide.get_tile_dimensions(17, (29,0))}")
# 	print(f"Number of widths: {number_of_widths}")
# 	print(f"Number of heights: {number_of_heights}")
# 	print(f"number of levels: {number_of_levels}")
# 	counter = 0
# 	total_slides = number_of_heights * number_of_widths
# 	print(f"total slides: {total_slides}")
# 	jobs_instructions = list()
# 	for width_index in range(number_of_widths):
# 		width = width_index * tile_size
# 		for height_index in range(number_of_heights):
# 			height = height_index * tile_size
# 			jobs_instructions.append(
# 					(slide_path, counter, width, height, tile_size, tile_size, level, tissue_threshold_percentage))
# 			counter += 1
#
#
# 	p_bar = tqdm(total=len(jobs_instructions))
# 	with futures.ThreadPoolExecutor(max_workers=8) as executor:
# 		futures_to_jobs = {executor.submit(classify_tile, job): job for job in jobs_instructions}
# 		for _ in futures.as_completed(futures_to_jobs):
# 			p_bar.update(1)
# 			p_bar.refresh()

# x, y are the tile's top right corner coordinates
def classify_tile(arguments):
	slide_path, tile_number, x, y, tile_width, tile_height, level, tissue_threshold_percentage = arguments
	slide_rename_me = openslide.OpenSlide(slide_path)
	tile = slide_rename_me.read_region((x, y), level, (tile_width, tile_height))
	tissue_percentage = calculate_tissue_percentage(tile)
	if tissue_percentage > tissue_threshold_percentage:
		# print(f'tile number {tile_number} with percentage {tissue_percentage} is being saved as tile{tile_number}.png')
		tile.save(f'tiles/tile{tile_number}.png')


def slice_image_parallel2(slide_path: openslide, tile_size_: int, level: int, tissue_threshold_percentage: int, output_folder: str):
	slide_ = deepzoom.DeepZoomGenerator(openslide.OpenSlide(slide_path), tile_size=tile_size_, overlap=1)
	tiles_info_per_level = slide_.level_tiles
	number_of_levels = len(tiles_info_per_level)
	number_of_widths, number_of_heights = tiles_info_per_level[level]
	print(f"level dimensions: {slide_.level_dimensions}")
	print(f"tile dimensions: {slide_.get_tile_dimensions(17, (29,0))}")
	print(f"Number of widths: {number_of_widths}")
	print(f"Number of heights: {number_of_heights}")
	print(f"number of levels: {number_of_levels}")
	counter = 0
	total_slides = number_of_heights * number_of_widths
	print(f"total slides: {total_slides}")
	jobs_instructions = list()
	for width_index in range(number_of_widths):
		# width = width_index * tile_size_
		for height_index in range(number_of_heights):
			# height = height_index * tile_size_
			jobs_instructions.append(
					(slide_path, counter, width_index, height_index, tile_size_, level, tissue_threshold_percentage, output_folder))
			counter += 1

	p_bar = tqdm(total=len(jobs_instructions))
	with futures.ThreadPoolExecutor(max_workers=8) as executor:
		futures_to_jobs = {executor.submit(classify_tile2, job): job for job in jobs_instructions}
		for _ in futures.as_completed(futures_to_jobs):
			p_bar.update(1)
			p_bar.refresh()

def classify_tile2(arguments):
	slide_path, tile_number, x, y, tile_size_, level, tissue_threshold_percentage, output_folder = arguments
	slide_ = deepzoom.DeepZoomGenerator(openslide.OpenSlide(slide_path), tile_size=tile_size_, overlap=1)
	tile = slide_.get_tile(level, (x, y))
	tissue_percentage = calculate_tissue_percentage(tile)
	if tissue_percentage > tissue_threshold_percentage:
		tile.save(os.path.join(output_folder, f"tile{tile_number}.png"))


# sample_image_path: str = '71208712-2893-4404-9cef-ff090774d057/71208712-2893-4404-9cef-ff090774d057.svs'
sample_image_path: str = './71208712-2893-4404-9cef-ff090774d057.svs'

tile_size = 1000

# explore image to find out how many levels there are, and decide which is best to use. Once decided, the code below can be commented out
slide = deepzoom.DeepZoomGenerator(openslide.OpenSlide(sample_image_path), tile_size=tile_size, overlap=1)
level_dimensions = slide.level_dimensions
number_of_levels = len(level_dimensions)
print(f"level image dimensions: {level_dimensions}")
print(f"number of levels: {number_of_levels} ")
print(f'Highest quality level: {number_of_levels - 1}')
print(f'Lowest quality level: {0}')

# perform slicing
slice_image_parallel2(sample_image_path, tile_size, 14, 50, 'tiles')
