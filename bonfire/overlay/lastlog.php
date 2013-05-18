<html>
<head>
<style type="text/css">
table.gridtable {
	font-family: verdana,arial,sans-serif;
	font-size:11px;
	color:#333333;
	border-width: 1px;
	border-color: #666666;
	border-collapse: collapse;
}
table.gridtable th {
	border-width: 1px;
	padding: 8px;
	border-style: solid;
	border-color: #666666;
	background-color: #dedede;
}
table.gridtable td {
	border-width: 1px;
	padding: 8px;
	border-style: solid;
	border-color: #666666;
	background-color: #ffffff;
}
</style>
</head>
<table class='gridtable'>
<tr>
<th>Time</th>
<th>Host</th>
<th>Message</th>
</tr>
<?php
require_once('include/config.inc.php');

$last = 100;
if(isset($_REQUEST['n'])){
  $last = $_REQUEST['n'];
  }

$sql = "select FROM_UNIXTIME(history_text.clock), hosts.host, history_text.value from items,hosts,history_text WHERE key_='p2ner.log' AND hosts.hostid=items.hostid AND history_text.itemid=items.itemid ORDER BY history_text.clock DESC LIMIT ".$last;
$values = DBselect($sql);
while ($row = DBfetch($values)) {

  print "<tr><td>".$row['FROM_UNIXTIME(history_text.clock)']."</td><td>".$row['host']."</td><td>".$row['value']."</td></tr>";

}

?>
</table>
</html>
