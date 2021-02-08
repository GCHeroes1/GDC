#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, os.path
import argparse

import json
import openslide

def process_args():
    ap = argparse.ArgumentParser(description='Convert data from an SVS virtual slide file.')

    ap.add_argument('-x', '--ext', help='export file type (extension)', default='tif')
    ap.add_argument('-a', '--alpha', help='retain image alpha channel', action='store_true')
    ap.add_argument('-c', '--compress', help='compress TIFF output', action='store_true')
    ap.add_argument('-q', '--quality', help='quality for JPEG images', type=int, default=90)
    
    ap.add_argument('-n', '--no_image', help='export properties only', action='store_true')
    ap.add_argument('-o', '--out', help='output image file name', default=None)
    ap.add_argument('-j', '--json', help='output properties file name', default=None)
    
    ap.add_argument('-t', '--thumb', help='export thumbnail rather than full image', action='store_true')
    ap.add_argument('-T', '--thumbsize', help='max size of thumbnail', default=1024)
    
    ap.add_argument('file', help='name of source SVS file')
    
    return ap.parse_args()

if __name__ == '__main__':
    args = process_args()

    if not os.path.isfile(args.file):
        print('%s not found' % args.file)
        sys.exit(0)
    
    print('opening ' + args.file)
    svs = openslide.OpenSlide(args.file)
    
    props = dict(svs.properties)
    
    print('base image size: ' + str(svs.level_dimensions[0]))
    print('magnification: %sx' % props['aperio.AppMag'])
    
    jname = args.json or os.path.splitext(args.file)[0] + '.json'
    print('writing properties to ' + jname)
    with open(jname, 'w') as f:
        print(json.dumps(props, indent=2), file=f)
    
    if args.no_image:
        print('skipping image data')
    else:
        if args.thumb:
            print('loading thumbnail')
            img = svs.get_thumbnail((args.thumbsize,args.thumbsize))
        
            if not args.alpha:
                print('removing alpha channel')
                img = img.convert('RGB')
        
            out = args.out or os.path.splitext(args.file)[0] + '-thumb.' + args.ext
            ext = os.path.splitext(out)[1][1:].lower()
        
            if ext=='tif' and args.compress:
                print('writing compressed TIFF image to: ' + out)
                img.save(out, compression='tiff_deflate')
            elif ext in ['jpg', 'jpeg']:
                print('writing JPEG image to: ' + out)
                img.save(out, quality=args.quality)
            else:
                print('writing image data to: ' + out)
                img.save(out)
        
        else:
        
            print('loading full baseline image data')
            img = svs.read_region((0,0), 0, svs.level_dimensions[0])
        
            if not args.alpha:
                print('removing alpha channel')
                img = img.convert('RGB')
        
            out = args.out or os.path.splitext(args.file)[0] + '.' + args.ext
            ext = os.path.splitext(out)[1][1:].lower()
        
            if ext=='tif' and args.compress:
                print('writing compressed TIFF image to: ' + out)
                img.save(out, compression='tiff_deflate')
            elif ext in ['jpg', 'jpeg']:
                print('writing JPEG image to: ' + out)
                img.save(out, quality=args.quality)
            else:
                print('writing image data to: ' + out)
                img.save(out)
    

