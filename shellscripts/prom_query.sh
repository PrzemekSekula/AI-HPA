#!/bin/bash
kubectl exec  `kubectl get pods | grep metrics-agent  | head -1 |  cut -f1 -d " "` -- sh -c "curl -s 'prometheus.default.svc.cluster.local:9090/api/v1/query?query=$1'"
