defmodule Plugboard.SobelowViolation do
  @moduledoc """
  A deliberately violating input for `mix sobelow --exit`.

  `Code.eval_string/1` on a caller-supplied binary is `RCE.CodeModule`. It is
  reported on this project even though there is no Phoenix router here, which
  is the fact the fixture exists to establish: Sobelow's non-Phoenix checks —
  code execution, directory traversal — do run over `lib/`, so a green Sobelow
  on the proxy is a scan that found nothing rather than a scan that looked at
  nothing.
  """

  @spec run(String.t()) :: term()
  def run(source) do
    Code.eval_string(source)
  end
end
