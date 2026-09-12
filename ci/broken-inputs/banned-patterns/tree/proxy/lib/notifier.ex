defmodule Fixture.Notifier do
  @moduledoc "Monitors, and never traps exits, so its :DOWN clause is unreachable."
  use GenServer

  def init(_), do: {:ok, %{ref: Process.monitor(self())}}

  def handle_info({:DOWN, _ref, _, _, _}, state), do: {:noreply, state}
end
