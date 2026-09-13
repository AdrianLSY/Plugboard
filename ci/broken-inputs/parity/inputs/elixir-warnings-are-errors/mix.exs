# A minimal project holding exactly one defect: a module that compiles with a
# warning. `elixirc_options: [warnings_as_errors: true]` is DELIBERATELY absent.
#
# proxy/mix.exs sets it, which is the right thing for the proxy and the wrong
# thing for this input: with the option set, `mix compile` refuses whatever flag
# it was handed, so the input could no longer tell a working flag from an inert
# one -- and telling those apart is the whole reason this directory exists.
defmodule ParityWarnings.MixProject do
  use Mix.Project

  def project do
    [app: :parity_warnings, version: "0.0.0", elixir: "~> 1.16"]
  end

  def application do
    [extra_applications: []]
  end
end
