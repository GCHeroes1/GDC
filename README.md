# GDC

Some python code for querying info from GDC and tabulating the results.

## Requirements

Python package requirements can be installed via pip:

```pip install -r requirements```

Note that the requirements file includes `openslide-python` and various dependencies, which are used by the scripts that actually *read* SVS files (currently `convert.py`, `tile.py`, `bulk_tile.py`) but not the other scripts. This depends on a working [OpenSlide](https://openslide.org) install, which is beyond the scope of `pip`. `openslide-python` will still install without the underlying library, it just won't work. If you only want to access the web API this doesn't matter.


## Scripts

* `get_mappings.py`: Trivially queries the GDC API for the endpoint fields. Results are already present in the `cases_mapping.json`, `files_mapping.json` and `annotations_mapping.json`, so you don't need to run this unless you make changes.
* `query.py`: Run a query to get cases for a given primary site (default `Kidney`) that have slide data, and then individually query all the SVS files for those cases. Run with `-h` flag to check command line options (or look at the `process_args` function). Note that the second part (querying files) is pretty slow, since each file is queried in a separate HTTP request.
* `tabulate.py`: Flatten the hierarchical JSON output from `query.py` into a TSV.
* `convert.py`: Convert an SVS image into a TIFF or other common image format. TIFFs can optionally be compressed if `lib_tiff` is installed (it may well not be by default on MacOS).
* `tile.py`: Chop a single SVS file up into non-empty square image tiles.
* `bulk_tile.py`: Tile a bunch of SVS files based on info from the `slides_out.tsv` table output by `tabulate.py`. Doesn't yet support filtering or selection, but you can do this by modifying the input file. (Note that this script is currently more up to date than `tile.py` and offers slightly different options, but it has some behaviour and expectations about configuration that will make no sense anywhere outside the projeect it was written for.)
* `download.sh`: Download the SVS files specified in the `slide_files.txt` output of `tabulate.py`. This may take many hours. It is intended to run unsupervised somewhere off in the ether to which we may have somewhat limited access, which is why it's a shell script.


## Data

* `cases_mapping.json`: Information about data available from the GDC API `cases` endpoint.
* `files_mapping.json`: Information about data available from the GDC API `files` endpoint.
* `annotations_mapping.json`: Information about data available from the GDC API `annotations` endpoint.
