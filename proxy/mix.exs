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

  # `mod:` exists so that there IS a startup: rebuild-plugboard task 3.13 asks
  # each component to report the build it is at startup, and a library with no
  # application callback has nowhere to do that. It supervises nothing yet.
  def application do
    [extra_applications: [:logger], mod: {Plugboard.Application, []}]
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
