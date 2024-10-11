## Server REST API
- Add get_by_name service methods
- Remove EmptyNameErrors for entities whos primary identifies are UUIDs (basically
everything else) but keep EmptyNameErrors for entities whos primary identifiers are
their names (options).
- Consider making options case-insensitive
- 500 internal server errors cause an infinite loop
- if a listener is only compatible with one agent type we should not require the
passing of the agent type parameter to the register agent method.
- When tasking agents, no automatic data validation is being performed.
- Handler websocket 1006 disconnect message when clients forcefully disconnect
- Figure out what objects need non empty names and which dont. Systematize this as well.

## Client
- Deprecate client REST API connections service
- Refactor home commands to reflect interacting with a client session instead
- Shift the exit command to operate with client sessions instead of client connections
- Update the client side code to account for the new listener, agent, users and
template model
- list_results command does not work, also for interact agent it erroneously requires
the agent id to be passed.
- Get client to gracefully disconnect when server has exited before the client
- Get the client to gracefully handle 401s when server is restarted without client
restarting
- Add the ability to create client sessions independently of connecting them allowing
the client to connect and disconnect from servers at will without explicitly creating
or removing them from the client session manager.
- Make all tests pass. Many tests have been broken by the recent changes to the server.
    - Update json schemas - In particular add "additionalProperties": false to all
    schemas
