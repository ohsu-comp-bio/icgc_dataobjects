import json

from ga4gh import metadata_pb2 as metadata
from ga4gh import data_objects_pb2 as data_objects

from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import Parse

# PROBLEM:
# pytest ...
# ga4gh/metadata_service_pb2.py:17: in <module>
# from google.api import annotations_pb2 as google_dot_api_dot_annotations__pb2
# E   ImportError: No module named api
# solution:
# $ PYTHONPATH=. pytest ...
from ga4gh import metadata_service_pb2 as metadata_service
from ga4gh import data_objects_service_pb2 as data_objects_service


def test_dataset_json():
    """ assert dataset moves from pb to json struct """
    dataset = metadata.Dataset()
    dataset.id = 'foo'
    dataset.name = 'foo name'
    dataset.description = 'foo description'
    dataset.attributes.attr['file_ids'].values.add().string_value = '1'
    dataset.attributes.attr['file_ids'].values.add().string_value = '2'

    dataset_dict = json.loads(MessageToJson(dataset))
    assert(dataset.id == dataset_dict['id'])
    assert(dataset.name == dataset_dict['name'])
    assert(dataset.description == dataset_dict['description'])
    attributes = dataset_dict['attributes']['attr']['file_ids']['values']
    assert(attributes[0]['stringValue'] == '1')
    assert(attributes[1]['stringValue'] == '2')


def test_dataobject_json():
    text = """
{
  "dataobjects":[
    {
      "info":{
        "otherIdentifiers":{
          "tcgaAliquotBarcode":[
            null
          ],
          "tcgaSampleBarcode":[
            null
          ]
        },
        "specimenId":[
          "SP117136"
        ],
        "objectId":"6329334b-dcd5-53c8-98fd-9812ac386d30",
        "study":[
          "PCAWG"
        ],
        "sampleId":[
          "SA542735"
        ],
        "submittedSampleId":[
          "PD4982a"
        ],
        "access":"controlled",
        "submittedSpecimenId":[
          "CGP_specimen_1387555"
        ],
        "primarySite":"Breast",
        "dataCategorization":{
          "dataType":"Aligned Reads",
          "experimentalStrategy":"WGS"
        },
        "submittedDonorId":"CGP_donor_1337237",
        "analysisMethod":{
          "analysisType":"Reference alignment",
          "software":"BWA MEM"
        },
        "specimenType":[
          "Primary tumour - solid tissue"
        ],
        "referenceGenome":{
          "downloadUrl":"ftp://ftp.sanger.ac.uk/pub/project/PanCancer/genome.fa.gz",
          "genomeBuild":"GRCh37",
          "referenceName":"hs37d5"
        }
      },
      "updated":1428646138,
      "provenance":{
        "operation":"BWA MEM"
      },
      "links":[
        {
          "url":"https://dcc.icgc.org/api/v1/donors/DO217962",
          "mime_type":"application/json",
          "rel":"individual"
        },
        {
          "url":"https://dcc.icgc.org/api/v1/projects/BRCA-EU",
          "mime_type":"application/json",
          "rel":"project"
        },
        {
          "url":"https://dcc.icgc.org/api/v1/repositories/pcawg-london",
          "mime_type":"application/json",
          "rel":"repository"
        },
        {
          "url":"https://dcc.icgc.org/api/v1/repositories/pcawg-barcelona",
          "mime_type":"application/json",
          "rel":"repository"
        },
        {
          "url":"https://dcc.icgc.org/api/v1/repositories/collaboratory",
          "mime_type":"application/json",
          "rel":"repository"
        },
        {
          "url":"https://dcc.icgc.org/api/v1/repositories/ega",
          "mime_type":"application/json",
          "rel":"repository"
        }
      ],
      "file_name":"f5c9381090a53c54358feb2ba5b7a3d7.bam",
      "md5sum":"f5c9381090a53c54358feb2ba5b7a3d7",
      "urls":[
        "https:/gtrepo-ebi.annailabs.com/cghub/data/analysis/download/f5c9381090a53c54358feb2ba5b7a3d7.bam",
        "https:/gtrepo-bsc.annailabs.com/cghub/data/analysis/download/f5c9381090a53c54358feb2ba5b7a3d7.bam",
        "https:/www.cancercollaboratory.org:9080/oicr.icgc/data/6329334b-dcd5-53c8-98fd-9812ac386d30f5c9381090a53c54358feb2ba5b7a3d7.bam",
        "http:/ega.ebi.ac.uk/ega/f5c9381090a53c54358feb2ba5b7a3d7.bam"
      ],
      "file_size":128724614500,
      "dataset_id":"efcf90ee-53ae-4f9f-b29a-e0a83ca70272",
      "id":"FI9995",
      "mime_type":"BAM"
    }
  ]
}
    """
    pb_response = data_objects_service.ListDataObjectsResponse()
    Parse(text, pb_response, ignore_unknown_fields=True)
    assert(pb_response.dataobjects)
    assert(len(pb_response.dataobjects) == 1)
    data_object = pb_response.dataobjects[0]


def _dump_object(obj):
    try:
        for descriptor in obj.DESCRIPTOR.fields:
            value = getattr(obj, descriptor.name)
            if descriptor.type == descriptor.TYPE_MESSAGE:
                if descriptor.label == descriptor.LABEL_REPEATED:
                    map(_dump_object, value)
                else:
                    _dump_object(value)
            elif descriptor.type == descriptor.TYPE_ENUM:
                enum_name = descriptor.enum_type.values[value].name
                print "%s: %s" % (descriptor.full_name, enum_name)
            else:
                print "%s: %s" % (descriptor.full_name, value)
    except Exception as e:
        print obj
