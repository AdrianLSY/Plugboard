defmodule Fixture.Wire do
  @moduledoc "A term rendering that can reach a peer."

  def refuse(reason) do
    push(%{error: inspect(reason)})
  end

  defp push(payload), do: payload
end
