#!/usr/bin/env python

"""
Proxy front end to the dcc server
"""
import os
from flask import request, Response, abort, make_response
from flask import current_app as app
from flask import stream_with_context
import requests
import urllib
from pydash import deep_set, deep_get, filter_, reduce_, pluck
from json import loads, dumps
import re
import uuid

PROXY_TARGET = os.environ.get('PROXY_TARGET', None)
assert PROXY_TARGET, 'Please set env variable PROXY_TARGET to an icgc URL'
NOT_FOUND = 404

# for _snake_case
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def _snake_case(name):
    """ camel case to snake case """
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def _is_sequence(arg):
    """ true if list """
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


def _safe_set(t, tk, s, sk=None, make_snake=False):
    """ _safe_set(dest,'k1',source,'k2') # if k2 is source, set it.
       if k2 points to a single element vector, make it a scalar  """
    if not sk:
        sk = tk
    if s and sk in s:
        val = s[sk]
        if _is_sequence(val) and len(val) == 1:
            val = val[0]
        if make_snake:
            tk = _snake_case(tk)
        t[tk] = val


def datasets_get_one(id):
    url = _remote_url(url='/api/v1/entityset/{}?includeItems=true'.format(id))
    r = requests.get(url)
    entityset = r.json()
    """
    {
    "count": 0,
    "description": "foo description",
    "timestamp": 1493854922369,
    "subtype": "NORMAL",
    "state": "FINISHED",
    "version": 2,
    "items": [],
    "type": "FILE",
    "id": "fb0a58ec-8c8f-4246-a6e0-cb082780d190",
    "name": "foo name"
    }
    """
    file_ids = []
    attributes = {'attr': {'file_ids': {'values': file_ids}}}
    for item in entityset['items']:
        file_ids.append({"stringValue": item})
    dataset = {
        'id': entityset['id'],
        'name': entityset['name'],
        'description': entityset['description'],
        'attributes': attributes
    }
    return make_response(dumps(dataset))


def datasets_post():
    """
    facade create a dcc.entityset from a ga4gh.dataset
    """
    dataset = request.get_json()
    app.logger.debug(dataset)
    """
    {
      "attributes": {
        "attr": {
          "file_ids": {
            "values": [
              {
                "stringValue": "1"
              },
              {
                "stringValue": "2"
              }
            ]
          }
        }
      },
      "description": "foo description",
      "id": "foo",
      "name": "foo name"
    }
    """
    if 'attributes' in dataset and 'attr' in dataset['attributes']:
        attributes = dataset['attributes']['attr']
    file_ids = []
    if 'file_ids' in attributes:
        for attribute in attributes['file_ids']['values']:
            app.logger.debug(attribute.__class__)
            app.logger.debug(attribute)
            if 'stringValue' in attribute:
                file_ids.append(attribute['stringValue'])
    """
    https://localhost/api/v1/entityset/external
    {"filters":{"file":{"id":{"is":["FIffb3540a357a4c23611364d4cafa5d57","FIff8902a9dfebdb600b6b9e3ecfd7e999"]}}},"size":2,"type":"FILE","name":"test2","description":"","sortBy":"affectedDonorCountFiltered","sortOrder":"DESCENDING"}
    """
    entityset = {
      "filters": {
        "file": {
          "id": {
            "is": file_ids
          }
        }
      },
      "size": len(file_ids),
      "type": "FILE",
      "name": dataset['name'],
      "description": dataset['description'],
      "sortBy": "id",
      "sortOrder": "DESCENDING"
    }
    url = _remote_url(url='/api/v1/entityset/external')
    app.logger.debug(dumps(entityset))
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, data=dumps(entityset), headers=headers)
    return make_response(dumps({'id': r.json()['id']}))


def data_object_post():
    """
    facade:Implement ga4gh::data_objects POST using dcc backend
    * use api to fetch dependencies
    * however, the api does not have a way to create a file in repo
    therefore, create document directly in ES
    """

    # app.logger.debug(request.data)
    data_object = request.get_json()
    app.logger.debug(data_object)
    app.logger.debug(data_object.keys())

    # create a file centric document
    object_id = str(uuid.uuid4())
    file_centric = {
      "id": 'FI{}'.format(object_id.replace('-', '')),
      "object_id": object_id,
      "file_copies": [],
      "study": []
    }

    if 'submitted_id' in data_object:
        file_centric['submitted_id'] = data_object['submitted_id']

    info = data_object.get('info', None)
    _safe_set(file_centric, "analysisMethod", info, make_snake=True)
    _safe_set(file_centric, "referenceGenome", info, make_snake=True)
    _safe_set(file_centric, "study", info, make_snake=True)
    _safe_set(file_centric, "dataCategorization", info, make_snake=True)

    # fetch donors
    donor_keys = [
          "donorId",
          "otherIdentifiers",
          "primarySite",
          "projectCode",
          "sampleId",
          "specimenId",
          "specimenType",
          "study",
          "submittedDonorId",
          "submittedSampleId",
          "submittedSpecimenId"
        ]

    donors = []
    project_code = None
    sample_id = None
    for link in data_object.get('links', []):
        if link['rel'] == 'sample':
            sample_id = link['id']
    for link in data_object.get('links', []):
        if not link['rel'] == 'individual':
            continue
        url = _remote_url(url='/api/v1/donors/{}?include=specimen'
                              .format(link['id']))
        rsp = requests.get(url, allow_redirects=False)
        donor = rsp.json()
        app.logger.debug(donor)
        app.logger.debug(donor.keys())
        project_code = donor["projectId"]
        file_donor = {'donor_id': donor['id'],
                      'project_code': project_code,
                      "other_identifiers": {
                          "tcga_participant_barcode": None,
                          "tcga_sample_barcode": [],
                          "tcga_aliquot_barcode": []
                        }
                      }
        for key in donor.keys():
            if key in donor_keys:
                file_donor[_snake_case(key)] = donor[key]
        for specimen in donor['specimen']:
            for sample in specimen['samples']:
                if sample['id'] == sample_id:
                    file_donor['specimen_id'] = [specimen['id']]
                    file_donor['sample_id'] = [sample_id]
                    file_donor['study'] = sample['study']
                    file_centric['study'].append(sample['study'])
        donors.append(file_donor)
    file_centric['donors'] = donors

    for link in data_object.get('links', []):
        if not link['rel'] == 'project':
            continue
        project_code = link['id']

    url = _remote_url(url='/api/v1/projects/{}'
                          .format(project_code))
    rsp = requests.get(url, allow_redirects=False)
    app.logger.debug(url)
    app.logger.debug(rsp.json())
    repository_id = rsp.json()['repository'][0].lower()
    if repository_id == 'dbsnp':  # TODO dbsnp is not a repo id
        repository_id = 'cghub'

    url = _remote_url(url='/api/v1/repositories/{}'
                          .format(repository_id))
    rsp = requests.get(url, allow_redirects=False)
    repository = rsp.json()
    app.logger.debug(url)
    app.logger.debug(rsp.json())

    file_copy = {}

    file_centric['access'] = 'controlled'  # TODO - how to vary access level
    _safe_set(file_copy, "repoBaseUrl", repository, "baseUrl", make_snake=True)
    _safe_set(file_copy, "repoCode", repository, "code", make_snake=True)
    _safe_set(file_copy, "repoCountry", repository, "country", make_snake=True)
    _safe_set(file_copy, "repoDataPath", repository, "dataPath", make_snake=True)
    _safe_set(file_copy, "repoMetadataPath", repository, "metadataPath", make_snake=True)

    _safe_set(file_copy, "fileName", data_object, "file_name", make_snake=True)
    _safe_set(file_copy, "fileFormat", data_object, "mime_type", make_snake=True)
    _safe_set(file_copy, "fileMd5sum", data_object, "md5sum", make_snake=True)
    _safe_set(file_copy, "fileSize", data_object, "file_size", make_snake=True)
    _safe_set(file_copy, "lastModified", data_object, "created", make_snake=True)

    file_centric['file_copies'] = [file_copy]
    file_copy['repo_data_bundle_id'] = 'None'
    # we now have a document ready to write to the index
    app.logger.debug(file_centric)
    elastic_host = os.environ.get("ELASTIC_HOST", "dms-development")
    elastic_port = os.environ.get("ELASTIC_PORT", "8900")
    elastic_index = os.environ.get("ELASTIC_INDEX", "icgc-repository")
    elastic_host = "dms-development"
    elastic_port = "8900"

    url = 'http://{}:{}/{}/file-centric/{}'.format(
        elastic_host,
        elastic_port,
        elastic_index,
        file_centric['id']
    )

    r = requests.post(url, data=dumps(file_centric))
    app.logger.debug(url)
    app.logger.debug(r.status_code)
    app.logger.debug(r.text)

    url = 'http://{}:{}/{}/file-text/{}'.format(
        elastic_host,
        elastic_port,
        elastic_index,
        file_centric['id']
    )
    r = requests.post(url, data=dumps(
        {
          "type": "file",
          "id": file_centric['id'],
          "object_id": file_centric['object_id'],
          "file_name": [
            file_copy['file_name']
          ],
          "data_type": file_copy.get('file_format', ''),
          "donor_id": [
            donor['id']
          ],
          "project_code": [
            project_code
          ]
          # ,  "data_bundle_id": "82c009ee-0ec8-4811-bf7c-78b55a7b2fba"
        }
    ))
    app.logger.debug(url)
    app.logger.debug(r.status_code)
    app.logger.debug(r.text)

    return make_response(dumps(file_centric))


def data_object_get(id):
    """
    facade:Implement ga4gh::data_objects get using dcc backend
    use api to fetch
    """
    no_hits = dumps({})
    app.logger.debug(request.get_json())
    file_parameters = {}
    file_parameters['filters'] = {"file": {"id": {"is": [id]}}}
    url = _remote_url(params=file_parameters,
                      url='/api/v1/repository/files')
    rsp = requests.get(url, allow_redirects=False)
    app.logger.debug(rsp.text)
    if 'hits' in rsp.json() and len(rsp.json()['hits']) > 0:
        # create ga4gh data objects
        data_objects = []
        for hit in rsp.json()['hits']:
            data_objects.append(_make_data_object(hit))
        response = make_response(dumps(data_objects[0]))
        return response
    else:
        return make_response(no_hits, NOT_FOUND)


def data_object_search():
    """
    facade:Implement ga4gh::data_objects search using dcc backend
    use api to search & fetch
    """
    app.logger.debug(request.get_json())
    # ListDataObjectsRequest
    list_request = request.get_json()
    # &from=1&size=10&sort=id&order=desc
    default_size = 100
    # for no finds
    no_hits = dumps({'dataobjects': []})
    # file fetch parameters
    file_parameters = {'from': 1, 'size': default_size}
    if 'name_prefix' in list_request:
        # use the keyword api to find file ids
        # https://dcc.icgc.org/api/v1/keywords?from=1&q=41495b&size=5&type=file
        url = _remote_url(params={'from': 1,
                                  'q': list_request['name_prefix'],
                                  'type': 'file',
                                  'size': default_size},
                          url='/api/v1/keywords')
        rsp = requests.get(url, allow_redirects=False)
        app.logger.debug(rsp.text)
        # create a filter from the search results
        if 'hits' in rsp.json() and len(rsp.json()['hits']) > 0:
            ids = []
            for hit in rsp.json()['hits']:
                ids.append(hit['id'])
            file_parameters['filters'] = {"file": {"id": {"is": ids}}}
            # {"file":{"id":{"is":["FI9994","FI9974"]}}}
        else:
            return make_response(no_hits, NOT_FOUND)

    # use the filter to find the files
    # https://dcc.icgc.org/api/v1/repository/files?filters={"file":{"id":{"is":["FI9994","FI9974"]}}}&from=1&size=10&sort=id&order=desc
    url = _remote_url(params=file_parameters,
                      url='/api/v1/repository/files')
    rsp = requests.get(url, allow_redirects=False)
    app.logger.debug(url)
    app.logger.debug(rsp.text)
    if 'hits' in rsp.json() and len(rsp.json()['hits']) > 0:
        # create ga4gh data objects
        data_objects = []
        for hit in rsp.json()['hits']:
            data_objects.append(_make_data_object(hit))
        response = make_response(dumps({'dataobjects': data_objects}))
        return response
    else:
        return make_response(no_hits, NOT_FOUND)


def _make_data_object(hit):
    """ given a dcc repository file, create a ga4gh data object """
    do = {}
    repo_info = hit['fileCopies'][0]
    do['id'] = hit['id']

    _safe_set(do, 'file_name', repo_info, 'fileName')
    _safe_set(do, 'file_size', repo_info, 'fileSize')
    _safe_set(do, 'updated', repo_info, 'lastModified')
    _safe_set(do, 'md5sum', repo_info, 'fileMd5sum')
    _safe_set(do, 'mime_type', repo_info, 'fileFormat')
    _safe_set(do, 'dataset_id', repo_info, 'repoDataBundleId')
    do['urls'] = []
    for repo_info in hit['fileCopies']:
        app.logger.debug(repo_info)
        url = '{}{}{}'.format(
            repo_info.get('repoBaseUrl', ''),
            repo_info.get('repoDataPath', ''),
            repo_info.get('fileName', '')
        )
        do['urls'].append(url.replace('//', '/'))

    if 'analysisMethod' in hit and 'analysisType' in hit['analysisMethod']:
        provenance = {'operation': hit['analysisMethod']['software']}
        do['provenance'] = provenance

    links = []
    for donor in hit['donors']:
        links.append(
            {'rel': 'individual',
             'url': _remote_url(url='/api/v1/donors/{}'.format(donor['donorId'])),  # NOQA
             'mime_type': 'application/json'
             })
    links.append(
        {'rel': 'project',
         'url': _remote_url(url='/api/v1/projects/{}'.format(hit['donors'][0]['projectCode'])),  # NOQA
         'mime_type': 'application/json'
         })
    for repo_info in hit['fileCopies']:
        links.append(
            {'rel': 'repository',
             'url': _remote_url(url='/api/v1/repositories/{}'.format(repo_info['repoCode'])),  # NOQA
             'mime_type': 'application/json'
            })
    do['links'] = links

    info = {}
    for k in hit['donors'][0]:
        # skip fields already mapped
        if k in ['projectCode', 'donorId', 'analysisMethod']:
            continue
        info[k] = hit['donors'][0][k]
    for k in hit:
        # skip fields already mapped
        if k in ['donors', 'fileCopies', 'id']:
            continue
        info[k] = hit[k]
    do['info'] = info
    return do


def _remote_url(params=None, url=None):
    """
    format a url for the configured remote host. if params, a new query_string
    is created.  if url, that url is used instead of original
    """
    if params:
        return _remote_url_params(params, url)
    if url:  # pragma nocoverage
        return "{}{}".format(PROXY_TARGET, url)
    return "{}{}".format(PROXY_TARGET, request.full_path)


def _remote_url_params(params, url=None):
    """
    format a url for the configured remote host, using passed param dict
    """
    if 'filters' in params:
        filters = params['filters']
        params['filters'] = dumps(filters)
    query = urllib.urlencode(params)
    if not url:
        url = request.path
    url = "{}{}?{}".format(PROXY_TARGET, url, query)
    app.logger.debug('url {}'.format(url))
    return url
