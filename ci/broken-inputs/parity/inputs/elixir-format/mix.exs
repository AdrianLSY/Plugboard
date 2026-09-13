# A minimal project holding exactly one defect: source the formatter would
# rewrite. Nothing here is unformatted except lib/unformatted.ex, so an
# invocation that exits zero over this tree did not check formatting.
defmodule ParityFormat.MixProject do
  use Mix.Project

  def project do
    [app: :parity_format, version: "0.0.0", elixir: "~> 1.16"]
  end

  def application do
    [extra_applications: []]
  end
end
