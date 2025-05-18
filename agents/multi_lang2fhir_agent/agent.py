import requests
import os
from typing import Dict, List, Any, Optional, Literal
from google.adk.agents import Agent
from datetime import datetime
import json

# Define all FHIR profiles with their corresponding resource types
FHIR_PROFILES = {
    "appointment": "Appointment",
    "condition-encounter-diagnosis": "Condition",
    "medicationrequest": "MedicationRequest",
    "careplan": "CarePlan",
    "condition-problems-health-concerns": "Condition",
    "coverage": "Coverage",
    "encounter": "Encounter",
    "invoice": "Invoice",
    "observation-clinical-result": "Observation",
    "observation-lab": "Observation",
    "patient": "Patient",
    "procedure": "Procedure",
    "questionnaire": "Questionnaire",
    "questionnaireresponse": "QuestionnaireResponse",
    "simple-observation": "Observation",
    "schedule": "Schedule",
    "slot": "Slot",
    "vital-signs": "Observation"
}

# Get the valid resource types from the profiles
FHIR_RESOURCE_TYPES = list(set(FHIR_PROFILES.values()))


def lang2fhir_and_create(natural_language_description: str,
                         profile: str,
                         patient_id: Optional[str] = None,
                         version: str = "R4",
                         practitioner_id: Optional[str] = None,
                         location_id: Optional[str] = None) -> dict:
    """Converts natural language to a FHIR resource and directly creates it on the FHIR server.

    Args:
        natural_language_description (str): Natural language description of the resource to create.
        patient_id (str, optional): The patient ID to associate this resource with.
        resource_type (str): The specific FHIR profile to use. 
            Must be one of: appointment, condition-encounter-diagnosis, medicationrequest, careplan, 
            condition-problems-health-concerns, coverage, encounter, observation-clinical-result, 
            observation-lab, patient, procedure, questionnaire, questionnaireresponse, 
            simple-observation, schedule, slot, vital-signs.
            Select the most appropriate profile based on the description.
        version (str, optional): FHIR version to use. Defaults to "R4".
        practitioner_id (str, optional): The practitioner ID to associate with this resource. Required for appointments.
        location_id (str, optional): The location ID to associate with this resource. Required for appointments on Canvas FHIR servers.

    Returns:
        dict: Creation result with status and resource data or error message.
    """
    try:
        # Get tokens from environment variables
        phenoml_token = os.environ.get("PHENOML_TOKEN")
        medplum_token = os.environ.get("MEDPLUM_TOKEN")
        canvas_token = os.environ.get("CANVAS_TOKEN")
        canvas_instance_identifier = os.environ.get(
            "CANVAS_INSTANCE_IDENTIFIER")

        if not phenoml_token:
            return {
                "status": "error",
                "error_message": "PHENOML_TOKEN environment variable not set"
            }

        if (not medplum_token and not canvas_token) or (medplum_token
                                                        and canvas_token):
            return {
                "status":
                "error",
                "error_message":
                "Exactly one of MEDPLUM_TOKEN or CANVAS_TOKEN environment variable must be set"
            }

        # Set FHIR server URL
        if canvas_token and not medplum_token:
            fhir_server_url = f"https://fumage-{canvas_instance_identifier}.canvasmedical.com"
            fhir_access_token = canvas_token
        if medplum_token and not canvas_token:
            base_url = os.environ.get("MEDPLUM_BASE_URL")
            if not base_url:
                # if no base_url is provided, use the default api.medplum.com
                base_url = "https://api.medplum.com"
            fhir_server_url = f"{base_url}/fhir/R4"
            fhir_access_token = medplum_token

        # Validate resource type (profile)
        if profile not in FHIR_PROFILES:
            return {
                "status":
                "error",
                "error_message":
                f"Invalid profile: {profile}. Valid profiles are: {', '.join(FHIR_PROFILES.keys())}"
            }

        # Get the base FHIR resource type for this profile
        base_resource_type = FHIR_PROFILES.get(profile)

        # Step 1: Convert natural language to FHIR using lang2fhir
        lang2fhir_url = "https://experiment.app.pheno.ml/lang2fhir/create"
        lang2fhir_payload = {
            "version": version,
            "resource": profile,
            "text": natural_language_description
        }

        lang2fhir_headers = {
            "Authorization": f"Bearer {phenoml_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Call lang2fhir API to get FHIR resource
        lang2fhir_response = requests.post(lang2fhir_url,
                                           json=lang2fhir_payload,
                                           headers=lang2fhir_headers)

        lang2fhir_response.raise_for_status()

        fhir_resource = lang2fhir_response.json()

        # Step 2: Add patient reference to the resource if it's a clinical resource (not a Patient resource)
        if base_resource_type.lower() != "patient":
            # Handle Appointment resources differently - they use participant array
            if base_resource_type.lower() == "appointment":
                # Completely overwrite participants array with correctly formatted entries
                fhir_resource["participant"] = [{
                    "actor": {
                        "reference": f"Patient/{patient_id}"
                    },
                    "status": "accepted"
                }]

                # Add practitioner if provided
                if practitioner_id:
                    fhir_resource["participant"].append({
                        "actor": {
                            "reference": f"Practitioner/{practitioner_id}"
                        },
                        "status": "accepted"
                    })

                # Ensure appointment has a status
                fhir_resource["status"] = "booked"

                # For Canvas Medical FHIR server, add supportingInformation with Location reference. this is a hack for the hackathon, adding support for Canvas FHIR profiles on lang2FHIR
                if canvas_token and not medplum_token:

                    # Add location reference if provided
                    if location_id:
                        fhir_resource["supportingInformation"] = [{
                            "reference":
                            f"Location/{location_id}"
                        }]
                    else:
                        print(
                            "[WARNING] Canvas requires location_id for appointments"
                        )

            else:
                # Add subject reference for clinical resources
                fhir_resource["subject"] = {
                    "reference": f"Patient/{patient_id}"
                }

                # For specific resource types that use patient instead of subject
                if base_resource_type.lower() in [
                        "encounter", "appointmentresponse",
                        "appointmentrecurrence"
                ]:
                    fhir_resource["patient"] = {
                        "reference": f"Patient/{patient_id}"
                    }

        # Step 3: Create the resource on the FHIR server
        fhir_headers = {
            "Authorization": f"Bearer {fhir_access_token}",
            "Content-Type": "application/json"
        }

        # Create the resource on the FHIR server
        fhir_url = f"{fhir_server_url}/{base_resource_type}"

        fhir_response = requests.post(fhir_url,
                                      json=fhir_resource,
                                      headers=fhir_headers)

        fhir_response.raise_for_status()

        # Handle 201 Created with empty body (common in Canvas)
        if fhir_response.status_code == 201 and not fhir_response.text.strip():
            created_resource = {
                "resourceType": base_resource_type,
                "status": "created"
            }
        else:
            created_resource = fhir_response.json()

        return {
            "status": fhir_response.status_code,
            "lang2fhir_result": fhir_resource,
            "fhir_resource": created_resource,
            "profile_used": profile,
            "base_resource_type": base_resource_type
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to create resource: {str(e)}"
        }


def lang2fhir_and_search(natural_language_query: str) -> dict:
    """Converts a natural language query to FHIR search parameters and performs the search in one operation.

    Args:
        natural_language_query (str): Natural language search query like "Find all patients with diabetes".

    Returns:
        dict: Search result with status and search results or error message.
    """
    try:

        # Get tokens from environment variables
        phenoml_token = os.environ.get("PHENOML_TOKEN")
        medplum_token = os.environ.get("MEDPLUM_TOKEN")
        canvas_token = os.environ.get("CANVAS_TOKEN")
        canvas_instance_identifier = os.environ.get(
            "CANVAS_INSTANCE_IDENTIFIER")

        if not phenoml_token:
            return {
                "status": "error",
                "error_message": "PHENOML_TOKEN environment variable not set"
            }

        if (not medplum_token and not canvas_token) or (medplum_token
                                                        and canvas_token):
            return {
                "status":
                "error",
                "error_message":
                "Exactly one of MEDPLUM_TOKEN or CANVAS_TOKEN environment variable must be set"
            }

        # Set FHIR server URL
        if canvas_token and not medplum_token:
            fhir_server_url = f"https://fumage-{canvas_instance_identifier}.canvasmedical.com"
            fhir_access_token = canvas_token
        if medplum_token and not canvas_token:
            base_url = os.environ.get("MEDPLUM_BASE_URL")
            if not base_url:
                # if no base_url is provided, use the default api.medplum.com
                base_url = "https://api.medplum.com"
            fhir_server_url = f"{base_url}/fhir/R4"
            fhir_access_token = medplum_token

        # Step 1: Convert natural language to FHIR search parameters using lang2fhir
        lang2fhir_url = "https://experiment.app.pheno.ml/lang2fhir/search"
        lang2fhir_payload = {"text": natural_language_query}

        lang2fhir_headers = {
            "Authorization": f"Bearer {phenoml_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Call lang2fhir API to get FHIR search parameters
        lang2fhir_response = requests.post(lang2fhir_url,
                                           json=lang2fhir_payload,
                                           headers=lang2fhir_headers)

        lang2fhir_response.raise_for_status()

        search_params = lang2fhir_response.json()

        # Extract resource type and search parameters from lang2fhir response
        detected_resource_type = search_params.get("resourceType")
        search_params_str = search_params.get("searchParams", "")

        # remove this debug line if you want! it's helping to get a little bit of chain of thought
        print(
            f"[DEBUG] Search for: {detected_resource_type} with params: {search_params_str}"
        )

        # Build search URL
        fhir_url = f"{fhir_server_url}/{detected_resource_type}"

        # Add search parameters with proper reference handling for FHIR
        if search_params_str:
            # Parse parameters
            parts = search_params_str.split('&')
            fixed_parts = []

            for part in parts:
                if '=' in part:
                    name, value = part.split('=', 1)

                    if ('/' not in value and
                            # Pattern match for UUIDs so we know it's a reference Id
                        ('-' in value
                         or value.startswith('0') and len(value) > 20)):

                        # Simple mapping of parameter names to resource types
                        param_to_resource = {
                            # Common reference parameters
                            'patient': 'Patient',
                            'subject': 'Patient',
                            'practitioner': 'Practitioner',
                            'actor': 'Practitioner',
                            'provider': 'Practitioner',
                            'schedule': 'Schedule',
                            'encounter': 'Encounter',
                            'organization': 'Organization',
                            'location': 'Location',
                            'slot': 'Slot',
                            'appointment': 'Appointment',
                        }

                        # Try to determine resource type
                        resource_type = None

                        # 1. Check if parameter name is in our mapping
                        if name in param_to_resource:
                            resource_type = param_to_resource[name]

                        # 2. If parameter ends with 'Id', strip 'Id' and capitalize, backup to catch references
                        elif name.endswith('Id'):
                            resource_type = name[:-2].capitalize()

                        # 3. Check if parameter matches a FHIR resource type (case-insensitive)
                        else:
                            # Try to find a matching resource type
                            for rt in FHIR_RESOURCE_TYPES:
                                if rt.lower() == name.lower():
                                    resource_type = rt
                                    break

                        # Special handling for Slot status parameter - change to "free"
                        if detected_resource_type == "Slot" and name == "status" and value == "available":
                            value = "free"
                        # If we identified a resource type, format as a proper reference
                        if resource_type:
                            fixed_parts.append(
                                f"{name}={resource_type}/{value}")
                        else:
                            fixed_parts.append(part)
                    else:
                        fixed_parts.append(part)
                else:
                    fixed_parts.append(part)

            # Reconstruct the query string and add pagination, this is a hack for the hackathon lol, ideally you'd want to handle pagination properly
            search_params_str = '&'.join(fixed_parts)
            fhir_url = f"{fhir_url}?{search_params_str}&_count=250"
        else:
            # No search params, just add pagination
            fhir_url = f"{fhir_url}?_count=250"

        fhir_headers = {
            "Authorization": f"Bearer {fhir_access_token}",
            "Content-Type": "application/json"
        }

        # Execute the search on the FHIR server
        fhir_response = requests.get(fhir_url, headers=fhir_headers)

        fhir_response.raise_for_status()

        search_results = fhir_response.json()

        return {
            "status": "success",
            "search_params": search_params,
            "search_results": search_results,
            "resource_type_used": detected_resource_type
        }
    except Exception as e:

        return {"status": "error", "error_message": f"Search failed: {str(e)}"}


def list_todoist_projects() -> dict:
    """Lists all Todoist projects with their IDs and names.

    Returns:
        dict: Result with status and projects list or error message.
    """
    try:
        # Get Todoist API token from environment variables
        todoist_token = os.environ.get("TODOIST_TOKEN")

        if not todoist_token:
            return {
                "status": "error",
                "error_message": "TODOIST_TOKEN environment variable not set"
            }

        # Set Todoist API URL and headers
        todoist_api_url = "https://api.todoist.com/rest/v2/projects"
        todoist_headers = {
            "Authorization": f"Bearer {todoist_token}",
            "Content-Type": "application/json"
        }

        # Execute the request to the Todoist API
        todoist_response = requests.get(todoist_api_url,
                                        headers=todoist_headers)

        todoist_response.raise_for_status()

        projects = todoist_response.json()

        # Format the projects for easier reading
        formatted_projects = []
        for project in projects:
            formatted_projects.append({
                "id":
                project.get("id"),
                "name":
                project.get("name"),
                "color":
                project.get("color", ""),
                "is_favorite":
                project.get("is_favorite", False),
                "is_shared":
                project.get("is_shared", False),
                "view_count":
                project.get("view_count", 0)
            })

        return {"status": "success", "projects": formatted_projects}
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to list Todoist projects: {str(e)}"
        }


def list_todoist_tasks(project_id: str) -> dict:
    """Lists tasks for a specific Todoist project.

    Args:
        project_id (str): The ID of the Todoist project to list tasks for.

    Returns:
        dict: Result with status and task list or error message.
    """
    try:
        # Get Todoist API token from environment variables
        todoist_token = os.environ.get("TODOIST_TOKEN")

        if not todoist_token:
            return {
                "status": "error",
                "error_message": "TODOIST_TOKEN environment variable not set"
            }

        # Set Todoist API URL and headers
        todoist_api_url = "https://api.todoist.com/rest/v2/tasks"
        todoist_headers = {
            "Authorization": f"Bearer {todoist_token}",
            "Content-Type": "application/json"
        }

        # Add project_id as a query parameter
        params = {"project_id": project_id}

        # Execute the request to the Todoist API
        todoist_response = requests.get(todoist_api_url,
                                        headers=todoist_headers,
                                        params=params)

        todoist_response.raise_for_status()

        tasks = todoist_response.json()

        return {"status": "success", "project_id": project_id, "tasks": tasks}
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to list Todoist tasks: {str(e)}"
        }


def create_todoist_task(content: str,
                        project_id: str,
                        due_string: Optional[str] = None,
                        priority: Optional[int] = None,
                        description: Optional[str] = None,
                        labels: Optional[List[str]] = None) -> dict:
    """Creates a task in a specific Todoist project.

    Args:
        content (str): The task content/title.
        project_id (str): The ID of the Todoist project to create the task in.
        due_string (str, optional): Human-readable due date, e.g. "tomorrow", "next Monday".
        priority (int, optional): Task priority from 1 (normal) to 4 (urgent).
        description (str, optional): Detailed description of the task.
        labels (List[str], optional): List of label names to apply to the task.

    Returns:
        dict: Result with status and created task data or error message.
    """
    try:
        # Get Todoist API token from environment variables
        todoist_token = os.environ.get("TODOIST_TOKEN")

        if not todoist_token:
            return {
                "status": "error",
                "error_message": "TODOIST_TOKEN environment variable not set"
            }

        # Set Todoist API URL and headers
        todoist_api_url = "https://api.todoist.com/rest/v2/tasks"
        todoist_headers = {
            "Authorization": f"Bearer {todoist_token}",
            "Content-Type": "application/json"
        }

        # Prepare the payload
        payload = {"content": content, "project_id": project_id}

        # Add optional parameters if provided
        if due_string:
            payload["due_string"] = due_string

        if priority:
            payload["priority"] = priority

        if description:
            payload["description"] = description

        if labels:
            payload["labels"] = labels

        # Execute the request to the Todoist API
        todoist_response = requests.post(todoist_api_url,
                                         headers=todoist_headers,
                                         json=payload)

        todoist_response.raise_for_status()

        created_task = todoist_response.json()

        return {
            "status": "success",
            "project_id": project_id,
            "created_task": created_task
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to create Todoist task: {str(e)}"
        }


def find_nearby_places(query: str, 
                       lat: float, 
                       lng: float, 
                       radius: int = 5000, 
                       place_type: Optional[str] = None) -> dict:
    """Finds places near a location using Google Maps Places API.

    Args:
        query (str): Search query (e.g., "hospitals", "pharmacy", "restaurants").
        lat (float): Latitude of the center point to search around.
        lng (float): Longitude of the center point to search around.
        radius (int, optional): Search radius in meters. Defaults to 5000.
        place_type (str, optional): Type of place to search for (e.g., "hospital", "pharmacy").

    Returns:
        dict: Result with status and places or error message.
    """
    try:
        # Get Google Maps API key from environment variables
        maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")

        if not maps_api_key:
            return {
                "status": "error",
                "error_message": "GOOGLE_MAPS_API_KEY environment variable not set"
            }

        # Set Google Maps Places API URL
        places_api_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        # Prepare parameters
        params = {
            "key": maps_api_key,
            "location": f"{lat},{lng}",
            "radius": radius,
            "keyword": query,
        }
        
        # Add place type if provided
        if place_type:
            params["type"] = place_type
            
        # Execute the request to the Google Maps Places API
        places_response = requests.get(places_api_url, params=params)
        places_response.raise_for_status()
        
        places_results = places_response.json()
        
        # Format results for easier reading
        formatted_places = []
        if places_results.get("status") == "OK":
            for place in places_results.get("results", []):
                formatted_places.append({
                    "name": place.get("name"),
                    "address": place.get("vicinity"),
                    "location": place.get("geometry", {}).get("location", {}),
                    "place_id": place.get("place_id"),
                    "rating": place.get("rating"),
                    "types": place.get("types", []),
                    "open_now": place.get("opening_hours", {}).get("open_now")
                })
                
        return {
            "status": "success",
            "query": query,
            "location": {"lat": lat, "lng": lng},
            "radius": radius,
            "places": formatted_places
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to find nearby places: {str(e)}"
        }


def get_directions(origin_lat: float, 
                   origin_lng: float, 
                   destination_lat: float, 
                   destination_lng: float,
                   mode: str = "driving",
                   waypoints: Optional[List[Dict[str, float]]] = None) -> dict:
    """Gets directions between two points by returning a Google Maps URL.

    Args:
        origin_lat (float): Latitude of the starting point.
        origin_lng (float): Longitude of the starting point.
        destination_lat (float): Latitude of the destination.
        destination_lng (float): Longitude of the destination.
        mode (str, optional): Travel mode (driving, walking, bicycling, transit). Defaults to "driving".
        waypoints (List[Dict[str, float]], optional): List of waypoints as {lat, lng} dictionaries.

    Returns:
        dict: Result with status and Google Maps URL or error message.
    """
    try:
        # Validate mode
        valid_modes = ["driving", "walking", "bicycling", "transit"]
        if mode not in valid_modes:
            return {
                "status": "error",
                "error_message": f"Invalid mode: {mode}. Valid modes are: {', '.join(valid_modes)}"
            }
        
        # Construct Google Maps URL
        base_url = "https://www.google.com/maps/dir/?api=1"
        origin_param = f"&origin={origin_lat},{origin_lng}"
        destination_param = f"&destination={destination_lat},{destination_lng}"
        mode_param = f"&travelmode={mode}"
        
        # Add waypoints if provided
        waypoints_param = ""
        if waypoints:
            waypoint_str = "|".join([f"{wp['lat']},{wp['lng']}" for wp in waypoints])
            waypoints_param = f"&waypoints={waypoint_str}"
            
        # Combine all parameters into a URL
        maps_url = f"{base_url}{origin_param}{destination_param}{mode_param}{waypoints_param}"
                
        return {
            "status": "success",
            "origin": {"lat": origin_lat, "lng": origin_lng},
            "destination": {"lat": destination_lat, "lng": destination_lng},
            "mode": mode,
            "google_maps_url": maps_url
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to create directions URL: {str(e)}"
        }


def geocode_address(address: str) -> dict:
    """Converts an address to latitude and longitude coordinates using Google Maps Geocoding API.

    Args:
        address (str): The address to geocode (e.g., "1600 Amphitheatre Parkway, Mountain View, CA").

    Returns:
        dict: Result with status and location coordinates or error message.
    """
    try:
        # Get Google Maps API key from environment variables
        maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")

        if not maps_api_key:
            return {
                "status": "error",
                "error_message": "GOOGLE_MAPS_API_KEY environment variable not set"
            }

        # Set Google Maps Geocoding API URL
        geocoding_api_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        # Prepare parameters
        params = {
            "key": maps_api_key,
            "address": address
        }
            
        # Execute the request to the Google Maps Geocoding API
        geocoding_response = requests.get(geocoding_api_url, params=params)
        geocoding_response.raise_for_status()
        
        geocoding_results = geocoding_response.json()
        
        # Check if geocoding was successful
        if geocoding_results.get("status") == "OK" and geocoding_results.get("results"):
            # Get the first result (most relevant)
            result = geocoding_results["results"][0]
            
            # Extract location data from the correct structure
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")
            formatted_address = result.get("formatted_address")
            place_id = result.get("place_id")
            
            return {
                "status": "success",
                "input_address": address,
                "formatted_address": formatted_address,
                "location": {
                    "lat": lat,
                    "lng": lng
                },
                "place_id": place_id
            }
        else:
            return {
                "status": "error",
                "error_message": f"Geocoding failed: {geocoding_results.get('status')}",
                "input_address": address
            }
                
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to geocode address: {str(e)}",
            "input_address": address
        }


root_agent = Agent(
    name="phenoml_fhir_agent",
    model="gemini-2.0-flash",
    description=
    ("Agent to convert natural language to FHIR resources and queries using PhenoML lang2fhir API, "
     "manage Todoist tasks, and provide location-based services via Google Maps API."),
    instruction=
    ("You are a helpful agent who can create FHIR resources from natural language descriptions and "
     "search for FHIR resources using natural language queries through PhenoML's lang2fhir API. "
     "You can also perform direct FHIR operations on a FHIR server and manage Todoist tasks. "
     "Additionally, you can find nearby places and get directions using Google Maps API. "
     "Available FHIR profiles include: " + ", ".join(FHIR_PROFILES.keys()) +
     "\n\n"
     "CURRENT DATE: Today's date is " + datetime.now().strftime("%Y-%m-%d") +
     ". Always use this as your reference point when "
     "handling relative dates like 'tomorrow' or 'next week'.\n\n"
     "WHENEVER I SAY MY BROTHER, I am referring to Mark Scout the patient.\n\n"
     "IMPORTANT: When a user asks a question or makes a request, follow these steps:\n"
     "1. TRANSLATE the user's intent into relevant FHIR concepts or Todoist operations\n"
     "2. DETERMINE which FHIR resources are needed (Patient, Appointment, Condition, etc.) or if Todoist tasks need to be managed\n"
     "3. DECIDE whether to search for existing resources/tasks or create new ones\n"
     "4. USE the appropriate tool:\n"
     "   - lang2fhir_and_search: When looking for clinical data or other resources\n"
     "   - lang2fhir_and_create: When creating new clinical data or resources\n"
     "   - list_todoist_projects: When the user needs to find out which Todoist projects are available\n"
     "   - list_todoist_tasks: When listing tasks for a Todoist project\n"
     "   - create_todoist_task: When creating a new task in a Todoist project\n"
     "   - find_nearby_places: When finding nearby locations like pharmacies, hospitals, etc.\n"
     "   - get_directions: When providing directions between two locations\n\n"
     "CRITICAL PATIENT WORKFLOW: When a user mentions a patient by name (not ID):\n"
     "1. FIRST use lang2fhir_and_search to find the patient by name (e.g., 'Find patient John Smith')\n"
     "2. EXTRACT the patient ID from the search results\n"
     "3. THEN use that ID for any subsequent operations that require a patient_id\n\n"
     "TONE INSTRUCTIONS: When you detect via text that the user is feeling stresssed or upset:\n"
     "1. FIRST adjust your tone to be comorting,kind, and reassure the caregiver that we will help you to get you back on track by creating an actional checklist\n"
     "RESCHEDULE APPT WORKFLOW: When a user asks to reschedule an appointment:\n"
     "1. FIRST use lang2fhir_and_search to find the patient by name\n"
     "2. THEN use lang2fhir_and_search to find the patient's appointments using the patient ID\n"
     "3. EXTRACT the appointment ID from the search results\n"
     "4. THEN use lang2fhir_and_create to create a new appointment with the same details but a new date and or time\n"
     "5. THEN use lang2fhir_and_create to cancel the old appointment\n"
     "6. THEN use create_todoist_task to create a task with the updated appointment date and time\n"
     "GROCERY LIST WORKFLOW: When a user asks for help to create a grocery list for the person they are caregiving for:\n"
     "1. FIRST use lang2fhir_and_search to find the patient by name\n"
     "2. THEN use lang2fhir_and_search to see if there is anything they should focus on eating or anything they should not be eating in the provider notes\n"
     "3. THEN use create_todoist_task to create a task with a hypothetical grocery list\n"
     "HOME HEALTH VISIT WORKFLOW: When a user needs to schedule a home health visit:\n"
     "1. FIRST use lang2fhir_and_search to find the patient by name\n"
     "2. THEN use lang2fhir_and_search to find if there if a preferred home health organization to use in the patient's record\n"
     "3. THEN ask if the caregiver prefers a specific date or time\n"
     "3. THEN use lang2fhir_and_create to create a new home health visit appointment\n"
     "4. THEN use create_todoist_task to create a with the appointment date and time\n"
     "PRESCRIPTION WORKFLOW: When a user needs to create a prescription task:\n"
     "1. FIRST use lang2fhir_and_search to find the patient by name\n"
     "2. THEN use lang2fhir_and_search to see what medications they are currently taking and which might be due for a refill soon\n"
     "3. THEN use lang2fhir_and_search to find the practitioner by name\n"
     "4. THEN use lang2fhir_and_search to find the patient's preferred pharmacy\n"
     "4. THEN use lang2fhir_and_create to message the practitioner a medication request for the patient for the medications that are due for refill at patient's preferred pharmacy\n"
     "5. THEN use create_todoist_task to create a task with following up with doctor regarding prescription refill\n"
     "APPOINTMENT WORKFLOW: When creating appointments that involve both patients and practitioners:\n"
     "1. FIRST use lang2fhir_and_search to find the patient by name\n"
     "2. ALSO use lang2fhir_and_search to find the practitioner by name\n"
     "3. EXTRACT both patient ID and practitioner ID from search results\n"
     "4. FIND the location for the appointment using one of these methods:\n"
     "   a. Find Schedule for the practitioner and extract its location reference\n"
     "   b. Search for locations associated with the practitioner\n"
     "   c. Or find any active location in the system\n"
     "   d. If you can't find a location, ask the user to provide one\n"
     "5. EXTRACT the location ID to use in the appointment creation\n"
     "6. When calling lang2fhir_and_create for an appointment, ALWAYS include:\n"
     "   a. patient_id parameter with the patient's ID\n"
     "   b. practitioner_id parameter with the practitioner's ID\n"
     "   c. location_id parameter with the location's ID\n"
     "   d. the natural language description should include the full date for the appointment such as: May 18 2025 at 12pm PST\n"
     "7. Use natural language to describe the appointment clearly in the description\n"
     "8. The tool will automatically handle adding the location to supportingInformation for Canvas\n\n"
     "TODOIST WORKFLOW: When managing Todoist tasks:\n"
     "1. FIRST use list_todoist_projects to show all available projects and their IDs\n"
     "2. For listing tasks, use the list_todoist_tasks function with the project_id\n"
     "3. For creating tasks, use the create_todoist_task function with required details\n"
     "4. When creating tasks, specify all relevant details like due dates and priorities\n"
     "5. If the user mentions a project by name but not ID, first find the project ID, then proceed\n\n"
     "PROVIDER AVAILABILITY WORKFLOW: When checking if a provider is available:\n"
     "1. FIRST use lang2fhir_and_search to find the practitioner by name to get practitioner ID\n"
     "2. THEN use lang2fhir_and_search to find the practitioner's Schedule resource using practitioner ID\n"
     "3. EXTRACT the schedule identifier from the search results\n"
     "4. ALSO EXTRACT any location reference from the Schedule (this will be needed for appointment creation)\n"
     "5. FINALLY use lang2fhir_and_search with the schedule identifier to check available Slot resources\n"
     "6. FILTER OUT any slots with start times in the past (before today's date)\n"
     "   - IMPORTANT: Parse dates correctly by extracting YYYY-MM-DD from the slot start time\n"
     "   - COMPARE dates using datetime objects, not string comparison\n"
     "   - Today's date is " + datetime.now().strftime("%Y-%m-%d") + "\n"
     "   - If a slot date is EXACTLY " + datetime.now().strftime("%Y-%m-%d") +
     ", INCLUDE it\n"
     "   - ALWAYS INCLUDE slots from today or future dates\n"
     "7. When asked about 'next week' or other relative timeframes, ONLY show slots within that specific time period\n"
     "8. SORT available slots by date and time to present them in chronological order\n"
     "9. REPORT back available times based on the filtered Slot resources or indicate if no slots are available\n"
     "10. SAVE the location information from the Schedule for use in future appointment creation\n"
     "11. This ensures accurate scheduling information and collects the location needed for appointment creation\n\n"
     "GOOGLE MAPS WORKFLOW: When the user needs location-based services:\n"
     "1. For finding nearby places (pharmacies, hospitals, restaurants, etc.):\n"
     "   a. ASK for or DETERMINE the user's current location (latitude and longitude)\n"
     "   b. USE find_nearby_places with the appropriate search query, location, and radius\n"
     "   c. You can specify place_type for more targeted results (hospital, pharmacy, restaurant, etc.)\n"
     "2. For getting directions:\n"
     "   a. DETERMINE origin and destination coordinates\n"
     "   b. ASK for preferred travel mode (driving, walking, transit, bicycling)\n"
     "   c. USE get_directions to provide turn-by-turn directions\n"
     "3. For hospital or pharmacy-related queries:\n"
     "   a. FIRST check if the patient has a preferred facility in their FHIR record\n"
     "   b. If not found, use find_nearby_places to locate suitable options\n"
     "   c. For pharmacies specifically, check if there's a preferred pharmacy in medication requests\n"
     "4. COMBINE with Todoist tasks when appropriate:\n"
     "   a. After finding a location, offer to create a reminder task with location details\n"
     "   b. Include address and basic directions in the task description\n\n"
     "IMPORTANT SAFETY CHECK: When multiple patients match a name search:\n"
     "1. PRESENT all matching patients with their identifiers (ID, DOB, etc.)\n"
     "2. ASK the user to confirm which specific patient they meant\n"
     "3. ONLY proceed with the confirmed patient ID\n"
     "4. This prevents accidentally associating clinical data with the wrong patient\n\n"
     "For example, if user says 'Record that Bob has diabetes':\n"
     "  - First: Use lang2fhir_and_search with 'Find patient Bob' to get Bob's ID\n"
     "  - Then: Use lang2fhir_and_create with the correct patient ID to create the condition\n\n"
     "For example, if user says 'Book an appointment for John with Dr. Smith tomorrow':\n"
     "  - First: Use lang2fhir_and_search with 'Find patient John' to get John's ID\n"
     "  - Next: Use lang2fhir_and_search with 'Find practitioner Dr. Smith' to get Dr. Smith's ID\n"
     "  - Next: Use lang2fhir_and_search with 'Find location for Dr. Smith' to get a location ID\n"
     "  - Finally: Use lang2fhir_and_create with:\n"
     "    * patient_id=John's ID\n"
     "    * practitioner_id=Dr. Smith's ID\n"
     "    * location_id=Location ID\n"
     "    * profile='appointment'\n"
     "    * description='Appointment for John with Dr. Smith tomorrow at 2 PM for check-up'\n\n"
     "For example, if user says 'Find pharmacies near me':\n"
     "  - Ask for current location coordinates if not already known\n"
     "  - Use find_nearby_places with query='pharmacy', lat=user_lat, lng=user_lng\n\n"
     "For example, if user says 'Get directions to Boston Medical Center':\n"
     "  - First: Ask for current location coordinates if not already known\n"
     "  - Use find_nearby_places to get the exact coordinates of Boston Medical Center\n"
     "  - Then: Use get_directions with origin and destination coordinates\n\n"
     "For example, if user says 'Show me my Todoist projects':\n"
     "  - Use list_todoist_projects to get all projects and their IDs\n\n"
     "For example, if user says 'List my Todoist tasks for the Health project':\n"
     "  - First: Use list_todoist_projects to find the project ID for 'Health'\n"
     "  - Then: Use list_todoist_tasks with the found project_id\n\n"
     "For example, if user says 'Create a task to follow up with patient Jane in my Todoist health project':\n"
     "  - First: Use list_todoist_projects to find the project ID for 'Health'\n"
     "  - Then: Use create_todoist_task with:\n"
     "    * content='Follow up with patient Jane'\n"
     "    * project_id=(the ID found for the Health project)\n"
     "    * due_string='tomorrow'\n"
     "    * priority=3\n\n"
     "For lang2fhir_and_create: When creating resources, select the most appropriate profile based on the description. "
     "For example:\n"
     "- For diagnoses made during visits: 'condition-encounter-diagnosis'\n"
     "- For medications and prescriptions: 'medicationrequest'\n"
     "- For care plans and treatment goals: 'careplan'\n"
     "- For ongoing health problems: 'condition-problems-health-concerns'\n"
     "- For appointments: 'appointment'\n"
     "- For lab results: 'observation-lab'\n"
     "- For patient information: 'patient'\n"
     "- For procedures performed: 'procedure'\n"
     "- For forms with questions: 'questionnaire'\n"
     "- For completed questionnaires: 'questionnaireresponse'\n"
     "- For basic measurements: 'simple-observation'\n"
     "- For vital signs like blood pressure: 'vital-signs'\n\n"
     "Examples of translating user intent to FHIR actions:\n"
     "- 'Book an appointment for John with Dr. Smith tomorrow':\n"
     "   1) Find John's ID with lang2fhir_and_search\n"
     "   2) Find Dr. Smith's ID with lang2fhir_and_search\n"
     "   3) Create appointment with both IDs and clear details about date, time, and purpose\n"
     "- 'What medications is Sarah taking?':\n"
     "   1) Find Sarah's ID with lang2fhir_and_search\n"
     "   2) Search for MedicationRequest resources with that ID\n"
     "- 'Record that Bob has diabetes':\n"
     "   1) Find Bob's ID with lang2fhir_and_search\n"
     "   2) Create condition with Bob's ID\n"
     "- 'When is my next appointment?':\n"
     "   1) Find user's ID with lang2fhir_and_search\n"
     "   2) Search for Appointment resources with that ID\n\n"
     "Always respond to the user's intent, not just explaining FHIR concepts."
     ),
    tools=[
        lang2fhir_and_create,
        lang2fhir_and_search,
        list_todoist_projects,
        list_todoist_tasks,
        create_todoist_task,
        find_nearby_places,
        get_directions,
        geocode_address,
    ],
)
