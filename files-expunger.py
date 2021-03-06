'''
written by Cioscos

script takes different arguments:
--dir1
--dir2
--trash-dir or -t
--force-extension or -f
--separate-trash or -s
--check-sha256 or -c


With dir1 you show it first directory, dir2 second directory, and those two are mandatory.
By default it only compares file names (so asd.png and asd.jpg are considered as "the same file"), but you can use --force-extension to force it to check extension as well
and instead of deleting files, it creates a new folder called "trash_files" by default or you can give a custom name to that folder using -t argument and moves the files there
so you can still go there and check if it "deleted" something that you wanted to keep.
If you want to know from where moved files come from, you can use -s arg to create 2 trash folders according to the original position of the files.
In addition, using the -c argument it is possible after moving the files to their respective folders to check if the hash of the remaining files matches. 
If it matches, then the files will remain in the folders, otherwise they will be moved to a new folder called "different for hash".
If the -s argument is used, then 2 different folders will also be created for the hash check.
'''

import os
import sys
import shutil
import hashlib
from pathlib import Path
import re
import argparse
import textwrap
from tqdm import tqdm

def alphaNumOrder(string: str) -> str:
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

def sha256sum(filename: Path) -> str:
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()

def main():
    if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 10):
        raise Exception("This program requires at least Python 3.10")

    parser = argparse.ArgumentParser(
        prog='Files comparator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
script takes different arguments:
--dir1
--dir2
--trash-dir or -t
--force-extension or -f
--separate-trash or -s
--check-sha256 or -c


With dir1 you show it first directory, dir2 second directory, and those two are mandatory.
By default it only compares file names (so asd.png and asd.jpg are considered as "the same file"), but you can use --force-extension to force it to check extension as well
and instead of deleting files, it creates a new folder called "trash_files" by default or you can give a custom name to that folder using -t argument and moves the files there
so you can still go there and check if it "deleted" something that you wanted to keep.
If you want to know from where moved files come from, you can use -s arg to create 2 trash folders according to the original position of the files.
In addition, using the -c argument it is possible after moving the files to their respective folders to check if the hash of the remaining files matches. 
If it matches, then the files will remain in the folders, otherwise they will be moved to a new folder called "different for hash".
If the -s argument is used, then 2 different folders will also be created for the hash check.''')
    )
    parser.add_argument('--dir1', type=str, dest='dir_1', required=True, default='directory_1', help='First folder with files')
    parser.add_argument('--dir2', type=str, dest='dir_2', required=True, default='directory_2', help='Second folder with files')
    parser.add_argument('-t', '--trash-dir', type=str, dest='trash_dir', default='trash_files', help='Folder where deleted files will go')
    parser.add_argument('-s', '--separate-trash', action='store_true', dest='separate_trash', default=False, help='Move trashed files to two different folders')
    parser.add_argument('-f', '--force-extension', action='store_true', dest='force_extension', default=False, help='Files with same name but different extension are considered different')
    parser.add_argument('-c', '--check-sha256', action='store_true', dest='check_sha256', default=False, help="Check the digest of the file to understand if they're equal or not")
    args = parser.parse_args()

    if args.separate_trash:
        os.makedirs(f'trash_from_{args.dir_1}', exist_ok=True)
        os.makedirs(f'trash_from_{args.dir_2}', exist_ok=True)
        if args.check_sha256:
            os.makedirs(f'different for hash {args.dir_1}', exist_ok=True)
            os.makedirs(f'different for hash {args.dir_2}', exist_ok=True)
    else:
        os.makedirs(args.trash_dir, exist_ok=True)
        if args.check_sha256:
            os.makedirs('different for hash', exist_ok=True)

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

    if args.check_sha256:
        dataset_one = make_dataset(args.dir_1)
        dataset_two = make_dataset(args.dir_2)

        print("\nCalculating Hash")
        digests_one = []
        digests_two = []
        for file in dataset_one:
            digests_one.append((file, sha256sum(file)))
        for file in dataset_two:
            digests_two.append((file, sha256sum(file)))

        different_digest = []
        for digest_one in digests_one:
            for digest_two in digests_two:
                if (digest_one[0].name if args.force_extension else digest_one[0].stem) == \
                    (digest_two[0].name if args.force_extension else digest_two[0].stem) and \
                    (digest_one[1] != digest_two[1]):
                    if args.separate_trash:
                        different_digest.extend([(1, digest_one[0]), (2, digest_two[0])])
                    else:
                        different_digest.extend([digest_one, digest_two])

        if args.separate_trash:
            for path in tqdm(different_digest, desc='Moving files'):
                shutil.move(path[1], f'different for hash {args.dir_1 if path[0] == 1 else args.dir_2}')
        else:
            for path in tqdm(different_digest, desc='Moving files'):
                shutil.move(path, 'different for hash')

if __name__ == '__main__':
    main()
