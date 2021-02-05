#!/bin/bash
while IFS=$'\t' read -r fileid filename filesize; do
    if [ -f "$filename" ];
    then
        echo $filename already exists
    else
        echo attempting to download $filename
        curl -OJ https://api.gdc.cancer.gov/data/$fileid
        break
    fi
done < slide_files.txt
