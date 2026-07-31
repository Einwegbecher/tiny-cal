from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Hello World Button</title>
</head>
<body>
    <h1>Press the button</h1>
    <form action="/hello" method="POST">
        <button type="submit">Click me!</button>
    </form>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/hello', methods=['POST'])
def hello():
    print("Hello World")
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
