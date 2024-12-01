from elevenlabs.client import ElevenLabs
from elevenlabs import play, stream
import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM  # Updated import based on the warning

# Load environment variables
load_dotenv()

# Initialize ElevenLabs client
client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Initialize Ollama model
cached_llm = OllamaLLM(model="llama3.2:1b", base_url="http://localhost:11434")

def process_query(query):
    """
    Processes a query by generating a spoken response for the query and the LLM output.

    Args:
        query (str): The input query from the user.

    Returns:
        str: The response from the LLM.
    """
    print(f"You asked: {query}")

    # Generate audio for the query
    print("Generating audio for the query...")
    audio_stream = client.generate(text="You asked: " + query, stream=True)
    stream(audio_stream)

    # Query the LLM
    print("Querying the LLM...")
    response = cached_llm.invoke(query)

    # Display the LLM's response
    print(f"LLM response: {response}")

    # Generate audio for the LLM response
    print("Generating audio for the LLM response...")
    audio_stream = client.generate(text=response, stream=True)
    stream(audio_stream)

    return response

def main():
    print("Welcome to SpeakLLM! Type your query below or type 'exit' to quit.")
    while True:
        # Get user input
        query = input("\nYour query: ")
        if query.lower() == 'exit':
            print("Goodbye!")
            break

        try:
            # Process the query
            process_query(query)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
