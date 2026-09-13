defmodule Plugboard.BuildStampTest do
  # `async: false`: capture_log installs a handler for the whole node, so an
  # async module could capture a line another module emitted and assert on it.
  use ExUnit.Case, async: false

  import ExUnit.CaptureLog

  # The provenance vocabulary, written out here rather than read back from the
  # stamp. A list taken from the artifact under test cannot notice that artifact
  # dropping a field.
  @want_fields ["component", "version", "commit", "tree", "built_at"]

  test "the proxy is stamped with every provenance field, in order, none blank" do
    fields = Plugboard.BuildStamp.fields()

    assert Enum.map(fields, &elem(&1, 0)) == @want_fields

    for {name, value} <- fields do
      assert value != "", "the proxy stamp field #{name} is blank"
    end

    assert {"component", "proxy"} = hd(fields)
  end

  test "what the proxy reports at startup is exactly the generated stamp" do
    expected =
      "build-provenance " <>
        Enum.map_join(Plugboard.BuildStamp.fields(), " ", fn {name, value} ->
          name <> "=" <> value
        end)

    assert Plugboard.BuildStamp.line() == expected

    logged = capture_log(fn -> assert Plugboard.Application.report_provenance() == :ok end)

    [reported] = logged |> String.trim() |> String.split("\n")

    assert String.ends_with?(reported, expected),
           "the proxy reported #{inspect(reported)}; it was stamped #{inspect(expected)}"
  end
end
