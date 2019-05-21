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

from hypernotes import (
    Store,
    Note,
    _flatten_notes,
    _all_keys_from_dicts,
    _key_order,
    _format_datetime,
)


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
                value = _format_datetime(value)
            row[col] = value
        data.append(row)

    js_var_data = json.dumps(data)
    # Points in column names need to be escaped for the 'data' attribute in datatables
    escaped_columns = [col.replace(".", "\\\\.") for col in key_order]
    js_columns = "[" + ", ".join(f'{{data: "{col}"}}' for col in escaped_columns) + "]"
    js_table_tr = "<tr>" + "".join(f"<th>{col}</th>" for col in key_order) + "</tr>"

    html_start = _html_start()
    html_header = _html_header(js_var_data, js_columns)
    html_body = _html_body(js_table_tr)
    html_end = "</html>"

    return html_start + html_header + html_body + html_end


def _html_start() -> str:
    return textwrap.dedent(
        """\
            <!DOCTYPE html>
            <html>
            """
    )


def _html_header(js_var_data: str, js_columns: str) -> str:
    return textwrap.dedent(
        f"""\
        <head>
            <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.1.3/css/bootstrap.css">
            <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.19/css/dataTables.bootstrap4.min.css">

            <script src="https://code.jquery.com/jquery-3.4.1.min.js"></script>
            <script type="text/javascript" language="javascript" src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
            <script type="text/javascript" language="javascript" src="https://cdn.datatables.net/1.10.19/js/dataTables.bootstrap4.min.js"></script>

            <script type="text/javascript" class="init">
                        var data = {js_var_data}
                        $(document).ready(function () {{
                            $('#store_table').DataTable({{
                                data: data,
                                columns: {js_columns},
                                scrollX: true,
                                scrollY: '60vh',
                                scrollCollapse: true,
                            }}

                            );
                        }});

                    </script>

            <style type="text/css" class="init">
                div.dataTables_wrapper {{
                    width: 100%;
                    margin: 0 auto;
                }}
                th {{ font-size: 14px; }}
                td {{ font-size: 13px; }}
            </style>

            <meta charset=utf-8 />
            <title>Store - DataTable</title>
        </head>
        """
    )


def _html_body(js_table_tr: str) -> str:
    return textwrap.dedent(
        f"""\
        <body>
            <div class="page-header text-center">
                <h1>Store Content</h1>
            </div>
            <hr>
            <div class="container">
                <div class="row">
                    <table id="store_table" class="table table-striped table-bordered" style="width:100%">
                        <thead>
                            {js_table_tr}
                        </thead>
                    </table>
                </div>
            </div>
        </body>
        """
    )


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
        "--ip",
        type=str,
        default="localhost",
        help="ip to use for hosting the http server (default=localhost)",
    )
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
        server = HTTPServer((args.ip, args.port), HTMLResponder)
        url = f"http://{args.ip}:{args.port}"
        print(f"Started server on {url}. Server can be stopped with control+c / ctrl+c")
        if not args.no_browser:
            webbrowser.open_new_tab(url)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt recieved. Shutting down...")
        server.socket.close()


if __name__ == "__main__":
    main(sys.argv[1:])
