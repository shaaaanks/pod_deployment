import subprocess
import json
import csv
import ast


def main():
    print('Starting')
    helm_list = subprocess.check_output(
        ['bash', '-c', 'helm list | grep -v NAME | awk \'{print $1}\'']).decode()
    helm_pods_list = get_helm_deployments_status(helm_list)
    all_pods_list = subprocess.check_output(
        ['bash', '-c', 'kubectl get pods --all-namespaces -o json | jq -r .items'])

    all_pods = json.loads(all_pods_list)

    helm_pods = get_helm_pods(helm_pods_list)

    csv_file = generate_csv_file(all_pods, helm_pods)

    print_csv_file(csv_file)


def get_helm_deployments_status(helm_list_output):
    print('Generating list of Helm Deployments')
    helm_list_results = []

    for pod_name in helm_list_output.splitlines():
        print('Getting status for Pod: ' + pod_name)
        helm_status = subprocess.check_output(
            ['bash', '-c', 'helm status ' + pod_name + ' --output json'])
        helm_status_json = json.loads(helm_status)
        helm_list_results.append(helm_status_json)

    return helm_list_results


def get_helm_pods(helm_deployments):
    helm_pods = []

    for deployment in helm_deployments:
        deployment_info = deployment['info']['status']
        copy = False

        if 'resources' in deployment_info:
            resources = deployment_info.get('resources')
            for line in resources.splitlines():
                if line.strip() == '':
                    copy = False

                if copy:
                    firstWord = line.split(' ', 1)[0]
                    if firstWord != 'NAME':
                        helm_pods.append(firstWord.encode('utf-8'))

                if line.strip() == '==> v1/Pod(related)':
                    copy = True

    return helm_pods


def generate_csv_file(all_pods, helm_pods):
    known_deployments = []
    print('Generating CSV output')
    print('Number of Pods to check: ', len(all_pods))
    csv_output = [['Name', 'Image', 'App', 'Created At', 'Deployment Method']]

    for pod in all_pods:
        if pod['metadata']['name'] in helm_pods:
            csv_item = [pod['metadata']['name'], pod['spec']['containers'][0]['image'],
                        pod['metadata']['labels']['app'], pod['metadata']['creationTimestamp'], 'Helm']
            csv_output.append(csv_item)
            known_deployments.append(pod)

    print('Number of Pods with known deployment: ', len(known_deployments))
    for pod in known_deployments:
        all_pods.remove(pod)

    for pod in all_pods:
        csv_item = [pod['metadata']['name'], pod['spec']['containers'][0]['image'],
                    '', pod['metadata']['creationTimestamp'], '']
        csv_output.append(csv_item)

    print('Pods not deployed via Helm: ', len(all_pods))

    return csv_output


def print_csv_file(csvFileContents):
    print('Writing CSV file')

    with open('helmlist.csv', 'w') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(csvFileContents)

    csvFile.close()


if __name__ == "__main__":
    main()
