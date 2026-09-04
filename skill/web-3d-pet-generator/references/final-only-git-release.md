# Final-only Git Release

Use this procedure only after the user explicitly authorizes both upload and deletion of visible history.

1. Record the development HEAD, remote URL, visibility and current remote branch SHA.
2. Create a local `git bundle --all` outside the publication tree and record its SHA-256. Do not upload the bundle.
3. Build and test the development tree before selecting files.
4. Create a new clean directory. Copy only the latest editable source, web source, current runtime assets, three-view reference, final preview/QA evidence, MCP source/configuration, Skill, tests, lockfiles, build configuration, README and copyright notice.
5. Exclude old models, unversioned duplicates of the final model, old videos, iteration/pass renders, action-comparison frames, browser automation screenshots, diff files, plans/specs, research notes, logs, caches, `.blend1`, `node_modules`, local absolute paths, credentials and generated test artifacts. Keep one explicit versioned source file per asset directory; source/public/dist copies are allowed only when each location is required by the build contract and every copy has the same versioned filename and hash.
6. Search the entire clean tree for superseded version strings, internal project names, user paths, secrets and process vocabulary. Correct release documentation rather than carrying historical narratives forward.
7. Initialize a fresh repository, create exactly one root commit, add the existing private remote, then force-push that root commit to the release branch. Never rewrite a public or shared repository without equally explicit scope.
8. Verify from the remote: visibility is private, default branch is correct, commit count is one, remote SHA equals the clean local SHA, the tree contains no excluded paths and the latest model/reference/Skill are downloadable.
9. Report the remote URL, commit SHA, asset hashes, local backup path and the limitation that unreachable Git objects or provider caches may remain recoverable for a period even though no old history is visible from branch refs.
