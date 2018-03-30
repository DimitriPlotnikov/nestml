#
# ExpressionTypeVisitor.py
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


from pynestml.modelprocessor import ASTArithmeticOperator, ASTBitOperator, ASTComparisonOperator, ASTLogicalOperator
from pynestml.modelprocessor.ASTSimpleExpression import ASTSimpleExpression
from pynestml.modelprocessor.ASTSimpleExpression import ASTSimpleExpression
from pynestml.modelprocessor.ASTExpression import ASTExpression
from pynestml.modelprocessor.ModelVisitor import NESTMLVisitor
from pynestml.modelprocessor.BinaryLogicVisitor import BinaryLogicVisitor
from pynestml.modelprocessor.BooleanLiteralVisitor import BooleanLiteralVisitor
from pynestml.modelprocessor.ComparisonOperatorVisitor import ComparisonOperatorVisitor
from pynestml.modelprocessor.ConditionVisitor import ConditionVisitor
from pynestml.modelprocessor.DotOperatorVisitor import DotOperatorVisitor
from pynestml.modelprocessor.FunctionCallVisitor import FunctionCallVisitor
from pynestml.modelprocessor.InfVisitor import InfVisitor
from pynestml.modelprocessor.LineOperatorVisitor import LineOperatorVisitor
from pynestml.modelprocessor.LogicalNotVisitor import LogicalNotVisitor
from pynestml.modelprocessor.NoSemantics import NoSemantics
from pynestml.modelprocessor.NumericLiteralVisitor import NumericLiteralVisitor
from pynestml.modelprocessor.ParenthesesVisitor import ParenthesesVisitor
from pynestml.modelprocessor.PowVisitor import PowVisitor
from pynestml.modelprocessor.StringLiteralVisitor import StringLiteralVisitor
from pynestml.modelprocessor.UnaryVisitor import UnaryVisitor
from pynestml.modelprocessor.VariableVisitor import VariableVisitor


class ExpressionTypeVisitor(NESTMLVisitor):
    """
    This is the main visitor as used to derive the type of an expression. By using different sub-visitors and
    real-self it is possible to adapt to different types of sub-expressions.
    """

    __unaryVisitor = UnaryVisitor()
    __powVisitor = PowVisitor()
    __parenthesesVisitor = ParenthesesVisitor()
    __logicalNotVisitor = LogicalNotVisitor()
    __dotOperatorVisitor = DotOperatorVisitor()
    __lineOperatorVisitor = LineOperatorVisitor()
    __noSemantics = NoSemantics()
    __comparisonOperatorVisitor = ComparisonOperatorVisitor()
    __binaryLogicVisitor = BinaryLogicVisitor()
    __conditionVisitor = ConditionVisitor()
    __functionCallVisitor = FunctionCallVisitor()
    __booleanLiteralVisitor = BooleanLiteralVisitor()
    __numericLiteralVisitor = NumericLiteralVisitor()
    __stringLiteralVisitor = StringLiteralVisitor()
    __variableVisitor = VariableVisitor()
    __infVisitor = InfVisitor()

    def handle(self, _node):
        """
        Handles the handed over node and executes the required sub routines.
        :param _node: a ast node.
        :type _node: AST_
        """
        assert (_node is not None), \
            '(PyNestML.Visitor.ExpressionTypeVisitor) No ast node provided (%s)!' % type(_node)
        self.traverse(_node)
        self.get_real_self().visit(_node)
        self.get_real_self().endvisit(_node)
        return

    def traverse_simple_expression(self, _node):
        """
        Traverses a simple expression and invokes required subroutines.
        :param _node: a single node.
        :type _node: ASTSimpleExpression
        """
        assert (_node is not None and isinstance(_node, ASTSimpleExpression)), \
            '(PyNestML.ExpressionTypeVisitor) No or wrong type of simple-expression provided (%s)!' % type(_node)
        # handle all simpleExpressions
        if isinstance(_node, ASTSimpleExpression):
            # simpleExpression = functionCall
            if _node.getFunctionCall() is not None:
                self.set_real_self(self.__functionCallVisitor)
                return
            # simpleExpression =  (INTEGER|FLOAT) (variable)?
            if _node.getNumericLiteral() is not None or \
                    (_node.getNumericLiteral() is not None and _node.getVariable() is not None):
                self.set_real_self(self.__numericLiteralVisitor)
                return
            # simpleExpression =  variable
            if _node.getVariable() is not None:
                self.set_real_self(self.__variableVisitor)
                return
            # simpleExpression = BOOLEAN_LITERAL
            if _node.isBooleanTrue() or _node.isBooleanFalse():
                self.set_real_self(self.__booleanLiteralVisitor)
                return
            # simpleExpression = isInf='inf'
            if _node.isInfLiteral():
                self.set_real_self(self.__infVisitor)
                return
            # simpleExpression = string=STRING_LITERAL
            if _node.isString():
                self.set_real_self(self.__stringLiteralVisitor)
                return

        return

    def traverse_expression(self, _node):
        """
        Traverses an expression and executes the required sub-routines.
        :param _node: a single ast node
        :type _node: ASTExpression
        """
        assert (_node is not None and isinstance(_node, ASTExpression)), \
            '(PyNestML.ExpressionTypeVisitor) No or wrong type of expression provided (%s)!' % type(_node)
        # Expr = unaryOperator term=expression
        if _node.getExpression() is not None and _node.getUnaryOperator() is not None:
            _node.getExpression().accept(self)
            self.set_real_self(self.__unaryVisitor)
            return

        # Parentheses and logicalNot
        if _node.getExpression() is not None:
            _node.getExpression().accept(self)
            # Expr = leftParentheses='(' term=expression rightParentheses=')'
            if _node.isEncapsulated():
                self.set_real_self(self.__parenthesesVisitor)
                return
            # Expr = logicalNot='not' term=expression
            if _node.isLogicalNot():
                self.set_real_self(self.__logicalNotVisitor)
                return

        # Rules with binary operators
        if _node.getBinaryOperator() is not None:
            binOp = _node.getBinaryOperator()
            # All these rules employ left and right side expressions.
            if _node.getLhs() is not None:
                _node.getLhs().accept(self)
            if _node.getRhs() is not None:
                _node.getRhs().accept(self)
            # Handle all Arithmetic Operators:
            if isinstance(binOp, ASTArithmeticOperator.ASTArithmeticOperator):
                # Expr = <assoc=right> left=expression powOp='**' right=expression
                if binOp.isPowOp():
                    self.set_real_self(self.__powVisitor)
                    return
                # Expr = left=expression (timesOp='*' | divOp='/' | moduloOp='%') right=expression
                if binOp.isTimesOp() or binOp.isDivOp() or binOp.isModuloOp():
                    self.set_real_self(self.__dotOperatorVisitor)
                    return
                # Expr = left=expression (plusOp='+'  | minusOp='-') right=expression
                if binOp.isPlusOp() or binOp.isMinusOp():
                    self.set_real_self(self.__lineOperatorVisitor)
                    return
            # handle all bitOperators:
            if isinstance(binOp, ASTBitOperator.ASTBitOperator):
                # Expr = left=expression bitOperator right=expression
                self.set_real_self(self.__noSemantics)  # TODO: implement something -> future work with more operators
                return
            # handle all comparison Operators:
            if isinstance(binOp, ASTComparisonOperator.ASTComparisonOperator):
                # Expr = left=expression comparisonOperator right=expression
                self.set_real_self(self.__comparisonOperatorVisitor)
                return
            # handle all logical Operators
            if isinstance(binOp, ASTLogicalOperator.ASTLogicalOperator):
                # Expr = left=expression logicalOperator right=expression
                self.set_real_self(self.__binaryLogicVisitor)
                return

        # Expr = condition=expression '?' ifTrue=expression ':' ifNot=expression
        if _node.getCondition() is not None and _node.getIfTrue() is not None and _node.getIfNot() is not None:
            _node.getCondition().accept(self)
            _node.getIfTrue().accept(self)
            _node.getIfNot().accept(self)
            self.set_real_self(self.__conditionVisitor)
            return
