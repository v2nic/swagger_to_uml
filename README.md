# Swagger to UML

A small pure Python script that converts API specifications ([OpenAPI](https://www.openapis.org)/[Swagger](https://swagger.io)) into UML diagrams. Supports both [PlantUML](http://plantuml.com) and [Mermaid](https://mermaid.js.org/) output formats. The goal is not to replace existing documentation generators, but to complement them with a visual representation of the routes, models, and their relationships.

## Example

![excerpt of the petstore example](petstore_example/swagger.png)

To create a PlantUML diagram from the [petstore example](http://petstore.swagger.io), call the script with:

```
python bin/swagger_to_uml petstore_example/swagger.json > petstore_example/swagger.puml
```

It will create the file `petstore_example/swagger.puml` which can then be translated into a PNG image with PlantUML with:

```
plantuml petstore_example/swagger.puml -tpng
```

Note you need to install [PlantUML](http://plantuml.com) and [Graphviz](http://www.graphviz.org) for this.

### Mermaid Output

To generate a Mermaid diagram instead, use the `-f mermaid` option:

```
python bin/swagger_to_uml petstore_example/swagger.json -f mermaid > petstore_example/swagger.mmd
```

Mermaid diagrams can be rendered directly in many Markdown viewers (GitHub, GitLab, VS Code, etc.) or using the [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli).

## Input formats

- Supports Swagger 2.0 and OpenAPI 3.x.
- Input can be JSON or YAML; format is auto-detected. For YAML files, `PyYAML` is required.

## Output formats

- **PlantUML** (default): Traditional UML diagram format requiring PlantUML tooling.
- **Mermaid**: Modern diagram format with native support in many platforms.

## Installation

The script runs with Python 3. For YAML input, `PyYAML` is required. Transforming PUML into vector graphics or other requires external tools however.

On macOS, the installation of the required tools with [Homebrew](https://brew.sh) is simple:

```
brew install plantuml graphviz
```

## Usage

```
python bin/swagger_to_uml [-h] [-f {plantuml,mermaid}] input_file

positional arguments:
  input_file            Path to Swagger/OpenAPI specification file (JSON or YAML)

options:
  -h, --help            show this help message and exit
  -f, --format {plantuml,mermaid}
                        Output format: plantuml (default) or mermaid
```

## Programmatic Usage

The tool can also be used as a Python library:

```python
from swagger_to_uml import parse_file, PlantUMLRenderer, MermaidRenderer

diagram = parse_file("api_spec.json")

plantuml_output = PlantUMLRenderer().render(diagram)

mermaid_output = MermaidRenderer().render(diagram)
```

## Converting to SVG

### PlantUML to SVG

To convert PlantUML diagrams to SVG:

```bash
# Using PlantUML CLI
plantuml diagram.puml -tsvg

# Or using the Java jar directly
java -jar plantuml.jar diagram.puml -tsvg
```

### Mermaid to SVG

To convert Mermaid diagrams to SVG:

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Convert to SVG
mmdc -i diagram.mmd -o diagram.svg

# Convert to other formats
mmdc -i diagram.mmd -o diagram.png
mmdc -i diagram.mmd -o diagram.pdf
```

### Online Alternatives

- **PlantUML**: [PlantUML Online Server](http://www.plantuml.com/plantuml/)
- **Mermaid**: [Mermaid Live Editor](https://mermaid.live/)

## Testing

The script is tested with `pytest`. Install dependencies and run tests:

```bash
pip install -r requirements.txt
python -m pytest -q
```

## Contribute

The script is just a first proof-of-concept version. Issues and pull requests welcome!

## Copyright

MIT License

Copyright (c) 2017 Niels Lohmann <http://nlohmann.me>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
