#
# CoCoIllegalExpression.py
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
from pynestml.modelprocessor.CoCo import CoCo
from pynestml.modelprocessor.ErrorTypeSymbol import ErrorTypeSymbol
from pynestml.modelprocessor.LoggingHelper import LoggingHelper
from pynestml.modelprocessor.ModelVisitor import NESTMLVisitor
from pynestml.modelprocessor.PredefinedTypes import PredefinedTypes
from pynestml.modelprocessor.TypeCaster import TypeCaster
from pynestml.utils.Logger import LOGGING_LEVEL, Logger
from pynestml.utils.Messages import Messages


class CoCoIllegalExpression(CoCo):
    """
    This coco checks that all expressions are correctly typed.
    """

    @classmethod
    def checkCoCo(cls, _neuron=None):
        """
        Ensures the coco for the handed over neuron.
        :param _neuron: a single neuron instance.
        :type _neuron: ASTNeuron
        """
        assert (_neuron is not None and isinstance(_neuron, ASTNeuron)), \
            '(PyNestML.CoCo.CorrectNumerator) No or wrong type of neuron provided (%s)!' % type(_neuron)
        _neuron.accept(CorrectExpressionVisitor())
        return


class CorrectExpressionVisitor(NESTMLVisitor):
    """
    This visitor checks that all expression correspond to the expected type.
    """

    def visit_declaration(self, _declaration=None):
        """
        Visits a single declaration and asserts that type of lhs is equal to type of rhs.
        :param _declaration: a single declaration.
        :type _declaration: ASTDeclaration
        """
        if _declaration.hasExpression():
            lhs_type = _declaration.getDataType().getTypeSymbol()
            rhs_type = _declaration.getExpression().type
            if isinstance(rhs_type, ErrorTypeSymbol):
                LoggingHelper.drop_missing_type_error(_declaration)
                return
            if self.__types_do_not_match(lhs_type, rhs_type):
                TypeCaster.try_to_recover_or_error(lhs_type, rhs_type, _declaration.getExpression())
        return

    def visit_assignment(self, _assignment=None):
        """
        Visits a single expression and assures that type(lhs) == type(rhs).
        :param _assignment: a single assignment.
        :type _assignment: ASTAssignment
        """
        if _assignment.isDirectAssignment():  # case a = b is simple
            self.handle_simple_assignment(_assignment)
        else:
            self.handle_complex_assignment(_assignment)  # e.g. a *= b
        return

    def handle_complex_assignment(self, _assignment):
        rhs_expr = _assignment.getExpression()
        lhs_variable_symbol = _assignment.resolveLhsVariableSymbol()
        rhs_type_symbol = rhs_expr.type

        if isinstance(rhs_type_symbol, ErrorTypeSymbol):
            LoggingHelper.drop_missing_type_error(_assignment)
            return

        if self.__types_do_not_match(lhs_variable_symbol.getTypeSymbol(), rhs_type_symbol):
            TypeCaster.try_to_recover_or_error(lhs_variable_symbol.getTypeSymbol(), rhs_type_symbol,
                                               _assignment.getExpression())
        return

    @staticmethod
    def __types_do_not_match(_lhs_type_symbol, _rhs_type_symbol):
        return not _lhs_type_symbol.equals(_rhs_type_symbol)

    def handle_simple_assignment(self, _assignment):
        from pynestml.modelprocessor.Symbol import SymbolKind
        lhs_variable_symbol = _assignment.getScope().resolveToSymbol(_assignment.getVariable().getCompleteName(),
                                                                     SymbolKind.VARIABLE)

        rhs_type_symbol = _assignment.getExpression().type
        if isinstance(rhs_type_symbol, ErrorTypeSymbol):
            LoggingHelper.drop_missing_type_error(_assignment)
            return

        if lhs_variable_symbol is not None and self.__types_do_not_match(lhs_variable_symbol.getTypeSymbol(),
                                                                         rhs_type_symbol):
            TypeCaster.try_to_recover_or_error(lhs_variable_symbol.getTypeSymbol(), rhs_type_symbol,
                                               _assignment.getExpression())
        return

    def visit_if_clause(self, _if_clause=None):
        """
        Visits a single if clause and checks that its condition is boolean.
        :param _if_clause: a single elif clause.
        :type _if_clause: ASTIfClause
        """
        cond_type = _if_clause.getCondition().type
        if isinstance(cond_type, ErrorTypeSymbol):
            code, message = Messages.getTypeCouldNotBeDerived(_if_clause.getCondition())
            Logger.log_message(code=code, message=message,
                               error_position=_if_clause.getCondition().getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        elif not cond_type.equals(PredefinedTypes.getBooleanType()):
            code, message = Messages.getTypeDifferentFromExpected(PredefinedTypes.getBooleanType(),
                                                                  cond_type)
            Logger.log_message(code=code, _message=message,
                              error_position=_if_clause.getCondition().getSourcePosition(),
                              log_level=LOGGING_LEVEL.ERROR)
        return

    def visit_elif_clause(self, _elif_clause=None):
        """
        Visits a single elif clause and checks that its condition is boolean.
        :param _elif_clause: a single elif clause.
        :type _elif_clause: ASTElifClause
        """
        cond_type = _elif_clause.getCondition().type
        if isinstance(cond_type, ErrorTypeSymbol):
            code, message = Messages.getTypeCouldNotBeDerived(_elif_clause.getCondition())
            Logger.log_message(code=code, message=message,
                               error_position=_elif_clause.getCondition().getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        elif not cond_type.equals(PredefinedTypes.getBooleanType()):
            code, message = Messages.getTypeDifferentFromExpected(PredefinedTypes.getBooleanType(),
                                                                  cond_type)
            Logger.log_message(code=code, message=message,
                               error_position=_elif_clause.getCondition().getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        return

    def visit_while_stmt(self, _while_stmt=None):
        """
        Visits a single while stmt and checks that its condition is of boolean type.
        :param _while_stmt: a single while stmt
        :type _while_stmt: ASTWhileStmt
        """
        cond_type = _while_stmt.getCondition().type
        if isinstance(cond_type, ErrorTypeSymbol):
            code, message = Messages.getTypeCouldNotBeDerived(_while_stmt.getCondition())
            Logger.log_message(code=code, message=message,
                               error_position=_while_stmt.getCondition().getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        elif not cond_type.equals(PredefinedTypes.getBooleanType()):
            code, message = Messages.getTypeDifferentFromExpected(PredefinedTypes.getBooleanType(),
                                                                  cond_type)
            Logger.log_message(code=code, message=message,
                               error_position=_while_stmt.getCondition().getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        return

    def visit_for_stmt(self, _for_stmt=None):
        """
        Visits a single for stmt and checks that all it parts are correctly defined.
        :param _for_stmt: a single for stmt
        :type _for_stmt: ASTForStmt
        """
        # check that the from stmt is an integer or real
        from_type = _for_stmt.getFrom().type
        if isinstance(from_type, ErrorTypeSymbol):
            code, message = Messages.getTypeCouldNotBeDerived(_for_stmt.getFrom())
            Logger.log_message(code=code, message=message, error_position=_for_stmt.getFrom().getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        elif not (from_type.equals(PredefinedTypes.getIntegerType())
                  or from_type.equals(
                PredefinedTypes.getRealType())):
            code, message = Messages.getTypeDifferentFromExpected(PredefinedTypes.getIntegerType(),
                                                                  from_type)
            Logger.log_message(code=code, message=message, error_position=_for_stmt.getFrom().getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        # check that the to stmt is an integer or real
        to_type = _for_stmt.getTo().type
        if isinstance(to_type, ErrorTypeSymbol):
            code, message = Messages.getTypeCouldNotBeDerived(_for_stmt.getTo())
            Logger.log_message(code=code, message=message, error_position=_for_stmt.getTo().getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        elif not (to_type.equals(PredefinedTypes.getIntegerType())
                  or to_type.equals(PredefinedTypes.getRealType())):
            code, message = Messages.getTypeDifferentFromExpected(PredefinedTypes.getIntegerType(), to_type)
            Logger.log_message(code=code, message=message, error_position=_for_stmt.getTo().getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        return
