#!/bin/bash

echo "🔧 Upgrading BPMN packages to newer versions..."
echo ""
echo "Changes:"
echo "  bpmn-js:                    ^17.11.1 → ^18.9.1"
echo "  bpmn-js-properties-panel:   ^5.19.0 → ^5.44.0"
echo "  bpmn-js-spiffworkflow:      #main → #allow-any-bpmn-js"
echo "  diagram-js:                 ^14.11.3 → ^15.4.0"
echo "  dmn-js-properties-panel:    ^3.8.0 → ^3.8.3"
echo ""
echo "⚠️  WARNING: This will modify package.json in the current directory!"
echo "   Make sure you're in the correct app directory."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Update package.json
echo "📝 Updating package.json..."

# Use node to modify package.json programmatically
node << 'EOF'
const fs = require('fs');
const path = require('path');

const packageJsonPath = path.join(process.cwd(), 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

// Update versions
packageJson.dependencies['bpmn-js'] = '^18.9.1';
packageJson.dependencies['bpmn-js-properties-panel'] = '^5.44.0';
packageJson.dependencies['bpmn-js-spiffworkflow'] = 'github:sartography/bpmn-js-spiffworkflow#allow-any-bpmn-js';
packageJson.dependencies['diagram-js'] = '^15.4.0';
packageJson.dependencies['dmn-js-properties-panel'] = '^3.8.3';

// Write back to file
fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2) + '\n');
console.log('✅ package.json updated');
EOF

if [ $? -ne 0 ]; then
    echo "❌ Failed to update package.json"
    exit 1
fi

# Remove node_modules and package-lock.json to ensure clean install
echo "🗑️  Removing node_modules and package-lock.json..."
rm -rf node_modules package-lock.json

echo "📦 Installing packages..."
npm install

echo ""
echo "✅ Done! Packages upgraded to newer versions."
echo ""
echo "🚀 Start the app with: npm start"
echo ""
echo "⚠️  Note: The newer versions may have frozen business objects."
echo "   If you get 'Cannot add property __, object is not extensible' errors,"
echo "   you may need to apply workarounds in the BpmnEditor component."
