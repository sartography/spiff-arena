import {
  Box,
  Container,
  CssBaseline,
  IconButton,
  Grid,
  ThemeProvider,
  PaletteMode,
  createTheme,
  useMediaQuery,
} from '@mui/material';
import { Routes, Route, useLocation } from 'react-router-dom';
import MenuIcon from '@mui/icons-material/Menu';
import React, { ReactElement, useEffect, useState } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { ErrorBoundaryFallback } from './ErrorBoundaryFallack';
import SideNav from './components/SideNav';

import Extension from './views/Extension';
import { useUriListForPermissions } from './hooks/UriListForPermissions';
import { PermissionsToCheck, ProcessFile, ProcessModel } from './interfaces';
import { usePermissionFetcher } from './hooks/PermissionService';
import {
  ExtensionUiSchema,
  UiSchemaUxElement,
} from './extension_ui_schema_interfaces';
import HttpService from './services/HttpService';
import BaseRoutes from './views/BaseRoutes';
import BackendIsDown from './views/BackendIsDown';
import Login from './views/Login';
import useAPIError from './hooks/UseApiError';
import ScrollToTop from './components/ScrollToTop';
import { createSpiffTheme } from './assets/theme/SpiffTheme';

const fadeIn = 'fadeIn';
const fadeOutImmediate = 'fadeOutImmediate';

export default function ContainerForExtensions() {
  const [backendIsUp, setBackendIsUp] = useState<boolean | null>(null);
  const [extensionUxElements, setExtensionUxElements] = useState<
    UiSchemaUxElement[] | null
  >(null);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.extensionListPath]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  const { removeError } = useAPIError();

  const location = useLocation();

  const storedTheme: PaletteMode = (localStorage.getItem('theme') ||
    'light') as PaletteMode;
  const [globalTheme, setGlobalTheme] = useState(
    createTheme(createSpiffTheme(storedTheme)),
  );
  const isDark = globalTheme.palette.mode === 'dark';

  const [displayLocation, setDisplayLocation] = useState(location);
  const [transitionStage, setTransitionStage] = useState('fadeIn');
  const [additionalNavElement, setAdditionalNavElement] =
    useState<ReactElement | null>(null);

  const [isNavCollapsed, setIsNavCollapsed] = useState<boolean>(false);

  const isMobile = useMediaQuery((theme: any) => theme.breakpoints.down('sm'));
  const [isSideNavVisible, setIsSideNavVisible] = useState<boolean>(!isMobile);

  const toggleNavCollapse = () => {
    if (isMobile) {
      setIsSideNavVisible(!isSideNavVisible);
    } else {
      setIsNavCollapsed(!isNavCollapsed);
    }
    if (isMobile) {
      setIsSideNavVisible(!isSideNavVisible);
    } else {
      setIsNavCollapsed(!isNavCollapsed);
    }
  };

  const toggleDarkMode = () => {
    const desiredTheme: PaletteMode = isDark ? 'light' : 'dark';
    setGlobalTheme(createTheme(createSpiffTheme(desiredTheme)));
    localStorage.setItem('theme', desiredTheme);
  };

  useEffect(() => {
    /**
     * The housing app has an element with a white background
     * and a very high z-index. This is a hack to remove it.
     */
    const element = document.querySelector('.cds--white');
    if (element) {
      element.classList.remove('cds--white');
    }
  }, []);
  // never carry an error message across to a different path
  useEffect(() => {
    removeError();
    // if we include the removeError function to the dependency array of this useEffect, it causes
    // an infinite loop where the page with the error adds the error,
    // then this runs and it removes the error, etc. it is ok not to include it here, i think, because it never changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  /** Respond to transition events, this softens screen changes (UX) */
  useEffect(() => {
    if (location !== displayLocation) {
      // const isComingFromInterstitialOrProgress = /\/interstitial$|\/progress$/.test(displayLocation.pathname);
      // setIsLongFadeIn(
      //   isComingFromInterstitialOrProgress && location.pathname === '/',
      // );
      setTransitionStage(fadeOutImmediate);
    }
    if (transitionStage === fadeOutImmediate) {
      setDisplayLocation(location);
      setTransitionStage(fadeIn);
    }
  }, [location, displayLocation, transitionStage]);

  useEffect(() => {
    if (isMobile) {
      setIsSideNavVisible(false);
    } else {
      setIsSideNavVisible(true);
      setIsNavCollapsed(false);
    }
  }, [isMobile]);

  // never carry an error message across to a different path
  useEffect(() => {
    removeError();
    // if we include the removeError function to the dependency array of this useEffect, it causes
    // an infinite loop where the page with the error adds the error,
    // then this runs and it removes the error, etc. it is ok not to include it here, i think, because it never changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // eslint-disable-next-line sonarjs/cognitive-complexity
  useEffect(() => {
    const processExtensionResult = (processModels: ProcessModel[]) => {
      const eni: UiSchemaUxElement[] = processModels
        .map((processModel: ProcessModel) => {
          const extensionUiSchemaFile = processModel.files.find(
            (file: ProcessFile) => file.name === 'extension_uischema.json',
          );
          if (extensionUiSchemaFile && extensionUiSchemaFile.file_contents) {
            try {
              const extensionUiSchema: ExtensionUiSchema = JSON.parse(
                extensionUiSchemaFile.file_contents,
              );
              if (
                extensionUiSchema &&
                extensionUiSchema.ux_elements &&
                !extensionUiSchema.disabled
              ) {
                return extensionUiSchema.ux_elements;
              }
            } catch (jsonParseError: any) {
              console.error(
                `Unable to get navigation items for ${processModel.id}`,
              );
            }
          }
          return [] as UiSchemaUxElement[];
        })
        .flat();
      if (eni) {
        setExtensionUxElements(eni);
      }
    };

    const getExtensions = () => {
      setBackendIsUp(true);
      if (!permissionsLoaded) {
        return;
      }
      if (ability.can('GET', targetUris.extensionListPath)) {
        HttpService.makeCallToBackend({
          path: targetUris.extensionListPath,
          successCallback: processExtensionResult,
        });
      } else {
        // set to an empty array so we know that it loaded
        setExtensionUxElements([]);
      }
    };

    HttpService.makeCallToBackend({
      path: targetUris.statusPath,
      successCallback: getExtensions,
      failureCallback: () => setBackendIsUp(false),
    });
  }, [
    targetUris.extensionListPath,
    targetUris.statusPath,
    permissionsLoaded,
    ability,
  ]);

  const routeComponents = () => {
    return (
      <Routes>
        <Route
          path="*"
          element={
            <BaseRoutes
              extensionUxElements={extensionUxElements}
              setAdditionalNavElement={setAdditionalNavElement}
              isMobile={isMobile}
            />
          }
        />
        <Route path="extensions/:page_identifier" element={<Extension />} />
        <Route path="login" element={<Login />} />
      </Routes>
    );
  };

  const backendIsDownPage = () => {
    return [<BackendIsDown key="backendIsDownPage" />];
  };

  const innerComponents = () => {
    if (backendIsUp === null) {
      return [];
    }
    if (backendIsUp) {
      return routeComponents();
    }
    return backendIsDownPage();
  };

  return (
    <ThemeProvider theme={globalTheme}>
      <CssBaseline />
      <ScrollToTop />
      <ErrorBoundary FallbackComponent={ErrorBoundaryFallback}>
        <Container
          id="container-for-extensions-container"
          maxWidth={false}
          data-theme={globalTheme.palette.mode}
          sx={{
            // Hack to position the internal view over the "old" base components
            position: 'absolute',
            top: 0,
            left: 0,
            alignItems: 'center',
            zIndex: 1000,
            padding: '0px !important',
          }}
        >
          <Grid
            id="container-for-extensions-grid"
            container
            sx={{
              height: '100%',
            }}
          >
            <Box
              id="container-for-extensions-box"
              sx={{
                display: 'flex',
                width: '100%',
                height: '100vh',
                overflow: 'hidden', // Consider removing this if the child's overflow: auto is sufficient
              }}
            >
              {isSideNavVisible && (
                <SideNav
                  isCollapsed={isNavCollapsed}
                  onToggleCollapse={toggleNavCollapse}
                  onToggleDarkMode={toggleDarkMode}
                  isDark={isDark}
                  additionalNavElement={additionalNavElement}
                  setAdditionalNavElement={setAdditionalNavElement}
                  extensionUxElements={extensionUxElements}
                />
              )}
              {isMobile && !isSideNavVisible && (
                <IconButton
                  onClick={() => {
                    setIsSideNavVisible(true);
                    setIsNavCollapsed(false);
                  }}
                  sx={{
                    position: 'absolute',
                    top: 16,
                    right: 16,
                    zIndex: 1300,
                  }}
                >
                  <MenuIcon />
                </IconButton>
              )}
              <Box
                id="container-for-extensions-box-2"
                className={`${transitionStage}`}
                sx={{
                  bgcolor: 'background.default',
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  flexGrow: 1,
                  overflow: 'auto', // allow scrolling
                }}
                onAnimationEnd={(e) => {
                  if (e.animationName === fadeOutImmediate) {
                    setDisplayLocation(location);
                    setTransitionStage(fadeIn);
                  }
                }}
              >
                {innerComponents()}
              </Box>
            </Box>
          </Grid>
        </Container>
      </ErrorBoundary>
    </ThemeProvider>
  );
}
