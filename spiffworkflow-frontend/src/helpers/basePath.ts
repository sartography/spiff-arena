const getBaseUrl = (baseUrl?: string): string => {
  return baseUrl ?? (import.meta.env.BASE_URL as string | undefined) ?? '/';
};

export const getRouterBasename = (baseUrl?: string): string | undefined => {
  const base = getBaseUrl(baseUrl);
  return base === '/' ? undefined : base.replace(/\/$/, '');
};

export const withBasePath = (path: string, baseUrl?: string): string => {
  // Leave absolute URLs (https://..., mailto:..., etc.) untouched.
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(path)) {
    return path;
  }
  const basename = getRouterBasename(baseUrl);
  if (!basename) {
    return path;
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  if (
    normalizedPath === basename ||
    normalizedPath.startsWith(`${basename}/`)
  ) {
    return normalizedPath;
  }
  return `${basename}${normalizedPath}`;
};

export const stripBasePath = (pathname: string, baseUrl?: string): string => {
  const basename = getRouterBasename(baseUrl);
  if (!basename) {
    return pathname;
  }
  if (pathname === basename) {
    return '/';
  }
  if (pathname.startsWith(`${basename}/`)) {
    return pathname.slice(basename.length) || '/';
  }
  return pathname;
};
