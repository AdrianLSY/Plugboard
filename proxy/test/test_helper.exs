# The fast tier runs with no Postgres, no network and no sleeps. Nothing is
# started here, because starting something is how a fast-tier test acquires a
# dependency nobody declared.
ExUnit.start()
