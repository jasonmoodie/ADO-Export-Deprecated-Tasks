import requests
import json
from requests.auth import HTTPBasicAuth

# Configuration
ADO_ORG = "my-organization"  # Replace with your Azure DevOps organization name
ADO_PAT = "my-personal-access-token"  # Replace with your PAT
OUTPUT_FILE = "deprecated_tasks.json"

# Azure DevOps REST API endpoints
TASKS_URL = f"https://dev.azure.com/{ADO_ORG}/_apis/distributedtask/tasks?api-version=7.1-preview.1"
PROJECTS_URL = f"https://dev.azure.com/{ADO_ORG}/_apis/projects?api-version=7.1"

def get_all_projects():
    response = requests.get(PROJECTS_URL, auth=HTTPBasicAuth('', ADO_PAT))
    response.raise_for_status()
    return response.json().get('value', [])

def get_project_build_definitions(project_name):
    url = f"https://dev.azure.com/{ADO_ORG}/{project_name}/_apis/build/definitions?api-version=7.1"
    response = requests.get(url, auth=HTTPBasicAuth('', ADO_PAT))
    if response.status_code == 200:
        return response.json().get('value', [])
    return []

def get_build_definition_detail(project_name, definition_id):
    url = f"https://dev.azure.com/{ADO_ORG}/{project_name}/_apis/build/definitions/{definition_id}?api-version=7.1"
    response = requests.get(url, auth=HTTPBasicAuth('', ADO_PAT))
    if response.status_code == 200:
        return response.json()
    return None

def check_definition_for_deprecated_task(definition, deprecated_task_versions):
    """Check if a build definition uses any deprecated task versions"""
    if not definition:
        return []
    
    found_deprecated = []
    
    # Check process for classic pipelines
    if 'process' in definition and isinstance(definition['process'], dict):
        phases = definition['process'].get('phases', [])
        for phase in phases:
            for step in phase.get('steps', []):
                task_info = step.get('task', {})
                task_id = task_info.get('id')
                task_version = f"{task_info.get('versionSpec', 'unknown')}"
                
                # Check if this task/version combo is deprecated
                for dep_task in deprecated_task_versions:
                    if (dep_task['id'] == task_id and 
                        dep_task['major_version'] == task_info.get('versionSpec', '').split('.')[0]):
                        found_deprecated.append({
                            'task_name': dep_task['name'],
                            'version_used': task_version,
                            'pipeline_name': definition.get('name', 'Unknown')
                        })
    
    return found_deprecated

def get_all_tasks():
    response = requests.get(TASKS_URL, auth=HTTPBasicAuth('', ADO_PAT))
    response.raise_for_status()
    return response.json().get('value', [])

def filter_deprecated_versions(tasks):
    """Group tasks by ID and identify deprecated versions"""
    task_groups = {}
    
    # Group tasks by ID
    for task in tasks:
        task_id = task.get('id')
        if task_id not in task_groups:
            task_groups[task_id] = []
        task_groups[task_id].append(task)
    
    deprecated_versions = []
    
    for task_id, versions in task_groups.items():
        # Sort by major version descending
        versions.sort(key=lambda x: x.get('version', {}).get('major', 0), reverse=True)
        
        # Check each version for deprecation flag OR if it's not the latest major version
        latest_major = versions[0].get('version', {}).get('major', 0)
        
        for version in versions:
            is_deprecated = (
                version.get('deprecated', False) or 
                version.get('version', {}).get('major', 0) < latest_major
            )
            
            if is_deprecated:
                deprecated_versions.append({
                    'id': task_id,
                    'name': version.get('name'),
                    'friendlyName': version.get('friendlyName'),
                    'description': version.get('description'),
                    'major_version': str(version.get('version', {}).get('major', 0)),
                    'full_version': f"{version.get('version', {}).get('major', 0)}.{version.get('version', {}).get('minor', 0)}.{version.get('version', {}).get('patch', 0)}"
                })
    
    return deprecated_versions

def main():
    print("Fetching all projects...")
    projects = get_all_projects()
    print(f"Total projects found: {len(projects)}")
    
    print("\nFetching all ADO tasks...")
    tasks = get_all_tasks()
    print(f"Total tasks found: {len(tasks)}")
    
    print("\nIdentifying deprecated task versions...")
    deprecated_versions = filter_deprecated_versions(tasks)
    print(f"Deprecated task versions found: {len(deprecated_versions)}")
    
    # Find projects using deprecated versions
    results = []
    
    for project in projects:
        project_name = project.get("name")
        print(f"\nChecking project: {project_name}")
        
        definitions = get_project_build_definitions(project_name)
        
        for definition in definitions:
            definition_detail = get_build_definition_detail(project_name, definition['id'])
            deprecated_usage = check_definition_for_deprecated_task(definition_detail, deprecated_versions)
            
            if deprecated_usage:
                results.append({
                    'project': project_name,
                    'deprecated_tasks': deprecated_usage
                })
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults exported to {OUTPUT_FILE}")
    print(f"Found {len(results)} projects using deprecated task versions")

if __name__ == "__main__":
    main()