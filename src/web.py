import time
import sys
import os
import json
import logging
from datetime import datetime

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.resolver import resolve
from src.db import db, QueryLog

# Load environment variables
load_dotenv()

# Setup structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "logger": record.name
        }
        if hasattr(record, 'extra_data'):
            log_obj.update(record.extra_data)
        return json.dumps(log_obj)

logger = logging.getLogger("dns_resolver")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Database Configuration
# Fallback to local SQLite if DATABASE_URL is not provided (Model 1)
database_url = os.getenv("DATABASE_URL", "sqlite:///dns_resolver.db")
# Fix for Heroku/Render postgres:// -> postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize DB tables (for standalone model)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "UP"}), 200

@app.route('/api/ready')
def ready():
    # Simple check if DB is accessible
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "READY"}), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({"status": "NOT_READY"}), 503

@app.route('/api/resolve')
def api_resolve():
    domain = request.args.get('domain')
    if not domain:
        return jsonify({'error': 'domain is required'}), 400

    trace = []
    start = time.time()
    ip = None
    try:
        ip = resolve(domain, trace=trace)
    except Exception as e:
        logger.error("Resolution failed", extra={'extra_data': {'domain': domain, 'error': str(e)}})
    
    elapsed = time.time() - start
    elapsed_ms = elapsed * 1000

    # Log to DB
    try:
        log_entry = QueryLog(domain=domain, resolved_ip=ip, elapsed_ms=elapsed_ms)
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        logger.error("DB log failed", extra={'extra_data': {'error': str(e)}})
        db.session.rollback()

    logger.info("DNS Query Resolved", extra={'extra_data': {
        'domain': domain,
        'ip': ip,
        'elapsed_ms': round(elapsed_ms, 2)
    }})

    return jsonify({
        'domain': domain,
        'ip': ip,
        'trace': trace,
        'elapsed': f"{elapsed:.3f}s"
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv("FLASK_ENV") == "development")
