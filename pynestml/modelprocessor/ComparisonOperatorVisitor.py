#
# ComparisonOperatorVisitor.py
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

"""
expression : left=expression comparisonOperator right=expression
"""
from pynestml.modelprocessor.PredefinedTypes import PredefinedTypes
from pynestml.modelprocessor.ErrorStrings import ErrorStrings
from pynestml.modelprocessor.ModelVisitor import NESTMLVisitor
from pynestml.modelprocessor.Either import Either
from pynestml.modelprocessor.ASTExpression import ASTExpression
from pynestml.utils.Logger import Logger
from pynestml.utils.LoggingLevel import LOGGING_LEVEL
from pynestml.utils.Messages import MessageCode


class ComparisonOperatorVisitor(NESTMLVisitor):
    """
    Visits a single expression consisting of a binary comparison operator.
    """

    def visitExpression(self, _expr=None):
        """
        Visits a single comparison operator expression and updates the type.
        :param _expr: an expression
        :type _expr: ASTExpression
        """
        assert (_expr is not None and isinstance(_expr, ASTExpression)), \
            '(PyNestML.Visitor.ConditionVisitor) No or wrong type of expression provided (%s)!' % type(_expr)
        lhsTypeE = _expr.getLhs().getTypeEither()
        rhsTypeE = _expr.getRhs().getTypeEither()

        if lhsTypeE.isError():
            _expr.setTypeEither(lhsTypeE)
            return
        if rhsTypeE.isError():
            _expr.setTypeEither(rhsTypeE)
            return

        lhsType = lhsTypeE.getValue()
        rhsType = rhsTypeE.getValue()

        if ((lhsType.isReal() or lhsType.isInteger()) and (rhsType.isReal() or rhsType.isInteger())) \
                or (lhsType.equals(rhsType) and lhsType.isNumeric()) or (lhsType.isBoolean() and rhsType.isBoolean()):
            _expr.setTypeEither(Either.value(PredefinedTypes.getBooleanType()))
            return

        # Error message for any other operation
        if (lhsType.isUnit() and rhsType.isNumeric()) or (rhsType.isUnit() and lhsType.isNumeric()):
            # if the incompatibility exists between a unit and a numeric, the c++ will still be fine, just WARN
            errorMsg = ErrorStrings.messageComparison(self, _expr.getSourcePosition())
            _expr.setTypeEither(Either.value(PredefinedTypes.getBooleanType()))
            Logger.log_message(message=errorMsg, code=MessageCode.SOFT_INCOMPATIBILITY,
                               error_position=_expr.getSourcePosition(),
                               log_level=LOGGING_LEVEL.WARNING)
            return
        else:
            # hard incompatibility, cannot recover in c++, ERROR
            errorMsg = ErrorStrings.messageComparison(self, _expr.getSourcePosition())
            _expr.setTypeEither(Either.error(errorMsg))
            Logger.log_message(code=MessageCode.HARD_INCOMPATIBILITY,
                               error_position=_expr.getSourcePosition(),
                               message=errorMsg, log_level=LOGGING_LEVEL.ERROR)
            return
