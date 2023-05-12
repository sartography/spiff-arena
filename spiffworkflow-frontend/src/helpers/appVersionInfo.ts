const appVersionInfo = () => {
  const versionInfoFromHtmlMetaTag = document.querySelector(
    'meta[name="version-info"]'
  );
  let versionInfo: { [key: string]: string } = {};
  if (versionInfoFromHtmlMetaTag) {
    const versionInfoContentString =
      versionInfoFromHtmlMetaTag.getAttribute('content');
    if (
      versionInfoContentString &&
      versionInfoContentString !== '%REACT_APP_VERSION_INFO%'
    ) {
      versionInfo = JSON.parse(versionInfoContentString);
    }
  }
  versionInfo = {
    version: '1.0.0',
    git_sha: 'sdkfjksd',
    sure: '3',
  };

  return versionInfo;
};

export default appVersionInfo;
