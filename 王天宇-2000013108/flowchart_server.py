from base64 import decode
from flask import Flask, request, render_template
from myflowchart import flowchart
# from pyflowchart import Flowchart

pyfc = Flask(__name__)

@pyfc.route('/')
def root():
    return pyfc.send_static_file('home.html')

@pyfc.route('/parsepy', methods=['post'])
def parsepy():
    pycode = request.form['pycode']
    try:
        codeflowchart = flowchart.from_code(pycode)
        ret = codeflowchart.flowchart()
    except:
        return ""
    return ret

@pyfc.route('/file-upload', methods=['post'])
def fileupload():
    f = request.files.getlist('file')[0]
    print(f)
    pycode = f.stream.read()
    return pycode

# @pyfc.route('/svgedit', methods=['post'])
# def svgedit():
#     dsl = request.form['dsl']
#     return render_template('svgedit.html', dsl=dsl)

@pyfc.route('/help')
def helppage():
    return pyfc.send_static_file('help.html')

@pyfc.route('/about')
def aboutme():
    return pyfc.send_static_file('about.html')
if __name__ == '__main__':
    pyfc.run(host='0.0.0.0', port=80, debug=True)
