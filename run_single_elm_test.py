#! /usr/bin/env python
from __future__ import print_function

import json
import argparse
import os
import os.path
import re


def find_files(directory):
    for root, dirs, files in os.walk(directory):
        if 'elm-stuff' in root:
            continue

        for basename in files:
            if basename.startswith('_') or basename == 'Test.elm':
                continue

            if basename.endswith('.elm'):
                filename = os.path.join(root, basename)
                yield filename

def find_specs_importing_module(root_folder, module_names):
    specs = []

    dir = os.getcwd()
    folder = os.path.join(dir, root_folder)

    for file in find_files(folder):
        with open(file, 'r') as f:
            text = f.read()

        for module_name in module_names:
            if 'import ' + module_name in text:
                specs.append(file[len(dir) + 1:])

    return specs

def get_module_name(root_folder, spec_file):
    """
        Takes a root folder, and a spec file, returns the elm module name

        >>> get_module_name("spec/elm", "spec/elm/Assignment/DashboardSpec.elm")
        'Assignment.DashboardSpec'

        >>> get_module_name("", "Assignment/DashboardSpec.elm")
        'Assignment.DashboardSpec'

        >>> get_module_name("spec/elm", "Assignment/DashboardSpec.elm")
        'Assignment.DashboardSpec'
    """

    without_root = spec_file.lstrip(root_folder)
    without_elm = without_root.rstrip('.elm')

    return without_elm.replace('/', '.')


def find_exposed_names(text):
    """
        ## If everything is exposed, then return '..'

        >>> find_exposed_names("module Robot (..) where")
        '..'

        >>> find_exposed_names("module Robot where")
        '..'

        >>> find_exposed_names("")
        '..'


        ## Otherwise, only return the exposed names

        >>> find_exposed_names("module Robot (cat) where")
        ['cat']

        >>> find_exposed_names("module Robot (cat, dog) where")
        ['cat', 'dog']

        >>> find_exposed_names("module Robot \\n(cat\\n, dog)\\n where")
        ['cat', 'dog']

        >>> find_exposed_names("module Robot \\n(cat\\n, dog)\\n where\\n f = (2 + 2)\\n wheret = 5")
        ['cat', 'dog']
    """

    if 'module' not in text:
        return '..'

    between_bits = re.findall('module(.+?)where', text, re.DOTALL)

    if len(between_bits) == 0:
        return '..'

    between_bits = between_bits[0]

    if '(' not in between_bits or '..' in between_bits:
        return '..'

    open_bracket_index = between_bits.index("(")
    close_bracket_index =  between_bits.index(")")

    exposed_names = between_bits[open_bracket_index + 1
        : close_bracket_index
        ].split(',')

    stripped_names = [ name.strip() for name in exposed_names ]

    return stripped_names


def is_a_spec_line(line):
    """
        >>> is_a_spec_line("spec : Test")
        True
        >>> is_a_spec_line("donald : Test")
        True
        >>> is_a_spec_line("ashdasd")
        False
        >>> is_a_spec_line("spec = blob")
        True
    """
    return 'spec =' in line or ': Test' in line


def get_identifier_name(line):
    """
        Get the idenifier name from a line. Idents are considered to be the left-hand names

        >>> get_identifier_name("dave =")
        'dave'

        >>> get_identifier_name("dave=")
        'dave'

        >>> get_identifier_name("dave x=")
        'dave'

        >>> get_identifier_name("sausage : Test")
        'sausage'

        >>> get_identifier_name("sausage:Test")
        'sausage'
    """

    # TODO: this is dumb and slow
    # but the code was fast to write
    valid_splits = ['=', ':']

    for split in valid_splits:
        line = line.replace(split, ' ')

    return line.split(' ')[0]


def find_spec_names(text):
    """
        Spec names are those with the type test or `spec` as the name

        >>> find_spec_names("dave : Test\\n\\n\\nsausage = blob\\n\\nspec = something")
        ['dave', 'spec']
    """
    names = []

    for line in text.split('\n'):
        if is_a_spec_line(line):
            name = get_identifier_name(line)

            if name not in names:
                names.append(name)

    return names

def imports():
    return """
import Signal exposing (..)
import ElmTest exposing (..)
import Console exposing (IO, run)
import Task exposing (Task)
"""

def runner():
    return """
port runner : Signal (Task.Task x ())
port runner = run (consoleRunner tests)
"""

def generate_imports(module_name):
    """
        >>> generate_imports("Dog")
        'import Dog'
    """

    return 'import ' + module_name

def generate_test_lines(spec_names):
    """
        >>> generate_test_lines({"Dog" :["spec"]})
        'tests = suite "Dog tests" [ Dog.spec ]'
        >>> generate_test_lines({"Dog": ["spec", "sausage"]})
        'tests = suite "Dog tests" [ Dog.spec, Dog.sausage ]'
    """

    module_names = ', '.join(module_name for module_name in spec_names)

    tests_part = "tests = suite \"{module_name} tests\" [ ".format(module_name=module_names)
    end = " ]"

    prepend_module_name = []

    for (module_name, specs) in spec_names.items():
        prepend_module_name.extend(
            '{module}.{func}'.format(module=module_name, func=spec_name) for spec_name in specs
        )

    joined = ', '.join(prepend_module_name)

    return tests_part + joined + end


def generate_runner(spec_names):
    """
        >>> 'import Dog' in generate_runner({"Dog": ["spec"]})
        True
        >>> 'port runner = run' in generate_runner({"Dog": ["spec"]})
        True
        >>> 'tests = suite "Dog tests" [ Dog.spec ]' in generate_runner({"Dog": ["spec"]})
        True
    """
    extra_imports = [ generate_imports(module_name) for module_name in spec_names ]

    top = imports() + '\n'.join(extra_imports)
    tests = generate_test_lines(spec_names)
    bottom = runner()

    return top + '\n' + tests + '\n' + bottom


def run_elm_test_on_files(bin_location, root_folder, spec_files, output_file_name):
    """
        run elm test on multiple files as described in the description
    """
    spec_file_names = {}

    for spec_file in spec_files:
        with open(spec_file) as f:
            read_text = f.read()

        exposed_names = find_exposed_names(read_text)
        spec_names = find_spec_names(read_text)

        if exposed_names == '..':
            spec_file_names[spec_file] = spec_names
        else:
            valid_names = [ name for name in spec_names if name in exposed_names ]
            spec_file_names[spec_file] = valid_names

    spec_names = {}

    for (spec_file, names) in spec_file_names.items():
        module_name = get_module_name(root_folder, spec_file)
        spec_names[module_name] = names

    runner_code = generate_runner(spec_names)

    current_dir = os.getcwd()

    os.chdir(root_folder)

    with open(output_file_name, 'w') as f:
        f.write(runner_code)

    run_elm_test(current_dir, bin_location, output_file_name)


def run_elm_test(master_dir, bin_location, spec_file):
    """
        Run elm test on a spec file
        Run elm-package in the current dir
        Uses the binaries from global if bin_location is not set, Otherwise
        `master_dir/bin_location/<bin_name>`
    """
    from subprocess import call

    # default to global
    if bin_location is None:
        bin_location = ''
        master_dir = ''

    elm_package_path = os.path.join(master_dir, bin_location, "elm-package")
    elm_test_path = os.path.join(master_dir, bin_location, "elm-test")

    call([elm_package_path, "install", "--yes"])
    call([elm_test_path, spec_file])

def test():
    import doctest
    doctest.testmod()

LONG_DESCRIPTION = '''
Run tests in files manually by just giving their name. Give multiple names if you want. Globs too.

Using the `--module` flag will create a test suite generated from every module that imports that module.

Files called `Test.elm` or starting with `_` will be ignored as these are common entry points

This script will:
    - Grab the files
    - Find the exposed names from a file
    - Group all the ones with the type `: Test` or the name `spec`
    - Create a test suite composed from all the found tests in each file
    - Run them!
'''

def main():
    parser = argparse.ArgumentParser(description=LONG_DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('spec_file', help='give relative path to the spec file you want to run or the name of the module', nargs='+')
    parser.add_argument('--module', help='use a module name', action='store_true', default=False)
    parser.add_argument('--root', help='define the root folder where your elm-package lives', default='spec/elm')
    parser.add_argument('--bin', help='define a custom binary location - if none provided, default to global', default=None)
    parser.add_argument('--output', help='define a custom output file', default='_Temp.elm')

    args = parser.parse_args()

    if args.module:
        spec_files = find_specs_importing_module(args.root, args.spec_file)
        print('Found the module {module} imported by:'.format(module=','.join(args.spec_file)))
        print('---------------------------------------')
        for file in spec_files:
            print(file)
    else:
        spec_files = args.spec_file

    run_elm_test_on_files(args.bin, args.root, spec_files, args.output)


if __name__ == '__main__':
    main()
