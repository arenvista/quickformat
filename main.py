from format.formater import Formater
from format.model_settings import ModelSettings
from pathlib import Path
import argparse
import os

def init():
    parser = argparse.ArgumentParser(
        description="A simple script that formats files."
    )

    parser.add_argument(
        "-t", "--template", 
        type=str,
        help="Expects path to template file that stores context for format edits"
    )

    parser.add_argument(
        "-f", "--file", 
        type=str,
        help="Single File Processing"
    )

    parser.add_argument(
        "-v", "--verbosity", 
        type=int,
        default=2,
        help="Model Verbosity (1-3)"
    )

    parser.add_argument(
        "-e", "--effort", 
        type=int,
        default=2,
        help="Model Effort (1-3)"
    )

    return parser.parse_args()

        
def main():
    args = init()
    
    # These will now work correctly because args.verbosity/effort are integers
    model_verbosity = ModelSettings(args.verbosity)
    model_effort = ModelSettings(args.effort)
    
    # Check for template in args first, then environment variables
    template_path_str = args.template or os.environ.get('MDTEMPLATE')
    template_path = Path(template_path_str) if template_path_str else None

    # Instantiate the analyzer once
    analyzer = Formater(
        model="gpt-5.4",
        template=template_path, 
        model_verbosity=model_verbosity, 
        model_effort=model_effort
    )
    
    analyzer.run(single_file=args.file)

if __name__ == "__main__":
    main()
