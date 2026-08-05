import os
import shutil

base_dir = r"C:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl"
src_dir = os.path.join(base_dir, "src")

# Create new directories
dirs = [
    "infrastructure",
    "e2",
    "domain",
    "agents",
    "coordination",
    "observability",
    "agents/marl"
]
for d in dirs:
    os.makedirs(os.path.join(src_dir, d), exist_ok=True)

# Move existing agents
shutil.move(os.path.join(src_dir, "perception_agent.py"), os.path.join(src_dir, "agents", "perception_agent.py"))
shutil.move(os.path.join(src_dir, "reasoning_agent.py"), os.path.join(src_dir, "agents", "reasoning_agent.py"))
shutil.move(os.path.join(src_dir, "refinement_agent.py"), os.path.join(src_dir, "agents", "refinement_agent.py"))

# Move models into agents/marl (MAPPO)
models_dir = os.path.join(base_dir, "models")
if os.path.exists(models_dir):
    for f in os.listdir(models_dir):
        if f.endswith(".py"):
            shutil.move(os.path.join(models_dir, f), os.path.join(src_dir, "agents", "marl", f))
    try:
        os.rmdir(models_dir)
    except OSError:
        pass

# Move infrastructure/observability
shutil.move(os.path.join(src_dir, "metrics_server.py"), os.path.join(src_dir, "observability", "metrics.py"))
shutil.move(os.path.join(src_dir, "utils.py"), os.path.join(src_dir, "observability", "logging.py"))
shutil.move(os.path.join(src_dir, "memory_module.py"), os.path.join(src_dir, "infrastructure", "sdl_repository.py"))

# Move E2
shutil.move(os.path.join(src_dir, "asn1_decoder.py"), os.path.join(src_dir, "e2", "kpm_decoder.py"))

# We leave conflict_types.py for now to break it down later.
# We leave rdl_xapp.py in src/
# Create main.py stub
with open(os.path.join(src_dir, "main.py"), "w") as f:
    f.write("from src.rdl_xapp import RDLxApp\n\nif __name__ == '__main__':\n    app = RDLxApp()\n    app.start()\n")

print("Reorganização concluída com sucesso.")
