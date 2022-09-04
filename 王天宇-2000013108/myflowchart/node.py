import time
import uuid
import itertools

class Node(object):
    """
    Node类型是所有类型的基类，包含一个节点最基础的操作
    """
    node_type = 'node' # 对应于flowchart.js nodeType = node
    node_id = itertools.count(0)

    def __init__(self) -> None:
        self.node_name = '' # 节点名，对应flowchart.js的nodename
        self.node_text = '' # 节点内容，对应flowchart.js的nodetext
        self.connections = [] # 节点链接对象
        self.params = {} # 节点若为函数，则有参数，对应于flowchart.js的param
        self.direction = None # 节点的链接方向
        self.__visited = None # 遍历时是否已经被访问
        self.id = next(self.node_id) # 节点id，递增数

    def node_definition(self):
        """
        此函数返回flowchart.js对应的第一部分，即节点定义
        node_name(param1=value1, param2=value2)=>node_type: node_text
        """
        params = ""
        if self.params:
            params = f"({','.join(list(self.params))})"
        return f'{self.node_name}{params}=>{self.node_type}: {self.node_text}\n'
    
    def node_connection(self):
        """
        此函数返回flowchart.js对应的第二部分，即节点链接关系
        node_name->node_name_1
        node_name->node_name_2
        ...
        """
        connections = ""
        for connection in self.connections: 
            if isinstance(connection, Node): # 确保connection连接的是Node？
                if self.direction:
                    direction = f'({self.direction})'
                else:
                    direction = ""
                connections += f'{self.node_name}{direction}->{connection.node_name}\n'
        return connections

    def travel(self, func, visited_flag):
        """
        当此节点为头节点时，遍历节点组
        """    
        if self.__visited == visited_flag:
            return
        self.__visited = visited_flag

        if not func(self):
            return
        
        for subnode in self.connections:
            if isinstance(subnode, Node):
                subnode.travel(func, visited_flag)
    
    def connect(self, sub_node, direction=''):
        """
        链接两个节点
        """        
        if direction:
            self.direction = direction
        self.connections.append(sub_node)


class NodesGroup(Node):    
    """
    将一组节点看作一个整体可以方便地进行一些操作
    一个节点组有一个头节点，可能有多个尾节点
    """
    def __init__(self, head_node=None, tail_nodes=[]) -> None:
        Node.__init__(self)
        # print(type(head_node))
        if tail_nodes == None:
            tail_nodes = []
        self.head, self.tails = head_node, tail_nodes
        self.node_definitions = '' # 此节点组所有节点的定义
        self.node_connections = '' # 此节点组的内部链接情况
        if self.head:
            self.node_name = self.head.node_name

    def node_definition(self):
        self.refresh() # 更新定义，否则刚链接上的节点会因为定义没更新而被忽略掉
        return self.node_definitions
    
    def node_connection(self):
        self.refresh() # 同上，及时更新链接情况
        return self.node_connections

    def travel(self, func, visited_flag):
        """
        此函数遍历节点图，边界是func函数
        func有时候是while true的add_node，遍历所有节点并把所有节点的定义加进来
        """

        self.head.travel(func, visited_flag)
    
    def connect(self, sub_node, direction=''):
        """
        定义节点组到下一个节点的链接
        就是将所有的tail都链接到上面
        """
        for tail in self.tails:
            if isinstance(tail, Node):
                if direction:
                    tail.direction = direction
                tail.connect(sub_node)

    def add_node(self, node: Node):
        """
        在遍历节点组时候调用，一边遍历一边把所有的定义加成串
        """
        self.node_definitions += node.node_definition()
        self.node_connections += node.node_connection()
        return True
    
    def refresh(self):
        """
        遍历所有节点，利用add_node更新节点组的信息
        """
        self.node_definitions = ''
        self.node_connections = ''

        visited_flag = f'{id(self)}--{time.time()}--{uuid.uuid4()}'
        self.travel(self.add_node, visited_flag)


"""
下面的节点类型对应flowchart.js中的所有类型
节点按照类型+时间戳来命名
"""
class StartNode(Node):

    node_type = 'start'

    def __init__(self, name) -> None:
        super().__init__()
        self.node_name = f'st{self.id}'
        self.node_text = f'start {name}'

class EndNode(Node):

    node_type = 'end'

    def __init__(self, name) -> None:
        super().__init__()
        self.node_name = f'e{self.id}'
        self.node_text = f'end {name}'

class OperationNode(Node):

    node_type = 'operation'

    def __init__(self, operation) -> None:
        super().__init__()
        self.node_name = f'op{self.id}'
        self.node_text = f'{operation}'

class InputOutputNode(Node):

    node_type = 'inputoutput'

    i = 'input'
    o = 'output'

    def __init__(self, io, content) -> None:
        super().__init__()
        self.node_name = f'io{self.id}'
        self.node_text = f'{io}: {content}'

class SubroutineNode(Node):

    node_type = 'subroutine'

    def __init__(self, subroutine) -> None:
        super().__init__()
        self.node_name = f'sub{self.id}'
        self.node_text = f'{subroutine}'

class ConditionNode(Node):

    node_type = 'condition'

    def __init__(self, condition) -> None:
        super().__init__()
        self.node_name = f'cond{self.id}'
        self.node_text = f'{condition}'

        self.conn_yes = None
        self.conn_no = None

    def connect_yes(self, yes_node, direction = None, istry = False):
        self.conn_yes = CondYN(self, 'yes' if not istry else 'yes@begin try', yes_node)
        self.conn_yes.direction = direction
        self.connections.append(self.conn_yes)

    def connect_no(self, no_node, direction = None, istry = False):
        self.conn_no = CondYN(self, 'no' if not istry else 'no@ ', no_node)
        self.conn_no.direction = direction
        self.connections.append(self.conn_no)

'''
这个类型比较特殊，因为condition节点会产生两个分支
用这个来存储分支信息、分支连接方向
'''
class CondYN(Node):
    def __init__(self, cond, yn = '', sub = None) -> None:
        super().__init__()
        self.cond = cond
        self.yn = yn
        self.sub = sub

        if isinstance(sub, Node):
            self.connections = [self.sub]
    
    def node_definition(self):
        return ''
    
    def node_connection(self):
        if self.sub:
            direction = ''
            if self.direction:
                direction = f'{self.direction}'
            return f'{self.cond.node_name}({self.yn}, {direction})->{self.sub.node_name}\n'
        return ''
    
    def connect(self, sub_node, direction=''):
        if direction:
            self.direction = direction
        self.connections.append(sub_node)
        self.sub = sub_node