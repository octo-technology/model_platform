import argparse

from jinja2 import Template

parser = argparse.ArgumentParser(description="Générer un fichier YAML avec un nom de project.")
parser.add_argument("project_name", type=str, help="Nom du project")
parser.add_argument("template_file", type=str, help="Nom du template à générer")
parser.add_argument("output_file", type=str, help="Nom de l'output")
args = parser.parse_args()

with open(args.template_file, "r") as f:
    template_content = f.read()

template = Template(template_content)

rendered_content = template.render(project_name=args.project_name)

with open(args.output_file, "w") as f:
    f.write(rendered_content)

print(f"Fichier YAML généré avec succès: {args.output_file}")
