- Add get_by_name service methods
- Remove EmptyNameErrors for entities whos primary identifies are UUIDs (basically
everything else) but keep EmptyNameErrors for entities whos primary identifiers are
their names (options).
- Consider making options case-insensitive
- 500 internal server errors cause an infinite loop
- Update the client side code to account for the new listener, agent, users and
template model
- if a listener is only compatible with one agent type we should not require the
passing of the agent type paramter to the register agent method.
- When tasking agents, no automatic data validation is being performed.
- list_results command doesnt work, also for interact agent it erroneously requires the
agent id to be passed.
- Get client to gracefully disconnect when server has exited before the client
- Get the client to gracefully handle 401s when server is restarted without client
restarting
