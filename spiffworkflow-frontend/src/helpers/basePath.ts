/**
 * Frontend base path helpers.
 *
 * Vite's `base` is exposed at runtime as `import.meta.env.BASE_URL` and is
 * always normalized to have a leading and trailing slash (e.g. "/" or
 * "/workflow/"). React Router's `basename` expects a leading slash without a
 * trailing slash (e.g. "/workflow") or `undefined` for root.
 */

export const normalizeBase = (raw?: string): string => {
  let base = (raw ?? '/').trim();
  if (!base) {
    base = '/';
  }
  if (!base.startsWith('/')) {
    base = `/${base}`;
  }
  if (!base.endsWith('/')) {
    base += '/';
  }
  return base;
};

/**
 * Returns the normalized Vite base URL. Defaults to "/" for backwards
 * compatibility with existing deployments.
 */
export const getBaseUrl = (baseUrl?: string): string => {
  const raw =
    baseUrl ?? (import.meta.env.BASE_URL as string | undefined) ?? '/';
  return normalizeBase(raw);
};

/**
 * Returns the React Router basename derived from the Vite base. Returns
 * `undefined` for root so that `createBrowserRouter` behaves identically to
 * the previous default.
 */
export const getRouterBasename = (baseUrl?: string): string | undefined => {
  const base = getBaseUrl(baseUrl);
  if (base === '/') {
    return undefined;
  }
  return base.replace(/\/$/, '');
};

/**
 * Prefixes an absolute frontend path with the current base, if any.
 * Example: withBasePath("/login") -> "/workflow/login" when base is "/workflow/"
 */
export const withBasePath = (path: string, baseUrl?: string): string => {
  const base = getBaseUrl(baseUrl);
  if (base === '/') {
    return path;
  }
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const baseWithoutTrailing = base.replace(/\/$/, '');
  // Avoid double prefix if path already starts with base
  if (
    normalizedPath === baseWithoutTrailing ||
    normalizedPath.startsWith(`${baseWithoutTrailing}/`)
  ) {
    return normalizedPath;
  }
  return `${baseWithoutTrailing}${normalizedPath}`;
};

/**
 * Strips the base prefix from a pathname, if present. Useful for comparing
 * `window.location.pathname` without being sensitive to the configured base.
 */
export const stripBasePath = (pathname: string, baseUrl?: string): string => {
  const basename = getRouterBasename(baseUrl);
  if (!basename) {
    return pathname;
  }
  if (pathname === basename) {
    return '/';
  }
  if (pathname.startsWith(`${basename}/`)) {
    const stripped = pathname.slice(basename.length);
    return stripped || '/';
  }
  return pathname;
};
