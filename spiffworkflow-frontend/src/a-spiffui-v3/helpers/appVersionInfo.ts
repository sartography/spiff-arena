import { ObjectWithStringKeysAndValues } from '../interfaces';

const appVersionInfo = () => {
  const versionInfoFromHtmlMetaTag = document.querySelector(
    'meta[name="version-info"]',
  );
  let versionInfo: ObjectWithStringKeysAndValues = {};
  if (versionInfoFromHtmlMetaTag) {
    const versionInfoContentString =
      versionInfoFromHtmlMetaTag.getAttribute('content');
    if (
      versionInfoContentString &&
      versionInfoContentString !== '%VITE_VERSION_INFO%'
    ) {
      versionInfo = JSON.parse(versionInfoContentString);
    }
  }

  return versionInfo;
};

export default appVersionInfo;
