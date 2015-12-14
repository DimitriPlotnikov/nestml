/*
 * Copyright (c)  RWTH Aachen. All rights reserved.
 *
 * http://www.se-rwth.de/
 */
package org.nest.codegeneration.sympy;

import de.se_rwth.commons.Names;
import org.nest.nestml._ast.ASTBodyDecorator;
import org.nest.nestml._ast.ASTNESTMLCompilationUnit;
import org.nest.nestml._ast.ASTNeuron;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Optional;

import static com.google.common.base.Preconditions.checkState;
import static de.se_rwth.commons.Names.getPathFromPackage;
import static de.se_rwth.commons.logging.Log.info;

/**
 * Analyzes a neuron for defined ODE. If an ode is defined, it produces a temporary NESTML model
 * with the exact solution if possible or creates an explicit form of the ODEs.
 *
 * @author plotnikov
 */
public class ODEProcessor {
  private final String LOG_NAME = ODEProcessor.class.getName();
  private final ExplicitSolutionTransformer explicitSolutionTransformer = new ExplicitSolutionTransformer();
  enum SolutionType {exact, numeric}

  public ASTNESTMLCompilationUnit process(
      final ASTNESTMLCompilationUnit root,
      final Path outputBase) {
    checkState(root.getNeurons().size() > 0);
    final ASTNeuron neuron = root.getNeurons().get(0);
    final ASTBodyDecorator astBodyDecorator = new ASTBodyDecorator(neuron.getBody());
    if (astBodyDecorator.getOdeDefinition().isPresent()) {
      return handleNeuronWithODE(root, outputBase);
    }
    else {
      return root;
    }

  }

  private ASTNESTMLCompilationUnit handleNeuronWithODE(
      final ASTNESTMLCompilationUnit root,
      final Path outputBase) {

    final Optional<Path> generatedScript = SymPyScriptGenerator.generateSympyODEAnalyzer(
        root.getNeurons().get(0),
        outputBase);

    checkState(generatedScript.isPresent());

    final SymPyScriptEvaluator evaluator = new SymPyScriptEvaluator();
    boolean successfulExecution = evaluator.execute(generatedScript.get());
    checkState(successfulExecution, "Error during solver script evaluation.");
    final Path odeTypePath = Paths.get(outputBase.toString(), SymPyScriptEvaluator.ODE_TYPE);
    final SolutionType solutionType = readSolutionType(odeTypePath);

    if (solutionType.equals(SolutionType.exact)) {
      info("ODE is solved exactly.", LOG_NAME);
      final ASTNESTMLCompilationUnit transformedModel = explicitSolutionTransformer
          .replaceODEWithSymPySolution(
              root,
              Paths.get(outputBase.toString(), SymPyScriptEvaluator.P30_FILE),
              Paths.get(outputBase.toString(), SymPyScriptEvaluator.PSC_INITIAL_VALUE_FILE),
              Paths.get(outputBase.toString(), SymPyScriptEvaluator.STATE_VECTOR_FILE),
              Paths.get(outputBase.toString(), SymPyScriptEvaluator.UPDATE_STEP_FILE));

      return transformedModel;
    }
    else {
      info("ODE is solved numerically.", LOG_NAME);
      return root;
    }

  }

  private SolutionType readSolutionType(Path odeTypePath) {
    try {
      final List<String> type = Files.readAllLines(odeTypePath);
      checkState(type.size() == 1);
      return SolutionType.valueOf(type.get(0));
    }
    catch (IOException e) {
      throw new RuntimeException(e);
    }
  }

}