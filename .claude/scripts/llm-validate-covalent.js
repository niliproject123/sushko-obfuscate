#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

function validateCochart(jsonFile) {
    if (!fs.existsSync(jsonFile)) {
        console.error(`Error: File not found: ${jsonFile}`);
        process.exit(1);
    }

    try {
        const data = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));

        if (!Array.isArray(data)) {
            console.error('Error: JSON root must be an array');
            process.exit(1);
        }

        let errors = 0;
        let checked = 0;

        console.log('======================================');
        console.log('COCHART VALIDATION REPORT');
        console.log('======================================');
        console.log(`File: ${jsonFile}`);
        console.log('');

        // First pass: Schema validation
        console.log('--- SCHEMA VALIDATION ---');
        for (const node of data) {
            const { id, type } = node;
            checked++;

            // Check required label field
            if (!node.hasOwnProperty('label')) {
                errors++;
                console.log(`[ERROR] Node ${id}: Missing required label`);
            }

            if (type === 'todo') {
                // TODO node validation
                if (node.hasOwnProperty('lineNumber')) {
                    errors++;
                    console.log(`[ERROR] Node ${id}: TODO node should not have lineNumber`);
                }
                if (node.hasOwnProperty('filePath')) {
                    errors++;
                    console.log(`[ERROR] Node ${id}: TODO node should not have filePath`);
                }
            } else if (type && type !== 'todo') {
                // Invalid type
                errors++;
                console.log(`[ERROR] Node ${id}: Invalid type '${type}' (only 'todo' allowed)`);
            } else {
                // CODE node validation
                if (!node.hasOwnProperty('lineNumber')) {
                    errors++;
                    console.log(`[ERROR] Node ${id}: CODE node missing lineNumber`);
                }
                if (!node.hasOwnProperty('filePath')) {
                    errors++;
                    console.log(`[ERROR] Node ${id}: CODE node missing filePath`);
                }
            }
        }

        // Second pass: Content validation
        console.log('');
        console.log('--- CONTENT VALIDATION ---');
        const codeNodes = data.filter(node => node.type !== 'todo');

        for (const node of codeNodes) {
            const { id, label, filePath, lineNumber, lineContent } = node;
            const baseDir = path.dirname(jsonFile);
            const fullPath = path.resolve(baseDir, '../../', filePath);

            checked++;
            let nodeStatus = '[OK]';

            if (!fs.existsSync(fullPath)) {
                nodeStatus = '[ERROR]';
                errors++;
                console.log(`[ERROR] Node ${id}: File not found at ${fullPath}`);
            } else {
                const fileContent = fs.readFileSync(fullPath, 'utf8');
                const lines = fileContent.split('\n');
                const lineNum = parseInt(lineNumber);

                if (lineNum < 1 || lineNum > lines.length) {
                    nodeStatus = '[ERROR]';
                    errors++;
                    console.log(`[ERROR] Node ${id}: Line ${lineNum} out of range (file has ${lines.length} lines)`);
                } else {
                    const actualLine = lines[lineNum - 1].trim();
                    const expectedLine = lineContent.trim();

                    if (actualLine !== expectedLine) {
                        nodeStatus = '[ERROR]';
                        errors++;
                        console.log(`[ERROR] Node ${id}: Line content mismatch`);
                        console.log(`  Expected: "${expectedLine}"`);
                        console.log(`  Actual:   "${actualLine}"`);
                    }
                }
            }
        }

        console.log('');
        console.log('======================================');
        console.log(`Total Nodes: ${data.length}`);
        console.log(`Errors: ${errors}`);
        console.log('======================================');

        return errors === 0;
    } catch (err) {
        console.error(`Error reading/parsing JSON: ${err.message}`);
        process.exit(1);
    }
}

const jsonFile = process.argv[2];
if (!jsonFile) {
    console.error('Usage: node validate-covalent.js <cochart-file.json>');
    process.exit(1);
}

validateCochart(jsonFile);
