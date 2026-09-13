defmodule ParityWarnings do
  @moduledoc "One warning, on purpose: `unused` is bound and never read."

  def go do
    unused = 1
    :ok
  end
end
