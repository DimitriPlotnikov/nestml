#
# SymbolTableBuilderTest.py
#
# This file is part of NEST.
#
# Copyright (C) 2004 The NEST Initiative
#
# NEST is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NEST is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NEST.  If not, see <http://www.gnu.org/licenses/>.
import os
import unittest

from pynestml.modelprocessor.ASTNESTMLCompilationUnit import ASTNESTMLCompilationUnit
from pynestml.modelprocessor.ModelParser import ModelParser
from pynestml.utils.Logger import Logger, LOGGING_LEVEL

Logger.initLogger(LOGGING_LEVEL.INFO)


class SymbolTableBuilderTest(unittest.TestCase):

    def test_building_symboltable_for_all_neurons(self):
        for filename in os.listdir(os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                                 os.path.join('..', 'models')))):
            if filename.endswith(".nestml"):
                file_path = os.path.join(os.path.dirname(__file__), os.path.join(os.path.join('..', 'models'), filename))

                ast = ModelParser.parse_model(file_path)

                assert isinstance(ast, ASTNESTMLCompilationUnit)
                for neuron in ast.getNeuronList():
                    assert neuron.getScope() is not None


if __name__ == '__main__':
    unittest.main()
