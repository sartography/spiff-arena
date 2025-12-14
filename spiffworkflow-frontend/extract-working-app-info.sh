#!/bin/bash

# This script should be run in the working app's directory
# Usage: cd /path/to/working-app && bash /path/to/this/extract-working-app-info.sh

echo "=== Working App Package Versions ==="
echo ""
cat package.json | grep -E '"(bpmn-js|@bpmn-io|dmn-js|diagram-js)' | sed 's/^[ \t]*//'
echo ""
echo ""

echo "=== ReactDiagramEditor.tsx (How BpmnEditor is used) ==="
echo ""
if [ -f "src/components/ReactDiagramEditor.tsx" ]; then
    cat src/components/ReactDiagramEditor.tsx
else
    echo "File not found: src/components/ReactDiagramEditor.tsx"
    echo "Please provide the correct path to this file"
fi
echo ""
echo ""

echo "=== SpiffBpmnApiService.ts (API Service Implementation) ==="
echo ""
if [ -f "src/services/SpiffBpmnApiService.ts" ]; then
    cat src/services/SpiffBpmnApiService.ts
else
    echo "File not found: src/services/SpiffBpmnApiService.ts"
    echo "Please provide the correct path to this file"
fi
echo ""
echo ""

echo "=== Any other files that import/configure BpmnEditor ==="
echo ""
echo "Searching for files that import BpmnEditor..."
if command -v rg &> /dev/null; then
    rg -l "from.*bpmn-js-spiffworkflow-react|import.*BpmnEditor" --type ts --type tsx 2>/dev/null || true
else
    find . -name "*.ts" -o -name "*.tsx" | xargs grep -l "bpmn-js-spiffworkflow-react\|BpmnEditor" 2>/dev/null || true
fi
echo ""
echo ""

echo "=== BpmnEditor Component Configuration (first 250 lines) ==="
echo ""
# Try to find the actual BpmnEditor component in node_modules or local packages
if [ -d "node_modules/bpmn-js-spiffworkflow-react" ]; then
    echo "Found in node_modules..."
    if [ -f "node_modules/bpmn-js-spiffworkflow-react/src/components/BpmnEditor.tsx" ]; then
        head -250 node_modules/bpmn-js-spiffworkflow-react/src/components/BpmnEditor.tsx
    elif [ -f "node_modules/bpmn-js-spiffworkflow-react/dist/BpmnEditor.js" ]; then
        head -100 node_modules/bpmn-js-spiffworkflow-react/dist/BpmnEditor.js
        echo "... (compiled version, not source)"
    fi
elif [ -d "packages/bpmn-js-spiffworkflow-react" ]; then
    echo "Found in local packages..."
    head -250 packages/bpmn-js-spiffworkflow-react/src/components/BpmnEditor.tsx
else
    echo "BpmnEditor source not found in standard locations"
fi
echo ""
echo ""

echo "=== App initialization / setup files ==="
echo ""
echo "--- index.tsx or main.tsx ---"
if [ -f "src/index.tsx" ]; then
    head -50 src/index.tsx
elif [ -f "src/main.tsx" ]; then
    head -50 src/main.tsx
fi
echo ""
echo ""

echo "=== Any BPMN-related configuration files ==="
echo ""
if [ -f "src/config/bpmn.ts" ]; then
    cat src/config/bpmn.ts
elif [ -f "src/config/bpmn.tsx" ]; then
    cat src/config/bpmn.tsx
fi
echo ""
