from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class LocalLLM:
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        # Initialize model and tokenizer
        print("Loading model and tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,  # Use float16 for better memory efficiency
            device_map="auto"  # Automatically choose best device (CPU/GPU)
        )
        print("Model loaded successfully!")

    def generate_response(self, prompt, max_length=512):
        # Tokenize input prompt
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate response
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=max_length,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        # Decode and return response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

def main():
    # Initialize the LLM
    llm = LocalLLM()
    
    # Interactive loop
    print("\nEnter your prompts (type 'quit' to exit):")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            break
            
        response = llm.generate_response(user_input)
        print(f"\nLLM: {response}")

if __name__ == "__main__":
    main() 