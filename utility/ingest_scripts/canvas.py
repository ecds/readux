import argparse
import sys
import requests
import json
import glob
import os

def make_csv(args):
    print(','.join(['manifest',
                'id',
                'label',
                'pid',
                'summary',
                'position',
                'height',
                'width',]))
    dirlist = []
    dirlist = sorted(glob.glob(os.path.join(args.image_dir, '*.' + args.file_ext)))

    for file in dirlist:
        filename = os.path.basename(file)
        url = 'http://images.readux.ecds.emory.edu/cantaloupe/iiif/2/' + args.manifest_pid + '_' + filename + '/info.json'
        data = requests.get(url).text
        data = json.loads(data)
        pid = args.manifest_pid + '_' + filename
        position = dirlist.index(file) + 1
        height = data['height']
        width = data['width']
        image_server = 'https://images.readux.ecds.emory.edu:8443/cantaloupe/iiif/2'
        manifest = args.manifest_pid
        if position == 1:
            label = 'cover'
        else:
            label = 'canvas ' + str(position)
        print(','.join([manifest,
                        image_server,
                        '',
                        label,
                        pid,
                        '',
                        str(position),
                        str(height),
                        str(width)]))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_dir', type=str,
                        help='Input a directory containing the local image files')
    parser.add_argument('--file_ext', type=str,
                        help='Input the file extension for the images.')
    parser.add_argument('--manifest_pid', type=str,
                        help='Input the manifest pid. This should match the name of the image directory on the image server.')
    args = parser.parse_args()
    sys.stdout.write(str(make_csv(args)))

if __name__ == '__main__':
    main()
