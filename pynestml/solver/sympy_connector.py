#
# sympy_connector.py
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
from copy import deepcopy

from pynestml.codegeneration.ExpressionsPrettyPrinter import ExpressionsPrettyPrinter
from pynestml.modelprocessor.ASTEquationsBlock import ASTEquationsBlock
from pynestml.modelprocessor.ASTOdeEquation import ASTOdeEquation
from pynestml.modelprocessor.ASTOdeFunction import ASTOdeFunction
from pynestml.modelprocessor.ASTOdeShape import ASTOdeShape
from pynestml.utils.OdeTransformer import OdeTransformer


def transform_ode_and_shapes_to_json(equations_block):
    # type: (ASTEquationsBlock) -> dict[str, list]
    """
    Converts AST node to a JSON representation
    :param equations_block:equations_block
    :return: json mapping: {odes: [...], shape: [...]}
    """
    printer = ExpressionsPrettyPrinter()
    result = {"odes": [], "shapes": []}

    for equation in equations_block.get_equations():
        result["odes"].append({"symbol": equation.getLhs().getCompleteName(),
                               "definition": printer.printExpression(equation.getRhs())})

    for shape in equations_block.get_shapes():
        result["shapes"].append({"symbol": shape.getVariable().getCompleteName(),
                                 "definition": printer.printExpression(shape.getExpression())})

    return result


def transform_functions_json(equations_block):
    # type: (ASTEquationsBlock) -> list[dict[str, str]]
    """
    Converts AST node to a JSON representation
    :param equations_block:equations_block
    :return: json mapping: {odes: [...], shape: [...]}
    """
    printer = ExpressionsPrettyPrinter()
    result = []

    for fun in equations_block.get_functions():
        result.append({"symbol": fun.getVariableName(),
                       "definition": printer.printExpression(fun.getExpression())})

    return result

## TODO write and test extract functions
def prepare_functions(functions):
    """
    Make function definition self contained, e.g. without any references to functions from `functions`.
    :param functions: A sorted list with entries {"symbol": "name", "definition": "expression"}.
    :return: A list with entries {"symbol": "name", "definition": "expression"}. Expressions don't depend on each other.
    """
    functions = deepcopy(functions)
    for source in functions:
        for target in functions:
            target["definition"] = target["definition"].replace(source["symbol"], source["definition"])
    return functions


def refactor(definitions, functions):
    """
    Refactors symbols form `functions` in `definitions` with corresponding defining expressions from `functions`.
    :param definitions: A sorted list with entries {"symbol": "name", "definition": "expression"} that should be made
    free from.
    :param functions: A sorted list with entries {"symbol": "name", "definition": "expression"} with functions which
    must be replaced in `definitions`.
    :return: A list with definitions. Expressions in `definitions` don't depend on functions from `functions`.
    """
    functions = deepcopy(functions)
    for fun in functions:
        for definition in definitions:
            definition["definition"] = definition["definition"].replace(fun["symbol"], fun["definition"])
    return functions


class SolverInput(object):
    """
    Captures the ODE block for the processing in the SymPy. Generates corresponding json representation.
    """
    __shapes = []
    __odes = []
    __printer = None

    def __init__(self):
        """
        Standard constructor.
        """
        self.__printer = ExpressionsPrettyPrinter()
        return

    def from_ode_with_shapes(self, _equations_block):
        """
        Standard constructor providing the basic functionality to transform equation blocks to json format.
        :param _equations_block: a single equation block.
        :type _equations_block: ASTEquationsBlock
        """
        assert (isinstance(_equations_block, ASTEquationsBlock)), \
            '(PyNestML.Solver.Input) Wrong type of equations block provided (%s)!' % _equations_block
        working_copy = deepcopy(_equations_block)
        working_copy = OdeTransformer.replaceSumCalls(working_copy)
        self.__ode = self.print_equation(working_copy.get_equations()[0])
        self.__functions = list()

        self.__shapes = list()
        for shape in working_copy.get_shapes():
            self.__shapes.append(self.print_shape(shape))
        return self

    def from_shapes(self, _shapes):
        """
        The same functionality as in the case of from_ode_with_shapes, but now only shapes are solved
        :param _shapes: a list of shapes
        :type _shapes: list(ASTOdeShape)
        """
        self.__shapes = list()
        for shape in _shapes:
            self.__shapes.append(self.print_shape(shape))
        self.__ode = None
        self.__functions = list()
        return self

    def print_equation(self, _equation):
        """
        Prints an equation to a processable format.
        :param _equation: a single equation
        :type _equation: ASTOdeEquation
        :return: the corresponding string representation
        :rtype: str
        """
        assert (_equation is not None and isinstance(_equation, ASTOdeEquation)), \
            '(PyNestML.Solver.Input) No or wrong type of equation provided (%s)!' % type(_equation)
        return _equation.getLhs().getCompleteName() + ' = ' + self.__printer.printExpression(_equation.getRhs())

    def print_shape(self, _shape=None):
        """
        Prints a single shape to a processable format.
        :param _shape: a single shape
        :type _shape: ASTOdeShape
        :return: the corresponding string representation
        :rtype: str
        """
        assert (_shape is not None and isinstance(_shape, ASTOdeShape)), \
            '(PyNestML.Solver.Input) No or wrong type of shape provided (%s)!' % type(_shape)
        return _shape.getVariable().getCompleteName() + ' = ' \
               + self.__printer.printExpression(_shape.getExpression())

    def print_function(self, _function=None):
        """
        Prints a single function to a processable format.
        :param _function: a single function
        :type _function: ASTOdeFunction
        :return: the corresponding string representation
        :rtype: str
        """
        assert (_function is not None and isinstance(_function, ASTOdeFunction)), \
            '(PyNestML.Solver.Input) No or wrong type of function provided (%s)!' % type(_function)
        return _function.getVariableName() + ' = ' + self.__printer.printExpression(_function.getExpression())
