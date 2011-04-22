<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
	<link href="sql.css" rel="stylesheet" type="text/css" media="screen" />
  	<link rel="icon" type="image/png" href="cctv.ico" />
    <script type="text/javascript" src="../OpenLayers/OpenLayers.js"></script>
    <script type="text/javascript" src="../osm/OpenStreetMap.js"></script>
    <script type="text/javascript" src="jquery.js"></script>
    <script type="text/javascript" src="cctv_map.js"></script>
  	<title>Inventaire de la vid&eacute;osurveillance en France</title>
</head>
  	<body onLoad="init()">
		<div id="logo">
			<p>Inventaire de la vid&eacute;o-surveillance<br>
			sur la voie publique en France</p>
	</div>
	<div id="map"></div>
		<div id="about">
		<p><em><a href="index.html"><strong>Retour au projet</strong></a><br>
		Donn&eacute;es globales <a href="http://bugbrother.blog.lemonde.fr/category/videosurveillance">BugBrother</a> et g&eacute;olocalisation extraites de <a href="http://www.openstreetmap.org/?lat=45.6976&lon=-0.328&zoom=14&layers=M">OpenStreetMap</a> :
				<script type="text/javascript">
		<!--
			/* get the modification date of the cctv.txt file */
			var request=new XMLHttpRequest();
			request.open("HEAD","http://www.leretourdelautruche.com/map/cctv/cctv.txt",false);
			request.send(null);
			var date=request.getResponseHeader("Last-Modified")
			document.writeln(date)
		-->
				</script>
				<noscript>
		no javascript
				</noscript>
			</em><br>
		r&eacute;alis&eacute; par <a href="http://www.openstreetmap.org/user/Pierre-Alain Dorange">Pierre-Alain Dorange</a> avec Javascript+OpenLayers, MySQL, PHP et Python.</p>
  </div>
  <?php
		require("config.php");
		$connect = mysql_connect($server,$login,$pwd) or die("connect error : ".mysql_error());
		mysql_select_db($database,$connect) or die("select db : ".mysql_error()) ;

		$query="select * from city,cctv where city.insee=cctv.insee".$version." order by name";
					
		$result = mysql_query($query,$connect) or die("select error : ".mysql_error());
		echo "<div id='list'>Villes<ul>";
		while ($row = mysql_fetch_array($result))
		{
			$lat=$row[latitude];
			$lon=$row[longitude];
			echo '<li><b><a href="http://www.leretourdelautruche.com/map/cctv/cctv_map.php?zoom=12&lat='.$lat.'&lon='.$lon.'">'.$row[name].'</a></b> '.$row[county].'</li>';
		}
		echo '</ul></div>';
			
		mysql_close($connect);
	?>
<!-- Start of StatCounter Code -->
	<script type="text/javascript" language="javascript">
	var sc_project=1651860; 
	var sc_invisible=1; 
	var sc_partition=15; 
	var sc_security="9710e8ad"; 
	</script>
	<script type="text/javascript" language="javascript" src="http://www.statcounter.com/counter/counter.js"></script>
	<noscript>
		<a href="http://www.statcounter.com/" target="_blank">
		<img  src="http://c16.statcounter.com/counter.php?sc_project=1651860&amp;java=0&amp;security=9710e8ad&amp;invisible=1" alt="hit counter script" border="0">
		</a>
	</noscript>
	<!-- End of StatCounter Code -->
	</body>
</html>