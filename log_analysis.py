import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "tinyllama" 

def get_logs(container_name="my-test-container", line_limit=100):
    from subprocess import check_output, CalledProcessError
    try:
        logs = check_output(["docker", "logs", "--tail", str(line_limit), container_name], text=True)
        return logs
    except CalledProcessError as e:
        print("Error collecting logs:", e)
        return ""

def analyze_logs(logs):
    try:
        prompt = f"Please analyze the following logs and suggest the root cause for high CPU usage:\n\n{logs}"
        
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120  # increased timeout to 2 minutes
        )

        response.raise_for_status()
        output = response.json()
        return output.get("response", "No response from model.")
    
    except requests.exceptions.Timeout:
        print("Ollama request timed out.")
        return "Ollama timed out. No response received."
    except requests.exceptions.RequestException as e:
        print("Error contacting Ollama:", e)
        return "Failed to get response from Ollama."

if __name__ == "__main__":
    logs = get_logs()
    summary = analyze_logs(logs)
    print("--- LLM Response ---")
    print(summary)
