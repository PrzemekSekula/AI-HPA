#!/bin/bash

kubectl exec  `kubectl get pods | grep metrics-agent  | head -1 |  cut -f1 -d " "` -- sh -c "curl -s 'localhost:8080/metrics'"
