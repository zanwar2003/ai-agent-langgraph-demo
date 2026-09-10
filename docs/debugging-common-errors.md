# Debugging Common Errors

## "ImagePullBackOff" on a new deployment
Almost always one of: the image tag doesn't exist yet (a build is still in flight), the cluster's
service account lacks pull access to the private registry, or the overlay is pointing at the
wrong registry path. Check `kubectl describe pod <pod>` for the exact pull error before assuming
which one it is.

## Kustomize overlay not applying as expected
Overlay precedence bites almost everyone at least once: a patch defined in an overlay silently
wins over the same field defined in the base, with no warning. Run `kustomize build
overlays/<env>` locally and diff the rendered output against what you expected before pushing â
don't debug this by trial and error against a live cluster.

## Argo CD Application stuck "OutOfSync"
Check whether auto-sync is disabled for that Application first â a surprising number of "stuck"
syncs are just waiting for a manual sync trigger. If auto-sync is on and it's still not
converging, check the Application's `Diff` view for a field a validating admission webhook is
rejecting silently.

## Secrets not resolving in a pod
If a pod can't find an expected environment variable or mounted secret, check the
ExternalSecret's status first (`kubectl describe externalsecret <name> -n <namespace>`) before
assuming the value is wrong in the secret store â a misconfigured ExternalSecret that never
synced looks identical to a missing value from the pod's perspective.
