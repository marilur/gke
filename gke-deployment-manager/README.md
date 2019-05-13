# Deployment manager for GKE clusters as a code using Deployment Manager

Thoses examples are using Python and it's based on [this posting](https://medium.com/google-cloud/cloud-deployment-manager-kubernetes-2dd9b8124223).

And this other [Deployment manger posting](https://github.com/GoogleCloudPlatform/deploymentmanager-samples/blob/master/examples/v2/gke/python/cluster.py) as well but instead of using the type container.v1.cluster, it uses the gcp-types/container-v1beta1:projects.locations.clusters for DM type providers.

[gke-cluster-single-pool](https://github.com/marilur/gke/tree/master/gke-deployment-manager/gke-cluster-single-pool) create a GKE cluster with a single node pool. 

[gke-cluster-two-pools](https://github.com/marilur/gke/tree/master/gke-deployment-manager/gke-cluster-two-pools) create a GKE cluster with two node pools.
