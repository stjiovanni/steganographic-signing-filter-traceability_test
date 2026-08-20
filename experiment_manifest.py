"""Create the immutable image manifest used by a benchmark run."""

import argparse
import hashlib
import json
import os
from glob import glob
from PIL import Image


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--image-count', type=int, default=1200)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output', default='output/results/image_manifest.json')
    args = parser.parse_args()

    paths = sorted(glob(os.path.join(args.input_dir, '*.jpg')))[:args.image_count]
    if len(paths) < args.image_count:
        raise SystemExit(f'Only {len(paths)} JPG images found; {args.image_count} required')
    images = []
    for path in paths:
        with Image.open(path) as image:
            width, height = image.size
        images.append({
            'image_id': os.path.splitext(os.path.basename(path))[0],
            'filename': os.path.basename(path),
            'sha256': sha256_file(path),
            'width': width,
            'height': height,
        })
    manifest = {
        'dataset': 'MS-COCO 2017 validation split',
        'selection': 'lexicographically first N JPG files',
        'image_count': len(images),
        'seed': args.seed,
        'images': images,
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as stream:
        json.dump(manifest, stream, indent=2)
    print(f'Wrote {len(images)} image records to {args.output}')


if __name__ == '__main__':
    main()
