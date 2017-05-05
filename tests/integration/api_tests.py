#!/usr/bin/env python
"""
Test endpoints
"""
from ga4gh import metadata_pb2 as metadata
from ga4gh import data_objects_pb2 as data_objects

from google.protobuf.json_format import Parse
import json
import os

HEADERS = {'Content-Type': 'application/json'}
FILE_ID = os.environ.get('TEST_FILE_ID', "FI9995")


def test_search_for_file(client):
    # search for a file
    # curl -X POST    \
    # localhost:8000/api/v1/data/object/search \
    # -H "Content-Type: application/json"  \
    # -d '{"name_prefix":"fffd8a2e-da4a-4355-b2bc-1a2f6cef0c5e"}' | jq  '.'
    # export TEST_FILE_ID=FI9995
    # export TEST_FILE_ID=fffd8a2e-da4a-4355-b2bc-1a2f6cef0c5e
    data = {"name_prefix": FILE_ID}
    response = client.post('/api/v1/data/object/search',
                           data=json.dumps(data),
                           headers=HEADERS)
    assert response.status_code == 200
    pb_response = data_objects.ListDataObjectsResponse()
    Parse(response.data, pb_response, ignore_unknown_fields=True)
    assert(pb_response.dataobjects)
    assert(len(pb_response.dataobjects) == 1)
    data_object = pb_response.dataobjects[0]
    assert data_object.id == FILE_ID


def test_get_a_file(client):
    # get a file
    # curl -s localhost:8000/api/v1/data/object/FI9995  | jq .
    response = client.get('/api/v1/data/object/{}'.format(FILE_ID))
    assert response.status_code == 200
    data_object = data_objects.DataObject()
    Parse(response.data, data_object, ignore_unknown_fields=True)
    assert data_object.id == FILE_ID


def test_get_a_file(client):
    # get a file
    # curl -s localhost:8000/api/v1/data/object/FI9995  | jq .
    response = client.get('/api/v1/data/object/{}'.format(FILE_ID))
    assert response.status_code == 200
    data_object = data_objects.DataObject()
    Parse(response.data, data_object, ignore_unknown_fields=True)
    assert data_object.id == FILE_ID


def skip_test_add_a_file(client):
    # add a file
    # curl -X POST  -s localhost:8000/api/v1/data/object
    # -H "Content-Type: application/json"
    # -d  '
    # {
    #   "id":"FFF",
    #   "file_name":"my-great-file.txt",
    #   "links":[
    #     {
    #       "rel":"individual",
    #       "id":"DO217962"
    #     },
    #     {
    #       "rel":"sample",
    #       "id":"SA544497"
    #     }
    #   ]
    # }
    # '
    # | jq .
    url = '/api/v1/data/object'
    data = """
        {
          "id":"FFF",
          "file_name":"my-great-file.txt",
          "links":[
            {
              "rel":"individual",
              "id":"DO217962"
            },
            {
              "rel":"sample",
              "id":"SA544497"
            }
          ]
        }
    """


    response = client.post(url, data=data, headers=HEADERS)
    print response.text
    assert response.status_code == 200
    pb_response = data_objects.AddDataObjectResponse()
    Parse(response.data, pb_response, ignore_unknown_fields=True)
    assert(len(pb_response.id) > 1)
