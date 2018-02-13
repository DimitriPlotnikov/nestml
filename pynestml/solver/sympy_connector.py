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
import re

from odetoolbox import analysis

from pynestml.codegeneration.ExpressionsPrettyPrinter import ExpressionsPrettyPrinter
from pynestml.modelprocessor.ASTEquationsBlock import ASTEquationsBlock
from pynestml.utils.OdeTransformer import OdeTransformer

variable_matching_template = r'(\b)({})(\b)'


def transform_ode_and_shapes_to_json(equations_block):
    # type: (ASTEquationsBlock) -> dict[str, list]
    """
    Converts AST node to a JSON representation
    :param equations_block:equations_block
    :return: json mapping: {odes: [...], shape: [...]}
    """
    printer = ExpressionsPrettyPrinter()
    equations_block = OdeTransformer.refactor_convolve_call(equations_block)
    result = {"odes": [], "shapes": []}

    for equation in equations_block.get_equations():
        result["odes"].append({"symbol": equation.getLhs().getName(),
                               "definition": printer.printExpression(equation.getRhs())})

    for shape in equations_block.get_shapes():
        result["shapes"].append({"type": "function",
                                 "symbol": shape.getVariable().getCompleteName(),
                                 "definition": printer.printExpression(shape.getExpression())})

    result["parameters"] = []  # ode-framework requires this.
    return result


def transform_functions_json(equations_block):
    # type: (ASTEquationsBlock) -> list[dict[str, str]]
    """
    Converts AST node to a JSON representation
    :param equations_block:equations_block
    :return: json mapping: {odes: [...], shape: [...]}
    """
    printer = ExpressionsPrettyPrinter()
    equations_block = OdeTransformer.refactor_convolve_call(equations_block)
    result = []

    for fun in equations_block.get_functions():
        result.append({"symbol": fun.getVariableName(),
                       "definition": printer.printExpression(fun.getExpression())})

    return result


def make_definitions_self_contained(functions):
    """
    Make function definition self contained, e.g. without any references to functions from `functions`.
    :param functions: A sorted list with entries {"symbol": "name", "definition": "expression"}.
    :return: A list with entries {"symbol": "name", "definition": "expression"}. Expressions don't depend on each other.
    """
    for source in functions:
        for target in functions:
            matcher = re.compile(variable_matching_template.format(source["symbol"]))
            target["definition"] = re.sub(matcher, "(" + source["definition"] + ")", target["definition"])
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
    for fun in functions:
        for target in definitions:
            matcher = re.compile(variable_matching_template.format(fun["symbol"]))
            target["definition"] = re.sub(matcher, "(" + fun["definition"] + ")", target["definition"])
    return definitions


def solve_ode_with_shapes(equations_block):
    # type: (ASTEquationsBlock) -> dict[str, list]
    odes_shapes_json = transform_ode_and_shapes_to_json(equations_block)
    functions_json = transform_functions_json(equations_block)
    functions_json = make_definitions_self_contained(functions_json)

    odes_shapes_json["shapes"] = refactor(odes_shapes_json["shapes"], functions_json)
    odes_shapes_json["odes"] = refactor(odes_shapes_json["odes"], functions_json)

    return analysis(odes_shapes_json)
