#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Automatically build documentation with Sphinx and copy it in the package."""

import argparse
import os
import shutil
import subprocess


def _parse_command_line():
    """Parse the arguments passed to makedoc.py script."""
    usage = '%(prog)s [option]'
    description = 'Build the ViTables documentation using Sphinx'
    parser = argparse.ArgumentParser(usage=usage, description=description)

    # Positional arguments
    parser.add_argument(
        'builder', choices=['html', 'latex'], nargs='?', metavar='BUILDER',
        help='builder to be used by Sphinx. Can be html or latex')
    parser.set_defaults(builder='html')

    return parser.parse_args()


def _cleanup():
    """Cleanup the build directory."""
    try:
        os.remove('index.rst')
        shutil.rmtree(f'{build_dir}')
    except FileNotFoundError as err:
        print(err)


if __name__ == '__main__':
    args = _parse_command_line()
    builder = args.builder
    build_dir = '_build'
    os.chdir('./doc')
    shutil.copy2(f"indices/index_{builder}.rst", "index.rst")
    subprocess.run(["sphinx-build", "-b", builder, ".", build_dir])

    # Move documentation to its final destination
    if builder == 'html':
        static_dir = f'{build_dir}/_static'
        sources_dir = f'{build_dir}/_sources'
        htmldocs_dir = '../vitables/htmldocs'
        shutil.move(f'{static_dir}/basic.css',
                    f'{static_dir}/classic.css')
        shutil.rmtree(f'{sources_dir}')
        shutil.rmtree(f'{htmldocs_dir}')
        shutil.copytree(build_dir, f'{htmldocs_dir}')
    elif builder == 'latex':
        os.chdir('./_build')
        subprocess.run('pdflatex UsersGuide.tex')
        subprocess.run('pdflatex UsersGuide.tex')
        shutil.copy2('UsersGuide.pdf', '../../UsersGuide.pdf')
        os.chdir('..')
    # Cleanup the doc directory
    _cleanup()
