defmodule Plugboard.CredoViolation do
  @moduledoc """
  A deliberately violating input for `mix credo --strict`.

  `value/0` is public and carries no `@spec`, which is
  `Credo.Check.Readability.Specs` — enabled explicitly in `.credo.exs` and a
  strict-mode check. The file is formatted, compiles without a warning, and
  says nothing Dialyzer or Sobelow can object to, so Credo is the only tool in
  the lint recipe that sees it.
  """

  def value do
    42
  end
end
