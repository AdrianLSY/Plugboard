defmodule Plugboard.DialyzerViolation do
  @moduledoc """
  A deliberately violating input for `mix dialyzer`.

  The `@spec` says `:ok` and the success typing is `:error`, which is
  `invalid_contract`. The compiler does not object — a spec that contradicts a
  body is exactly the class of defect that survives compilation, which is why
  the PLT is cached rather than the analysis skipped.
  """

  @spec always_ok() :: :ok
  def always_ok do
    :error
  end
end
