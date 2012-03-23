# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup

setup(
      name="keyremap",
      version="0.0.1",
      author="Andrei Dragomir",
      author_email="adragomir@gmail.com",
      url="http://github.com/adragomir/keyremap",
      license="Apache",
      description="Simple Key Remapping for X",
      long_description="""Autokey allows you to remap X keyboard events.""",
      package_dir={"keyremap": "src/lib"},
      packages=["keyremap"],
      package_data={},
      data_files=[],
      scripts=['keyremap']
      )
