# Application protocol definition

This document describes the general protocol framework, which is used
by applications that communicate over WebSocket. The overall format follows
[JSON-RPC 2.0 Specification](http://www.jsonrpc.org/specification), with
following "relaxations" (or modifications):

- **jsonrpc** in request/response is omitted (or optional)

  The version 2.0 is assumed and there is no need to support 1.0.

- Event stream support (if needed)

: A method can trigger a contiquous event stream, the specifics of which depend
  totally on the method and supplied parameters. Once activated, the reponder will
  send responce objects with method specific frequency and duration, until stopped
  by another method call or an terminating error occurs. All responce objects must
  have the **id** from the request that started the stream.

- Support for **Batch** feature is open to discussion and could be
  included, if there is need.

## JSON-RPC 2.0

Short recap from the JSON-RPC specification.

**Request object**
: The request object has following format:

         {
            'method': <REQUIRED: A string defining the method name>,
            'params': <OPTIONAL: A structured value for parameters>,
            'id': <REQUIRED: a string provided by the client, opaque to server>
         }

**Reply object**
: The server must always send a reply to the any **request object**. The reply must
  either indicate succes (reply has 'result' member), or failure (reply has
  'error' member containing the **Error object**.

  Reply reporting success

         {
            'result': <REQUIRED: content depends on request>,
            'id': <REQUIRED: a string provided by the client, copied from request>
         }
         
  Reply reporting failure:

         {
            'error': <REQUIRED: Error object, see below>,
            'id': <REQUIRED: a string provided by the client, copied from request>
         }


**Notification object**
: A request object without an 'id' parameter is a notification object. Notifications
  do not require any responses from the receiving entity.

         {
            'method': <REQUIRED: A string defining the method name>,
            'params': <OPTIONAL: A structured value for parameters>,
         }

**Error object**
: The error object (in fail reply) from JSON-RPC is used as is. Application defined
  error codes can be defined, if there is a need.

        {
            'code': <A integer that indicates the error type>,
            'message': <A string providing a short description>,
            'data':  <Optional information, can be omitted>
        }

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
may contain optional additional information.

This generic section defines some optional information members
mainly used for hinting the graphical user interface

- **help**: must be a text string representing a short description of
  the capability that could be used as a "tooltip" in graphical user
  interface (OPTIONAL).

- **group**: the value should be a simple string token, hints the user interface about
  grouping of capabilities. If not specified, the capability belongs to
  an unnamed default group.

- **label**: the value is a string containing a HTML fragment. This is used by the user
  interface in place of the method. This allows the server to style the presented
  command in the user interface (OPTIONAL).

- **schema**: If present, indicates the method accepts the indicated
  parameters. The value must be an array of *parameter definitions*,
  which will appear in the 'params' of the request object. In user
  interfaces, the input elements for the parameters are presented in
  the order they appear in the schema array.
  
  In simplest form, the *parameter definition* is a plain string,
  which defines the name of the parameter, and the value of the
  parameter will be a text string.
  
  When *parameter definition* is a dictionary, it can have following
  members:
  
  - **name**: The name of the parameter (REQUIRED)
  
  - **type**: Type of the parameter (OPTIONAL). This is only needed,
    if the JSON encoded parameter value should be something else than
    a string. Currently, only one type keyword is supported: `"type":
    "number"` requests that the input value is converted into integer.
	
  - **help**: Descrition of the parameter (OPTIONAL). This can be used
    as a tooltip for the parameter.
  
  Optionally, **only one** of the following:
  
  - **choice**: The value must be an array of choices (strings). The
    corresponding message parameter value will be one of the listed
    choices. Currently, the following specials exist:
	  
     - **`#ENBID`**: If present, it represents a list of known eNB
        identifiers (actually eNBId + cellId).

     - **`None`**: (represented as `null` in JSON). If chosen, the
       resulting parameter value is an empty string, unless also the
       type `number` is present, in which case the choice omits the
       parameter totally.

  - **range**: The value is an array of at most 4 integer values:
    `[<default>,<min>,<max>,<step>]`, any of which can be set to
    `None` (`null` in JSON). In GUI these are used for number input
     element. For example, `"range": [20]` requests an integer with
     default 20, but no other limitations.
		
  - **schema**: Defines a parameter as an object, the value must be
    an array of *parameter definitions*.

  If none of the above is present, then this *parameter definition*
  defines a simple text string input for the parameter value.
  
If there are no additional information, each capability value can be
left as an empty dictionary (or **null**).

### Examples

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
    
## Remote Control App  


## SMA App Protocol (Spectrum Sharing)

TBD <need examples and descriptions>

## Monitoring APP Protocol (KPIs)

TBD <need examples and descriptions>

## RRM APP Protocol (RAN sharing)

TBD <need examples and descriptions>
