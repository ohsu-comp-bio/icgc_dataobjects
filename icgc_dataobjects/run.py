#!/usr/bin/env python

"""
Proxy front end to the dcc server
"""

import os
from flask import request, jsonify, Response, abort, Flask
from flask_cors import CORS
# our utilities
import dcc_proxy


def _configure_app():
    """ set app wide config """
    # start the app
    app = Flask(__name__)
    # allow cross site access
    CORS(app)
    # after commit, publish
    return app


#  main configuration
app = _configure_app()


# https://github.com/ohsu-comp-bio/data-object-schemas/blob/feature/gdc/proto/data_objects.proto
@app.route('/api/v1/data/object/search', methods=['POST'])
def data_object_search():
    """
    ga4gh::data-object-schemas data/object/search
    """
    app.logger.debug(request.data)
    return dcc_proxy.data_object_search()


# https://github.com/ohsu-comp-bio/data-object-schemas/blob/feature/gdc/proto/data_objects.proto
@app.route('/api/v1/data/object/<path:id>', methods=['GET'])
def data_object_get(id):
    """
    ga4gh::data-object-schemas data/object
    """
    return dcc_proxy.data_object_get(id)


# https://github.com/ohsu-comp-bio/data-object-schemas/blob/feature/gdc/proto/data_objects.proto
@app.route('/api/v1/data/object', methods=['POST'])
def data_object_post():
    """
    ga4gh::data-object-schemas data/object
    """
    return dcc_proxy.data_object_post()


# https://github.com/ohsu-comp-bio/data-object-schemas/blob/feature/gdc/proto/data_objects.proto
@app.route('/api/v1/datasets', methods=['POST'])
def datasets_post():
    """
    ga4gh::data-object-schemas data/object
    """
    return dcc_proxy.datasets_post()


# https://github.com/ohsu-comp-bio/data-object-schemas/blob/feature/gdc/proto/data_objects.proto
@app.route('/api/v1/datasets/<path:id>', methods=['GET'])
def datasets_get_one(id):
    """
    ga4gh::data-object-schemas data/object
    """
    return dcc_proxy.datasets_get_one(id)


# Private util functions


#  print useful information at startup
app.logger.debug('URL map {}'.format(app.url_map))


# Entry point of app
if __name__ == '__main__':  # pragma: no cover
    debug = 'API_DEBUG' in os.environ  # TODO does eve override?
    api_port = int(os.environ.get('API_PORT', '5000'))
    api_host = os.environ.get('API_TARGET', '0.0.0.0')
    app.run(debug=debug, port=api_port, host=api_host, threaded=True)
