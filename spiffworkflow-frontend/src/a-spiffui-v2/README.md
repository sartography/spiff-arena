All new components, hooks, services, etc. related to the new UI are in this folder.

The Spiff UIv2 is a React app using Material Design System and Component Library. 

We use Material exclusively and prescriptively for everything, including:

- The color palette
- The layout grid
- Breakpoints and responsivness
- Components

There are no "<divs>" etc. in this app; all containers are things like Box, Stack, Grid, Container, etc.

Themeing is handled at the top level by a ThemeProvider, otherwise please us the "sx={{}}" overrides to set in-place styles.

Please maintain this level of Material usage in any component in this app. 