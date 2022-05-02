'''
written by Cioscos

script takes 2 or 3 arguments:
--dir1
--dir2
--force-extension

With dir1 you show it first directory, dir2 second directory, and those two are mandatory.
By default it only compares file names (so asd.png and asd.jpg are considered as "the same file"), but you can use --force-extension to force it to check extension as well
and instead of deleting files, it creates a new folder called "trash_files" and moves the files there so you can still go there and check if it "deleted" something that you wanted to keep
'''
from ast import arg
import os
import shutil
from pathlib import Path
import re
import argparse
import textwrap
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
    parser = argparse.ArgumentParser(
        prog='Files comparator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
written by Cioscos

script takes 2 or 3 arguments:
--dir1
--dir2
--force-extension

With dir1 you show it first directory, dir2 second directory, and those two are mandatory.
By default it only compares file names (so asd.png and asd.jpg are considered as "the same file"), but you can use --force-extension to force it to check extension as well
and instead of deleting files, it creates a new folder called "trash_files" and moves the files there so you can still go there and check if it "deleted" something that you wanted to keep''')
    )
    parser.add_argument('--dir1', type=str, dest='dir_1', required=True, default='directory_1', help='First folder with files')
    parser.add_argument('--dir2', type=str, dest='dir_2', required=True, default='directory_2', help='Second folder with files')
    parser.add_argument('-t', '--trash-dir', type=str, dest='trash_dir', default='trash_files', help='Folder where deleted files will go')
    parser.add_argument('-s', '--separate-trash', action='store_true', dest='separate_trash', default=False, help='Move trashed files to two different folders')
    parser.add_argument('-f', '--force-extension', action='store_true', dest='force_extension', default=False, help='Files with same name but different extension are considered different')
    args = parser.parse_args()

    if args.separate_trash:
        os.makedirs(f'trash_from_{args.dir_1}', exist_ok=True)
        os.makedirs(f'trash_from_{args.dir_2}', exist_ok=True)
    else:
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
        if args.separate_trash:
            for path in dataset_one:
                if name == (path.name if args.force_extension else path.stem):
                    files_to_delete.append((1, path))
            for path in dataset_two:
                if name == (path.name if args.force_extension else path.stem):
                    files_to_delete.append((2, path))
        else:    
            for path in dataset_one + dataset_two:
                if name == (path.name if args.force_extension else path.stem):
                    files_to_delete.append(path)

    
    if args.separate_trash:
        for path in tqdm(files_to_delete, desc='Moving files'):
            shutil.move(path[1], f'trash_from_{args.dir_1 if path[0] == 1 else args.dir_2}')
    else:
        for path in tqdm(files_to_delete, desc='Moving files'):
            shutil.move(path, args.trash_dir)


if __name__ == '__main__':
    main()
