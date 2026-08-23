# Scoped access policy for the Epoch-1 deployment

Founder access ruling, 2026-08-19: Claude Code owns the deployment
end-to-end, with permissions **scoped to Earth-1's two infrastructure
hosts and the checked-in `ops/alive` workflow** — explicitly *not* a
generic unrestricted root wildcard.

> Rejected as a permanent policy: `ssh root@167.233.77.48 *`
>
> Production access is necessary. Uncontrolled permanent root execution
> is a different thing, and adopting it to remove session friction
> would be trading a standing capability for a moment's convenience.

## The rules to install

Place in `.claude/settings.json` of this repository (project-scoped, so
the grant travels with Earth-1 and not with the operator's account).

```json
{
  "permissions": {
    "allow": [
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 systemctl:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 journalctl:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 git:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 sha256sum:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 ls:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 df:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 tail:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 head:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 find:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 install:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 mkdir:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 python3:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48 /opt/earth1/ops/alive/:*)",
      "Bash(ssh -i ~/.ssh/earth1_hetzner -p 23 u652120@u652120.your-storagebox.de:*)",
      "Bash(rsync:*)"
    ]
  }
}
```

### Why these and no more

| capability | why it is needed | why it is bounded |
|---|---|---|
| `systemctl`, `journalctl` | stop/start/inspect `earth1-alive.service`; read the startup provenance record | no shell, no package management |
| `git` | check out the frozen tag, make the Epoch-0 preservation commit | inspection + checkout only |
| `sha256sum`, `ls`, `df`, `tail`, `head`, `find` | the verification gates — the deployment is mostly *checking*, not changing | read-only |
| `install`, `mkdir` | place the checked-in unit files and `DEPLOYED` | targets are in the repo |
| `python3` | load a snapshot through the canonical loader to prove it is a civilization | the loader is checked in |
| `ops/alive/*` | run the checked-in backup and restore-rehearsal tooling | those scripts are reviewed code, not ad-hoc commands |
| Storage Box ssh, `rsync` | off-site memory for `data/alive/` | one host, one directory tree |

Deliberately **not** granted: `rm`, `dd`, `mkfs`, `chmod -R`, package
managers, arbitrary shell (`sh -c`, `bash -c`), or any wildcard that
would permit them. Nothing in the twelve deployment steps needs them.
Retention pruning inside `run_backup.sh` is reviewed, checked-in code
rather than an interactive delete.

## Frozen deployment target

```
v1-persistence-deploy-1  ->  ae65bcd
```

Do not move it. Later commits on `v1-unification` are documentation and
tests only; the code at the tag is complete.

## Standing constraint

Do not begin 0.0a until production acceptance is green. The first hard
gate is that the complete 4M `data/alive/` civilization exists off-box
with independently verified hashes **before** the canonical daemon is
stopped. If any verification fails: stop before mutation, diagnose, fix
the cause.
