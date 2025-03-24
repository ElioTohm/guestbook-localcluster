"""
A sample backend server. Saves and retrieves entries using MongoDB with OpenTelemetry tracing and metrics.
"""
import os
import time
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import bleach
import sys

# OpenTelemetry imports for tracing
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# OpenTelemetry imports for metrics
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Set up OpenTelemetry tracing
resource = Resource(attributes={
    "service.name": os.environ.get("SERVICE_NAME"),
})
trace.set_tracer_provider(TracerProvider(resource=resource))

# Configure OTLP exporter for tracing (e.g., to Grafana Tempo or Jaeger)
otlp_trace_exporter = OTLPSpanExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True  # Set to False if using TLS
)

# Add span processor to export traces
span_processor = BatchSpanProcessor(otlp_trace_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Set up OpenTelemetry metrics
metric_exporter = OTLPMetricExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True
)
metric_reader = PeriodicExportingMetricReader(exporter=metric_exporter)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
meter = meter_provider.get_meter(__name__)

# Define a counter metric for request counts
requests_count = meter.create_counter(
    "http.server.requests",
    unit="1",
    description="Number of HTTP requests received by the server",
)

# Initialize Flask app
app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://{}/guestbook'.format(os.environ.get('GUESTBOOK_DB_ADDR'))
mongo = PyMongo(app)

# Instrument Flask and PyMongo
FlaskInstrumentor().instrument_app(app)
PymongoInstrumentor().instrument()
RequestsInstrumentor().instrument()  # Optional, remove if not using requests library

# Get a tracer for manual spans if needed
tracer = trace.get_tracer(__name__)

@app.route('/messages', methods=['GET'])
def get_messages():
    """Retrieve and return the list of messages on GET request"""
    field_mask = {'author': 1, 'message': 1, 'date': 1, '_id': 0}
    msg_list = list(mongo.db.messages.find({}, field_mask).sort("_id", -1))
    print("blasd asdhvbajhssvhjvfasd ", file=sys.stderr)  # Kept as-is; could be replaced with logging
    # Increment request counter
    requests_count.add(1, {"http.method": request.method, "http.path": request.path})
    return jsonify(msg_list), 201

@app.route('/messages', methods=['POST'])
def add_message():
    """Save a new message on POST request"""
    raw_data = request.get_json()
    msg_data = {
        'author': bleach.clean(raw_data['author']),
        'message': bleach.clean(raw_data['message']),
        'date': time.time()
    }
    mongo.db.messages.insert_one(msg_data)
    # Increment request counter
    requests_count.add(1, {"http.method": request.method, "http.path": request.path})
    return jsonify({}), 201

if __name__ == '__main__':
    for v in ['PORT', 'GUESTBOOK_DB_ADDR']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)

    # Start Flask server
    # Flask's debug mode is unrelated to ptvsd debugger used by Cloud Code
    app.run(debug=True, port=os.environ.get('PORT'), host='0.0.0.0')
