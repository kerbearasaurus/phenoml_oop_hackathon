# PhenoML FHIR Agent

This agent provides tools for interacting with a Medplum FHIR server using PhenoML's lang2fhir API for natural language processing of healthcare data.

## Features

- Convert natural language descriptions to FHIR resources using PhenoML's lang2fhir API
- Convert natural language queries to FHIR search parameters
- Perform direct FHIR searches and resource creation on a FHIR server
- Automatically handle patient context for related resources

## Prerequisites

1. PhenoML account with access to the lang2fhir API
2. Medplum account (or other FHIR server) for storing created resources
3. Python 3.8+
4. Google ADK (Agent Development Kit)

## Setup

1. Clone this repository

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables for authentication:

   ```bash
   # Required environment variables
   export PHENOML_TOKEN="your_phenoml_access_token" 
   export MEDPLUM_TOKEN="your_medplum_access_token"
   ```

   The agent will automatically use these environment variables for authentication.


## PhenoML lang2fhir API

This agent uses PhenoML's lang2fhir API, which provides:

- **Create endpoint**: Converts natural language to structured FHIR resources
- **Search endpoint**: Converts natural language to FHIR search parameters

For more information, visit: [PhenoML Documentation](https://developer.pheno.ml)

## License

[MIT](LICENSE) 
