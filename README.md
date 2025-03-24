# Guestbook

## Install

`./start-local.sh` <br>
<br>
steps that the code runs: <br>
=> start kind cluster with local registry and nginx <br>
=> deploy grafana stack locally <br>
=> build the code and push it to the local registry <br>
=> deploy the guestbook app with trace and metrics enabled <br>
<br>

### Notes

<br>
to deploy the victoria stack we need to first remove the helm charts that are installed by default
and run <br>
`./victoriametrics/deploy.sh` this will deploy the guestbook app and update the otlp to push to a new endpoint also it will deploy grafana with the victoriametric logs and metrics
