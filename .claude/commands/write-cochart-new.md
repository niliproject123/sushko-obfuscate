Only when I request a Cochart Diagram, follow these instructions:

## Cochart Diagrams

### General Description
Cochart diagrams visually represent code relationships, where each node corresponds to a line of code, and links denote logical relationships between them. The 
diagram can show various relationships: execution flow, variable usage, inheritance structure, dependencies, or any other code relationships requested.

IMPORTANT NOTE: we must run and pass validation stage, do not skip this stage (see Validation section below)

### Two-Step Process
#### Step 1: Build Main Code Flow (CODE nodes only)
Create the main relationship chain using ONLY CODE nodes:
- CODE → CODE → CODE → CODE...
- Each CODE node connects to the previous CODE node in the logical flow
- There could be different logical flows branching from same code node. 
- First CODE node has \`connectedTo: 0\`
    - This step is always required and forms the core of the diagram


#### Step 2: Add Planning Annotations (TODO nodes - OPTIONAL)
**TODO nodes are optional and only needed when planning work is requested.**
Many diagrams will have NO TODO nodes - they simply show existing code relationships.

When TODO nodes are needed:
- Add them after completing the main code flow
- Each TODO node points to ONE specific CODE node where work is needed
- TODO → CODE connections only
- TODO nodes do NOT connect to other TODO nodes
- TODO nodes are NOT part of the main flow

#### Connection Rules (CRITICAL)
- ✅ **CODE → CODE**: Main flow connections
- ✅ **TODO → CODE**: Planning annotations (when TODO nodes are used)
- ❌ **CODE → TODO**: FORBIDDEN
- ❌ **TODO → TODO**: FORBIDDEN

### Output JSON: Node Types and Field Usage (JSON schema)
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://Cochart-diagrams.com/schema/v1.0.0",
  "title": "Cochart Diagram",
  "description": "Schema for Cochart diagrams representing code relationships",
  "type": "array",
  "minItems": 1,
  "items": {
    "oneOf": [
      {
        "$ref": "#/$defs/codeNode"
      },
      {
        "$ref": "#/$defs/todoNode"
      }
    ]
  },
  "$defs": {
    "codeNode": {
      "type": "object",
      "description": "A CODE node representing an existing line of code",
      "required": [
        "id",
        "label",
        "filePath",
        "lineContent",
        "lineNumber",
        "connectedTo"
      ],
      "properties": {
        "id": {
          "type": "integer",
          "minimum": 1,
          "description": "Unique identifier in running sequence starting from 1"
        },
        "label": {
          "type": "string",
          "minLength": 1,
          "description": "What the existing code currently does"
        },
        "filePath": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?![\\/]|[A-Za-z]:)",
          "description": "Relative path to file (no absolute paths allowed)"
        },
        "lineContent": {
          "type": "string",
          "minLength": 1,
          "description": "Exact existing line of code from the file"
        },
        "lineNumber": {
          "type": "integer",
          "minimum": 1,
          "description": "Line number in the file"
        },
        "connectedTo": {
          "type": "integer",
          "minimum": 0,
          "description": "ID of previous CODE node (0 for first node)"
        },
        "linkLabel": {
          "type": "string",
          "description": "Optional connection description"
        }
      },
      "additionalProperties": false,
      "not": {
        "required": ["type"]
      }
    },
    "todoNode": {
      "type": "object",
      "description": "A TODO node representing work that needs to be done",
      "required": [
        "id",
        "type",
        "label",
        "content",
        "connectedTo"
      ],
      "properties": {
        "id": {
          "type": "integer",
          "minimum": 1,
          "description": "Unique identifier continuing the same sequence as CODE nodes"
        },
        "type": {
          "type": "string",
          "const": "todo",
          "description": "Must be 'todo' - no other types allowed"
        },
        "label": {
          "type": "string",
          "minLength": 1,
          "description": "Description of what needs to be done or a label. TODOs should start with 'TODO:'"
        },
        "content": {
          "type": "string",
          "minLength": 1,
          "description": "Planning details, suggested code, or work description (use \\n for line breaks)"
        },
        "connectedTo": {
          "type": "integer",
          "minimum": 1,
          "description": "ID of CODE node where this work is needed"
        },
        "linkLabel": {
          "type": "string",
          "description": "Optional connection description"
        }
      },
      "additionalProperties": false,
      "not": {
        "anyOf": [
          { "required": ["filePath"] },
          { "required": ["lineContent"] },
          { "required": ["lineNumber"] }
        ]
      }
    }
  }
}

### Output
- print JSON into file
- file format should be <short-description>.cochart.json
- user might asks to write in a different file, but keep the .cochart.json suffix
- do not print on screen, only in file
- mention which file was created, including relative path

### Verification (CRITICAL!!!!)
#### Guide line
After creating/updating diagram:
1. **You MUST verify ALL CODE nodes** 
filepath, line number, line content metch the content on the disk.
THIS IS CRUCIAL!!!
2. **Fix any mismatches immediately** before presenting diagram to user.
    -. read the label and line number of that node
    -. find the aproprtaite line number and line content and update the node
3. **You MUST ensure correctnes of nodes properties**
    - all code nodes have `id`, `filepath`, 
    `label`, `lineContent`, `lineNumber`. They DONT have `type`
    - all todo nodes have type "todo"
    - no nodes have other types different than "todo"

#### Execution
**Premade Shell scripts**
I've created 3 scripts you should use (windows, nodejs, linux). located in `.claude/commands/scripts/llm-validate-Cochart*`. Use the one most appropriate for the platform you're running on.
**Fallback Shell scripts**
if these are not avialable, make a shell script for validation

## user descrption
the user will tell you what to do, and what he wants to see: user wrote: $ARGUMENT
try to follow his request, shile adhearing to the guidelined above

