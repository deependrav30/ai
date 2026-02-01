"""
Metrics HTTP Server for Prometheus

Exposes /metrics endpoint that Prometheus can scrape.
Run this in a separate thread from the Streamlit app.
"""

from prometheus_client import start_http_server, generate_latest
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

logger = logging.getLogger(__name__)

class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for /metrics endpoint"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/metrics':
            # Generate Prometheus metrics
            metrics_output = generate_latest()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(metrics_output)
        elif self.path == '/health':
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def start_metrics_server(port=8000):
    """
    Start HTTP server for Prometheus metrics on specified port.
    Runs in a daemon thread so it doesn't block the main application.
    
    Args:
        port: Port to listen on (default 8000)
    """
    try:
        server = HTTPServer(('0.0.0.0', port), MetricsHandler)
        
        # Run server in daemon thread
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        
        logger.info(f"✓ Metrics server started on http://0.0.0.0:{port}/metrics")
        return server
        
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        return None


if __name__ == "__main__":
    # Test the metrics server
    logging.basicConfig(level=logging.INFO)
    print("Starting metrics server on port 8000...")
    print("Visit http://localhost:8000/metrics to see metrics")
    print("Press Ctrl+C to stop")
    
    server = start_metrics_server(8000)
    
    if server:
        try:
            # Keep the main thread alive
            threading.Event().wait()
        except KeyboardInterrupt:
            print("\nShutting down...")
            server.shutdown()
