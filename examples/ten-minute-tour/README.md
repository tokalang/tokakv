# TokaKV ten-minute tour

This is the source used by the public TokaKV quickstart. Starting with the
published Toka RC10 SDK:

```sh
toka new tokakv-tour
cd tokakv-tour
toka add tokakv
cp /path/to/tokakv/examples/ten-minute-tour/src/main.tk src/main.tk
toka run
toka run
```

The first run writes two versions, reads the old version through a snapshot,
keeps the latest value alive through a `ValueLease`, and closes the engine. The
second process reopens the same directory and verifies that WAL recovery
restored the latest value and sequence.

To restart the tour, remove only the generated `tokakv-tour-data` directory
inside the demo project.
