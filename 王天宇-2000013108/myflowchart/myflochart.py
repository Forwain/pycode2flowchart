import _ast
import ast

from myflowchart import ast_node
from myflowchart.node import NodesGroup

class flowchart(NodesGroup):

    def __init__(self, head_node) -> None:
        super().__init__(head_node)
    
    def flowchart(self):
        return self.node_definition() + '\n' + self.node_connection()
    
    def from_code(code):
        code_ast = ast.parse(code)
        assert code_ast.body, f"解析的代码为空"
        p = ast_node.parse(code_ast.body)
        return flowchart(p.head)
