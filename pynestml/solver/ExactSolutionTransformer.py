#
# ExactSolutionTransformer.py
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
from pynestml.solver.SolverOutput import SolverOutput
from pynestml.solver.TransformerBase import TransformerBase
from pynestml.modelprocessor.ASTNeuron import ASTNeuron
from pynestml.utils.ASTCreator import ASTCreator
from pynestml.utils.ASTUtils import ASTUtils


class ExactSolutionTransformer(TransformerBase):
    """
    Takes SymPy result with the linear solution of the ODE and the source AST.
    Produces an altered AST with the the exact solution.
    """

    @classmethod
    def addExactSolution(cls, _neuron=None, _solverOutput=None):
        """
        Adds a set of instructions to the given neuron as stated in the solver output.
        :param _neuron: a single neuron instance
        :type _neuron: ASTNeuron
        :param _solverOutput: the generated solver output
        :type _solverOutput: SolverOutput
        :return: a modified neuron
        :rtype: ASTNeuron
        """
        assert (_neuron is not None and isinstance(_neuron, ASTNeuron)), \
            '(PyNestML.Solver.ExactSolutionTransformer) No or wrong type of neuron provided (%s)!' % type(_neuron)
        assert (_solverOutput is not None and isinstance(_solverOutput, SolverOutput)), \
            '(PyNestML.Solver.ExactSolutionTransformer) No or wrong type of solver output provided (%s)!' % type(
                _solverOutput)
        workingVersion = _neuron
        workingVersion.addToInternalBlock(ASTCreator.createDeclaration('__h ms = resolution()'))
        workingVersion = TransformerBase.addVariableToInternals(workingVersion, _solverOutput.ode_var_factor)
        workingVersion = TransformerBase.addVariableToInternals(workingVersion, _solverOutput.const_input)
        workingVersion = TransformerBase.addVariablesToInternals(workingVersion, _solverOutput.propagator_elements)

        stateShapeVariablesWithInitialValues = TransformerBase.computeShapeStateVariablesWithInitialValues(
            _solverOutput)
        # copy initial block variables to the state block, since they are not backed through an ODE.
        for decl in _neuron.getInitialValuesDeclarations():
            _neuron.addToStateBlock(decl)
        workingVersion = TransformerBase.addVariablesToInitialValues(workingVersion,
                                                                     stateShapeVariablesWithInitialValues)
        cls.__addStateUpdates(_solverOutput, workingVersion)

        workingVersion = TransformerBase.replaceIntegrateCallThroughPropagation(workingVersion,_solverOutput.const_input,
                                                                                _solverOutput.ode_var_update_instructions)
        TransformerBase.applyIncomingSpikes(workingVersion)
        # get rid of the ODE stuff since the model is solved exactly and all ODEs are removed.
        workingVersion.get_equations_blocks().clear()

        for variable in stateShapeVariablesWithInitialValues:
            _neuron.addToStateBlock(ASTCreator.createDeclaration(variable[0] + ' real'))

        if workingVersion.getInitialBlocks() is not None:
            workingVersion.getInitialBlocks().clear()
        return workingVersion

    @classmethod
    def __addStateUpdates(cls, _solverOutput=None, _neuron=None):
        """
        Adds all update instructions as contained in the solver output to the update block of the neuron.
        :param _solverOutput: a solver output
        :type _solverOutput: SolverOutput
        :param _neuron: a single neuron
        :type _neuron: ASTNeuron
        :return: a modified version of the neuron
        :rtype: ASTNeuron
        """
        assert (_neuron is not None and isinstance(_neuron, ASTNeuron)), \
            '(PyNestML.Solver.ExactSolutionTransformer) No or wrong type of neuron provided (%s)!' % type(_neuron)
        assert (_solverOutput is not None and isinstance(_solverOutput, SolverOutput)), \
            '(PyNestML.Solver.ExactSolutionTransformer) No or wrong type of solver output provided (%s)!' % type(
                _solverOutput)
        tempVariables = list()
        for tup in _solverOutput.updates_to_shape_state_variables:
            key, value = ASTUtils.getTupleFromSingleDictEntry(tup)
            if key.startswith('__tmp'):
                tempVariables.append(key)
        for var in tempVariables:
            TransformerBase.addDeclarationToUpdateBlock(ASTCreator.createDeclaration(var + ' real'), _neuron)
        for out in _solverOutput.updates_to_shape_state_variables:
            key, value = ASTUtils.getTupleFromSingleDictEntry(out)
            TransformerBase.addAssignmentToUpdateBlock(ASTCreator.createAssignment(key + ' = ' + value), _neuron)
        return


