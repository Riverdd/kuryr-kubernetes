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


LOG = logging.getLogger(__name__)


class AutoSchedulerPodSubnetDriver(base.PodSubnetsDriver):
    """Provides subnet for Pod port auto scheduler by driver."""

    def get_subnets(self, pod, project_id):
        pod_namespace = pod['metadata']['namespace']
        return self.get_namespace_subnets(pod_namespace)

    def get_namespace_subnets(self, namespace, subnet_id_list=None):
        if not subnet_id_list:
            subnet_id_list = self._get_namespace_subnet_ids(namespace)
        subnet_list = []
        for subnet_id in subnet_id_list:
            subnet_id_dict = {subnet_id: utils.get_subnet(subnet_id)}
            subnet_list.append(subnet_id_dict)
        return subnet_list

    def _get_namespace_subnet_ids(self, namespace):
        kubernetes = clients.get_kubernetes_client()
        try:
            net_crds_path = (f"{constants.K8S_API_CRD_NAMESPACES}/"
                            f"{namespace}/kuryrnetworks")
            net_crds = kubernetes.get(net_crds_path)
        except exceptions.K8sClientException:
            LOG.exception("Kubernetes Client Exception.")
            raise

        subnet_id_list = []
        for crd in net_crds['items']:
            kuryrnetwork_name = crd['metadata']['name']
            net_crd_path = (f"{constants.K8S_API_CRD_NAMESPACES}/"
                            f"{namespace}/kuryrnetworks/{kuryrnetwork_name}")
            net_crd = kubernetes.get(net_crd_path)
            subnet_id_list.append(net_crd['status']['subnetId'])

        return subnet_id_list
