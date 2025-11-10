from transformers import AutoModelForCausalLM, AutoTokenizer

class LLModel:
    def __init__(self, model_name: str):
        # load the tokenizer and the model
        print("Loading model:", model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        print("Model loaded successfully.")

    def generate(self, prompt: str, max_new_tokens: int = 16384) -> str:
        # prepare the model input
        messages = [
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # conduct text completion
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens
        )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

        content = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        return content
    
# Example usage:
# model_name = "Qwen/Qwen3-4B-Instruct-2507"
# llm_model = LLMModel(model_name)
# prompt = "Give me a short introduction to large language model."
# content = llm_model.generate_text(prompt)
# print("content:", content)
