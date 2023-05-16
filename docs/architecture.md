# Architecture

## Line processor
All parsing in Entangled is done on a per-line basis using a primitive line processor `mawk`. This makes Entangled both simple in design and easy to configure.

## Transactions
Whenever we write a file, this is done through the `Transaction` class.

```python
with transaction() as t:
    t.write(...)
```

At the end of a transaction all write actions are checked against a database of known file contents. If any conflicts are found, the entire transaction is not executed (unless run with `-f/--force`).