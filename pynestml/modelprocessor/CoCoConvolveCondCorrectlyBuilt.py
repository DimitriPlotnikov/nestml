#
# CoCoShapeVarInCorrectExpression.py
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
from pynestml.utils.Logger import Logger
from pynestml.utils.LoggingLevel import LOGGING_LEVEL
from pynestml.utils.Messages import Messages
from pynestml.modelprocessor.CoCo import CoCo
from pynestml.modelprocessor.ASTNeuron import ASTNeuron
from pynestml.modelprocessor.Symbol import SymbolKind
from pynestml.modelprocessor.ModelVisitor import NESTMLVisitor


class CoCoConvolveCondCorrectlyBuilt(CoCo):
    """
    This coco ensures that convolve and cond/curr sum are correctly build, i.e.,
    that the first argument is the variable from the initial block and the second argument an input buffer.
    Allowed:
        function I_syn_exc pA =   convolve(g_ex, spikesExc) * ( V_bounded - E_ex )
    Not allowed:
        function I_syn_exc pA =   convolve(g_ex, g_ex) * ( V_bounded - E_ex )

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
        _neuron.accept(ConvolveCheckerVisitor())
        return


class ConvolveCheckerVisitor(NESTMLVisitor):
    """
    Visits a function call and checks that if the function call is a cond_sum,cur_sum or convolve, the parameters
    are correct.
    """

    def visit_function_call(self, _functionCall=None):
        funcName = _functionCall.getName()
        if funcName == 'convolve' or funcName == 'cond_sum' or funcName == 'curr_sum':
            symbolVar = _functionCall.getScope().resolveToSymbol(str(_functionCall.getArgs()[0]),
                                                                 SymbolKind.VARIABLE)
            symbolBuffer = _functionCall.getScope().resolveToSymbol(str(_functionCall.getArgs()[1]),
                                                                    SymbolKind.VARIABLE)
            if symbolVar is not None and not symbolVar.isShape() and not symbolVar.isInitValues():
                code, message = Messages.getFirstArgNotShapeOrEquation(funcName)
                Logger.log_message(code=code, message=message,
                                   error_position=_functionCall.getSourcePosition(), log_level=LOGGING_LEVEL.ERROR)
            if symbolBuffer is not None and not symbolBuffer.isInputBufferSpike():
                code, message = Messages.getSecondArgNotABuffer(funcName)
                Logger.log_message(error_position=_functionCall.getSourcePosition(),
                                   code=code, message=message,
                                   log_level=LOGGING_LEVEL.ERROR)
            return
