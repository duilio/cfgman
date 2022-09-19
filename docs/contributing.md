# How to contribute

TBD.

## Deploy a new release

1. Prepare a new branch.
2. Bump version:
   ```console
   $ poetry version patch
   ```
   We do follow semver, so use the appropriate string instead of patch to increment the version (e.g. `minor`, `major`, `prerelease`)
3. Push the new branch and open a PR.
4. Once merged, create a new tag:
   ```console
   $ git tag x.y.z && git push --tags
   ```
5. Edit the new release created by Github

TODO:

- Add `CHANGELOG` ?
- We might automate the tag creation once the a new version land in the main branch.
