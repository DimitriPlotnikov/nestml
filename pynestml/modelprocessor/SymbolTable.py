#
# SymbolTable.py
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
from pynestml.modelprocessor.Scope import Scope, ScopeType


class SymbolTable(object):
    """
    This class is used to store a single symbol table, consisting of scope and symbols.
    
    Attributes:
        __name2scope A dict from the name of a neuron to the corresponding scope. Type str->Scope
        __source_position The source position of the overall compilation unit. Type ASTSourcePosition
    """
    __name2scope = {}
    __source_position = None

    @classmethod
    def initialize_symbol_table(cls, _source_position):
        """
        Standard initializer.
        """
        from pynestml.modelprocessor.ASTSourcePosition import ASTSourcePosition
        assert (isinstance(_source_position, ASTSourcePosition)), \
            '(PyNestML.SymbolTable.SymbolTable) Wrong type of source position provided (%s)!' % type(
                _source_position)
        cls.__source_position = _source_position
        cls.__name2scope = {}
        return

    @classmethod
    def add_neuron_scope(cls, _name, _scope):
        """
        Adds a single neuron scope to the set of stored scopes.
        :return: a single scope element.
        :rtype: Scope
        """
        assert (isinstance(_scope, Scope)), \
            '(PyNestML.SymbolTable.SymbolTable) Wrong type of scope provided (%s)!' % type(_scope)
        assert (_scope.getScopeType() == ScopeType.GLOBAL), \
            '(PyNestML.SymbolTable.SymbolTable) Only global scopes can be added!'
        assert (isinstance(_name, str)), \
            '(PyNestML.SymbolTable.SymbolTable) Wrong type of name provided (%s)!' % type(_name)
        if _name not in cls.__name2scope.keys():
            cls.__name2scope[_name] = _scope
        return

    @classmethod
    def delete_neuron_scope(cls, _name):
        """
        Deletes a single neuron scope from the set of stored scopes.
        :return: the name of the scope to delete.
        :rtype: Scope
        """
        assert (isinstance(_name, Scope)), \
            '(PyNestML.SymbolTable.SymbolTable) No or wrong type of name provided (%s)!' % type(_name)
        if _name in cls.__name2scope.keys():
            del cls.__name2scope[_name]
        return

    @classmethod
    def cleanup(cls):
        """
        Deletes all entries as stored in the symbol table.
        """
        del cls.__name2scope
        cls.__name2scope = {}
        return

    @classmethod
    def print_symboltable(cls):
        """
        Prints the content of this symbol table.
        """
        ret = ''
        for _name in cls.__name2scope.keys():
            ret += '--------------------------------------------------\n'
            ret += _name + ':\n'
            ret += cls.__name2scope[_name].printScope()
        return ret
