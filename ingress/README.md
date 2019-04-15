# Ingress examples

Some ingress configuration files using the [GLBC ingress controller](https://github.com/kubernetes/ingress-gce)on GKE.

This example will configure an HTTPs load balance using an k8s ingress fanout to direct traffic to different instances based on the incoming URL, in this case for foo.bar.com and bar baz.com.

## Generating the self-signed certificates and the k8s secrets.

### Self-signed certificates

Generate self signed certificates for the URL terminatios for foo.bar.com and bar baz.com using openSSL.

```
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout bar-baz-com.key -out bar-baz-com.crt -subj "/CN=$bar.baz.com/O=bar.baz.com"
```

```
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout foo-bar-com.key -out foo-bar-com.crt -subj "/CN=$foo.bar.com/O=foo.bar.com"
```

### K8s secrets

Generate the two YAML files to be used for creating the k8s secrets. 

```
cat <<EOF >> bar-baz-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: barbaz
  namespace: default
data:
  tls.crt: "$(cat bar-baz-com.crt | base64 -w 0)"
  tls.key: "$(cat bar-baz-com.key | base64 -w 0)"
EOF
```

```
cat <<EOF >> foo-bar-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: foobar
  namespace: default
data:
  tls.crt: "$(cat foo-bar-com.crt | base64 -w 0)"
  tls.key: "$(cat foo-bar-com.key | base64 -w 0)"
EOF
```

Creating the k8s secrets to store the SSL certificates that will be used in the ingress resource.

```
kubectl create -f ssl_cert/bar-baz-secret.yaml 
```

```
kubectl create -f ssl_cert/foo-bar-secret.yaml
```

## Configuring the GKE HTTPs LB using the ingress resource.

The YAML file contains the configuration for the two K8s Deployments and service for each URL. 
The source file for the ingress is from [this Github link](https://github.com/kubernetes/contrib/blob/master/ingress/controllers/nginx/examples/multi-tls/multi-tls.yaml)

```
kubectl create -f multi-tls.yaml 
```

```
service/nginx created
deployment.apps/nginx-deployment created
service/echoheaders created
deployment.apps/echoheaders-deployment created
ingress.extensions/foo-tls created
```

Describing the ingress

```
kubectl describe ingress foo-tls
Name:             foo-tls
Namespace:        default
Address:          35.241.31.98
Default backend:  default-http-backend:80 (10.16.0.6:8080)
TLS:
  foobar terminates foo.bar.com
  barbaz terminates bar.baz.com
Rules:
  Host         Path  Backends
  ----         ----  --------
  foo.bar.com  
               /   echoheaders:80 (10.16.1.10:8080)
  bar.baz.com  
               /   nginx:80 (10.16.1.9:80)
Annotations:
  ingress.kubernetes.io/static-ip:              k8s-fw-default-foo-tls--a6f8f5f8036c286a
  ingress.kubernetes.io/target-proxy:           k8s-tp-default-foo-tls--a6f8f5f8036c286a
  ingress.kubernetes.io/url-map:                k8s-um-default-foo-tls--a6f8f5f8036c286a
  ingress.kubernetes.io/backends:               {"k8s-be-30119--a6f8f5f8036c286a":"HEALTHY","k8s-be-30191--a6f8f5f8036c286a":"HEALTHY","k8s-be-30765--a6f8f5f8036c286a":"HEALTHY"}
  ingress.kubernetes.io/forwarding-rule:        k8s-fw-default-foo-tls--a6f8f5f8036c286a
  ingress.kubernetes.io/https-forwarding-rule:  k8s-fws-default-foo-tls--a6f8f5f8036c286a
  ingress.kubernetes.io/https-target-proxy:     k8s-tps-default-foo-tls--a6f8f5f8036c286a
  ingress.kubernetes.io/ssl-cert:               k8s-ssl-3edb887c33713e47-517d158a08cd7cbb--a6f8f5f8036c286a,k8s-ssl-3edb887c33713e47-62457702ff4a882c--a6f8f5f8036c286a
Events:                                         <none 
```

## Testing the LB

For foo.bar.com

```
curl -k https://35.241.31.98 -H 'Host:foo.bar.com'
CLIENT VALUES:
client_address=10.128.0.41
command=GET
real path=/
query=nil
request_version=1.1
request_uri=http://foo.bar.com:8080/

SERVER VALUES:
server_version=nginx: 1.10.0 - lua: 10001

HEADERS RECEIVED:
accept=*/*
connection=Keep-Alive
host=foo.bar.com
user-agent=curl/7.52.1
via=1.1 google
x-cloud-trace-context=23db970662190ae3ba62c87451acd049/13668602683723240582
x-forwarded-for=35.232.244.128, 35.241.31.98
x-forwarded-proto=https
BODY:
-no body in request-
```

For bar.baz.com
```
curl -k https://35.241.31.98 -H 'Host:bar.baz.com'
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx on Debian!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>Welcome to nginx on Debian!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working on Debian. Further configuration is required.</p>

<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a></p>

<p>
      Please use the <tt>reportbug</tt> tool to report bugs in the
      nginx package with Debian. However, check <a
      href="http://bugs.debian.org/cgi-bin/pkgreport.cgi?ordering=normal;archive=0;src=nginx;repeatmerged=0">existing
      bug reports</a> before reporting a new bug.
</p>

<p><em>Thank you for using debian and nginx.</em></p>


</body>
</html>
```

The GKE default backend is used for matching any other invalid URL:

```
curl -k https://35.241.31.98
default backend - 404
``` 
