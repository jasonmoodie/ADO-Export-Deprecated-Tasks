# Azure DevOps Deprecated Tasks Scanner

This tool scans your Azure DevOps organization to identify build pipelines using deprecated task versions and exports the results to a JSON file.

## Overview

The scanner connects to your Azure DevOps organization via REST API to:
1. Fetch all available tasks and identify deprecated versions
2. Scan all projects and their build definitions
3. Identify pipelines using deprecated task versions
4. Export findings to a JSON report

## Requirements

### Python Dependencies
```bash
pip install requests
```

### Azure DevOps Prerequisites
- Azure DevOps organization access
- Personal Access Token (PAT) with the following permissions:
  - **Build**: Read
  - **Project and Team**: Read
  - **Task Groups**: Read

## Setup

1. **Clone or download the project files**
   - [`export_deprecated_ado_tasks.py`](export_deprecated_ado_tasks.py) - Main scanner script
   - [`deprecated_tasks.json`](deprecated_tasks.json) - Sample output file

2. **Configure your Azure DevOps connection**
   
   Edit the configuration section in [`export_deprecated_ado_tasks.py`](export_deprecated_ado_tasks.py):
   ```python
   # Configuration
   ADO_ORG = "your-organization-name"  # Replace with your Azure DevOps organization
   ADO_PAT = "your-personal-access-token"  # Replace with your PAT
   OUTPUT_FILE = "deprecated_tasks.json"
   ```

3. **Create a Personal Access Token**
   - Go to Azure DevOps → User Settings → Personal Access Tokens
   - Create new token with required permissions (see Prerequisites above)
   - Copy the token value to use in the script

## Usage

Run the scanner:
```bash
python export_deprecated_ado_tasks.py
```

The script will:
1. Connect to your Azure DevOps organization
2. Fetch all projects and available tasks
3. Identify deprecated task versions
4. Scan each project's build definitions
5. Generate a report in JSON format

### Sample Output

The script generates output similar to [`deprecated_tasks.json`](deprecated_tasks.json):
```json
[
  {
    "project": "PartsUnlimited",
    "deprecated_tasks": [
      {
        "task_name": "NuGetInstaller",
        "version_used": "0.*",
        "pipeline_name": "PartsUnlimitedE2E"
      }
    ]
  }
]
```

## How It Works

### Task Deprecation Detection
The scanner identifies deprecated tasks using two criteria:
1. **Explicit deprecation**: Tasks marked with `deprecated: true` flag
2. **Version obsolescence**: Task versions that are not the latest major version

### Pipeline Scanning
- Scans classic build pipelines (YAML pipelines require different approach)
- Checks each step's task ID and version specification
- Matches against the deprecated tasks list

### API Endpoints Used
- `/projects` - List all projects
- `/distributedtask/tasks` - Get all available tasks
- `/build/definitions` - List build definitions per project
- `/build/definitions/{id}` - Get detailed build definition

## Output Format

Each entry in the results contains:
- `project`: Azure DevOps project name
- `deprecated_tasks`: Array of deprecated task usage
  - `task_name`: Name of the deprecated task
  - `version_used`: Version specification used in the pipeline
  - `pipeline_name`: Name of the build pipeline

## Limitations

- Currently supports classic build pipelines only
- YAML pipelines require additional parsing logic
- Release pipelines are not included in the scan
- Rate limiting may affect large organizations

## Troubleshooting

### Authentication Issues
- Verify your PAT has the required permissions
- Check that your organization name is correct
- Ensure the PAT hasn't expired

### API Errors
- The script uses API version 7.1 - ensure your ADO instance supports this version
- Some endpoints may require different permissions for on-premises installations

### Performance
- Large organizations may take significant time to scan
- Consider implementing pagination for organizations with many projects/pipelines

## Security Notes

- Store your PAT securely and never commit it to version control
- Consider using environment variables for sensitive configuration
- Regularly rotate your Personal Access Tokens