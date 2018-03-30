#
# CoCoInvariantIsBoolean.py
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
from pynestml.modelprocessor.ModelVisitor import NESTMLVisitor

from pynestml.modelprocessor.PredefinedTypes import PredefinedTypes
from pynestml.utils.Logger import LOGGING_LEVEL, Logger
from pynestml.utils.Messages import Messages


class CoCoInvariantIsBoolean(CoCo):
    """
    This coco checks that all invariants are of type boolean

    """

    @classmethod
    def checkCoCo(cls, _neuron=None):
        """
        Ensures the coco for the handed over neuron.
        :param _neuron: a single neuron instance.
        :type _neuron: ASTNeuron
        """
        assert (_neuron is not None and isinstance(_neuron, ASTNeuron)), \
            '(PyNestML.CoCo.BufferNotAssigned) No or wrong type of neuron provided (%s)!' % type(_neuron)
        visitor = InvariantTypeVisitor()
        _neuron.accept(visitor)
        return


class InvariantTypeVisitor(NESTMLVisitor):
    """
    Checks if for each invariant, the type is boolean.
    """

    def visit_declaration(self, _declaration=None):
        """
        Checks the coco for a declaration.
        :param _declaration: a single declaration.
        :type _declaration: ASTDeclaration
        """
        if _declaration.hasInvariant():
            invariantType = _declaration.getInvariant().type
            if invariantType is None or isinstance(invariantType, ErrorTypeSymbol):
                code, message = Messages.getTypeCouldNotBeDerived(str(_declaration.getInvariant()))

                Logger.log_message(error_position=_declaration.getInvariant().getSourcePosition(), _code=code,
                                   message=message, log_level=LOGGING_LEVEL.ERROR)
            elif not invariantType.equals(PredefinedTypes.getBooleanType()):
                code, message = Messages.getTypeDifferentFromExpected(PredefinedTypes.getBooleanType(),
                                                                      invariantType)
                Logger.log_message(error_position=_declaration.getInvariant().getSourcePosition(), _code=code,
                                   message=message, log_level=LOGGING_LEVEL.ERROR)

        return
