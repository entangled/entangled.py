from entangled.tangle import read_markdown, tangle


def test_tangle(data):
    refs, content = read_markdown(data / "hello-world.md")
    tangled = tangle(refs, "hello_world.cc")
    print(tangled)
    with open(data / "hello_world.cc", "r") as f:
        assert f.read() == tangled + "\n"
