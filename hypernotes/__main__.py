import argparse
import copy
import json
import textwrap
import webbrowser
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Set, Union, Any

from hypernotes import Store, Note


def _format_notes_as_html(notes: List[Note]):
    template_note = notes[0]
    general_columns = [
        template_note._start_datetime_key,
        template_note._end_datetime_key,
        template_note._text_key,
    ]
    parameters = set()  # type: Set[str]
    metrics = set()  # type: Set[str]

    for note in notes:
        parameters.update(note.parameters)
        metrics.update(note.metrics)

    all_columns = (
        general_columns
        + sorted([f"metrics.{x}" for x in metrics])
        + sorted([f"parameters.{x}" for x in parameters])
    )

    data = []  # type: List[dict]
    for note in notes:
        row = {}  # type: dict
        for col in general_columns:
            value = note.get(col, "")
            if isinstance(value, datetime):
                value = value.isoformat()
            row[col] = value
        for col in metrics:
            row[f"metrics.{col}"] = note.metrics.get(col, "")
        for col in parameters:
            row[f"parameters.{col}"] = note.parameters.get(col, "")
        data.append(row)

    js_var_data = json.dumps(data)
    # Points in column names need to be escaped for the 'data' attribute in datatables
    escaped_columns = [col.replace(".", "\\\\.") for col in all_columns]
    js_columns = "[" + ", ".join(f'{{data: "{col}"}}' for col in escaped_columns) + "]"
    js_table_tr = "<tr>" + "".join(f"<th>{col}</th>" for col in all_columns) + "</tr>"

    html_start = textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
        """
    )

    html_header = textwrap.dedent(
        """\
        <head>
            <script src="https://code.jquery.com/jquery-3.4.1.min.js"></script>

            <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.19/css/jquery.dataTables.css">
            <script type="text/javascript" charset="utf8"
                src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.js"></script>

            <meta charset=utf-8 />
            <title>Store - DataTable</title>
        </head>
        """
    )

    html_body = textwrap.dedent(
        f"""\
        <body>
            <div class="container">
                <script type="text/javascript" class="init">
                    var data = {js_var_data}
                    $(document).ready(function () {{
                        $('#store_table').DataTable({{
                            data: data, columns: {js_columns}
                        }}

                        );
                    }});

                </script>
                <table id="store_table" class="display nowrap" width="100%">
                    <thead>
                        {js_table_tr}
                    </thead>
                </table>

            </div>
        </body>
        """
    )

    html_end = "</html>"

    return html_start + html_header + html_body + html_end


class HTMLResponder(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


if __name__ == "__main__":
    # TODO: Add text
    parser = argparse.ArgumentParser("")
    parser.add_argument("store_path", type=str)
    parser.add_argument("--view", action="store_true")
    group = parser.add_mutually_exclusive_group(required=False)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--no-browser", action="store_true")

    args = parser.parse_args()
    if args.view:
        store = Store(args.store_path)
        html = _format_notes_as_html(store.load())

        try:
            host = "localhost"
            server = HTTPServer((host, args.port), HTMLResponder)
            url = f"http://localhost:{args.port}"
            print(
                f"Started server on {url}. Server can be stopped with control+c / ctrl+c"
            )
            if not args.no_browser:
                webbrowser.open_new_tab(url)
            server.serve_forever()
        except KeyboardInterrupt:
            print("Keyboard interrupt recieved. Shutting down...")
            server.socket.close()
