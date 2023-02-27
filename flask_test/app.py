# Author by : ME!
# Date : 2023-02-27

from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/test')
def hello_test():
    return 'Test'

if __name__ == '__main__':
    # app.run()
    app.run(debug=True) # debug mode on


