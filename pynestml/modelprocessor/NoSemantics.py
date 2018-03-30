#
# NoSemantics.py
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
Placeholder for expression productions that are not implemented
"""
from pynestml.modelprocessor.ErrorStrings import ErrorStrings
from pynestml.modelprocessor.ErrorTypeSymbol import ErrorTypeSymbol
from pynestml.modelprocessor.ModelVisitor import NESTMLVisitor

from pynestml.utils.Logger import Logger, LOGGING_LEVEL
from pynestml.utils.Messages import MessageCode


class NoSemantics(NESTMLVisitor):
    """
    A visitor which indicates that there a no semantics for the given node.
    """

    def visit_expression(self, _expr=None):
        """
        Visits a single expression but does not execute any steps besides printing a message. This
        visitor indicates that no functionality has been implemented for this type of nodes.
        :param _expr: a single expression
        :type _expr: ASTExpression or ASTSimpleExpression
        """
        error_msg = ErrorStrings.messageNoSemantics(self, str(_expr), _expr.getSourcePosition())
        _expr.type = ErrorTypeSymbol()
        # just warn though
        Logger.log_message(message=error_msg,
                           code=MessageCode.NO_SEMANTICS,
                           error_position=_expr.getSourcePosition(),
                           log_level=LOGGING_LEVEL.WARNING)
