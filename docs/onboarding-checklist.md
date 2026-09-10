# New Engineer Onboarding Checklist

## Repository access
Request access to the platform-team GitHub org and the internal package registry before your
first day. Access requests typically take 24-48 hours to approve, so file them as early as
possible.

## Local environment setup
1. Install the required CLI tools: kubectl, the Argo CD CLI, and Helm.
2. Clone the workload repository and run the bootstrap script (`./scripts/bootstrap.sh`).
3. Configure your kubeconfig against the shared development cluster.
4. Verify access by running `kubectl get applications -n argocd` â you should see a list of
   Argo CD Application resources for the dev environment.

## First-week tasks
- Shadow an on-call rotation to see how incidents get triaged.
- Read the incident-response runbook end to end before touching production configuration.
- Submit a small, low-risk pull request against a dev overlay to get familiar with the review
  process.

## Common blockers
New engineers most often get stuck on kubeconfig context switching (mixing up dev/staging/prod
contexts) and on Kustomize overlay precedence (not realizing a patch in an overlay silently
overrides a value from the base). Both are covered in the debugging guide.
