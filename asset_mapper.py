import yaml
import re

# Sample module sequence as a string
module_sequence = '''
pick(container={type: "beaker", size: "null", content_name: "null", content_color: "blue", content_volume: "null", landmark: "null"})

pour(original_container={type: "beaker", size: "null", content_name: "null", content_color: "blue", content_volume: "null", landmark: "null"}, destination_container={type: "beaker", size: "null", content_name: "empty", content_color: "null", content_volume: "null", landmark: "null"}, volume="half")

place(container={type: "beaker", size: "null", content_name: "null", content_color: "blue", content_volume: "null", landmark: "null"}, destination_location=(1,2,3), landmark="null")
'''

# Load containers from YAML file
with open(r'Downloads/container_assets.yaml', 'r') as file:
    containers_data = yaml.safe_load(file)
containers = containers_data['containers']

# Function to parse parameters
def parse_parameters(parameters_string):
    try:
        # Replace Python-style dictionary with YAML-compatible format
        parameters_string = re.sub(r'(\w+):', r'"\1":', parameters_string)  # Quote keys
        parameters_string = parameters_string.replace("=", ":")  # Replace = with :
        parameters_string = f"{{{parameters_string}}}"  # Add outer braces
        # Parse the resulting string as YAML
        params_dict = yaml.safe_load(parameters_string)
        return params_dict
    except Exception as e:
        print(f"Error parsing parameters: {e}")
        return {}

# Function to match container descriptions to actual containers
def match_container(container_desc, containers):
    # Remove fields with value "null"
    criteria = {k: v for k, v in container_desc.items() if v != "null"}
    matching_containers = []
    for container in containers:
        match = all(
            str(container.get(key, "")).lower() == str(value).lower()
            for key, value in criteria.items()
        )
        if match:
            matching_containers.append(container)
    if len(matching_containers) == 1:
        return matching_containers[0]
    elif len(matching_containers) > 1:
        print(f"Warning: Multiple containers match criteria {criteria}. Selecting the first.")
        return matching_containers[0]
    else:
        return None

# Function to format parameters back into a string
def format_parameters(params):
    formatted_params = []
    for key, value in params.items():
        if isinstance(value, dict):
            # Format nested dictionaries
            nested = ", ".join(f'{k}: "{v}"' for k, v in value.items())
            formatted_params.append(f"{key}={{ {nested} }}")
        elif isinstance(value, tuple):
            # Format tuples (e.g., positions)
            tuple_string = ", ".join(str(v) for v in value)
            formatted_params.append(f"{key}=({tuple_string})")
        elif isinstance(value, str) and not value.isdigit():
            # Add quotes around string values
            formatted_params.append(f'{key}="{value}"')
        else:
            # Leave numeric or other values as-is
            formatted_params.append(f"{key}={value}")
    return ", ".join(formatted_params)

# Main processing
def process_module_sequence(module_sequence, containers):
    module_calls = re.findall(r"(\w+)\((.*?)\)", module_sequence, re.DOTALL)
    updated_module_sequence = ""
    for module_name, parameters_string in module_calls:
        params = parse_parameters(parameters_string)
        for param_name, param_value in params.items():
            if param_name in ["container", "original_container", "destination_container"]:
                matching_container = match_container(param_value, containers)
                if matching_container:
                    params[param_name] = {
                        "id": matching_container["id"],
                        "aruco_id": matching_container["aruco_id"],
                    }
                else:
                    print(f"No matching container found for {param_name} in {module_name}")
                    params[param_name] = {"id": "unknown", "aruco_id": "unknown"}
        # Reconstruct module call
        formatted_params = format_parameters(params)
        module_call = f"{module_name}({formatted_params})"
        updated_module_sequence += module_call + "\n\n"
    return updated_module_sequence.strip()

# Run the processing
final_module_sequence = process_module_sequence(module_sequence, containers)

# Output the final module sequence
print("Final Module Sequence:")
print(final_module_sequence)
