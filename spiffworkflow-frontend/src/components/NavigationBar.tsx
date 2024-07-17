import {
  Toggletip,
  ToggletipButton,
  ToggletipContent,
  Button,
  Header,
  HeaderContainer,
  HeaderMenuButton,
  SkipToContent,
  SideNav,
  SideNavItems,
  HeaderSideNavItems,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalAction,
  HeaderGlobalBar,
} from '@carbon/react';
import { Logout } from '@carbon/icons-react';
import { useEffect, useState } from 'react';
import { useLocation, Link, LinkProps } from 'react-router-dom';
import { Box } from '@mui/material';
import Logo from '../logo.svg';
import UserService from '../services/UserService';
import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';
import { DOCUMENTATION_URL, SPIFF_ENVIRONMENT } from '../config';
import appVersionInfo from '../helpers/appVersionInfo';
import { slugifyString } from '../helpers';
import ExtensionUxElementForDisplay from './ExtensionUxElementForDisplay';
import SpiffTooltip from './SpiffTooltip';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { Can } from '../contexts/Can';

type OwnProps = {
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export default function NavigationBar({ extensionUxElements }: OwnProps) {
  const handleLogout = () => {
    UserService.doLogout();
  };

  const location = useLocation();
  const [activeKey, setActiveKey] = useState<string>('');

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.authenticationListPath]: ['GET'],
    [targetUris.messageInstanceListPath]: ['GET'],
    [targetUris.secretListPath]: ['GET'],
    [targetUris.dataStoreListPath]: ['GET'],
    [targetUris.extensionListPath]: ['GET'],
    [targetUris.processInstanceListForMePath]: ['POST'],
    [targetUris.processGroupListPath]: ['GET'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  // default to readthedocs and let someone specify an environment variable to override:
  //
  let externalDocumentationUrl = 'https://spiff-arena.readthedocs.io';
  if (DOCUMENTATION_URL) {
    externalDocumentationUrl = DOCUMENTATION_URL;
  }

  const processGroupPath = '/process-groups';

  const versionInfo = appVersionInfo();

  const logoStyle = {
    marginTop: '1rem',
    marginBottom: '1rem',
    color: 'pink',
    svg: {
      height: 37,
      width: 152,
    },
  };

  useEffect(() => {
    let newActiveKey = 'unknown';
    if (location.pathname.match(/^\/messages\b/)) {
      newActiveKey = '/messages';
    } else if (location.pathname.match(/^\/process-instances\/reports\b/)) {
      newActiveKey = '/process-instances/reports';
    } else if (location.pathname.match(/^\/process-instances\b/)) {
      newActiveKey = '/process-instances';
    } else if (location.pathname.match(/^\/process-(groups|models)\b/)) {
      newActiveKey = processGroupPath;
    } else if (location.pathname.match(/^\/editor\b/)) {
      newActiveKey = processGroupPath;
    } else if (location.pathname.match(/^\/configuration\b/)) {
      newActiveKey = '/configuration';
    } else if (location.pathname.match(/^\/data-stores\b/)) {
      newActiveKey = '/data-stores';
    } else if (location.pathname === '/') {
      newActiveKey = '/';
    } else if (location.pathname.match(/^\/tasks\b/)) {
      newActiveKey = '/';
    }
    setActiveKey(newActiveKey);
  }, [location]);

  const isActivePage = (menuItemPath: string) => {
    return activeKey === menuItemPath;
  };

  const userEmail = UserService.getUserEmail();
  const username = UserService.getPreferredUsername();

  const extensionUserProfileElement = (uxElement: UiSchemaUxElement) => {
    const navItemPage = `/extensions${uxElement.page}`;
    return (
      <Link key={navItemPage} to={navItemPage}>
        {uxElement.label}
      </Link>
    );
  };

  const profileToggletip = () => {
    let aboutLinkElement = null;

    if (Object.keys(versionInfo).length) {
      aboutLinkElement = <Link to="/about">About</Link>;
    }

    return (
      <div style={{ display: 'flex' }} id="user-profile-toggletip">
        <Toggletip isTabTip align="bottom-right">
          <ToggletipButton
            aria-label="User Actions"
            className="user-profile-toggletip-button"
            type="button"
          >
            <div className="user-circle">{username[0].toUpperCase()}</div>
          </ToggletipButton>
          <ToggletipContent className="user-profile-toggletip-content">
            <p>
              <strong>{username}</strong>
            </p>
            {username !== userEmail && <p>{userEmail}</p>}
            <hr />
            {aboutLinkElement}
            <a target="_blank" href={externalDocumentationUrl} rel="noreferrer">
              Documentation
            </a>
            <ExtensionUxElementForDisplay
              displayLocation="user_profile_item"
              elementCallback={extensionUserProfileElement}
              extensionUxElements={extensionUxElements}
            />
            {!UserService.authenticationDisabled() ? (
              <>
                <hr />
                <Button
                  data-qa="logout-button"
                  className="button-link"
                  onClick={handleLogout}
                >
                  <Logout />
                  &nbsp;&nbsp;Sign out
                </Button>
              </>
            ) : null}
          </ToggletipContent>
        </Toggletip>
      </div>
    );
  };

  const logoutAction = () => {
    if (UserService.isLoggedIn()) {
      return (
        <>
          {SPIFF_ENVIRONMENT ? (
            <HeaderGlobalAction
              title={`The current SpiffWorkflow environment is: ${SPIFF_ENVIRONMENT}`}
              className="spiff-environment-header-text unclickable-text"
              aria-label="our-aria-label"
            >
              {SPIFF_ENVIRONMENT}
            </HeaderGlobalAction>
          ) : null}
          {profileToggletip()}
        </>
      );
    }
    return null;
  };

  const configurationElement = (closeSideNavMenuIfExpanded?: Function) => {
    return (
      <Can
        I="GET"
        a={targetUris.authenticationListPath}
        ability={ability}
        passThrough
      >
        {(authenticationAllowed: boolean) => {
          return (
            <Can
              I="GET"
              a={targetUris.secretListPath}
              ability={ability}
              passThrough
            >
              {(secretAllowed: boolean) => {
                if (secretAllowed || authenticationAllowed) {
                  return (
                    <SpiffTooltip title="Manage Secrets and Authentication information for Service Tasks">
                      <HeaderMenuItem
                        as={Link}
                        to="/configuration"
                        onClick={closeSideNavMenuIfExpanded}
                        isActive={isActivePage('/configuration')}
                      >
                        Configuration
                      </HeaderMenuItem>
                    </SpiffTooltip>
                  );
                }
                return null;
              }}
            </Can>
          );
        }}
      </Can>
    );
  };

  const extensionHeaderMenuItemElement = (uxElement: UiSchemaUxElement) => {
    const navItemPage = `/extensions${uxElement.page}`;
    const regexp = new RegExp(`^${navItemPage}$`);
    if (regexp.test(location.pathname)) {
      setActiveKey(navItemPage);
    }
    return (
      <SpiffTooltip key={navItemPage} title={uxElement?.tooltip}>
        <HeaderMenuItem
          as={Link}
          to={navItemPage}
          isActive={isActivePage(navItemPage)}
          data-qa={`extension-${slugifyString(
            uxElement.label || uxElement.page,
          )}`}
        >
          {uxElement.label || uxElement.page}
        </HeaderMenuItem>
      </SpiffTooltip>
    );
  };

  const headerMenuItems = (closeSideNavMenuIfExpanded?: Function) => {
    if (!UserService.isLoggedIn()) {
      return null;
    }
    return (
      <>
        <SpiffTooltip title="View and start Process Instances">
          <HeaderMenuItem<LinkProps>
            as={Link}
            to="/"
            onClick={closeSideNavMenuIfExpanded}
            isActive={isActivePage('/')}
          >
            <div>Home</div>
          </HeaderMenuItem>
        </SpiffTooltip>

        <Can I="GET" a={targetUris.processGroupListPath} ability={ability}>
          <SpiffTooltip title="Find and organize Process Groups and Process Models">
            <HeaderMenuItem
              as={Link}
              to={processGroupPath}
              onClick={closeSideNavMenuIfExpanded}
              isActive={isActivePage(processGroupPath)}
              data-qa="header-nav-processes"
            >
              Processes
            </HeaderMenuItem>
          </SpiffTooltip>
        </Can>
        <Can
          I="POST"
          a={targetUris.processInstanceListForMePath}
          ability={ability}
        >
          <SpiffTooltip title="List of active and completed Process Instances">
            <HeaderMenuItem
              as={Link}
              to="/process-instances"
              onClick={closeSideNavMenuIfExpanded}
              isActive={isActivePage('/process-instances')}
            >
              Process Instances
            </HeaderMenuItem>
          </SpiffTooltip>
        </Can>
        <Can I="GET" a={targetUris.messageInstanceListPath} ability={ability}>
          <SpiffTooltip title="Browse messages being sent and received">
            <HeaderMenuItem
              as={Link}
              to="/messages"
              onClick={closeSideNavMenuIfExpanded}
              isActive={isActivePage('/messages')}
            >
              Messages
            </HeaderMenuItem>
          </SpiffTooltip>
        </Can>
        <Can I="GET" a={targetUris.dataStoreListPath} ability={ability}>
          <SpiffTooltip title="Browse data that has been saved to Data Stores">
            <HeaderMenuItem
              as={Link}
              to="/data-stores"
              onClick={closeSideNavMenuIfExpanded}
              isActive={isActivePage('/data-stores')}
            >
              Data Stores
            </HeaderMenuItem>
          </SpiffTooltip>
        </Can>
        {configurationElement(closeSideNavMenuIfExpanded)}
        <ExtensionUxElementForDisplay
          displayLocation="header_menu_item"
          elementCallback={extensionHeaderMenuItemElement}
          extensionUxElements={extensionUxElements}
        />
      </>
    );
  };

  // App.jsx forces login (which redirects to keycloak) so we should never get here if we're not logged in.
  if (!UserService.isLoggedIn()) {
    return (
      <HeaderContainer
        render={() => (
          <Header aria-label="IBM Platform Name" className="cds--g100">
            <HeaderName as={Link} to="/" prefix="" data-qa="spiffworkflow-logo">
              <Box sx={logoStyle}>
                {/* @ts-expect-error TS(2322) FIXME */}
                <Logo style={{ ...logoStyle }} />
              </Box>
            </HeaderName>
          </Header>
        )}
      />
    );
  }

  if (activeKey && ability) {
    return (
      <HeaderContainer
        render={({ isSideNavExpanded, onClickSideNavExpand }: any) => {
          // define function to call onClickSideNavExpand if the side nav is not expanded
          // and the user clicks on a header menu item
          function closeSideNavMenuIfExpanded() {
            if (isSideNavExpanded) {
              // this function that is yielded to us by carbon is more of a toggle than an expand.
              // here we are using it to close the menu if it is open.
              onClickSideNavExpand();
            }
          }

          return (
            <Header aria-label="IBM Platform Name" className="cds--g100">
              <SkipToContent />
              <HeaderMenuButton
                data-qa="header-menu-expand-button"
                aria-label="Open menu"
                onClick={onClickSideNavExpand}
                isActive={isSideNavExpanded}
              />
              <HeaderName
                as={Link}
                to="/"
                onClick={closeSideNavMenuIfExpanded}
                prefix=""
                data-qa="spiffworkflow-logo"
              >
                <Box sx={logoStyle}>
                  <Logo />
                </Box>
              </HeaderName>
              <HeaderNavigation
                data-qa="main-nav-header"
                aria-label="Spiffworkflow"
              >
                {headerMenuItems()}
              </HeaderNavigation>
              <SideNav
                data-qa="side-nav-items"
                aria-label="Side navigation"
                expanded={isSideNavExpanded}
                isPersistent={false}
              >
                <SideNavItems>
                  <HeaderSideNavItems>
                    {headerMenuItems(closeSideNavMenuIfExpanded)}
                  </HeaderSideNavItems>
                </SideNavItems>
              </SideNav>
              <HeaderGlobalBar>{logoutAction()}</HeaderGlobalBar>
            </Header>
          );
        }}
      />
    );
  }
  return null;
}
