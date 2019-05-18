import argparse
import copy
import json
import textwrap
import webbrowser
import sys
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Set, Union, Any

from hypernotes import Store, Note, _flatten_notes, _all_keys_from_dicts, _key_order


def _format_notes_as_html(notes: List[Note]):
    flat_dicts = _flatten_notes(notes)
    all_keys = _all_keys_from_dicts(flat_dicts)

    key_order = _key_order(all_keys, additional_keys_subset=["metrics", "parameters"])

    data = []  # type: List[dict]
    for d in flat_dicts:
        row = {}  # type: dict
        for col in key_order:
            value = d.get(col, "")
            if isinstance(value, datetime):
                value = value.isoformat()
            row[col] = value
        data.append(row)

    js_var_data = json.dumps(data)
    # Points in column names need to be escaped for the 'data' attribute in datatables
    escaped_columns = [col.replace(".", "\\\\.") for col in key_order]
    js_columns = "[" + ", ".join(f'{{data: "{col}"}}' for col in escaped_columns) + "]"
    js_table_tr = "<tr>" + "".join(f"<th>{col}</th>" for col in key_order) + "</tr>"

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
        html = _format_notes_as_html(store.load())
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def _parse_args(args):
    parser = argparse.ArgumentParser(
        "This command-line interface can be used to"
        + " get a quick glance into a store.\n\nIt will start an http server and"
        + " automatically open the relevant page in your web browser."
        + " The page will contain an interactive table showing the most relevant"
        + " information of all notes in the store such as metrics, parameters, etc."
    )
    parser.add_argument("store_path", type=str, help="path to json store")
    parser.add_argument(
        "--port", type=int, default=8080, help="port for http server (default=8080)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="can be passed to prevent automatic opening of web browser",
    )

    return parser.parse_args(args)


def main(raw_args):
    global store
    args = _parse_args(raw_args)
    store = Store(args.store_path)

    try:
        host = "localhost"
        server = HTTPServer((host, args.port), HTMLResponder)
        url = f"http://localhost:{args.port}"
        print(f"Started server on {url}. Server can be stopped with control+c / ctrl+c")
        if not args.no_browser:
            webbrowser.open_new_tab(url)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt recieved. Shutting down...")
        server.socket.close()


if __name__ == "__main__":
    main(sys.argv[1:])
