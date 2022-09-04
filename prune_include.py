"""
prune_include: Scan a project folder for redundant 'include' directives.

For all files of a given extension in a project sub-folder,
try to remove 'include' directives and build the project.
If the bauld was a success (object file created) - the include was redundant.

"""

import sys
import re
import argparse
from pathlib import Path
import subprocess
import fileinput

__VERSION_INFO__ = ('1', '0', '0')
__VERSION__ = '.'.join(__VERSION_INFO__)


def parse_arguments():
    """
    Parse_arguments.

    Handle arguments and help info.
    """
    parser = argparse.ArgumentParser(
        description="""
Version updater script.
This script reads a project version ini file and updates the version information accordingly.
Without arguments, it prints the current Semantic Version found.
Default ini file location is: ./Configuration/Project.ini
Note: to keep trailing spaces in the ini file prefixes, append '$' to the prefix string.
    """,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('folder',
                        type=str,
                        default='.',
                        help='Specify folder to prune into. Defaule is "."')
    parser.add_argument('--build',
                        '-b',
                        type=str,
                        default="g++",
                        help='Build command. for inner quotes in path, ' +
                                'use back slash escape: \\" ' +
                                ' Default is "g++"')
    parser.add_argument('--artifact',
                        '-a',
                        type=str,
                        default="a.exe",
                        help='Build command\'s final atrifact file. Default is "a.exe"')
    parser.add_argument('--extension',
                        '-e',
                        type=str,
                        default='cpp',
                        help='Specify file extension (e.g. h c or cxx). no dot. default is "cpp"')
    parser.add_argument('--token',
                        '-t',
                        type=str,
                        default="#include",
                        help='Include token word. Default is "#include"')
    parser.add_argument('--comment',
                        '-c',
                        type=str,
                        default="// ",
                        help='Line comment pattern. Default is "// "')
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version="%(prog)s (" + __VERSION__ + ")")

    return parser.parse_args()


def exit_error(_str):
    """Print an error message and exit ablormally (exit(1))."""
    print("Error: " + _str)
    print("Use '--help' to see usage info")
    sys.exit(1)


def build_project(builder):
    """Build the project, check nothing."""
    subprocess.run(builder, capture_output=True, check=False)


def remove_artifact(artifact):
    """Delete the artifact file (no check)."""
    # remove artifact
    try:
        Path(artifact).unlink()
    except FileNotFoundError:
        pass  # OK if not found


def inplace_insert(file, line_number, replace_line):
    """Inplace replace a line in the given file."""
    with fileinput.input(files=(file), inplace=True) as file_input:
        for line in file_input:
            if fileinput.filelineno() == line_number:
                print(replace_line, end='')
            else:
                print(line, end='')


def prune_include(file, line_number, backup_line, args):
    """Try to build while pruning line_number from file."""
    artifact = args.artifact
    builder = args.build
    comment = args.comment
    was_changed = False

    print(f'    Testing line #{line_number}: {backup_line.rstrip()}')

    remove_artifact(artifact)
    replace_line = f'{comment}{backup_line}'
    inplace_insert(file, line_number, replace_line)
    build_project(builder)
    # if artifact exist, we can remove the include
    if Path(artifact).is_file():
        was_changed = True
        print(f'    Line #{line_number} was removed from {file}  !')
    else:   # need to revert
        inplace_insert(file, line_number, backup_line)
        build_project(builder)
        # the artifact must be restored
        if not Path(artifact).is_file():
            exit_error(f'Could not restore build after resetting line #{line_number} of {file}')
    return was_changed


def process_file(file, is_reversed, args):
    """Collect line candidates, scan and replace."""
    print(f'Processing: {file}', end='')
    if is_reversed:
        print(' (Reversed)')
    else:
        print('')

    token = args.token
    was_changed = False
    # list all matching tokens line numbers
    include_lines = []
    backup_lines = {}
    with fileinput.input(files=(file)) as file_input:
        for line in file_input:
            # Regular expression: Begin line, 0 or more white spaces,
            # token, at least one white space
            if re.match(f'^\\s*{token}\\s+', line):
                line_num = fileinput.filelineno()
                include_lines.append(line_num)
                backup_lines[line_num] = line

    if is_reversed:
        include_lines = reversed(include_lines)
    for line_number in include_lines:
        new_is_changed = prune_include(file, line_number, backup_lines[line_number], args)
        was_changed = was_changed or new_is_changed

    return was_changed


def initialize(file_list, args):
    """Remove artifact, touch all surce files, build. test artifact existance."""
    artifact = args.artifact
    builder = args.build
    # remove artifact
    # Print some info
    print(f'Found {len(file_list)} files: ')
    print(*file_list, sep="\n")
    print('')
    print(f'Building {artifact} first, might take some time')
    remove_artifact(artifact)
    # touch all
    for file in file_list:
        Path(file).touch()
    # Build
    build_project(builder)
    # Validate arrtifact exist
    if not Path(artifact).is_file():
        exit_error(f'Initialize error: artifact:{artifact} ' +
                   f'was not created after running build:{builder}')
    else:
        print('Initialization done.')


#####################################################
#             Main flow                             #
#####################################################


def main():
    """Run main program process below."""
    args = parse_arguments()

    try:
        # Build file list
        file_list = list(Path(args.folder).rglob(f'*.{args.extension}'))
        if not file_list:
            exit_error(f"No .{args.extension} files found under {args.folder}")

        initialize(file_list, args)

        # scan all files
        for file in file_list:
            was_changed = process_file(file, True, args)  # Reveresed order = True first
            if was_changed:  # no change means every include counts. no need to re-test
                process_file(file, False, args)

        # success !
        sys.exit(0)
    except FileNotFoundError as err:
        exit_error("File not found = " + str(err))


if __name__ == '__main__':
    main()
