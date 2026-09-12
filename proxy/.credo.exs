# Credo in strict mode. The prior art declared credo as a dependency and never
# invoked it, which is indistinguishable from not having it.
%{
  configs: [
    %{
      name: "default",
      strict: true,
      files: %{
        included: ["lib/", "test/"],
        excluded: [~r"/_build/", ~r"/deps/"]
      },
      checks: %{
        enabled: [
          {Credo.Check.Readability.Specs, []},
          {Credo.Check.Design.TagTODO, [exit_status: 2]},
          {Credo.Check.Design.TagFIXME, [exit_status: 2]}
        ]
      }
    }
  ]
}
