from PIL import Image
import openslide

# NOTE: Before starting, use "download_slides.py" to download an svs image

# SET TISSUE PIXELS AS BLACK, RETURNS NEW IMAGE
def label_non_whitespace(img):
    img = img.copy().convert("L")  # convert to greyscale
    for x in range(img.width):
        for y in range(img.height):
            if (img.getpixel((x,y)) < 210):    # threshold value can be played around with 
                img.putpixel((x,y), 0)
    return img
            
# threshold (optional) for pixels number of pixels that should be tissue
def calculate_tissue_percentage(img, threshold=None):
    img = img.convert("L")   # convert to greyscale
    # img = img.copy().convert("L")
    tissue_pixels = 0
    non_tissue_pixels = 0
    total_pixels = img.width * img.height
    for x in range(img.width):
        for y in range(img.height):
            if (img.getpixel((x,y)) < 210):     # threshold value can be played around with
                tissue_pixels += 1
            else:
                non_tissue_pixels += 1
            if (threshold is not None and (((tissue_pixels / total_pixels) * 100 > threshold) or ((non_tissue_pixels/total_pixels) * 100 > threshold))):
                return 200
    return (tissue_pixels / total_pixels) * 100




# READ IN SVS, READ A REGION OF IT AND SAVE IT. ONLY NEEDS TO BE DONE ONCE, THEN COMMENT IT OUT
# slide = openslide.OpenSlide("./slides/9817ec15-605a-40db-b848-2199e5ccbb7b/71208712-2893-4404-9cef-ff090774d057/71208712-2893-4404-9cef-ff090774d057.svs")
# width, height = slide.dimensions
# print(f"slide dimensions: {slide.dimensions}")
# print(f"level count: {slide.level_count}")
# print(f"level dimensions: {slide.level_dimensions}")
# img_svs = slide.read_region((10000,17000), 0, (5000, 5000))     # arbitrarily chosen values, chosen to test different image sizes and regions of the image
# img_svs.save("svs_image.png")


# READ IN PNG, SAVED USING ABOVE CODE. THEN USE IT TO TEST STUFF
# img_svs = Image.open("svs_image.png")
# labeled_img = label_non_whitespace(img_svs) 
# labeled_img.save("svs_image_modified.png")
# print(calculate_tissue_percentage(img_svs))
