defmodule PlugboardTest do
  use ExUnit.Case, async: true

  doctest Plugboard

  test "the skeleton compiles and reports that it carries no implementation" do
    assert Plugboard.banner() =~ "no contract implementation yet"
  end
end
