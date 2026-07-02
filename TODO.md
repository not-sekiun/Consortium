- Event hooks currently do not share ComponentLifeCycle logic with plugins listeners
  generators hence
  there is no idiomatic way to communicate error states on setup trigger or teardown.
  Fix this and update
  the appropriate documentation
- Asset and artifact endpoints raise generic ResourceErrors while payloads wraps and
  reraises payload errors, move payloads to use the ResourceErrors where appropriate
  and use their own domain specific errors where appropriate relating to their metadata
- Payloads need to maintain a separate metadata file to store payload metadata, subsume
  that into repository
- tests load framework default plugins and event hooks should probably disable that
  feature. The loading is done in the server object
  so add the ability to globally disable all plugins event hooks listener/agent profiles
  from server config

# important

implement the data field fully for repository directory, put it in tests and also
docstrings
move payloads onto using the datafield entirely getting rid of payload metadata json
again update docstrings and tests
implement a user_account field for assets using the data field for who created the
asset (none for system/plugins) again update tests and docstrings
