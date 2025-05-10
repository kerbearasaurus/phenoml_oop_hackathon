import requests
import os
from typing import Dict, List, Any, Optional
from google.adk.agents import Agent

# Define resource types once as a list for validation and documentation
FHIR_RESOURCE_TYPES = [
    "Patient", 
    "Condition", 
    "Observation", 
    "Procedure", 
    "Medication", 
    "MedicationRequest",
    "Encounter", 
    "DiagnosticReport", 
    "CarePlan", 
    "Appointment", 
    "DocumentReference", 
    "QuestionnaireResponse"
]


def lang2fhir_and_create(
    natural_language_description: str, 
    resource_type: str,
    patient_id: str, 
    version: str = "R4"
) -> dict:
    """Converts natural language to a FHIR resource and directly creates it on the FHIR server.
    
    Args:
        natural_language_description (str): Natural language description of the resource to create.
        resource_type (str): The FHIR resource type to create (e.g., "Patient", "Condition").
        patient_id (str): The patient ID to associate this resource with.
        version (str, optional): FHIR version to use. Defaults to "R4".
        
    Returns:
        dict: Creation result with status and resource data or error message.
    """
    try:
        # Get tokens from environment variables
        phenoml_token = os.environ.get("PHENOML_TOKEN")
        medplum_token = os.environ.get("MEDPLUM_TOKEN")
        
        if not phenoml_token:
            return {
                "status": "error",
                "error_message": "PHENOML_TOKEN environment variable not set"
            }
            
        if not medplum_token:
            return {
                "status": "error",
                "error_message": "MEDPLUM_TOKEN environment variable not set"
            }
            
        # Set FHIR server URL
        fhir_server_url = "https://api.medplum.com/fhir/R4"
        
        # Validate resource type
        if resource_type not in FHIR_RESOURCE_TYPES and not any(rt.lower() == resource_type.lower() for rt in FHIR_RESOURCE_TYPES):
            return {
                "status": "error",
                "error_message": f"Invalid resource type: {resource_type}. Valid types are: {', '.join(FHIR_RESOURCE_TYPES)}"
            }
        
        # Step 1: Convert natural language to FHIR using lang2fhir
        lang2fhir_url = "https://experiment.app.pheno.ml/lang2fhir/create"
        lang2fhir_payload = {
            "version": version,
            "resource": resource_type,
            "text": natural_language_description
        }
        
        lang2fhir_headers = {
            "Authorization": f"Bearer {phenoml_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Call lang2fhir API to get FHIR resource
        lang2fhir_response = requests.post(lang2fhir_url, json=lang2fhir_payload, headers=lang2fhir_headers)
        lang2fhir_response.raise_for_status()
        
        fhir_resource = lang2fhir_response.json()
        
        # Step 2: Add patient reference to the resource
        if resource_type.lower() != "patient":
            # Add subject reference for clinical resources
            fhir_resource["subject"] = {
                "reference": f"Patient/{patient_id}"
            }
            
            # For specific resource types that use patient instead of subject
            if resource_type.lower() in ["encounter", "appointmentresponse", "appointmentrecurrence"]:
                fhir_resource["patient"] = {
                    "reference": f"Patient/{patient_id}"
                }
        
        # Step 3: Create the resource on the FHIR server
        fhir_headers = {
            "Authorization": f"Bearer {medplum_token}",
            "Content-Type": "application/json"
        }
        
        # Ensure resourceType is set correctly
        fhir_resource["resourceType"] = resource_type
        
        # Create the resource on the FHIR server
        fhir_url = f"{fhir_server_url}/{resource_type}"
        fhir_response = requests.post(fhir_url, json=fhir_resource, headers=fhir_headers)
        fhir_response.raise_for_status()
        
        created_resource = fhir_response.json()
        
        return {
            "status": "success",
            "lang2fhir_result": fhir_resource,
            "fhir_resource": created_resource
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to create resource: {str(e)}"
        }


def lang2fhir_and_search(
    natural_language_query: str, 
    patient_id: Optional[str] = None, 
    resource_type: Optional[str] = None
) -> dict:
    """Converts a natural language query to FHIR search parameters and performs the search in one operation.
    
    Args:
        natural_language_query (str): Natural language search query like "Find all patients with diabetes".
        patient_id (Optional[str], optional): If provided, limits the search to a specific patient.
        resource_type (Optional[str], optional): If provided, forces a specific resource type.
        
    Returns:
        dict: Search result with status and search results or error message.
    """
    try:
        # Get tokens from environment variables
        phenoml_token = os.environ.get("PHENOML_TOKEN")
        medplum_token = os.environ.get("MEDPLUM_TOKEN")
        
        if not phenoml_token:
            return {
                "status": "error",
                "error_message": "PHENOML_TOKEN environment variable not set"
            }
            
        if not medplum_token:
            return {
                "status": "error",
                "error_message": "MEDPLUM_TOKEN environment variable not set"
            }
            
        # Set FHIR server URL
        fhir_server_url = "https://api.medplum.com/fhir/R4"
        
        # Validate resource_type if provided
        if resource_type and resource_type not in FHIR_RESOURCE_TYPES and not any(rt.lower() == resource_type.lower() for rt in FHIR_RESOURCE_TYPES):
            return {
                "status": "error",
                "error_message": f"Invalid resource type: {resource_type}. Valid types are: {', '.join(FHIR_RESOURCE_TYPES)}"
            }
        
        # Step 1: Convert natural language to FHIR search parameters using lang2fhir
        lang2fhir_url = "https://experiment.app.pheno.ml/lang2fhir/search"
        lang2fhir_payload = {
            "text": natural_language_query
        }
        
        # Add resource type to payload if specified
        if resource_type:
            lang2fhir_payload["resource"] = resource_type
        
        lang2fhir_headers = {
            "Authorization": f"Bearer {phenoml_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Call lang2fhir API to get FHIR search parameters
        lang2fhir_response = requests.post(lang2fhir_url, json=lang2fhir_payload, headers=lang2fhir_headers)
        lang2fhir_response.raise_for_status()
        
        search_params = lang2fhir_response.json()
        
        # Extract resource type and search parameters from lang2fhir response
        detected_resource_type = search_params.get("resourceType")
        params = search_params.get("parameters", {})
        
        # Use specified resource type if provided, otherwise use detected
        final_resource_type = resource_type if resource_type else detected_resource_type
        
        if not final_resource_type:
            return {
                "status": "error",
                "error_message": "Could not determine resource type from query"
            }
            
        # Add patient-specific filtering if patient_id is provided
        if patient_id and final_resource_type.lower() != "patient":
            # Add appropriate patient filter based on resource type
            if final_resource_type.lower() in ["encounter", "appointmentresponse"]:
                params["patient"] = f"Patient/{patient_id}"
            else:
                params["subject"] = f"Patient/{patient_id}"
        
        fhir_headers = {
            "Authorization": f"Bearer {medplum_token}",
            "Content-Type": "application/json"
        }
        
        # Build search URL
        fhir_url = f"{fhir_server_url}/{final_resource_type}"
        
        if params:
            query_string = "&".join([f"{key}={value}" for key, value in params.items()])
            fhir_url = f"{fhir_url}?{query_string}"
        
        # Execute the search on the FHIR server
        fhir_response = requests.get(fhir_url, headers=fhir_headers)
        fhir_response.raise_for_status()
        
        search_results = fhir_response.json()
        
        return {
            "status": "success",
            "search_params": search_params,
            "search_results": search_results
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Search failed: {str(e)}"
        }


root_agent = Agent(
    name="phenoml_fhir_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to convert natural language to FHIR resources and queries using PhenoML lang2fhir API."
    ),
    instruction=(
        "You are a helpful agent who can create FHIR resources from natural language descriptions and "
        "search for FHIR resources using natural language queries through PhenoML's lang2fhir API. "
        "You can also perform direct FHIR operations on a FHIR server. "
        "Available FHIR resource types include: " + 
        ", ".join(FHIR_RESOURCE_TYPES) + "\n\n"
        
        "IMPORTANT: When a user asks a question or makes a request, follow these steps:\n"
        "1. TRANSLATE the user's intent into relevant FHIR concepts\n"
        "2. DETERMINE which FHIR resources are needed (Patient, Appointment, Condition, etc.)\n"
        "3. DECIDE whether to search for existing resources or create new ones\n"
        "4. USE the appropriate tool:\n"
        "   - find_patient: When trying to locate a specific patient\n"
        "   - lang2fhir_and_search: When looking for clinical data or other resources\n"
        "   - lang2fhir_and_create: When creating new clinical data or resources\n\n"
        
        "Examples of translating user intent to FHIR actions:\n"
        "- 'Book an appointment for John tomorrow' → Create an Appointment resource\n"
        "- 'What medications is Sarah taking?' → Search for MedicationRequest resources\n"
        "- 'Record that Bob has diabetes' → Create a Condition resource\n"
        "- 'When is my next appointment?' → Search for Appointment resources\n\n"
        
        "Always respond to the user's intent, not just explaining FHIR concepts."
    ),
    tools=[
        lang2fhir_and_create,
        lang2fhir_and_search,

    ],
)