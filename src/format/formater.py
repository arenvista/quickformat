import os 
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm

from format.finder import Finder
from format.model_settings import ModelSettings

class Formater:
    """
    A class used to analyze and summarize Python codebases using an LLM.
    """

    def __init__(
        self,
        model: str = "gpt-4o", # Adjusted placeholder
        max_file_chars: int = 30000,
        exclude_dirs: set|None = None,
        template: Path|None = None,
        model_effort: ModelSettings|None = ModelSettings.MEDIUM,
        model_verbosity: ModelSettings|None = ModelSettings.MEDIUM
    ):
        # Ensure you have OPENAI_API_KEY set in your environment variables
        self.client = OpenAI()
        self.model = model
        self.max_file_chars = max_file_chars
        
        # Default directories to ignore (e.g., virtual environments, caches, git)
        self.exclude_dirs = exclude_dirs or {".venv", "venv", "env", "__pycache__", ".git", ".tox"}

        if template is None:
            self.summary_prompt = (
                "Read the provided markdown contents and run: clean, split into sections by header, title unnamed theorems, topics, sections etc.\n\n" 
                "Formatting Rules:\n\n"
                "- Use $$ $$ for display math.\n\n"
                "- Use $ $ if better formatted inline.\n\n"
                "- Use Markdown blockquote callouts (e.g., > [!thm] Title) when appropriate.\n\n"
                "- Focus on generating named headers and subheaders\n\n"
            )
        else:
            with open(template, 'r') as infile:
                self.summary_prompt = infile.read()
                
        self.model_effort = model_effort or ModelSettings.MEDIUM
        self.model_verbosity = model_verbosity or ModelSettings.MEDIUM

    def get_target_files(self, filetype: str, root: Path) -> list:
        """Recursively finds files while explicitly ignoring specified directories."""
        valid_files = []
        for p in root.rglob(f"*.{filetype}"):
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
                reasoning={"effort": self.model_effort.display_name},
                text={"verbosity": self.model_verbosity.display_name},
            )
            return response.output_text
        except Exception as e:
            print(f"\n[!] API Error: {e}")
            return f"API ERROR: {e}"


    def summarize_files(self, files: list, outdir, indir):
        print("Formatting Files =>")
        for file in tqdm(files):
            in_path = Path(indir) / file if indir else Path(file)
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

    def run(self, single_file: str|None = None):
        """Main orchestrator for the analysis process."""
        finder = Finder()
        print("Enter output files dir:")
        outdir = finder.fuzzy_find_dir()

        files = []
        root = ""
        if single_file is None:
            print("Enter input files dir:")
            root = finder.fuzzy_find_dir()
            if root is None: raise ValueError("Dir invalid")
            
            filetype = input("Enter file extension (ex: md): ").replace(".", "")
            files = [f for f in finder.get_all_files(root) if f.endswith(f"{filetype}")]
        else:
            print("Running in Single File Mode")
            files = [single_file]
            root = None

        if not files:
            print("No target files found.")
            return

        print(f"Found {len(files)} files to summarize.\n\t" + "\n\t".join(files))
        print(f"Summary Prompt => {self.summary_prompt}")

        self.summarize_files(files, outdir, root)
        print("Done!")

if __name__ == "__main__":
    analyzer = Formater()
    analyzer.run()
