import os
import shutil
from pathlib import Path
import re
import argparse
from tqdm import tqdm

def alphaNumOrder(string):
    return ''.join([format(int(x), '05d') if x.isdigit()
                    else x for x in re.split(r'(\d+)', string)])

def make_dataset(dir: str) -> list[Path]:
    files = []
    assert os.path.isdir(dir), '%s is not a valid directory' % dir

    for root, _, fnames in os.walk(dir):
        for fname in sorted(fnames, key=alphaNumOrder):
            path = os.path.join(root, fname)
            files.append(Path(path))

    return files

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir1', type=str, dest='dir_1', required=True, default='directory_1', help='First folder with files')
    parser.add_argument('--dir2', type=str, dest='dir_2', required=True, default='directory_2', help='Second folder with files')
    parser.add_argument('--trash-dir', type=str, dest='trash_dir', default='trash_files', help='Folder where deleted files will go')
    parser.add_argument('--force-extension', action='store_true', dest='force_extension', default=False, help='Files with same name but different extension are considered different')
    args = parser.parse_args()

    os.makedirs(args.trash_dir, exist_ok=True)

    dataset_one = make_dataset(args.dir_1)
    dataset_two = make_dataset(args.dir_2)

    if len(dataset_one) == 0 or len(dataset_two) == 0:
        print('All the folders must have some files inside')
        return -1

    filenames_one = set([x.name if args.force_extension else x.stem for x in dataset_one])
    filenames_two = set([x.name if args.force_extension else x.stem for x in dataset_two])

    intersection = filenames_one & filenames_two
    final_names = (filenames_one - intersection) | (filenames_two - intersection)

    files_to_delete = []

    for name in final_names:
        for path in dataset_one + dataset_two:
            if name == (path.name if args.force_extension else path.stem):
                files_to_delete.append(path)
    
    for path in tqdm(files_to_delete, desc='Copying files'):
        shutil.move(path, args.trash_dir)


if __name__ == '__main__':
    main()
