This should raise a `CyclicReference` error.

``` {.python #hello}
<<hello>>
```

So should this:

``` {.python #phobos}
<<deimos>>
```

``` {.python #deimos}
<<phobos>>
```

also when tangling from something else:

``` {.python #mars}
<<phobos>>
```

What should not throw an error is doubling a reference:

``` {.python #helium}
<<electron>>
<<electron>>
```

``` {.python #electron}
negative charge
```
