# Local Wheels

If you have any wheels you wish to test locally, copy them into this folder then run:

```
poetry add local_wheels/my.whl
```

Or if you don't want to wait for poetry to do that operation, you can sideload it:

```
poetry run pip install local_wheels/*.whl
```

when you boot the backend.