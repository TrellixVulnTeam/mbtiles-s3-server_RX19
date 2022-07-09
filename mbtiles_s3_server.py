from gevent import (
    monkey,
)
monkey.patch_all()

from contextlib import ExitStack, contextmanager
import itertools
import json
import logging
import os
import signal
import sys
import tarfile
import tempfile

import gevent
from gevent.pywsgi import (
    WSGIServer,
)
from flask import (
    Flask,
    Response,
    request,
)
import httpx
from sqlite_s3_query import sqlite_s3_query


def mbtiles_s3_server(
        logger,
        exit_stack,
        port,
        mbtiles,
        http_access_control_allow_origin,
):
    server = None

    http_client = exit_stack.enter_context(httpx.Client())

    # So we can share a single http client (i.e. a single pool of connections) for
    # all instances of sqlite_s3_query
    @contextmanager
    def get_http_client():
        yield http_client

    def read(path):
        real_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), path)
        with open(real_path, 'rb') as f:
            return f.read()

    def extract(path):
        tempdir = exit_stack.enter_context(tempfile.TemporaryDirectory())
        real_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), path)
        with tarfile.open(real_path, 'r:gz') as f:
            f.extractall(tempdir)
        return tempdir

    mbtiles_dict = {
        (mbtile['IDENTIFIER'], mbtile['VERSION']): mbtile
        for mbtile in mbtiles
    }

    styles_dict = {
        ('positron-gl-style', '1.8', 'style.json'):
        read('mbtiles_s3_server/vendor/positron-gl-style@1.8/style.json'),
    }

    statics_dict = {
        ('maplibre-gl', '2.1.9', 'maplibre-gl.css'): {
            'bytes': read('mbtiles_s3_server/vendor/maplibre-gl@2.1.9/maplibre-gl.css'),
            'mime': 'text/css',
        },
        ('maplibre-gl', '2.1.9', 'maplibre-gl.js'): {
            'bytes': read('mbtiles_s3_server/vendor/maplibre-gl@2.1.9/maplibre-gl.js'),
            'mime': 'application/javascript',
        },
    }

    fonts_dict = {
        ('fonts-gl', '2.0'): extract('mbtiles_s3_server/vendor/fonts-gl@2.0/fonts.tar.gz')
    }

    def start():
        server.serve_forever()

    def stop():
        server.stop()

    app = Flask('app')

    sql = '''
        SELECT
            tile_data
        FROM
            tiles
        WHERE
            zoom_level=? AND
            tile_column=? AND
            tile_row=?
        LIMIT 1
    '''

    def get_tile(identifier, version, z, x, y):
        try:
            mbtiles_url = mbtiles_dict[(identifier, version)]['URL']
        except KeyError:
            return Response(status=404)

        tile_data = None
        y_tms = (2**z - 1) - y

        with \
                sqlite_s3_query(url=mbtiles_url, get_http_client=get_http_client) as query, \
                query(sql, params=(z, x, y_tms)) as (columns, rows):

            for row in rows:
                tile_data = row[0]

        return \
            Response(status=200, response=tile_data, headers={
                'content-encoding': 'gzip',
                'content-type': 'application/vnd.mapbox-vector-tile',
            }) if tile_data is not None else \
            Response(status=404)

    def get_styles(identifier, version, file):
        try:
            style_bytes = styles_dict[(identifier, version, file)]
        except KeyError:
            return Response(status=404)

        try:
            tiles_identifier_with_version = request.args['tiles']
        except KeyError:
            return Response(status=400)

        try:
            tiles_identifier, tiles_version = tiles_identifier_with_version.split('@')
        except ValueError:
            return Response(status=400)

        try:
            mbtiles_dict[(tiles_identifier, tiles_version)]
        except KeyError:
            return Response(status=404)

        try:
            fonts_identifier_with_version = request.args['fonts']
        except KeyError:
            return Response(status=400)

        try:
            fonts_identifier, fonts_version = fonts_identifier_with_version.split('@')
        except ValueError:
            return Response(status=400)

        try:
            fonts_dict[(fonts_identifier, fonts_version)]
        except KeyError:
            return Response(status=404)

        style_dict = json.loads(style_bytes)
        style_dict['sources']['openmaptiles'] = {
            'type': 'vector',
            'tiles': [
                request.url_root + 'v1/tiles/' + tiles_identifier_with_version + '/{z}/{x}/{y}.mvt'
            ],
        }
        style_dict['glyphs'] = request.url_root + 'v1/fonts/' + \
            fonts_identifier_with_version + '/{fontstack}/{range}.pbf'

        return Response(status=200, content_type='application/json',
                        response=json.dumps(style_dict))

    def get_fonts(identifier, version, stack, range):
        try:
            font_path = fonts_dict[(identifier, version)]
        except KeyError:
            return Response(status=404)

        if '.' in stack or '.' in range:
            return Response(status=404)

        def read(path):
            with open(path, 'rb') as f:
                return f.read()

        # While we're unable to join the font stack
        stack = stack.split('.')[0]

        try:
            font_bytes = b''.join((
                read(os.path.join(font_path, font, range + '.pbf.gz'))
                for font in stack.split(',')
            ))
        except FileNotFoundError:
            return Response(status=404)

        return Response(status=200, headers={
            'content-encoding': 'gzip',
        }, response=font_bytes)

    def get_static(identifier, version, file):
        try:
            static_dict = statics_dict[(identifier, version, file)]
        except KeyError:
            return Response(status=404)

        return Response(status=200, content_type=static_dict['mime'],
                        response=static_dict['bytes'])

    @app.after_request
    def _add_headers(resp):
        if http_access_control_allow_origin:
            resp.headers['access-control-allow-origin'] = http_access_control_allow_origin
        return resp

    app.add_url_rule(
        '/v1/tiles/<string:identifier>@<string:version>/<int:z>/<int:x>/<int:y>.mvt',
        view_func=get_tile)
    app.add_url_rule(
        '/v1/styles/<string:identifier>@<string:version>/<string:file>', view_func=get_styles)
    app.add_url_rule(
        '/v1/fonts/<string:identifier>@<string:version>/<string:stack>/<string:range>.pbf',
        view_func=get_fonts)
    app.add_url_rule(
        '/v1/static/<string:identifier>@<string:version>/<string:file>', view_func=get_static)
    server = WSGIServer(('0.0.0.0', port), app, log=app.logger)

    return start, stop


def normalise_environment(key_values):
    # Separator is chosen to
    # - show the structure of variables fairly easily;
    # - avoid problems, since underscores are usual in environment variables
    separator = '__'

    def get_first_component(key):
        return key.split(separator)[0]

    def get_later_components(key):
        return separator.join(key.split(separator)[1:])

    without_more_components = {
        key: value
        for key, value in key_values.items()
        if not get_later_components(key)
    }

    with_more_components = {
        key: value
        for key, value in key_values.items()
        if get_later_components(key)
    }

    def grouped_by_first_component(items):
        def by_first_component(item):
            return get_first_component(item[0])

        # groupby requires the items to be sorted by the grouping key
        return itertools.groupby(
            sorted(items, key=by_first_component),
            by_first_component,
        )

    def items_with_first_component(items, first_component):
        return {
            get_later_components(key): value
            for key, value in items
            if get_first_component(key) == first_component
        }

    nested_structured_dict = {
        **without_more_components, **{
            first_component: normalise_environment(
                items_with_first_component(items, first_component))
            for first_component, items in grouped_by_first_component(with_more_components.items())
        }}

    def all_keys_are_ints():
        def is_int(string):
            try:
                int(string)
                return True
            except ValueError:
                return False

        return all([is_int(key) for key, value in nested_structured_dict.items()])

    def list_sorted_by_int_key():
        return [
            value
            for key, value in sorted(
                nested_structured_dict.items(),
                key=lambda key_value: int(key_value[0])
            )
        ]

    return \
        list_sorted_by_int_key() if all_keys_are_ints() else \
        nested_structured_dict


def main():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)

    env = normalise_environment(os.environ)

    with ExitStack() as exit_stack:
        start, stop = mbtiles_s3_server(
            logger,
            exit_stack,
            int(os.environ['PORT']),
            env['MBTILES'],
            env.get('HTTP_ACCESS_CONTROL_ALLOW_ORIGIN'),
        )

        gevent.signal_handler(signal.SIGTERM, stop)
        start()
        gevent.get_hub().join()

    logger.info('Shut down gracefully')


if __name__ == '__main__':
    main()
