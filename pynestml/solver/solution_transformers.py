#
# solution_transformers.py
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
import re

from pynestml.modelprocessor.ASTNeuron import ASTNeuron
from pynestml.modelprocessor.ASTOdeShape import ASTOdeShape
from pynestml.modelprocessor.ModelParser import ModelParser
from pynestml.solver.TransformerBase import add_declarations_to_internals, \
    compute_state_shape_variables_declarations, add_declarations_to_initial_values, \
    compute_state_shape_variables_updates, replace_integrate_call, add_state_updates
from pynestml.utils.ASTCreator import ASTCreator


def integrate_exact_solution(neuron, exact_solution):
    # type: (ASTNeuron, map[str, list]) -> ASTNeuron
    """
    Adds a set of instructions to the given neuron as stated in the solver output.
    :param neuron: a single neuron instance
    :param exact_solution: exact solution
    :return: a modified neuron with integrated exact solution and without equationsblock
    """

    neuron.addToInternalBlock(ASTCreator.createDeclaration('__h ms = resolution()'))
    neuron = add_declarations_to_internals(neuron, exact_solution["propagator"])

    state_shape_variables_declarations = compute_state_shape_variables_declarations(exact_solution)
    neuron = add_declarations_to_initial_values(neuron, state_shape_variables_declarations)

    state_shape_variables_updates = compute_state_shape_variables_updates(exact_solution)
    neuron = add_state_updates(state_shape_variables_updates, neuron)

    neuron = replace_integrate_call(neuron, exact_solution)

    return neuron


def functional_shapes_to_odes(neuron, transformed_shapes):
    # type: (ASTNeuron, map[str, list]) -> ASTNeuron
    """
    Adds a set of instructions to the given neuron as stated in the solver output.
    :param neuron: a single neuron instance
    :param transformed_shapes: ode-toolbox output that encodes transformation of functional shapes to odes with IV
    :return: the source neuron with modified equationsblock without functional shapes
    """
    shape_names, shape_name_to_initial_values, shape_name_to_shape_state_variables, shape_state_variable_to_ode = \
        _convert_to_shape_specific(transformed_shapes)

    # delete original functions shapes. they will be replaced though ode-shapes computed through ode-toolbox.
    shapes_to_delete = []  # you should not delete elements from list during iterating the list
    for declaration in neuron.get_equations_block().getDeclarations():
        if isinstance(declaration, ASTOdeShape):
            if declaration.getVariable().getName() in shape_names:
                shapes_to_delete.append(declaration)
    for declaration in shapes_to_delete:
        neuron.get_equations_block().getDeclarations().remove(declaration)

    state_shape_variables_declarations = {}
    for shape_name in shape_names:
        for variable, initial_value in zip(
                shape_name_to_shape_state_variables[shape_name],
                shape_name_to_initial_values[shape_name]):
            state_shape_variables_declarations[variable] = initial_value

        for variable, shape_state_ode in zip(
                shape_name_to_shape_state_variables[shape_name],
                shape_state_variable_to_ode[shape_name]):
            ode_shape = ModelParser.parseShape("shape " + variable + "' = " + shape_state_ode)
            neuron.add_shape(ode_shape)

    neuron = add_declarations_to_initial_values(neuron, state_shape_variables_declarations)

    return neuron


def _convert_to_shape_specific(transformed_shapes):
    """

    :param transformed_shapes: example input fo the alpha shape
    {
     'solver': 'numeric',
     'shape_ode_definitions': ['-1/tau_syn_in**2 * g_in + -2/tau_syn_in * g_in__d', '-1/tau_syn_ex**2 * g_ex + -2/tau_syn_ex * g_ex__d'],
     'shape_state_variables': ['g_in__d', 'g_in', 'g_ex__d', 'g_ex'],
     'shape_initial_values': ['0', 'e*nS/tau_syn_in', '0', 'e*nS/tau_syn_ex'], # wrong order
    }
    :return:
    """
    shape_names = []
    for shape_state_variable in transformed_shapes["shape_state_variables"]:
        if '__' not in shape_state_variable:
            shape_names.append(shape_state_variable)
    shape_name_to_shape_state_variables = {}
    shape_name_to_initial_values = {}
    shape_state_variable_to_ode = {}
    working_index_variables = 0
    working_index_odes = 0
    for shape_name in shape_names:
        matcher_shape = re.compile(shape_name + r"(__\d+)?")
        initial_values = []
        shape_state_variables = []
        shape_state_odes = []

        while working_index_variables < len(transformed_shapes["shape_state_variables"]) and \
                matcher_shape.match(transformed_shapes["shape_state_variables"][working_index_variables]):
            initial_values.append(transformed_shapes["shape_initial_values"][
                                      working_index_variables])  # currently these variables are disoredered. fix it.
            shape_state_variables = [transformed_shapes["shape_state_variables"][
                                         working_index_variables]] + shape_state_variables
            shape_state_odes.append(transformed_shapes["shape_state_variables"][working_index_variables])
            working_index_variables = working_index_variables + 1
        shape_state_odes[len(shape_state_odes) - 1] = transformed_shapes["shape_ode_definitions"][working_index_odes]
        working_index_odes = working_index_odes + 1

        shape_name_to_shape_state_variables[shape_name] = shape_state_variables
        shape_name_to_initial_values[shape_name] = initial_values
        shape_state_variable_to_ode[shape_name] = shape_state_odes
    return shape_names, shape_name_to_initial_values, shape_name_to_shape_state_variables, shape_state_variable_to_ode
