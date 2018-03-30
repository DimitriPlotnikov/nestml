import json
from unittest import TestCase

from pynestml.codegeneration.nest_codegeneration import solve_ode_with_shapes, make_functions_self_contained, \
    replace_functions_through_defining_expressions, solve_functional_shapes
from pynestml.modelprocessor import ASTSymbolTableVisitor
from pynestml.modelprocessor.ModelParser import ModelParser
from pynestml.solver.solution_transformers import integrate_exact_solution, functional_shapes_to_odes
from pynestml.utils.OdeTransformer import OdeTransformer
from tests.nestml_models_paths import iaf_cond_alpha_path, iaf_psc_alpha_path


class SolutionTransformerTest(TestCase):

    def test_exact_solution_integration(self):
        compilation_unit = ModelParser.parse_file_and_build_symboltable(iaf_psc_alpha_path)
        assert len(compilation_unit.getNeuronList()) == 1
        ast_neuron = compilation_unit.getNeuronList()[0]

        OdeTransformer.refactor_convolve_call(ast_neuron.get_equations_block())
        make_functions_self_contained(ast_neuron.get_equations_block().get_functions())
        replace_functions_through_defining_expressions(
            ast_neuron.get_equations_block().get_equations(),
            ast_neuron.get_equations_block().get_functions())
        
        equations_block = ast_neuron.get_equations_block()
        exact_solution = solve_ode_with_shapes(equations_block)
        self.assertTrue(exact_solution["solver"] is "analytical")
        print("Encoded exact solution")
        print(json.dumps(exact_solution, indent=4, sort_keys=True))

        integrate_exact_solution(ast_neuron, exact_solution)
        ASTSymbolTableVisitor.ASTSymbolTableVisitor.updateSymbolTable(ast_neuron)
        found_propagator_element = False
        for symbol in ast_neuron.getInternalSymbols():
            if "__P_I_shape_in" in symbol.getSymbolName():
                found_propagator_element = True
                break
        self.assertTrue(found_propagator_element)

    def test_numeric_solution(self):
        compilation_unit = ModelParser.parse_file_and_build_symboltable(iaf_cond_alpha_path)
        assert len(compilation_unit.getNeuronList()) == 2
        ast_neuron = compilation_unit.getNeuronList()[0]
        for shape in ast_neuron.get_equations_block().get_shapes():
            self.assertTrue(shape.getVariable().getDifferentialOrder() == 0)

        OdeTransformer.refactor_convolve_call(ast_neuron.get_equations_block())
        make_functions_self_contained(ast_neuron.get_equations_block().get_functions())
        replace_functions_through_defining_expressions(
            ast_neuron.get_equations_block().get_equations(),
            ast_neuron.get_equations_block().get_functions())

        equations_block = ast_neuron.get_equations_block()
        exact_solution = solve_functional_shapes(equations_block)
        self.assertTrue(exact_solution["solver"] is "numeric")

        ode_shapes = solve_functional_shapes(equations_block)
        functional_shapes_to_odes(ast_neuron, ode_shapes)
        ASTSymbolTableVisitor.ASTSymbolTableVisitor.updateSymbolTable(ast_neuron)

        for shape in ast_neuron.get_equations_block().get_shapes():
            self.assertTrue(shape.getVariable().getDifferentialOrder() > 0)
