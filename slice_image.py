from PIL import Image
import openslide
from openslide import deepzoom
from image_processing import calculate_tissue_percentage
import multiprocessing
import tqdm

sample_image_path: str = './71208712-2893-4404-9cef-ff090774d057/71208712-2893-4404-9cef-ff090774d057.svs'

multiprocessing.set_start_method("fork")

def slice_image(slide: openslide, tile_height: int, tile_width: int):
    slide_width, slide_height = slide.dimensions
    print("starting image slicing")
    number_of_widths = slide_width // tile_width
    number_of_heights = slide_height // tile_height
    print(f'Number of widths: {number_of_widths}')
    print(f'Number of heights: {number_of_heights}')
    counter = 0
    progress_counter = 0
    total_slides = number_of_heights * number_of_widths
    print(f'total slides to go through: {total_slides}')
    for width_index in range(number_of_widths):
        width = width_index * tile_width
        for height_index in range(number_of_heights):
            height = height_index * tile_height
            # print("creating tile")
            # print(f'top left corner: ({width}, {height}), bottom right corner: ({width + tile_width}, {height + tile_height})')
            tile = slide.read_region((width, height), 3, (tile_width, tile_height))
            tissue_percentage = calculate_tissue_percentage(tile, threshold=50)
            print(f'checking slice {progress_counter} / {total_slides}')
            if tissue_percentage > 50:
                print(f'tissue with percentage {tissue_percentage} is being saved as tile{counter}.png')
                tile.save(f'tiles/tile{counter}.png')
                counter += 1
            else:
                print(f'tissue with percentage {tissue_percentage} is TOO LOW to be useful')
            print()
            progress_counter += 1


def slice_image_parallel(slide_path: openslide, tile_height: int, tile_width: int, tissue_threshold_percentage: int):
    slide = openslide.OpenSlide(slide_path)
    slide_width, slide_height = slide.dimensions
    print("starting image slicing")
    number_of_widths = slide_width // tile_width
    number_of_heights = slide_height // tile_height
    print(f'Number of widths: {number_of_widths}')
    print(f'Number of heights: {number_of_heights}')
    counter = 0
    progress_counter = 0
    total_slides = number_of_heights * number_of_widths
    jobs_instructions = list()
    for width_index in range(number_of_widths):
        width = width_index * tile_width
        for height_index in range(number_of_heights):
            height = height_index * tile_height
            jobs_instructions.append((slide_path, counter, width, height, tile_width, tile_height, tissue_threshold_percentage))
            counter += 1
            # print("creating tile")
            # print(f'top left corner: ({width}, {height}), bottom right corner: ({width + tile_width}, {height + tile_height})')
            
    pool = multiprocessing.Pool(processes=10)
    for _ in tqdm.tqdm(pool.imap(classify_tile, jobs_instructions), total=len(jobs_instructions)):
        pass
    pool.close()


def slice_image_parallel2(slide_path: openslide, tile_height: int, tile_width: int, tissue_threshold_percentage: int):
    slide = deepzoom.DeepZoomGenerator(openslide.OpenSlide(slide_path), tile_size=5000, overlap=1)
    tiles_info_per_level = slide.level_tiles
    number_of_levels = len(tiles_info_per_level)
    number_of_widths, number_of_heights = tiles_info_per_level[number_of_levels - 1]
    print(f'Number of widths: {number_of_widths}')
    print(f'Number of heights: {number_of_heights}')
    counter = 0
    progress_counter = 0
    total_slides = number_of_heights * number_of_widths
    jobs_instructions = list()
    for width_index in range(number_of_widths):
        width = width_index * tile_width
        for height_index in range(number_of_heights):
            height = height_index * tile_height
            jobs_instructions.append((slide_path, counter, width, height, tile_width, tile_height, tissue_threshold_percentage))
            counter += 1
            # print("creating tile")
            # print(f'top left corner: ({width}, {height}), bottom right corner: ({width + tile_width}, {height + tile_height})')
            
    pool = multiprocessing.Pool(processes=4)
    for _ in tqdm.tqdm(pool.imap(classify_tile, jobs_instructions), total=len(jobs_instructions)):
        pass
    pool.close()


# x, y are the tile's top right corner coordinates
def classify_tile(arguments):
    slide_path, tile_number, x, y, tile_width, tile_height, tissue_threshold_percentage = arguments
    slide = openslide.OpenSlide(slide_path)
    # print(f'path: {slide_path}, tile number: {tile_number}, x: {x}, y: {y}, tile width: {tile_width}, tile height: {tile_height}')
    tile = slide.read_region((x, y), 2, (tile_width, tile_height))
    tissue_percentage = calculate_tissue_percentage(tile, threshold=tissue_threshold_percentage)
    if tissue_percentage > tissue_threshold_percentage:
        # print(f'tile number {tile_number} with percentage {tissue_percentage} is being saved as tile{tile_number}.png')
        tile.save(f'tiles/tile{tile_number}.png')
    # else:
        # print(f'tile number {tile_number} with percentage {tissue_percentage} is TOO LOW to be useful')
    # print()



# READ IN SVS, READ A REGION OF IT AND SAVE IT. ONLY NEEDS TO BE DONE ONCE, THEN COMMENT IT OUT
slide = openslide.OpenSlide(sample_image_path)
width, height = slide.dimensions
print(f"slide dimensions: {slide.dimensions}")
print(f"level count: {slide.level_count}")
print(f"level dimensions: {slide.level_dimensions}") 
# slice_image_parallel(sample_image_path, 3000, 3000, 50)
# slice_image(slide, 3000, 3000)
slice_image_parallel2(sample_image_path, 3000, 3000, 50)
# img_svs.save("svs_image.png")

# img2 = openslide.open_slide(sample_image_path)
# print(img2.dimensions)
# # img2 = img2.read_region((0, 0), 2, (20000, 20000))
# # img2.show()
# print()
# zoom = deepzoom.DeepZoomGenerator(img2, tile_size=5000, overlap=1)
# tiles_info_per_level = zoom.level_tiles
# number_of_levels = len(tiles_info_per_level)
# print(tiles_info_per_level)
# print()
# max_x, max_y = tiles_info_per_level[number_of_levels - 1]
# counter = 1
# print(f'number of images to check: {max_x * max_y}')
# for x in range(max_x):
#     for y in range(max_y):
#         print(f'checking image {counter}')
#         zoom_img = zoom.get_tile(number_of_levels - 1, (x,y))
#         # if calculate_tissue_percentage(zoom_img) > 50:
#         #     zoom_img.show()
#         # counter += 1
#         zoom_img.show()
