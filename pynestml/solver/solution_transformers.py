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
from pynestml.modelprocessor.ASTNeuron import ASTNeuron
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

    if neuron.get_equations_blocks() is not None:
        neuron.remove_equations_blocks()

    return neuron

