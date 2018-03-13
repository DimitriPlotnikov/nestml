#
# PyNestMLFrontend.py
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

import os
import sys

from pynestml.codegeneration.nest_codegeneration import NestCodeGenerator
from pynestml.frontend.FrontendConfiguration import FrontendConfiguration
from pynestml.modelprocessor.CoCosManager import CoCosManager
from pynestml.modelprocessor.ModelParser import ModelParser
from pynestml.modelprocessor.ModelParserExceptions import InvalidPathException
from pynestml.utils.Logger import Logger
from pynestml.utils.LoggingLevel import LOGGING_LEVEL
from pynestml.utils.Messages import Messages


def main(args):
    try:
        FrontendConfiguration.config(args)
    except InvalidPathException:
        print('Not a valid path to model or directory: "%s"!' % FrontendConfiguration.getPath())
        return

    # now proceed to parse all models
    compilationUnits = list()
    for file in FrontendConfiguration.getFiles():
        parsedUnit = ModelParser.parse_file_and_build_symboltable(file)
        if parsedUnit is not None:
            compilationUnits.append(parsedUnit)
    # generate a list of all neurons
    neurons = list()
    for compilationUnit in compilationUnits:
        neurons.extend(compilationUnit.getNeuronList())
    # check if across two files two neurons with same name have been defined
    CoCosManager.checkNotTwoNeuronsAcrossUnits(compilationUnits)
    # now exclude those which are broken, i.e. have errors.
    if not FrontendConfiguration.isDev():
        for neuron in neurons:
            if Logger.hasErrors(neuron):
                code, message = Messages.getNeuronContainsErrors(neuron.getName())
                Logger.log_message(neuron=neuron, code=code, message=message, error_position=neuron.getSourcePosition(),
                                   log_level=LOGGING_LEVEL.INFO)
                neurons.remove(neuron)

    if not FrontendConfiguration.isDryRun():
        nestGenerator = NestCodeGenerator()
        nestGenerator.analyse_and_generate_neurons(neurons)
        nestGenerator.generate_nest_module_code(neurons)
    else:
        code, message = Messages.getDryRun()
        Logger.log_message(neuron=None, code=code, message=message, log_level=LOGGING_LEVEL.INFO)
    if FrontendConfiguration.storeLog():
        with open(str(os.path.join(FrontendConfiguration.getTargetPath(),
                                   'log')) + '.txt', 'w+') as f:
            f.write(str(Logger.getPrintableFormat()))
    return


if __name__ == '__main__':
    main(sys.argv[1:])
