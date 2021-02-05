#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Chop up multiple GDC SVS files into tiles.

Some of the behaviour here is pretty cranky, designed around some particular
constraints in the storage & compute setup for the Kidney project.

You probably want to run with the --no_cache option, at least.
'''

import sys, os, os.path, shutil
import argparse

import numpy as np
import pandas as pd
import imageio

import json
import openslide


# NB: these settings also make no sense elsewhere, modify for your setup
DATA = '/tf/data'
GDC = os.path.join(DATA, 'csmicro1', 'gdc')
LOCAL = os.path.join(DATA, 'scratch')

def process_args():
    ap = argparse.ArgumentParser(description='Cut multiple SVS images into non-empty tiles')

    ap.add_argument('-G', '--gdc', help='directory containing GDC files', default=GDC)
    ap.add_argument('-L', '--local', help='local cache directory', default=LOCAL)
    
    ap.add_argument('-s', '--size', help='edge size (in pixels) of tiles to create', type=int, default=512)
    ap.add_argument('-p', '--panel', help='edge size (in tiles) of panels of tiles to load at a time', type=int, default=10)
    ap.add_argument('-S', '--small', help='keep partial tiles from edges', action='store_true')
    ap.add_argument('-x', '--ext', help='export file type (extension)', default='jpg')
    
    ap.add_argument('-q', '--quality', help='export quality for JPG images', type=int, default=85)
    
    ap.add_argument('-l', '--limit', help='max slides to tile', type=int, default=2)
    ap.add_argument('-n', '--no_cache', help='work directly on remote mounted filesystem', action='store_true')
    ap.add_argument('-N', '--no_clean', help='do not purge local cached copies', action='store_true')
    ap.add_argument('-M', '--map', help='write rejection map image for each slide', action='store_true')
    
    ap.add_argument('-u', '--updated', help='name for updated version of the metadata file', default='{tag}-updated.tsv')
    
    # acceptance heuristics -- unlike the single tile script, this defaults to SD acceptance criteria, which seem to work well
    ap.add_argument('-r', '--relative', help='use SD or mean relative to panel value', action='store_true')
    ap.add_argument('-d', '--std', help='min SD to accept', type=float, default=25)
    ap.add_argument('-a', '--avg', help='max mean to accept', type=float, default=0)
    ap.add_argument('-c', '--count', help='min pixels below threshold to accept', type=int, default=0)
    ap.add_argument('-t', '--thresh', help='highest pixel value considered non-background', default=200)
    
    ap.add_argument('meta', help='source metadata file', nargs='?', default='slides_out.tsv')
    
    return ap.parse_args()


def accept(patch, args, stats):
    if args.std:
        if args.relative:
            if np.std(patch) >= args.std * stats['std']:
                return True
        else:
            if np.std(patch) >= args.std:
                return True
    
    if args.avg:
        if args.relative:
            if np.mean(patch) >= args.mean * stats['mean']:
                return True
        else:
            if np.mean(patch) >= args.mean:
                return True
    
    if args.count:
        if np.sum(patch <= args.thresh) >= args.count:
            return True
    
    return False


if __name__ == '__main__':
    args = process_args()
    
    # source can be a directory or metadata file
    # in either case we construct a DataFrame of the data
    if os.path.isdir(args.meta):
        print('reading directory %s' % args.meta)
        meta = pd.DataFrame( { 'file_name' : [ ff for ff in os.listdir(args.meta) if ff.lower().endswith('.svs') ] } )
        src_dir = args.meta
        tag = os.path.basename(args.meta) + '-' + str(args.size)
    elif os.path.isfile(args.meta):
        print('loading metadata ' + args.meta)    
        meta = pd.read_csv(args.meta, sep='\t')
        src_dir = os.path.join(args.gdc, 'svs')
        tag = str(args.size)
    else:
        print('%s not found' % args.meta)
        sys.exit(0)
    
    if (not args.no_cache) and (not os.path.isdir(args.local)):
        os.makedirs(args.local)
    
    
    # for the moment, we're just going to plough through in order without any
    # ordering and selection, but we'll at least filter duplicates
    
    meta.drop_duplicates(subset='file_name', inplace=True, ignore_index=True)
    meta.reset_index(drop=True, inplace=True)
    
    # add some columns for info we'll want to record
    TILES_COL = f'tiles_{args.size}'
    meta[TILES_COL] = 0
    meta['height'] = 0
    meta['width'] = 0
    meta['magnification'] = ''
    
    print(f'{meta.shape[0]} files to process, limit {args.limit}')
    
    file_count = 0
    
    for ii in range(meta.shape[0]):
        g_src = os.path.join(src_dir, meta['file_name'].iloc[ii])
        g_dst = os.path.join(args.gdc, 'tiles', tag, os.path.splitext(meta['file_name'].iloc[ii])[0])
        
        if not os.path.isfile(g_src):
            #print(f'{g_src} does not exist, skipping')
            continue
        
        if args.no_cache:
            src = g_src
            dst = g_dst
        else:
            print(f'copying {meta["file_name"].iloc[ii]} to local cache')
            src = os.path.join(args.local, meta['file_name'].iloc[ii])
            shutil.copy(g_src, src)
            dst = os.path.join(args.local, 'tiles', str(args.size), os.path.splitext(meta['file_name'].iloc[ii])[0])
        
        os.makedirs(dst, exist_ok=True)

        print('opening ' + src)
        svs = openslide.OpenSlide(src)
        
        props = dict(svs.properties)

        # stash details
        meta.loc[ii, 'width'] = svs.level_dimensions[0][0]
        meta.loc[ii, 'height'] = svs.level_dimensions[0][1]
        meta.loc[ii, 'magnification'] = props['aperio.AppMag']
        
        full_width = svs.level_dimensions[0][0]
        full_height = svs.level_dimensions[0][1]
        panel_size = args.panel * args.size
        tile_count = 0

        
        for panel_top in range(0, full_height, panel_size):
            panel_bottom = min(full_height, panel_top + panel_size)
            panel_height = panel_bottom - panel_top
            
            for panel_left in range(0, full_width, panel_size):
                panel_right = min(full_width, panel_left + panel_size)
                panel_width = panel_right - panel_left
                
                print('loading & converting pixel data')
                im = np.array(svs.read_region((panel_left, panel_top), 0, (panel_width, panel_height)).convert('RGB'))
    
                print(f'panel shape: {im.shape}, dtype: {im.dtype}')
    
                stats = { 'mean' : np.mean(im), 'std' : np.std(im) }
        
                for top in range(0, im.shape[0], args.size):
                    bottom = min(im.shape[0], top + args.size)
                    
                    if (not args.small) and ((bottom - top) < args.size):
                        break
        
                    for left in range(0, im.shape[1], args.size):
                        right = min(im.shape[1], left + args.size)

                        if (not args.small) and ((right - left) < args.size):
                            break
            
                        patch = im[top:bottom, left:right, :]
                        if accept(patch, args, stats):
                            patchname = f'tile-{panel_left + left}-{panel_top + top}-{panel_left + right}-{panel_top + bottom}.{args.ext}'
                            print(f'saving accepted patch {tile_count + 1} to {patchname}')
                
                            if args.ext.lower() == 'jpg':
                                imageio.imwrite(os.path.join(dst, patchname), patch, quality=args.quality)
                            else:
                                imageio.imwrite(os.path.join(dst, patchname), patch)
                            tile_count += 1
                        else:
                            im[top:bottom, left:right, :] = 0
        
                print(f'{tile_count} tiles saved')
        
                if args.map:
                    print('writing rejection map')
                    imageio.imwrite(os.path.join(dst, f'rejection-{panel_left}-{panel_top}-{panel_right}-{panel_bottom}.{args.ext}'), im)
        
        meta.loc[ii, TILES_COL] = tile_count
        
        if not args.no_cache:
            print('copying results back to main')
            os.makedirs(g_dst, exist_ok=True)
            
            for item in os.listdir(dst):
                shutil.copy(os.path.join(dst, item), g_dst)
            
            if not args.no_clean:
                print('deleting cached results')
                shutil.rmtree(dst)
                print('deleting cached slide')
                os.remove(src)
        
        file_count += 1
        
        if args.limit and (file_count >= args.limit):
            print(f'image limit {args.limit} reached, stopping')
            break
    
    meta.to_csv(args.updated.format(tag=tag), sep='\t')
        
