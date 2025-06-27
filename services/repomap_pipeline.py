import os

def create_repo_map(src_dir: str) -> str:
    """
    Recursively walk through the src_dir and generate a markdown repo map.
    Only includes the directory and file names similar to Aider's repo map.
    """
    md_lines = []
    for root, dirs, files in os.walk(src_dir):
        dirs.sort()
        files.sort()
        rel_path = os.path.relpath(root, src_dir)
        # Format the header for the directory
        if rel_path == ".":
            header = "### Root Directory"
        else:
            header = f"### {rel_path}"
        md_lines.append(header)
        md_lines.append("")
        # List direct subdirectories and files
        for d in dirs:
            md_lines.append(f"- **{d}/**")
        for f in files:
            md_lines.append(f"- {f}")
        md_lines.append("")
    return "\n".join(md_lines)

def main():
    src_dir = os.path.join("data", "app", "src")
    if not os.path.exists(src_dir):
        print(f"Source directory '{src_dir}' does not exist.")
        return

    repo_map_md = create_repo_map(src_dir)
    output_path = "repo_map.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(repo_map_md)
    print(f"Repo map created at {output_path}")

if __name__ == "__main__":
    main()
