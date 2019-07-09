#!/usr/bin/env bash

output_folder="./figs"

jupyter nbconvert \
  --ExecutePreprocessor.allow_errors=True \
  --ExecutePreprocessor.timeout=-1 \
  --FilesWriter.build_directory=$output_folder \
  --execute "network simulation starter.ipynb"


jupyter nbconvert \
  --ExecutePreprocessor.allow_errors=True \
  --ExecutePreprocessor.timeout=-1 \
  --FilesWriter.build_directory=$output_folder \
  --execute "Reproduce paper figures.ipynb"