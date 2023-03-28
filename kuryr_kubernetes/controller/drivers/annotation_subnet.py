# Copyright 2018 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from kuryr.lib._i18n import _
from oslo_log import log as logging

from kuryr_kubernetes import clients
from kuryr_kubernetes import constants
from kuryr_kubernetes.controller.drivers import base
from kuryr_kubernetes import exceptions
from kuryr_kubernetes import utils

import json

LOG = logging.getLogger(__name__)


class AnnotationPodSubnetDriver(base.PodSubnetsDriver):
    """Provides subnet for Pod port based on a Pod's annotation."""

    def get_subnets(self, pod, project_id):
        pod_namespace = pod['metadata']['namespace']
        pod_annotations = pod['metadata'].get('annotations')
        subnet_annotation = pod_annotations.get('csk.pod.kuryrnetwork/name')
        fixedip = pod_annotations.get('csk.pod.kuryrport/fixedip')

        return self.get_annotation_subnet(pod_namespace, subnet_annotation, fixedip)

    def get_annotation_subnet(self, namespace, subnet_annotation, fixedip, subnet_id=None):
        if not subnet_id:
            subnet_id = self._get_annotation_subnet_id(namespace, subnet_annotation)
        return {subnet_id: utils.get_subnet(subnet_id, fixedip)}

    def _get_annotation_subnet_id(self, namespace, subnet_annotation):
        kubernetes = clients.get_kubernetes_client()
        try:
            net_crd_path = (f"{constants.K8S_API_CRD_NAMESPACES}/"
                            f"{namespace}/kuryrnetworks/{subnet_annotation}")
            net_crd = kubernetes.get(net_crd_path)
        except exceptions.K8sResourceNotFound:
            LOG.debug("Kuryrnetwork resource not yet created, retrying...")
            raise exceptions.ResourceNotReady(subnet_annotation)
        except exceptions.K8sClientException:
            LOG.exception("Kubernetes Client Exception.")
            raise

        try:
            subnet_id = net_crd['status']['subnetId']
        except KeyError:
            LOG.debug("Subnet %(subnet_name)s for namespace %(ns)s not yet created, retrying.",
                      {'subnet_name': subnet_annotation, 'ns': namespace})
            raise exceptions.ResourceNotReady(subnet_annotation)
        return subnet_id
