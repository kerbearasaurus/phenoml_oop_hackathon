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

3. Authenticate and set up environment variables:

   a. **Obtain PhenoML Token**:
   ```bash
   # Run the PhenoML authentication script
   python scripts/phenoml_auth.py --email your_email@example.com --password your_password
   
   # The script will output a token that you can use in the next step
   # Alternatively, you can run it with the --save flag to automatically save to .env
   python scripts/phenoml_auth.py --email your_email@example.com --password your_password --save
   ```

   b. **Obtain Medplum Token**:
   ```bash
   # Run the Medplum authentication script
   python scripts/medplum_auth.py --client-id your_client_id --client-secret your_client_secret
   
   # The script will output a token that you can use in the next step
   # Alternatively, you can run it with the --save flag to automatically save to .env
   python scripts/medplum_auth.py --client-id your_client_id --client-secret your_client_secret --save
   ```

   c. **Set Environment Variables**:
   If you didn't use the `--save` flag, manually set the environment variables:
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
