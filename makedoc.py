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
        shutil.rmtree('{0}'.format(build_dir))
    except FileNotFoundError as err:
        print(err)


if __name__ == '__main__':
    args = _parse_command_line()
    builder = args.builder
    build_dir = '_build'
    os.chdir('./doc')
    shutil.copy2("indices/index_{0}.rst".format(builder), "index.rst")
    subprocess.call('sphinx-build -b {0} . {1}'.format(builder, build_dir))

    # Move documentation to its final destination
    if builder == 'html':
        static_dir = '{0}/_static'.format(build_dir)
        sources_dir = '{0}/_sources'.format(build_dir)
        htmldocs_dir = '../vitables/htmldocs'
        shutil.move('{0}/basic.css'.format(static_dir),
                    '{0}/classic.css'.format(static_dir))
        shutil.rmtree('{0}'.format(sources_dir))
        shutil.rmtree('{0}'.format(htmldocs_dir))
        shutil.copytree(build_dir, '{0}'.format(htmldocs_dir))
    elif builder == 'latex':
        os.chdir('./_build')
        subprocess.call('pdflatex UsersGuide.tex')
        subprocess.call('pdflatex UsersGuide.tex')
        shutil.copy2('UsersGuide.pdf', '../../UsersGuide.pdf')
        os.chdir('..')
    # Cleanup the doc directory
    _cleanup()
