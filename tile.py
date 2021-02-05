#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, os.path
import argparse

import numpy as np
import imageio

import json
import openslide

def process_args():
    ap = argparse.ArgumentParser(description='Cut an SVS virtual slide file into tiles.')

    ap.add_argument('-s', '--size', help='size of tiles to create', type=int, default=512)
    
    ap.add_argument('-o', '--out', help='output directory', default=None)

    ap.add_argument('-x', '--ext', help='export file type (extension)', default='tif')
    ap.add_argument('-q', '--quality', help='export quality for JPG images', type=int, default=90)
    
    ap.add_argument('-l', '--limit', help='max tiles to create', type=int, default=None)
    
    # acceptance heuristics
    ap.add_argument('-d', '--std', help='min SD as frac of whole image SD', type=float, default=None)
    ap.add_argument('-a', '--avg', help='max mean as frac of whole image mean', type=float, default=None)
    ap.add_argument('-c', '--count', help='min pixels below threshold', type=int, default=None)
    ap.add_argument('-t', '--thresh', help='highest pixel value considered non-background', default=200)
    
    ap.add_argument('file', help='name of source SVS file')
    
    return ap.parse_args()

def accept(patch, args, stats):
    if args.std is not None:
        if np.std(patch) >= args.std * stats['std']:
            return True
    
    if args.avg is not None:
        if np.mean(patch) <= args.avg * stats['mean']:
            return True
    
    if args.count is not None:
        if np.sum(patch <= args.thresh) >= args.count:
            return True
    
    return False


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
    
    outdir = args.out or os.path.splitext(args.file)[0] + '-tiles-' + str(args.size)
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    
    print('loading & converting pixel data')
    im = np.array(svs.read_region((0,0), 0, svs.level_dimensions[0]).convert('RGB'))
    
    print(f'image shape: {im.shape}, dtype: {im.dtype}')
    
    stats = { 'mean' : np.mean(im), 'std' : np.std(im) }
    count = 0
    for top in range(0, im.shape[0], args.size):
        bottom = min(im.shape[0], top + args.size)
        
        for left in range(0, im.shape[1], args.size):
            right = min(im.shape[1], left + args.size)
            
            patch = im[top:bottom, left:right, :]
            if accept(patch, args, stats):
                patchname = f'tile-{left}-{top}-{right}-{bottom}.{args.ext}'
                print(f'saving accepted patch {count} to {patchname}')
                
                if args.ext.lower() == 'jpg':
                    imageio.imwrite(os.path.join(outdir, patchname), patch, quality=args.quality)
                else:
                    imageio.imwrite(os.path.join(outdir, patchname), patch)
                count += 1
                
                if args.limit and (count > args.limit): break
            else:
                im[top:bottom, left:right, :] = 0
        
        if args.limit and (count > args.limit): break
    
    print(f'{count} patches saved')
    print('writing rejection map')
    imageio.imwrite(os.path.join(outdir, f'rejection.{args.ext}'), im)
    



