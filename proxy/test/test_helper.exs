# The fast tier runs with no Postgres, no network and no sleeps. This helper
# starts nothing, because starting something is how a fast-tier test acquires a
# dependency nobody declared.
#
# `mix test` has already started Plugboard.Application by the time this runs:
# it prints the provenance line and starts an empty Plugboard.Supervisor. That
# is the component under test coming up the way it always does, not a
# dependency a test acquires -- it opens no socket, reaches no database, and
# supervises nothing a test could call. A child added to that tree starts under
# every fast-tier test too, and answers to the first paragraph as if it had
# been started here.
ExUnit.start()
