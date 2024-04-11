import { ObjectWithStringKeysAndValues } from '../interfaces';

const appVersionInfo = () => {
  const versionInfoFromHtmlMetaTag = document.querySelector(
    'meta[name="version-info"]'
  );
  let versionInfo: ObjectWithStringKeysAndValues = {};
  if (versionInfoFromHtmlMetaTag) {
    console.log('versionInfoFromHtmlMetaTag', versionInfoFromHtmlMetaTag);
    const versionInfoContentString =
      versionInfoFromHtmlMetaTag.getAttribute('content');
    if (
      versionInfoContentString &&
      versionInfoContentString !== '%VITE_VERSION_INFO%'
    ) {
      console.log('versionInfoContentString', versionInfoContentString);
      versionInfo = JSON.parse(versionInfoContentString);
    }
  }

  return versionInfo;
};

export default appVersionInfo;
