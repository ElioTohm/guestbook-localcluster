# Guestbook

## Install

`./start-local.sh`

steps that the code runs:
=> start kind cluster with local registry and nginx
=> deploy grafana stack locally
=> build the code and push it to the local registry
=> deploy the guestbook app with trace and metrics enabled

### Notes

to deploy the victoria stack we need to first remove the helm charts that are installed by default
and run
`./victoriametrics/deploy.sh` this will deploy the guestbook app and update the otlp to push to a new endpoint also it will deploy grafana with the victoriametric logs and metrics
