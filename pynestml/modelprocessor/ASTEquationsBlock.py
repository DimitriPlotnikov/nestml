#
# ASTEquationsBlock.py
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
from pynestml.modelprocessor.ASTNode import ASTElement
from pynestml.modelprocessor.ASTOdeEquation import ASTOdeEquation
from pynestml.modelprocessor.ASTOdeFunction import ASTOdeFunction
from pynestml.modelprocessor.ASTOdeShape import ASTOdeShape


class ASTEquationsBlock(ASTElement):
    """
    This class is used to store an equations block.
    ASTEquationsBlock a special function definition:
       equations:
         G = (e/tau_syn) * t * exp(-1/tau_syn*t)
         V' = -1/Tau * V + 1/C_m * (I_sum(G, spikes) + I_e + currents)
       end
     @attribute odeDeclaration Block with equations and differential equations.
     Grammar:
          equationsBlock:
            'equations'
            BLOCK_OPEN
              (odeFunction|odeEquation|odeShape|NEWLINE)+
            BLOCK_CLOSE;
    """
    __declarations = None

    def __init__(self, _declarations=None, _sourcePosition=None):
        """
        Standard constructor.
        :param _declarations: a block of definitions.
        :type _declarations: ASTBlock
        :param _sourcePosition: the position of this element in the source file.
        :type _sourcePosition: ASTSourcePosition.
        """
        assert (_declarations is not None and isinstance(_declarations, list)), \
            '(PyNestML.AST.EquationsBlock) No or wrong type of declarations provided (%s)!' % type(_declarations)
        for decl in _declarations:
            assert (decl is not None and (isinstance(decl, ASTOdeShape) or
                                          isinstance(decl, ASTOdeEquation) or
                                          isinstance(decl, ASTOdeFunction))), \
                '(PyNestML.AST.EquationsBlock) No or wrong type of ode-element provided (%s)' % type(decl)
        super(ASTEquationsBlock, self).__init__(_sourcePosition)
        self.__declarations = _declarations

    @classmethod
    def makeASTEquationsBlock(cls, _declarations=None, _sourcePosition=None):
        """
        Factory method of the ASTEquationsBlock class.
        :param _declarations: a block of definitions.
        :type _declarations: ASTBlock
        :param _sourcePosition: the position of this element in the source file.
        :type _sourcePosition: ASTSourcePosition.
        :return: a new ASTEquations object.
        :rtype: ASTEquationsBlock
        """
        return cls(_declarations, _sourcePosition)

    def getDeclarations(self):
        """
        Returns the block of definitions.
        :return: the block
        :rtype: list(ASTOdeFunction|ASTOdeEquation|ASTOdeShape)
        """
        return self.__declarations

    def getParent(self, _ast=None):
        """
        Indicates whether a this node contains the handed over node.
        :param _ast: an arbitrary ast node.
        :type _ast: AST_
        :return: AST if this or one of the child nodes contains the handed over element.
        :rtype: AST_ or None
        """
        for decl in self.getDeclarations():
            if decl is _ast:
                return self
            elif decl.getParent(_ast) is not None:
                return decl.getParent(_ast)
        return None

    def get_equations(self):
        """
        Returns a list of all ode equations in this block.
        :return: a list of all ode equations.
        :rtype: list(ASTOdeEquations)
        """
        ret = list()
        for decl in self.getDeclarations():
            if isinstance(decl, ASTOdeEquation):
                ret.append(decl)
        return ret

    def get_shapes(self):
        """
        Returns a list of all ode shapes in this block.
        :return: a list of all ode shapes.
        :rtype: list(ASTOdeShape)
        """
        ret = list()
        for decl in self.getDeclarations():
            if isinstance(decl, ASTOdeShape):
                ret.append(decl)
        return ret

    def get_functions(self):
        """
        Returns a list of all ode functions in this block.
        :return: a list of all ode shapes.
        :rtype: list(ASTOdeShape)
        """
        ret = list()
        for decl in self.getDeclarations():
            if isinstance(decl, ASTOdeFunction):
                ret.append(decl)
        return ret

    def clear(self):
        """
        Deletes all declarations as stored in this block.
        """
        del self.__declarations
        self.__declarations = list()
        return

    def __str__(self):
        """
        Returns a string representation of the equations block.
        :return: a string representing an equations block.
        :rtype: str
        """
        ret = 'equations:\n'
        for decl in self.getDeclarations():
            ret += str(decl) + '\n'
        return ret + 'end'

    def equals(self, _other=None):
        """
        The equals method.
        :param _other: a different object.
        :type _other: object
        :return: True if equal, otherwise False.
        :rtype: bool
        """
        if not isinstance(_other, ASTEquationsBlock):
            return False
        if len(self.getDeclarations()) != len(_other.getDeclarations()):
            return False
        myDeclarations = self.getDeclarations()
        yourDeclarations = _other.getDeclarations()
        for i in range(0, len(myDeclarations)):
            if not myDeclarations[i].equals(yourDeclarations[i]):
                return False
        return True
