- Event hooks currently do not share ComponentLifeCycle logic with plugins listeners
  generators hence
  there is no idiomatic way to communicate error states on setup trigger or teardown.
  Fix this and update
  the appropriate documentation
- Asset and artifact endpoints raise generic ResourceErrors while payloads wraps and
  reraises payloaderrors
  behaviour is inconsistent determine if we should fix it given that we already
  committed to asset and artifact id
- tests load framework default plugins and event hooks should probably disable that
  feature. The loading is done in the server object
  so add the ability to globally disable all plugins event hooks listener/agent profiles
  from server config
