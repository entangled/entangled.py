This is testing the REPL hook.

```python
#| id: hello-world
#| classes: ["repl"]
#| session: test.json
print("Hello, World!")
```

```python
#| id: hello-world
#| classes: ["repl"]
6 * 7
```

We leave out the `repl` class, but keep the id. This should still be entered into the REPL, but the result is not shown in rendering.

```python
#| id: hello-world
def fac(n):
    for i in range(1, n):
        n *= i
    return n
```

```python
#| id: hello-world
#| classes: ["repl"]
fac(10)
```

This should produce an output similar to:

```yaml
#| file: expected.yml
config:
  command: python -q
  first_prompt: ">>> "
  change_prompt: "import sys; sys.ps1 = '{key}>>> '; sys.ps2 = '{key}+++ '"
  prompt: "{key}>>> "
  continuation_prompt: "{key}\\+\\+\\+ "
  environment:
    NO_COLOR: "1"
commands:
  - command: print("Hello, World!")
  - command: 6 * 7
  - command: |-
      def fac(n):
          for i in range(1, n):
              n *= i
          return n
  - command: fac(10)
```
