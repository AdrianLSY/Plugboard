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
end
