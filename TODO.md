- Event hooks currently do not share ComponentLifeCycle logic with plugins listeners generators hence
there is no idiomatic way to communicate error states on setup trigger or teardown. Fix this and update
the appropriate documentation