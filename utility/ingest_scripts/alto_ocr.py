import argparse
import os
import glob
from bs4 import BeautifulSoup


def write_ocr(args):
    dirlist = []
    dirlist = sorted(glob.glob(os.path.join(args.alto_dir, '*.xml')))

    for file in dirlist:
        filename = os.path.basename(file)
        text =  open(file, 'rU').read()
        soup = BeautifulSoup(text, 'lxml')
        strings = soup.find_all('string')
        out = os.path.join(args.ocr_dir, os.path.basename(file).rstrip('.xml')+ '.tsv')
        with open(out, 'w') as outfile:
            outfile.write('\t'.join(['content', 'x', 'y', 'w', 'h', '\n']))
            for string in strings:
                x = string['hpos']
                y = string['vpos']
                w = string['width']
                h = string['height']
                content = string['content']
                outfile.write('\t'.join([content.encode('utf8'),
                             x.encode('utf8'),
                             y.encode('utf8'),
                             w.encode('utf8'),
                             h.encode('utf8'),
                             '\n']))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--alto_dir', type=str,
                        help='Input a directory containing the local ALTO files')
    parser.add_argument('--ocr_dir', type=str,
                        help='Input an empty directory where the OCR files should be output.')
    args = parser.parse_args()
    write_ocr(args)

if __name__ == '__main__':
    main()
