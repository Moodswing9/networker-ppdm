# GitHub Copilot Instructions — NetWorker & PPDM

You are an expert in Dell EMC **NetWorker** and **PowerProtect Data Manager (PPDM)**. Use the reference below to assist with backup administration, REST API scripting, CLI operations, Kubernetes protection, Data Domain configuration, and troubleshooting.

---

## Port & Auth Quick Reference

| Product | Port | Auth Method | Base URL |
|---|---|---|---|
| PPDM REST API | 8443 | Bearer token (`POST /api/v2/login`) | `https://<ppdm>:8443/api/v2` |
| NetWorker REST API | 9090 | HTTP Basic (user:pass) | `https://<server>:9090/nwrestapi/v3` |
| Data Domain REST API | 3009 | Session token (`POST /rest/v1.0/auth`, header `X-DD-AUTH-TOKEN`) | `https://<dd>:3009/rest/v1.0` |
| DDBoost data path | 2052 | DDBoost user credentials | — |
| Kubernetes API | 6443 | ServiceAccount Bearer token | `https://<k8s-api>:6443` |

---

## PPDM REST API

### Authentication
```bash
# Get Bearer token
TOKEN=$(curl -sk -X POST https://<ppdm>:8443/api/v2/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<pass>"}' \
  | jq -r '.access_token')

# Use in all subsequent requests
-H "Authorization: Bearer $TOKEN"
```

### Core Endpoints
```bash
# Assets
GET  /assets                                         # list all assets
GET  /assets?filter=name%20eq%20%22<name>%22         # filter by name
GET  /assets/<id>
GET  /assets/<id>/copies                             # available backup copies

# Protection Policies
GET  /protection-policies
POST /protection-policies                            # create policy
POST /protection-policies/<id>/protections           # on-demand backup
POST /protection-policies/<id>/asset-assignments     # assign assets

# Protection Rules (auto-assignment)
GET  /protection-rules
POST /protection-rules

# Activities (jobs)
GET  /activities
GET  /activities?filter=state%20eq%20%22FAILED%22    # failed jobs
GET  /activities/<id>

# Restores
POST /restores

# Storage
GET  /storage-systems

# Inventory Sources (vCenter, k8s clusters, app hosts)
GET  /inventory-sources
POST /inventory-sources
POST /inventory-sources/<id>/discover

# Credentials
GET  /credentials
POST /credentials

# Alerts
GET  /alerts
POST /alerts/<id>/acknowledge

# RBAC
GET  /roles
GET  /users
POST /users

# SLA
GET  /slas
GET  /slas/<id>/compliance

# Reports
POST /reports/<id>/run
```

### Python — Auth + List Failed Jobs
```python
import requests
requests.packages.urllib3.disable_warnings()

BASE = "https://<ppdm>:8443/api/v2"

def get_token(user, password):
    r = requests.post(f"{BASE}/login",
                      json={"username": user, "password": password}, verify=False)
    r.raise_for_status()
    return r.json()["access_token"]

def get_failed_activities(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE}/activities",
                     headers=headers,
                     params={"filter": 'state eq "FAILED"', "pageSize": 100},
                     verify=False)
    r.raise_for_status()
    return r.json().get("content", [])
```

### Common Troubleshooting
| Problem | Action |
|---|---|
| Agent not connecting | Port 7000/7001 must be open; re-register agent from PPDM UI |
| Activity stuck "RUNNING" | `GET /activities/<id>` — check sub-task states; cancel if needed |
| vCenter assets not discovered | `POST /inventory-sources/<id>/discover` |
| Restore fails "no copy" | Verify retention: `GET /assets/<id>/copies` |
| DD storage full | `GET /storage-systems/<id>` — check `usedSize` vs `size` |

---

## NetWorker

### Core CLI
```bash
# Status & admin
nsrwatch                              # real-time activity monitor
nsradmin -s <server>                  # interactive admin shell

# Backup
savegrp -G <group>                    # run a group manually
save -s <server> -N <name> /path      # manual client save

# Query savesets
mminfo -s <server> -q "client=<host>" -r "ssid,name,level,savetime,sumsize"
mminfo -s <server> -q "savetime>last week" -r "client,name,level,savetime(22),sumsize"
nsrinfo -s <server> -c <client> /path # browse saveset contents

# Recover
recover -s <server> -c <client> -t <date>
nsrrecover -s <server> -c <client> /path

# Media
nsrjb -s <server> -I                  # inventory jukebox
nsrmm -s <server> -d <volume>         # delete/expire volume
nsrmm -s <server> -e <date> <vol>     # set expiry date

# Logs
nsr_render_log /nsr/logs/daemon.raw
```

### nsradmin Quick Reference
```
print type: NSR client; name: <hostname>
update type: NSR client; name: <host>; backup enabled: No;
create type: NSR label template; ...
delete type: NSR client; name: <host>
```

### NetWorker REST API
```bash
# Base URL: https://<server>:9090/nwrestapi/v3
# Auth: HTTP Basic

GET /global/clients
GET /global/savesets?q=clientId:<id>
POST /global/protectiongroups/<id>/op/backup
POST /global/recovers
{
  "sourceClient": "<client>",
  "destinationClient": "<client>",
  "saveSets": ["<ssid>"]
}
```

### Common Troubleshooting
| Problem | Action |
|---|---|
| Backup failed | `nsr_render_log /nsr/logs/daemon.raw` — search for client name |
| "no space left on device" | `mminfo -mv` — check volume utilization |
| Media waiting | `nsrwatch` → "waiting for media"; check device/pool mapping |
| Client not resolving | Check DNS, `/etc/hosts`, `nsrauth`/`nsrexecd` on client |
| License exceeded | `nsrlic -s <server>` |

---

## Kubernetes Protection with PPDM

PPDM deploys a **CDI (Container Data Integrator)** pod inside the cluster to capture namespace-scoped backups using VolumeSnapshots.

### 10-Step Setup

**Step 1 — Install VolumeSnapshot CRDs**
```bash
kubectl apply -f client/config/crd/                    # from kubernetes-csi/external-snapshotter
kubectl apply -f deploy/kubernetes/snapshot-controller/
kubectl get crd | grep snapshot                         # verify 3 CRDs present
```

**Step 2 — Create VolumeSnapshotClass**
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ppdm-snapclass
  annotations:
    snapshot.storage.kubernetes.io/is-default-class: "true"
deletionPolicy: Delete
driver: csi.vsphere.volume   # replace with your CSI driver
```

**Step 3 — Create PPDM ServiceAccount + RBAC**
```yaml
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
```

```bash
# Extract token
kubectl get secret powerprotect-admin-token \
  -n powerprotect \
  -o jsonpath='{.data.token}' | base64 --decode
```

**Step 4 — Register Cluster in PPDM**
```bash
curl -sk -X POST https://<ppdm>:8443/api/v2/inventory-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "KUBERNETES",
    "name": "prod-k8s-cluster",
    "address": "<k8s-api-server>",
    "port": 6443,
    "credentials": {"type": "TOKEN", "token": "<sa-token>"},
    "details": {"k8s": {"caCertificate": "<base64-ca-cert>"}}
  }'
```

**Step 5 — Discover Assets**
```bash
POST /inventory-sources/<id>/discover
GET  /assets?filter=type%20eq%20%22K8S_NAMESPACE%22
```

**Step 6 — Create Protection Policy**
```json
{
  "name": "k8s-daily-policy",
  "assetType": "KUBERNETES",
  "type": "ACTIVE",
  "dataConsistency": "CRASH_CONSISTENT",
  "stages": [{
    "type": "PROTECTION",
    "retention": {"unit": "DAY", "interval": 30},
    "target": {"storageSystemId": "<dd-id>", "dataTargetWithDdBoost": true},
    "operations": [{
      "type": "AUTO_FULL",
      "schedule": {"frequency": "DAILY", "startTime": "02:00"}
    }]
  }]
}
```

**Step 7 — Assign Namespaces**
```bash
POST /protection-policies/<id>/asset-assignments
{"assetIds": ["<namespace-asset-id>"]}

# Or use Protection Rules for auto-assignment:
POST /protection-rules
{"name":"k8s-auto-assign","assetType":"KUBERNETES","policyId":"<id>",
 "conditions":[{"assetAttributeName":"type","operator":"EQUALS","assetAttributeValue":"K8S_NAMESPACE"}]}
```

**Step 8 — On-Demand Backup**
```bash
POST /protection-policies/<id>/protections
{"assetIds":["<ns-id>"],"stages":[{"type":"PROTECTION"}]}
```

**Step 9 — Restore**
```bash
# List copies
GET /assets/<id>/copies

# Restore to original
POST /restores
{"copyId":"<id>","restoreType":"TO_ORIGINAL","options":{"k8s":{"restorePVCs":true}}}

# Restore to new namespace
{"copyId":"<id>","restoreType":"TO_NEW","options":{"k8s":{"targetNamespace":"<ns>","targetClusterId":"<id>"}}}
```

**Step 10 — Monitor**
```bash
kubectl get pods -n powerprotect           # CDI pod health
kubectl get volumesnapshots --all-namespaces
GET /activities?filter=state%20eq%20%22FAILED%22%20and%20assetType%20eq%20%22KUBERNETES%22
```

### K8s Troubleshooting
| Problem | Cause | Fix |
|---|---|---|
| `NO_SNAPSHOT_CLASS` | No default VolumeSnapshotClass | Add `snapshot.storage.kubernetes.io/is-default-class: "true"` |
| CDI pod Pending | Resource constraints | `kubectl describe pod -n powerprotect <cdi-pod>` |
| Discovery returns nothing | RBAC or API server unreachable | Verify ServiceAccount token; test API server reachability |
| PVC restore fails — StorageClass not found | Missing StorageClass in target | Create matching StorageClass before restoring |
| CDI can't reach Data Domain | Network policy blocking port 2052 | Add egress NetworkPolicy from `powerprotect` namespace to DD IP:2052 |

---

## DDBoost (Data Domain Boost)

### Data Domain CLI
```bash
ddsh> ddboost enable
ddsh> ddboost status
ddsh> user add <ddboost-user> role none
ddsh> ddboost user assign <ddboost-user> read-write
ddsh> ddboost storage-unit create <su-name> user <ddboost-user>
ddsh> ddboost storage-unit list
ddsh> ddboost option set encryption-strength medium
```

### Data Domain REST API (port 3009)
```bash
# Auth
DD_TOKEN=$(curl -sk -X POST https://<dd>:3009/rest/v1.0/auth \
  -H "Content-Type: application/json" \
  -d '{"username":"sysadmin","password":"<pass>"}' | jq -r '.token')

# All requests: -H "X-DD-AUTH-TOKEN: $DD_TOKEN"

# DDBoost status
GET  /dd-systems/0/protocols/ddboost

# Enable DDBoost
PUT  /dd-systems/0/protocols/ddboost
{"status": "enabled"}

# Storage units
GET  /dd-systems/0/protocols/ddboost/storage-units
POST /dd-systems/0/protocols/ddboost/storage-units
{"name":"<su-name>","user":"<ddboost-user>"}

# Filesystem stats
GET  /dd-systems/0/filesystems

# VTL
GET  /dd-systems/0/protocols/vtl/libraries
POST /dd-systems/0/protocols/vtl/libraries
GET  /dd-systems/0/protocols/vtl/access-groups
POST /dd-systems/0/protocols/vtl/access-groups

# Replication
GET  /dd-systems/0/replication
POST /dd-systems/0/replication/contexts

# Encryption
GET  /dd-systems/0/encryption
PUT  /dd-systems/0/encryption
{"state":"enabled","tier":"internal"}

# Users
GET  /dd-systems/0/users
POST /dd-systems/0/users
```

### Register Data Domain with PPDM (DDBoost)
```bash
POST /api/v2/storage-systems
{
  "name": "dd-prod",
  "type": "DATA_DOMAIN_SYSTEM",
  "address": "<dd-hostname>",
  "port": 3009,
  "credentials": {"username":"<ddboost-user>","password":"<pass>"},
  "details": {
    "dataDomain": {
      "preferredInterface": "DDBoost",
      "ddboostUser": "<ddboost-user>"
    }
  }
}
```

---

## Database Protection (PPDM)

### Oracle
```json
{
  "assetType": "ORACLE",
  "stages": [{
    "operations": [{
      "backupOptions": {
        "oracleBackupOptions": {
          "backupMode": "ARCHIVELOG",
          "rmanChannels": 4,
          "archiveLogRetentionHours": 48
        }
      },
      "dataConsistency": "APPLICATION_CONSISTENT"
    }]
  }]
}
```

### SQL Server
```json
{
  "assetType": "MICROSOFT_SQL_SERVER",
  "stages": [{
    "operations": [{
      "backupOptions": {
        "mssqlBackupOptions": {
          "backupType": "FULL",
          "differentialBackup": true,
          "logBackupIntervalMinutes": 15
        }
      }
    }]
  }]
}
```

### SAP HANA
```json
{
  "assetType": "SAP_HANA",
  "stages": [{
    "operations": [{
      "backupOptions": {
        "hanaBackupOptions": {
          "backupPrefix": "PPDM_BACKUP",
          "logBackup": true
        }
      }
    }]
  }]
}
```

---

## CloudBoost

```bash
# Register CloudBoost appliance with NetWorker
POST /global/devices
{
  "deviceType": "CloudBoost",
  "deviceName": "<name>",
  "cloudBoostAddress": "<appliance-ip>"
}

# AWS S3 cloud profile
POST /cloudboost/profiles
{
  "type": "aws",
  "bucket": "<bucket-name>",
  "region": "us-east-1",
  "accessKeyId": "<key>",
  "secretAccessKey": "<secret>"
}

# Azure Blob cloud profile
{
  "type": "azure",
  "storageAccountName": "<account>",
  "containerName": "<container>",
  "storageAccountKey": "<key>"
}
```

---

## Cross-Product Reference

| Capability | NetWorker | PPDM |
|---|---|---|
| Primary interface | CLI + REST (port 9090) | REST API (port 8443) |
| Auth | HTTP Basic | Bearer token |
| Policy hierarchy | Group → Policy → Workflow → Action | Protection Policy → Stage → Operation |
| Kubernetes support | Via CDI integration | Native (preferred) |
| DB agent | NetWorker Module for DB (NMM) | TSDM App Agent |
| Storage | AFTD, tape, DD, CloudBoost | Data Domain (DDBoost), cloud tier |
| On-demand backup CLI | `savegrp -G <group>` | `POST /protection-policies/<id>/protections` |

---

## General Troubleshooting

| Symptom | Product | Check |
|---|---|---|
| Backup failed | NetWorker | `nsr_render_log /nsr/logs/daemon.raw` |
| Agent offline | PPDM | Port 7000/7001; re-register from UI |
| DD storage full | Both | `GET /storage-systems/<id>` or `ddsh filesystem show space` |
| Rate limit 429 | PPDM API | Implement retry with 65s backoff; use prompt caching for large payloads |
| Restore "no copy" | PPDM | `GET /assets/<id>/copies` — check retention not expired |
| SLA breach | PPDM | Review policy schedule; check `GET /slas/<id>/compliance` |
| Stale lockbox | NetWorker | Re-auth client with `nsraddadmin`; check `nsrpolicy` |
