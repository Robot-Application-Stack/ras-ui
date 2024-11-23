import yaml
import re

# Load containers from YAML file
with open(r'Downloads/container_assets.yaml', 'r') as file:
    containers_data = yaml.safe_load(file)
containers = containers_data['containers']

# Function to parse module calls
def parse_module_call(module_call_str):
    try:
        # Extract the function name and parameters
        match = re.match(r'(\w+)\((.*)\)', module_call_str.strip(), re.DOTALL)
        if not match:
            print(f"Error parsing module call '{module_call_str}': Invalid format")
            return None, {}
        func_name = match.group(1)
        params_str = match.group(2)

        # Split parameters at the top level
        param_list = split_top_level(params_str)
        params = {}
        for param in param_list:
            if '=' not in param:
                continue
            key, value = param.split('=', 1)
            key = key.strip()
            value = value.strip()
            # Parse the value
            parsed_value = parse_value(value)
            params[key] = parsed_value
        return func_name, params
    except Exception as e:
        print(f"Error parsing module call '{module_call_str}': {e}")
        return None, {}

# Function to split parameters at the top level
def split_top_level(s):
    result = []
    bracket_level = 0
    current = ''
    for c in s:
        if c == ',' and bracket_level == 0:
            result.append(current)
            current = ''
        else:
            current += c
            if c in '([{':
                bracket_level += 1
            elif c in ')]}':
                bracket_level -= 1
    if current:
        result.append(current)
    return result

# Function to parse individual values
def parse_value(value_str):
    value_str = value_str.strip()
    # Handle dictionaries
    if value_str.startswith('{') and value_str.endswith('}'):
        return parse_dict(value_str)
    # Handle tuples or lists
    elif value_str.startswith('(') and value_str.endswith(')'):
        return parse_tuple(value_str)
    elif value_str.startswith('[') and value_str.endswith(']'):
        return parse_list(value_str)
    # Handle strings
    elif (value_str.startswith("'") and value_str.endswith("'")) or (value_str.startswith('"') and value_str.endswith('"')):
        return value_str[1:-1]
    # Handle numbers
    else:
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            return value_str  # Return as string if not a number

# Function to parse dictionaries
def parse_dict(dict_str):
    dict_str = dict_str.strip()[1:-1].strip()  # Remove braces
    items = split_top_level(dict_str)
    result = {}
    for item in items:
        if ':' not in item:
            continue
        key, value = item.split(':', 1)
        key = key.strip().strip('\'"')  # Remove quotes from keys
        value = value.strip()
        result[key] = parse_value(value)
    return result

# Function to parse tuples
def parse_tuple(tuple_str):
    tuple_str = tuple_str.strip()[1:-1].strip()  # Remove parentheses
    items = split_top_level(tuple_str)
    return tuple(parse_value(item) for item in items)

# Function to parse lists
def parse_list(list_str):
    list_str = list_str.strip()[1:-1].strip()  # Remove brackets
    items = split_top_level(list_str)
    return [parse_value(item) for item in items]

# Function to match container descriptions to actual containers
def match_container(container_desc, containers):
    # Remove fields with value 'null' or None
    criteria = {k: v for k, v in container_desc.items() if v != 'null' and v is not None}
    matching_containers = []
    for container in containers:
        match = all(
            str(container.get(key, '')).lower() == str(value).lower()
            for key, value in criteria.items()
        )
        if match:
            matching_containers.append(container)
    if len(matching_containers) == 1:
        return matching_containers[0]
    elif len(matching_containers) == 0:
        return None
    else:
        # Multiple matches; select the first one or implement additional logic
        return matching_containers[0]

# Function to format parameters back into a string
def format_parameters(params):
    formatted_params = []
    for key, value in params.items():
        if value is None or value == 'null':
            continue  # Skip unnecessary None or 'null' values
        if isinstance(value, dict):
            # Format nested dictionaries
            nested = ', '.join(f'{k}: "{v}"' for k, v in value.items())
            formatted_params.append(f"{key}={{ {nested} }}")
        elif isinstance(value, (tuple, list)):
            # Format tuples or lists (e.g., positions)
            tuple_string = ', '.join(str(v) for v in value if v is not None)
            formatted_params.append(f"{key}=({tuple_string})")
        elif isinstance(value, str):
            # Add quotes around string values
            formatted_params.append(f'{key}="{value}"')
        else:
            # Leave numeric or other values as-is
            formatted_params.append(f"{key}={value}")
    return ', '.join(formatted_params)

# Main processing
def process_module_sequence(module_sequence, containers):
    # Split the module sequence into individual module calls
    module_calls = re.findall(r'(\w+\(.*?\))', module_sequence, re.DOTALL)
    updated_module_sequence = ""
    for module_call in module_calls:
        module_name, params = parse_module_call(module_call)
        if not module_name:
            continue  # Skip if parsing failed
        # Process the parameters
        for param_name, param_value in params.items():
            if param_name in ['container', 'original_container', 'destination_container']:
                matching_container = match_container(param_value, containers)
                if matching_container:
                    params[param_name] = {
                        'id': matching_container['id'],
                        'aruco_id': str(matching_container['aruco_id']),
                    }
                else:
                    print(f"No matching container found for {param_name} in {module_name}")
                    params[param_name] = {'id': 'unknown', 'aruco_id': 'unknown'}
        # Reconstruct the module call
        formatted_params = format_parameters(params)
        module_call_str = f"{module_name}({formatted_params})"
        updated_module_sequence += module_call_str + "\n\n"
    return updated_module_sequence.strip()

# Sample module sequence as a string
module_sequence = '''
pick(container={type: "beaker", size: "null", content_name: "null", content_color: "blue", content_volume: "null", landmark: "null"})

pour(original_container={type: "beaker", size: "null", content_name: "null", content_color: "blue", content_volume: "null", landmark: "null"}, destination_container={type: "beaker", size: "null", content_name: "empty", content_color: "null", content_volume: "null", landmark: "null"}, volume="half")

place(container={type: "beaker", size: "null", content_name: "null", content_color: "blue", content_volume: "null", landmark: "null"}, destination_location=(1,2,3))
'''

# Run the processing
final_module_sequence = process_module_sequence(module_sequence, containers)

# Output the final module sequence
print("Final Module Sequence:")
print(final_module_sequence)
