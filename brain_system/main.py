
import os
import sys
from dotenv import load_dotenv
from .core.orchestrator import BrainOrchestrator

# Load environment variables
load_dotenv()

def select_provider() -> tuple[str, str | None]:
    """
    Interactive menu for the user to choose their LLM provider.
    Returns (provider_name, model_name).
    """
    print("\n" + "=" * 50)
    print("       🧠 BRAIN SYSTEM — Model Selection")
    print("=" * 50)
    print("  1. Gemini (Google API — requires GOOGLE_API_KEY)")
    print("  2. OpenAI (OpenAI API — requires OPENAI_API_KEY)")
    print("  3. Ollama (Local models — no API key needed)")
    print("=" * 50)
    
    while True:
        choice = input("Select provider [1/2/3]: ").strip()
        if choice == "1":
            if not os.getenv("GOOGLE_API_KEY"):
                print("⚠️  GOOGLE_API_KEY not found in .env file.")
                cont = input("Continue anyway? (y/n): ").strip().lower()
                if cont != "y":
                    continue
            return "gemini", None
        elif choice == "2":
            if not os.getenv("OPENAI_API_KEY"):
                print("⚠️  OPENAI_API_KEY not found in .env file.")
                cont = input("Continue anyway? (y/n): ").strip().lower()
                if cont != "y":
                    continue
            return "openai", None
        elif choice == "3":
            model = input("Enter Ollama model name (default: mistral): ").strip()
            return "ollama", model if model else None
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def main():
    print("Initializing Brain System...")
    
    provider, model_name = select_provider()
    print(f"\n✅ Using provider: {provider}" + (f" (model: {model_name})" if model_name else ""))

    try:
        brain = BrainOrchestrator(provider=provider, model_name=model_name)

        # --- Persona Mode ---
        print("\n" + "=" * 50)
        print("       🎭 Persona Mode (Optional)")
        print("=" * 50)
        print("  Upload a biography/autobiography to make the")
        print("  Brain respond as that person.")
        print("  Supported formats: .txt, .pdf")
        print("  Press Enter to skip (normal mode).")
        print("=" * 50)
        
        persona_path = input("Document path: ").strip()
        if persona_path:
            try:
                brain.set_persona(persona_path)
                print(f"\n🎭 Persona Mode: Responding as {brain.persona.name}")
            except FileNotFoundError:
                print(f"⚠️  File not found: {persona_path}. Starting in normal mode.")
            except Exception as e:
                print(f"⚠️  Failed to load persona: {e}. Starting in normal mode.")

        mode_label = f"🎭 {brain.persona.name}" if brain.persona and brain.persona.active else "🧠 Brain"
        print(f"\n{mode_label} System Online. (Type 'exit' to quit)")
        print("-" * 50)
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Shutting down Brain System...")
                break
            
            print(f"\n{mode_label} is thinking...")
            response = brain.run(user_input)
            print(f"\n{mode_label}: {response}")
            print("-" * 50)
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

