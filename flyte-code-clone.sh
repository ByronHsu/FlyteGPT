#!/bin/bash
set -x

pushd data

repos=("flytesnacks" "flytekit" "flyte" "flyteidl" "flyteconsole" "flyteadmin" "flyteplugins" "datacatalog" "flytectl" "flytetools" "flytepropeller")

for repo in "${repos[@]}"; do
    git clone "git@github.com:flyteorg/$repo.git"
done

popd data
