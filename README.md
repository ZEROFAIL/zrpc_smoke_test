# Running the Smoke Test

The smo

## Get a fresh environment:
```
$ mkvirtualenv -p /usr/bin/python3.5 smoke_test
```

## Install dependencies:

```
$ pip install <zrpc_root@mutliple_broker>
$ pip install goblin, networkx
$ pip install -U aiohttp
```
**Make sure** you pull the most recent version of zrpc from gitlab

## Install the `zrpc_smoke_test` module

```
$ pip install git+https://github.com/ZEROFAIL/zrpc_smoke_test.git
```

## Populating the TinkerGraph DB

At the core of the smoke test is the `create` service. This service provides two
methods:

- `yield_edge` gets a single edge from and external datastore and returns it
to the client.

- `create_edge` receives the yielded edge checks if the source and target
vertices exist in the TinkerGraph DB, creates them if necessary, and then
creates the edge between them.

### Setting up the external datastore

The external datastore consists of a simple HTTP server that accesses a queue
of edges. These edges are read from a flat text file. To create the text file,
simply call:

```
$ creategraph
```

This will create an edge list with 10k nodes and ~500k edges. Next, fire up the
service that will queue and serve the edges:

```
$ queue
```

Ok, good to go, you can pretty much forget this part for the rest of the demo.

### Starting the create service

Now let's actually start putting some data in TinkerGraph. First fire up the
Gremlin Server. It doesn't really matter what version you are using:

```
$ ./bin/gremlin-server.sh
```

Next, get a broker up and running in a new terminal:

```
$ broker --frontend tcp://127.0.0.1:5556 --backend tcp://127.0.0.1:5555
```

Then, fire up a `create` service worker in a separate terminal:

```
$ worker --broker tcp://127.0.0.1:5555 --service create
```

Finally, start the client:

```
$ client --task build --broker tcp://127.0.0.1:5556
```

The client should start populating the database almost immediately, which you
can see in the output.

### Testing Failure

The client is the least robust part of the system, and in real life application
code should handle errors and recovery in case of broker failure. However,
it does have some recovery code baked in to the implementation.

Try killing the broker...what happens? The client should log that it has been
hospitalized. Turn it back on, the client should start creating data again.
You can do the same with the worker.

## Setting up the streaming service

The smoke test is also set up to simultaneously stream nodes and edges while
they are being created. So, you can leave the population process going, and
add a couple `streaming` service workers. Open a terminal:

```
$ worker --broker tcp://127.0.0.1:5555 --service streaming
```

Then in a separate terminal:

```
$ worker --broker tcp://127.0.0.1:5555 --service streaming
```

Then, open a couple more terminals and start up some clients:

```
$ client --task nodes --broker tcp://127.0.0.1:5556
```

and

```
$ client --task edges --broker tcp://127.0.0.1:5556
```

These clients will open streams that return the all the vertices and edges
in the database. Since edges are constantly being created by the `create`
service, we can slow the streams down a bit using a short sleep, and they
will continuously stream graph elements as they are created.


## Multi-Broker Example

This system runs equally well with multiple brokers. Shut down all of the clients,
brokers, and workers running from the first process (you could leave the broker
and workers running if you want, but this way the example is cleaner).

This example uses: 3 clients, 2 brokers, and 4 workers + the `queue` service and
the Gremlin Server. Therefore, you need 11 open terminals.

1. Start the Gremlin Server:
```
$ ./bin/gremlin-server.sh
```
2. Start the data queue:
```
$ queue
```
3. Start the brokers:
```
$ broker --frontend tcp://127.0.0.1:5556 --backend tcp://127.0.0.1:5555
```
```
$ broker --frontend tcp://127.0.0.1:8080 --backend tcp://127.0.0.1:8081
```
4. Start the workers:
```
$ worker --broker tcp://127.0.0.1:5555 --service streaming
```
```
$ worker --broker tcp://127.0.0.1:8081 --service streaming
```
```
$ worker --broker tcp://127.0.0.1:5555 --service create
```
```
$ worker --broker tcp://127.0.0.1:8081 --service create
```
5. Start the clients:
```
$ client --task build --broker tcp://127.0.0.1:5556 --broker tcp://127.0.0.1:8080
```
```
$ client --task nodes --broker tcp://127.0.0.1:5556 --broker tcp://127.0.0.1:8080
```
```
$ client --task edges --broker tcp://127.0.0.1:5556 --broker tcp://127.0.0.1:8080
```
6. Check for smoke...
