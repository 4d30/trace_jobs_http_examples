#!/usr/bin/env python

import os
import json
from itertools import repeat
from datetime import datetime, date, timedelta
from functools import partial

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from . import cafs
from .trace_jobs_index import engine


def generate_queries():
    integers = range(7)
    names = map(lambda x: f"{x:02d}.json", integers)
    names = map(os.path.join,
                repeat('http-examples'),
                repeat('queries'),
                names)
    yield from names


def load_json(filename):
    with open(filename, 'r') as handle:
        return json.load(handle)


def overwrite_yesterday(data):
    output = {}
    for k, v in data.items():
        # Check if the value is a dictionary 
        if isinstance(v, dict):
            nested_dict = {}
            for nk, nv in v.items():
                if nv == '$YESTERDAY':
                    yesterday = date.today() - timedelta(days=2)
                    nv = yesterday.isoformat()
                nested_dict[nk] = nv
            output[k] = nested_dict
        # Handle top-level string values
        elif v == '$YESTERDAY':
            yesterday = date.today() - timedelta(days=2)
            output[k] = yesterday.isoformat()
        else:
            output[k] = v
    return output


def make_nice_html(title, filename):
    raw_json = load_json(filename)
    pretty_json = json.dumps(raw_json, indent=2)
    today = datetime.now().strftime("%Y-%m-%d")
    formatter = HtmlFormatter(
        full=True,
        title=' '.join([title, today]),
        noclasses=False,
        style="friendly",
        lineanchors='line',
        linenos='inline',
        wrapcode=True,
        prestyles='font-size:16px;',
        cssfile='foo.css'
    )
    highlighted_code = highlight(pretty_json, JsonLexer(), formatter)
    # css = formatter.get_style_defs(".highlight")
    # css_path = os.path.join(os.getenv('HTTP_ROOT'), 'style.css')
    # with open(css_path, "w") as f:
    #     f.write(css)
    return highlighted_code


cafs_get = partial(cafs.get, cafs_root=os.getenv('CAFS_ROOT'))


def main():
    names = generate_queries()
    for name in names:
        query = load_json(name)
        query = overwrite_yesterday(query)

        content_ids = engine.search(query)
        content_ids = tuple(content_ids)
        records = map(cafs_get, content_ids)
        records = tuple(records)
        content_ids = zip(repeat('id'), content_ids)
        records = zip(repeat('data'), records)
        results = zip(content_ids, records)
        results = map(dict, results)
        results = tuple(results)

        payload = results = {"results": results,
                             "next_offset": 12 }

        payload_path = os.path.join(os.getenv('HTTP_ROOT'),
                                    os.path.basename(name))
        with open(payload_path, 'w') as handle:
            print(json.dumps(payload), file=handle)
        html = make_nice_html(query['title'], payload_path)
        output_path = payload_path.replace('json', 'html')
        with open(output_path, 'w') as handle:
            print(html, file=handle)


if __name__ == '__main__':
    main()
