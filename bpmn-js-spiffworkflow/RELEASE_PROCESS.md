## Releases

Be sure to edit the package.json, and update the version.  Releases won't create
a new NPM package unless the version was updated. 
A good way to do go about this is with npm version. Which will increment the version in package.json and create a new commit and tag.  Here are few examples that you might use, but
there is more information on [NPM Version](https://docs.npmjs.com/cli/v8/commands/npm-version).

For doing a patch release, you can do
```bash
npm version patch -m "Upgrade to %s for reasons"
```
aside from patch, you can use the keywords `minor`, and `major` (there are some others).  

Once this is complete, log into GitHub and do an offical release of the package.  A published release will result in a new published version on NPM (via a GitHub Action)

