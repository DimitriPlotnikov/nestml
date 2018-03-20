#
# PyNestMLFrontendTest.py
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

from pynestml.codegeneration.nest_codegeneration import generate_nest_module_code, make_functions_self_contained, \
    replace_functions_through_defining_expressions, transform_ode_and_shapes_to_json, transform_shapes_and_odes, \
    analyse_and_generate_neurons
from pynestml.frontend.FrontendConfiguration import FrontendConfiguration
from pynestml.modelprocessor.ModelParser import ModelParser
from tests.nestml_models_paths import iaf_psc_alpha_path


class CodegeneratorTest(unittest.TestCase):
    """
    Tests codegenerator with a psc, cond, delta and abitrary model
    """

    def test_model_preparation(self):
        compilation_unit = ModelParser.parse_file_and_build_symboltable(iaf_psc_alpha_path)
        assert len(compilation_unit.getNeuronList()) == 1
        ast_neuron = compilation_unit.getNeuronList()[0]
        equations_block = ast_neuron.get_equations_block()
        # the idea here is to go through the rhs, print expressions, use the same mechanism as before, and reread them
        # again
        # TODO: add tests for this function
        # this function changes stuff inplace
        make_functions_self_contained(equations_block.get_functions())

        replace_functions_through_defining_expressions(equations_block.get_equations(), equations_block.get_functions())

        json_representation = transform_ode_and_shapes_to_json(equations_block)
        self.assertTrue("convolve(I_shape_in, in_spikes)" in json_representation["odes"][0]["definition"])
        self.assertTrue("convolve(I_shape_ex, ex_spikes)" in json_representation["odes"][0]["definition"])

    def test_solve_odes_and_shapes(self):
        compilation_unit = ModelParser.parse_file_and_build_symboltable(iaf_psc_alpha_path)
        assert len(compilation_unit.getNeuronList()) == 1
        ast_neuron = compilation_unit.getNeuronList()[0]
        ast_neuron = transform_shapes_and_odes(ast_neuron)
        print(ast_neuron)

    def test_iaf_psc_alpha(self):
        path = str(os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.join(
            '..', 'models', 'iaf_psc_alpha.nestml'))))

        params = list()
        params.append('-path')
        params.append(path)
        # params.append('-dry')
        params.append('-logging_level')
        params.append('NO')
        params.append('-target')
        params.append('target')
        params.append('-store_log')
        params.append('-dev')

        FrontendConfiguration.config(params)

        compilation_unit = ModelParser.parse_file_and_build_symboltable(path)
        generate_nest_module_code(compilation_unit.getNeuronList())
        analyse_and_generate_neurons(compilation_unit.getNeuronList())

    def test_iaf_cond_alpha_implicit(self):
        path = str(os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.join(
            '..', 'models', 'iaf_cond_alpha.nestml'))))

        params = list()
        params.append('-path')
        params.append(path)
        # params.append('-dry')
        params.append('-logging_level')
        params.append('NO')
        params.append('-target')
        params.append('target')
        params.append('-store_log')
        params.append('-dev')

        FrontendConfiguration.config(params)

        compilation_unit = ModelParser.parse_file_and_build_symboltable(path)

        iaf_cond_alpha_implicit = list()
        iaf_cond_alpha_implicit.append(compilation_unit.getNeuronList()[1])
        generate_nest_module_code(iaf_cond_alpha_implicit)
        analyse_and_generate_neurons(iaf_cond_alpha_implicit)

    def test_iaf_cond_alpha_functional(self):
        path = str(os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.join(
            '..', 'models', 'iaf_cond_alpha.nestml'))))

        params = list()
        params.append('-path')
        params.append(path)
        # params.append('-dry')
        params.append('-logging_level')
        params.append('NO')
        params.append('-target')
        params.append('target')
        params.append('-store_log')
        params.append('-dev')

        FrontendConfiguration.config(params)

        compilation_unit = ModelParser.parse_file_and_build_symboltable(path)

        iaf_cond_alpha_functional = list()
        iaf_cond_alpha_functional.append(compilation_unit.getNeuronList()[0])
        generate_nest_module_code(iaf_cond_alpha_functional)
        analyse_and_generate_neurons(iaf_cond_alpha_functional)


if __name__ == '__main__':
    unittest.main()
