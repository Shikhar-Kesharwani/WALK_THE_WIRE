import time
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from flask import Flask, request, jsonify, send_from_directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.resolver import resolve

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/resolve')
def api_resolve():
    domain = request.args.get('domain')
    if not domain:
        return jsonify({'error': 'domain is required'}), 400

    trace = []
    start = time.time()
    ip = resolve(domain, trace=trace)
    elapsed = time.time() - start

    return jsonify({
        'domain': domain,
        'ip': ip,
        'trace': trace,
        'elapsed': f"{elapsed:.3f}s"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
