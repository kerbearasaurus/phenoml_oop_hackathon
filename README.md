# Medplum FHIR Agent with PhenoML lang2fhir

This agent provides tools for interacting with a Medplum FHIR server using PhenoML's lang2fhir API for natural language processing of healthcare data.

## Features

- Convert natural language descriptions to FHIR resources using PhenoML's lang2fhir API
- Convert natural language queries to FHIR search parameters
- Perform direct FHIR searches and resource creation on a FHIR server

## Prerequisites

1. PhenoML account with access to the lang2fhir API
2. Medplum account (or other FHIR server) for storing created resources
3. Python 3.8+

## Setup

1. Clone this repository

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Authenticate with PhenoML and Medplum to obtain tokens. You can use the provided authentication scripts:

   **PhenoML Authentication**:
   ```bash
   # Using environment variables
   export PHENOML_EMAIL="your_phenoml_email@example.com" 
   export PHENOML_PASSWORD="your_phenoml_password"
   python phenoml_auth.py --save
   
   # Or passing credentials directly
   python phenoml_auth.py --email "your_phenoml_email@example.com" --password "your_phenoml_password" --save
   ```

   **Medplum Authentication**:
   ```bash
   # Using environment variables
   export MEDPLUM_CLIENT_ID="your_medplum_client_id"
   export MEDPLUM_CLIENT_SECRET="your_medplum_client_secret" 
   python medplum_auth.py --save
   
   # Or passing credentials directly
   python medplum_auth.py --client-id "your_medplum_client_id" --client-secret "your_medplum_client_secret" --save
   ```

   This will save your tokens to a `.env` file, which will be automatically loaded by the example scripts.

4. Run the example script
   ```bash
   python example.py
   ```

## API Usage

### Converting Natural Language to FHIR Resource

```python
from agents.multi_tool_agent.agent import lang2fhir_create

result = lang2fhir_create(
    "Patient has severe asthma with acute exacerbation", 
    "condition-encounter-diagnosis",
    phenoml_token
)
print(json.dumps(result["resource"], indent=2))
```

### Converting Natural Language to FHIR Search

```python
from agents.multi_tool_agent.agent import lang2fhir_search

result = lang2fhir_search(
    "Appointments between March 2-9, 2025",
    phenoml_token
)
print(json.dumps(result["search_params"], indent=2))

# Output example:
# {
#   "resourceType": "Appointment",
#   "searchParams": "date=ge2025-03-02&date=le2025-03-09"
# }
```

### Performing FHIR Search

```python
from agents.multi_tool_agent.agent import fhir_search

# Search Medplum or specify a different FHIR server
result = fhir_search(
    "Patient", 
    {"name": "Smith"},
    medplum_token,
    "https://your-fhir-server.com/fhir/R4"  # Optional
)
```

### Creating FHIR Resource Directly

```python
from agents.multi_tool_agent.agent import fhir_create

patient_data = {
    "resourceType": "Patient",
    "name": [{"family": "Smith", "given": ["John"]}],
    "gender": "male",
    "birthDate": "1970-01-01"
}

result = fhir_create(
    "Patient", 
    patient_data, 
    medplum_token
)
```

## Agent Architecture

This agent follows a clean separation of concerns:

1. **Authentication** - Handled by separate scripts (`phenoml_auth.py` and `medplum_auth.py`) outside the agent
2. **API Interaction** - Core functionality in the agent.py file
3. **Token Management** - Tokens are passed explicitly to functions, allowing for flexible authentication approaches

## PhenoML lang2fhir API

This agent uses PhenoML's lang2fhir API, which provides:

- **Create endpoint**: Converts natural language to structured FHIR resources
- **Search endpoint**: Converts natural language to FHIR search parameters

For more information, visit: [PhenoML Documentation](https://docs.pheno.ml)

## License

[MIT](LICENSE) 
