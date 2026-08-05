import os

replacements = {
    "from src.observability.logging": "from src.observability.logging",
    "import src.observability.logging": "import src.observability.logging",
    "from src.infrastructure.sdl_repository": "from src.infrastructure.sdl_repository",
    "import src.infrastructure.sdl_repository": "import src.infrastructure.sdl_repository",
    "from src.agents.perception_agent": "from src.agents.perception_agent",
    "from src.agents.reasoning_agent": "from src.agents.reasoning_agent",
    "from src.agents.refinement_agent": "from src.agents.refinement_agent",
    "from src.e2.kpm_decoder": "from src.e2.kpm_decoder",
    "from src.agents.marl.mappo_agent": "from src.agents.marl.mappo_agent",
    "from src.agents.marl.intent_classifier": "from src.agents.marl.intent_classifier",
    "src.observability.logging": "src.observability.logging",
    "SdlRepository": "SdlRepository",
    "KpmDecoder": "KpmDecoder"
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, _, files in os.walk(r"C:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl"):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))

