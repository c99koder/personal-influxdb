## Secrets
The Kubernetes manifests here are pretty straight forward.  I personally use [external-secrets](https://external-secrets.io/v0.8.5/) with [doppler.com](https://doppler.com) to manage my secrets outside the cluster, but you can use a regular old kubernetes secret if you want.  I've included examples for both.  Obviously depending on which python file you're using and how you modify the config.py, you may need to rename/change/add/delete from here.

Simply use the secret/external-secret examples as a starting point, and then apply with `kubectl apply -f secret.yaml` and you should be good to go.

## Cron Job
The cronjob example runs the image at a preset time.  I have mine currently set to run every hour, where it grabs librelinkup data for my pet's blood sugar monitor.  You can customize as necessary, then same as the secret, deploy with `kubectl apply -f cronjob.yaml` or your favorite automation tool of choice.  I use ArgoCD and have a manifest for that to deploy  into my cluster.


> Written with [StackEdit](https://stackedit.io/).