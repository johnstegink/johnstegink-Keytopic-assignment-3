import ollama
import json
import os


def create_newtitle(title, summary, base_on_title):
    """
    Creates a new desensationalized title using AI.
    Currently just a placeholder implementation.
    """

    summary_empty = summary.strip() == "Geen samenvatting beschikbaar."
    # Determine prompt filename
    prompt_filename = "title.json" if base_on_title or summary_empty else "summary.json"

    # Open een json bestand en lees de properties
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, '..', '..', 'prompts', prompt_filename)

    with open(prompt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        sys_instruction = data.get("sys_instruction", "")
        if isinstance(sys_instruction, list):
            sys_instruction = "\n".join(sys_instruction)

        prompt_template = data.get("prompt", "")
        if isinstance(prompt_template, list):
            prompt_template = "\n".join(prompt_template)


    # Format the user prompt
    user_prompt = prompt_template.replace("{title}", title).replace("{summary}", summary)

    answer = ask_ollama(
        model_name="mistral",
        system_instruction=sys_instruction,
        user_prompt=user_prompt
    )

    return answer



def ask_ollama( model_name, system_instruction, user_prompt):
    """
    Ask question to Ollama
    """
    response = ollama.chat(model=model_name, messages=[
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': user_prompt}
    ])
    output = response['message']['content'].strip()
    clean_output = output.split('\n')[0].replace('Output:', '').replace('"', '').strip()
    if clean_output.endswith('.'):
        clean_output = clean_output[:-1]
    return clean_output
