from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# 1. Load the model and tokenizer
# The Babelscape/rebel-large model is specifically designed for this task
tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")

# 2. Define the conversion function
def extract_rebel_triplets(text):
    # Prepare the input text by adding the task prefix
    input_text = f"<{model.config.task_prefix}> " + text
    
    # Encode the text and generate the output
    input_ids = tokenizer(input_text, return_tensors="pt").input_ids
    
    # Generate the linearized triplets
    generated_ids = model.generate(input_ids, max_length=256)
    
    # Decode the output IDs back to a string
    decoded_output = tokenizer.decode(generated_ids.squeeze(), skip_special_tokens=False)
    
    # The output is a linearized string of triplets (Subject, Relation, Object)
    return decoded_output

# --- Example Usage ---
# Input: A simple sentence about a fact
text = "The Statue of Liberty is a colossal neoclassical sculpture on Liberty Island in New York Harbor in New York City."

# Convert the text
triplet_output = extract_rebel_triplets(text)

# Print the results
print(f"--- Input Text ---\n{text}\n")
print(f"--- REBEL Triplet Output ---\n{triplet_output}")