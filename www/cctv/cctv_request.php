<?php
# Generate a text output (UTF-8 encoded) that match OpenLayers Layer data format :
#	- latitude and longitude (lat,lon)
#	- icon picture url (url)
#	- icone size (x,y)
#	- icon offset (x,y)
#	- title (text, html accepted)
#	- description (text, html accepted)
#
# Output is generate for the 2 layers (city data and cctv localisation), 
# data are extracted from the local MySQL database
# parameters (html url) :
#	- l : left (latitude)
#	- r : right
#	- t : top
#	- b : bottom
#	- z : zoom level

#header to define the texte file as UTF8 encoded
header("Content-type: text/plain; charset=UTF-8");

#include config file (define serveur and paths)
require("config.php");

#$dbg=True;

function write_header()
{
#       lat  lon  icon  iconSize  iconOffset  title  description
 print("lat\tlon\ticon\ticonSize\ticonOffset\ttitle\tdescription\n");
}

function write_line_city($row,$coef)
{
	global $city_icon_path,$city_icon_minsize,$city_icon_maxsize,$canedit;
	
	$id=$row["insee"];
	$nb0=$row["nb0"];
	$title1=$row["title1"];
	$title2=$row["title2"];
	$src1=$row["source1"];
	$src2=$row["source2"];
	$nb=intval($nb0);
	# lat  lon
    echo $row["lat"]."\t".$row["lon"]."\t";
	#  icon url, iconSize & offset
	if ($coef==0)
		$size=$city_icon_minsize;
	else
		$size=(($city_icon_maxsize-$city_icon_minsize)*$nb/$coef)+$city_icon_minsize;
 	echo $city_icon_path."\t".strval($size).",".strval($size)."\t-".strval($size/2).",-".strval($size/2)."\t";
	#  title
 	echo utf8_encode("<h2>".$row["name"]."<br>".$row["county"]."</h2>\t");
	#  description
	if ($nb==0)
		$str='nombre inconnu';
	else
		$str=$nb0;
	echo utf8_encode('<p>Caméra(s) : '.$str.'<br><b>Population</b> : '.$row["population"].' (insee 2007)');
	echo utf8_encode('<br>'.$row["comm"].'<br><b>Source(s)</b> : </p><ul>');
	if (strlen($src1)>0)
		if (strlen($title1)>0)
			echo utf8_encode('<li><a href="'.$src1.'" target="_blank">'.$title1.'</a></li>');
		else
			echo utf8_encode('<li><a href="'.$src1.'" target="_blank">'.$src1.'</a></li>');
	if (strlen($src2)>0)
		if (strlen($title2)>0)
			echo utf8_encode('<li><a href="'.$src2.'" target="_blank">'.$title2.'</a></li>');
		else
			echo utf8_encode('<li><a href="'.$src2.'" target="_blank">'.$src2.'</a></li>');
	if ($can_edit)
		echo '</ul><br><p><a href="cctv_edit.php?insee='.$id.'"><b>Modifier</b><a></p>';
	echo '</ul></p>';
	echo "\n";
}

function fetch_poi_city($query,$connect,$max,$dbg)
{
	global $dbg;
	
    $res = mysql_query($query,$connect) or die("select error : ".mysql_error());

	$nb=mysql_num_rows($res);
	if ($dbg) { echo("Nb ligne(s) : ".$nb."\n"); }
	if ($nb > 0)
    {
    	while ($row = mysql_fetch_array ($res))
    	{
            write_line_city($row,$max);
        }
    }
    mysql_free_result($res);
}

function write_line_osm($row,$z)
{
	global $small_icon_path,$small_icon_size,$normal_icon_path,$normal_icon_size;

	# lat  lon
    echo $row["lat"]."\t".$row["lon"]."\t";
	#  icon url, size and offset
	if ($z>=16)
	{
		$size=$normal_icon_size;
 		echo $normal_icon_path."\t".strval($size).",".strval($size)."\t-".strval($size/2).",-".strval($size/2)."\t";
	}
	else
	{
		$size=$small_icon_size;
 		echo $small_icon_path."\t".strval($size).",".strval($size)."\t-".strval($size/2).",-".strval($size/2)."\t";
	}
	#  title
 	echo utf8_encode("<h2>".$row["name"]."</h2>\t");
	#  description
 	echo utf8_encode("<p>".$row["source"]."<br>latitude=".$row["lat"]."<br>longitude=".$row["lon"]."</p>");
 	echo "\n";
}

function fetch_poi_osm($query,$connect,$z,$dbg)
{
	global $dbg;
	
    $res = mysql_query($query,$connect) or die("select error : ".mysql_error());

	$nb=mysql_num_rows($res);
	if ($dbg) { echo("Nb ligne(s) : ".$nb."\n"); }
	if ($nb > 0)
    {
    	while ($row = mysql_fetch_array ($res))
    	{
            write_line_osm($row,$z);
        }
    }
    mysql_free_result($res);
}

# get box (longitude, latitude) and zoom level (as parameters)
$left = $_GET["l"];
$top = $_GET["t"];
$right = $_GET["r"];
$bottom = $_GET["b"];
$zoom = $_GET["z"];

if ($left>$right)
{
    $temp =$left;
    $left=$right;
    $right=$temp;
}

if ($bottom>$top)
{
    $temp =$top;
    $top=$bottom;
    $bottom=$temp;
}

# connect to MySQL database
$connect = mysql_connect($server,$login,$pwd) or die("connect error : ".mysql_error());
mysql_select_db($database,$connect) or die("select db : ".mysql_error()) ;

# query nb camera in database
$query = "SELECT MAX(nb_actual)as nb FROM cctv\n";
$res = mysql_query($query,$connect) or die("select error : ".mysql_error());
$row = mysql_fetch_array ($res);
$nbmax=intval($row["nb"]);

# write the output text 
write_header();

# for zoom higher than 12, also query the cctv geolocalisation from database
if ($z>=12)
{
	$query = "SELECT osmcctv.latitude as lat, osmcctv.longitude as lon, osmcctv.name as name, osmcctv.source as source\n";
	$query .= " FROM osmcctv WHERE\n";
	$query .= " osmcctv.longitude>=$left AND osmcctv.longitude<$right AND osmcctv.latitude>=$bottom AND osmcctv.latitude<$top\n";

	if ($dbg) {
	    echo($query."\n"); }

	fetch_poi_osm($query,$connect,$z,$dbg);
}

$query = "SELECT city.latitude as lat, city.longitude as lon, city.name as name, city.population as population, city.county as county, cctv.cam_comm as comm, cctv.source1 as source1, cctv.source2 as source2,\n";
$query .= " cctv.nb_actual as nb0, cctv.source_title1 as title1, cctv.source_title2 as title2, cctv.insee as insee\n";
$query .= " FROM city, cctv WHERE cctv.insee=city.insee AND\n";
$query .= " city.longitude>=$left AND city.longitude<$right AND city.latitude>=$bottom AND city.latitude<$top\n";

if ($dbg) {
    echo($query."\n"); }

fetch_poi_city($query,$connect,$nbmax,$dbg);

mysql_close($connect);

?>