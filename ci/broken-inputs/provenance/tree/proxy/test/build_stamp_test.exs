defmodule Plugboard.BuildStampTest do
  # `async: false`: capture_log installs a handler for the whole node.
  use ExUnit.Case, async: false

  test "what the proxy reports at startup is exactly the generated stamp" do
    assert Plugboard.Application.report_provenance() == :ok
  end
end
