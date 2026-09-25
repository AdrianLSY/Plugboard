defmodule Plugboard do
  @moduledoc """
  Skeleton. What this component owns is stated once, in
  `docs/code/boundaries/proxy.md`, and its behaviour is owned by the
  specifications named there — neither is restated here.

  Deliberately empty of tunnel code: the wire schema is frozen before any
  implementation speaks it, because a hand-written codec landing first is the
  "two independent fictions" the conformance suite exists to remove.
  """

  @doc """
  A placeholder so the application compiles and the skeleton is provably
  buildable. Deleted by the first task that puts real code here.
  """
  @spec banner() :: String.t()
  def banner, do: "plugboard proxy: no contract implementation yet"

  @doc """
  What this component reports at startup: its identity and the four provenance
  fields, from the one place that computes them (`ci/stamp.py`).
  `Plugboard.Application.start/2` prints it, before the supervision tree starts.

  `ci/provenance-check.py` does not call this. It starts the application and
  reads the line from startup output, then holds each field to the generated
  stamp and the commit and tree status to what it reads from git itself. An
  earlier attempt built its expectation out of the same stamp it compared
  against, which passes over a blank stamp and over the wrong component name;
  calling this with startup suppressed proved the function and not the report.
  """
  @spec provenance_line() :: String.t()
  def provenance_line do
    stamp = Plugboard.BuildStamp.stamp()

    "#{Plugboard.BuildStamp.component()} version=#{stamp["version"]} " <>
      "commit=#{stamp["commit"]} tree=#{stamp["tree"]} built=#{stamp["built_at"]}"
  end
end
