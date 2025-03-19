"""
A sample backend server. Saves and retrieves entries using MongoDB with OpenTelemetry tracing.
"""
import os
import time
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import bleach
import sys

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Set up OpenTelemetry tracing
resource = Resource(attributes={
    "service.name": os.environ.get("SERVICE_NAME"),
})
trace.set_tracer_provider(TracerProvider(resource=resource))

# Configure OTLP exporter (e.g., to Grafana Tempo or Jaeger)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True  # Set to False if using TLS
)

# Add span processor to export traces
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Initialize Flask app
app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://{}/guestbook'.format(os.environ.get('GUESTBOOK_DB_ADDR'))
mongo = PyMongo(app)

# Instrument Flask and PyMongo
FlaskInstrumentor().instrument_app(app)
PymongoInstrumentor().instrument()
RequestsInstrumentor().instrument()

# Get a tracer for manual spans if needed
tracer = trace.get_tracer(__name__)

@app.route('/messages', methods=['GET'])
def get_messages():
    """ retrieve and return the list of messages on GET request """
    field_mask = {'author':1, 'message':1, 'date':1, '_id':0}
    msg_list = list(mongo.db.messages.find({}, field_mask).sort("_id", -1))
    print("blasd asdhvbajhssvhjvfasd ", file=sys.stderr)
    return jsonify(msg_list), 201

@app.route('/messages', methods=['POST'])
def add_message():
    """ save a new message on POST request """
    raw_data = request.get_json()
    msg_data = {'author':bleach.clean(raw_data['author']),
                'message':bleach.clean(raw_data['message']),
                'date':time.time()}
    mongo.db.messages.insert_one(msg_data)
    return  jsonify({}), 201

if __name__ == '__main__':
    for v in ['PORT', 'GUESTBOOK_DB_ADDR']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)

    # start Flask server
    # Flask's debug mode is unrelated to ptvsd debugger used by Cloud Code
    app.run(debug=True, port=os.environ.get('PORT'), host='0.0.0.0')
