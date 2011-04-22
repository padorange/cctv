<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Administration des donn&eacute;es</title>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
  	<link rel="icon" type="image/png" href="cctv.ico" />
	<style type="text/css">
<!--
.Style1 {
	color: #660000;
	font-weight: bold;
}
-->
	</style>
</head>

<body>
  <h1>
Administration des donn&eacute;es	</h1>
  <p>Cliquer sur les titres des	colonnes pour trier la liste des villes (par nom, par d&eacute;partement, par population ou nombre de cam&eacute;ras inventori&eacute;es).<br>
  Le bouton &quot;modifier&quot; en fin de ligne permet d'acc&eacute;der &agrave; la fiche d'information de la ville.<br>
  Le bouton &quot;ajouter&quot; (en haut &agrave; droite) permet de cr&eacute;er une nouvelle ville vid&eacute;osurveill&eacute;e (merci de bien v&eacute;rifier que celle-ci n'existe pas d&eacute;j&agrave;).</p>
  <p>Les donn&eacute;es saisies sont <strong>mod&eacute;r&eacute;es</strong>, vos modifications <strong>n'apparaitront donc pas imm&eacute;diatement</strong>.</p>
  <p class="Style1">Version en test uniquement, non fonctionnelle.</p>
<p>
  	<?php
			#include config file (define serveur and paths)
			require("config.php");

			$connect = mysql_connect($server,$login,$pwd) or die("connect error : ".mysql_error());
			mysql_select_db($database,$connect) or die("select db : ".mysql_error()) ;

			$sort="order by city.name ";
			if (isset($_GET['sort']))
			{
				$s=$_GET['sort'];
				if ($s=="name") { $sort="order by city.name "; }
				if ($s=="camera") { $sort="order by cctv.nb_actual "; }
				if ($s=="county") { $sort="order by city.county "; }
				if ($s=="population") { $sort="order by city.population "; }
			}
			$query="select * from city,cctv where city.insee=cctv.insee ".$sort;
					
			$result = mysql_query($query,$connect) or die("select error : ".mysql_error());
			echo "<table border='1'><tr><th><a href='".$base_admin."?sort=city'>Ville</a></th>";
			echo "<th><a href='".$base_admin."?sort=county'>Département</a></th>";
			echo "<th><a href='".$base_admin."?sort=population'>Population</a></th>";
			echo "<th><a href='".$base_admin."?sort=camera'>Caméra(s)</a></th>";
			echo "<th>Densité<br>(caméra/ 1000 habitants)</th>";
			echo "<th>Géolocalisation</th><th>";
			if ($can_edit)
			{
				echo "<a href='".$edit_url."?insee=0'>ajouter</a>";
			}
			echo "</th></tr>";
			while ($row = mysql_fetch_array($result))
			{
				$lat=$row[latitude];
				$lon=$row[longitude];
				$name=$row[name];
				$county=$row[county];
				$id=$row[insee];
				$nbcam=$row[nb_actual];
				$pop=$row[population];
				if ($nbcam=='0')
				{
					$nbcam='?';
					$dens="";
				}
				else
				{
					if ($pop==0)
						$dens="";
					else
						$dens=strval(round(1000*intval($nbcam)/intval($pop),2));
				}
				echo '<tr><td>'.$name.'</td><td>'.$county.'</td><td>'.$pop.'</td><td>'.$nbcam.'</td><td>'.$dens.'</td><td>'.$lat.','.$lon.'</td><td>';
				if ($can_edit)
				{
					echo '<a href="'.$edit_url.'?insee='.$id.'">modifier</a>';
				}
				echo '</td></tr>';
			}
			echo '</table>';
			
			mysql_close($connect);
	?>
</p>
<p>&nbsp;
		</p>
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
