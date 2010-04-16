import os 
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from .finder import Finder


class Formater:
    """
    A class used to analyze and summarize Python codebases using an LLM.
    """

    def __init__(
        self,
        model: str = "gpt-5",
        max_file_chars: int = 30000,
        exclude_dirs: set|None = None
    ):
        # Ensure you have OPENAI_API_KEY set in your environment variables
        self.client = OpenAI()
        self.model = model
        self.max_file_chars = max_file_chars
        
        # Default directories to ignore (e.g., virtual environments, caches, git)
        self.exclude_dirs = exclude_dirs or {".venv", "venv", "env", "__pycache__", ".git", ".tox"}

        self.summary_prompt = (
            "Read the provided markdown contents and run: clean, split into sections by header, title unnamed theorems, topics, sections etc.\n\n" 
            "Formatting Rules:\n\n"
            "- Use $$ $$ for display math.\n\n"
            "- Use $ $ if better formatted inline.\n\n"
            "- Use Markdown blockquote callouts (e.g., > [!thm] Title) when appropriate.\n\n"
            "- Focus on generating named headers and subheaders\n\n"
        )

    def get_target_files(self, filetype: str, root: Path) -> list:
        """Recursively finds .py files while explicitly ignoring specified directories."""
        valid_files = []
        for p in root.rglob(f"*.{filetype}"):
            # Exclude matching directories and files with 'api' in their path
            if p.is_file() and not any(part in self.exclude_dirs for part in p.parts) and "api" not in str(p):
                valid_files.append(p)
        return valid_files

    def read_file(self, path: Path) -> str:
        print(f"Reading {path}")
        """Reads a file and truncates it to prevent massive context costs."""
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            return text[:self.max_file_chars]
        except Exception as e:
            return f"ERROR READING FILE: {e}"

    def call_llm(self, prompt: str, content: str) -> str:
        """Helper to manage the API call to OpenAI."""
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content},
                ],
                reasoning={"effort": "low"},
                text={"verbosity": "low"},
            )
            return response.output_text
        except Exception as e:
            print(f"\n[!] API Error: {e}")
            return f"API ERROR: {e}"

    def suggest_edits(self, files: list, context_files: list) -> dict:
        """Suggests edits for specific files based on provided context files."""
        suggestions = {}

        for i, file in enumerate(files):
            print(f"[{i+1}/{len(files)}] Suggesting Edits {file}...")
            
            content = self.read_file(file)
            for context_file in context_files:
                content += self.read_file(context_file)

            suggestion = self.call_llm(
                self.summary_prompt,
                f"File: {file}\n\n{content}"
            )
            suggestions[str(file)] = suggestion

        return suggestions

    def summarize_files(self, files: list, outdir, indir):
        print("Formatting Files =>")
        for file in tqdm(files):
            # 'file' is the relative path from 'indir' (e.g., 'test.md' or 'subdir/test.md')
            in_path = Path(indir) / file
            out_path = Path(outdir) / file
            
            content = self.read_file(in_path)
            summary = self.call_llm(
                self.summary_prompt,
                f"File: {in_path}\n\n{content}"
            )
            
            # Ensure the output directory structure exists before writing
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"{summary}")
    def run(self):
        """Main orchestrator for the analysis process."""
        print("Initializing Summary State")
        finder = Finder()
        print("Enter input files dir:")
        root = finder.fuzzy_find_dir()
        print("Enter output files dir:")
        outdir = finder.fuzzy_find_dir()
        if root is None: raise ValueError("Dir invalid")
        filetype = input("Enter filextension (ex: .md): ")
        files = [f for f in finder.get_all_files(root) if f.endswith(filetype)]

        if not files:
            print("No target files found.")
            return

        print(f"Found {len(files)} files to summarize.\n\t" + "\n\t".join(files))

        self.summarize_files(files, outdir, root)
        print("Done!")
if __name__ == "__main__":
    # Instantiate and run
    analyzer = Formater(model="gpt-5")
    analyzer.run()

