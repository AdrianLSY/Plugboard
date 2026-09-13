defmodule Plugboard.FormatViolation do
  @moduledoc """
  A deliberately violating input for `mix format --check-formatted`.

  The body of `value/0` is indented six columns where the formatter writes
  four. Everything else here is deliberately clean: it compiles without a
  warning, it carries a `@moduledoc` and a `@spec`, and Credo has no
  indentation check — so this file is visible to the formatter and to nothing
  else in the lint recipe.
  """

  @spec value() :: integer()
  def value do
      42
  end
end
