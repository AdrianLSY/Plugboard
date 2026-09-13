defmodule Plugboard.Application do
  @moduledoc false
  use Application

  require Logger

  @impl Application
  def start(_type, _args) do
    :ok = report_provenance()
    Supervisor.start_link([], strategy: :one_for_one, name: Plugboard.Supervisor)
  end

  @spec report_provenance() :: :ok
  def report_provenance do
    Logger.info(Plugboard.BuildStamp.line())
  end
end
