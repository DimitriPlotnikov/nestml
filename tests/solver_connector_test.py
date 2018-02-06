from unittest import TestCase

from pynestml.modelprocessor.ModelParser import ModelParser
from pynestml.solver.sympy_connector import prepare_functions, refactor, transform_ode_and_shapes_to_json, \
    transform_functions_json


class SolverConnectorTest(TestCase):

    def test_individual_functions(self):
        functions = prepare_functions([
            {"symbol": "f1",
             "definition": "a"},
            {"symbol": "f2",
             "definition": "f1 + b"},
            {"symbol": "f3",
             "definition": "f2 + c"}])

        for fun1 in functions:
            for fun2 in functions:
                self.assertTrue(fun1["symbol"] not in fun2["definition"])

        odes = {
            "odes": [
                {"symbol": "V_m",
                 "definition": "f1 + f2 + f3"}
            ]
        }

        odes["odes"] = refactor(odes["odes"], functions)
        for fun in functions:
            for ode in odes["odes"]:
                self.assertTrue(fun["symbol"] not in ode["definition"])

    def test_equations_preparation(self):
        compilation_unit = ModelParser.parse_file_and_build_symboltable("../models/iaf_psc_alpha.nestml")
        assert len(compilation_unit.getNeuronList()) == 1
        ast_neuron = compilation_unit.getNeuronList()[0]
        equations_block = ast_neuron.get_equations_block()

        odes_shapes_json = transform_ode_and_shapes_to_json(equations_block)

        for k in odes_shapes_json:
            self.assertTrue(k is "odes" or k is "shapes" or k is "parameters")
            self.assertTrue(len(odes_shapes_json["odes"]) > 0)
            self.assertTrue(len(odes_shapes_json["shapes"]) > 0)

        functions_json = transform_functions_json(equations_block)
        self.assertTrue(len(functions_json) == 1)

        self.assertTrue("currents" not in odes_shapes_json["odes"][0]["definition"])
        odes_shapes_json["odes"] = refactor(odes_shapes_json["odes"], functions_json)
        self.assertTrue("currents" in odes_shapes_json["odes"][0]["definition"])
        print(str(odes_shapes_json))

        from odetoolbox import analysis

        self.assertTrue(analysis(odes_shapes_json)["solver"] is "analytical")
