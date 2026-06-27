# Artifacts service

Artifacts are files that are generated remote agents and then either
downloaded by other clients or used within the framework. Typically, the artifacts
service is used to make remote files from agents available to clients locally.

The artifacts service is a particular instance of a repository service and as such has
the exact same API see [Repository Service Reference](repository-service-reference.md)
for more information.

Note that at the REST API level however the artifacts service does not allow clients to
upload files to it.
