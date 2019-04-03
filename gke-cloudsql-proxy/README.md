# Connect from GKE to CloudSQL private IP via CloudSQL proxy

Connection to a CloudSQL instance, with private IP, from an application runing in GKE using the Cloud SQL proxy.

## Getting Started

This instructions will help you create a CloudSQL instance with only private IP and a GKE cluster to run an application running on GKE that will be able to
connect to the CloudSLQ instance using that private IP. Some configuation YAML files were taken from the [Github GKE examples listed in here](https://github.com/GoogleCloudPlatform/kubernetes-engine-samples/tree/master/cloudsql).  

### Prerequisites

A Google Cloud Platform project with billing enabled.

A second generation CloudSQL instance with private IP. 

A GKE cluster version 1.8 or higher on a [VPC native](https://cloud.google.com/kubernetes-engine/docs/how-to/alias-ips) GCE network. For the GKE cluster is recommended to enable alias IP, but in this example it will be disabled.

Note that the GKE cluster and the CloudSQL instnaces should be located in the same subnet in the VPC Native network.

Since we'll be using the gcloud command tool, you will need to have the [cloud SDK](https://cloud.google.com/sdk/docs/) installed and kubectl tool in your local computer or you can use the [Cloud Shell]( https://cloud.google.com/shell/docs/starting-cloud-shell#starting_a_new_session) which has both tools alredy installed.

##Creating the GKE cluster

```
gcloud beta container --project "<your project>" clusters create "cloudsql-gke-cluster" --zone "us-central1-a" --num-nodes "2" \
--no-enable-ip-alias --network "projects/<your project>/global/networks/shared-network" \
--subnetwork "projects/<your project>/regions/us-central1/subnetworks/shared-network"
```

The output should look like
```
NAME                  LOCATION       MASTER_VERSION  MASTER_IP      MACHINE_TYPE   NODE_VERSION   NUM_NODES  STATUS
cloudsql-gke-cluster  us-central1-a  1.11.7-gke.12   35.193.167.63  n1-standard-1  1.11.7-gke.12  2          RUNNING
```

## Creating the CloudSQL instance with private IP

A faster way to create the CloudSQL instance will be using the Cloud Console as described in [here](https://cloud.google.com/sql/docs/mysql/configure-private-ip#configuring_an_instance_to_use_private_ip_at_creation_time)

Using the gcloud commands, you need to [allocate an IP address range to be used by the service producer's VPC network)](https://cloud.google.com/vpc/docs/configure-private-services-access#allocating-range),


### Allocating an IP address range
```
gcloud compute addresses create google-managed-services-shared-network \
--global \
--purpose=VPC_PEERING \
--prefix-length=16 \
--description="peering range for Google" \
--network=shared-network \
--project=<your-project>
```

### Creating a private connection to a service producer.
```
gcloud beta services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges=google-managed-services-shared-network \
    --network=shared-network \
    --project=<your-project>
```

### Creating the CloudSQL private instance

```
gcloud beta sql instances create sql-private --network=projects/<your-project>/global/networks/shared-network --no-assign-ip --zone us-central1-a
```

```
Created [https://www.googleapis.com/sql/v1beta4/projects/<your-project>/instances/sql-private].
NAME         DATABASE_VERSION  LOCATION       TIER              PRIMARY_ADDRESS  PRIVATE_ADDRESS  STATUS
sql-private  MYSQL_5_7         us-central1-a  db-n1-standard-1  -                10.109.0.3       RUNNABLE
```

In the Cloud Console, set the password for the user.


## Connecting from GKE using the Cloud SQL proxy

To connect to the Postgres DB using private a IP, the [Cloud SQL proxy](https://cloud.google.com/sql/docs/mysql/connect-kubernetes-engine) is used.

### Create the [Service Account](https://cloud.google.com/docs/authentication/getting-started) with the proper IAM roles and they json key.
```
gcloud iam service-accounts create postgres-sql --display-name postgres-sql
```

```
Created service account [postgres-sql].
```

List the service accounts in the project

```
gcloud iam service-accounts list
NAME                                    EMAIL                                                  DISABLED
postgres-sql                            postgres-sql@<your-project>.iam.gserviceaccount.com  False
```

### Add the IAM permission to the SA
```
  gcloud projects add-iam-policy-binding <your-project> --member "serviceAccount:postgres-sql@<your-project>.iam.gserviceaccount.com" --role "roles/cloudsql.editor"
```

### Create the json key for the SA
```
gcloud iam service-accounts keys create sa-key-postgres.json --iam-account postgres-sql@<your-project>.iam.gserviceaccount.com
```

```
created key [d024f44ed92xxxxxxxxxxxxxxxxxx9ba5da3c81] of type [json] as [sa-key-postgres.json] for [postgres-sql@<your-project>.iam.gserviceaccount.com]
```

The command above create a file as 'sa-key-postgres.json' which has been deleted from this directory after using it for createing the secrets.


### Creating the secrets
For the SA
```
kubectl create secret generic cloudsql-instance-credentials --from-file=credentials.json=sa-key-postgres.json 
```
```
secret/cloudsql-instance-credentials created
```

For the DB user
```
kubectl create -f user-sql-credentials.yaml 
```
```
secret/cloudsql-db-credentials created
```

### Create the deployment with the app and the cloudSQL proxy container, file used is from this [GKE repository](https://github.com/GoogleCloudPlatform/kubernetes-engine-samples/blob/master/cloudsql/postgres_deployment.yaml)
```
kubectl create -f postgres_deployment.yaml 
```
```
deployment.apps/myapp created
```

Verify the pods are running
```
kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
myapp-797448b78b-92msw   2/2     Running   0          4m
```

### Modifying node's IPtables
For this setup, you need to have a VPC native GKE cluster with alias enabled, in the case the GKE cluster was created without IP tables, pods will not be able to communicate with the CloudSQL.
To make this work, the node's IPtables should be modified. The [IP masquerade agent](https://cloud.google.com/kubernetes-engine/docs/how-to/ip-masquerade-agent) is one possibility. IF this doesn't apply, then a daemonset with an startup script can be used.
```
kubectl create -f iptables-daemon.yaml
```

