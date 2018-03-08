# Application protocol definition

This document describes the general protocol framework, which is used
by applications that communicate over WebSocket. The overall format follows
[JSON-RPC 2.0 Specification](http://www.jsonrpc.org/specification), with
following "relaxations" (or modifications):

- **jsonrpc** in request/response is omitted (or optional)

  The version 2.0 is assumed and there is no need to support 1.0.

- Event stream support (if needed)

  A method can trigger a contiquous event stream, the specifics of which depend
  totally on the method and supplied parameters. Once activated, the reponder will
  send responce objects with method specific frequency and duration, until stopped
  by another method call or an terminating error occurs. All responce objects must
  have the **id** from the request that started the stream.

- Support for **Batch** feature is open to discussion and could be
  included, if there is need.

- Error object

  The error object from JSON-RPC is used as is. Application defined error codes can
  be defined, if there is a need.

## Generic Protocol Specification and Guidelines

As noted in the JSON-RCP document, this protocol can be used
on both ends of the WebSocket connection as **server** and/or **client**
role regardless of which side actually initiated the connection.

A **client** can send multiple requests without waiting a respose in
between them.  In such case, the **server** can send the responses
when they become ready -- response order may differ from request
order.

If a request results an error object reply, the client should not
try to interpret the error code. Any error just means that the
request was not accepted. The error information is for debugging,
logging or reporting to the user in case of interactive application.

Use notifications in reporting non-fatal exceptional conditions.

### Capabilities Notification

After a WebSocket connection is established, both sides can send
**capabilities** notification. This notification defines the requests
and notifications (methods) that the sender supports.

A client should only send requests or notifications which were
explicitly allowed by the server. The only exception is the
**capabilities** notification, which can be sent any time.

The syntax of **cababilities** notification (*note the lack of id*):

     {
        "method": "capabilities",
        "params": {
          "cap1" : { <description of capability 1> },
          "cap2" : { <description of capability 2> },
          ...
        }
     }

The **params** is a dictionary of accepted capabilities, and each value
may contain optional additional information. This generic section defines
only one optional information field: **help**, which must be a text
string representing a short description of the capability that
could be used as a "tooltip" in graphical user interface. If there are
no additional information, each capability value can be left as an
empty dictionary (or **null**).

Example handshake of web GUI connecting the SMA application (*assuming
the current semantics were upgraged to this protocol*):

    GUI ---> {"method": "capabilities"}
    SMA ---> {"method": "capabilities",
              "params": {"cmd1": {"help": "cmd1 help"},
                         "cmd2": {"help": "cmd2 help"}}
             }

Means that the GUI accepts no requests (actually, GUI sending this is
optional, as "no capabilities" is the default for a new WebSocket
connection), and the only request GUI can use for SMA, are the "cmd1"
and "cmd2". SMA app sends "get-list" **notifications** implicitly.

    SMA ---> {"method": "get-list", "params": <result of get-list>}
         ...
         ...
        ---> {"method": "get-list", "params": <result of get-list>}
         ...

The "get-list" could also be designed as a method that has the
streaming semantics, and thus once requested, SMA would keep sending
repeated responses whenever the content of the list changes. For
documentation purposes, the capability description could contain some
field that marks it as a streaming event (for example, have **cancel**
with value indicating the method that cancels the streaming action).

The following is just rough sketch of an idea. Defining a more generic
set of methods for subscrition service could be a better approach.

    SMA ---> {"method": "capabilities",
              "params": {"cmd1": {"help": "cmd1 help"},
                         "cmd2": {"help": "cmd2 help"},}
                         "get-list": {"help": "stream of get-list", "cancel": "cancel"},}
             }

    GUI ---> {"method": "get-list", "id": "list-report"}
    SMA ---> {"id": "list-report", "result": <result of get-list>}
         ...
         ...
        ---> {"id": "list-report", "result": <result of get-list>}
         ...
    GUI ---> {"method": "cancel", "id": "list-report-cancel-id", "params": "list-resport"}
    SMA ---> {"id": "list-report-cancel-id", "result": "list-resport"}
    

## SMA App Protocol (Spectrum Sharing)

TBD <need examples and descriptions>

## Monitoring APP Protocol (KPIs)

TBD <need examples and descriptions>

## RRM APP Protocol (RAN sharing)

TBD <need examples and descriptions>
