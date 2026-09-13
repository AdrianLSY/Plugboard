defmodule Plugboard.CompileViolation do
  @moduledoc """
  A deliberately violating input for `mix compile --warnings-as-errors`.

  `value` is bound and never read, which the compiler warns about. `mix.exs`
  sets `elixirc_options: [warnings_as_errors: true]`, so the warning is an
  error in every environment rather than only under the CI flag — the prior
  art's defect was the singular `--warning-as-errors` spelling, which is
  accepted, does nothing, and reads in review as the plural one.
  """

  @spec ignore(term()) :: :ok
  def ignore(value) do
    :ok
  end
end
