from flask import Flask, request, jsonify
import sys
import os
import json
import logging
import requests
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents', '.env')
logger.debug(f"Loading environment variables from: {env_path}")
if not os.path.exists(env_path):
    logger.error(f".env file not found at {env_path}")
else:
    load_dotenv(env_path)
    logger.debug("Environment variables loaded from .env file")

app = Flask(__name__)

# Enable CORS for all routes with a very permissive configuration
CORS(app, 
     resources={r"/*": {
         "origins": "*",
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type"],
         "expose_headers": ["Content-Type"]
     }})

# ADK API server URL
ADK_API_URL = "http://localhost:8000"

@app.before_request
def log_request_info():
    logger.debug('Request path: %s', request.path)
    logger.debug('Request method: %s', request.method)
    logger.debug('Request headers: %s', dict(request.headers))
    logger.debug('Request body: %s', request.get_data())

@app.after_request
def after_request(response):
    logger.debug('Response status: %s', response.status)
    logger.debug('Response headers: %s', dict(response.headers))
    return response

@app.route('/api/test', methods=['GET', 'OPTIONS'])
def test():
    logger.debug("Test endpoint called")
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
        
    return jsonify({"status": "ok", "message": "Server is running"})

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
@cross_origin()
def chat():
    logger.debug(f"Received {request.method} request to /api/chat")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    if request.method == 'OPTIONS':
        logger.debug("Handling OPTIONS request")
        return jsonify({'status': 'ok'})
        
    try:
        data = request.json
        logger.debug(f"Request data: {data}")
        message = data.get('message', '')
        
        if not message:
            logger.error("No message provided in request")
            return jsonify({'error': 'No message provided'}), 400
        
        # Check environment variables
        missing_vars = check_environment()
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 500
        
        # Log the environment variables being passed (without values)
        env_vars = {k: bool(v) for k, v in os.environ.items() if k in ['PHENOML_TOKEN', 'MEDPLUM_TOKEN', 'CANVAS_TOKEN', 'CANVAS_INSTANCE_IDENTIFIER']}
        logger.debug(f"Environment variables being used: {env_vars}")
        
        # Create a session if it doesn't exist
        session_url = f"{ADK_API_URL}/apps/multi_lang2fhir_agent/users/default/sessions/default"
        logger.debug(f"Creating session at {session_url}")
        session_response = requests.post(session_url)
        if session_response.status_code != 200:
            logger.error(f"Failed to create session: {session_response.text}")
            return jsonify({'error': 'Failed to create agent session'}), 500
        
        # Send the message to the agent
        run_url = f"{ADK_API_URL}/run"
        run_data = {
            "app_name": "multi_lang2fhir_agent",
            "user_id": "default",
            "session_id": "default",
            "new_message": {
                "role": "user",
                "parts": [{
                    "text": message
                }]
            }
        }
        logger.debug(f"Sending message to agent at {run_url}")
        run_response = requests.post(run_url, json=run_data)
        if run_response.status_code != 200:
            logger.error(f"Failed to run agent: {run_response.text}")
            return jsonify({'error': 'Failed to run agent'}), 500
        
        # Extract the final response from the events
        events = run_response.json()
        final_response = None
        for event in reversed(events):
            if event.get('content', {}).get('parts', [{}])[0].get('text'):
                final_response = event['content']['parts'][0]['text']
                break
        
        if not final_response:
            logger.error("No response text found in events")
            return jsonify({'error': 'No response from agent'}), 500
        
        logger.debug(f"Agent response: {final_response}")
        return jsonify({'response': final_response})
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = ['PHENOML_TOKEN']
    optional_vars = ['MEDPLUM_TOKEN', 'CANVAS_TOKEN', 'CANVAS_INSTANCE_IDENTIFIER']
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
        else:
            logger.debug(f"Found {var} environment variable")
    
    # Check that exactly one of MEDPLUM_TOKEN or CANVAS_TOKEN is set
    has_medplum = bool(os.environ.get('MEDPLUM_TOKEN'))
    has_canvas = bool(os.environ.get('CANVAS_TOKEN'))
    
    if not (has_medplum or has_canvas):
        missing.append('MEDPLUM_TOKEN or CANVAS_TOKEN')
    elif has_medplum and has_canvas:
        missing.append('Only one of MEDPLUM_TOKEN or CANVAS_TOKEN should be set')
    
    if has_canvas and not os.environ.get('CANVAS_INSTANCE_IDENTIFIER'):
        missing.append('CANVAS_INSTANCE_IDENTIFIER (required when using CANVAS_TOKEN)')
    
    return missing

@app.route('/test-env', methods=['GET'])
def test_env():
    """Test endpoint to verify environment variables."""
    env_vars = {
        'PHENOML_TOKEN': bool(os.environ.get('PHENOML_TOKEN')),
        'MEDPLUM_TOKEN': bool(os.environ.get('MEDPLUM_TOKEN')),
        'CANVAS_TOKEN': bool(os.environ.get('CANVAS_TOKEN')),
        'CANVAS_INSTANCE_IDENTIFIER': bool(os.environ.get('CANVAS_INSTANCE_IDENTIFIER'))
    }
    return jsonify(env_vars)

if __name__ == '__main__':
    app.run(port=5000, debug=True, host='0.0.0.0') 