# networker-ppdm

A comprehensive Claude Code skill for Dell EMC **NetWorker** and **PowerProtect Data Manager (PPDM)** — covering backup/restore operations, Kubernetes protection, database agents, REST APIs, CLI commands, troubleshooting, and automation.

## What's covered

| Product | Areas |
|---|---|
| **PPDM REST API** | Assets, policies, protection rules, activities, restores, SLA compliance, alerts, credentials, users & RBAC, LDAP/AD, reports, system config, cloud tier, replication, copies management, NAS, VMware, Kubernetes, database protection (Oracle / SQL Server / SAP HANA), vProxy, tags, diagnostics, upgrade |
| **NetWorker REST API + CLI** | Clients, savesets, backup/restore, policy/workflow/actions, clone, storage nodes, devices, volumes, directives, notifications, NDMP, bootstrap/DR, lockbox, client properties, server statistics |
| **Data Domain REST API + CLI** | DDBoost, storage units, VTL, cloud tier, NFS/CIFS shares, encryption at rest, user management, SNMP, syslog, replication, dedup/compression metrics, filesystem maintenance |
| **CloudBoost** | Appliance registration, AWS S3 / Azure Blob cloud profiles, NetWorker device integration |
| **Kubernetes** | Full 10-step PPDM protection guide — CDI, VolumeSnapshot, RBAC, policy, restore, monitoring |

## Install

```bash
npx skills add Moodswing9/networker-ppdm -g
```

## Usage

Once installed, the skill activates automatically in Claude Code when you ask questions about NetWorker, PPDM, Data Domain, or backup/restore operations.

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- `npx` (Node.js)

## License

MIT
