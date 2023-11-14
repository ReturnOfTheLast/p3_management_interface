from flask import Flask, render_template

app = Flask(__name__)


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/mongo')
def mongo():
    return render_template('mongo.html')


@app.get('/redis')
def redis():
    return render_template('redis.html')


if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
