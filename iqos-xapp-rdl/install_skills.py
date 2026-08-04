import os
import shutil

source_dir = r"C:\Users\george.barbosa\Downloads\Arquiteto de Redes Autônomas Open RAN\Skills"
dest_root = r"C:\Users\george.barbosa\.gemini\config\skills"

os.makedirs(dest_root, exist_ok=True)

files = [f for f in os.listdir(source_dir) if f.endswith(".md") and f != "README.md"]

for file in files:
    skill_name = file.replace(".md", "").replace("_", "-")
    skill_dir = os.path.join(dest_root, skill_name)
    os.makedirs(skill_dir, exist_ok=True)
    
    source_path = os.path.join(source_dir, file)
    dest_path = os.path.join(skill_dir, "SKILL.md")
    
    with open(source_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract title from the first line if it's a heading
    title = skill_name
    first_line = content.split('\n')[0]
    if first_line.startswith("# Skill:"):
        title = first_line.replace("# Skill:", "").strip()
    elif first_line.startswith("#"):
        title = first_line.replace("#", "").strip()
        
    # Check if frontmatter already exists
    if not content.startswith("---"):
        frontmatter = f"---\nname: {skill_name}\ndescription: {title}\n---\n\n"
        content = frontmatter + content
        
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Instalada skill: {skill_name} em {dest_path}")
