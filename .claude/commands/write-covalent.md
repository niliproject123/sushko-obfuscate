Only when I request a Covalent Diagram, follow these instructions:

## Covalent Diagrams

### General Description
Covalent diagrams visually represent code relationships, where each node corresponds to a line of code, and links denote logical relationships between them. The diagram can show various relationships: execution flow, variable usage, inheritance structure, dependencies, or any other code relationships requested.

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

### Node Types and Field Usage

**CODE nodes** (main relationship flow):
- \`id\`: single running number sequence, starting from 1
- \`label\`: **what the existing code currently does** (e.g., "Filter state interface", "Data preparation function")
- \`filePath\`: **RELATIVE PATH ONLY** to existing file (never full/absolute paths)
- \`lineContent\`: **EXACT EXISTING LINE** of code content from the file
- \`lineNumber\`: line number in file
- \`connectedTo\`: id of previous CODE node in relationship flow (0 for first node)
- \`linkLabel\`: optional connection description

**TODO nodes** (optional planning annotations):
- \`id\`: continues the same running number sequence as CODE nodes
- \`type\`: "todo"
- \`label\`: **what needs to be done, or description of something**. IF its a todo, start with "TODO:" (e.g., "TODO: Add new field", "TODO: Modify parameters"). if not just put the label (e.g "Github Action runner")
- \`content\`: planning details, suggested code, or work description **formatted with \n for line breaks to prevent overflow**
- \`connectedTo\`: id of CODE node where this work is needed
- \`linkLabel\`: optional connection description
- **OMIT**: filePath, lineContent, lineNumber (TODO nodes don't reference existing code)

### Output Format
file format should be <short-description>.cochart.json
user might asks to write in a different file
do not print on screen, only in file

\`\`\`json
[{
    "id": number,              // single running sequence for all nodes, starting with 1
    "label": string,           // CODE: what code does; TODO: what needs doing
    "filePath": string,        // CODE nodes only - RELATIVE PATH
    "lineContent": string,     // CODE nodes only - EXISTING LINE
    "lineNumber": number,      // CODE nodes only
    "connectedTo": number,     // 0 for first CODE node, otherwise previous node id
    "linkLabel": string,       // optional
    "type": "todo",           // TODO nodes only
    "content": string         // TODO nodes only - use \n for line breaks
}]
\`\`\``

### Verification (CRITICAL)
After creating/updating diagram, verify ALL CODE nodes point to correct locations:

1. **For EACH CODE node, run these commands:**
   \`\`\`bash
   # Check file exists
   test -f <filePath> && echo "EXISTS" || echo "MISSING"

   # Extract exact line
   sed -n '<lineNumber>p' <filePath>
   \`\`\`

2. **Compare results:**
   - Does extracted line match \`lineContent\` in diagram (ignoring whitespace)?
   - **CRITICAL**: Does the \`filePath\` in the diagram JSON match the file you tested?

3. **Common error to avoid:**
   - ❌ Running bash command on correct file but diagram has wrong filePath
   - ✅ Always verify the filePath in JSON matches what you're testing

   **Example of error:**
   \`\`\`json
   {"filePath": "src/services/priceCalculations.ts", "lineNumber": 20}
   \`\`\`
   But you run: \`sed -n '20p' src/services/weeklyProcessing.ts\`
   Result: Line matches but diagram has WRONG filePath!

4. **Fix any mismatches immediately** before presenting diagram to user.

## user descrption
the user will tell you what to do, and what he wants to see.
the may ask for creating a diagram, updadting a diagram, or adding to a diagram.
### rules
try to follow his request, while adhearing to the guidelined above
when adding nodes to existing diagram, read the diagram, then add the nodes to the end of array. note to use connectTo to link nodes to aporopritate node ids

user wrote: $ARGUMENT

