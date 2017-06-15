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

### Examples
Create zone :
```pypdns zones create 12example.com. --soa 'ns1.example.com. admins.example.com. 0 28800 7200 604800 86400' --nameservers=ns1.example.com.,ns2.example.com.```
Note that the serial is managed automatically by PowerDNS, pypdns use the default behaviour but --soa_edit can be used to override this. ( same value of soa_edit in pdns API)

List zones : ( add --name to filter on zone name)
```pypdns zones list --name .*in\-addr.*```

Get zone info :
```pypdns get zones example.com```

Add an A record to a zone
```pypdns record add example.com test 10.190.32.32 'mandatory comment' --rtype A```

Search an object in DNS ( zone or record), use * for wildcard char and ? for a single wildcard char.

```pypdns search example* --rtype A``` (search for a A record matching example*)

```pypdns search exa* --otype zone``` ( search for a zone matching exa*)
