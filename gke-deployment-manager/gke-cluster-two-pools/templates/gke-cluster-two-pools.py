# This example was generated from this post:
# https://medium.com/google-cloud/cloud-deployment-manager-kubernetes-2dd9b8124223

def GenerateConfig(context):
  """Generate YAML resource configuration."""

  cluster_region = context.properties['cluster_region']
  #number of nodes for default pool
  number_of_nodes = context.properties['default_pool_num_nodes']
  name_prefix = context.env['deployment'] + '-' + context.env['name']
  cluster_name = name_prefix
  #number of nodes for pool_1
  pool_1_name = context.properties['name_pool_1']
  number_of_nodes_pool_1 = context.properties['pool_1_initialNodeCount']
  type_name = name_prefix + '-type'
  k8s_endpoints = {
      '': 'api/v1',
      '-apps': 'apis/apps/v1beta1',
      '-v1beta1-extensions': 'apis/extensions/v1beta1'
  }


  resources = []
  outputs = []

  resources.append({
      'name': cluster_name,
      'type': 'gcp-types/container-v1beta1:projects.locations.clusters',
      'properties': {
          'parent': 'projects/{}/locations/{}'.format(context.env['project'], cluster_region),
          'cluster': {
              'name': cluster_name,
              'nodePools': [{
                  'name': 'core',
                  'initialNodeCount': number_of_nodes,
                  'config': {
                      'imageType': 'COS',
                      'preemptible': True,
                      'oauthScopes': [
                          'https://www.googleapis.com/auth/' + scope
                          for scope in [
                              'compute',
                              'devstorage.read_only',
                              'logging.write',
                              'monitoring'
                          ]
                      ]
                  },
                  'autoscaling': {
                      'enabled': False
                  },
				  'management': {
                      'autoUpgrade': True,
                      'autoRepair': True,
                      'upgradeOptions': {}
                  }
              }]
          } # cluster
      }
  }) #resouces.append

  resources.append({
    'name': pool_1_name,
    'type': 'gcp-types/container-v1beta1:projects.locations.clusters.nodePools',
    'properties': {
        'parent': 'projects/' + context.env['project'] + '/locations/' + cluster_region + '/clusters/' + cluster_name,
        'nodePool': {
          'name': context.properties['name_pool_1'],
	  'config': {
	  'imageType': 'COS',
	  'preemptible': True,
	  'oauthScopes': [
        	  'https://www.googleapis.com/auth/' + scope
		   for scope in [
			  'compute',
			   'devstorage.read_only',
			   'logging.write',
			   'monitoring'
		   ]
	  ] #oauthScopes
	  }, #config
          'initialNodeCount': number_of_nodes_pool_1
        } #nodePool
    }, #properties
    'metadata': {
        'dependsOn': [cluster_name]
    }
  }) #pool1

  for type_suffix, endpoint in k8s_endpoints.iteritems():
    resources.append({
        'name': type_name + type_suffix,
        'type': 'deploymentmanager.v2beta.typeProvider',
        'properties': {
            'options': {
                'validationOptions': {
                    # Kubernetes API accepts ints, in fields they annotate
                    # with string. This validation will show as warning
                    # rather than failure for Deployment Manager.
                    # https://github.com/kubernetes/kubernetes/issues/2971
                    'schemaValidation': 'IGNORE_WITH_WARNINGS'
                },
                # According to kubernetes spec, the path parameter 'name'
                # should be the value inside the metadata field
                # https://github.com/kubernetes/community/blob/master
                # /contributors/devel/api-conventions.md
                # This mapping specifies that
                'inputMappings': [{
                    'fieldName': 'name',
                    'location': 'PATH',
                    'methodMatch': '^(GET|DELETE|PUT)$',
                    'value': '$.ifNull('
                             '$.resource.properties.metadata.name, '
                             '$.resource.name)'
                }, {
                    'fieldName': 'metadata.name',
                    'location': 'BODY',
                    'methodMatch': '^(PUT|POST)$',
                    'value': '$.ifNull('
                             '$.resource.properties.metadata.name, '
                             '$.resource.name)'
                }, {
                    'fieldName': 'Authorization',
                    'location': 'HEADER',
                    'value': '$.concat("Bearer ",'
                             '$.googleOauth2AccessToken())'
                }]
            },
            'descriptorUrl':
                ''.join([
                    'https://$(ref.', cluster_name, '.endpoint)/swaggerapi/',
                    endpoint
                ])
        }
    })
    outputs.append({
        'name': 'clusterType' + type_suffix,
        'value': type_name + type_suffix
    })

  return {'resources': resources, 'outputs': outputs}
