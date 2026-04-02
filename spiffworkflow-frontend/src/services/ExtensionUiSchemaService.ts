import {
  ExtensionUiSchema,
  UiSchemaDisplayLocation,
  UiSchemaLocationSpecificConfig,
  UiSchemaPage,
  UiSchemaUxElement,
} from '../extension_ui_schema_interfaces';

type NavigationLocationV1 =
  | 'primary_nav'
  | 'user_menu'
  | 'configuration_tab';

type NavigationTargetV1 =
  | {
      type: 'extension_page';
      path: string;
    }
  | {
      type: 'path';
      path: string;
    };

type NavigationItemV1 = {
  label: string;
  location: NavigationLocationV1;
  target: NavigationTargetV1;
  icon?: string;
  tooltip?: string;
  highlight_on_tabs?: string[];
};

type RouteEntryV1 =
  | string
  | {
      path: string;
    };

type ExtensionUiSchemaV1 = {
  version: '1.0';
  navigation?: NavigationItemV1[];
  routes?: RouteEntryV1[];
  assets?: {
    stylesheets?: Array<{
      file: string;
    }>;
  };
  pages?: UiSchemaPage;
  disabled?: boolean;
};

const navigationLocationMap: Record<NavigationLocationV1, UiSchemaDisplayLocation> =
  {
    primary_nav: UiSchemaDisplayLocation.primary_nav_item,
    user_menu: UiSchemaDisplayLocation.user_profile_item,
    configuration_tab: UiSchemaDisplayLocation.configuration_tab_item,
  } as const;

function normalizeRouteEntries(
  routes: RouteEntryV1[] | undefined,
): UiSchemaUxElement[] {
  if (!routes) {
    return [];
  }
  return routes.map((routeEntry) => {
    const page = typeof routeEntry === 'string' ? routeEntry : routeEntry.path;
    return {
      page,
      display_location: UiSchemaDisplayLocation.routes,
      label: page,
    };
  });
}

function normalizeStylesheets(
  stylesheets: Array<{ file: string }> | undefined,
): UiSchemaUxElement[] {
  if (!stylesheets) {
    return [];
  }
  return stylesheets.map((stylesheet) => ({
    label: stylesheet.file,
    page: '',
    display_location: UiSchemaDisplayLocation.css,
    location_specific_configs: {
      css_file: stylesheet.file,
    } satisfies UiSchemaLocationSpecificConfig,
  }));
}

function normalizeNavigation(
  navigation: NavigationItemV1[] | undefined,
): UiSchemaUxElement[] {
  if (!navigation) {
    return [];
  }
  return navigation.map((item) => ({
    label: item.label,
    page: item.target.path,
    display_location: navigationLocationMap[item.location],
    tooltip: item.tooltip,
    icon: item.icon,
    use_full_page_path: item.target.type === 'path',
    location_specific_configs: item.highlight_on_tabs
      ? {
          highlight_on_tabs: item.highlight_on_tabs,
        }
      : undefined,
  }));
}

function normalizeV1(rawSchema: ExtensionUiSchemaV1): ExtensionUiSchema {
  return {
    version: '1.0',
    disabled: rawSchema.disabled,
    pages: rawSchema.pages || {},
    ux_elements: [
      ...normalizeNavigation(rawSchema.navigation),
      ...normalizeRouteEntries(rawSchema.routes),
      ...normalizeStylesheets(rawSchema.assets?.stylesheets),
    ],
  };
}

function normalizeLegacy(rawSchema: any): ExtensionUiSchema {
  return {
    version: rawSchema.version,
    disabled: rawSchema.disabled,
    pages: rawSchema.pages || {},
    ux_elements: rawSchema.ux_elements || [],
  };
}

const ExtensionUiSchemaService = {
  normalize(rawSchema: any): ExtensionUiSchema {
    if (rawSchema?.version === '1.0') {
      return normalizeV1(rawSchema as ExtensionUiSchemaV1);
    }
    return normalizeLegacy(rawSchema);
  },
};

export default ExtensionUiSchemaService;
