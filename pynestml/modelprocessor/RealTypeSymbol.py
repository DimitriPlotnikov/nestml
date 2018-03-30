#
# RealTypeSymbol.py
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


class RealTypeSymbol(TypeSymbol):
    def isNumeric(self):
        return True

    def isPrimitive(self):
        return True

    def __init__(self):
        super(RealTypeSymbol, self).__init__(_name='real')

    def print_symbol(self):
        result = 'real'
        if self.is_buffer:
            result += ' buffer'
        return result

    def _get_concrete_nest_type(self):
        return 'double'

    def __mul__(self, other):
        from pynestml.modelprocessor.ErrorTypeSymbol import ErrorTypeSymbol
        from pynestml.modelprocessor.UnitTypeSymbol import UnitTypeSymbol

        if other.is_instance_of(ErrorTypeSymbol):
            return other
        if other.is_instance_of(UnitTypeSymbol):
            return other
        if other.isNumericPrimitive():
            return self
        return self.binary_operation_not_defined_error('*', other)

    def __truediv__(self, other):
        from pynestml.modelprocessor.ErrorTypeSymbol import ErrorTypeSymbol
        from pynestml.modelprocessor.UnitTypeSymbol import UnitTypeSymbol

        if other.is_instance_of(ErrorTypeSymbol):
            return other
        if other.is_instance_of(UnitTypeSymbol):
            return self.inverse_of_unit(other)
        if other.isNumericPrimitive():
            return self
        return self.binary_operation_not_defined_error('/', other)

    def __neg__(self):
        return self

    def __pos__(self):
        return self

    def __invert__(self):
        return self.unary_operation_not_defined_error('~')

    def __pow__(self, power, modulo=None):
        from pynestml.modelprocessor.ErrorTypeSymbol import ErrorTypeSymbol

        if power.is_instance_of(ErrorTypeSymbol):
            return power
        if power.isNumericPrimitive():
            return self
        return self.binary_operation_not_defined_error('**', power)

    def __add__(self, other):
        from pynestml.modelprocessor.ErrorTypeSymbol import ErrorTypeSymbol
        from pynestml.modelprocessor.StringTypeSymbol import StringTypeSymbol
        from pynestml.modelprocessor.UnitTypeSymbol import UnitTypeSymbol
        if other.is_instance_of(ErrorTypeSymbol):
            return other
        if other.is_instance_of(StringTypeSymbol):
            return other
        if other.isNumericPrimitive():
            return self
        if other.is_instance_of(UnitTypeSymbol):
            return self.warn_implicit_cast_from_to(self, other)
        return self.binary_operation_not_defined_error('+', other)

    def __sub__(self, other):
        from pynestml.modelprocessor.ErrorTypeSymbol import ErrorTypeSymbol
        from pynestml.modelprocessor.StringTypeSymbol import StringTypeSymbol
        from pynestml.modelprocessor.UnitTypeSymbol import UnitTypeSymbol
        if other.is_instance_of(ErrorTypeSymbol):
            return other
        if other.isNumericPrimitive():
            return self
        if other.is_instance_of(UnitTypeSymbol):
            return self.warn_implicit_cast_from_to(self, other)
        return self.binary_operation_not_defined_error('-', other)

    def is_castable_to(self, _other_type):
        from pynestml.modelprocessor.BooleanTypeSymbol import BooleanTypeSymbol
        from pynestml.modelprocessor.IntegerTypeSymbol import IntegerTypeSymbol
        if _other_type.is_instance_of(BooleanTypeSymbol):
            return True
        elif _other_type.is_instance_of(IntegerTypeSymbol):
            return True
        else:
            return False
