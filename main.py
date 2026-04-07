from format import *
import argparse
import os
def init():
    # 1. Create the parser
    parser = argparse.ArgumentParser(
        description="A simple script that formats files."
    )

    # Optional argument (Flag)
    parser.add_argument(
        "-t", "--template", 
        type=str,
        help="Expects path to template file that stores context for format edits"
    )
    
    # 3. Parse the arguments
    args = parser.parse_args()
    return args

        
def main():
    args = init()
    if args.template:
        analyzer = Formater(model="gpt-5", template=Path(args.template))
        analyzer.run()
        return

    template_path = os.environ.get('MDTEMPLATE')
    if template_path and template_path != "":
        analyzer = Formater(model="gpt-5", template=Path(template_path))
        analyzer.run()
        return

if __name__ == "__main__":
    main()
