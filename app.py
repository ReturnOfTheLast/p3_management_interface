from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/network_data')
def network_data():
    return render_template('network_data.html')

@app.route('/ip_addresses')
def ip_addresses():
    return render_template('ip_addresses.html')

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

if __name__ == '__main__':
    app.run(debug=True)