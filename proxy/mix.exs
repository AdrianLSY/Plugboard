defmodule Plugboard.MixProject do
  @moduledoc """
  The proxy: the Elixir application the operator runs.

  No Phoenix endpoint and no application middleware, per D5 — proxied traffic
  terminates before any of it, and the direct cause of the prior art's worst
  defect was `Plug.Parsers` consuming request bodies before the proxy read them.
  The pipeline arrives as a dedicated one, not as a layer under the default
  stack.
  """
  use Mix.Project

  def project do
    [
      app: :plugboard,
      version: "0.0.0",
      elixir: "~> 1.16",
      # Warnings are errors in every environment, not only in CI. The prior art
      # ran `--warning-as-errors` locally -- singular, therefore inert -- while
      # CI ran the plural flag, for months.
      elixirc_options: [warnings_as_errors: true],
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      dialyzer: [
        plt_local_path: "priv/plts",
        plt_core_path: "priv/plts",
        flags: [:error_handling, :extra_return, :missing_return, :unmatched_returns]
      ],
      test_paths: ["test"]
    ]
  end

  # The callback prints this component's provenance line and starts an empty
  # supervision tree -- not middleware and not an endpoint, which D5 and task
  # 2.1 forbid. Without it, starting the proxy printed nothing, and the one
  # caller of `Plugboard.provenance_line/0` was the check that claimed it did.
  def application do
    [
      mod: {Plugboard.Application, []},
      extra_applications: [:logger]
    ]
  end

  # Quality tooling only. No runtime dependency is added before the code that
  # needs it: the contract is frozen first, and a dependency chosen ahead of the
  # code is a dependency chosen without a reason.
  defp deps do
    [
      {:credo, "~> 1.7", only: [:dev, :test], runtime: false},
      {:dialyxir, "~> 1.4", only: [:dev, :test], runtime: false},
      {:sobelow, "~> 0.13", only: [:dev, :test], runtime: false},
      {:mix_audit, "~> 2.1", only: [:dev, :test], runtime: false}
    ]
  end
end
