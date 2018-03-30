#
# StringTypeSymbol.py
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
from copy import copy

from pynestml.modelprocessor.TypeSymbol import TypeSymbol


class StringTypeSymbol(TypeSymbol):
    def isNumeric(self):
        return False

    def isPrimitive(self):
        return True

    def __init__(self):
        super(StringTypeSymbol, self).__init__(_name='string')

    def print_symbol(self):
        result = 'string'
        if self.is_buffer:
            result += ' buffer'
        return result

    def _get_concrete_nest_type(self):
        return 'std::string'

    def __add__(self, other):
        from pynestml.modelprocessor.ErrorTypeSymbol import ErrorTypeSymbol
        from pynestml.modelprocessor.VoidTypeSymbol import VoidTypeSymbol
        if other.is_instance_of(ErrorTypeSymbol):
            return other
        if not other.is_instance_of(VoidTypeSymbol):
            return self
        return self.binary_operation_not_defined_error('+', other)

    def is_castable_to(self, _other_type):
        return False
