import _ast
import astunparse
from typing import List, Tuple
from myflowchart.node import *

class AstNode(Node):
    """
    ast树节点基类
    """
    def __init__(self, ast_object: _ast.AST):
        Node.__init__(self)
        self.ast_object = ast_object

    def ast_to_source(self) -> str:
        """
        把ast model解为代码
        """
        return astunparse.unparse(self.ast_object).strip()

class AstConditionNode(AstNode, ConditionNode):

    def __init__(self, ast_cond: _ast.stmt, **kwargs):

        AstNode.__init__(self, ast_cond, **kwargs)
        ConditionNode.__init__(self, condition=self.cond_expr())

    def cond_expr(self) -> str:

        source = astunparse.unparse(self.ast_object)
        loop_statement = source.strip()
        lines = loop_statement.splitlines()
        if len(lines) >= 1:
            return lines[0].rstrip(':')
        else:
            return 'True'

    def node_connection(self) -> str:
        return ""

class LoopCondition(AstConditionNode):

    def connect(self, sub_node, direction='') -> None:
        if direction:
            self.direction = direction
        self.connect_no(sub_node)

    def is_one_line_body(self) -> bool:
        one_line_body = False
        try:
            loop_body = self.conn_yes
            one_line_body = isinstance(loop_body, CondYN) and \
                            isinstance(loop_body.sub, Node) and \
                            not isinstance(loop_body.sub, NodesGroup) and \
                            not isinstance(loop_body.sub, ConditionNode) and \
                            len(loop_body.sub.connections) == 1 and \
                            loop_body.sub.connections[0] == self
        except Exception as e:
            print(e)
        return one_line_body


class Loop(NodesGroup, AstNode):

    def __init__(self, ast_loop: _ast.stmt, **kwargs):
        """
            Loop -> LoopCondition -> (yes) -> LoopCondition
                                  -> (no)  -> <next_node>
        """
        AstNode.__init__(self, ast_loop, **kwargs)

        self.cond_node = LoopCondition(ast_loop)

        NodesGroup.__init__(self, self.cond_node)

        self.parse_loop_body(**kwargs)

        self._virtual_no_tail()

        if kwargs.get("simplify", True):
            self.simplify()

    def parse_loop_body(self, **kwargs) -> None:

        progress = parse(self.ast_object.body, **kwargs)

        if progress.head is not None:
            process = parse(self.ast_object.body, **kwargs)
            self.cond_node.connect_yes(process.head)
            for tail in process.tails:
                if isinstance(tail, Node):
                    tail.direction = "left"
                    tail.connect(self.cond_node)
        else:
            noop = SubroutineNode("no-op")
            noop.direction = "left"
            noop.connect(self.cond_node)
            self.cond_node.conn_yes(noop)

    def _virtual_no_tail(self) -> None:
        virtual_no = CondYN(self, 'no')

        self.cond_node.conn_no = virtual_no
        self.cond_node.connections.append(virtual_no)

        self.tails.append(virtual_no)

    def simplify(self) -> None:
        try:
            if self.cond_node.is_one_line_body():
                cond = self.cond_node
                body = self.cond_node.conn_yes.sub

                simplified = OperationNode(f'{body.node_text} while {cond.node_text.lstrip("for").lstrip("while")}')

                simplified.node_name = self.head.node_name
                self.head = simplified
                self.tails = [simplified]

        except AttributeError as e:
            print(e)

class IfCondition(AstConditionNode):

    def is_one_line_body(self) -> bool:
        one_line_body = False
        try:
            yes = self.conn_yes
            one_line_body = isinstance(yes, CondYN) and \
                            isinstance(yes.sub, Node) and \
                            not isinstance(yes.sub, NodesGroup) and \
                            not isinstance(yes.sub, ConditionNode) and \
                            not yes.sub.connections
        except Exception as e:
            print(e)
        return one_line_body

    def is_no_else(self) -> bool:
        no_else = False
        try:
            no = self.conn_no
            no_else = isinstance(no, CondYN) and \
                      not no.sub
        except Exception as e:
            print(e)
        return no_else


class If(NodesGroup, AstNode):

    def __init__(self, ast_if: _ast.If, **kwargs):
 
        AstNode.__init__(self, ast_if, **kwargs)

        self.cond_node = IfCondition(ast_if)

        NodesGroup.__init__(self, self.cond_node)

        self.parse_if_body(**kwargs)
        self.parse_else_body(**kwargs)

        if kwargs.get("simplify", True):
            self.simplify()
        if kwargs.get("conds_align", False) and self.cond_node.is_no_else():
            self.cond_node.conn_yes.direction = "right"

    def parse_if_body(self, **kwargs) -> None:

        progress = parse(self.ast_object.body, **kwargs)

        if progress.head is not None:
            self.cond_node.connect_yes(progress.head)
            self.tails.extend(progress.tails)
        else:
            virtual_yes = CondYN(self, CondYN.YES)
            self.cond_node.conn_yes = virtual_yes
            self.cond_node.connections.append(virtual_yes)

            self.tails.append(virtual_yes)

    def parse_else_body(self, **kwargs) -> None:
        progress = parse(self.ast_object.orelse, **kwargs)

        if progress.head is not None:
            self.cond_node.connect_no(progress.head)
            self.tails.extend(progress.tails)
        else:  # connect virtual conn_no
            virtual_no = CondYN(self, 'no')
            self.cond_node.conn_no = virtual_no
            self.cond_node.connections.append(virtual_no)

            self.tails.append(virtual_no)

    def simplify(self) -> None:
        try:
            if self.cond_node.is_no_else() and self.cond_node.is_one_line_body():  # simplify
                cond = self.cond_node
                body = self.cond_node.conn_yes.sub

                simplified = OperationNode(f'{body.node_text} if {cond.node_text.lstrip("if")}')

                simplified.node_name = self.head.node_name
                self.head = simplified
                self.tails = [simplified]

        except AttributeError as e:
            print(e)

    def align(self):
        self.cond_node.no_align_next()

class Try(NodesGroup, AstNode):

    def __init__(self, ast_try: _ast.Try, **kwargs):
        AstNode.__init__(self, ast_try, **kwargs)

        self.cond_node = IfCondition(ast_try)

        NodesGroup.__init__(self, self.cond_node)

        self.parse_try_body(**kwargs)
        self.parse_except_body(**kwargs)

        if kwargs.get("conds_align", False) and self.cond_node.is_no_else():
            self.cond_node.conn_yes.direction = "right"

    def parse_try_body(self, **kwargs) -> None:
        progress = parse(self.ast_object.body, **kwargs)

        if progress.head is not None:
            self.cond_node.connect_yes(progress.head, istry=True)
            # for t in progress.tails:
            #     if isinstance(t, Node):
            #         t.set_connect_direction("right")
            self.tails.extend(progress.tails)
        else:  # connect virtual conn_yes
            virtual_yes = CondYN(self, 'yes@ ')
            self.cond_node.conn_yes = virtual_yes
            self.cond_node.connections.append(virtual_yes)

            self.tails.append(virtual_yes)

    def parse_except_body(self, **kwargs) -> None:
        print(self.ast_object.body)
        progress = parse(self.ast_object.handlers, **kwargs)

        if progress.head is not None:
            self.cond_node.connect_no(progress.head, istry=True)
            self.tails.extend(progress.tails)
        else:  # connect virtual conn_no
            virtual_no = CondYN(self, 'no')
            self.cond_node.conn_no = virtual_no
            self.cond_node.connections.append(virtual_no)

            self.tails.append(virtual_no)

    def simplify(self) -> None:
        try:
            if self.cond_node.is_no_else() and self.cond_node.is_one_line_body():  # simplify
                cond = self.cond_node
                body = self.cond_node.conn_yes.sub

                simplified = OperationNode(f'{body.node_text} if {cond.node_text.lstrip("if")}')

                simplified.node_name = self.head.node_name
                self.head = simplified
                self.tails = [simplified]

        except AttributeError as e:
            print(e)

    def align(self):

        self.cond_node.no_align_next()

class FunctionDefStart(AstNode, StartNode):

    def __init__(self, ast_function_def: _ast.FunctionDef, **kwargs):
        AstNode.__init__(self, ast_function_def, **kwargs)
        StartNode.__init__(self, ast_function_def.name)


class FunctionDefEnd(AstNode, EndNode):

    def __init__(self, ast_function_def: _ast.FunctionDef, **kwargs):
        AstNode.__init__(self, ast_function_def, **kwargs)
        EndNode.__init__(self, ast_function_def.name)


class FunctionDefArgsInput(AstNode, InputOutputNode):

    def __init__(self, ast_function_def: _ast.FunctionDef, **kwargs):
        AstNode.__init__(self, ast_function_def, **kwargs)
        InputOutputNode.__init__(self, 'input', self.func_args_str())

    def func_args_str(self):
        args = []
        for arg in self.ast_object.args.args:
            args.append(str(arg.arg))

        return ', '.join(args)

class FunctionDef(NodesGroup, AstNode):

    def __init__(self, ast_func: _ast.FunctionDef, **kwargs):
        AstNode.__init__(self, ast_func, **kwargs)

        self.func_start = FunctionDefStart(ast_func, **kwargs)
        self.func_args_input = FunctionDefArgsInput(ast_func, **kwargs)
        self.body_head, self.body_tails = self.parse_func_body(**kwargs)
        self.func_end = FunctionDefEnd(ast_func, **kwargs)

        self.func_start.connect(self.func_args_input)
        self.func_args_input.connect(self.body_head)
        for t in self.body_tails:
            if isinstance(t, Node):
                t.connect(self.func_end)

        NodesGroup.__init__(self, self.func_start, [self.func_end])

    def parse_func_body(self, **kwargs) -> Tuple[Node, List[Node]]:
        p = parse(self.ast_object.body, **kwargs)
        return p.head, p.tails

class CommonOperation(AstNode, OperationNode):

    def __init__(self, ast_object: _ast.AST, **kwargs):
        AstNode.__init__(self, ast_object, **kwargs)
        OperationNode.__init__(self, operation=self.ast_to_source())



class BreakContinueSubroutine(AstNode, SubroutineNode):

    def __init__(self, ast_break_continue: _ast.stmt, **kwargs):
        AstNode.__init__(self, ast_break_continue, **kwargs)
        SubroutineNode.__init__(self, self.ast_to_source())

    def connect(self, sub_node, direction='') -> None:
        pass


class YieldOutput(AstNode, InputOutputNode):

    def __init__(self, ast_return: _ast.Return, **kwargs):
        AstNode.__init__(self, ast_return, **kwargs)
        InputOutputNode.__init__(self, 'output', self.ast_to_source())

class ReturnOutput(AstNode, InputOutputNode):

    def __init__(self, ast_return: _ast.Return, **kwargs):
        AstNode.__init__(self, ast_return, **kwargs)
        InputOutputNode.__init__(self, 'output', self.ast_to_source().lstrip("return"))


class ReturnEnd(AstNode, EndNode):

    def __init__(self, ast_return: _ast.Return, **kwargs):
        AstNode.__init__(self, ast_return, **kwargs)
        EndNode.__init__(self, "function return")  # TODO: the returning function name


class Return(NodesGroup, AstNode):
    def __init__(self, ast_return: _ast.Return, **kwargs):
        AstNode.__init__(self, ast_return, **kwargs)

        self.output_node = None
        self.end_node = None

        self.head = None

        self.end_node = ReturnEnd(ast_return, **kwargs)
        self.head = self.end_node
        if ast_return.value:
            self.output_node = ReturnOutput(ast_return, **kwargs)
            self.output_node.connect(self.end_node)
            self.head = self.output_node

        self.connections.append(self.head)

        NodesGroup.__init__(self, self.head, [self.end_node])

    def connect(self, sub_node, direction='') -> None:
        pass

class CallSubroutine(AstNode, SubroutineNode):

    def __init__(self, ast_call: _ast.Call, **kwargs):
        AstNode.__init__(self, ast_call, **kwargs)
        SubroutineNode.__init__(self, self.ast_to_source())

__func_stmts = {
    _ast.FunctionDef: FunctionDef
}

__cond_stmts = {
    _ast.If: If,
    _ast.Try: Try,
}

__loop_stmts = {
    _ast.For: Loop,
    _ast.While: Loop,
}

__ctrl_stmts = {
    _ast.Break: BreakContinueSubroutine,
    _ast.Continue: BreakContinueSubroutine,
    _ast.Return: Return,
    _ast.Yield: YieldOutput,
    _ast.Call: CallSubroutine,
}

# merge dict: PEP448
__special_stmts = {**__func_stmts, **__cond_stmts, **__loop_stmts, **__ctrl_stmts}


def parse(ast_list: List[_ast.AST], **kwargs) -> NodesGroup:
    head_node = None
    tail_node = None

    process = NodesGroup(head_node, tail_node)

    for ast_object in ast_list:
        ast_node_class = __special_stmts.get(type(ast_object), CommonOperation)
        print(ast_node_class)
        if type(ast_object) == _ast.Expr:
            try:
                ast_node_class = __special_stmts.get(type(ast_object.value), CommonOperation)
            except AttributeError:
                ast_node_class = CommonOperation

        assert issubclass(ast_node_class, AstNode)

        node = ast_node_class(ast_object, **kwargs)
        # print(f'{tail_node} -> {node}')
 
        if head_node is None: 
            head_node = node
            tail_node = node
        else:
            tail_node.connect(node) # 上一个节点连过来
            if isinstance(tail_node, If) and isinstance(node, If) and \
                    kwargs.get("conds_align", True):
                tail_node.align()

            tail_node = node

    process.head = head_node

    process.tails.append(tail_node)

    return process
