# GKE Autoscaler combined with taints and node anti affinity.

## Getting started

This example creates a GKE cluster with two tainted node pools, so some specific load can be located in a dedicated pool.

[Taints and tolerations](https://kubernetes.io/docs/concepts/configuration/taint-and-toleration/) will be combined with [pod anti affinity](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#affinity-and-anti-affinity) to have a single pod per node, this is to have the ability to increase the replicas at any random time.

Autoscaler combined with taints and node anti affinity is used to accomplish this.

A daemon set is not useful in this case at this will only guarantee to place a pod only when more nodes are added.


### Prerequisites

A GCP account with billing enabled to create a GKE cluster. 

Since we'll be using the gcloud command tool, you will need to have the [cloud SDK](https://cloud.google.com/sdk/docs/) installed and kubectl tool in your local computer or you can use the [Cloud Shell]( https://cloud.google.com/shell/docs/starting-cloud-shell#starting_a_new_session) which has both tools alredy installed.

### Creating the cluster
```
 gcloud beta container --project "<your project>" clusters create "gke-cluster" --zone "us-central1-a" --node-taints pool=default:NoSchedule \
--num-nodes "2" --enable-autoscaling --min-nodes "1" --max-nodes "3"
```

### Add the second nood pool with taints to cluster

```
gcloud beta container --project "<your project>" node-pools create "pool-1" --cluster "gke-cluster" --zone "us-central1-a" \
--node-taints pool=pool1:NoSchedule --num-nodes "1" --enable-autoscaling --min-nodes "1" --max-nodes "3"
```

## Verify the nodes created in the cluster

```
kubectl get nodes
```

### The output of the command
```
NAME                                         STATUS   ROLES    AGE   VERSION
gke-gke-cluster-default-pool-fbe884a6-p3hk   Ready    <none>   3m    v1.11.7-gke.4
gke-gke-cluster-default-pool-fbe884a6-r4pc   Ready    <none>   3m    v1.11.7-gke.4
gke-gke-cluster-pool-1-d2e3b13f-b8r8         Ready    <none>   1m    v1.11.7-gke.4
```

## Create the deployment
```
kubectl create -f echoheaders-taint.yaml 
```

### Verify the deployment is created
```
kubectl get deployment
NAME                  DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
echoheaders-tainted   1         1         1            1           3m
```

### Verify the pods and and where they were create
```
kubectl get pods -o wide
```

The result shows the pod being added in the pool1
```
NAME                                  READY   STATUS    RESTARTS   AGE   IP          NODE                                   NOMINATED NODE
echoheaders-tainted-c8764f79b-fncfk   1/1     Running   0          13h   10.28.2.4   gke-gke-cluster-pool-1-d2e3b13f-b8r8   <none>
```

### Add more pods to the deployment
```
kubectl edit deployment echoheaders-tainted
```

Edit the deployment to add more replicas, modify the line 'replicas: 1' to  'replicas: 3'

### Verify the pods again
```
kubectl get pods -o wide
NAME                                  READY   STATUS    RESTARTS   AGE   IP          NODE                                   NOMINATED NODE
echoheaders-tainted-c8764f79b-bglvx   1/1     Running   0          3m    10.28.4.2   gke-gke-cluster-pool-1-d2e3b13f-8crg   <none>
echoheaders-tainted-c8764f79b-fncfk   1/1     Running   0          13h   10.28.2.4   gke-gke-cluster-pool-1-d2e3b13f-b8r8   <none>
echoheaders-tainted-c8764f79b-krd8f   1/1     Running   0          3m    10.28.3.2   gke-gke-cluster-pool-1-d2e3b13f-dwzj   <none>
```

New nodes has been added to the cluster and each pod got created in a different node.
