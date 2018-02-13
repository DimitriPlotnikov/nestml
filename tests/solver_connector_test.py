import json
from unittest import TestCase

from pynestml.modelprocessor.ModelParser import ModelParser
from pynestml.solver.sympy_connector import make_definitions_self_contained, refactor, transform_ode_and_shapes_to_json, \
    transform_functions_json, solve_ode_with_shapes, variable_matching_template
from tests.nestml_models_paths import iaf_psc_alpha_path, iaf_cond_alpha_path


class SolverConnectorTest(TestCase):

    def test_individual_functions(self):
        functions = make_definitions_self_contained([
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
        compilation_unit = ModelParser.parse_file_and_build_symboltable(iaf_psc_alpha_path)
        assert len(compilation_unit.getNeuronList()) == 1
        ast_neuron = compilation_unit.getNeuronList()[0]
        equations_block = ast_neuron.get_equations_block()

        odes_shapes_json = transform_ode_and_shapes_to_json(equations_block)

        for k in odes_shapes_json:
            self.assertTrue(k is "odes" or k is "shapes" or k is "parameters")
            self.assertTrue(len(odes_shapes_json["odes"]) > 0)
            self.assertTrue(len(odes_shapes_json["shapes"]) > 0)

        functions_json = transform_functions_json(equations_block)
        functions_json = make_definitions_self_contained(functions_json)

        self.assertTrue(len(functions_json) == 1)

        self.assertTrue("currents" not in odes_shapes_json["odes"][0]["definition"])
        odes_shapes_json["odes"] = refactor(odes_shapes_json["odes"], functions_json)
        self.assertTrue("currents" in odes_shapes_json["odes"][0]["definition"])

        from odetoolbox import analysis

        result = analysis(odes_shapes_json)
        print(json.dumps(result, indent=4, sort_keys=True))

        self.assertTrue(result["solver"] is "analytical")

    def test_solution_exact_model(self):
        compilation_unit = ModelParser.parse_file_and_build_symboltable(iaf_psc_alpha_path)
        assert len(compilation_unit.getNeuronList()) == 1
        ast_neuron = compilation_unit.getNeuronList()[0]
        equations_block = ast_neuron.get_equations_block()
        result = solve_ode_with_shapes(equations_block)
        self.assertTrue(result["solver"] is "analytical")
        print("Encoded exact solution")
        print(json.dumps(result, indent=4, sort_keys=True))

    def test_numeric_solution(self):
        compilation_unit = ModelParser.parse_file_and_build_symboltable(iaf_cond_alpha_path)
        assert len(compilation_unit.getNeuronList()) == 2
        ast_neuron = compilation_unit.getNeuronList()[0]
        equations_block = ast_neuron.get_equations_block()
        result = solve_ode_with_shapes(equations_block)
        self.assertTrue(result["solver"] is "numeric")
        print("Encoded numeric solution")
        print(json.dumps(result, indent=4, sort_keys=True))

    def test_regex(self):
        source = "V_abs' = -1/Tau * V_abs + 1/C_m *-I+I_syn"

        import re
        matcher = re.compile(variable_matching_template.format("I"))
        print(re.sub(matcher, r"(a+b)", source))
        self.assertTrue("(a+b)" in re.sub(matcher, r"(a+b)", source))
        self.assertTrue("I_syn" in re.sub(matcher, r"(a+b)", source))

        matcher = re.compile(variable_matching_template.format("I_syn"))
        print(re.sub(matcher, r"(a+b)", source))
        self.assertTrue(not ("I_syn" in re.sub(matcher, r"(a+b)", source)))

