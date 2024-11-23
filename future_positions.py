import yaml
import re

# Load containers from YAML file
with open(r'Downloads\container_assets.yaml', 'r') as file:
    containers_data = yaml.safe_load(file)
containers = containers_data['containers']

# Sample module sequence as a string
module_sequence = '''
pick(container={ id: "B", aruco_id: "102" })

pour(original_container={ id: "B", aruco_id: "102" }, destination_container={ id: "A", aruco_id: "101" }, volume="half")

place(container={ id: "B", aruco_id: "102" }, destination_location=(1,2,3))
'''

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
    in_quotes = False
    quote_char = ''
    for c in s:
        if c in '"\'':
            if in_quotes and c == quote_char:
                in_quotes = False
            elif not in_quotes:
                in_quotes = True
                quote_char = c
        elif c == ',' and bracket_level == 0 and not in_quotes:
            result.append(current.strip())
            current = ''
            continue
        elif not in_quotes:
            if c in '([{':
                bracket_level += 1
            elif c in ')]}':
                bracket_level -= 1
        current += c
    if current.strip():
        result.append(current.strip())
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

# Function to find a container by id
def find_container_by_id(containers, container_id):
    for container in containers:
        if container['id'] == container_id:
            return container
    return None

# Function to simulate module execution
def simulate_modules(modules, containers):
    # Copy the containers list to avoid modifying the original data
    containers_state = [container.copy() for container in containers]

    # Keep track of container positions after each module
    positions_after_each_module = []

    for module_name, params in modules:
        if module_name == 'pick':
            # Optionally, set an 'active' status or similar
            pass  # For this example, 'pick' doesn't change position
        elif module_name == 'moveto':
            # Update container position
            container_info = params.get('original_container')
            destination = params.get('destination')
            if container_info and destination:
                container = find_container_by_id(containers_state, container_info['id'])
                if container:
                    container['position'] = destination
        elif module_name == 'place':
            # Update container position
            container_info = params.get('container')
            destination_location = params.get('destination_location')
            if container_info and destination_location:
                container = find_container_by_id(containers_state, container_info['id'])
                if container:
                    container['position'] = destination_location
        elif module_name == 'pour':
            # Update contents of containers
            original_container_info = params.get('original_container')
            destination_container_info = params.get('destination_container')
            volume = params.get('volume')
            if original_container_info and destination_container_info:
                orig_container = find_container_by_id(containers_state, original_container_info['id'])
                dest_container = find_container_by_id(containers_state, destination_container_info['id'])
                if orig_container and dest_container:
                    # Simplified logic for 'half' volume
                    if volume == 'half':
                        transfer_volume = orig_container['content_volume'] / 2
                    elif volume == 'all':
                        transfer_volume = orig_container['content_volume']
                    else:
                        try:
                            transfer_volume = float(volume)
                        except ValueError:
                            transfer_volume = 0
                    # Update volumes
                    orig_container['content_volume'] -= transfer_volume
                    dest_container['content_volume'] += transfer_volume
                    # Update content names if needed (simplified logic)
                    dest_container['content_name'] = orig_container['content_name']
                    dest_container['content_color'] = orig_container['content_color']
        # Record the positions after this module execution
        positions = {container['id']: container['position'] for container in containers_state}
        positions_after_each_module.append((module_name, positions))

    return positions_after_each_module, containers_state

# Parse the module sequence
def parse_module_sequence(module_sequence):
    module_calls = re.findall(r'(\w+\(.*?\))', module_sequence, re.DOTALL)
    modules = []
    for module_call in module_calls:
        module_name, params = parse_module_call(module_call)
        if module_name:
            modules.append((module_name, params))
    return modules

# Main execution
modules = parse_module_sequence(module_sequence)
positions_after_each_module, final_containers_state = simulate_modules(modules, containers)

# Output positions after each module
print("Container Positions After Each Module Execution:")
for i, (module_name, positions) in enumerate(positions_after_each_module):
    print(f"After '{module_name}' module:")
    for container_id, position in positions.items():
        print(f"  Container {container_id}: Position {position}")
    print()

# Output the final state of containers
print("Final State of Containers:")
for container in final_containers_state:
    print(f"Container {container['id']}:")
    print(f"  Position: {container['position']}")
    print(f"  Content Volume: {container['content_volume']}")
    print(f"  Content Name: {container['content_name']}")
    print(f"  Content Color: {container['content_color']}")
    print()
