# Incident Response Runbook

## Severity levels
- **Sev1**: production outage or data-loss risk. Page on-call immediately.
- **Sev2**: significant degradation, no full outage. Notify the team channel and begin triage
  within 15 minutes.
- **Sev3**: minor issue, no customer impact. Log it and address during business hours.

## Triage steps
1. Confirm the alert is real: check the relevant dashboard, not just the alert text.
2. Identify the affected environment (dev / staging / production) and the affected service.
3. Check recent deploys: `kubectl rollout history deployment/<service> -n <namespace>`. Most
   incidents trace back to a change in the last 24 hours.
4. If a recent deploy is the likely cause, roll back first and investigate after service is
   restored â don't debug forward during an active Sev1.
5. Check Argo CD sync status for the affected Application. An out-of-sync or failed sync can
   leave a service running a stale or partially-applied configuration.

## Rollback procedure
- Via Argo CD: select the previous healthy sync in the Application's history view and click
  "Rollback."
- Via kubectl (if Argo CD itself is degraded): `kubectl rollout undo deployment/<service> -n
  <namespace>`.

## After the incident
Write a short post-incident note: what broke, how it was caught, how it was fixed, and one
concrete follow-up action. Keep it under a page â a long post-mortem nobody reads is worse than
a short one everybody does.
