#!/usr/bin/env python

"""Automatically build documentation with Sphinx and copy it in the package."""

import argparse
import logging
import os
import shutil
import subprocess

logger = logging.getLogger()

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
        shutil.rmtree(build_dir)
    except FileNotFoundError as err:
        logger.error(err)


if __name__ == '__main__':
    args = _parse_command_line()
    builder = args.builder
    doc_dir = './doc'
    build_dir = '_build'
    os.chdir(doc_dir)
    shutil.copy2(f"indices/index_{builder}.rst", "index.rst")
    try:
        subprocess.run(["/home/user/miniconda3/envs/leo/bin/sphinx-build", "-b", builder, ".", build_dir], check=True)
    except subprocess.CalledProcessError as err:
        logger.error(err)

    # Move documentation to its final destination
    if builder == 'html':
        static_dir = f'{build_dir}/_static'
        sources_dir = f'{build_dir}/_sources'
        htmldocs_dir = '../vitables/htmldocs'
        shutil.move(f'{static_dir}/basic.css',
                    f'{static_dir}/classic.css')
        shutil.rmtree(sources_dir)
        if os.path.isdir(htmldocs_dir):
            shutil.rmtree(htmldocs_dir)
        shutil.copytree(build_dir, htmldocs_dir)
    elif builder == 'latex':
        os.chdir(build_dir)
        try:
            subprocess.run('pdflatex UsersGuide.tex', check=True)
            subprocess.run('pdflatex UsersGuide.tex', check=True)
        except subprocess.CalledProcessError as err:
            logger.error(err)
        shutil.copy2('UsersGuide.pdf', '../../UsersGuide.pdf')
        os.chdir('..')
    # Cleanup the doc directory
    _cleanup()
