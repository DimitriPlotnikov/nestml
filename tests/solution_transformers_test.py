import json
from copy import deepcopy
from unittest import TestCase

from pynestml.modelprocessor.ModelParser import ModelParser
from pynestml.solver.solution_transformers import integrate_exact_solution
from pynestml.solver.sympy_connector import solve_ode_with_shapes
from tests.nestml_models_paths import iaf_psc_alpha_path


class SolverConnectorTest(TestCase):

    def test_exact_solution_integration(self):
        compilation_unit = ModelParser.parse_file_and_build_symboltable(iaf_psc_alpha_path)
        assert len(compilation_unit.getNeuronList()) == 1
        ast_neuron = compilation_unit.getNeuronList()[0]
        
        equations_block = ast_neuron.get_equations_block()
        exact_solution = solve_ode_with_shapes(equations_block)
        self.assertTrue(exact_solution["solver"] is "analytical")
        print("Encoded exact solution")
        print(json.dumps(exact_solution, indent=4, sort_keys=True))

        integrate_exact_solution(ast_neuron, exact_solution)
        self.assertTrue(ast_neuron.get_equations_block() is None)
