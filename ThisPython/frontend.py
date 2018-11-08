from flask import Flask, render_template, request, url_for

app = Flask(__name__)

def flaskThread():
    # app.run(debug=True)
    app.run(host='0.0.0.0') # listen for all host names

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search_result():
    if 'q' in request.values:
        search = str(request.values.get('q', 0))
        return search
    else:
        return render_template('index.html')