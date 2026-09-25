defmodule Plugboard.Application do
  @moduledoc """
  The proxy's startup path, and so the place it reports its build provenance.
  rebuild-plugboard task 3.13.

  `Plugboard.provenance_line/0` existed before this module did, and nothing
  called it on the way up: starting the proxy printed a compile message and
  nothing else, while the check claiming a startup report called the function
  itself with startup suppressed. A function that can report is not a process
  that does. So the line is printed here, before the supervision tree starts,
  and `ci/provenance-check.py` observes it by starting the application rather
  than by calling the function.

  Not application middleware and not an endpoint: D5 and task 2.1 forbid both
  ahead of the dedicated pipeline, and this starts neither. The tree is empty
  because nothing exists to supervise yet -- a child added before the code that
  needs it is a child chosen without a reason, which is the rule `mix.exs`
  already holds dependencies to.

  What it does not decide: the on-demand report, and the rest of what task 5.3
  asks of a startup report. This prints the generated stamp and nothing else.
  """
  use Application

  # `Supervisor.on_start/0` rather than the narrower `{:ok, pid()}`: the tree
  # can also answer `:ignore` or an error, and Dialyzer's `missing_return` flag
  # refuses a spec that leaves out a return the function can produce.
  @impl Application
  @spec start(Application.start_type(), term()) :: Supervisor.on_start()
  def start(_type, _args) do
    IO.puts(Plugboard.provenance_line())
    Supervisor.start_link([], strategy: :one_for_one, name: Plugboard.Supervisor)
  end
end
