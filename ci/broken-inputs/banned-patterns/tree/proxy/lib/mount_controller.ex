defmodule Fixture.MountController do
  @moduledoc "A controller action whose with has no else."

  def create(conn, params) do
    with {:ok, tenant} <- fetch(params),
         {:ok, mount} <- build(tenant) do
      {:ok, mount}
    end
  end

  defp fetch(p), do: {:ok, p}
  defp build(t), do: {:ok, t}
end
