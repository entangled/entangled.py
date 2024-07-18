= Fibonacci sequence

The Fibonacci sequence can be computed in Python.

```python
#| id: fibonacci
def fibonacci(n, a=1, b=1):
    seq = [a, b]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq
```

Let's create a program that prints the first 20 numbers in the sequence:

```python
#| file: fib.py

<<fibonacci>>

if __name__ == "__main__":
    print(" ".join(str(i) for i in fibonacci(20))
```
