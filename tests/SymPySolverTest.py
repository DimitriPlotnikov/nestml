from unittest import TestCase

from pynestml.modelprocessor.ModelParser import ModelParser


class TestSymPySolver(TestCase):
    def test_solve_ode_with_shapes(self):
        compilation_unit = ModelParser.parse_file_and_build_symboltable("../models/iaf_psc_alpha.nestml")


    def test_transform_shapes_to_odes(self):
        self.fail()
