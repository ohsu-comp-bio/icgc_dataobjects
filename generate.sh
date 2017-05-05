#!/usr/bin/env bash

# clone schemas
mkdir -p schemas
cd schemas
if [ ! -d "ga4gh-schemas" ]; then
  git clone https://github.com/ga4gh/ga4gh-schemas
else
  echo ga4gh-schemas already cloned
fi
# ensure we are on correct branch
cd ga4gh-schemas
git checkout data-objects
# back to project root
cd ../..

# generate python code for ga4gh
protoc \
   --proto_path=schemas/ga4gh-schemas/src/main/proto \
   --python_out=. \
   schemas/ga4gh-schemas/src/main/proto/ga4gh/*.proto
# and google
protoc \
  --proto_path=schemas/ga4gh-schemas/src/main/proto \
  --python_out=. \
  schemas/ga4gh-schemas/src/main/proto/google/api/*.proto


# make them a python package
touch ./ga4gh/__init__.py
touch ./google/__init__.py
touch ./google/api/__init__.py

echo Code generation complete 
