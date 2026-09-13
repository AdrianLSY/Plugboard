defmodule Plugboard.MixProject do
  @moduledoc false
  use Mix.Project

  def project, do: [app: :plugboard, version: "0.0.0"]

  def application, do: [extra_applications: [:logger], mod: {Plugboard.Application, []}]
end
