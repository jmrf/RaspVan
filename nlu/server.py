import http.server
import json
import logging
import socketserver

logger = logging.getLogger(__name__)


class NLURequesthandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, nlp, *args, **kwargs):
        self.nlp = nlp
        super().__init__(*args, **kwargs)

    def do_POST(self):
        """This is the predict endpoint. Takes a text parameter as input"""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")

        # Parse the POST data
        data = json.loads(post_data)

        # Process the string parameter
        response = {}
        if "text" in data:
            sentence = data["text"]
            logger.info(f"[POST] sentence: '{sentence}'")
            response = self.nlp([sentence])[0]
        else:
            error_msg = "💥 No text parameter received"
            logger.error(f"[POST] {error_msg}")
            response = {"error": error_msg}

        # Send JSON response
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        # Send JSON response
        self.wfile.write(json.dumps("hello 👋").encode())


def init_handler_and_run_server(nlp, port):
    def handler_factory(nlp):
        """This is a wrapper to do delayed initialization of the handler"""

        def _handler(*args, **kwargs):
            return NLURequesthandler(nlp, *args, **kwargs)

        return _handler

    # Create the handler
    nlu_handler = handler_factory(nlp)

    # Set up the server
    with socketserver.TCPServer(("", port), nlu_handler) as httpd:
        print(f"🔌 Serving on port {port}")
        httpd.serve_forever()
