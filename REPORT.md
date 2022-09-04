## flowchart.js

flowchar.js是一个javascript库，可以签到很多应用中直接使用，所以在很多类型的平台都是直接支持的，比如CSDN的markdown语法也是支持flowchart.js的，这篇文章的flowchart.js示例也都是使用mermaid方式直接指定并进行显示的。这样，用户就可以直接已DSL的方式非常容易地进行流程图的绘制了。

## 概述

项目原理：利用flowchart.js这一js库。
将py代码转换为合法的fc语句，然后调用这个库。
转换的过程利用py内置的ADT树。

后端：接受前端传来的py代码，提交fc语句
前端：输入py，输出流程图

可做：流程图的自定义，比如颜色等等，最好能实现不用写代码的鼠标点点就能做好的。

