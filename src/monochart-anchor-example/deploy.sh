#!/bin/bash
. $(pwd)/init.sh

print_headline "Installing Guestbook"
helm upgrade --install growthbook bedag/raw -f src/chart/values.yaml  -n default
