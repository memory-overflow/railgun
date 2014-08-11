Finish <code>reform_path</code> in path.py, so that it will produce output for input <code>path</code> that satisfies given requirements.

The homework has 6 test points. Please upload your handin before deadline.

```python
def reform_path(path):
    """Re-format the input `path`. Strip all "." and ".." parts. Return the
    new path that matches the following rules:

    *   All "\\" in old path should be treated as and translated to "/".
    *   Continous "/" should be compressed to one.
    *   "." in old path should be stripped directly.
    *   ".." in old path should consume one parent dir. However if no parent
        exists, a `ValueError` should be raised.
    *   If old path is empty, or all parents in old path is consumed, new path
        should be "" or "/", depending on the following rule.
    *   New path should starts with "/" if and only if the old does.
    *   Whether or not the old path ends with "/", new path shouldn't, unless
        it is "/".
    """

    raise NotImplementedError()
```