import datetime
import json
import os
import requests
from typing import Dict, List, Any, Optional, Union
from zoneinfo import ZoneInfo
from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """

    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}


def lang2fhir_and_create(natural_language_description: str, resource_type: str, phenoml_token: str, medplum_token: str, patient_id: str, fhir_server_url: str = None, version: str = "R4") -> dict:
    """Converts natural language to a FHIR resource and directly creates it on the FHIR server.
    
    Args:
        natural_language_description (str): Natural language description of the resource to create.
        resource_type (str): The FHIR resource type to create (e.g., "Patient", "condition-encounter-diagnosis").
        phenoml_token (str): Authentication token for PhenoML API.
        medplum_token (str): Authentication token for Medplum/FHIR server.
        patient_id (str): The patient ID to associate this resource with.
        fhir_server_url (str, optional): URL of the FHIR server. Defaults to Medplum.
        version (str, optional): FHIR version to use. Defaults to "R4".
        
    Returns:
        dict: Creation result with status and resource data or error message.
    """
    try:
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
        if not fhir_server_url:
            fhir_server_url = "https://api.medplum.com/fhir/R4"
        
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


def lang2fhir_and_search(natural_language_query: str, phenoml_token: str, medplum_token: str, patient_id: str = None, fhir_server_url: str = None) -> dict:
    """Converts a natural language query to FHIR search parameters and performs the search in one operation.
    
    Args:
        natural_language_query (str): Natural language search query like "Find all patients with diabetes".
        phenoml_token (str): Authentication token for PhenoML API.
        medplum_token (str): Authentication token for Medplum/FHIR server.
        patient_id (str, optional): If provided, limits the search to a specific patient.
        fhir_server_url (str, optional): URL of the FHIR server. Defaults to Medplum.
        
    Returns:
        dict: Search result with status and search results or error message.
    """
    try:
        # Step 1: Convert natural language to FHIR search parameters using lang2fhir
        lang2fhir_url = "https://experiment.app.pheno.ml/lang2fhir/search"
        lang2fhir_payload = {
            "text": natural_language_query
        }
        
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
        resource_type = search_params.get("resourceType")
        params = search_params.get("parameters", {})
        
        if not resource_type:
            return {
                "status": "error",
                "error_message": "Could not determine resource type from query"
            }
            
        # Add patient-specific filtering if patient_id is provided
        if patient_id and resource_type.lower() != "patient":
            # Add appropriate patient filter based on resource type
            if resource_type.lower() in ["encounter", "appointmentresponse"]:
                params["patient"] = f"Patient/{patient_id}"
            else:
                params["subject"] = f"Patient/{patient_id}"
        
        # Step 2: Perform the search on the FHIR server
        if not fhir_server_url:
            fhir_server_url = "https://api.medplum.com/fhir/R4"
        
        fhir_headers = {
            "Authorization": f"Bearer {medplum_token}",
            "Content-Type": "application/json"
        }
        
        # Build search URL
        fhir_url = f"{fhir_server_url}/{resource_type}"
        
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
    name="medplum_fhir_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to convert natural language to FHIR resources and queries using PhenoML lang2fhir API."
    ),
    instruction=(
        "You are a helpful agent who can create FHIR resources from natural language descriptions and "
        "search for FHIR resources using natural language queries through PhenoML's lang2fhir API. "
        "You can also perform direct FHIR operations on a FHIR server."
    ),
    tools=[
        get_weather, 
        get_current_time, 
        lang2fhir_create, 
        lang2fhir_search, 
        fhir_search, 
        fhir_create,
        lang2fhir_and_create,
        lang2fhir_and_search
    ],
)