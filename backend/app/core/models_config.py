"""Centralized configuration for AI model names."""

# --- OpenAI Model Names ---

# Model for the VisioScan agent (specialized in image analysis)
# Options could include: "gpt-4o", "gpt-4-turbo", "gpt-4.1-mini", etc.
VISIOSCAN_DEFAULT_MODEL = "gpt-4.1-mini"

# Model for the main Brain agent (general tasks, orchestration)
# Options could include: "gpt-4o", "gpt-4-turbo", "gpt-4.1-mini", "gpt-4.1", etc.
BRAIN_DEFAULT_MODEL = "gpt-4.1" # Updated to gpt-4.1 as requested

# Add other model configurations as needed
# EXAMPLE_AGENT_MODEL = "some-other-model" 