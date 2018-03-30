#
# ASTIfClause.py
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

from pynestml.modelprocessor.ASTNode import ASTNode
from pynestml.modelprocessor.ASTExpression import ASTExpression
from pynestml.modelprocessor.ASTBlock import ASTBlock
from pynestml.modelprocessor.ASTSimpleExpression import ASTSimpleExpression


class ASTIfClause(ASTNode):
    """
    This class is used to store a single if-clause.
    Grammar:
        ifClause : 'if' expr BLOCK_OPEN block;
    """
    __condition = None
    __block = None

    def __init__(self, _condition=None, _block=None, _sourcePosition=None):
        """
        Standard constructor.
        :param _condition: the condition of the block.
        :type _condition: ASTExpression
        :param _block: a block of statements.
        :type _block: ASTBlock
        :param _sourcePosition: the position of this element in the source file.
        :type _sourcePosition: ASTSourcePosition.
        """
        assert (_condition is not None and (isinstance(_condition, ASTExpression) or
                                            isinstance(_condition, ASTSimpleExpression))), \
            '(PyNestML.AST.IfClause) No or wrong type of condition provided (%s)!' % type(_condition)
        assert (_block is not None and isinstance(_block, ASTBlock)), \
            '(PyNestML.AST.IfClause) No or wrong type of block provided (%s)!' % type(_block)
        super(ASTIfClause, self).__init__(_sourcePosition)
        self.__block = _block
        self.__condition = _condition
        return

    @classmethod
    def makeASTIfClause(cls, _condition=None, _block=None, _sourcePosition=None):
        """
        The factory method of the ASTIfClause class.
        :param _condition: the condition of the block.
        :type _condition: ASTExpression
        :param _block: a block of statements.
        :type _block: ASTBlock
        :param _sourcePosition: the position of this element in the source file.
        :type _sourcePosition: ASTSourcePosition.
        :return: a new block
        :rtype: ASTIfClause
        """
        return cls(_condition, _block, _sourcePosition)

    def getCondition(self):
        """
        Returns the condition of the block.
        :return: the condition.
        :rtype: ASTExpression
        """
        return self.__condition

    def getBlock(self):
        """
        Returns the block of statements.
        :return: the block of statements.
        :rtype: ASTBlock
        """
        return self.__block

    def getParent(self, _ast=None):
        """
        Indicates whether a this node contains the handed over node.
        :param _ast: an arbitrary ast node.
        :type _ast: AST_
        :return: AST if this or one of the child nodes contains the handed over element.
        :rtype: AST_ or None
        """
        if self.getCondition() is _ast:
            return self
        elif self.getCondition().getParent(_ast) is not None:
            return self.getCondition().getParent(_ast)
        if self.getBlock() is _ast:
            return self
        elif self.getBlock().getParent(_ast) is not None:
            return self.getBlock().getParent(_ast)
        return None

    def __str__(self):
        """
        Returns a string representation of the if clause.
        :return: a string representation
        :rtype: str
        """
        return 'if ' + str(self.getCondition()) + ':\n' + str(self.getBlock())

    def equals(self, _other=None):
        """
        The equals method.
        :param _other: a different object.
        :type _other: object
        :return: True if equals, otherwise False.
        :rtype: bool
        """
        if not isinstance(_other, ASTIfClause):
            return False
        return self.getCondition().equals(_other.getCondition()) and self.getBlock().equals(_other.getBlock())
