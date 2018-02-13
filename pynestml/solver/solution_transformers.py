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
    compute_state_shape_variables_updates, replaceIntegrateCallThroughPropagation, add_declaration_to_update_block, \
    add_assignment_to_update_block
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
    print(neuron)
    neuron = replaceIntegrateCallThroughPropagation(neuron, exact_solution.const_input,
                                                                            exact_solution.ode_var_update_instructions)

    for variable in stateShapeVariablesWithInitialValues:
        neuron.addToStateBlock(ASTCreator.createDeclaration(variable[0] + ' real'))

    # copy initial block variables to the state block, since they are not backed through an ODE.
    for decl in neuron.getInitialValuesDeclarations():
        neuron.addToStateBlock(decl)
    # get rid of the ODE specification since the model is solved exactly and all ODEs are removed.
    if neuron.get_initial_blocks() is not None:
        neuron.get_initial_blocks().clear()
    if neuron.get_equations_blocks() is not None:
        neuron.get_equations_blocks().clear()
    return neuron


def add_state_updates(state_shape_variables_updates, neuron):
    # type: (map[str, str], ASTNeuron) -> ASTNeuron
    """
    Adds all update instructions as contained in the solver output to the update block of the neuron.
    :param state_shape_variables_updates: map of variables to corresponding updates during the update step.
    :param neuron: a single neuron
    :return: a modified version of the neuron
    """

    for variable in state_shape_variables_updates:
        declaration_statement = variable + '__tmp real = ' + state_shape_variables_updates[variable]
        add_declaration_to_update_block(ASTCreator.createDeclaration(declaration_statement), neuron)

    for variable in state_shape_variables_updates:
        add_assignment_to_update_block(ASTCreator.createAssignment(variable + ' = ' + variable + '__tmp'), neuron)
    return neuron
