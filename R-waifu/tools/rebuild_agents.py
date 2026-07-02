import os

COMPONENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "components")
AGENTS_MD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "AGENTS.md")


def rebuild():
    if not os.path.isdir(COMPONENTS_DIR):
        print("No components/ directory found")
        return

    parts = []
    for fname in sorted(os.listdir(COMPONENTS_DIR)):
        if fname.endswith(".md"):
            fpath = os.path.join(COMPONENTS_DIR, fname)
            with open(fpath) as f:
                parts.append(f.read())

    header = "# R-waifu — Agent Instructions\n\n"
    header += "> Auto-generated file. Do not edit directly.\n"
    header += "> Edit source components in `R-waifu/components/` and run:\n"
    header += "> ```bash\n"
    header += "> py -3 R-waifu/tools/rebuild_agents.py\n"
    header += "> ```\n\n"

    content = header + "\n---\n".join(parts)
    with open(AGENTS_MD, "w") as f:
        f.write(content)
    print(f"Written {AGENTS_MD}")


if __name__ == "__main__":
    rebuild()
