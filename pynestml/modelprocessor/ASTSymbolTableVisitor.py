#
# ASTSymbolTableVisitor.py
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
from pynestml.modelprocessor.ModelVisitor import NESTMLVisitor
from pynestml.modelprocessor.Either import Either
from pynestml.utils.Logger import Logger
from pynestml.utils.LoggingLevel import LOGGING_LEVEL
from pynestml.utils.Messages import Messages
from pynestml.modelprocessor.FunctionSymbol import FunctionSymbol
from pynestml.modelprocessor.PredefinedTypes import PredefinedTypes
from pynestml.modelprocessor.VariableSymbol import VariableSymbol, BlockType, VariableType
from pynestml.modelprocessor.PredefinedFunctions import PredefinedFunctions
from pynestml.modelprocessor.PredefinedVariables import PredefinedVariables
from pynestml.modelprocessor.CoCosManager import CoCosManager


class ASTSymbolTableVisitor(NESTMLVisitor):
    """
    This class is used to create a symbol table from a handed over AST.
    
    Attributes:
        __currentBlockType This variable is used to store information regarding which block with declarations is 
                            currently visited. It is used to update the BlockType of variable symbols to the correct
                            element.
    """
    __currentBlockType = None

    @classmethod
    def updateSymbolTable(cls, _astNeuron=None):
        """
        Creates for the handed over ast the corresponding symbol table.
        :param _astNeuron: a AST neuron object as used to create the symbol table
        :type _astNeuron: ASTNeuron
        :return: a new symbol table
        :rtype: SymbolTable
        """
        Logger.setCurrentNeuron(_astNeuron)
        code, message = Messages.getStartBuildingSymbolTable()
        Logger.log_message(neuron=_astNeuron, code=code, error_position=_astNeuron.getSourcePosition(),
                           message=message, log_level=LOGGING_LEVEL.INFO)
        ASTSymbolTableVisitor.visitNeuron(_astNeuron)
        Logger.setCurrentNeuron(None)
        return

    @classmethod
    def visitNeuron(cls, _neuron=None):
        """
        Private method: Used to visit a single neuron and create the corresponding global as well as local scopes.
        :return: a single neuron.
        :rtype: ASTNeuron
        """
        from pynestml.modelprocessor.ASTNeuron import ASTNeuron
        assert (_neuron is not None and isinstance(_neuron, ASTNeuron)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of neuron provided (%s)!' % type(_neuron)
        # before starting the work on the neuron, make everything which was implicit explicit
        # but if we have a model without an equations block, just skip this step
        if len(_neuron.get_equations_blocks()) == 1:
            cls.makeImplicitOdesExplicit(_neuron.get_equations_block())
        scope = Scope(_scopeType=ScopeType.GLOBAL, _sourcePosition=_neuron.getSourcePosition())
        _neuron.updateScope(scope)
        _neuron.getBody().updateScope(scope)
        # now first, we add all predefined elements to the scope
        variables = PredefinedVariables.getVariables()
        functions = PredefinedFunctions.getFunctionSymbols()
        for symbol in variables.keys():
            _neuron.getScope().addSymbol(variables[symbol])
        for symbol in functions.keys():
            _neuron.getScope().addSymbol(functions[symbol])
        # now create the actual scope
        cls.visitBody(_neuron.getBody())
        # before following checks occur, we need to ensure several simple properties
        CoCosManager.postSymbolTableBuilderChecks(_neuron)
        # the following part is done in order to mark conductance based buffers as such.
        if _neuron.getInputBlocks() is not None and len(_neuron.get_equations_blocks()) == 1 and \
                        len(_neuron.get_equations_block().getDeclarations()) > 0:
            # this case should be prevented, since several input blocks result in  a incorrect model
            if isinstance(_neuron.getInputBlocks(), list):
                buffers = (buffer for bufferA in _neuron.getInputBlocks() for buffer in bufferA.getInputLines())
            else:
                buffers = (buffer for buffer in _neuron.getInputBlocks().getInputLines())
            from pynestml.modelprocessor.ASTOdeShape import ASTOdeShape
            odeDeclarations = (decl for decl in _neuron.get_equations_block().getDeclarations() if
                               not isinstance(decl, ASTOdeShape))
            cls.markConductanceBasedBuffers(_inputLines=buffers, _odeDeclarations=odeDeclarations)
        # now update the equations
        if len(_neuron.get_equations_blocks()) == 1:
            cls.assignOdeToVariables(_neuron.get_equations_block())
        CoCosManager.postOdeSpecificationChecks(_neuron)
        return

    @classmethod
    def visitBody(cls, _body=None):
        """
        Private method: Used to visit a single neuron body and create the corresponding scope.
        :param _body: a single body element.
        :type _body: ASTBody
        """
        from pynestml.modelprocessor.ASTBlockWithVariables import ASTBlockWithVariables
        from pynestml.modelprocessor.ASTUpdateBlock import ASTUpdateBlock
        from pynestml.modelprocessor.ASTEquationsBlock import ASTEquationsBlock
        from pynestml.modelprocessor.ASTInputBlock import ASTInputBlock
        from pynestml.modelprocessor.ASTOutputBlock import ASTOutputBlock
        from pynestml.modelprocessor.ASTFunction import ASTFunction
        for bodyElement in _body.getBodyElements():
            bodyElement.updateScope(_body.getScope())
            if isinstance(bodyElement, ASTBlockWithVariables):
                cls.visitBlockWithVariables(bodyElement)
            elif isinstance(bodyElement, ASTUpdateBlock):
                cls.visitUpdateBlock(bodyElement)
            elif isinstance(bodyElement, ASTEquationsBlock):
                cls.visitEquationsBlock(bodyElement)
            elif isinstance(bodyElement, ASTInputBlock):
                cls.visitInputBlock(bodyElement)
            elif isinstance(bodyElement, ASTOutputBlock):
                cls.visitOutputBlock(bodyElement)
            elif isinstance(bodyElement, ASTFunction):
                cls.visitFunctionBlock(bodyElement)
        return

    @classmethod
    def visitFunctionBlock(cls, _block=None):
        """
        Private method: Used to visit a single function block and create the corresponding scope.
        :param _block: a function block object.
        :type _block: ASTFunction
        """
        from pynestml.modelprocessor.ASTFunction import ASTFunction
        from pynestml.modelprocessor.ASTUnitTypeVisitor import ASTUnitTypeVisitor
        assert (_block is not None and isinstance(_block, ASTFunction)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of function block provided (%s)!' % type(_block)
        cls.__currentBlockType = BlockType.LOCAL  # before entering, update the current block type
        symbol = FunctionSymbol(_scope=_block.getScope(), _elementReference=_block, _paramTypes=list(),
                                _name=_block.getName(), _isPredefined=False)
        symbol.setComment(_block.getComment())
        _block.getScope().addSymbol(symbol)
        scope = Scope(_scopeType=ScopeType.FUNCTION, _enclosingScope=_block.getScope(),
                      _sourcePosition=_block.getSourcePosition())
        _block.getScope().addScope(scope)
        for arg in _block.getParameters():
            # first visit the data type to ensure that variable symbol can receive a combined data type
            arg.getDataType().updateScope(scope)
            cls.visitDataType(arg.getDataType())
            # given the fact that the name is not directly equivalent to the one as stated in the model,
            # we have to get it by the sub-visitor
            typeName = ASTUnitTypeVisitor.visitDatatype(arg.getDataType())
            # first collect the types for the parameters of the function symbol
            symbol.addParameterType(PredefinedTypes.getTypeIfExists(typeName))
            # update the scope of the arg
            arg.updateScope(scope)
            # create the corresponding variable symbol representing the parameter
            varSymbol = VariableSymbol(_elementReference=arg, _scope=scope, _name=arg.getName(),
                                       _blockType=BlockType.LOCAL, _isPredefined=False, _isFunction=False,
                                       _isRecordable=False,
                                       _typeSymbol=PredefinedTypes.getTypeIfExists(typeName),
                                       _variableType=VariableType.VARIABLE)
            scope.addSymbol(varSymbol)
        if _block.hasReturnType():
            _block.getReturnType().updateScope(scope)
            cls.visitDataType(_block.getReturnType())
            symbol.setReturnType(
                PredefinedTypes.getTypeIfExists(ASTUnitTypeVisitor.visitDatatype(_block.getReturnType())))
        else:
            symbol.setReturnType(PredefinedTypes.getVoidType())
        _block.getBlock().updateScope(scope)
        cls.visitBlock(_block.getBlock())
        cls.__currentBlockType = None  # before leaving update the type
        return

    @classmethod
    def visitUpdateBlock(cls, _block=None):
        """
        Private method: Used to visit a single update block and create the corresponding scope.
        :param _block: an update block object.
        :type _block: ASTDynamics
        """
        from pynestml.modelprocessor.ASTUpdateBlock import ASTUpdateBlock
        assert (_block is not None and isinstance(_block, ASTUpdateBlock)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of update-block provided (%s)!' % type(_block)
        cls.__currentBlockType = BlockType.LOCAL
        scope = Scope(_scopeType=ScopeType.UPDATE, _enclosingScope=_block.getScope(),
                      _sourcePosition=_block.getSourcePosition())
        _block.getScope().addScope(scope)
        _block.getBlock().updateScope(scope)
        cls.visitBlock(_block.getBlock())
        cls.__currentBlockType = BlockType.LOCAL
        return

    @classmethod
    def visitBlock(cls, _block=None):
        """
        Private method: Used to visit a single block of statements, create and update the corresponding scope.
        :param _block: a block object.
        :type _block: ASTBlock
        """
        from pynestml.modelprocessor.ASTBlock import ASTBlock
        from pynestml.modelprocessor.ASTSmallStmt import ASTSmallStmt
        from pynestml.modelprocessor.ASTCompoundStmt import ASTCompoundStmt
        assert (_block is not None and isinstance(_block, ASTBlock)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of block provided %s!' % type(_block)
        for stmt in _block.getStmts():
            if isinstance(stmt, ASTSmallStmt):
                stmt.updateScope(_block.getScope())
                cls.visitSmallStmt(stmt)
            elif isinstance(stmt, ASTCompoundStmt):
                stmt.updateScope(_block.getScope())
                cls.visitCompoundStmt(stmt)
        return

    @classmethod
    def visitSmallStmt(cls, _stmt=None):
        """
        Private method: Used to visit a single small statement and create the corresponding sub-scope.
        :param _stmt: a single small statement.
        :type _stmt: ASTSmallStatement
        """
        from pynestml.modelprocessor.ASTSmallStmt import ASTSmallStmt
        assert (_stmt is not None and isinstance(_stmt, ASTSmallStmt)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of small statement provided (%s)!' % type(_stmt)
        if _stmt.isDeclaration():
            _stmt.getDeclaration().updateScope(_stmt.getScope())
            cls.visitDeclaration(_stmt.getDeclaration())
        elif _stmt.isAssignment():
            _stmt.getAssignment().updateScope(_stmt.getScope())
            cls.visitAssignment(_stmt.getAssignment())
        elif _stmt.isFunctionCall():
            _stmt.getFunctionCall().updateScope(_stmt.getScope())
            cls.visitFunctionCall(_stmt.getFunctionCall())
        elif _stmt.isReturnStmt():
            _stmt.getReturnStmt().updateScope(_stmt.getScope())
            cls.visitReturnStmt(_stmt.getReturnStmt())
        return

    @classmethod
    def visitCompoundStmt(cls, _stmt=None):
        """
        Private method: Used to visit a single compound statement and create the corresponding sub-scope.
        :param _stmt: a single compound statement.
        :type _stmt: ASTCompoundStatement
        """
        from pynestml.modelprocessor.ASTCompoundStmt import ASTCompoundStmt
        assert (_stmt is not None and isinstance(_stmt, ASTCompoundStmt)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of compound statement provided (%s)!' % type(_stmt)
        if _stmt.isIfStmt():
            _stmt.getIfStmt().updateScope(_stmt.getScope())
            cls.visitIfStmt(_stmt.getIfStmt())
        elif _stmt.isWhileStmt():
            _stmt.getWhileStmt().updateScope(_stmt.getScope())
            cls.visitWhileStmt(_stmt.getWhileStmt())
        else:
            _stmt.getForStmt().updateScope(_stmt.getScope())
            cls.visitForStmt(_stmt.getForStmt())
        return

    @classmethod
    def visitAssignment(cls, _assignment=None):
        """
        Private method: Used to visit a single assignment and update the its corresponding scope.
        :param _assignment: an assignment object.
        :type _assignment: ASTAssignment
        :return: no return value, since neither scope nor symbol is created
        :rtype: void
        """
        from pynestml.modelprocessor.ASTAssignment import ASTAssignment
        assert (_assignment is not None and isinstance(_assignment, ASTAssignment)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of assignment provided (%s)!' % type(_assignment)
        _assignment.getVariable().updateScope(_assignment.getScope())
        cls.visitVariable(_assignment.getVariable())
        _assignment.getExpression().updateScope(_assignment.getScope())
        cls.visitExpression(_assignment.getExpression())
        return

    @classmethod
    def visitFunctionCall(cls, _functionCall=None):
        """
        Private method: Used to visit a single function call and update its corresponding scope.
        :param _functionCall: a function call object.
        :type _functionCall: ASTFunctionCall
        :return: no return value, since neither scope nor symbol is created
        :rtype: void
        """
        from pynestml.modelprocessor.ASTFunctionCall import ASTFunctionCall
        assert (_functionCall is not None and isinstance(_functionCall, ASTFunctionCall)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of function call provided (%s)!' % type(_functionCall)
        for arg in _functionCall.getArgs():
            arg.updateScope(_functionCall.getScope())
            cls.visitExpression(arg)
        return

    @classmethod
    def visitDeclaration(cls, _declaration=None):
        """
        Private method: Used to visit a single declaration, update its scope and return the corresponding set of
        symbols
        :param _declaration: a declaration object.
        :type _declaration: ASTDeclaration
        :return: the scope is update without a return value.
        :rtype: void
        """
        from pynestml.modelprocessor.ASTDeclaration import ASTDeclaration
        from pynestml.modelprocessor.VariableSymbol import VariableSymbol, BlockType, VariableType
        from pynestml.modelprocessor.ASTUnitTypeVisitor import ASTUnitTypeVisitor
        assert (_declaration is not None and isinstance(_declaration, ASTDeclaration)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong typ of declaration provided (%s)!' % type(_declaration)

        expression = _declaration.getExpression() if _declaration.hasExpression() else None
        typeName = ASTUnitTypeVisitor.visitDatatype(_declaration.getDataType())
        # all declarations in the state block are recordable
        isRecordable = _declaration.isRecordable() or \
                       cls.__currentBlockType == BlockType.STATE or cls.__currentBlockType == BlockType.INITIAL_VALUES
        initValue = _declaration.getExpression() if cls.__currentBlockType == BlockType.INITIAL_VALUES else None
        vectorParameter = _declaration.getSizeParameter()
        for var in _declaration.getVariables():  # for all variables declared create a new symbol
            var.updateScope(_declaration.getScope())
            typeSymbol = PredefinedTypes.getTypeIfExists(typeName)
            symbol = VariableSymbol(_elementReference=_declaration,
                                    _scope=_declaration.getScope(),
                                    _name=var.getCompleteName(),
                                    _blockType=cls.__currentBlockType,
                                    _declaringExpression=expression, _isPredefined=False,
                                    _isFunction=_declaration.isFunction(),
                                    _isRecordable=isRecordable,
                                    _typeSymbol=typeSymbol,
                                    _initialValue=initValue,
                                    _vectorParameter=vectorParameter,
                                    _variableType=VariableType.VARIABLE
                                    )
            symbol.setComment(_declaration.getComment())
            _declaration.getScope().addSymbol(symbol)
            var.setTypeSymbol(Either.value(typeSymbol))
            cls.visitVariable(var)
        _declaration.getDataType().updateScope(_declaration.getScope())
        cls.visitDataType(_declaration.getDataType())
        if _declaration.hasExpression():
            _declaration.getExpression().updateScope(_declaration.getScope())
            cls.visitExpression(_declaration.getExpression())
        if _declaration.hasInvariant():
            _declaration.getInvariant().updateScope(_declaration.getScope())
            cls.visitExpression(_declaration.getInvariant())
        return

    @classmethod
    def visitReturnStmt(cls, _returnStmt=None):
        """
        Private method: Used to visit a single return statement and update its scope.
        :param _returnStmt: a return statement object.
        :type _returnStmt: ASTReturnStmt
        """
        from pynestml.modelprocessor.ASTReturnStmt import ASTReturnStmt
        assert (_returnStmt is not None and isinstance(_returnStmt, ASTReturnStmt)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of return statement provided (%s)!' % type(_returnStmt)
        if _returnStmt.hasExpression():
            _returnStmt.getExpression().updateScope(_returnStmt.getScope())
            cls.visitExpression(_returnStmt.getExpression())
        return

    @classmethod
    def visitIfStmt(cls, _ifStmt=None):
        """
        Private method: Used to visit a single if-statement, update its scope and create the corresponding sub-scope.
        :param _ifStmt: an if-statement object.
        :type _ifStmt: ASTIfStmt
        """
        from pynestml.modelprocessor.ASTIfStmt import ASTIfStmt
        assert (_ifStmt is not None and isinstance(_ifStmt, ASTIfStmt)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of if-statement provided (%s)!' % type(_ifStmt)
        _ifStmt.getIfClause().updateScope(_ifStmt.getScope())
        cls.visitIfClause(_ifStmt.getIfClause())
        for elIf in _ifStmt.getElifClauses():
            elIf.updateScope(_ifStmt.getScope())
            cls.visitElifClause(elIf)
        if _ifStmt.hasElseClause():
            _ifStmt.getElseClause().updateScope(_ifStmt.getScope())
            cls.visitElseClause(_ifStmt.getElseClause())
        return

    @classmethod
    def visitIfClause(cls, _ifClause=None):
        """
        Private method: Used to visit a single if-clause, update its scope and create the corresponding sub-scope.
        :param _ifClause: an if clause.
        :type _ifClause: ASTIfClause
        """
        from pynestml.modelprocessor.ASTIfClause import ASTIfClause
        assert (_ifClause is not None and isinstance(_ifClause, ASTIfClause)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of if-clause provided (%s)!' % type(_ifClause)
        _ifClause.getCondition().updateScope(_ifClause.getScope())
        cls.visitExpression(_ifClause.getCondition())
        _ifClause.getBlock().updateScope(_ifClause.getScope())
        cls.visitBlock(_ifClause.getBlock())
        return

    @classmethod
    def visitElifClause(cls, _elifClause=None):
        """
        Private method: Used to visit a single elif-clause, update its scope and create the corresponding sub-scope.
        :param _elifClause: an elif clause.
        :type _elifClause: ASTElifClause
        """
        from pynestml.modelprocessor.ASTElifClause import ASTElifClause
        assert (_elifClause is not None and isinstance(_elifClause, ASTElifClause)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of elif-clause provided (%s)!' % type(_elifClause)
        _elifClause.getCondition().updateScope(_elifClause.getScope())
        cls.visitExpression(_elifClause.getCondition())
        _elifClause.getBlock().updateScope(_elifClause.getScope())
        cls.visitBlock(_elifClause.getBlock())
        return

    @classmethod
    def visitElseClause(cls, _elseClause=None):
        """
        Private method: Used to visit a single else-clause, update its scope and create the corresponding sub-scope.
        :param _elseClause: an else clause.
        :type _elseClause: ASTElseClause
        """
        from pynestml.modelprocessor.ASTElseClause import ASTElseClause
        assert (_elseClause is not None and isinstance(_elseClause, ASTElseClause)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of else-clause provided (%s)!' % type(_elseClause)
        _elseClause.getBlock().updateScope(_elseClause.getScope())
        cls.visitBlock(_elseClause.getBlock())
        return

    @classmethod
    def visitForStmt(cls, _forStmt=None):
        """
        Private method: Used to visit a single for-stmt, update its scope and create the corresponding sub-scope.
        :param _forStmt: a for-statement.
        :type _forStmt: ASTForStmt
        """
        from pynestml.modelprocessor.ASTForStmt import ASTForStmt
        assert (_forStmt is not None and isinstance(_forStmt, ASTForStmt)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of for-statement provided (%s)!' % type(_forStmt)
        _forStmt.getFrom().updateScope(_forStmt.getScope())
        cls.visitExpression(_forStmt.getFrom())
        _forStmt.getTo().updateScope(_forStmt.getScope())
        cls.visitExpression(_forStmt.getTo())
        _forStmt.getBlock().updateScope(_forStmt.getScope())
        cls.visitBlock(_forStmt.getBlock())
        return

    @classmethod
    def visitWhileStmt(cls, _whileStmt=None):
        """
        Private method: Used to visit a single while-stmt, update its scope and create the corresponding sub-scope.
        :param _whileStmt: a while-statement.
        :type _whileStmt: ASTWhileStmt
        """
        from pynestml.modelprocessor.ASTWhileStmt import ASTWhileStmt
        assert (_whileStmt is not None and isinstance(_whileStmt, ASTWhileStmt)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of while-statement provided (%s)!' % type(_whileStmt)
        _whileStmt.getCondition().updateScope(_whileStmt.getScope())
        cls.visitExpression(_whileStmt.getCondition())
        _whileStmt.getBlock().updateScope(_whileStmt.getScope())
        cls.visitBlock(_whileStmt.getBlock())
        return

    @classmethod
    def visitDataType(cls, _dataType=None):
        """
        Private method: Used to visit a single data-type and update its scope.
        :param _dataType: a data-type.
        :type _dataType: ASTDataType
        """
        from pynestml.modelprocessor.ASTDatatype import ASTDatatype
        assert (_dataType is not None and isinstance(_dataType, ASTDatatype)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of data-type provided (%s)!' % type(_dataType)
        if _dataType.isUnitType():
            _dataType.getUnitType().updateScope(_dataType.getScope())
            return cls.visitUnitType(_dataType.getUnitType())
        # besides updating the scope no operations are required, since no type symbols are added to the scope.
        return

    @classmethod
    def visitUnitType(cls, _unitType=None):
        """
        Private method: Used to visit a single unit-type and update its scope.
        :param _unitType: a unit type.
        :type _unitType: ASTUnitType
        """
        from pynestml.modelprocessor.ASTUnitType import ASTUnitType
        assert (_unitType is not None and isinstance(_unitType, ASTUnitType)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of unit-typ provided (%s)!' % type(_unitType)
        if _unitType.isPowerExpression():
            _unitType.getBase().updateScope(_unitType.getScope())
            cls.visitUnitType(_unitType.getBase())
        elif _unitType.isEncapsulated():
            _unitType.getCompoundUnit().updateScope(_unitType.getScope())
            cls.visitUnitType(_unitType.getCompoundUnit())
        elif _unitType.isDiv() or _unitType.isTimes():
            if isinstance(_unitType.getLhs(), ASTUnitType):  # lhs can be a numeric Or a unit-type
                _unitType.getLhs().updateScope(_unitType.getScope())
                cls.visitUnitType(_unitType.getLhs())
            _unitType.getRhs().updateScope(_unitType.getScope())
            cls.visitUnitType(_unitType.getRhs())
        return

    @classmethod
    def visitExpression(cls, _expr=None):
        """
        Private method: Used to visit a single expression and update its scope.
        :param _expr: an expression.
        :type _expr: ASTExpression
        """
        from pynestml.modelprocessor.ASTSimpleExpression import ASTSimpleExpression
        from pynestml.modelprocessor.ASTExpression import ASTExpression
        from pynestml.modelprocessor.ASTBitOperator import ASTBitOperator
        from pynestml.modelprocessor.ASTLogicalOperator import ASTLogicalOperator
        from pynestml.modelprocessor.ASTComparisonOperator import ASTComparisonOperator
        if isinstance(_expr, ASTSimpleExpression):
            return cls.visitSimpleExpression(_expr)
        assert (_expr is not None and isinstance(_expr, ASTExpression)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of expression provided (%s)!' % type(_expr)
        if _expr.isLogicalNot():
            _expr.getExpression().updateScope(_expr.getScope())
            cls.visitExpression(_expr.getExpression())
        elif _expr.isEncapsulated():
            _expr.getExpression().updateScope(_expr.getScope())
            cls.visitExpression(_expr.getExpression())
        elif _expr.isUnaryOperator():
            _expr.getUnaryOperator().updateScope(_expr.getScope())
            cls.visitUnaryOperator(_expr.getUnaryOperator())
            _expr.getExpression().updateScope(_expr.getScope())
            cls.visitExpression(_expr.getExpression())
        elif _expr.isCompoundExpression():
            _expr.getLhs().updateScope(_expr.getScope())
            cls.visitExpression(_expr.getLhs())
            _expr.getBinaryOperator().updateScope(_expr.getScope())
            if isinstance(_expr.getBinaryOperator(), ASTBitOperator):
                cls.visitBitOperator(_expr.getBinaryOperator())
            elif isinstance(_expr.getBinaryOperator(), ASTComparisonOperator):
                cls.visitComparisonOperator(_expr.getBinaryOperator())
            elif isinstance(_expr.getBinaryOperator(), ASTLogicalOperator):
                cls.visitLogicalOperator(_expr.getBinaryOperator())
            else:
                cls.visitArithmeticOperator(_expr.getBinaryOperator())
            _expr.getRhs().updateScope(_expr.getScope())
            cls.visitExpression(_expr.getRhs())
        if _expr.isTernaryOperator():
            _expr.getCondition().updateScope(_expr.getScope())
            cls.visitExpression(_expr.getCondition())
            _expr.getIfTrue().updateScope(_expr.getScope())
            cls.visitExpression(_expr.getIfTrue())
            _expr.getIfNot().updateScope(_expr.getScope())
            cls.visitExpression(_expr.getIfNot())
        return

    @classmethod
    def visitSimpleExpression(cls, _expr=None):
        """
        Private method: Used to visit a single simple expression and update its scope.
        :param _expr: a simple expression.
        :type _expr: ASTSimpleExpression
        """
        from pynestml.modelprocessor.ASTSimpleExpression import ASTSimpleExpression
        assert (_expr is not None and isinstance(_expr, ASTSimpleExpression)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of simple expression provided (%s)!' % type(_expr)
        if _expr.isFunctionCall():
            _expr.getFunctionCall().updateScope(_expr.getScope())
            cls.visitFunctionCall(_expr.getFunctionCall())
        elif _expr.isVariable() or _expr.hasUnit():
            _expr.getVariable().updateScope(_expr.getScope())
            cls.visitVariable(_expr.getVariable())
        return

    @classmethod
    def visitUnaryOperator(cls, _unaryOp=None):
        """
        Private method: Used to visit a single unary operator and update its scope.
        :param _unaryOp: a single unary operator.
        :type _unaryOp: ASTUnaryOperator
        """
        from pynestml.modelprocessor.ASTUnaryOperator import ASTUnaryOperator
        assert (_unaryOp is not None and isinstance(_unaryOp, ASTUnaryOperator)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of unary operator provided (%s)!' % type(_unaryOp)
        return

    @classmethod
    def visitBitOperator(cls, _bitOp=None):
        """
        Private method: Used to visit a single unary operator and update its scope.
        :param _bitOp: a single bit operator.
        :type _bitOp: ASTBitOperator
        """
        from pynestml.modelprocessor.ASTBitOperator import ASTBitOperator
        assert (_bitOp is not None and isinstance(_bitOp, ASTBitOperator)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of bit operator provided (%s)!' % type(_bitOp)
        return

    @classmethod
    def visitComparisonOperator(cls, _comparisonOp=None):
        """
        Private method: Used to visit a single comparison operator and update its scope.
        :param _comparisonOp: a single comparison operator.
        :type _comparisonOp: ASTComparisonOperator
        """
        from pynestml.modelprocessor.ASTComparisonOperator import ASTComparisonOperator
        assert (_comparisonOp is not None and isinstance(_comparisonOp, ASTComparisonOperator)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of comparison operator provided (%s)!' % type(
                _comparisonOp)
        return

    @classmethod
    def visitLogicalOperator(cls, _logicalOp=None):
        """
        Private method: Used to visit a single logical operator and update its scope.
        :param _logicalOp: a single logical operator.
        :type _logicalOp: ASTLogicalOperator
        """
        from pynestml.modelprocessor.ASTLogicalOperator import ASTLogicalOperator
        assert (_logicalOp is not None and isinstance(_logicalOp, ASTLogicalOperator)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of logical operator provided (%s)!' % type(_logicalOp)
        return

    @classmethod
    def visitVariable(cls, _variable=None):
        """
        Private method: Used to visit a single variable and update its scope.
        :param _variable: a single variable.
        :type _variable: ASTVariable
        """
        from pynestml.modelprocessor.ASTVariable import ASTVariable
        assert (_variable is not None and isinstance(_variable, ASTVariable)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of variable provided (%s)!' % type(_variable)
        return

    @classmethod
    def visitOdeFunction(cls, _odeFunction=None):
        """
        Private method: Used to visit a single ode-function, create the corresponding symbol and update the scope.
        :param _odeFunction: a single ode-function.
        :type _odeFunction: ASTOdeFunction
        """
        from pynestml.modelprocessor.ASTOdeFunction import ASTOdeFunction
        from pynestml.modelprocessor.ASTUnitTypeVisitor import ASTUnitTypeVisitor
        from pynestml.modelprocessor.VariableSymbol import BlockType, VariableType
        assert (_odeFunction is not None and isinstance(_odeFunction, ASTOdeFunction)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of ode-function provided (%s)!' % type(_odeFunction)
        typeSymbol = PredefinedTypes.getTypeIfExists(ASTUnitTypeVisitor.visitDatatype(_odeFunction.getDataType()))
        symbol = VariableSymbol(_elementReference=_odeFunction, _scope=_odeFunction.getScope(),
                                _name=_odeFunction.getVariableName(),
                                _blockType=BlockType.EQUATION,
                                _declaringExpression=_odeFunction.getExpression(),
                                _isPredefined=False, _isFunction=True,
                                _isRecordable=_odeFunction.isRecordable(),
                                _typeSymbol=typeSymbol,
                                _variableType=VariableType.VARIABLE)
        symbol.setComment(_odeFunction.getComment())
        _odeFunction.getScope().addSymbol(symbol)
        _odeFunction.getDataType().updateScope(_odeFunction.getScope())
        cls.visitDataType(_odeFunction.getDataType())
        _odeFunction.getExpression().updateScope(_odeFunction.getScope())
        cls.visitExpression(_odeFunction.getExpression())
        return

    @classmethod
    def visitOdeShape(cls, _odeShape=None):
        """
        Private method: Used to visit a single ode-shape, create the corresponding symbol and update the scope.
        :param _odeShape: a single ode-shape.
        :type _odeShape: ASTOdeShape
        """
        from pynestml.modelprocessor.ASTOdeShape import ASTOdeShape
        from pynestml.modelprocessor.VariableSymbol import VariableSymbol, BlockType
        from pynestml.modelprocessor.Symbol import SymbolKind
        assert (_odeShape is not None and isinstance(_odeShape, ASTOdeShape)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of ode-shape provided (%s)!' % type(_odeShape)
        if _odeShape.getVariable().getDifferentialOrder() == 0 and \
                        _odeShape.getScope().resolveToSymbol(_odeShape.getVariable().getCompleteName(),
                                                             SymbolKind.VARIABLE) is None:
            symbol = VariableSymbol(_elementReference=_odeShape, _scope=_odeShape.getScope(),
                                    _name=_odeShape.getVariable().getName(),
                                    _blockType=BlockType.EQUATION,
                                    _declaringExpression=_odeShape.getExpression(),
                                    _isPredefined=False, _isFunction=False,
                                    _isRecordable=True,
                                    _typeSymbol=PredefinedTypes.getRealType(), _variableType=VariableType.SHAPE)
            symbol.setComment(_odeShape.getComment())
            _odeShape.getScope().addSymbol(symbol)
        _odeShape.getVariable().updateScope(_odeShape.getScope())
        cls.visitVariable(_odeShape.getVariable())
        _odeShape.getExpression().updateScope(_odeShape.getScope())
        cls.visitExpression(_odeShape.getExpression())
        return

    @classmethod
    def visitOdeEquation(cls, _equation=None):
        """
        Private method: Used to visit a single ode-equation and update the corresponding scope.
        :param _equation: a single ode-equation.
        :type _equation: ASTOdeEquation
        """
        from pynestml.modelprocessor.ASTOdeEquation import ASTOdeEquation
        assert (_equation is not None and isinstance(_equation, ASTOdeEquation)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of ode-equation provided (%s)!' % type(_equation)
        _equation.getLhs().updateScope(_equation.getScope())
        cls.visitVariable(_equation.getLhs())
        _equation.get_rhs().updateScope(_equation.getScope())
        cls.visitExpression(_equation.get_rhs())
        return

    @classmethod
    def visitBlockWithVariables(cls, _block=None):
        """
        Private method: Used to visit a single block of variables and update its scope.
        :param _block: a block with declared variables.
        :type _block: ASTBlockWithVariables
        """
        from pynestml.modelprocessor.ASTBlockWithVariables import ASTBlockWithVariables
        from pynestml.modelprocessor.VariableSymbol import BlockType
        assert (_block is not None and isinstance(_block, ASTBlockWithVariables)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of block with variables provided (%s)!' % type(_block)
        cls.__currentBlockType = BlockType.STATE if _block.isState() else \
            BlockType.INTERNALS if _block.isInternals() else BlockType.PARAMETERS if _block.isParameters() else \
                BlockType.INITIAL_VALUES
        for decl in _block.getDeclarations():
            decl.updateScope(_block.getScope())
            cls.visitDeclaration(decl)
        cls.__currentBlockType = None
        return

    @classmethod
    def visitEquationsBlock(cls, _block=None):
        """
        Private method: Used to visit a single equations block and update its scope.
        :param _block: a single equations block.
        :type _block: ASTEquationsBlock
        """
        from pynestml.modelprocessor.ASTEquationsBlock import ASTEquationsBlock
        from pynestml.modelprocessor.ASTOdeFunction import ASTOdeFunction
        from pynestml.modelprocessor.ASTOdeShape import ASTOdeShape
        assert (_block is not None and isinstance(_block, ASTEquationsBlock)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of equations block provided (%s)!' % type(_block)
        for decl in _block.getDeclarations():
            decl.updateScope(_block.getScope())
            if isinstance(decl, ASTOdeFunction):
                cls.visitOdeFunction(decl)
            elif isinstance(decl, ASTOdeShape):
                cls.visitOdeShape(decl)
            else:
                cls.visitOdeEquation(decl)
        return

    @classmethod
    def visitInputBlock(cls, _block=None):
        """
        Private method: Used to visit a single input block and update its scope.
        :param _block: a single input block.
        :type _block: ASTInputBlock
        """
        from pynestml.modelprocessor.ASTInputBlock import ASTInputBlock
        assert (_block is not None and isinstance(_block, ASTInputBlock)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of input-block provided (%s)!' % type(_block)
        for line in _block.getInputLines():
            line.updateScope(_block.getScope())
            cls.visitInputLine(line)
        return

    @classmethod
    def visitOutputBlock(cls, _block=None):
        """
        Private method: Used to visit a single output block and visit its scope.
        :param _block: a single output block.
        :type _block: ASTOutputBlock
        """
        from pynestml.modelprocessor.ASTOutputBlock import ASTOutputBlock
        assert (_block is not None and isinstance(_block, ASTOutputBlock)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of output-block provided (%s)!' % type(_block)
        return

    @classmethod
    def visitInputLine(cls, _line=None):
        """
        Private method: Used to visit a single input line, create the corresponding symbol and update the scope.
        :param _line: a single input line.
        :type _line: ASTInputLine
        """
        from pynestml.modelprocessor.ASTInputLine import ASTInputLine
        from pynestml.modelprocessor.VariableSymbol import BlockType, VariableType
        assert (_line is not None and isinstance(_line, ASTInputLine)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of input-line provided (%s)!' % type(_line)
        from pynestml.modelprocessor.VariableSymbol import VariableSymbol
        bufferType = BlockType.INPUT_BUFFER_SPIKE if _line.isSpike() else BlockType.INPUT_BUFFER_CURRENT
        if _line.isSpike() and _line.hasDatatype():
            _line.getDatatype().updateScope(_line.getScope())
            cls.visitDataType(_line.getDatatype())
            typeSymbol = _line.getDatatype().getTypeSymbol()
        elif _line.isSpike():
            code, message = Messages.getBufferTypeNotDefined(_line.getName())
            Logger.log_message(code=code, message=message, error_position=_line.getSourcePosition(),
                               log_level=LOGGING_LEVEL.WARNING)
            typeSymbol = PredefinedTypes.getTypeIfExists('nS')
        else:
            typeSymbol = PredefinedTypes.getTypeIfExists('pA')
        typeSymbol.setBuffer(True)  # set it as a buffer
        symbol = VariableSymbol(_elementReference=_line, _scope=_line.getScope(), _name=_line.getName(),
                                _blockType=bufferType, _vectorParameter=_line.getIndexParameter(),
                                _isPredefined=False, _isFunction=False, _isRecordable=False,
                                _typeSymbol=typeSymbol, _variableType=VariableType.BUFFER)
        symbol.setComment(_line.getComment())
        _line.getScope().addSymbol(symbol)
        for inputType in _line.getInputTypes():
            cls.visitInputType(inputType)
            inputType.updateScope(_line.getScope())
        return

    @classmethod
    def visitInputType(cls, _type=None):
        """
        Private method: Used to visit a single input type and update its scope.
        :param _type: a single input-type.
        :type _type: ASTInputType
        """
        from pynestml.modelprocessor.ASTInputType import ASTInputType
        assert (_type is not None and isinstance(_type, ASTInputType)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of input-type provided (%s)!' % type(_type)
        return

    @classmethod
    def visitArithmeticOperator(cls, _arithmeticOp=None):
        """
        Private method: Used to visit a single arithmetic operator and update its scope.
        :param _arithmeticOp: a single arithmetic operator.
        :type _arithmeticOp: ASTArithmeticOperator
        """
        from pynestml.modelprocessor.ASTArithmeticOperator import ASTArithmeticOperator
        assert (_arithmeticOp is not None and isinstance(_arithmeticOp, ASTArithmeticOperator)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of arithmetic operator provided (%s)!' % type(
                _arithmeticOp)
        return

    @classmethod
    def makeImplicitOdesExplicit(cls, _equationsBlock=None):
        """
        This method inspects a handed over block of equations and makes all implicit declarations of odes explicit.
        E.g. the declaration g_in'' implies that there have to be, either implicit or explicit, g_in' and g_in
        stated somewhere. This method collects all non explicitly defined elements and adds them to the model.
        :param _equationsBlock: a single equations block
        :type _equationsBlock: ASTEquationsBlock
        """
        from pynestml.modelprocessor.ASTEquationsBlock import ASTEquationsBlock
        from pynestml.modelprocessor.ASTOdeShape import ASTOdeShape
        from pynestml.modelprocessor.ASTOdeEquation import ASTOdeEquation
        from pynestml.modelprocessor.ASTVariable import ASTVariable
        from pynestml.modelprocessor.ASTSourcePosition import ASTSourcePosition
        from pynestml.modelprocessor.ASTSimpleExpression import ASTSimpleExpression
        assert (_equationsBlock is not None and isinstance(_equationsBlock, ASTEquationsBlock)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of equations block provided (%s)!' % type(_equationsBlock)
        checked = list()  # used to avoid redundant checking
        for declaration in _equationsBlock.getDeclarations():
            if declaration in checked:
                continue
            if isinstance(declaration, ASTOdeShape) and declaration.getVariable().getDifferentialOrder() > 0:
                # now we found a variable with order > 0, thus check if all previous orders have been defined
                order = declaration.getVariable().getDifferentialOrder()
                # check for each smaller order if it is defined
                for i in range(1, order):
                    found = False
                    for shape in _equationsBlock.get_shapes():
                        if shape.getVariable().getName() == declaration.getVariable().getName() and \
                                        shape.getVariable().getDifferentialOrder() == i:
                            found = True
                            break
                    # now if we did not found the corresponding declaration, we have to add it by hand
                    if not found:
                        lhsVariable = ASTVariable.makeASTVariable(_name=declaration.getVariable().getName(),
                                                                  _differentialOrder=i,
                                                                  _sourcePosition=ASTSourcePosition.
                                                                  getAddedSourcePosition())
                        rhsVariable = ASTVariable.makeASTVariable(_name=declaration.getVariable().getName(),
                                                                  _differentialOrder=i,
                                                                  _sourcePosition=ASTSourcePosition.
                                                                  getAddedSourcePosition())
                        expression = ASTSimpleExpression.makeASTSimpleExpression(_variable=rhsVariable,
                                                                                 _sourcePosition=ASTSourcePosition.
                                                                                 getAddedSourcePosition())
                        _equationsBlock.getDeclarations().append(
                            ASTOdeShape.makeASTOdeShape(_lhs=lhsVariable,
                                                        _rhs=expression,
                                                        _sourcePosition=ASTSourcePosition.getAddedSourcePosition()))
            if isinstance(declaration, ASTOdeEquation):
                # now we found a variable with order > 0, thus check if all previous orders have been defined
                order = declaration.getLhs().getDifferentialOrder()
                # check for each smaller order if it is defined
                for i in range(1, order):
                    found = False
                    for ode in _equationsBlock.get_equations():
                        if ode.getLhs().getName() == declaration.getLhs().getName() and \
                                        ode.getLhs().getDifferentialOrder() == i:
                            found = True
                            break
                    # now if we did not found the corresponding declaration, we have to add it by hand
                    if not found:
                        lhsVariable = ASTVariable.makeASTVariable(_name=declaration.getLhs().getName(),
                                                                  _differentialOrder=i,
                                                                  _sourcePosition=ASTSourcePosition.
                                                                  getAddedSourcePosition())
                        rhsVariable = ASTVariable.makeASTVariable(_name=declaration.getLhs().getName(),
                                                                  _differentialOrder=i,
                                                                  _sourcePosition=ASTSourcePosition.
                                                                  getAddedSourcePosition())
                        expression = ASTSimpleExpression.makeASTSimpleExpression(_variable=rhsVariable,
                                                                                 _sourcePosition=ASTSourcePosition.
                                                                                 getAddedSourcePosition())
                        _equationsBlock.getDeclarations().append(
                            ASTOdeEquation.makeASTOdeEquation(_lhs=lhsVariable,
                                                              _rhs=expression,
                                                              _sourcePosition=ASTSourcePosition.getAddedSourcePosition()))
            checked.append(declaration)

    @classmethod
    def markConductanceBasedBuffers(cls, _odeDeclarations=None, _inputLines=None):
        """
        Inspects all handed over buffer definitions and updates them to conductance based if they occur as part of
        a cond_sum expression.
        :param _odeDeclarations: a set of ode declarations.
        :type _odeDeclarations: ASTOdeEquation,ASTOdeFunction
        :param _inputLines: a set of input buffers.
        :type _inputLines: ASTInputLine
        """
        from pynestml.modelprocessor.PredefinedTypes import PredefinedTypes
        from pynestml.modelprocessor.Symbol import SymbolKind
        # this is the updated version, where nS buffers are marked as conductance based
        for bufferDeclaration in _inputLines:
            if bufferDeclaration.isSpike():
                symbol = bufferDeclaration.getScope().resolveToSymbol(bufferDeclaration.getName(), SymbolKind.VARIABLE)
                if symbol is not None and symbol.getTypeSymbol().equals(PredefinedTypes.getTypeIfExists('nS')):
                    symbol.setConductanceBased(True)
        return

    @classmethod
    def assignOdeToVariables(cls, _odeBlock=None):
        """
        Adds for each variable symbol the corresponding ode declaration if present.
        :param _odeBlock: a single block of ode declarations.
        :type _odeBlock: ASTEquations
        """
        from pynestml.modelprocessor.ASTEquationsBlock import ASTEquationsBlock
        from pynestml.modelprocessor.ASTOdeEquation import ASTOdeEquation
        from pynestml.modelprocessor.ASTOdeShape import ASTOdeShape
        assert (_odeBlock is not None and isinstance(_odeBlock, ASTEquationsBlock)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of equations block provided (%s)!' % type(_odeBlock)
        for decl in _odeBlock.getDeclarations():
            if isinstance(decl, ASTOdeEquation):
                cls.addOdeToVariable(decl)
            if isinstance(decl, ASTOdeShape):
                cls.addOdeShapeToVariable(decl)
        return

    @classmethod
    def addOdeToVariable(cls, _odeEquation=None):
        """
        Resolves to the corresponding symbol and updates the corresponding ode-declaration. In the case that
        :param _odeEquation: a single ode-equation
        :type _odeEquation: ASTOdeEquation
        """
        from pynestml.modelprocessor.ASTOdeEquation import ASTOdeEquation
        from pynestml.modelprocessor.Symbol import SymbolKind
        assert (_odeEquation is not None and isinstance(_odeEquation, ASTOdeEquation)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of equation provided (%s)!' % type(_odeEquation)
        # the definition of a differential equations is defined by stating the derivation, thus derive the actual order
        diffOrder = _odeEquation.getLhs().getDifferentialOrder() - 1
        # we check if the corresponding symbol already exists, e.g. V_m' has already been declared
        existingSymbol = _odeEquation.getScope().resolveToSymbol(_odeEquation.getLhs().getName() + '\'' * diffOrder,
                                                           SymbolKind.VARIABLE)
        if existingSymbol is not None:
            existingSymbol.setOdeDefinition(_odeEquation.get_rhs())
            code, message = Messages.getOdeUpdated(_odeEquation.getLhs().getNameOfLhs())
            Logger.log_message(neuron=None, error_position=existingSymbol.getReferencedObject().getSourcePosition(),
                               code=code, message=message, log_level=LOGGING_LEVEL.INFO)
        else:
            code, message = Messages.getNoVariableFound(_odeEquation.getLhs().getNameOfLhs())
            Logger.log_message(neuron=None, code=code, message=message, error_position=_odeEquation.getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        return

    @classmethod
    def addOdeShapeToVariable(cls, _odeShape=None):
        """
        Adds the shape as the defining equation.
        :param _odeShape: a single shape object.
        :type _odeShape: ASTOdeShape
        """
        from pynestml.modelprocessor.ASTOdeShape import ASTOdeShape
        from pynestml.modelprocessor.Symbol import SymbolKind
        from pynestml.modelprocessor.VariableSymbol import VariableType
        assert (_odeShape is not None and isinstance(_odeShape, ASTOdeShape)), \
            '(PyNestML.SymbolTable.Visitor) No or wrong type of shape provided (%s)!' % type(_odeShape)
        if _odeShape.getVariable().getDifferentialOrder() == 0:
            # we only update those which define an ode
            return
        # we check if the corresponding symbol already exists, e.g. V_m' has already been declared
        existingSymbol = _odeShape.getScope().resolveToSymbol(_odeShape.getVariable().getNameOfLhs(),
                                                           SymbolKind.VARIABLE)
        if existingSymbol is not None:
            existingSymbol.setOdeDefinition(_odeShape.getExpression())
            existingSymbol.setVariableType(VariableType.SHAPE)
            code, message = Messages.getOdeUpdated(_odeShape.getVariable().getNameOfLhs())
            Logger.log_message(error_position=existingSymbol.getReferencedObject().getSourcePosition(),
                               code=code, message=message, log_level=LOGGING_LEVEL.INFO)
        else:
            code, message = Messages.getNoVariableFound(_odeShape.getVariable().getNameOfLhs())
            Logger.log_message(code=code, message=message, error_position=_odeShape.getSourcePosition(),
                               log_level=LOGGING_LEVEL.ERROR)
        return
