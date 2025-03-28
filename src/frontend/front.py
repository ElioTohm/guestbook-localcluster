"""
A sample frontend server. Hosts a web page to display messages with OpenTelemetry tracing and metrics.
"""
import json
import os
import datetime
import time
from flask import Flask, render_template, redirect, url_for, request, jsonify
import requests
import dateutil.relativedelta
import sys

# OpenTelemetry imports for tracing
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
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
    "service.name": os.environ.get("SERVICE_NAME")
})
trace.set_tracer_provider(TracerProvider(resource=resource))

otlp_trace_exporter = OTLPSpanExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True 
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
    description="Number of HTTP requests received by the server"
)

app = Flask(__name__)
app.config["BACKEND_URI"] = 'http://{}/messages'.format(os.environ.get('GUESTBOOK_API_ADDR'))

# Instrument Flask and Requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Get a tracer for manual spans if needed
tracer = trace.get_tracer(__name__)

@app.route('/')
def main():
    """Retrieve a list of messages from the backend, and use them to render the HTML template"""
    response = requests.get(app.config["BACKEND_URI"], timeout=3)
    json_response = json.loads(response.text)
    # Increment request counter
    requests_count.add(1, {"http.method": request.method, "http.path": request.path})
    return render_template('home.html', messages=json_response)

@app.route('/post', methods=['POST'])
def post():
    """Send the new message to the backend and redirect to the homepage"""
    new_message = {'author': request.form['name'],
                   'message': request.form['message']}
    print("blasd sasdasdasdasdasdasdasdasdasdasdasdasdasd", file=sys.stderr)
    requests.post(url=app.config["BACKEND_URI"],
                  data=jsonify(new_message).data,
                  headers={'content-type': 'application/json'},
                  timeout=3)
    print("llllllllllllLLLLLLlllllllllll", file=sys.stderr)
    # Increment request counter
    requests_count.add(1, {"http.method": request.method, "http.path": request.path})
    return redirect(url_for('main'))

def format_duration(timestamp):
    """Format the time since the input timestamp in a human readable way"""
    now = datetime.datetime.fromtimestamp(time.time())
    prev = datetime.datetime.fromtimestamp(timestamp)
    rd = dateutil.relativedelta.relativedelta(now, prev)

    for n, unit in [(rd.years, "year"), (rd.days, "day"), (rd.hours, "hour"),
                    (rd.minutes, "minute")]:
        if n == 1:
            return "{} {} ago".format(n, unit)
        elif n > 1:
            return "{} {}s ago".format(n, unit)
    return "just now"

if __name__ == '__main__':
    for v in ['PORT', 'GUESTBOOK_API_ADDR']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)

    # Register format_duration for use in HTML template
    app.jinja_env.globals.update(format_duration=format_duration)

    # Start Flask server
    # Flask's debug mode is unrelated to ptvsd debugger used by Cloud Code
    app.run(debug=True, port=os.environ.get('PORT'), host='0.0.0.0')
