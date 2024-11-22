# api_calls.py
import openai
import numpy as np
import spacy
import logging
import json
import re

# Set up logging
logging.basicConfig(level=logging.INFO)

# LLM Interface
class LLMInterface:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def generate(self, prompt):
        raise NotImplementedError("LLMInterface.generate method must be overridden.")

# GPT-4 LLM Implementation
class GPT4LLM(LLMInterface):
    def __init__(self, api_key):
        super().__init__(api_key)
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided.")
        openai.api_key = self.api_key

    def generate(self, prompt):
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Ensure you have access to GPT-4
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.0,
        )
        return response.choices[0].message['content'].strip()

# Load embeddings from a file
def load_embeddings(embedding_file):
    embeddings = {}
    with open(embedding_file, 'r') as f:
        for line in f:
            tokens = line.strip().split()
            word = tokens[0]
            vector = [float(x) for x in tokens[1:]]
            embeddings[word] = vector
    return embeddings

# Parse input text to extract actions and negations
def parse_input_text(input_text):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(input_text)
    actions = []
    negations = []
    for token in doc:
        if token.dep_ == 'neg' and token.head.pos_ == 'VERB':
            negations.append(token.head.lemma_)
        if token.pos_ == 'VERB':
            actions.append(token.lemma_)
    return actions, negations

# Compute cosine similarity
def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Exclude modules similar to negated actions
def exclude_negated_modules(negations, action_embeddings, module_embeddings, threshold=0.5):
    excluded_modules = set()
    for action in negations:
        if action in action_embeddings:
            action_embedding = action_embeddings[action]
            for module_name, module_embedding in module_embeddings.items():
                sim = cosine_similarity(action_embedding, module_embedding)
                if sim > threshold:
                    excluded_modules.add(module_name)
    return excluded_modules

# Select modules based on similarities
def select_modules(actions, negations, action_embeddings, module_embeddings, top_k=3, exclusion_threshold=0.5):
    excluded_modules = exclude_negated_modules(
        negations, action_embeddings, module_embeddings, threshold=exclusion_threshold)
    selected_modules = []
    for action in actions:
        if action in negations:
            continue  # Skip negated actions
        if action not in action_embeddings:
            logging.warning(f"No embedding found for action '{action}'. Skipping.")
            continue
        action_embedding = action_embeddings[action]
        similarities = {}
        for module_name, module_embedding in module_embeddings.items():
            if module_name in excluded_modules:
                continue  # Skip excluded modules
            sim = cosine_similarity(action_embedding, module_embedding)
            similarities[module_name] = sim
        # Sort modules by similarity
        sorted_modules = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        # Select top_k modules
        top_modules = [module for module, sim in sorted_modules[:top_k]]
        selected_modules.extend(top_modules)
    # Remove duplicates
    selected_modules = list(set(selected_modules))
    return selected_modules

# Extract parameters using GPT
def extract_parameters_with_gpt(input_text, module_name, llm):
    prompt = f"""
Given the instruction: "{input_text}"

Extract the parameters required for the module "{module_name}" in the format of a JSON object.

The parameters should match the following schema based on the module:

For 'pick':
{{
  "container": {{
    "type": string,
    "id": string (if available),
    "content_name": string (if available),
    "content_volume": string (if available),
    "content_color": string (if available),
    "position": string (e.g., "(x, y, z)" if available),
    "landmark": string (if available)
  }}
}}

For 'place':
{{
  "container": {{
    "type": string,
    "id": string (if available),
    "content_name": string (if available),
    "content_volume": string (if available),
    "content_color": string (if available),
    "position": string (if available),
    "landmark": string (if available)
  }},
  "destination_location": string (e.g., "(x, y, z)" if available),
  "landmark": string (if available)
}}

For 'moveto':
{{
  "original_container": {{
    "type": string,
    "id": string (if available),
    "position": string (if available),
    "landmark": string (if available)
  }},
  "destination": string (e.g., "(x, y, z)" if available),
  "landmark": string (if available)
}}

For 'pour':
{{
  "original_container": {{
    "type": string (if available),
    "id": string (if available),
    "content_name": string (if available),
    "content_volume": string (if available),
    "content_color": string (if available),
    "position": string (if available),
    "landmark": string (if available)
  }},
  "destination_container": {{
    "type": string (if available),
    "id": string (if available),
    "position": string (if available),
    "landmark": string (if available)
  }},
  "volume": string (e.g., "all" or specific amount)
}}

Important rules:
- If an (x, y, z) position is provided in the instruction, set 'position' to that value.
- If no (x, y, z) position is provided, set 'position' to 'none'.
- For 'place' and 'moveto' modules:
  - If an (x, y, z) position is provided for the destination, set 'destination_location' or 'destination' to that value.
  - If no (x, y, z) position is provided, set 'destination_location' or 'destination' to 'none', even if a landmark like 'table' is mentioned.
- 'landmark' can be set if a landmark is mentioned.

Please provide the parameters as a JSON object.

If a parameter is not available from the instruction, you can omit it or set it to null.
"""

    response = llm.generate(prompt)
    # Parse the JSON from the response
    try:
        # Extract JSON from the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            parameters_json = json_match.group()
            parameters = json.loads(parameters_json)
            return parameters
        else:
            logging.warning(f"Could not extract JSON parameters from GPT response: {response}")
            return {}
    except Exception as e:
        logging.warning(f"Error parsing parameters from GPT response: {e}")
        return {}

# Post-process parameters to enforce 'destination_location' rule
def post_process_parameters(parameters, module_name):
    if module_name in ['place', 'moveto']:
        # For 'place' module
        if module_name == 'place':
            if 'destination_location' in parameters:
                dest_loc = parameters['destination_location']
                # If 'destination_location' is not in (x, y, z) format, set it to 'none'
                if not re.match(r'^\(\s*-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?\s*\)$', str(dest_loc)):
                    parameters['destination_location'] = 'none'
        # For 'moveto' module
        if module_name == 'moveto':
            if 'destination' in parameters:
                dest = parameters['destination']
                # If 'destination' is not in (x, y, z) format, set it to 'none'
                if not re.match(r'^\(\s*-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?\s*\)$', str(dest)):
                    parameters['destination'] = 'none'
    return parameters

# Generate the sequence of modules with parameters using GPT
def generate_module_sequence_with_parameters(selected_modules, input_text, llm):
    module_sequence = []
    for module in selected_modules:
        parameters = extract_parameters_with_gpt(input_text, module, llm)
        if not parameters:
            continue  # Skip if parameters could not be extracted
        # Post-process parameters to enforce 'destination_location' rule
        parameters = post_process_parameters(parameters, module)
        # Convert parameters to string representation
        params_str = json.dumps(parameters)
        module_call = f"{module}({params_str})"
        module_sequence.append(module_call)
    # Return the sequence as a single string separated by commas
    return ', '.join(module_sequence)

# Process instructions function
def process_instructions(input_text, embedding_file='keyword_to_module.txt', module_names=['pick', 'place', 'moveto', 'pour'], api_key=None):
    # Load embeddings
    embeddings = load_embeddings(embedding_file)

    # Extract module embeddings
    module_embeddings = {name: embeddings[name] for name in module_names if name in embeddings}
    missing_modules = set(module_names) - set(module_embeddings.keys())
    if missing_modules:
        raise ValueError(f"Embeddings for modules {missing_modules} not found in the embedding file.")

    # Parse input text
    actions, negations = parse_input_text(input_text)
    logging.info(f"Actions: {actions}")
    logging.info(f"Negations: {negations}")

    # Collect unique action words
    unique_actions = set(actions + negations)

    # Extract action embeddings
    action_embeddings = {action: embeddings[action] for action in unique_actions if action in embeddings}
    missing_actions = unique_actions - set(action_embeddings.keys())
    if missing_actions:
        logging.warning(f"Embeddings for actions {missing_actions} not found in the embedding file.")

    # Select modules
    selected_modules = select_modules(actions, negations, action_embeddings, module_embeddings)
    logging.info(f"Selected Modules: {selected_modules}")

    if not selected_modules:
        raise ValueError("No modules selected. Cannot generate module sequence.")

    # Initialize LLM
    llm = GPT4LLM(api_key=api_key)

    # Generate module sequence with parameters using GPT
    module_sequence = generate_module_sequence_with_parameters(selected_modules, input_text, llm)

    # Log the final module sequence
    logging.info(f"Final Module Sequence: {module_sequence}")

    return module_sequence
