
Goals and Scope
---------------

* standardized use of common attributes/values for data_objects(files, images and resources)
* comply with data_set container semantics

The API provides information on the data_objects and how the link to data_sets and other entities in the metadata schema.


DataObject Records
----------------

A data object represents a resource associated with a project, individual, sample or other metadata entity.

[Dataobjects](https://github.com/ga4gh/ga4gh-schemas/blob/data-objects/src/main/proto/ga4gh/data_objects.proto#L28) can belong to one or more [Datasets](https://github.com/ga4gh/ga4gh-schemas/blob/master/src/main/proto/ga4gh/metadata.proto#L10)


Dataobject Use Cases
----------------

For server implementors, data_objects are a useful way
to represent data stored in a file system, object store 'bucket', API or other data management system.

For data curators, data_objects provide a mechanism to represent and exchange the data describing the underlying resources for a project or experiment.

For data accessors, data_objects are a simple way provide provenance and reproducibility.



Example application
----------------

`icgc_dataobjects` is a Flask application that accepts GA4GH data object service requests and resolves them against an ICGC data portal.



Setup
----------------

```
# after ensuring python 2.7 is installed
# install dependencies
$ pip install -r requirements.txt

# bring down ga4gh schemas and generate code
$ ./generate.sh

# run tests
$ pytest

```
