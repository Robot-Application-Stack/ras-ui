# api_calls.py

import openai

# Function to generate module sequence using GPT-4
def generate_module_sequence(input_instruction, api_key):
    # Initialize OpenAI API key
    openai.api_key = api_key

    # Elaborate prompt to guide GPT-4
    prompt = f"""
You are an AI assistant that converts natural language instructions into a sequence of module calls with appropriate parameters.

**Available Modules:**

1. **pick**:
   - **Parameters**:
     - container: A dictionary with the following keys:
       - type: The type of container (e.g., "beaker", "test tube").
       - size: Any size information if provided; otherwise, "null"
       - content name: Name of the contents (e.g., "copper sulphate solution") if specified, otherwise "null" (**note: "null" is not the same as "empty", treat "empty" as a content name)
       - content color: Color of the contents (e.g., "blue") if specified, otherwise "null"
       - content volume: Volume of the content if specified, otherwise "null"
       - landmark: A landmark if specified; otherwise "null".
   - **Usage**:
     
pick(container={{type: ..., size: ..., content name: ..., content color: ..., content volume: ..., landmark: ...}})


2. **pour**:
   - **Parameters**:
     - original_container: A dictionary similar to the container in pick.
     - destination_container: A dictionary for the destination container. Use "active container" if not specified.
     - volume: The volume to pour; use "all" if not specified.
   - **Usage**:
     
pour(original_container={{...}}, conten, destination_container={{...}}, volume=...)


3. **place**:
   - **Parameters**:
     - container: A dictionary similar to the container in pick.
     - destination_location: The destination location if an (x, y, z) coordinate is provided; otherwise, "none".
     - landmark: A landmark if specified; otherwise, "null".
   - **Usage**: 
     
place(container={{...}}, destination_location=..., landmark=...)


4. **moveto**:
   - **Parameters**:
     - original_container: A dictionary similar to the container in pick.
     - destination: The destination if an (x, y, z) coordinate is provided; otherwise, "null".
     - landmark: A landmark if specified; otherwise, "null".
   - **Usage**:
     
moveto(original_container={{...}}, destination=..., landmark=...)


**Instructions:**

- **Extract as much information as possible** from the input instruction to fill the parameters.
- **If a parameter is not specified**, use the default values as described.
- **Do not query any external data sources**; rely solely on the input instruction.
- **Handle negations** appropriately. If an action is negated in the instruction (e.g., "Do not pour"), do not include that module in the sequence.
- **Sequence the modules** in the order that makes sense based on the instruction.

**Now, process the following instruction and generate the module sequence:**

\"\"\"{input_instruction}\"\"\"
"""

    # Call GPT-4 to generate the module sequence
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.0,
        n=1,
        stop=None
    )

    # Extract and return the generated module sequence
    module_sequence = response['choices'][0]['message']['content'].strip()
    return module_sequence
