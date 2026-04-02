/* @vitest-environment node */

import { execFileSync } from 'node:child_process';
import { readdirSync, readFileSync, rmSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import ExtensionUiSchemaService from './ExtensionUiSchemaService';

const repoRoots = [
  '/home/spiffuser/sample-process-models/extensions',
  '/home/spiffuser/enterprise-process-models/extensions',
  '/home/spiffuser/sartography-process-models/extensions',
];

const migratorScriptPath = '/home/spiffuser/spiff-arena/bin/migrate_extension_uischema.py';

function comparableNormalizedSchema(rawSchema: object) {
  const normalized = ExtensionUiSchemaService.normalize(rawSchema as any);
  return {
    pages: normalized.pages,
    ux_elements: (normalized.ux_elements || [])
      .map((item) => {
        const comparableItem: Record<string, unknown> = {
          display_location: item.display_location,
        };
        if (
          item.page &&
          item.display_location !== 'css'
        ) {
          comparableItem.page = item.page;
        }
        if (
          item.label &&
          item.display_location !== 'routes' &&
          item.display_location !== 'css'
        ) {
          comparableItem.label = item.label;
        }
        if (item.tooltip) {
          comparableItem.tooltip = item.tooltip;
        }
        if (item.icon) {
          comparableItem.icon = item.icon;
        }
        if (item.use_full_page_path) {
          comparableItem.use_full_page_path = item.use_full_page_path;
        }
        if (item.location_specific_configs?.highlight_on_tabs) {
          comparableItem.location_specific_configs = {
            highlight_on_tabs: item.location_specific_configs.highlight_on_tabs,
          };
        }
        if (
          item.display_location === 'css' &&
          item.location_specific_configs?.css_file
        ) {
          comparableItem.location_specific_configs = {
            css_file: item.location_specific_configs.css_file,
          };
        }
        return comparableItem;
      })
      .sort((left, right) =>
        JSON.stringify(left).localeCompare(JSON.stringify(right)),
      ),
  };
}

function migrateSchemaWithScript(schema: object) {
  const tempDir = mkdtempSync(join(tmpdir(), 'extension-ui-schema-'));
  const inputPath = join(tempDir, 'extension_uischema.json');
  try {
    writeFileSync(inputPath, `${JSON.stringify(schema, null, 2)}\n`);
    const stdout = execFileSync(
      'python3',
      [migratorScriptPath, '--stdout', inputPath],
      { encoding: 'utf8' },
    );
    return JSON.parse(stdout);
  } finally {
    rmSync(tempDir, { recursive: true, force: true });
  }
}

function allExtensionUiSchemaFiles() {
  return repoRoots.flatMap((root) =>
    readdirSync(root, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => resolve(root, entry.name, 'extension_uischema.json'))
      .filter((path) => {
        try {
          readFileSync(path, 'utf8');
          return true;
        } catch {
          return false;
        }
      }),
  );
}

describe('ExtensionUiSchemaService', () => {
  it('migrates a legacy nav extension to 1.0 and preserves normalized behavior', () => {
    const legacySchema = {
      version: '0.1',
      ux_elements: [
        {
          label: 'Support',
          page: '/support',
          display_location: 'user_profile_item',
        },
      ],
      pages: {
        '/support': {
          components: [
            {
              name: 'MarkdownRenderer',
              arguments: { source: 'SPIFF_PROCESS_MODEL_FILE:::support.md' },
            },
          ],
        },
      },
    };

    const migrated = migrateSchemaWithScript(legacySchema);
    expect(migrated).toEqual({
      version: '1.0',
      navigation: [
        {
          label: 'Support',
          location: 'user_menu',
          target: {
            type: 'extension_page',
            path: '/support',
          },
        },
      ],
      pages: legacySchema.pages,
    });
    expect(comparableNormalizedSchema(migrated)).toEqual(
      comparableNormalizedSchema(legacySchema),
    );
  });

  it('migrates legacy routes and css to 1.0 and preserves normalized behavior', () => {
    const legacySchema = {
      version: '0.2',
      ux_elements: [
        {
          label: 'Theme Demo',
          page: '/theme-demo',
          display_location: 'primary_nav_item',
          tooltip: 'See information about the active theme',
        },
        {
          label: 'Vibrant Theme',
          page: '/theme-demo',
          display_location: 'css',
          location_specific_configs: {
            css_file: 'vibrant_theme.css',
          },
        },
        {
          page: '/reports',
          display_location: 'routes',
        },
      ],
      pages: {
        '/theme-demo': {
          header: 'Theme Demo',
        },
        '/reports': {
          header: 'Reports',
        },
      },
    };

    const migrated = migrateSchemaWithScript(legacySchema);
    expect(migrated).toEqual({
      version: '1.0',
      navigation: [
        {
          label: 'Theme Demo',
          location: 'primary_nav',
          target: {
            type: 'extension_page',
            path: '/theme-demo',
          },
          tooltip: 'See information about the active theme',
        },
      ],
      routes: [{ path: '/reports' }],
      assets: {
        stylesheets: [{ file: 'vibrant_theme.css' }],
      },
      pages: legacySchema.pages,
    });
    expect(comparableNormalizedSchema(migrated)).toEqual(
      comparableNormalizedSchema(legacySchema),
    );
  });

  it('migrates full-path navigation links to 1.0 path targets', () => {
    const legacySchema = {
      version: '0.2',
      ux_elements: [
        {
          label: 'Analytics',
          page: '/analytics',
          display_location: 'primary_nav_item',
          icon: 'analytics',
          use_full_page_path: true,
        },
      ],
    };

    const migrated = migrateSchemaWithScript(legacySchema);
    expect(migrated).toEqual({
      version: '1.0',
      navigation: [
        {
          label: 'Analytics',
          location: 'primary_nav',
          icon: 'analytics',
          target: {
            type: 'path',
            path: '/analytics',
          },
        },
      ],
    });
    expect(comparableNormalizedSchema(migrated)).toEqual(
      comparableNormalizedSchema(legacySchema),
    );
  });

  it('normalizes every known extension ui schema file from the model repos', () => {
    for (const filePath of allExtensionUiSchemaFiles()) {
      const rawSchema = JSON.parse(readFileSync(filePath, 'utf8'));
      const normalized = ExtensionUiSchemaService.normalize(rawSchema);
      expect(normalized.pages).toBeDefined();
      expect(Array.isArray(normalized.ux_elements)).toBe(true);
    }
  });
});
