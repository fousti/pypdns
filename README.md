# pypdns

pypdns is a simple library wrapper around PDNS api (https://doc.powerdns.com/md/httpapi/README/).
It also feature a cli application for interacting with PowerDNS API.

  - Configurable via .ini or cli arguments
  - depends on : requests, docopt
  - Still a work in progress...

pypdns is not an official PowerDNS tool.

### Installation

pypdns is a standard python package, currently not push on pypi. Feel free to use your preferred way of installing.
(packaging is coming)

### Configuration (cli)

You can provide a  configuration file (check pypdns.example.ini), pypdns will first look in the current directory for a file name ```pypdns.ini``` or you can provide a path to a conf file through cli argument ```--config```.

### Usage

Creation


```pypdns  zones create example.com. --soa 'ns1.example.com. admins.example.com. 0 28800 7200 604800 86400' --nameservers=ns1.example.com.,ns2.example.com. --kind MASTER```

Note the serial is 0 , it's because serial is managed by PowerDNS automatically.

the --kind parameter is by default : NATIVE , if you want your zone to be publicly exposed, you have to specify --kind=MASTER.


Edition

When editing a record, the API always receive a PATCH requests with a full body (re)-defining the record ( creates, edits, disabled, delete ), by defaults , we first check if the record exists before making any changes.

the --override options is used for controlling the behaviour :

if set to True : No check before making the requests → all records existing records will be replaced

if set to False ( default ) : In a CLI mode, we asks the users if he wants to continue and we display the record which going to be replaced, when using the library, you MUST specify override kwargs otherwise the function exist with err = -1.

Note that for all operations : Delete, disabled , you can specify --override if you know what you're doing since the record is obviously present in the database.
Add record

```pypdns  record edit example.com test 10.190.26.57 'Add record test' --rtype A --reverse```

Use --reverse to automatically add a PTR record for the newly created record. Warning ! if a previous PTR record exists it will be replaced by the new one.
Disable record

```pypdns  record edit example.com test 10.190.26.57 'Disable record test' --rtype A --reverse --disabled```

This command disabled the given record , returning NXDOMAIN on resolve. But the record is still present in the DB.
Re-enable record

```pypdns  record edit example.com test 10.190.26.57 'Add record test' --rtype A ```

Delete record

```pypdns  record edit example.com test 10.190.26.57 'Delete record test' --rtype A --changetype DELETE --override```

Note that the PTR record ( if it exists ) will be not delete even if you specify --reverse (smile)
Delete PTR record

```pypdns  record edit 190.10.in-addr.arpa. 57.26 test.example.com 'Delete test record' --rtype PTR --changetype DELETE --override```

Edit zone in bind format ( only available on dnsmaster-02 )

 pdnsutils edit-zone example.com

Read

Note that all the filtering is done on client side so the requests will responds with all the data available.

The parameter --name is used to construct a regular expression, you can use that to filter with a pattern.
List zones

```pypdns  zones list --name <zone_name>```

List all the zones on the server, use --name to get a specific name.
Get zones

```pypdns  zones get <zone_name> --name <record_name> --rtype <record_type>```

Get zone content , you can filter on either record name or record type.
Search in Zone / Record

```pypdns  search <search_term>```

The * character can be used in <search_term> as a wildcard character and the ? character can be used as a wildcard for a single character.
