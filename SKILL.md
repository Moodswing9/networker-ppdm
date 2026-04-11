---
name: networker-ppdm
description: Expert guidance for Dell EMC NetWorker and PowerProtect Data Manager (PPDM) — backup/restore operations, Kubernetes protection, policy config, REST API, CLI commands, troubleshooting, and automation.
---

# NetWorker & PowerProtect Data Manager (PPDM)

You are an expert in Dell EMC **NetWorker** and **PowerProtect Data Manager (PPDM)**. When this skill is active, assist with all aspects of backup administration, Kubernetes namespace protection, automation, REST API usage, CLI operations, troubleshooting, and best practices.

---

## When to Use

- Configuring or managing NetWorker servers, storage nodes, clients, and devices
- Protecting Kubernetes namespaces, PVCs, and cluster resources with PPDM
- Working with PPDM policies, protection rules, assets, and schedules
- Writing scripts against the NetWorker REST API or PPDM REST API
- Diagnosing backup/restore failures, performance issues, or license problems
- Automating tasks with `nsradmin`, `mminfo`, `nsrinfo`, `savegrp`, or REST
- Migrating from NetWorker to PPDM or integrating both products

---

## NetWorker

### Key Concepts

| Term | Description |
|---|---|
| **Server** | Central NW server managing all backup operations |
| **Storage Node** | Host with direct device access; moves backup data |
| **Client** | Host being backed up |
| **Device** | Backup target — tape, AFTD (disk), CloudBoost, DD |
| **Pool** | Logical grouping of volumes; maps data to devices |
| **Group** | Schedule + client list; triggers savesets |
| **Saveset** | A single backup instance of a client/save path |
| **Browse/Retention** | Browse: recover window. Retention: media expiry |
| **NSR** | Namespace prefix for all NetWorker resource types |

### Core CLI Commands

```bash
# Server / daemon status
nsrwatch                          # real-time activity monitor
nsradmin -s <server>              # interactive admin shell
nsradmin -p nsrla                 # local agent admin

# Backup
savegrp -G <group>                # manually run a group
save -s <server> -N <name> /path  # manual client-side save

# Query savesets
mminfo -s <server> -q "client=<host>" -r "ssid,name,level,savetime,sumsize"
mminfo -s <server> -q "savetime>last week" -r "client,name,level,savetime(22),sumsize"
nsrinfo -s <server> -c <client> /path   # browse saveset contents

# Recover
recover -s <server> -c <client> -t <date>   # interactive recover
nsrrecover -s <server> -c <client> /path    # scripted recover

# Device / media
nsrjb -s <server> -I              # inventory jukebox
nsrmm -s <server> -d <volume>     # delete/expire volume
nsrmm -s <server> -e <date> <vol> # set expiry date

# Logs
nsr_render_log /nsr/logs/daemon.raw   # render raw daemon log
tail -f /nsr/logs/daemon.log          # follow live log (Linux)
```

### nsradmin Quick Reference

```
nsradmin> print type: NSR client; name: <hostname>   # show client resource
nsradmin> print type: NSR group; name: <group>       # show group
nsradmin> update type: NSR client; name: <host>; \
          backup enabled: No;                        # disable client
nsradmin> create type: NSR label template; ...       # create resource
nsradmin> delete type: NSR client; name: <host>      # delete resource
```

### NetWorker REST API

Base URL: `https://<nwserver>:9090/nwrestapi/v3`

```bash
# Auth
curl -k -u admin:<pass> https://<server>:9090/nwrestapi/v3/global/clients

# List clients
GET /global/clients

# Get savesets for a client
GET /global/savesets?q=clientId:<id>

# Start a backup
POST /global/protectiongroups/<id>/op/backup

# Start a recover
POST /global/recovers
Content-Type: application/json
{
  "sourceClient": "<client>",
  "destinationClient": "<client>",
  "saveSets": ["<ssid>"]
}
```

### Common Troubleshooting

| Problem | Where to look / what to run |
|---|---|
| Backup failed | `nsr_render_log /nsr/logs/daemon.raw` — search for client name |
| "no space left on device" | `mminfo -mv` — check volume utilization; add capacity |
| Client not resolving | Check `/etc/hosts`, DNS, `nsrauth` / `nsrexecd` on client |
| Media waiting | `nsrwatch` — look for "waiting for media"; check device/pool mapping |
| License exceeded | `nsrlic -s <server>` — list current license consumption |
| Stale lockbox | `nsrpolicy` / re-auth client with `nsraddadmin` |

---

## PowerProtect Data Manager (PPDM)

### Key Concepts

| Term | Description |
|---|---|
| **Protection Policy** | Defines what, when, where, and how long to back up |
| **Asset** | Any backup target — VM, DB, filesystem, k8s namespace |
| **Protection Rule** | Auto-assigns assets to policies based on criteria |
| **SLA** | Service Level Agreement — compliance window for RPO |
| **Storage Unit** | Target storage — DD (Data Domain), cloud, etc. |
| **Activity** | A single backup or restore job instance |
| **Agent** | Software on the protected host (TSDM, App Agent) |

### PPDM REST API

Base URL: `https://<ppdm>:8443/api/v2`

```bash
# Authenticate — get Bearer token
POST /login
{
  "username": "admin",
  "password": "<pass>"
}
# Returns: { "access_token": "..." }

# Use token in subsequent requests
-H "Authorization: Bearer <token>"
```

```bash
# Assets
GET  /assets                          # list all assets
GET  /assets?filter=name%20eq%20%22<name>%22   # filter by name
GET  /assets/<id>                     # single asset detail

# Protection policies
GET  /protection-policies             # list policies
POST /protection-policies             # create policy
GET  /protection-policies/<id>        # policy detail

# Activities (jobs)
GET  /activities                      # list recent activities
GET  /activities?filter=state%20eq%20%22FAILED%22   # failed jobs
GET  /activities/<id>                 # single activity detail

# Restore
POST /restores                        # initiate a restore

# Storage systems
GET  /storage-systems                 # list connected DD/cloud storage

# Agents / inventory sources
GET  /inventory-sources               # vCenters, app hosts, k8s clusters
```

### Python Snippet — PPDM Auth + List Failed Jobs

```python
import requests, json
requests.packages.urllib3.disable_warnings()

BASE = "https://<ppdm>:8443/api/v2"

def get_token(user, password):
    r = requests.post(f"{BASE}/login",
                      json={"username": user, "password": password},
                      verify=False)
    r.raise_for_status()
    return r.json()["access_token"]

def get_failed_activities(token):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"filter": 'state eq "FAILED"', "pageSize": 100}
    r = requests.get(f"{BASE}/activities", headers=headers,
                     params=params, verify=False)
    r.raise_for_status()
    return r.json().get("content", [])

token = get_token("admin", "Password123!")
for job in get_failed_activities(token):
    print(job["id"], job["name"], job["startTime"])
```

### PowerShell Snippet — PPDM Backup on Demand

```powershell
$base = "https://<ppdm>:8443/api/v2"
$creds = @{ username = "admin"; password = "Password123!" } | ConvertTo-Json

$token = (Invoke-RestMethod "$base/login" -Method POST `
          -Body $creds -ContentType "application/json" `
          -SkipCertificateCheck).access_token

$headers = @{ Authorization = "Bearer $token" }

# Trigger on-demand backup for a policy
Invoke-RestMethod "$base/protection-policies/<policyId>/protections" `
  -Method POST -Headers $headers -ContentType "application/json" `
  -Body '{}' -SkipCertificateCheck
```

### Common Troubleshooting

| Problem | Action |
|---|---|
| Agent not connecting | Check port 7000/7001 open; re-register agent from PPDM UI |
| Activity stuck "RUNNING" | `GET /activities/<id>` — check sub-task states; may need to cancel |
| Compliance SLA breach | Review policy schedule vs. RPO; check storage capacity |
| DD storage full | `GET /storage-systems/<id>` — check usedSize vs. size; expand or add DD |
| vCenter assets not discovered | Refresh inventory source: `POST /inventory-sources/<id>/discover` |
| Restore fails "no copy" | Verify retention not expired: `GET /assets/<id>/copies` |

---

## Kubernetes Protection with PPDM

PPDM provides native, agentless Kubernetes protection using a **Container Data Integrator (CDI)** deployed inside the cluster. It captures namespace-scoped backups including PersistentVolumeClaims (PVCs), Kubernetes object metadata, and application configurations — with full crash-consistent or application-consistent recovery.

---

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                 │
│                                                     │
│  ┌─────────────┐    ┌──────────────────────────┐   │
│  │  Namespace  │    │  Container Data           │   │
│  │  (Assets)   │◄───│  Integrator (CDI Pod)     │   │
│  │  PVCs / YAML│    │  Deployed by PPDM         │   │
│  └─────────────┘    └────────────┬─────────────┘   │
│                                  │ VolumeSnapshot    │
│                                  ▼                  │
│                     CSI Driver (snapshot-capable)   │
└──────────────────────────────────┬─────────────────┘
                                   │
                          ┌────────▼────────┐
                          │   PPDM Server   │
                          │  (Orchestrator) │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  Data Domain    │
                          │  (Storage Target│
                          └─────────────────┘
```

**Key components:**
- **CDI (Container Data Integrator)** — PPDM-deployed controller pod that orchestrates snapshots and data movement inside the cluster
- **CSI Driver** — Must support `VolumeSnapshot` API (e.g., vSphere CSI, Portworx, NetApp Trident, AWS EBS CSI)
- **PPDM Server** — Manages policy, scheduling, retention, and restore orchestration
- **Data Domain** — Stores deduplicated backup data

---

### Prerequisites

Before registering a Kubernetes cluster with PPDM, confirm all of the following:

| # | Requirement | How to Verify |
|---|---|---|
| 1 | PPDM 19.10+ (19.14+ recommended for full k8s feature set) | PPDM UI → Settings → About |
| 2 | Kubernetes 1.21 or later | `kubectl version --short` |
| 3 | CSI driver installed and healthy | `kubectl get pods -n kube-system \| grep csi` |
| 4 | VolumeSnapshotClass configured and set as default | `kubectl get volumesnapshotclass` |
| 5 | `VolumeSnapshot` CRDs installed | `kubectl get crd \| grep snapshot` |
| 6 | PPDM can reach the cluster API server (port 6443) | `curl -k https://<k8s-api>:6443/healthz` |
| 7 | Data Domain reachable from PPDM and CDI pods | `ping` / `nc -zv <dd-host> 2052` |
| 8 | Sufficient RBAC — PPDM needs a ServiceAccount with cluster-admin or scoped permissions | `kubectl auth can-i list namespaces --as=system:serviceaccount:ppdm:ppdm-sa` |

---

### Step 1 — Install VolumeSnapshot CRDs and Controller

If VolumeSnapshot CRDs are not already present in the cluster, install them from the upstream CSI snapshot repository:

```bash
# Clone the CSI snapshot repo (use the branch matching your k8s version)
git clone https://github.com/kubernetes-csi/external-snapshotter.git
cd external-snapshotter

# Install CRDs
kubectl apply -f client/config/crd/

# Install the common snapshot controller
kubectl apply -f deploy/kubernetes/snapshot-controller/

# Verify
kubectl get crd | grep snapshot
# Expected output:
# volumesnapshotclasses.snapshot.storage.k8s.io
# volumesnapshotcontents.snapshot.storage.k8s.io
# volumesnapshots.snapshot.storage.k8s.io

kubectl get pods -n kube-system | grep snapshot-controller
# Expected: snapshot-controller-* Running
```

---

### Step 2 — Create a VolumeSnapshotClass

Create a `VolumeSnapshotClass` that matches your CSI driver. The annotation `snapshot.storage.kubernetes.io/is-default-class: "true"` tells PPDM which class to use automatically.

```yaml
# volumesnapshotclass.yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ppdm-snapclass
  annotations:
    snapshot.storage.kubernetes.io/is-default-class: "true"
deletionPolicy: Delete
driver: csi.vsphere.volume   # Replace with your CSI driver name
                              # Examples:
                              # ebs.csi.aws.com          (AWS EBS)
                              # disk.csi.azure.com        (Azure Disk)
                              # pd.csi.storage.gke.io     (GKE PD)
                              # csi.trident.netapp.io     (NetApp Trident)
```

```bash
kubectl apply -f volumesnapshotclass.yaml

# Verify
kubectl get volumesnapshotclass
```

---

### Step 3 — Create PPDM ServiceAccount and RBAC

PPDM requires a Kubernetes ServiceAccount with sufficient permissions to deploy the CDI, create snapshots, and manage namespaces.

```yaml
# ppdm-rbac.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: powerprotect
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: powerprotect-admin
  namespace: powerprotect
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: powerprotect-admin-binding
subjects:
  - kind: ServiceAccount
    name: powerprotect-admin
    namespace: powerprotect
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
---
# Generate a long-lived token (k8s 1.24+)
apiVersion: v1
kind: Secret
metadata:
  name: powerprotect-admin-token
  namespace: powerprotect
  annotations:
    kubernetes.io/service-account.name: powerprotect-admin
type: kubernetes.io/service-account-token
```

```bash
kubectl apply -f ppdm-rbac.yaml

# Extract the token — you will need this in Step 4
kubectl get secret powerprotect-admin-token \
  -n powerprotect \
  -o jsonpath='{.data.token}' | base64 --decode
```

---

### Step 4 — Register the Kubernetes Cluster in PPDM

**Via PPDM UI:**

1. Navigate to **Infrastructure → Asset Sources**
2. Click **+ Add** → select **Kubernetes**
3. Fill in the registration form:

| Field | Value |
|---|---|
| **Name** | A friendly label for the cluster |
| **Address** | Kubernetes API server hostname or IP |
| **Port** | `6443` (default) |
| **CA Certificate** | Paste the cluster CA cert (from kubeconfig) |
| **Token** | The ServiceAccount token from Step 3 |

4. Click **Verify** — PPDM will test connectivity and deploy the CDI
5. Click **Save**

**Via PPDM REST API:**

```bash
# Authenticate first
TOKEN=$(curl -sk -X POST https://<ppdm>:8443/api/v2/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<pass>"}' \
  | jq -r '.access_token')

# Get the cluster CA cert (base64-encoded, from kubeconfig)
K8S_CA=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')

# Get the ServiceAccount token
K8S_TOKEN=$(kubectl get secret powerprotect-admin-token \
  -n powerprotect -o jsonpath='{.data.token}' | base64 --decode)

# Register the cluster
curl -sk -X POST https://<ppdm>:8443/api/v2/inventory-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"KUBERNETES\",
    \"name\": \"prod-k8s-cluster\",
    \"address\": \"<k8s-api-server>\",
    \"port\": 6443,
    \"credentials\": {
      \"type\": \"TOKEN\",
      \"token\": \"$K8S_TOKEN\"
    },
    \"details\": {
      \"k8s\": {
        \"caCertificate\": \"$K8S_CA\"
      }
    }
  }" | jq .
```

---

### Step 5 — Discover Kubernetes Assets

After registration, trigger a discovery to populate namespaces and PVCs as protectable assets:

```bash
# Get the inventory source ID
INV_ID=$(curl -sk https://<ppdm>:8443/api/v2/inventory-sources \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.content[] | select(.name=="prod-k8s-cluster") | .id')

# Trigger discovery
curl -sk -X POST \
  https://<ppdm>:8443/api/v2/inventory-sources/$INV_ID/discover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

# Poll until discovery completes
curl -sk "https://<ppdm>:8443/api/v2/inventory-sources/$INV_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{name: .name, lastDiscovery: .details.k8s.lastDiscoveryTime}'

# List discovered namespace assets
curl -sk "https://<ppdm>:8443/api/v2/assets?filter=type%20eq%20%22K8S_NAMESPACE%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, clusterName: .details.k8s.inventorySourceName}'
```

---

### Step 6 — Create a Kubernetes Protection Policy

A protection policy defines the backup schedule, retention, and target storage for Kubernetes namespaces.

**Via PPDM UI:**

1. Navigate to **Protection → Protection Policies**
2. Click **+ Add**
3. Select type **Kubernetes**
4. Configure:

| Field | Recommended Value |
|---|---|
| **Name** | `k8s-daily-policy` |
| **Asset Type** | Kubernetes |
| **Backup Schedule** | Daily at 02:00 |
| **Retention** | 30 days |
| **Storage Target** | Your Data Domain system |
| **Namespace Selection** | Manually select or use Protection Rules |

5. Click **Save**

**Via REST API:**

```bash
# Get the storage system (Data Domain) ID
DD_ID=$(curl -sk https://<ppdm>:8443/api/v2/storage-systems \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.content[0].id')

# Create protection policy
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"k8s-daily-policy\",
    \"assetType\": \"KUBERNETES\",
    \"type\": \"ACTIVE\",
    \"dataConsistency\": \"CRASH_CONSISTENT\",
    \"stages\": [
      {
        \"type\": \"PROTECTION\",
        \"retention\": {
          \"unit\": \"DAY\",
          \"storageSystemRetentionLock\": false,
          \"interval\": 30
        },
        \"target\": {
          \"storageSystemId\": \"$DD_ID\",
          \"dataTargetWithDdBoost\": true
        },
        \"operations\": [
          {
            \"type\": \"AUTO_FULL\",
            \"schedule\": {
              \"frequency\": \"DAILY\",
              \"startTime\": \"02:00\",
              \"duration\": 10,
              \"durationUnit\": \"HOURS\"
            }
          }
        ]
      }
    ]
  }" | jq '{id, name, assetType}'
```

---

### Step 7 — Assign Namespaces to the Policy

**Manually assign a specific namespace:**

```bash
# Get namespace asset ID
NS_ID=$(curl -sk "https://<ppdm>:8443/api/v2/assets?filter=name%20eq%20%22<namespace>%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.content[0].id')

# Get policy ID
POLICY_ID=$(curl -sk "https://<ppdm>:8443/api/v2/protection-policies?filter=name%20eq%20%22k8s-daily-policy%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.content[0].id')

# Assign asset to policy
curl -sk -X POST \
  "https://<ppdm>:8443/api/v2/protection-policies/$POLICY_ID/asset-assignments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"assetIds\": [\"$NS_ID\"]}" | jq .
```

**Auto-assign with a Protection Rule (recommended for dynamic clusters):**

```bash
# Create a rule: assign any K8S_NAMESPACE asset to the policy automatically
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"k8s-auto-assign\",
    \"assetType\": \"KUBERNETES\",
    \"policyId\": \"$POLICY_ID\",
    \"conditions\": [
      {
        \"assetAttributeName\": \"type\",
        \"operator\": \"EQUALS\",
        \"assetAttributeValue\": \"K8S_NAMESPACE\"
      }
    ],
    \"action\": \"MOVE_TO_POLICY\",
    \"priority\": 1
  }" | jq .
```

---

### Step 8 — Run an On-Demand Backup

Trigger an immediate backup without waiting for the scheduled window:

```bash
# Trigger on-demand backup for the policy
curl -sk -X POST \
  "https://<ppdm>:8443/api/v2/protection-policies/$POLICY_ID/protections" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assetIds\": [\"$NS_ID\"],
    \"stages\": [{\"type\": \"PROTECTION\"}]
  }" | jq '{activityId: .activityId}'

# Monitor the activity
ACTIVITY_ID=<activityId from above>
curl -sk "https://<ppdm>:8443/api/v2/activities/$ACTIVITY_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{state, result, progress: .stats.percentComplete}'
```

---

### Step 9 — Restore a Kubernetes Namespace

PPDM supports two restore types:

| Restore Type | Use Case |
|---|---|
| **Original location** | Overwrite the existing namespace in-place |
| **New location** | Restore to a different namespace or cluster |

```bash
# List available backup copies for the namespace asset
curl -sk "https://<ppdm>:8443/api/v2/assets/$NS_ID/copies" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {copyId: .id, createTime, retentionTime}'

COPY_ID=<copyId from above>

# Restore to original namespace (overwrites existing)
curl -sk -X POST https://<ppdm>:8443/api/v2/restores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"copyId\": \"$COPY_ID\",
    \"restoreType\": \"TO_ORIGINAL\",
    \"options\": {
      \"k8s\": {
        \"restorePVCs\": true,
        \"restoreNamespaceMetadata\": true
      }
    }
  }" | jq '{restoreId: .id, state}'

# Restore to a new namespace
curl -sk -X POST https://<ppdm>:8443/api/v2/restores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"copyId\": \"$COPY_ID\",
    \"restoreType\": \"TO_NEW\",
    \"options\": {
      \"k8s\": {
        \"targetNamespace\": \"<new-namespace>\",
        \"targetClusterId\": \"$INV_ID\",
        \"restorePVCs\": true,
        \"restoreNamespaceMetadata\": true
      }
    }
  }" | jq '{restoreId: .id, state}'
```

---

### Step 10 — Verify and Monitor Protection

**Check SLA compliance for Kubernetes assets:**

```bash
# List all K8S assets with their SLA compliance status
curl -sk "https://<ppdm>:8443/api/v2/assets?filter=type%20eq%20%22K8S_NAMESPACE%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {name, complianceStatus: .lastAvailableCopyTime, policy: .protectionPolicyName}'

# List failed K8S activities from last 24 hours
curl -sk "https://<ppdm>:8443/api/v2/activities?filter=state%20eq%20%22FAILED%22%20and%20assetType%20eq%20%22KUBERNETES%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, startTime, errorCode: .result.error.code, errorMsg: .result.error.message}'
```

**Verify CDI pod health inside the cluster:**

```bash
# CDI is deployed in the powerprotect namespace
kubectl get pods -n powerprotect

# Check CDI logs for errors
kubectl logs -n powerprotect -l app=cdi-controller --tail=100

# Check VolumeSnapshots created by PPDM
kubectl get volumesnapshots --all-namespaces

# Inspect a specific snapshot
kubectl describe volumesnapshot <snapshot-name> -n <namespace>
```

---

### Kubernetes Troubleshooting

| Problem | Likely Cause | Resolution |
|---|---|---|
| CDI pod stuck `Pending` | Node resource constraints or missing toleration | Check `kubectl describe pod -n powerprotect <cdi-pod>`; review node capacity |
| Discovery returns no namespaces | RBAC insufficient or API server unreachable | Verify ServiceAccount token; test `curl -k https://<api>:6443/api/v1/namespaces` |
| `VolumeSnapshot` stays `ReadyToUse: false` | CSI driver issue or snapshot class misconfigured | `kubectl describe volumesnapshot <name>`; check CSI driver logs |
| Backup activity fails with `NO_SNAPSHOT_CLASS` | No default VolumeSnapshotClass set | Add annotation `snapshot.storage.kubernetes.io/is-default-class: "true"` |
| PVC restore fails — `StorageClass not found` | Target cluster missing the original StorageClass | Create matching StorageClass in target cluster before restoring |
| Restore partially complete — some PVCs missing | PVC bound to `ReadWriteOnce` volume on a different node | Scale down workloads before restore; ensure node affinity matches |
| CDI cannot reach Data Domain | Network policy blocking egress on port 2052 | Add egress NetworkPolicy rule allowing CDI namespace → DD IP:2052 |
| SLA breach despite successful backups | RPO window too tight or backup duration exceeds schedule gap | Increase backup frequency or widen SLA window in policy |

---

### Kubernetes Protection — Best Practices

1. **Protect namespaces, not individual PVCs** — namespace-level backups capture both data and Kubernetes object definitions (Deployments, ConfigMaps, Secrets, Services) together.
2. **Use Protection Rules for dynamic environments** — new namespaces are auto-assigned to policies without manual intervention.
3. **Ensure CSI driver supports `VolumeSnapshot` v1** — older beta (`v1beta1`) snapshots are not supported in PPDM 19.10+.
4. **Test restores to a separate namespace regularly** — validate data integrity without impacting production.
5. **Label namespaces consistently** — use labels like `ppdm-protect: "true"` and build Protection Rules around them.
6. **Scale down stateful workloads before in-place restore** — prevents data corruption from live writes during namespace overwrite.
7. **Monitor CDI pod health proactively** — a failed CDI blocks all backups for that cluster; set up alerts on the `powerprotect` namespace.
8. **Exclude system namespaces** — never include `kube-system`, `kube-public`, or `kube-node-lease` in protection policies.
9. **Align retention with RTO/RPO requirements** — keep at least 7 daily + 4 weekly copies for production workloads.
10. **Use DDBoost with Data Domain** — deduplicated backup streams significantly reduce backup window and storage consumption for k8s workloads with large overlapping layers.

---

## Extended API Reference

This section covers all major integration APIs beyond core backup/restore — DDBoost configuration, Data Domain management, VMware VADP, CloudBoost, SLA reporting, credentials, alerts, and system health.

---

### DDBoost Configuration

**DDBoost (Data Domain Boost)** is the recommended data path between PPDM/NetWorker and Data Domain. It enables client-side deduplication, encrypted transport, and significantly faster backups compared to standard NFS/CIFS.

#### Step 1 — Enable DDBoost on the Data Domain Appliance

DDBoost is managed via the **Data Domain REST API** (port 3009) or the DD CLI (`ddsh`).

```bash
# DD CLI — enable DDBoost service
ddsh> ddboost status
ddsh> ddboost enable
ddsh> ddboost status   # confirm: DDBoost status: enabled

# Create a dedicated DDBoost user
ddsh> user add <ddboost-user> role none
ddsh> ddboost user assign <ddboost-user> read-write

# Create a storage unit for PPDM or NetWorker
ddsh> ddboost storage-unit create <su-name> user <ddboost-user>
ddsh> ddboost storage-unit list   # verify creation

# Enable encryption in flight (optional but recommended)
ddsh> ddboost option set encryption-strength medium
```

#### Step 2 — Configure DDBoost on Data Domain via REST API

Data Domain exposes a management REST API at `https://<dd-host>:3009/rest/v1.0`.

```bash
# Authenticate — get session token
DD_TOKEN=$(curl -sk -X POST https://<dd-host>:3009/rest/v1.0/auth \
  -H "Content-Type: application/json" \
  -d '{"username":"sysadmin","password":"<pass>"}' \
  | jq -r '.token')

# Check DDBoost service status
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/ddboost \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" | jq '{status: .status, encryption: .encryption}'

# Enable DDBoost service
curl -sk -X PUT https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/ddboost \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "enabled"}' | jq .

# Create a storage unit
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/ddboost/storage-units \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<su-name>",
    "user": "<ddboost-user>",
    "quota": {
      "soft-limit": {"value": 10, "unit": "TiB"},
      "hard-limit": {"value": 12, "unit": "TiB"}
    }
  }' | jq '{name, status}'

# List all storage units
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/ddboost/storage-units \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.storage_units[] | {name, "pre-comp-used", quota}'

# Create a DDBoost user
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/users \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<ddboost-user>",
    "password": "<user-pass>",
    "role": "none"
  }' | jq .

# Assign user to storage unit
curl -sk -X PUT \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/ddboost/storage-units/<su-name>/users" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "<ddboost-user>", "access": "read-write"}' | jq .
```

#### Step 3 — Register Data Domain as a Storage System in PPDM

```bash
# Authenticate to PPDM
TOKEN=$(curl -sk -X POST https://<ppdm>:8443/api/v2/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<pass>"}' | jq -r '.access_token')

# Add Data Domain as a storage system with DDBoost credentials
curl -sk -X POST https://<ppdm>:8443/api/v2/storage-systems \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "DATA_DOMAIN_SYSTEM",
    "name": "<dd-name>",
    "address": "<dd-host>",
    "port": 3009,
    "credentials": {
      "type": "STORAGE",
      "username": "sysadmin",
      "password": "<dd-pass>"
    },
    "details": {
      "dataDomain": {
        "enableDdBoost": true,
        "ddBoostUser": "<ddboost-user>",
        "ddBoostPassword": "<ddboost-pass>",
        "storageUnit": "<su-name>",
        "encryptionEnabled": true
      }
    }
  }' | jq '{id, name, type, status}'

# List registered storage systems
curl -sk https://<ppdm>:8443/api/v2/storage-systems \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, type, "usedSize", "totalSize"}'

# Get capacity details for a specific system
curl -sk https://<ppdm>:8443/api/v2/storage-systems/<id> \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{name, usedSize, totalSize, compressionRatio: .details.dataDomain.compressionRatio}'

# Update DDBoost credentials on existing storage system
curl -sk -X PATCH https://<ppdm>:8443/api/v2/storage-systems/<id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "details": {
      "dataDomain": {
        "ddBoostPassword": "<new-pass>"
      }
    }
  }' | jq '{id, name}'

# Delete a storage system (only if no active policies reference it)
curl -sk -X DELETE https://<ppdm>:8443/api/v2/storage-systems/<id> \
  -H "Authorization: Bearer $TOKEN"
```

#### Step 4 — Register DDBoost Device in NetWorker

For NetWorker environments, add the DD storage unit as a DDBoost device:

```bash
# On the NetWorker server — configure DDBoost device
nsradmin -s <nw-server>

nsradmin> create type: NSR device;
  name: DDBoost:<dd-host>:/<su-name>;
  device access information: host=<dd-host>,user=<ddboost-user>,password=<ddboost-pass>;
  media type: Data Domain;
  target sessions: 10;
  max sessions: 60;
  enabled: Yes;

# Verify device is online
nsradmin> print type: NSR device; name: DDBoost:<dd-host>:/<su-name>

# Label and mount (via NMC or CLI)
nsrmm -s <nw-server> -l -f DDBoost:<dd-host>:/<su-name> -T "DD-Pool"
```

#### DDBoost — Port Reference

| Port | Protocol | Purpose |
|---|---|---|
| `2052` | TCP | DDBoost data transfer (client → DD) |
| `3009` | HTTPS | Data Domain REST API |
| `111` | TCP/UDP | NFS portmapper (if using NFS alongside DDBoost) |
| `2049` | TCP | NFS (AFTD devices, not DDBoost) |

---

### Data Domain REST API — Full Reference

Base URL: `https://<dd-host>:3009/rest/v1.0`

```bash
# ── SYSTEM INFO ───────────────────────────────────────────────────
# Get system overview (model, version, serial)
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0 \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{model, version, hostname, serial}'

# Get filesystem usage
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/filesystems \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.filesystems[] | {name, status, "total-size", "used-size", "avail-size"}'

# ── REPLICATION ───────────────────────────────────────────────────
# List replication contexts
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/replication \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.replication_contexts[] | {id, source, destination, status}'

# Start replication sync
curl -sk -X POST \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/replication/<ctx-id>/sync" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" | jq .

# ── ALERTS ────────────────────────────────────────────────────────
# List active alerts
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/alerts \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.alerts[] | {severity, class, object, message, "post-time"}'

# ── PERFORMANCE ───────────────────────────────────────────────────
# Get current I/O throughput stats
curl -sk "https://<dd-host>:3009/rest/v1.0/dd-systems/0/stats/throughput?duration=1hour" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" | jq .

# ── NETWORK ───────────────────────────────────────────────────────
# List network interfaces
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/network/interfaces \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.interfaces[] | {name, ipv4, status, speed}'

# ── MAINTENANCE ───────────────────────────────────────────────────
# Start filesystem clean (reclaim space)
curl -sk -X POST \
  https://<dd-host>:3009/rest/v1.0/dd-systems/0/filesystems/0/clean \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" | jq .

# Check clean status
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/filesystems/0/clean \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" | jq '{status, "bytes-freed"}'
```

---

### VMware Protection API (PPDM)

PPDM integrates with vCenter to discover and protect VMs using **VMware VADP (vStorage APIs for Data Protection)** or **vSphere CBT (Changed Block Tracking)**.

#### Step 1 — Register vCenter as an Inventory Source

```bash
# Add vCenter
curl -sk -X POST https://<ppdm>:8443/api/v2/inventory-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "VCENTER",
    "name": "<vcenter-name>",
    "address": "<vcenter-fqdn>",
    "port": 443,
    "credentials": {
      "type": "VCENTER",
      "username": "administrator@vsphere.local",
      "password": "<pass>"
    }
  }' | jq '{id, name, type}'

# Trigger VM discovery
curl -sk -X POST \
  https://<ppdm>:8443/api/v2/inventory-sources/<vcenter-id>/discover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

# List discovered VMs
curl -sk "https://<ppdm>:8443/api/v2/assets?filter=type%20eq%20%22VMWARE_VIRTUAL_MACHINE%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, powerState: .details.vm.powerState}'
```

#### Step 2 — Create a VM Protection Policy

```bash
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"vm-daily-policy\",
    \"assetType\": \"VMWARE_VIRTUAL_MACHINE\",
    \"type\": \"ACTIVE\",
    \"dataConsistency\": \"CRASH_CONSISTENT\",
    \"stages\": [
      {
        \"type\": \"PROTECTION\",
        \"retention\": {\"unit\": \"DAY\", \"interval\": 14},
        \"target\": {
          \"storageSystemId\": \"$DD_ID\",
          \"dataTargetWithDdBoost\": true
        },
        \"operations\": [
          {
            \"type\": \"SYNTHETIC_FULL\",
            \"schedule\": {
              \"frequency\": \"DAILY\",
              \"startTime\": \"22:00\",
              \"duration\": 8,
              \"durationUnit\": \"HOURS\"
            }
          }
        ]
      }
    ]
  }" | jq '{id, name}'
```

#### Step 3 — VM Instant Access Restore

Spin up a VM directly from the backup copy without a full restore (useful for quick validation or DR):

```bash
# List copies for a VM asset
curl -sk "https://<ppdm>:8443/api/v2/assets/<vm-asset-id>/copies" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, createTime, consistent}'

# Instant access restore — mounts VM directly from DD
curl -sk -X POST https://<ppdm>:8443/api/v2/restores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"copyId\": \"$COPY_ID\",
    \"restoreType\": \"INSTANT_ACCESS\",
    \"options\": {
      \"vm\": {
        \"powerOn\": true,
        \"targetVcenter\": \"<vcenter-id>\",
        \"targetDatastore\": \"<datastore-name>\",
        \"targetResourcePool\": \"<resource-pool>\"
      }
    }
  }" | jq '{restoreId: .id, state}'
```

---

### CloudBoost API (NetWorker)

**CloudBoost** is the NetWorker cloud gateway — it presents as a standard NetWorker device while transparently tiering data to object storage (AWS S3, Azure Blob, GCP GCS).

#### Step 1 — Register CloudBoost Appliance in NetWorker

```bash
# Via NetWorker REST API
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/cloudboost \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "<cloudboost-host>",
    "port": 9000,
    "username": "administrator",
    "password": "<cb-pass>"
  }' | jq .

# List registered CloudBoost appliances
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/cloudboost \
  -u admin:<pass> | jq '.[] | {hostname, status, version}'
```

#### Step 2 — Configure Cloud Storage Bucket

```bash
# Create cloud storage profile (AWS S3 example)
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/cloudboost/storageprofiles \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "name": "aws-s3-profile",
    "cloudProvider": "AWS",
    "bucketName": "<s3-bucket-name>",
    "region": "us-east-1",
    "accessKeyId": "<aws-access-key>",
    "secretAccessKey": "<aws-secret-key>",
    "encryptionEnabled": true,
    "encryptionAlgorithm": "AES256"
  }' | jq .

# Azure Blob example
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/cloudboost/storageprofiles \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "name": "azure-blob-profile",
    "cloudProvider": "AZURE",
    "containerName": "<container-name>",
    "accountName": "<storage-account>",
    "accountKey": "<storage-key>",
    "encryptionEnabled": true
  }' | jq .
```

#### Step 3 — Add CloudBoost as a NetWorker Device

```bash
# List available CloudBoost storage units
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/cloudboost/storageunits \
  -u admin:<pass> | jq '.[] | {name, cloudProvider, usedCapacity}'

# Add CloudBoost device to NetWorker
nsradmin -s <nw-server>
nsradmin> create type: NSR device;
  name: CloudBoost:<cloudboost-host>:/<storage-unit>;
  device access information: host=<cloudboost-host>,user=administrator,password=<pass>;
  media type: CloudBoost;
  target sessions: 8;
  enabled: Yes;
```

---

### Credentials API (PPDM)

PPDM stores credentials centrally and references them by ID in policies, inventory sources, and storage systems.

```bash
# ── CREATE ─────────────────────────────────────────────────────────
# Create OS credentials (for app agents / filesystem protection)
curl -sk -X POST https://<ppdm>:8443/api/v2/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "OS",
    "name": "linux-backup-creds",
    "username": "root",
    "password": "<pass>"
  }' | jq '{id, name, type}'

# Create database credentials (Oracle / SQL)
curl -sk -X POST https://<ppdm>:8443/api/v2/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ORACLE",
    "name": "oracle-prod-creds",
    "username": "rman",
    "password": "<pass>"
  }' | jq '{id, name, type}'

# Create vCenter credentials
curl -sk -X POST https://<ppdm>:8443/api/v2/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "VCENTER",
    "name": "vcenter-admin-creds",
    "username": "administrator@vsphere.local",
    "password": "<pass>"
  }' | jq '{id, name, type}'

# ── READ / UPDATE / DELETE ─────────────────────────────────────────
# List all credentials (passwords are never returned)
curl -sk https://<ppdm>:8443/api/v2/credentials \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, type, lastUpdated}'

# Update a credential password
curl -sk -X PATCH https://<ppdm>:8443/api/v2/credentials/<id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "<new-pass>"}' | jq '{id, name}'

# Delete a credential (only if not referenced)
curl -sk -X DELETE https://<ppdm>:8443/api/v2/credentials/<id> \
  -H "Authorization: Bearer $TOKEN"

# Verify credential connectivity (test against target host)
curl -sk -X POST https://<ppdm>:8443/api/v2/credentials/<id>/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"host": "<target-host>"}' | jq '{status, message}'
```

---

### SLA and Compliance API (PPDM)

SLAs define the RPO window. PPDM continuously measures compliance against them.

```bash
# List all SLAs
curl -sk https://<ppdm>:8443/api/v2/slas \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, rpoInSeconds, compliance}'

# Get compliance summary — count compliant vs non-compliant assets
curl -sk https://<ppdm>:8443/api/v2/slas/compliance-summary \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{compliant, nonCompliant, notProtected}'

# List non-compliant assets
curl -sk "https://<ppdm>:8443/api/v2/assets?filter=complianceStatus%20eq%20%22NON_COMPLIANT%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {name, type, lastCopyTime, protectionPolicyName}'

# Create a custom SLA (4-hour RPO)
curl -sk -X POST https://<ppdm>:8443/api/v2/slas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "4hr-rpo-sla",
    "rpoInSeconds": 14400,
    "backupWindowStart": "00:00",
    "backupWindowEnd": "06:00"
  }' | jq '{id, name, rpoInSeconds}'

# Assign SLA to a protection policy
curl -sk -X PATCH https://<ppdm>:8443/api/v2/protection-policies/<policy-id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slaId": "<sla-id>"}' | jq '{id, name}'
```

---

### Alerts and Events API (PPDM)

```bash
# List all active alerts (unacknowledged)
curl -sk "https://<ppdm>:8443/api/v2/alerts?filter=acknowledgementStatus%20eq%20%22UNACKNOWLEDGED%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, severity, messageCode, description, createTime}'

# Filter by severity: INFO | WARNING | ERROR | CRITICAL
curl -sk "https://<ppdm>:8443/api/v2/alerts?filter=severity%20eq%20%22CRITICAL%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, description, createTime}'

# Acknowledge an alert
curl -sk -X PATCH https://<ppdm>:8443/api/v2/alerts/<alert-id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"acknowledgementStatus": "ACKNOWLEDGED"}' | jq .

# Acknowledge all alerts in bulk
curl -sk -X POST https://<ppdm>:8443/api/v2/alerts/bulk-acknowledge \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filter": "severity eq \"WARNING\""}' | jq .

# List audit log events (user actions, policy changes)
curl -sk https://<ppdm>:8443/api/v2/audit-logs \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {user, action, resource, result, timestamp}'

# Configure SMTP for alert email notifications
curl -sk -X PUT https://<ppdm>:8443/api/v2/notification-settings/email \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "smtpServer": "<smtp-host>",
    "smtpPort": 587,
    "fromAddress": "ppdm-alerts@company.com",
    "recipients": ["ops-team@company.com"],
    "useTLS": true,
    "alertSeverities": ["WARNING", "ERROR", "CRITICAL"]
  }' | jq .
```

---

### System Health and Certificates API (PPDM)

```bash
# ── HEALTH ─────────────────────────────────────────────────────────
# Overall system health status
curl -sk https://<ppdm>:8443/api/v2/system-settings \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{version, buildDate, systemHealth}'

# Component health check (database, services, storage)
curl -sk https://<ppdm>:8443/api/v2/components \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {name, status, version}'

# ── CERTIFICATES ───────────────────────────────────────────────────
# List installed certificates
curl -sk https://<ppdm>:8443/api/v2/certificates \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, subject, issuer, notAfter, type}'

# Accept a certificate from an inventory source (vCenter, k8s, DD)
curl -sk -X POST https://<ppdm>:8443/api/v2/certificates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "<target-host>",
    "port": 443,
    "type": "HOST"
  }' | jq '{id, subject, notAfter}'

# ── LICENSE ────────────────────────────────────────────────────────
# Check license capacity and usage
curl -sk https://<ppdm>:8443/api/v2/licenses \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.[] | {feature, capacity, used, percentUsed, expirationDate}'
```

---

### Python Automation Library — Reusable PPDM Client

A minimal reusable client covering auth, DDBoost storage, assets, and activities:

```python
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PPDMClient:
    """Minimal PPDM REST API client with auto-token management."""

    def __init__(self, host: str, username: str, password: str):
        self.base = f"https://{host}:8443/api/v2"
        self.session = requests.Session()
        self.session.verify = False
        self._token = None
        self._auth(username, password)

    def _auth(self, username: str, password: str):
        r = self.session.post(f"{self.base}/login",
                              json={"username": username, "password": password})
        r.raise_for_status()
        self._token = r.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self._token}"})

    def get(self, path: str, **params):
        r = self.session.get(f"{self.base}{path}", params=params)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, body: dict):
        r = self.session.post(f"{self.base}{path}", json=body)
        r.raise_for_status()
        return r.json()

    def patch(self, path: str, body: dict):
        r = self.session.patch(f"{self.base}{path}", json=body)
        r.raise_for_status()
        return r.json()

    # ── Storage ──────────────────────────────────────────────────
    def list_storage_systems(self):
        return self.get("/storage-systems").get("content", [])

    def add_data_domain(self, name, address, dd_user, dd_pass, su_name):
        return self.post("/storage-systems", {
            "type": "DATA_DOMAIN_SYSTEM",
            "name": name,
            "address": address,
            "port": 3009,
            "credentials": {"type": "STORAGE", "username": "sysadmin", "password": dd_pass},
            "details": {
                "dataDomain": {
                    "enableDdBoost": True,
                    "ddBoostUser": dd_user,
                    "ddBoostPassword": dd_pass,
                    "storageUnit": su_name,
                    "encryptionEnabled": True
                }
            }
        })

    # ── Assets ───────────────────────────────────────────────────
    def list_assets(self, asset_type: str = None, page_size: int = 100):
        params = {"pageSize": page_size}
        if asset_type:
            params["filter"] = f'type eq "{asset_type}"'
        return self.get("/assets", **params).get("content", [])

    def get_asset_copies(self, asset_id: str):
        return self.get(f"/assets/{asset_id}/copies").get("content", [])

    # ── Activities ───────────────────────────────────────────────
    def list_failed_activities(self, asset_type: str = None):
        f = 'state eq "FAILED"'
        if asset_type:
            f += f' and assetType eq "{asset_type}"'
        return self.get("/activities", filter=f, pageSize=100).get("content", [])

    def get_activity(self, activity_id: str):
        return self.get(f"/activities/{activity_id}")

    # ── Alerts ───────────────────────────────────────────────────
    def list_critical_alerts(self):
        return self.get("/alerts",
                        filter='severity eq "CRITICAL" and acknowledgementStatus eq "UNACKNOWLEDGED"'
                        ).get("content", [])

    # ── SLA ──────────────────────────────────────────────────────
    def compliance_summary(self):
        return self.get("/slas/compliance-summary")


# Usage example
if __name__ == "__main__":
    ppdm = PPDMClient("ppdm.corp.local", "admin", "Password123!")

    print("=== Storage Systems ===")
    for s in ppdm.list_storage_systems():
        print(f"  {s['name']}  used={s.get('usedSize','?')}  total={s.get('totalSize','?')}")

    print("\n=== Failed Activities (Last Run) ===")
    for a in ppdm.list_failed_activities():
        print(f"  [{a['startTime']}] {a['name']}  error={a.get('result',{}).get('error',{}).get('code','?')}")

    print("\n=== SLA Compliance ===")
    c = ppdm.compliance_summary()
    print(f"  Compliant: {c.get('compliant')}  Non-compliant: {c.get('nonCompliant')}  Unprotected: {c.get('notProtected')}")

    print("\n=== Critical Alerts ===")
    for alert in ppdm.list_critical_alerts():
        print(f"  [{alert['createTime']}] {alert['description']}")
```

---

### PPDM Users and Role-Based Access Control (RBAC) API

PPDM ships with built-in roles. Users are either local accounts or mapped from an external LDAP/AD directory (see LDAP section). Every user must be assigned at least one role.

#### Built-in Roles

| Role | Permissions |
|---|---|
| `ROLE_ADMIN` | Full system access — all read/write operations |
| `ROLE_BACKUP_ADMINISTRATOR` | Manage policies, assets, storage; cannot change system settings |
| `ROLE_RESTORE_ADMINISTRATOR` | Initiate and manage restores; read-only on policies |
| `ROLE_USER` | View activities and assets; no configuration rights |
| `ROLE_AUDIT_ADMINISTRATOR` | Read audit logs only |

```bash
# ── LIST ───────────────────────────────────────────────────────────
# List all local users
curl -sk https://<ppdm>:8443/api/v2/users \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, role, enabled, lastLogin}'

# List all available roles
curl -sk https://<ppdm>:8443/api/v2/roles \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, description}'

# ── CREATE ─────────────────────────────────────────────────────────
# Create a local user with Backup Administrator role
ROLE_ID=$(curl -sk https://<ppdm>:8443/api/v2/roles \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.content[] | select(.name=="ROLE_BACKUP_ADMINISTRATOR") | .id')

curl -sk -X POST https://<ppdm>:8443/api/v2/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"backup-ops\",
    \"password\": \"SecurePass123!\",
    \"roleId\": \"$ROLE_ID\",
    \"enabled\": true,
    \"email\": \"backup-ops@company.com\"
  }" | jq '{id, name, role}'

# ── UPDATE ─────────────────────────────────────────────────────────
# Change a user's role
curl -sk -X PATCH https://<ppdm>:8443/api/v2/users/<user-id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"roleId\": \"$ROLE_ID\"}" | jq '{id, name, role}'

# Reset a user's password
curl -sk -X POST https://<ppdm>:8443/api/v2/users/<user-id>/reset-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "NewSecurePass456!"}' | jq .

# Disable a user account
curl -sk -X PATCH https://<ppdm>:8443/api/v2/users/<user-id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' | jq '{id, name, enabled}'

# ── DELETE ─────────────────────────────────────────────────────────
curl -sk -X DELETE https://<ppdm>:8443/api/v2/users/<user-id> \
  -H "Authorization: Bearer $TOKEN"

# ── SESSIONS ───────────────────────────────────────────────────────
# List active sessions (who is currently logged in)
curl -sk https://<ppdm>:8443/api/v2/sessions \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {user, loginTime, lastActivityTime, sourceIp}'

# Invalidate a specific session (force logout)
curl -sk -X DELETE https://<ppdm>:8443/api/v2/sessions/<session-id> \
  -H "Authorization: Bearer $TOKEN"
```

---

### PPDM LDAP / Active Directory Integration API

Integrate PPDM with an external LDAP or Active Directory server so that AD users and groups can log in with their domain credentials.

```bash
# ── CONFIGURE LDAP PROVIDER ────────────────────────────────────────
curl -sk -X POST https://<ppdm>:8443/api/v2/ldap-providers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "corp-ad",
    "type": "ACTIVE_DIRECTORY",
    "serverAddress": "ldaps://dc01.corp.local",
    "port": 636,
    "useSsl": true,
    "baseDn": "DC=corp,DC=local",
    "bindDn": "CN=svc-ppdm,OU=ServiceAccounts,DC=corp,DC=local",
    "bindPassword": "<bind-pass>",
    "userSearchBase": "OU=Users,DC=corp,DC=local",
    "userSearchFilter": "(sAMAccountName={0})",
    "groupSearchBase": "OU=Groups,DC=corp,DC=local",
    "groupSearchFilter": "(member={0})"
  }' | jq '{id, name, type, status}'

# Test LDAP connectivity
curl -sk -X POST https://<ppdm>:8443/api/v2/ldap-providers/<id>/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "<test-pass>"}' \
  | jq '{status, message}'

# List configured LDAP providers
curl -sk https://<ppdm>:8443/api/v2/ldap-providers \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, serverAddress, status}'

# ── MAP AD GROUP TO PPDM ROLE ──────────────────────────────────────
# Find the LDAP provider ID
LDAP_ID=$(curl -sk https://<ppdm>:8443/api/v2/ldap-providers \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.content[] | select(.name=="corp-ad") | .id')

# Map AD group "PPDM-BackupAdmins" to ROLE_BACKUP_ADMINISTRATOR
curl -sk -X POST https://<ppdm>:8443/api/v2/ldap-providers/$LDAP_ID/group-mappings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"groupDn\": \"CN=PPDM-BackupAdmins,OU=Groups,DC=corp,DC=local\",
    \"roleId\": \"$ROLE_ID\"
  }" | jq '{id, groupDn, roleId}'

# List all group mappings
curl -sk https://<ppdm>:8443/api/v2/ldap-providers/$LDAP_ID/group-mappings \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {groupDn, roleId}'

# Delete a group mapping
curl -sk -X DELETE \
  "https://<ppdm>:8443/api/v2/ldap-providers/$LDAP_ID/group-mappings/<mapping-id>" \
  -H "Authorization: Bearer $TOKEN"

# ── UPDATE / DELETE LDAP PROVIDER ─────────────────────────────────
# Update bind password
curl -sk -X PATCH https://<ppdm>:8443/api/v2/ldap-providers/<id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bindPassword": "<new-pass>"}' | jq '{id, name}'

# Remove LDAP provider
curl -sk -X DELETE https://<ppdm>:8443/api/v2/ldap-providers/<id> \
  -H "Authorization: Bearer $TOKEN"
```

---

### PPDM App Host and Agent Registration API

Before protecting Oracle, SQL Server, or SAP HANA databases, you must register the application host in PPDM and install the appropriate agent.

#### Agent Types

| Agent | Workload | Package |
|---|---|---|
| `TSDM` (Transparent Snapshot Data Mover) | VMware VMs | Deployed automatically |
| `FS_AGENT` | Linux/Windows filesystems | `powerprotect-agentsvc-*.rpm/deb/exe` |
| `ORACLE_AGENT` | Oracle databases | `oracle-agent-*.rpm` |
| `MSSQL_AGENT` | Microsoft SQL Server | `mssql-agent-*.msi` |
| `SAPHANA_AGENT` | SAP HANA | `saphana-agent-*.rpm` |

```bash
# ── REGISTER AN APPLICATION HOST ───────────────────────────────────
# Step 1: Create OS credentials for the host
CRED_ID=$(curl -sk -X POST https://<ppdm>:8443/api/v2/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "OS",
    "name": "oracle-host-creds",
    "username": "root",
    "password": "<pass>"
  }' | jq -r '.id')

# Step 2: Register the host as an inventory source
curl -sk -X POST https://<ppdm>:8443/api/v2/inventory-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"HOST\",
    \"name\": \"oracle-db-host\",
    \"address\": \"<host-fqdn>\",
    \"port\": 7000,
    \"credentials\": {
      \"id\": \"$CRED_ID\"
    }
  }" | jq '{id, name, type}'

# Step 3: Trigger agent discovery on the host
curl -sk -X POST \
  "https://<ppdm>:8443/api/v2/inventory-sources/<host-id>/discover" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

# ── LIST REGISTERED HOSTS ──────────────────────────────────────────
curl -sk "https://<ppdm>:8443/api/v2/inventory-sources?filter=type%20eq%20%22HOST%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, address, agentStatus: .details.host.agentStatus}'

# ── CHECK AGENT STATUS ─────────────────────────────────────────────
curl -sk "https://<ppdm>:8443/api/v2/inventory-sources/<host-id>" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{name, agentVersion: .details.host.agentVersion, agentStatus: .details.host.agentStatus}'

# ── UPDATE AGENT (push upgrade from PPDM) ─────────────────────────
curl -sk -X POST \
  "https://<ppdm>:8443/api/v2/inventory-sources/<host-id>/agent-upgrade" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '{activityId}'

# ── REMOVE A HOST ─────────────────────────────────────────────────
curl -sk -X DELETE "https://<ppdm>:8443/api/v2/inventory-sources/<host-id>" \
  -H "Authorization: Bearer $TOKEN"
```

---

### PPDM Database Protection API

PPDM supports application-consistent backups for **Oracle**, **Microsoft SQL Server**, and **SAP HANA** via dedicated app agents and protection policies.

#### Oracle Database Protection

```bash
# List discovered Oracle database assets
curl -sk "https://<ppdm>:8443/api/v2/assets?filter=type%20eq%20%22ORACLE%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, host: .details.database.hostName, dbName: .details.database.databaseName}'

# Create Oracle credentials (RMAN catalog user)
ORACLE_CRED_ID=$(curl -sk -X POST https://<ppdm>:8443/api/v2/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ORACLE",
    "name": "oracle-rman-creds",
    "username": "rman",
    "password": "<rman-pass>"
  }' | jq -r '.id')

# Create Oracle protection policy
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"oracle-daily-policy\",
    \"assetType\": \"ORACLE\",
    \"type\": \"ACTIVE\",
    \"dataConsistency\": \"APPLICATION_CONSISTENT\",
    \"details\": {
      \"oracle\": {
        \"credentialId\": \"$ORACLE_CRED_ID\",
        \"backupMode\": \"ARCHIVELOG\",
        \"rmanChannels\": 4,
        \"enableArchiveLogBackup\": true,
        \"archiveLogRetentionHours\": 48
      }
    },
    \"stages\": [
      {
        \"type\": \"PROTECTION\",
        \"retention\": {\"unit\": \"DAY\", \"interval\": 30},
        \"target\": {
          \"storageSystemId\": \"$DD_ID\",
          \"dataTargetWithDdBoost\": true
        },
        \"operations\": [
          {
            \"type\": \"FULL\",
            \"schedule\": {\"frequency\": \"WEEKLY\", \"dayOfWeek\": \"SUNDAY\", \"startTime\": \"01:00\"}
          },
          {
            \"type\": \"INCREMENTAL\",
            \"schedule\": {\"frequency\": \"DAILY\", \"startTime\": \"02:00\"}
          }
        ]
      }
    ]
  }" | jq '{id, name, assetType}'

# Restore Oracle database to a point in time
curl -sk -X POST https://<ppdm>:8443/api/v2/restores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"copyId\": \"$COPY_ID\",
    \"restoreType\": \"TO_ORIGINAL\",
    \"options\": {
      \"oracle\": {
        \"pointInTimeRecovery\": true,
        \"recoveryTime\": \"2026-04-10T14:00:00Z\",
        \"openDatabase\": true
      }
    }
  }" | jq '{restoreId: .id, state}'
```

#### Microsoft SQL Server Protection

```bash
# List discovered SQL Server assets
curl -sk "https://<ppdm>:8443/api/v2/assets?filter=type%20eq%20%22MICROSOFT_SQL_SERVER%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, instance: .details.database.instanceName}'

# Create SQL Server credentials
MSSQL_CRED_ID=$(curl -sk -X POST https://<ppdm>:8443/api/v2/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "MSSQL",
    "name": "mssql-sa-creds",
    "username": "sa",
    "password": "<sa-pass>"
  }' | jq -r '.id')

# Create SQL Server protection policy with log backups
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"mssql-policy\",
    \"assetType\": \"MICROSOFT_SQL_SERVER\",
    \"type\": \"ACTIVE\",
    \"dataConsistency\": \"APPLICATION_CONSISTENT\",
    \"details\": {
      \"mssql\": {
        \"credentialId\": \"$MSSQL_CRED_ID\",
        \"enableLogBackup\": true,
        \"logBackupIntervalMinutes\": 15
      }
    },
    \"stages\": [
      {
        \"type\": \"PROTECTION\",
        \"retention\": {\"unit\": \"DAY\", \"interval\": 14},
        \"target\": {\"storageSystemId\": \"$DD_ID\", \"dataTargetWithDdBoost\": true},
        \"operations\": [
          {
            \"type\": \"FULL\",
            \"schedule\": {\"frequency\": \"DAILY\", \"startTime\": \"23:00\"}
          }
        ]
      }
    ]
  }" | jq '{id, name}'

# Restore SQL database to alternate instance
curl -sk -X POST https://<ppdm>:8443/api/v2/restores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"copyId\": \"$COPY_ID\",
    \"restoreType\": \"TO_NEW\",
    \"options\": {
      \"mssql\": {
        \"targetHost\": \"<target-sql-host>\",
        \"targetInstance\": \"MSSQLSERVER\",
        \"targetDatabase\": \"<restored-db-name>\",
        \"pointInTimeRecovery\": true,
        \"recoveryTime\": \"2026-04-10T10:30:00Z\",
        \"withRecovery\": true
      }
    }
  }" | jq '{restoreId: .id, state}'
```

#### SAP HANA Protection

```bash
# List SAP HANA assets
curl -sk "https://<ppdm>:8443/api/v2/assets?filter=type%20eq%20%22SAP_HANA%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, sid: .details.database.sid}'

# Create SAP HANA credentials (SYSTEM user or dedicated backup user)
HANA_CRED_ID=$(curl -sk -X POST https://<ppdm>:8443/api/v2/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "SAPHANA",
    "name": "hana-backup-creds",
    "username": "SYSTEM",
    "password": "<hana-pass>"
  }' | jq -r '.id')

# Create HANA protection policy
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"hana-policy\",
    \"assetType\": \"SAP_HANA\",
    \"type\": \"ACTIVE\",
    \"dataConsistency\": \"APPLICATION_CONSISTENT\",
    \"details\": {
      \"sapHana\": {
        \"credentialId\": \"$HANA_CRED_ID\",
        \"enableLogBackup\": true,
        \"logBackupIntervalMinutes\": 30,
        \"backupPrefix\": \"PPDM\"
      }
    },
    \"stages\": [
      {
        \"type\": \"PROTECTION\",
        \"retention\": {\"unit\": \"DAY\", \"interval\": 21},
        \"target\": {\"storageSystemId\": \"$DD_ID\", \"dataTargetWithDdBoost\": true},
        \"operations\": [
          {
            \"type\": \"FULL\",
            \"schedule\": {\"frequency\": \"DAILY\", \"startTime\": \"03:00\"}
          }
        ]
      }
    ]
  }" | jq '{id, name}'
```

---

### PPDM Replication and Multi-Tier Copy API

PPDM can replicate backup copies from a primary Data Domain to a remote Data Domain for DR, and add cloud vault tiers for long-term retention — all defined within a single protection policy using multiple stages.

#### Architecture

```
Primary Site                         DR Site
┌─────────────────┐                 ┌─────────────────┐
│  PPDM (primary) │                 │  PPDM (DR)      │
│  DD (primary)   │──── replicate ──│  DD (replica)   │
└─────────────────┘                 └─────────────────┘
         │
         │ cloud vault
         ▼
┌─────────────────┐
│  AWS S3 / Azure │
│  (long-term)    │
└─────────────────┘
```

```bash
# ── ADD REMOTE PPDM AS A REPLICATION TARGET ────────────────────────
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-engines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "PPDM",
    "address": "<remote-ppdm-host>",
    "port": 8443,
    "credentials": {
      "username": "admin",
      "password": "<remote-pass>"
    }
  }' | jq '{id, address, status}'

# List registered protection engines (remote PPDM instances)
curl -sk https://<ppdm>:8443/api/v2/protection-engines \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, address, type, status}'

# ── CREATE MULTI-STAGE POLICY (local + replicate + cloud vault) ────
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"vm-3tier-policy\",
    \"assetType\": \"VMWARE_VIRTUAL_MACHINE\",
    \"type\": \"ACTIVE\",
    \"stages\": [
      {
        \"id\": \"stage-local\",
        \"type\": \"PROTECTION\",
        \"retention\": {\"unit\": \"DAY\", \"interval\": 14},
        \"target\": {\"storageSystemId\": \"$DD_ID\", \"dataTargetWithDdBoost\": true},
        \"operations\": [
          {
            \"type\": \"SYNTHETIC_FULL\",
            \"schedule\": {\"frequency\": \"DAILY\", \"startTime\": \"22:00\"}
          }
        ]
      },
      {
        \"id\": \"stage-replicate\",
        \"type\": \"REPLICATION\",
        \"sourceStageId\": \"stage-local\",
        \"retention\": {\"unit\": \"DAY\", \"interval\": 30},
        \"target\": {
          \"storageSystemId\": \"<remote-dd-id>\",
          \"dataTargetWithDdBoost\": true,
          \"protectionEngineId\": \"<remote-ppdm-id>\"
        },
        \"operations\": [
          {
            \"type\": \"REPLICATION\",
            \"schedule\": {\"frequency\": \"DAILY\", \"startTime\": \"23:30\"}
          }
        ]
      },
      {
        \"id\": \"stage-cloud\",
        \"type\": \"CLOUD_TIER\",
        \"sourceStageId\": \"stage-replicate\",
        \"retention\": {\"unit\": \"YEAR\", \"interval\": 7},
        \"target\": {\"cloudTargetId\": \"<cloud-target-id>\"},
        \"operations\": [
          {
            \"type\": \"CLOUD_TIER\",
            \"schedule\": {\"frequency\": \"WEEKLY\", \"dayOfWeek\": \"SUNDAY\", \"startTime\": \"01:00\"}
          }
        ]
      }
    ]
  }" | jq '{id, name}'

# ── MONITOR REPLICATION ACTIVITIES ────────────────────────────────
curl -sk "https://<ppdm>:8443/api/v2/activities?filter=type%20eq%20%22REPLICATION%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, state, startTime, bytesTransferred: .stats.bytesTransferred}'
```

---

### PPDM Cloud Tier API

Cloud Tier moves backup data from Data Domain to object storage (AWS S3, Azure Blob, or GCP GCS) for long-term, cost-effective retention.

```bash
# ── REGISTER A CLOUD TARGET ────────────────────────────────────────
# AWS S3
curl -sk -X POST https://<ppdm>:8443/api/v2/cloud-targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "aws-s3-vault",
    "type": "AWS_S3",
    "region": "us-east-1",
    "bucketName": "<s3-bucket>",
    "credentials": {
      "accessKeyId": "<aws-key>",
      "secretAccessKey": "<aws-secret>"
    },
    "encryptionEnabled": true,
    "storageClass": "GLACIER_IR"
  }' | jq '{id, name, type, status}'

# Azure Blob
curl -sk -X POST https://<ppdm>:8443/api/v2/cloud-targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "azure-blob-vault",
    "type": "AZURE_BLOB",
    "containerName": "<container>",
    "credentials": {
      "accountName": "<storage-account>",
      "accountKey": "<storage-key>"
    },
    "encryptionEnabled": true,
    "tier": "ARCHIVE"
  }' | jq '{id, name, type}'

# GCP GCS
curl -sk -X POST https://<ppdm>:8443/api/v2/cloud-targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gcp-gcs-vault",
    "type": "GCP_GCS",
    "bucketName": "<gcs-bucket>",
    "projectId": "<gcp-project-id>",
    "credentials": {
      "serviceAccountJson": "<base64-encoded-sa-json>"
    },
    "storageClass": "ARCHIVE"
  }' | jq '{id, name, type}'

# List registered cloud targets
curl -sk https://<ppdm>:8443/api/v2/cloud-targets \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, type, status, usedCapacity}'

# Manually trigger a cloud tier job for a policy stage
curl -sk -X POST \
  "https://<ppdm>:8443/api/v2/protection-policies/$POLICY_ID/cloud-tier" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"assetIds\": [\"$ASSET_ID\"]}" | jq '{activityId}'

# Recall (restore) data from cloud tier back to DD
curl -sk -X POST https://<ppdm>:8443/api/v2/cloud-recalls \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"copyId\": \"$COPY_ID\",
    \"storageSystemId\": \"$DD_ID\"
  }" | jq '{recallId: .id, state}'
```

---

### PPDM Copies Management API

Manage individual backup copies — delete expired data early, apply retention lock to prevent deletion, or place copies on legal hold for compliance.

```bash
# ── LIST COPIES FOR AN ASSET ───────────────────────────────────────
curl -sk "https://<ppdm>:8443/api/v2/assets/<asset-id>/copies" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, createTime, retentionTime, location, retentionLock, legalHold}'

# ── DELETE A COPY EARLY ────────────────────────────────────────────
# WARNING: irreversible — verify the copy ID before deleting
curl -sk -X DELETE "https://<ppdm>:8443/api/v2/copies/<copy-id>" \
  -H "Authorization: Bearer $TOKEN"

# Bulk delete copies by filter (e.g. all copies older than a date)
curl -sk -X POST https://<ppdm>:8443/api/v2/copies/bulk-delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": "createTime lt \"2025-01-01T00:00:00Z\" and assetId eq \"<asset-id>\""
  }' | jq '{deletedCount}'

# ── RETENTION LOCK ─────────────────────────────────────────────────
# Apply retention lock — copy cannot be deleted before lockExpiry
curl -sk -X PATCH "https://<ppdm>:8443/api/v2/copies/<copy-id>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "retentionLock": true,
    "retentionLockExpiry": "2030-12-31T23:59:59Z"
  }' | jq '{id, retentionLock, retentionLockExpiry}'

# List all retention-locked copies
curl -sk "https://<ppdm>:8443/api/v2/copies?filter=retentionLock%20eq%20true" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, assetName, createTime, retentionLockExpiry}'

# ── LEGAL HOLD ─────────────────────────────────────────────────────
# Place a copy on legal hold (indefinite retention until released)
curl -sk -X POST "https://<ppdm>:8443/api/v2/copies/<copy-id>/legal-hold" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Litigation hold — case #2026-0042",
    "requestedBy": "legal-team@company.com"
  }' | jq '{id, legalHold, legalHoldReason}'

# Release a legal hold
curl -sk -X DELETE "https://<ppdm>:8443/api/v2/copies/<copy-id>/legal-hold" \
  -H "Authorization: Bearer $TOKEN"

# List all copies currently on legal hold
curl -sk "https://<ppdm>:8443/api/v2/copies?filter=legalHold%20eq%20true" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, assetName, legalHoldReason, createTime}'
```

---

### PPDM NAS Protection API

PPDM protects NAS file systems from Dell PowerScale (Isilon), NetApp ONTAP, and generic NFS/SMB shares using a file system agent or agentless NAS connector.

```bash
# ── REGISTER A NAS SYSTEM ──────────────────────────────────────────
# PowerScale / Isilon
curl -sk -X POST https://<ppdm>:8443/api/v2/inventory-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "POWERSCALE",
    "name": "isilon-cluster",
    "address": "<isilon-mgmt-ip>",
    "port": 8080,
    "credentials": {
      "type": "OS",
      "username": "root",
      "password": "<pass>"
    }
  }' | jq '{id, name, type}'

# NetApp ONTAP
curl -sk -X POST https://<ppdm>:8443/api/v2/inventory-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "NETAPP",
    "name": "netapp-cluster",
    "address": "<ontap-mgmt-ip>",
    "port": 443,
    "credentials": {
      "type": "OS",
      "username": "admin",
      "password": "<pass>"
    }
  }' | jq '{id, name, type}'

# ── DISCOVER AND LIST NAS ASSETS ───────────────────────────────────
# Trigger NAS discovery
curl -sk -X POST \
  "https://<ppdm>:8443/api/v2/inventory-sources/<nas-id>/discover" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

# List discovered NAS file system assets
curl -sk "https://<ppdm>:8443/api/v2/assets?filter=type%20eq%20%22FILE_SYSTEM%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, path: .details.fileSystem.path, protocol: .details.fileSystem.protocol}'

# ── CREATE NAS PROTECTION POLICY ───────────────────────────────────
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"nas-daily-policy\",
    \"assetType\": \"FILE_SYSTEM\",
    \"type\": \"ACTIVE\",
    \"dataConsistency\": \"CRASH_CONSISTENT\",
    \"stages\": [
      {
        \"type\": \"PROTECTION\",
        \"retention\": {\"unit\": \"DAY\", \"interval\": 30},
        \"target\": {\"storageSystemId\": \"$DD_ID\", \"dataTargetWithDdBoost\": true},
        \"operations\": [
          {
            \"type\": \"FULL\",
            \"schedule\": {\"frequency\": \"WEEKLY\", \"dayOfWeek\": \"SATURDAY\", \"startTime\": \"02:00\"}
          },
          {
            \"type\": \"INCREMENTAL\",
            \"schedule\": {\"frequency\": \"DAILY\", \"startTime\": \"03:00\"}
          }
        ]
      }
    ]
  }" | jq '{id, name}'

# ── GRANULAR FILE RESTORE ──────────────────────────────────────────
# Restore individual files/folders from a NAS backup
curl -sk -X POST https://<ppdm>:8443/api/v2/restores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"copyId\": \"$COPY_ID\",
    \"restoreType\": \"TO_NEW\",
    \"options\": {
      \"fileSystem\": {
        \"targetPath\": \"/restore-staging\",
        \"targetHost\": \"<target-host>\",
        \"filePaths\": [\"/data/reports/2026\", \"/data/config/app.conf\"],
        \"overwriteExisting\": false
      }
    }
  }" | jq '{restoreId: .id, state}'
```

---

### NetWorker Policy and Workflow API (NW 19+)

NetWorker 19+ replaced the legacy Group/Schedule model with a three-tier hierarchy: **Policy → Workflow → Action**. This provides granular control over backup types, schedules, and data movement in a single pipeline.

#### Policy Hierarchy

```
Policy
 └── Workflow  (schedule + client list)
      ├── Action: Backup        (save data)
      ├── Action: Clone         (copy to secondary)
      └── Action: Expire        (remove expired media)
```

```bash
# ── POLICIES ──────────────────────────────────────────────────────
# List all policies
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/policies \
  -u admin:<pass> | jq '.policies[] | {id, name, comment}'

# Create a policy
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/policies \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gold-Policy",
    "comment": "Tier-1 workloads — daily full, hourly incremental"
  }' | jq .

# Delete a policy
curl -sk -X DELETE "https://<nw-server>:9090/nwrestapi/v3/global/policies/<policy-id>" \
  -u admin:<pass>

# ── WORKFLOWS ─────────────────────────────────────────────────────
# List workflows in a policy
curl -sk "https://<nw-server>:9090/nwrestapi/v3/global/policies/<policy-id>/workflows" \
  -u admin:<pass> | jq '.workflows[] | {id, name, comment, enabled}'

# Create a workflow
curl -sk -X POST \
  "https://<nw-server>:9090/nwrestapi/v3/global/policies/<policy-id>/workflows" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily-Workflow",
    "comment": "Daily backup for Gold clients",
    "autoStartEnabled": true,
    "startInterval": "24:00",
    "startIntervalUnit": "Hours",
    "startTime": "2026-01-01T22:00:00+00:00",
    "clientGroups": ["Gold-Clients"]
  }' | jq .

# ── ACTIONS ───────────────────────────────────────────────────────
# List actions in a workflow
curl -sk \
  "https://<nw-server>:9090/nwrestapi/v3/global/policies/<policy-id>/workflows/<workflow-id>/actions" \
  -u admin:<pass> | jq '.actions[] | {id, name, actionType, scheduleActivities}'

# Create a backup action (traditional backup)
curl -sk -X POST \
  "https://<nw-server>:9090/nwrestapi/v3/global/policies/<policy-id>/workflows/<workflow-id>/actions" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily-Backup-Action",
    "actionType": "backup",
    "backupSpecification": {
      "backupType": "Automatic",
      "destinationPool": "Gold-DD-Pool",
      "retentionPeriod": {"amount": 30, "unit": "Days"}
    },
    "scheduleActivities": [
      {
        "level": "Full",
        "schedule": {
          "interval": "Weekly",
          "weekDays": ["Sunday"],
          "startTime": "22:00"
        }
      },
      {
        "level": "Incr",
        "schedule": {
          "interval": "Daily",
          "startTime": "22:00"
        }
      }
    ]
  }' | jq .

# ── RUN WORKFLOW ON DEMAND ─────────────────────────────────────────
curl -sk -X POST \
  "https://<nw-server>:9090/nwrestapi/v3/global/policies/<policy-id>/workflows/<workflow-id>/op/start" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

# ── MONITOR WORKFLOW ACTIVITIES ────────────────────────────────────
curl -sk "https://<nw-server>:9090/nwrestapi/v3/global/activities" \
  -u admin:<pass> \
  | jq '.activities[] | {id, name, status, startTime, endTime}'

# Get a specific activity detail
curl -sk "https://<nw-server>:9090/nwrestapi/v3/global/activities/<activity-id>" \
  -u admin:<pass> | jq .
```

---

### NetWorker Clone API

Cloning copies savesets from one device/pool to another — typically from a primary DD to tape or a remote DD for DR and long-term retention.

```bash
# ── CLONE VIA REST API ─────────────────────────────────────────────
# Clone specific savesets by SSID to a target pool
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/clones \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "saveSetIds": ["<ssid1>", "<ssid2>"],
    "destinationPool": "DR-DD-Pool",
    "retentionPeriod": {"amount": 90, "unit": "Days"},
    "reclaimOriginalSpace": false,
    "deleteSource": false
  }' | jq '{jobId: .id, status}'

# Clone all savesets from the last 24h for a client
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/clones \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "clientName": "<client-hostname>",
    "saveTime": "last 24 hours",
    "destinationPool": "Tape-Pool",
    "retentionPeriod": {"amount": 365, "unit": "Days"}
  }' | jq '{jobId: .id}'

# Monitor clone job
curl -sk "https://<nw-server>:9090/nwrestapi/v3/global/clones/<job-id>" \
  -u admin:<pass> | jq '{status, completedCount, failedCount}'

# ── CLONE VIA CLI ──────────────────────────────────────────────────
# Clone by saveset ID
nsrclone -s <nw-server> -S <ssid> -b "DR-DD-Pool" -y 90

# Clone all savesets for a client from last week
nsrclone -s <nw-server> -c <client> -t "last week" -b "Tape-Pool" -y 365

# Clone action in a workflow (preferred for scheduled clones)
# Add a clone action to a workflow — see Policy/Workflow API above
# actionType: "clone"  with destinationPool and retentionPeriod
```

---

### NetWorker Directives and Notifications API

**Directives** control what happens during a backup at the client level — skip paths, compress data, or apply encryption. **Notifications** define how NetWorker alerts operators on backup events.

#### Directives

```bash
# ── LIST DIRECTIVES ────────────────────────────────────────────────
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/directives \
  -u admin:<pass> | jq '.directives[] | {id, name, comment}'

# ── CREATE A DIRECTIVE ─────────────────────────────────────────────
# Skip temp files and compress /data
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/directives \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod-directive",
    "comment": "Skip temp, compress data",
    "directive": "<<skip: /tmp /var/tmp>>\n<<compress: /data>>"
  }' | jq '{id, name}'

# Common directive syntax
# <<skip: /path>>           — exclude path from backup
# <<compress: /path>>       — compress path data
# <<nsr_nt_attr: nocomp>>   — disable compression for a path
# <<uasm: /path>>           — use UNIX ASM for ACL backup

# ── ASSIGN DIRECTIVE TO A CLIENT ──────────────────────────────────
nsradmin -s <nw-server>
nsradmin> update type: NSR client; name: <host>;
          directive: prod-directive;
```

#### Notifications

```bash
# ── LIST NOTIFICATIONS ─────────────────────────────────────────────
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/notifications \
  -u admin:<pass> | jq '.notifications[] | {id, name, event, action}'

# ── CREATE EMAIL NOTIFICATION ON BACKUP FAILURE ────────────────────
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/notifications \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "name": "backup-failure-email",
    "comment": "Email ops team on any backup failure",
    "event": "Savegroup Completion",
    "action": "mail -s \"NetWorker Alert: %s\" ops-team@company.com",
    "priority": "Warning",
    "executeOnServer": true
  }' | jq '{id, name, event}'

# Common notification events:
# "Savegroup Completion"       — fires after any group/workflow completes
# "Savegroup Failure"          — fires only on failure
# "Media Event"                — fires on media mount request, full volume, etc.
# "NSR Registration"           — fires when a new client registers
# "Device Registration"        — fires when a device comes online/offline
```

---

### Data Domain VTL API

DD VTL (Virtual Tape Library) presents the Data Domain appliance as a physical tape library to backup applications including NetWorker. It emulates tape drives and cartridges over Fibre Channel or iSCSI.

```bash
# ── VTL SERVICE STATUS ─────────────────────────────────────────────
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/vtl \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{status, "total-slots", "total-drives", "total-caps"}'

# Enable VTL service
curl -sk -X PUT https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/vtl \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "enabled"}' | jq .

# ── LIBRARY MANAGEMENT ─────────────────────────────────────────────
# List VTL libraries
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/vtl/libraries \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.libraries[] | {name, model, slots, drives, caps}'

# Create a VTL library
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/vtl/libraries \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VTL-LIB-01",
    "model": "L700",
    "slots": 200,
    "caps": 20,
    "drives": [
      {"count": 4, "model": "T10KC"}
    ]
  }' | jq '{name, model}'

# ── TAPE / CARTRIDGE MANAGEMENT ────────────────────────────────────
# List cartridges in a library
curl -sk \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/vtl/libraries/VTL-LIB-01/slots" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.slots[] | select(.barcode != null) | {slot, barcode, "write-protected"}'

# Add tapes (cartridges) to a library
curl -sk -X POST \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/vtl/libraries/VTL-LIB-01/tapes" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 50,
    "barcode-prefix": "AA",
    "barcode-start": 1000,
    "capacity": {"value": 800, "unit": "GiB"}
  }' | jq .

# Move a tape to vault (remove from library, retain on DD)
curl -sk -X POST \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/vtl/libraries/VTL-LIB-01/tapes/AA1000/recall" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" | jq .

# ── ACCESS GROUPS (FC/iSCSI ZONING) ───────────────────────────────
# List access groups (which initiators can see the VTL)
curl -sk "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/vtl/access-groups" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.access_groups[] | {name, initiators, devices}'

# Create access group for a NetWorker storage node
curl -sk -X POST \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/vtl/access-groups" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nw-storage-node",
    "initiators": [{"wwpn": "10:00:00:90:fa:xx:xx:xx"}],
    "devices": [{"library": "VTL-LIB-01", "drives": "all"}]
  }' | jq .
```

---

### Data Domain Cloud Tier API

DD Cloud Tier transparently moves inactive data from the active DD file system to object storage (AWS S3, Azure Blob, GCP GCS, or Elastic Cloud Storage), freeing primary disk while preserving data accessibility.

```bash
# ── CHECK CLOUD TIER STATUS ────────────────────────────────────────
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/cloud \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{status, provider, bucket, "active-tier-used", "cloud-tier-used"}'

# ── CONFIGURE CLOUD PROFILE ────────────────────────────────────────
# AWS S3 profile
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/cloud/profiles \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "aws-s3-profile",
    "provider": "AWS",
    "region": "us-east-1",
    "bucket": "<s3-bucket-name>",
    "access-key": "<aws-access-key>",
    "secret-key": "<aws-secret-key>",
    "storage-class": "STANDARD_IA",
    "encryption": {"algorithm": "AES256", "enabled": true}
  }' | jq '{name, provider, status}'

# Azure Blob profile
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/cloud/profiles \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "azure-profile",
    "provider": "AZURE",
    "container": "<container-name>",
    "account-name": "<storage-account>",
    "account-key": "<storage-key>",
    "tier": "Cool"
  }' | jq '{name, provider}'

# List configured cloud profiles
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/cloud/profiles \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.profiles[] | {name, provider, bucket, status}'

# ── ENABLE CLOUD TIER ON A STORAGE UNIT ───────────────────────────
curl -sk -X PUT \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/ddboost/storage-units/<su-name>/cloud-tier" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "profile-name": "aws-s3-profile",
    "age-threshold-days": 30
  }' | jq .

# ── MANUALLY TIER DATA ─────────────────────────────────────────────
# Trigger immediate cloud tier for files older than 30 days
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/cloud/tier \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "storage-unit": "<su-name>",
    "age-threshold-days": 30
  }' | jq '{jobId: .id, status}'

# Check tiering job status
curl -sk "https://<dd-host>:3009/rest/v1.0/dd-systems/0/cloud/tier/<job-id>" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{status, "files-tiered", "bytes-tiered", "percent-complete"}'

# ── RECALL DATA FROM CLOUD ─────────────────────────────────────────
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/cloud/recall \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "storage-unit": "<su-name>",
    "file-path": "/backup/saveset-<ssid>"
  }' | jq '{jobId: .id, status}'

# ── CAPACITY REPORTING ─────────────────────────────────────────────
curl -sk "https://<dd-host>:3009/rest/v1.0/dd-systems/0/cloud/capacity" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{"active-tier-used", "cloud-tier-used", "cloud-tier-savings", "compression-ratio"}'
```

---

### PPDM Reports API

PPDM ships with a set of built-in report templates covering backup trends, SLA compliance, asset protection, storage utilization, and activity history. Reports can be run on-demand or scheduled, and exported as CSV or PDF.

```bash
# ── LIST AVAILABLE REPORT TEMPLATES ───────────────────────────────
curl -sk https://<ppdm>:8443/api/v2/report-templates \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, description, category}'

# Common built-in templates:
# "SLA Compliance Summary"         — compliant vs. non-compliant assets
# "Backup Activity Summary"        — success/failure counts by policy
# "Asset Protection Coverage"      — protected vs. unprotected assets
# "Storage Utilization"            — DD usage per storage system
# "Top Assets by Data Size"        — largest protected assets
# "Backup Window Analysis"         — average backup duration trends

# ── RUN A REPORT ON DEMAND ─────────────────────────────────────────
# Get template ID
TEMPLATE_ID=$(curl -sk https://<ppdm>:8443/api/v2/report-templates \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.content[] | select(.name=="SLA Compliance Summary") | .id')

# Execute report
curl -sk -X POST https://<ppdm>:8443/api/v2/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"templateId\": \"$TEMPLATE_ID\",
    \"parameters\": {
      \"startDate\": \"2026-04-01T00:00:00Z\",
      \"endDate\": \"2026-04-11T23:59:59Z\",
      \"assetType\": \"ALL\"
    }
  }" | jq '{reportId: .id, status}'

# Poll for completion
curl -sk "https://<ppdm>:8443/api/v2/reports/<report-id>" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{status, rowCount, generatedAt}'

# ── EXPORT REPORT ─────────────────────────────────────────────────
# Export as CSV
curl -sk "https://<ppdm>:8443/api/v2/reports/<report-id>/export?format=CSV" \
  -H "Authorization: Bearer $TOKEN" \
  -o report.csv

# Export as PDF
curl -sk "https://<ppdm>:8443/api/v2/reports/<report-id>/export?format=PDF" \
  -H "Authorization: Bearer $TOKEN" \
  -o report.pdf

# ── LIST PAST REPORTS ──────────────────────────────────────────────
curl -sk https://<ppdm>:8443/api/v2/reports \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, templateName, status, generatedAt, rowCount}'

# ── SCHEDULE A RECURRING REPORT ────────────────────────────────────
curl -sk -X POST https://<ppdm>:8443/api/v2/report-schedules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Weekly SLA Report\",
    \"templateId\": \"$TEMPLATE_ID\",
    \"schedule\": {
      \"frequency\": \"WEEKLY\",
      \"dayOfWeek\": \"MONDAY\",
      \"startTime\": \"07:00\"
    },
    \"recipients\": [\"ops-team@company.com\"],
    \"exportFormat\": \"CSV\"
  }" | jq '{id, name}'
```

---

### PPDM System Diagnostics and Log Bundle API

```bash
# ── DOWNLOAD SUPPORT LOG BUNDLE ────────────────────────────────────
# Trigger log bundle generation
curl -sk -X POST https://<ppdm>:8443/api/v2/support-bundles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "includeSystemLogs": true,
    "includeActivityLogs": true,
    "daysBack": 7
  }' | jq '{bundleId: .id, status}'

# Poll for bundle readiness
curl -sk "https://<ppdm>:8443/api/v2/support-bundles/<bundle-id>" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{status, sizeBytes, createdAt}'

# Download the bundle
curl -sk "https://<ppdm>:8443/api/v2/support-bundles/<bundle-id>/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o ppdm-support-bundle.zip

# List past bundles
curl -sk https://<ppdm>:8443/api/v2/support-bundles \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, status, sizeBytes, createdAt}'

# ── SYSTEM UPGRADE API ─────────────────────────────────────────────
# Check current version
curl -sk https://<ppdm>:8443/api/v2/upgrade/current-version \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{version, buildDate, patchLevel}'

# List available upgrades
curl -sk https://<ppdm>:8443/api/v2/upgrade/available-versions \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {version, releaseDate, upgradeType}'

# Upload an upgrade package (multipart form upload)
curl -sk -X POST https://<ppdm>:8443/api/v2/upgrade/packages \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/ppdm-upgrade-19.16.pkg" \
  | jq '{packageId: .id, status}'

# Run pre-upgrade compatibility check
curl -sk -X POST https://<ppdm>:8443/api/v2/upgrade/precheck \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"packageId": "<package-id>"}' \
  | jq '{status, checks: [.checks[] | {name, result, message}]}'

# Start the upgrade (CAUTION: PPDM will restart)
curl -sk -X POST https://<ppdm>:8443/api/v2/upgrade/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"packageId": "<package-id>"}' \
  | jq '{upgradeId: .id, status}'

# Monitor upgrade progress
curl -sk "https://<ppdm>:8443/api/v2/upgrade/<upgrade-id>" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{status, percentComplete, currentStep, estimatedCompletion}'
```

---

### PPDM System Configuration API

Configure network settings, NTP, DNS, proxy, two-factor authentication, and manage API tokens.

```bash
# ── NETWORK CONFIGURATION ──────────────────────────────────────────
# Get current network settings
curl -sk https://<ppdm>:8443/api/v2/network-settings \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{hostname, ipAddress, gateway, netmask, dns, ntp}'

# Update DNS servers
curl -sk -X PATCH https://<ppdm>:8443/api/v2/network-settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dns": {
      "primary": "10.0.0.53",
      "secondary": "10.0.0.54",
      "searchDomains": ["corp.local", "backup.corp.local"]
    }
  }' | jq .

# Update NTP servers
curl -sk -X PATCH https://<ppdm>:8443/api/v2/network-settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ntp": {
      "servers": ["ntp1.corp.local", "ntp2.corp.local"],
      "syncEnabled": true
    }
  }' | jq .

# ── PROXY SETTINGS ─────────────────────────────────────────────────
# Configure HTTP proxy (for cloud tier / telemetry outbound traffic)
curl -sk -X PUT https://<ppdm>:8443/api/v2/proxy-settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "host": "proxy.corp.local",
    "port": 3128,
    "username": "proxy-user",
    "password": "<proxy-pass>",
    "noProxyHosts": ["10.0.0.0/8", "*.corp.local"]
  }' | jq .

# ── TWO-FACTOR AUTHENTICATION (2FA) ───────────────────────────────
# Get current 2FA settings
curl -sk https://<ppdm>:8443/api/v2/mfa-settings \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{enabled, provider, enforcedForAllUsers}'

# Enable 2FA with TOTP (authenticator app)
curl -sk -X PUT https://<ppdm>:8443/api/v2/mfa-settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "provider": "TOTP",
    "enforcedForAllUsers": true,
    "gracePeriodDays": 7
  }' | jq .

# Enroll a user in 2FA — returns QR code URI for authenticator app
curl -sk -X POST "https://<ppdm>:8443/api/v2/users/<user-id>/mfa-enrollment" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{qrCodeUri, secret}'

# Reset 2FA for a user (force re-enrollment)
curl -sk -X DELETE "https://<ppdm>:8443/api/v2/users/<user-id>/mfa-enrollment" \
  -H "Authorization: Bearer $TOKEN"

# ── TOKEN MANAGEMENT ───────────────────────────────────────────────
# Refresh an expiring token (default expiry: 10 minutes)
curl -sk -X POST https://<ppdm>:8443/api/v2/token/refresh \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{access_token, expires_in}'

# Revoke a token (force logout of a specific session)
curl -sk -X POST https://<ppdm>:8443/api/v2/token/revoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "<token-to-revoke>"}' | jq .

# List all active API tokens (service accounts / automation tokens)
curl -sk https://<ppdm>:8443/api/v2/tokens \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, createdBy, expiresAt, lastUsed}'

# Create a long-lived service account token (for automation pipelines)
curl -sk -X POST https://<ppdm>:8443/api/v2/tokens \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ci-pipeline-token",
    "expiresInDays": 365,
    "roleId": "<role-id>"
  }' | jq '{id, token, expiresAt}'

# Revoke a service account token
curl -sk -X DELETE "https://<ppdm>:8443/api/v2/tokens/<token-id>" \
  -H "Authorization: Bearer $TOKEN"

# ── TELEMETRY & PHONE HOME ─────────────────────────────────────────
# Get telemetry settings
curl -sk https://<ppdm>:8443/api/v2/telemetry-settings \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{enabled, proxyEnabled, lastSentAt}'

# Disable telemetry (air-gapped environments)
curl -sk -X PUT https://<ppdm>:8443/api/v2/telemetry-settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' | jq .
```

---

### PPDM Asset Tags and vProxy Management API

#### Asset Tags

Tags allow grouping and filtering assets across types, enabling tag-based protection rules and reporting.

```bash
# ── TAG MANAGEMENT ─────────────────────────────────────────────────
# List all tags
curl -sk https://<ppdm>:8443/api/v2/asset-tags \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, key, value, assetCount}'

# Create a tag
curl -sk -X POST https://<ppdm>:8443/api/v2/asset-tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key": "environment", "value": "production"}' \
  | jq '{id, key, value}'

# Assign tag to one or more assets
curl -sk -X POST https://<ppdm>:8443/api/v2/asset-tags/<tag-id>/assets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"assetIds": ["<asset-id-1>", "<asset-id-2>"]}' | jq .

# Query assets by tag
curl -sk "https://<ppdm>:8443/api/v2/assets?filter=tags.key%20eq%20%22environment%22%20and%20tags.value%20eq%20%22production%22" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, type}'

# Create protection rule based on tag (auto-assign tagged assets to policy)
curl -sk -X POST https://<ppdm>:8443/api/v2/protection-rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"tag-production-rule\",
    \"assetType\": \"VMWARE_VIRTUAL_MACHINE\",
    \"policyId\": \"$POLICY_ID\",
    \"conditions\": [
      {
        \"assetAttributeName\": \"tags.value\",
        \"operator\": \"EQUALS\",
        \"assetAttributeValue\": \"production\"
      }
    ],
    \"action\": \"MOVE_TO_POLICY\",
    \"priority\": 1
  }" | jq '{id, name}'

# Remove tag from asset
curl -sk -X DELETE "https://<ppdm>:8443/api/v2/asset-tags/<tag-id>/assets/<asset-id>" \
  -H "Authorization: Bearer $TOKEN"

# Delete tag entirely
curl -sk -X DELETE "https://<ppdm>:8443/api/v2/asset-tags/<tag-id>" \
  -H "Authorization: Bearer $TOKEN"
```

#### vSphere Proxy (vProxy) Management

vProxy is the PPDM vSphere data mover — it performs snapshot-based backups using VMware VADP. You can deploy multiple vProxies for load distribution.

```bash
# ── LIST VPROXIES ──────────────────────────────────────────────────
curl -sk https://<ppdm>:8443/api/v2/vproxies \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.content[] | {id, name, status, version, vcenter: .vcenterId, maxConcurrentSessions}'

# ── DEPLOY A NEW VPROXY ────────────────────────────────────────────
curl -sk -X POST https://<ppdm>:8443/api/v2/vproxies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "vproxy-01",
    "vcenterId": "<vcenter-inventory-source-id>",
    "datastore": "<datastore-name>",
    "network": "<portgroup-name>",
    "resourcePool": "<resource-pool>",
    "storageSystemId": "<dd-storage-system-id>",
    "maxConcurrentSessions": 8
  }' | jq '{id, name, status}'

# ── MONITOR VPROXY STATUS ──────────────────────────────────────────
curl -sk "https://<ppdm>:8443/api/v2/vproxies/<vproxy-id>" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{name, status, version, activeSessions, maxConcurrentSessions, lastHealthCheck}'

# ── UPDATE MAX SESSIONS (tune performance) ────────────────────────
curl -sk -X PATCH "https://<ppdm>:8443/api/v2/vproxies/<vproxy-id>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"maxConcurrentSessions": 12}' | jq '{id, name, maxConcurrentSessions}'

# ── UPGRADE VPROXY ────────────────────────────────────────────────
curl -sk -X POST "https://<ppdm>:8443/api/v2/vproxies/<vproxy-id>/upgrade" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '{activityId}'

# ── DELETE VPROXY ─────────────────────────────────────────────────
curl -sk -X DELETE "https://<ppdm>:8443/api/v2/vproxies/<vproxy-id>" \
  -H "Authorization: Bearer $TOKEN"
```

---

### NetWorker Storage Node, Device and Volume Management REST API

#### Storage Nodes

```bash
# List all storage nodes
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/storagenodes \
  -u admin:<pass> \
  | jq '.storageNodes[] | {id, hostname, enabled, status, comment}'

# Create a storage node
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/storagenodes \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "<storage-node-host>",
    "comment": "Secondary storage node — Site B",
    "enabled": true,
    "targetSessions": 16,
    "maxSessions": 60
  }' | jq .

# Update storage node max sessions
curl -sk -X PUT "https://<nw-server>:9090/nwrestapi/v3/global/storagenodes/<id>" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{"maxSessions": 80, "enabled": true}' | jq .

# Delete storage node
curl -sk -X DELETE "https://<nw-server>:9090/nwrestapi/v3/global/storagenodes/<id>" \
  -u admin:<pass>
```

#### Devices

```bash
# List all devices
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/devices \
  -u admin:<pass> \
  | jq '.devices[] | {id, name, mediaType, status, enabled, storageNode}'

# Create a new AFTD (Advanced File Type Device — disk backup target)
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/devices \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AFTD-01",
    "deviceAccessInformation": "/nsr/aftd/AFTD-01",
    "mediaType": "file",
    "targetSessions": 8,
    "maxSessions": 32,
    "enabled": true,
    "comment": "Local AFTD on storage node"
  }' | jq .

# Enable / disable a device
curl -sk -X PATCH "https://<nw-server>:9090/nwrestapi/v3/global/devices/<id>" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' | jq .

# Delete a device
curl -sk -X DELETE "https://<nw-server>:9090/nwrestapi/v3/global/devices/<id>" \
  -u admin:<pass>

# CLI equivalents
nsradmin> print type: NSR device                         # list all devices
nsradmin> update type: NSR device; name: AFTD-01; enabled: No;
nsradmin> delete type: NSR device; name: AFTD-01;
```

#### Volume Management

```bash
# List volumes (media instances)
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/volumes \
  -u admin:<pass> \
  | jq '.volumes[] | {id, name, pool, device, status, percentFull, writeable}'

# Get a specific volume
curl -sk "https://<nw-server>:9090/nwrestapi/v3/global/volumes/<id>" \
  -u admin:<pass> | jq .

# Label a new volume (initialise media)
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/volumes \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "device": "AFTD-01",
    "pool": "Gold-DD-Pool",
    "label": "GLD-0001",
    "retentionPeriod": {"amount": 30, "unit": "Days"}
  }' | jq .

# Mount a volume on a device
curl -sk -X POST "https://<nw-server>:9090/nwrestapi/v3/global/volumes/<id>/op/mount" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{"device": "AFTD-01"}' | jq .

# Unmount a volume
curl -sk -X POST "https://<nw-server>:9090/nwrestapi/v3/global/volumes/<id>/op/unmount" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

# Mark volume as full (prevent further writes)
curl -sk -X PATCH "https://<nw-server>:9090/nwrestapi/v3/global/volumes/<id>" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{"writeable": false}' | jq .

# Expire a volume (release for relabelling)
curl -sk -X DELETE "https://<nw-server>:9090/nwrestapi/v3/global/volumes/<id>" \
  -u admin:<pass>

# CLI equivalents
mminfo -s <server> -mv                         # list all volumes with detail
nsrmm -s <server> -e tomorrow <vol-name>       # set expiry to tomorrow
nsrmm -s <server> -o full <vol-name>           # mark volume full
nsrmm -s <server> -d <vol-name>                # delete expired volume
```

---

### NetWorker Client Properties, Lockbox and Server Statistics API

#### Client Properties

Client-level tuning controls backup parallelism, network encryption, and compression.

```bash
# Get full client resource properties
curl -sk "https://<nw-server>:9090/nwrestapi/v3/global/clients/<id>" \
  -u admin:<pass> \
  | jq '{name, parallelism, compression, encryption, backupRename, directive}'

# Update client parallelism (concurrent save streams per client)
curl -sk -X PATCH "https://<nw-server>:9090/nwrestapi/v3/global/clients/<id>" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{"parallelism": 8}' | jq .

# Enable client-side encryption
curl -sk -X PATCH "https://<nw-server>:9090/nwrestapi/v3/global/clients/<id>" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "encryption": "aes 256 cbc",
    "comment": "Encryption enabled per security policy"
  }' | jq .

# Disable client (skip in backup but retain resource)
curl -sk -X PATCH "https://<nw-server>:9090/nwrestapi/v3/global/clients/<id>" \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{"backupEnabled": false}' | jq .

# nsradmin equivalents
nsradmin> update type: NSR client; name: <host>;
          parallelism: 8;
          encryption: aes 256 cbc;
          backup enabled: Yes;
```

#### Lockbox Management

The NetWorker lockbox stores encrypted client credentials and certificates used for agent-to-server authentication.

```bash
# List lockbox entries
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/lockbox \
  -u admin:<pass> \
  | jq '.lockboxEntries[] | {hostname, type, status}'

# Re-register a client certificate in the lockbox (after client cert rotation)
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/lockbox \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "<client-hostname>",
    "action": "refresh"
  }' | jq .

# Remove a stale lockbox entry (after decommissioning a client)
curl -sk -X DELETE "https://<nw-server>:9090/nwrestapi/v3/global/lockbox/<hostname>" \
  -u admin:<pass>

# CLI equivalent — re-authenticate client from server side
nsrauth -s <nw-server> -c <client-hostname>
# Or from the client side:
nsrauthtrust -H <nw-server>
```

#### Server Performance Statistics

```bash
# Get NetWorker server throughput and session statistics
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/stats \
  -u admin:<pass> \
  | jq '{activeSessions, queuedSessions, throughputMBps, cpuUsagePercent}'

# Get per-device performance
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/devices/stats \
  -u admin:<pass> \
  | jq '.deviceStats[] | {device, readMBps, writeMBps, activeSessions}'

# Get index size and media database stats
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/serverinfo \
  -u admin:<pass> \
  | jq '{serverName, version, indexSizeGB, mediaDatabaseSizeGB, uptime}'

# Historical activity summary (last N days)
curl -sk "https://<nw-server>:9090/nwrestapi/v3/global/activities?startTime=<ISO-date>&endTime=<ISO-date>" \
  -u admin:<pass> \
  | jq '[.activities[] | {name, status, startTime, endTime, sizeSaved}]'
```

---

### NetWorker NDMP and Bootstrap/Disaster Recovery

#### NDMP (Network Data Management Protocol)

NDMP enables direct backup of NAS filers (NetApp, Isilon) without routing data through a NetWorker storage node.

```bash
# ── NDMP CLIENT CONFIGURATION ─────────────────────────────────────
# Create an NDMP-enabled client resource
nsradmin -s <nw-server>
nsradmin> create type: NSR client;
  name: <nas-filer-hostname>;
  backup type: NDMP;
  username: root;
  NDMP multistream: Yes;
  save set: /vol/vol0 /vol/data;

# NDMP save paths follow NAS volume naming:
# NetApp:   /vol/<volume-name>
# Isilon:   /ifs/<path>

# ── NDMP VIA REST API ─────────────────────────────────────────────
# Create NDMP client
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/clients \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "<nas-filer>",
    "backupType": "NDMP",
    "ndmpProperties": {
      "username": "root",
      "password": "<ndmp-pass>",
      "multistreamEnabled": true,
      "dmaEnabled": false
    },
    "saveSets": ["/vol/vol0", "/vol/data"]
  }' | jq '{id, hostname}'

# Verify NDMP connectivity from storage node
nsrndmp_save -s <nw-server> -c <nas-filer> -T ndmp -N /vol/vol0 -l full

# ── NDMP THREE-WAY BACKUP ─────────────────────────────────────────
# Three-way: NAS filer → storage node → device (data never touches NW server)
nsradmin> create type: NSR client;
  name: <nas-filer>;
  backup type: NDMP;
  storage nodes: <storage-node-host>;
  NDMP multistream: Yes;
```

#### Bootstrap Backup and Disaster Recovery

The **bootstrap** is a critical NetWorker save set that captures the server's media database, resource database, and index — required to recover a NetWorker server from scratch.

```bash
# ── BOOTSTRAP BACKUP ──────────────────────────────────────────────
# NetWorker automatically backs up the bootstrap daily
# Force an immediate bootstrap backup
savegrp -O -G "Default" -c <nw-server>   # runs full server-level save

# Locate the most recent bootstrap save set ID
mminfo -s <nw-server> -q "savetime>last week" \
  -r "ssid,savetime(22),sumsize" \
  -N "bootstrap"

# Note the SSID and media label printed — write these down for DR

# ── BOOTSTRAP RESTORE (disaster recovery) ─────────────────────────
# Step 1 — install NetWorker on the replacement server (same version)
# Step 2 — recover the media database and resource database

nsrdr -s <nw-server>    # interactive disaster recovery wizard (Linux)

# Or manually:
# 2a. Mount the media containing the bootstrap save set
# 2b. Run scanner to rebuild media database
scanner -s <nw-server> -m <volume-label>

# 2c. Recover the bootstrap save set
nsrrecover -s <nw-server> -S <bootstrap-ssid> -d /nsr

# 2d. Restart NetWorker daemons
systemctl restart networker

# ── BOOTSTRAP VIA REST API ────────────────────────────────────────
# Trigger manual bootstrap backup
curl -sk -X POST https://<nw-server>:9090/nwrestapi/v3/global/op/backupbootstrap \
  -u admin:<pass> \
  -H "Content-Type: application/json" \
  -d '{}' | jq '{jobId: .id}'

# Get the most recent bootstrap info
curl -sk https://<nw-server>:9090/nwrestapi/v3/global/bootstrap \
  -u admin:<pass> \
  | jq '{ssid, saveTime, volumeLabel, device, sizeBytes}'
```

---

### Data Domain Encryption, User Management, SNMP and Syslog API

#### Filesystem Encryption at Rest

```bash
# ── CHECK ENCRYPTION STATUS ────────────────────────────────────────
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/filesystems/0/encryption \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{status, algorithm, keyManagement, tierStatus}'

# Enable encryption at rest (CAUTION: requires filesystem restart)
curl -sk -X PUT https://<dd-host>:3009/rest/v1.0/dd-systems/0/filesystems/0/encryption \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "enabled",
    "algorithm": "AES256-GCM",
    "keyManagement": "DEFAULT"
  }' | jq .

# Integrate with external key manager (KMIP — e.g. Vormetric, SafeNet)
curl -sk -X PUT https://<dd-host>:3009/rest/v1.0/dd-systems/0/filesystems/0/encryption \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "enabled",
    "algorithm": "AES256-GCM",
    "keyManagement": "KMIP",
    "kmipServer": "<kmip-host>",
    "kmipPort": 5696,
    "kmipCertificate": "<base64-cert>"
  }' | jq .

# List encryption key tiers and rotation status
curl -sk "https://<dd-host>:3009/rest/v1.0/dd-systems/0/filesystems/0/encryption/keys" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.keys[] | {id, tier, created, lastRotated, status}'

# Rotate encryption keys
curl -sk -X POST \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/filesystems/0/encryption/keys/rotate" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" | jq .
```

#### Full DD User Management

```bash
# List all system users
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/users \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.users[] | {name, role, enabled, "last-login"}'

# DD user roles:
# sysadmin    — full administrative access
# admin       — most admin tasks, cannot change sysadmin password
# user        — read-only monitoring
# backup-operator — manage backup jobs, no system config
# none        — used for DDBoost-only accounts

# Create a system user
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/users \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "backup-ops",
    "password": "<pass>",
    "role": "backup-operator"
  }' | jq .

# Change user password
curl -sk -X PUT "https://<dd-host>:3009/rest/v1.0/dd-systems/0/users/backup-ops/password" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old-password": "<old>", "new-password": "<new>"}' | jq .

# Disable a user account
curl -sk -X PUT "https://<dd-host>:3009/rest/v1.0/dd-systems/0/users/backup-ops" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' | jq .

# Delete a user
curl -sk -X DELETE "https://<dd-host>:3009/rest/v1.0/dd-systems/0/users/backup-ops" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN"

# CLI equivalent
ddsh> user add <name> role <role>
ddsh> user change password <name>
ddsh> user disable <name>
ddsh> user delete <name>
ddsh> user show list
```

#### SNMP Configuration

```bash
# Get SNMP settings
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/snmp \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{status, version, "trap-hosts", "community-string"}'

# Enable SNMPv3
curl -sk -X PUT https://<dd-host>:3009/rest/v1.0/dd-systems/0/snmp \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "enabled",
    "version": "v3",
    "users": [
      {
        "name": "snmp-monitor",
        "auth-protocol": "SHA",
        "auth-password": "<auth-pass>",
        "priv-protocol": "AES128",
        "priv-password": "<priv-pass>"
      }
    ],
    "trap-hosts": [
      {"host": "<snmp-manager-ip>", "port": 162, "version": "v3", "user": "snmp-monitor"}
    ]
  }' | jq .

# Test SNMP trap (send test trap to manager)
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/snmp/test-trap \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" | jq .
```

#### Syslog Configuration

```bash
# List configured syslog destinations
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/syslog \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.hosts[] | {host, port, protocol, facility, severity}'

# Add a syslog destination
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/syslog \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "<siem-host>",
    "port": 514,
    "protocol": "UDP",
    "facility": "LOCAL0",
    "severity": "WARNING"
  }' | jq .

# Remove a syslog destination
curl -sk -X DELETE "https://<dd-host>:3009/rest/v1.0/dd-systems/0/syslog/<host>" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN"

# CLI equivalents
ddsh> log host add <host> port <port> protocol udp
ddsh> log host del <host>
ddsh> log host show
```

---

### Data Domain NFS/CIFS Shares and Deduplication Metrics API

#### NFS Exports

```bash
# List all NFS exports
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/nfs/exports \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.exports[] | {path, clients, options}'

# Create an NFS export for a DDBoost storage unit path
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/nfs/exports \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/data/col1/<su-name>",
    "clients": [
      {
        "name": "<nw-storage-node-ip>",
        "options": "sec=sys,rw,no_root_squash"
      },
      {
        "name": "10.0.0.0/24",
        "options": "sec=sys,ro"
      }
    ]
  }' | jq .

# Delete NFS export
curl -sk -X DELETE \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/nfs/exports/<path>" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN"

# CLI
ddsh> nfs export add /data/col1/<su-name> clients <ip>(sec=sys,rw,no_root_squash)
ddsh> nfs export show
```

#### CIFS Shares

```bash
# List CIFS shares
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/cifs/shares \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.shares[] | {name, path, comment, clients}'

# Enable CIFS service
curl -sk -X PUT https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/cifs \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "enabled"}' | jq .

# Create a CIFS share
curl -sk -X POST https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/cifs/shares \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nw-backup-share",
    "path": "/data/col1/<su-name>",
    "comment": "NetWorker AFTD target",
    "max-connections": 0,
    "clients": [{"name": "<backup-server-ip>", "access": "read-write"}]
  }' | jq .

# Delete CIFS share
curl -sk -X DELETE \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/cifs/shares/nw-backup-share" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN"
```

#### Deduplication and Compression Metrics

```bash
# ── GLOBAL DEDUP / COMPRESSION STATS ──────────────────────────────
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/stats/compression \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{
    "pre-comp-global": ."pre-comp-global",
    "post-comp-global": ."post-comp-global",
    "global-compression-factor": ."global-compression-factor",
    "local-compression-factor": ."local-compression-factor",
    "total-compression-factor": ."total-compression-factor"
  }'

# ── PER STORAGE UNIT STATS ─────────────────────────────────────────
curl -sk \
  "https://<dd-host>:3009/rest/v1.0/dd-systems/0/protocols/ddboost/storage-units/<su-name>/stats" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{
    "pre-comp-used",
    "post-comp-used",
    "compression-factor",
    "bytes-saved"
  }'

# ── HISTORICAL COMPRESSION TREND ──────────────────────────────────
curl -sk "https://<dd-host>:3009/rest/v1.0/dd-systems/0/stats/compression?duration=30days" \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '.samples[] | {timestamp, "compression-factor", "pre-comp-mb", "post-comp-mb"}'

# ── SPACE RECLAMATION ESTIMATE ─────────────────────────────────────
# Estimate how much space will be freed by next garbage collection
curl -sk https://<dd-host>:3009/rest/v1.0/dd-systems/0/filesystems/0/clean/estimate \
  -H "X-DD-AUTH-TOKEN: $DD_TOKEN" \
  | jq '{"estimated-bytes-freed", "last-clean-time", "clean-status"}'

# CLI equivalents
ddsh> filesys show compression                   # global dedup ratio
ddsh> ddboost storage-unit show compression <su> # per-SU ratio
ddsh> filesys clean start                        # run garbage collection
ddsh> filesys clean status                       # check clean progress
```

---

### API Port and Endpoint Summary

| System | Port | Base URL | Auth Method |
|---|---|---|---|
| PPDM | `8443` | `https://<ppdm>:8443/api/v2` | POST `/login` → Bearer token |
| NetWorker | `9090` | `https://<nw>:9090/nwrestapi/v3` | HTTP Basic (user:pass) |
| Data Domain | `3009` | `https://<dd>:3009/rest/v1.0` | POST `/auth` → `X-DD-AUTH-TOKEN` header |
| CloudBoost | `9000` | `https://<cb>:9000/api/v1` | HTTP Basic |
| Kubernetes API | `6443` | `https://<k8s>:6443` | Bearer token (ServiceAccount) |
| DD DDBoost data | `2052` | TCP (not HTTP) | DDBoost user credentials |
| DD VTL (FC) | N/A | Fibre Channel / iSCSI | Access group (WWPN zoning) |
| PPDM → Agent | `7000/7001` | TCP (not HTTP) | Certificate-based mutual TLS |
| LDAP/AD | `389/636` | `ldap://` or `ldaps://` | Bind DN + password |

---

## NetWorker vs PPDM — Quick Comparison

| Feature | NetWorker | PPDM |
|---|---|---|
| Management UI | NMC (Java) / REST | Modern web UI / REST |
| Policy model | Groups + schedules | Protection policies + rules |
| API style | REST v3 (port 9090) | REST v2 (port 8443) |
| Cloud support | CloudBoost add-on | Native (AWS, Azure, GCP) |
| Kubernetes | Limited | Native namespace protection |
| VMware | VADP proxy | Direct vCenter integration |
| Automation | nsradmin, CLI, REST | REST, PowerShell, Python SDK |

---

## Best Practices

- Always test restores — a backup is only as good as a verified recovery.
- Set browse retention shorter than media retention to control index growth.
- Use Data Domain Boost (DDBoost) wherever possible — better dedup + performance.
- In PPDM, use Protection Rules to auto-assign new assets — avoid manual policy assignment.
- Rotate PPDM `admin` credentials and store tokens securely; tokens expire after 10 minutes by default.
- Monitor SLA compliance daily via `GET /slas` or the PPDM dashboard.
- For large environments, filter `mminfo` queries with time ranges — unfiltered queries can be slow.
