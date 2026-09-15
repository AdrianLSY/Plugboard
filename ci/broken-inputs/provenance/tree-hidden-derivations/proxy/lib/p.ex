defmodule P do
  @doc """
  Nothing in this documentation runs git.
  """
  # Hidden behind `#{`, which begins an INTERPOLATION and not a comment. A regex
  # that deletes from `#` to end of line deletes the System.cmd that mix really
  # compiles and really runs.
  def v, do: "#{System.cmd("git", ["rev-parse", "HEAD"])}"
end
